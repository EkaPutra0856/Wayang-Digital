# voice_trigger.py
import speech_recognition as sr
import sounddevice as sd
import numpy as np
import os
import threading
import time
from collections import deque

TRIGGER_KEYWORDS = {
    "rumah": "Rumah",
    "sekolah": "SekolahIslamAlAzharPekalongan",
    "al azhar": "SekolahIslamAlAzharPekalongan",
    "alazhar": "SekolahIslamAlAzharPekalongan",
    "pekalongan": "SekolahIslamAlAzharPekalongan",
    "taman": "Taman"
}

LATAR_DIR = os.path.join(os.path.dirname(__file__), "Latar")


class VoiceBackgroundManager:
    def __init__(self, trigger_dict=TRIGGER_KEYWORDS, latar_dir=LATAR_DIR, device_index=1):
        self.trigger_dict = trigger_dict
        self.latar_dir = latar_dir
        self.device_index = device_index
        
        # State Scene
        self.current_scene_name = None
        self.current_png_path = None
        self.current_mp4_path = None
        self.trigger_event = False
        
        self.running = False
        self.recognizer = sr.Recognizer()
        self.sample_rate = 16000
        
        self.buffer_size = self.sample_rate * 3
        self.audio_ring_buffer = deque(maxlen=self.buffer_size)
        self.last_trigger_time = 0
        self.cooldown_duration = 2.0

    def _audio_callback(self, indata, frames, time_info, status):
        if self.running:
            self.audio_ring_buffer.extend(indata[:, 0].tolist())

    def _recognize_chunk(self, audio_data, trigger_label="Detector 1"):
        try:
            raw_bytes = np.array(audio_data, dtype=np.int16).tobytes()
            audio = sr.AudioData(raw_bytes, self.sample_rate, 2)
            text = self.recognizer.recognize_google(audio, language="id-ID").lower()
            print(f"[{trigger_label} Menangkap]: \"{text}\"")

            matched_base = None
            for kw, base_name in self.trigger_dict.items():
                if kw in text:
                    matched_base = base_name
                    break

            if matched_base:
                # KUNCI 1: Jika scene yang disebut SAMA DENGAN scene yang sedang aktif, abaikan
                if matched_base == self.current_scene_name:
                    print(f"[{trigger_label}] Scene '{matched_base}' sudah aktif. Transisi diabaikan.")
                    return

                png_path = os.path.join(self.latar_dir, f"{matched_base}.png")
                mp4_path = os.path.join(self.latar_dir, f"{matched_base}.mp4")

                if os.path.exists(png_path):
                    self.current_scene_name = matched_base
                    self.current_png_path = png_path
                    self.current_mp4_path = mp4_path if os.path.exists(mp4_path) else None
                    self.trigger_event = True
                    self.last_trigger_time = time.time()
                    print(f"\n========================================")
                    print(f" >>> [GANTI SCENE]: [{matched_base.upper()}]")
                    print(f"========================================\n")
                else:
                    print(f"[Peringatan] File '{png_path}' belum ada di folder Latar/!\n")

        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            print(f"[Voice Network Error]: {e}")
        except Exception:
            pass

    def _delayed_secondary_detect(self, delay=1.8):
        time.sleep(delay)
        if not self.running:
            return
        snapshot = list(self.audio_ring_buffer)
        if len(snapshot) >= self.sample_rate * 1.5:
            chunk = snapshot[-int(self.sample_rate * 2.5):]
            self._recognize_chunk(chunk, trigger_label="Detector 2 (Delayed)")

    def listen_loop(self):
        print(f"\n[Voice] Standby mendengarkan kata kunci latar...")
        print(f"[Voice] Target Scene: Rumah, Sekolah/Al Azhar, Taman\n")

        block_size = int(self.sample_rate * 0.05)
        energy_threshold = 450
        is_speaking = False
        last_speech_time = 0

        try:
            with sd.InputStream(device=self.device_index, samplerate=self.sample_rate, 
                                channels=1, dtype='int16', blocksize=block_size, 
                                callback=self._audio_callback):
                while self.running:
                    time.sleep(0.05)
                    if len(self.audio_ring_buffer) < block_size:
                        continue
                        
                    recent_samples = np.array(list(self.audio_ring_buffer)[-block_size:], dtype=np.float32)
                    rms = np.sqrt(np.mean(recent_samples ** 2))
                    current_time = time.time()

                    if rms > energy_threshold:
                        if not is_speaking and (current_time - last_speech_time > 1.0):
                            is_speaking = True
                            last_speech_time = current_time
                            
                            def trigger_sequence():
                                time.sleep(0.7)
                                snapshot = list(self.audio_ring_buffer)
                                if len(snapshot) >= self.sample_rate:
                                    chunk = snapshot[-int(self.sample_rate * 2.0):]
                                    self._recognize_chunk(chunk, trigger_label="Detector 1 (Auto)")
                                threading.Thread(target=self._delayed_secondary_detect, args=(1.5,), daemon=True).start()

                            threading.Thread(target=trigger_sequence, daemon=True).start()
                    else:
                        if is_speaking and (current_time - last_speech_time > 0.6):
                            is_speaking = False
        except Exception as e:
            print(f"[Voice Mic Error]: {e}")

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.listen_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
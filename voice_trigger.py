"""Bounded Indonesian voice background trigger, using the FIX ASSET scene order."""
from collections import deque
from queue import Queue, Empty, Full
import threading
import time
import numpy as np
import sounddevice as sd
import speech_recognition as sr

# Inspected backgrounds: park, dining room, school entrance, class, corridor.
TRIGGER_KEYWORDS = {"koridor": 4, "kelas": 3, "sekolah": 2, "al azhar": 2,
                    "alazhar": 2, "pekalongan": 2, "rumah": 1, "makan": 1, "taman": 0}


class VoiceBackgroundManager:
    def __init__(self, device_index=None):
        self.device_index = device_index
        self.recognizer = sr.Recognizer()
        self.recognizer.operation_timeout = 4
        self.running = threading.Event()
        self.enabled = True
        self.generation = 0
        self.samples = deque(maxlen=32000)
        self.chunks = Queue(maxsize=1)
        self.events = Queue(maxsize=1)
        self.last_capture = 0.0
        self.thread = None

    def set_enabled(self, enabled):
        if self.enabled != enabled:
            self.enabled = enabled
            self.generation += 1
        if not enabled:
            self.poll()  # discard a previously recognized event during media playback

    def _audio_callback(self, indata, frames, time_info, status):
        if not self.enabled:
            self.samples.clear()
            return
        self.samples.extend(indata[:, 0].tolist())
        now = time.monotonic()
        rms = np.sqrt(np.mean(indata.astype(np.float32)**2))
        if len(self.samples) == 32000 and rms > 450 and now-self.last_capture >= 2.0:
            try:
                self.chunks.put_nowait((self.generation, np.asarray(self.samples, dtype=np.int16).tobytes()))
                self.last_capture = now
            except Full:
                pass

    def listen_loop(self):
        try:
            with sd.InputStream(device=self.device_index, samplerate=16000, channels=1,
                                dtype='int16', blocksize=1600, callback=self._audio_callback):
                print("[VOICE] Active: taman / rumah / sekolah / kelas / koridor")
                while self.running.is_set():
                    try:
                        generation, raw = self.chunks.get(timeout=0.2)
                    except Empty:
                        continue
                    if not self.enabled or generation != self.generation:
                        continue
                    try:
                        text = self.recognizer.recognize_google(sr.AudioData(raw, 16000, 2), language="id-ID").lower()
                        if not self.running.is_set() or not self.enabled or generation != self.generation:
                            continue
                        for keyword, index in TRIGGER_KEYWORDS.items():
                            if keyword in text:
                                try:
                                    self.events.put_nowait(index)
                                except Full:
                                    pass
                                break
                    except sr.UnknownValueError:
                        pass
                    except Exception as exc:
                        print(f"[VOICE ERROR] Recognition: {exc}")
        except Exception as exc:
            print(f"[VOICE ERROR] Microphone: {exc}. Keyboard controls remain available.")

    def poll(self):
        try:
            return self.events.get_nowait()
        except Empty:
            return None

    def start(self):
        self.running.set()
        self.thread = threading.Thread(target=self.listen_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running.clear()
        if self.thread:
            self.thread.join(timeout=0.5)

# effect_animator.py
import cv2
import numpy as np
import os
import math
import time
import speech_recognition as sr
import sounddevice as sd
import threading
from collections import deque

EFFECT_DIR = os.path.join(os.path.dirname(__file__), "Effect")


class EffectAnimator:
    def __init__(self, effect_dir=EFFECT_DIR, device_index=1):
        self.effect_dir = effect_dir
        self.device_index = device_index
        
        # Load Aset PNG (BGRA)
        self.tas_img = cv2.imread(os.path.join(self.effect_dir, "Tas.png"), cv2.IMREAD_UNCHANGED)
        self.buku_img = cv2.imread(os.path.join(self.effect_dir, "Buku.png"), cv2.IMREAD_UNCHANGED)

        # State Animasi Tas ('hidden', 'pop_in', 'looping', 'fade_out')
        self.tas_state = "hidden"
        self.tas_timer = 0.0
        self.tas_alpha = 1.0

        # State Animasi Buku ('hidden', 'slide_in', 'looping', 'fade_out')
        self.buku_state = "hidden"
        self.buku_timer = 0.0
        self.buku_alpha = 1.0

        # Inisialisasi Audio Listener
        self.running = False
        self.recognizer = sr.Recognizer()
        self.sample_rate = 16000
        self.audio_ring_buffer = deque(maxlen=self.sample_rate * 3)

    # ==========================================
    # LOGIKA TRIGGER KEYBOARD & TOGGLE
    # ==========================================
    def trigger_tas(self):
        self.tas_state = "pop_in"
        self.tas_timer = time.time()
        self.tas_alpha = 1.0
        print("\n>>> [EFFECT]: TAS AKTIF (Pop-in) <<<")

    def dismiss_tas(self):
        if self.tas_state != "hidden":
            self.tas_state = "fade_out"
            print("\n>>> [EFFECT]: TAS FADE OUT <<<")

    def toggle_tas(self):
        """Tekan 1: Toggle Muncul / Hilang Tas"""
        if self.tas_state in ["hidden", "fade_out"]:
            self.trigger_tas()
        else:
            self.dismiss_tas()

    def trigger_buku(self):
        if self.tas_state == "hidden":
            self.trigger_tas()
        self.buku_state = "slide_in"
        self.buku_timer = time.time()
        self.buku_alpha = 1.0
        print("\n>>> [EFFECT]: BUKU AKTIF (Slide-out dari Tas) <<<")

    def dismiss_buku(self):
        if self.buku_state != "hidden":
            self.buku_state = "fade_out"
            print("\n>>> [EFFECT]: BUKU FADE OUT <<<")

    def toggle_buku(self):
        """Tekan 2: Toggle Muncul / Hilang Buku"""
        if self.buku_state in ["hidden", "fade_out"]:
            self.trigger_buku()
        else:
            self.dismiss_buku()

    def trigger_dismiss(self):
        """Tekan 0: Hilangkan Semua Efek"""
        self.dismiss_tas()
        self.dismiss_buku()
        print("\n>>> [EFFECT]: HILANGKAN SEMUA EFEK <<<")

    # ==========================================
    # AUDIO RECOGNIZER
    # ==========================================
    def _audio_callback(self, indata, frames, time_info, status):
        if self.running:
            self.audio_ring_buffer.extend(indata[:, 0].tolist())

    def _recognize_chunk(self, audio_data):
        try:
            raw_bytes = np.array(audio_data, dtype=np.int16).tobytes()
            audio = sr.AudioData(raw_bytes, self.sample_rate, 2)
            text = self.recognizer.recognize_google(audio, language="id-ID").lower()
            print(f"[Effect Voice Menangkap]: \"{text}\"")

            dismiss_phrases = ["alhamdulillah", "tidak tertinggal", "tidak ketinggalan", "syukurlah", "masih lengkap", "sudah selesai"]
            if any(p in text for p in dismiss_phrases):
                self.trigger_dismiss()
                return

            buku_phrases = ["ternyata bukuku", "bukuku masih ada", "ternyata bukunya", "buku pelajaranku", "buku tulisku", "ada bukunya"]
            if any(p in text for p in buku_phrases):
                self.trigger_buku()
                return

            tas_phrases = ["tertinggal di tas", "ketinggalan di tas", "dalam tasku", "mengecek tas", "cek tasku", "periksa tas"]
            if any(p in text for p in tas_phrases):
                self.trigger_tas()
                return

        except sr.UnknownValueError:
            pass
        except Exception:
            pass

    def listen_loop(self):
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

                    recent = np.array(list(self.audio_ring_buffer)[-block_size:], dtype=np.float32)
                    rms = np.sqrt(np.mean(recent ** 2))
                    current_time = time.time()

                    if rms > energy_threshold:
                        if not is_speaking and (current_time - last_speech_time > 1.0):
                            is_speaking = True
                            last_speech_time = current_time

                            def trigger_sequence():
                                time.sleep(0.8)
                                snapshot = list(self.audio_ring_buffer)
                                if len(snapshot) >= self.sample_rate:
                                    chunk = snapshot[-int(self.sample_rate * 2.2):]
                                    self._recognize_chunk(chunk)

                            threading.Thread(target=trigger_sequence, daemon=True).start()
                    else:
                        if is_speaking and (current_time - last_speech_time > 0.6):
                            is_speaking = False
        except Exception as e:
            print(f"[Effect Mic Error]: {e}")

    def start_voice(self):
        self.running = True
        self.thread = threading.Thread(target=self.listen_loop, daemon=True)
        self.thread.start()

    def stop_voice(self):
        self.running = False

    # ==========================================
    # LOGIKA TRANSFORMASI OVERLAY
    # ==========================================
    def _overlay(self, background, img, center_x, center_y, scale_w, scale_h, angle=0.0, alpha_mult=1.0):
        if img is None or scale_w <= 0 or scale_h <= 0 or alpha_mult <= 0.0:
            return background

        h, w = background.shape[:2]
        target_w = max(1, int(scale_w))
        target_h = max(1, int(scale_h))

        resized = cv2.resize(img, (target_w, target_h), interpolation=cv2.INTER_AREA)

        if angle != 0:
            diag = int(math.hypot(target_w, target_h))
            pad_x = (diag - target_w) // 2
            pad_y = (diag - target_h) // 2
            padded = cv2.copyMakeBorder(resized, pad_y, pad_y, pad_x, pad_x, cv2.BORDER_CONSTANT, value=[0, 0, 0, 0])
            center = (padded.shape[1] // 2, padded.shape[0] // 2)
            rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(padded, rot_mat, (padded.shape[1], padded.shape[0]), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=[0, 0, 0, 0])
            resized = rotated
            target_w, target_h = resized.shape[1], resized.shape[0]

        x1 = int(center_x - target_w // 2)
        y1 = int(center_y - target_h // 2)
        x2 = x1 + target_w
        y2 = y1 + target_h

        clip_x1, clip_y1 = max(0, x1), max(0, y1)
        clip_x2, clip_y2 = min(w, x2), min(h, y2)

        if clip_x1 >= clip_x2 or clip_y1 >= clip_y2:
            return background

        crop_ox1, crop_oy1 = clip_x1 - x1, clip_y1 - y1
        crop_ox2, crop_oy2 = crop_ox1 + (clip_x2 - clip_x1), crop_oy1 + (clip_y2 - clip_y1)

        overlay_crop = resized[crop_oy1:crop_oy2, crop_ox1:crop_ox2]
        bg_crop = background[clip_y1:clip_y2, clip_x1:clip_x2]

        if overlay_crop.shape[2] == 4:
            alpha = (overlay_crop[:, :, 3] / 255.0) * alpha_mult
            alpha = np.expand_dims(alpha, axis=2)
            rgb = overlay_crop[:, :, :3]
            bg_crop[:] = (alpha * rgb + (1.0 - alpha) * bg_crop).astype(np.uint8)

        return background

    # ==========================================
    # RENDER PIPELINE KE CANVAS WHITEBOARD
    # ==========================================
    def render(self, canvas):
        h, w = canvas.shape[:2]
        cur_time = time.time()

        # Handle Fade Out Tas
        if self.tas_state == "fade_out":
            self.tas_alpha -= 0.05
            if self.tas_alpha <= 0.0:
                self.tas_alpha = 0.0
                self.tas_state = "hidden"

        # Handle Fade Out Buku
        if self.buku_state == "fade_out":
            self.buku_alpha -= 0.05
            if self.buku_alpha <= 0.0:
                self.buku_alpha = 0.0
                self.buku_state = "hidden"

        tas_center_x = w * 0.5
        tas_center_y = h * 0.55
        base_tas_w = w * 0.40
        base_tas_h = base_tas_w * (self.tas_img.shape[0] / self.tas_img.shape[1]) if self.tas_img is not None else h * 0.45

        # 1. RENDER BUKU
        if self.buku_state != "hidden" and self.buku_img is not None:
            base_buku_w = base_tas_w * 0.55
            base_buku_h = base_buku_w * (self.buku_img.shape[0] / self.buku_img.shape[1])

            target_buku_x = tas_center_x + (base_tas_w * 0.42)
            target_buku_y = tas_center_y - (base_tas_h * 0.38)

            elapsed_b = cur_time - self.buku_timer

            if self.buku_state == "slide_in":
                progress = min(1.0, elapsed_b / 0.6)
                ease_out = math.sin(progress * (math.pi / 2))

                buku_x = tas_center_x + (target_buku_x - tas_center_x) * ease_out
                buku_y = tas_center_y + (target_buku_y - tas_center_y) * ease_out
                buku_w = base_buku_w * (0.3 + 0.7 * ease_out)
                buku_h = base_buku_h * (0.3 + 0.7 * ease_out)
                buku_angle = 15.0 * (1.0 - ease_out)

                if progress >= 1.0:
                    self.buku_state = "looping"
                    self.buku_timer = cur_time
            else:
                loop_t = cur_time - self.buku_timer
                scale_pulse = 1.0 + 0.05 * math.sin(loop_t * 3.5)
                buku_x = target_buku_x
                buku_y = target_buku_y + (math.sin(loop_t * 3.0) * 8.0)
                buku_w = base_buku_w * scale_pulse
                buku_h = base_buku_h * scale_pulse
                buku_angle = 15.0 * math.sin(loop_t * 2.5)

            canvas = self._overlay(canvas, self.buku_img, buku_x, buku_y, buku_w, buku_h,
                                   angle=buku_angle, alpha_mult=self.buku_alpha)

        # 2. RENDER TAS
        if self.tas_state != "hidden" and self.tas_img is not None:
            elapsed_t = cur_time - self.tas_timer

            if self.tas_state == "pop_in":
                progress = min(1.0, elapsed_t / 0.5)
                elastic = math.sin(progress * math.pi * 0.7) * (1.15 if progress < 0.75 else 1.0)
                tas_w = base_tas_w * elastic
                tas_h = base_tas_h * elastic

                if progress >= 1.0:
                    self.tas_state = "looping"
                    self.tas_timer = cur_time
            else:
                loop_t = cur_time - self.tas_timer
                stretch_x = 1.0 + 0.04 * math.sin(loop_t * 3.0)
                stretch_y = 1.0 - 0.04 * math.sin(loop_t * 3.0)
                tas_w = base_tas_w * stretch_x
                tas_h = base_tas_h * stretch_y

            canvas = self._overlay(canvas, self.tas_img, tas_center_x, tas_center_y, tas_w, tas_h,
                                   angle=0, alpha_mult=self.tas_alpha)

        return canvas
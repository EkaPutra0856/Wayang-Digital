# ball_animator.py
import cv2
import numpy as np
import os
import random
import math

EFFECT_DIR = os.path.join(os.path.dirname(__file__), "Effect")


class BallAnimator:
    def __init__(self, effect_dir=EFFECT_DIR):
        self.effect_dir = effect_dir
        self.ball_path = os.path.join(self.effect_dir, "Bola.png")
        self.ball_img = None
        
        if os.path.exists(self.ball_path):
            self.ball_img = cv2.imread(self.ball_path, cv2.IMREAD_UNCHANGED)

        # State Aktif Bola
        self.is_active = False
        self.radius = 45           # Jari-jari bola
        self.pos_x = 0.0
        self.pos_y = 0.0
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.speed = 18.0          # Kecepatan bola
        self.rotation_angle = 0.0  # Efek putaran bola saat memantul
        self.rot_speed = 5.0

    def toggle(self, screen_w=1920, screen_h=1080):
        """Toggle tombol 3: Munculkan / Hilangkan Bola."""
        if self.is_active:
            self.dismiss()
        else:
            self.spawn(screen_w, screen_h)

    def spawn(self, screen_w=1920, screen_h=1080):
        """Munculkan bola dari posisi tengah atas dengan sudut gerak acak."""
        self.is_active = True
        self.pos_x = screen_w * 0.5
        self.pos_y = screen_h * 0.25

        # Pilih sudut acak yang mengarah ke bawah (antara 30 s.d 150 derajat)
        angle_rad = math.radians(random.uniform(35, 145))
        direction_x = 1 if random.random() < 0.5 else -1
        self.vel_x = math.cos(angle_rad) * self.speed * direction_x
        self.vel_y = math.sin(angle_rad) * self.speed
        self.rot_speed = random.choice([-8.0, 8.0])
        print("\n>>> [EFFECT]: BOLA DIMUNCULKAN (Memantul Acak) <<<")

    def dismiss(self):
        """Hilangkan bola dari layar (Tombol 3 atau Tombol 0)."""
        if self.is_active:
            self.is_active = False
            print("\n>>> [EFFECT]: BOLA DIHILANGKAN <<<")

    def _overlay_transparent(self, background, overlay, center_x, center_y, angle=0.0):
        """Merender sprite bola dengan rotasi dan alpha channel."""
        h, w = background.shape[:2]
        target_size = int(self.radius * 2)

        if overlay is not None:
            resized = cv2.resize(overlay, (target_size, target_size), interpolation=cv2.INTER_AREA)
        else:
            # Fallback: Buat bola lingkaran visual jika Bola.png belum ada
            resized = np.zeros((target_size, target_size, 4), dtype=np.uint8)
            cv2.circle(resized, (self.radius, self.radius), self.radius - 2, (0, 140, 255, 255), -1)
            cv2.circle(resized, (self.radius, self.radius), self.radius - 2, (255, 255, 255, 255), 3)

        # Rotasi Bola
        if angle != 0:
            diag = int(math.hypot(target_size, target_size))
            pad_x = (diag - target_size) // 2
            pad_y = (diag - target_size) // 2
            padded = cv2.copyMakeBorder(resized, pad_y, pad_y, pad_x, pad_x, cv2.BORDER_CONSTANT, value=[0, 0, 0, 0])
            center = (padded.shape[1] // 2, padded.shape[0] // 2)
            rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
            resized = cv2.warpAffine(padded, rot_mat, (padded.shape[1], padded.shape[0]), 
                                     flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=[0, 0, 0, 0])
            target_size = resized.shape[0]

        x1 = int(center_x - target_size // 2)
        y1 = int(center_y - target_size // 2)
        x2 = x1 + target_size
        y2 = y1 + target_size

        clip_x1, clip_y1 = max(0, x1), max(0, y1)
        clip_x2, clip_y2 = min(w, x2), min(h, y2)

        if clip_x1 >= clip_x2 or clip_y1 >= clip_y2:
            return background

        crop_ox1, crop_oy1 = clip_x1 - x1, clip_y1 - y1
        crop_ox2, crop_oy2 = crop_ox1 + (clip_x2 - clip_x1), crop_oy1 + (clip_y2 - clip_y1)

        overlay_crop = resized[crop_oy1:crop_oy2, crop_ox1:crop_ox2]
        bg_crop = background[clip_y1:clip_y2, clip_x1:clip_x2]

        if overlay_crop.shape[2] == 4:
            alpha = overlay_crop[:, :, 3] / 255.0
            alpha = np.expand_dims(alpha, axis=2)
            rgb = overlay_crop[:, :, :3]
            bg_crop[:] = (alpha * rgb + (1.0 - alpha) * bg_crop).astype(np.uint8)

        return background

    def update_and_render(self, canvas, character_boxes):
        """
        canvas: Layar whiteboard
        character_boxes: List bounding box karakter [(x_min, y_min, x_max, y_max), ...]
        """
        if not self.is_active:
            return canvas

        h, w = canvas.shape[:2]

        # 1. Update Posisi
        self.pos_x += self.vel_x
        self.pos_y += self.vel_y
        self.rotation_angle = (self.rotation_angle + self.rot_speed) % 360

        # 2. Tabrakan dengan Dinding Tepi Layar (Kiri & Kanan)
        if self.pos_x - self.radius <= 0:
            self.pos_x = self.radius
            self.vel_x = abs(self.vel_x)
            self.rot_speed = -self.rot_speed
        elif self.pos_x + self.radius >= w:
            self.pos_x = w - self.radius
            self.vel_x = -abs(self.vel_x)
            self.rot_speed = -self.rot_speed

        # Tabrakan dengan Dinding Tepi Layar (Atas & Bawah)
        if self.pos_y - self.radius <= 0:
            self.pos_y = self.radius
            self.vel_y = abs(self.vel_y)
        elif self.pos_y + self.radius >= h:
            self.pos_y = h - self.radius
            self.vel_y = -abs(self.vel_y)

        # 3. Tabrakan dengan Karakter Wayang (AABB vs Circle Collision)
        for box in character_boxes:
            bx_min, by_min, bx_max, by_max = box

            # Titik terdekat dari lingkaran ke persegi panjang karakter
            closest_x = max(bx_min, min(self.pos_x, bx_max))
            closest_y = max(by_min, min(self.pos_y, by_max))

            dist_x = self.pos_x - closest_x
            dist_y = self.pos_y - closest_y
            distance = math.hypot(dist_x, dist_y)

            # Jika terjadi kontak/tabrakan dengan karakter
            if distance < self.radius:
                # Tentukan arah pantulan berdasarkan sisi tabrakan
                overlap_x = self.radius - abs(dist_x) if dist_x != 0 else self.radius
                overlap_y = self.radius - abs(dist_y) if dist_y != 0 else self.radius

                if overlap_x < overlap_y:
                    # Tabrakan samping karakter
                    self.vel_x = -self.vel_x * 1.02  # Sedikit akselerasi pantul
                    self.pos_x += math.copysign(overlap_x, dist_x) if dist_x != 0 else self.vel_x
                else:
                    # Tabrakan atas/bawah karakter
                    self.vel_y = -self.vel_y * 1.02
                    self.pos_y += math.copysign(overlap_y, dist_y) if dist_y != 0 else self.vel_y

                # Batasi kecepatan maksimum agar bola tetap terkontrol
                self.vel_x = max(-28.0, min(28.0, self.vel_x))
                self.vel_y = max(-28.0, min(28.0, self.vel_y))
                self.rot_speed = random.uniform(-12.0, 12.0)
                break

        # 4. Gambar Bola ke Whiteboard
        canvas = self._overlay_transparent(canvas, self.ball_img, self.pos_x, self.pos_y, self.rotation_angle)
        return canvas
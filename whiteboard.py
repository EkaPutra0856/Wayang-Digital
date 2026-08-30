# whiteboard.py
import cv2
import numpy as np
import os
from collections import deque

class WhiteboardRenderer:
    def __init__(self, window_name="Wayang Digital", asset_dir="Animasi Wayang", 
                 show_box=False, show_pip=True, pause_delay_seconds=1.0):
        self.window_name = window_name
        self.asset_dir = os.path.join(os.path.dirname(__file__), asset_dir)
        
        self.show_box = show_box
        self.show_pip = show_pip
        
        # Kapasitas frame untuk rewind pause (30 FPS)
        buffer_frames = max(1, int(pause_delay_seconds * 30))
        self.is_paused = False
        self.paused_hand_boxes = []
        self.hand_history = deque(maxlen=buffer_frames)
        
        # State Background & Video Transisi
        self.active_png_path = None
        self.cached_png = None
        self.video_cap = None
        self.total_video_frames = 0
        self.current_video_frame_idx = 0
        self.fade_frames = 20
        
        self.character_sprites = {}
        self._load_sprites()

        # Inisialisasi Window Fullscreen
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    def _load_sprites(self):
        for i in range(1, 6):
            path_anak = os.path.join(self.asset_dir, f"{i}.png")
            if os.path.exists(path_anak):
                self.character_sprites[("Right", i)] = cv2.imread(path_anak, cv2.IMREAD_UNCHANGED)

            path_ibu = os.path.join(self.asset_dir, f"{i}i.png")
            if os.path.exists(path_ibu):
                self.character_sprites[("Left", i)] = cv2.imread(path_ibu, cv2.IMREAD_UNCHANGED)

    def set_scene(self, png_path, mp4_path=None):
        if not png_path or not os.path.exists(png_path):
            return

        if png_path == self.active_png_path:
            return

        self.active_png_path = png_path
        self.cached_png = cv2.imread(png_path)

        if self.video_cap is not None:
            self.video_cap.release()
            self.video_cap = None

        if mp4_path and os.path.exists(mp4_path):
            self.video_cap = cv2.VideoCapture(mp4_path)
            self.total_video_frames = int(self.video_cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.current_video_frame_idx = 0

    def _get_current_background(self, w, h):
        if self.cached_png is not None:
            base_bg = cv2.resize(self.cached_png, (w, h))
        else:
            base_bg = np.ones((h, w, 3), dtype=np.uint8) * 255

        if self.video_cap is not None and self.video_cap.isOpened():
            ret, v_frame = self.video_cap.read()
            self.current_video_frame_idx += 1

            if ret:
                v_frame_resized = cv2.resize(v_frame, (w, h))
                remaining_frames = self.total_video_frames - self.current_video_frame_idx
                
                if remaining_frames <= self.fade_frames and self.fade_frames > 0:
                    alpha = max(0.0, remaining_frames / float(self.fade_frames))
                    blended = cv2.addWeighted(v_frame_resized, alpha, base_bg, 1.0 - alpha, 0)
                    return blended
                else:
                    return v_frame_resized
            else:
                self.video_cap.release()
                self.video_cap = None

        return base_bg

    def _overlay_transparent(self, background, overlay, x, y, target_w, target_h):
        if overlay is None or target_w <= 0 or target_h <= 0:
            return background

        resized_overlay = cv2.resize(overlay, (target_w, target_h), interpolation=cv2.INTER_AREA)
        bg_h, bg_w, _ = background.shape
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(bg_w, x + target_w), min(bg_h, y + target_h)

        overlay_x1 = x1 - x
        overlay_y1 = y1 - y
        overlay_x2 = overlay_x1 + (x2 - x1)
        overlay_y2 = overlay_y1 + (y2 - y1)

        if x1 >= x2 or y1 >= y2:
            return background

        overlay_crop = resized_overlay[overlay_y1:overlay_y2, overlay_x1:overlay_x2]
        bg_crop = background[y1:y2, x1:x2]

        if overlay_crop.shape[2] == 4:
            alpha = overlay_crop[:, :, 3] / 255.0
            alpha = np.expand_dims(alpha, axis=2)
            rgb_overlay = overlay_crop[:, :, :3]
            bg_crop[:] = (alpha * rgb_overlay + (1.0 - alpha) * bg_crop).astype(np.uint8)
        else:
            bg_crop[:] = overlay_crop

        return background

    def toggle_pause(self):
        """Toggle pause posisi wayang."""
        self.is_paused = not self.is_paused
        if self.is_paused:
            if len(self.hand_history) > 0:
                self.paused_hand_boxes = self.hand_history[0]
            else:
                self.paused_hand_boxes = []
            print("\n[Sistem] PAUSE: Posisi Wayang dibekukan.")
        else:
            print("\n[Sistem] RESUME: Posisi Wayang kembali aktif.")

    def render(self, screen_res, cam_frame, hand_boxes, cam_res, effect_mgr=None):
        screen_w, screen_h = screen_res
        cam_w, cam_h = cam_res

        # 1. Simpan buffer riwayat tangan saat live
        if not self.is_paused:
            self.hand_history.append(list(hand_boxes))
            active_boxes = hand_boxes
        else:
            active_boxes = self.paused_hand_boxes

        # 2. Dapatkan Background Fullscreen
        canvas = self._get_current_background(screen_w, screen_h)

        # 3. Render Efek Animasi (Tas & Buku) jika effect_mgr dipassing
        if effect_mgr is not None:
            canvas = effect_mgr.render(canvas)

        scale_x = screen_w / cam_w
        scale_y = screen_h / cam_h

        # 4. Render Karakter Wayang di Layar Penuh
        for item in active_boxes:
            label = item["label"]
            x_min, y_min, x_max, y_max = item["box"]
            count = item["count"]

            sx_min = int(x_min * scale_x)
            sy_min = int(y_min * scale_y)
            sx_max = int(x_max * scale_x)
            sy_max = int(y_max * scale_y)

            box_w = sx_max - sx_min
            box_h = sy_max - sy_min

            if 1 <= count <= 5:
                sprite = self.character_sprites.get((label, count))
                if sprite is not None:
                    render_h = int(box_h * 1.5)
                    aspect_ratio = sprite.shape[1] / sprite.shape[0]
                    render_w = int(render_h * aspect_ratio)

                    render_x = sx_min + (box_w - render_w) // 2
                    render_y = sy_min - (render_h - box_h)

                    canvas = self._overlay_transparent(canvas, sprite, render_x, render_y, render_w, render_h)

            if self.show_box:
                box_color = (255, 120, 0) if label == "Left" else (0, 80, 255)
                role_label = f"IBU: {count}" if label == "Left" else f"ANAK: {count}"

                cv2.rectangle(canvas, (sx_min, sy_min), (sx_max, sy_max), box_color, 2)
                cv2.rectangle(canvas, (sx_min, max(0, sy_min - 30)), (sx_min + 150, sy_min), box_color, -1)
                cv2.putText(canvas, role_label, (sx_min + 8, sy_min - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # 5. Render PiP Camera Mini di Atas
        if self.show_pip:
            pip_w = int(screen_w * 0.20)
            pip_h = int(pip_w * (cam_h / cam_w))
            pip_cam = cv2.resize(cam_frame, (pip_w, pip_h))

            margin = 20
            pip_x1 = screen_w - pip_w - margin
            pip_y1 = margin
            pip_x2 = pip_x1 + pip_w
            pip_y2 = pip_y1 + pip_h

            border_color = (0, 0, 255) if self.is_paused else (255, 255, 255)
            cv2.rectangle(canvas, (pip_x1 - 3, pip_y1 - 3), (pip_x2 + 3, pip_y2 + 3), border_color, 3)
            canvas[pip_y1:pip_y2, pip_x1:pip_x2] = pip_cam

        cv2.imshow(self.window_name, canvas)

    def is_closed(self):
        try:
            return cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) < 1
        except cv2.error:
            return True

    def close(self):
        if self.video_cap is not None:
            self.video_cap.release()
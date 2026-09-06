"""Existing OpenCV stage: cached backgrounds, wayang, cutscenes and operator HUD."""
import cv2
import numpy as np
from asset_manager import BACKGROUNDS
from effect_animator import EffectAnimator

HELP_LINES = [
    "TAB: Bank 1/2       1-5: Manual pose (both characters)",
    "G: Return to finger poses    [: Previous BG    ]: Next BG",
    "F1-F5: Background 1-5",
    "Z X C V B: Sound 1-5         M: Stop sound",
    "6 7 8 9 0: Video 1-5        ESC: Skip video / Quit outside video",
    "R: Run mode       LEFT / RIGHT (hold): Move Nando",
    "K: Football       T: Sleep       H: Pelukan",
    "SPACE: Pause/resume (animation + audio + video)",
    "F: Fullscreen     W: Webcam preview     D: Hand boxes",
    "U: HUD            F12 or ?: Help        Q: Quit",
    "Voice: taman, rumah, sekolah, kelas, koridor (backgrounds)",
]


def fit_image(image, size, cover=False):
    w, h = size
    ih, iw = image.shape[:2]
    scale = (max if cover else min)(w/iw, h/ih)
    resized = cv2.resize(image, (max(1, round(iw*scale)), max(1, round(ih*scale))))
    rh, rw = resized.shape[:2]
    if cover:
        x, y = max(0, (rw-w)//2), max(0, (rh-h)//2)
        return resized[y:y+h, x:x+w].copy()
    canvas = np.zeros((h, w, 3), np.uint8)
    x, y = (w-rw)//2, (h-rh)//2
    canvas[y:y+rh, x:x+rw] = resized[:, :, :3]
    return canvas


class WhiteboardRenderer:
    def __init__(self, assets, window_name="Wayang Digital", create_window=True):
        self.assets = assets
        self.window_name = window_name
        self.effects = EffectAnimator(assets)
        self.create_window = create_window
        self.bg_cache = {}
        self.previous_bg = None
        self.bg_changed_at = 0.0
        self.bg_index = None
        if create_window:
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
            cv2.resizeWindow(window_name, 1280, 720)
            self.set_fullscreen(True)

    def set_fullscreen(self, enabled):
        if self.create_window:
            cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN,
                                  cv2.WINDOW_FULLSCREEN if enabled else cv2.WINDOW_NORMAL)

    def _background(self, state, size):
        key = (state.current_bg, size)
        if key not in self.bg_cache:
            self.bg_cache[key] = fit_image(self.assets.images[BACKGROUNDS[state.current_bg]], size, True)
            if len(self.bg_cache) > 10:
                self.bg_cache = {key: self.bg_cache[key]}
        bg = self.bg_cache[key]
        if self.bg_index != state.current_bg:
            old = self.bg_cache.get((self.bg_index, size))
            self.previous_bg = old
            self.bg_index, self.bg_changed_at = state.current_bg, state.clock
        progress = min(1.0, (state.clock-self.bg_changed_at)/0.4)
        if self.previous_bg is not None and self.previous_bg.shape == bg.shape and progress < 1:
            return cv2.addWeighted(self.previous_bg, 1-progress, bg, progress, 0)
        return bg.copy()

    @staticmethod
    def panel(canvas, lines, origin=(12, 12), scale=0.48):
        x, y = origin
        line_h = max(20, int(36*scale))
        width = max(cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)[0][0] for line in lines)+20
        x2, y2 = min(canvas.shape[1], x+width), min(canvas.shape[0], y+line_h*len(lines)+12)
        roi = canvas[y:y2, x:x2]
        roi[:] = (roi*0.22).astype(np.uint8)
        for i, line in enumerate(lines):
            cv2.putText(canvas, line, (x+8, y+line_h*(i+1)), cv2.FONT_HERSHEY_SIMPLEX,
                        scale, (240, 245, 245), 1, cv2.LINE_AA)

    def render(self, screen_res, cam_frame, hand_boxes, state, audio, video):
        w, h = screen_res
        canvas = self._background(state, screen_res)
        if video.video_playing and video.frame is not None:
            canvas = fit_image(video.frame, screen_res)
        else:
            self.effects.render(canvas, state)
            if video.fade_frame is not None:
                alpha = min(1.0, video.fade_remaining/0.45)
                canvas = cv2.addWeighted(fit_image(video.fade_frame, screen_res), alpha, canvas, 1-alpha, 0)
            if state.show_box and cam_frame is not None:
                ch, cw = cam_frame.shape[:2]
                for item in hand_boxes:
                    x1, y1, x2, y2 = item["box"]
                    cv2.rectangle(canvas, (round(x1*w/cw), round(y1*h/ch)),
                                  (round(x2*w/cw), round(y2*h/ch)), (0, 200, 255), 2)
            if state.show_pip and cam_frame is not None:
                pip_w = max(1, int(w*0.20))
                pip_h = max(1, min(h-40, int(pip_w*cam_frame.shape[0]/cam_frame.shape[1])))
                preview = cv2.resize(cam_frame, (pip_w, pip_h))
                x, y = w-pip_w-20, 20
                canvas[y:y+pip_h, x:x+pip_w] = preview
                cv2.rectangle(canvas, (x, y), (x+pip_w, y+pip_h),
                              (0, 0, 255) if state.paused else (255, 255, 255), 2)
        if state.show_hud:
            sound = audio.current_sound
            lines = [
                f"BANK: {state.animation_bank}/2   BG: {state.current_bg+1}/5   {'PAUSED' if state.paused else 'LIVE'}",
                f"POSE NANDO: {state.characters['Right'].pose}   IBU: {state.characters['Left'].pose}   {'MANUAL (G: gesture)' if state.manual_pose else 'GESTURE'}",
                f"RUN: {'ON' if state.run_mode else 'OFF'}   SLEEP: {'ON' if state.sleep_mode else 'OFF'}   BALL: {'PLAYING' if state.football_active else 'READY'}",
                f"AUDIO: {sound.stem if sound else 'NONE'}",
                f"VIDEO: {video.current_video.stem if video.current_video else 'NONE'}",
                f"ENDING: {'PELUKAN' if state.hug_mode else 'OFF'}   F12: HELP",
            ]
            self.panel(canvas, lines, scale=max(0.35, min(0.55, w/2400)))
        if state.show_help:
            self.panel(canvas, HELP_LINES, (12, max(155, h//3)), max(0.35, min(0.58, w/2000)))
        if self.create_window:
            cv2.imshow(self.window_name, canvas)
        return canvas

    def is_closed(self):
        if not self.create_window:
            return False
        try:
            return cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) < 1
        except cv2.error:
            return True

    def close(self):
        if self.create_window:
            try:
                cv2.destroyWindow(self.window_name)
            except cv2.error:
                pass

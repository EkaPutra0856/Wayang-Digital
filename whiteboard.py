"""Existing OpenCV stage: cached backgrounds, wayang, cutscenes and operator HUD."""
import cv2
import numpy as np
from asset_manager import BACKGROUNDS
from effect_animator import EffectAnimator
from animation_controller import CURTAIN_CLOSE, CURTAIN_OPEN

HELP_LINES = [
    "TAB: Bank 1/2       1-5: Manual pose (both characters)",
    "G: Return to finger poses    [: Previous BG    ]: Next BG",
    "F1-F5: Background 1-5",
    "Z X C V B: Sound 1-5         M: Stop sound",
    "6 7 8 9: Video + BG + song 1/2/4/5   ESC: Skip / Quit",
    "R: Run mode       LEFT / RIGHT (hold): Move Nando",
    "K: Football       T: Sleep       H: Pelukan",
    "P: Curtain        L: Lock size + horizontal only    S: Balance size",
    "Y: Nando costume MANUAL     J: AUTO (BG1-2 SPORT, BG3-5 SCHOOL)",
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
        self.curtain_texture = None
        if create_window:
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
            cv2.resizeWindow(window_name, 1280, 720)
            self.set_fullscreen(True)

    def set_fullscreen(self, enabled):
        if self.create_window:
            cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN,
                                  cv2.WINDOW_FULLSCREEN if enabled else cv2.WINDOW_NORMAL)

    def render_curtain(self, canvas, state):
        if state.curtain_phase == 'idle':
            return
        h, w = canvas.shape[:2]
        half = (w+1)//2
        if self.curtain_texture is None or self.curtain_texture.shape[:2] != (h, half):
            # Procedural fabric folds, no new external image asset.
            x = np.linspace(0, 12*np.pi, half, dtype=np.float32)
            shade = (0.65 + 0.25*np.cos(x) + 0.1*np.cos(2*x))[None, :, None]
            vertical = np.linspace(1.0, 0.7, h, dtype=np.float32)[:, None, None]
            self.curtain_texture = (shade*vertical*np.array([40, 30, 150])).astype(np.uint8)
        alpha = 1.0
        if state.curtain_phase == 'closing':
            progress = min(1.0, state.curtain_timer/CURTAIN_CLOSE)
            amount = progress*progress*(3-2*progress)
        elif state.curtain_phase == 'opening':
            progress = min(1.0, state.curtain_timer/CURTAIN_OPEN)
            amount = 1-progress*progress*(3-2*progress)
            alpha = 1-progress
        else:
            amount = 1.0
        count = min(half, max(0, round(half*amount)))
        if count:
            left = self.curtain_texture[:, half-count:]
            right = left[:, ::-1]
            canvas[:, :count] = (left*alpha+canvas[:, :count]*(1-alpha)).astype(np.uint8)
            canvas[:, w-count:] = (right*alpha+canvas[:, w-count:]*(1-alpha)).astype(np.uint8)

    @staticmethod
    def ui_text(card, text, x, y, size=0.52, color=(210, 218, 230)):
        cv2.putText(card, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX,
                    size, color, 1, cv2.LINE_AA)

    @staticmethod
    def place_card(canvas, card, x, y, scale):
        card = cv2.resize(card, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        h, w = card.shape[:2]
        roi = canvas[y:y+h, x:x+w]
        roi[:] = cv2.addWeighted(roi, 0.05, card, 0.95, 0)

    def render_ui(self, canvas, state, audio, video):
        if not state.show_hud:
            return
        h, w = canvas.shape[:2]
        scale = min(w/1280, h/720)
        put = self.ui_text
        if state.show_help:
            card = np.full((600, 1100, 3), (27, 23, 20), np.uint8)
            cv2.rectangle(card, (0, 0), (1099, 599), (92, 76, 48), 1)
            cv2.rectangle(card, (0, 0), (6, 599), (130, 200, 245), -1)
            put(card, 'PANDUAN PANGGUNG', 28, 40, .88, (240, 245, 250))
            put(card, 'Wayang Interaktif  |  Nando & Ibu', 29, 66, .49)
            put(card, 'F12  Tutup panduan     U  Sembunyikan UI', 675, 42, .48, (130, 200, 245))
            cv2.line(card, (28, 85), (1072, 85), (65, 58, 48), 1)
            groups = [
                ('01  KARAKTER & KOSTUM', [
                    'I+1-5  Ibu   N+1-5  Nando   TAB  Bank',
                    'Ulang kombinasi: hide   G: mode jari',
                    'Y  Ganti kostum manual     J  Kostum AUTO',
                    'AUTO: BG1-2 SPORT / BG3-5 SCHOOL']),
                ('02  LATAR & MEDIA', [
                    '[ / ]  Latar sebelumnya / berikutnya',
                    'F1-F5  Pilih latar langsung',
                    'Z X C V B  Audio 1-5     M  Stop audio',
                    '6 7 8 9  Video + BG/lagu 1/2/4/5']),
                ('03  ANIMASI KHUSUS', [
                    'R  Lari looping     Panah  Arah & gerak',
                    'K  Tendang bola     T  Tidur / istirahat',
                    'H  Pelukan (audio dipilih terpisah)',
                    'P  Curtain: tutup, tahan 0.5 dtk, buka']),
                ('04  KONTROL TAMPILAN', [
                    'SPACE  Pause / resume seluruh animasi',
                    'F  Fullscreen     W  Preview webcam',
                    'U  Show / hide UI     D  Kotak deteksi',
                    'F12 atau ?  Panduan     Q  Keluar']),
                ('05  UKURAN & VISIBILITAS', [
                    'L  Kunci ukuran + tinggi; gerak kiri-kanan',
                    'S  Seimbangkan ukuran, lalu kunci',
                    'Tangan hilang: fade-out 0.35 detik',
                    'Tangan kembali: fade-in kostum aktif']),
                ('06  CARA MEMAINKAN', [
                    'Tangan kanan: Nando / tangan kiri: Ibu',
                    'Tahan pose jari sebentar agar stabil',
                    'Lepas panah: diam di tempat, lari tetap loop',
                    'Slot pose kosong: tahan pose sebelumnya']),
            ]
            for i, (title, lines) in enumerate(groups):
                x = 29+(i % 2)*540
                y = 119+(i//2)*151
                put(card, title, x, y, .53, (130, 200, 245))
                for j, line in enumerate(lines):
                    put(card, line, x, y+27+j*24, .48)
            put(card, 'Klik window Wayang untuk fokus keyboard. Tekan dan lepaskan tombol toggle sebelum mengulang.',
                29, 580, .46, (160, 169, 182))
            self.place_card(canvas, card, round((w-1100*scale)/2), round((h-600*scale)/2), scale)
            return
        card = np.full((260, 390, 3), (27, 23, 20), np.uint8)
        cv2.rectangle(card, (0, 0), (389, 259), (92, 76, 48), 1)
        cv2.rectangle(card, (0, 0), (4, 259), (130, 200, 245), -1)
        put(card, 'WAYANG  /  OPERATOR', 17, 30, .60, (240, 245, 250))
        put(card, 'PAUSED' if state.paused else 'LIVE', 300, 30, .49,
            (100, 180, 255) if state.paused else (160, 230, 130))
        put(card, f'BG {state.current_bg+1}/5  |  BANK {state.animation_bank}/2  |  '+
            ('POSE MANUAL' if state.manual_pose else 'GESTURE'), 17, 59, .45)
        cv2.line(card, (17, 71), (373, 71), (65, 58, 48), 1)
        sound = audio.current_sound
        rows = [
            f'Kostum   {state.nando_costume} / {state.costume_mode}',
            f'Pose      Nando {state.characters["Right"].pose}   Ibu {state.characters["Left"].pose}',
            f'Run {"ON" if state.run_mode else "OFF"}   Sleep {"ON" if state.sleep_mode else "OFF"}   Ball {"PLAY" if state.football_active else "READY"}',
            f'Lock {"ON" if state.scale_locked else "OFF"}   Balance {"PENDING" if any(c.balance_pending for c in state.characters.values()) else "READY"}   Hug {"ON" if state.hug_mode else "OFF"}',
            'Audio  '+(sound.stem[:35] if sound else 'NONE'),
            'Video  '+(video.current_video.stem[:35] if video.current_video else 'NONE'),
        ]
        for i, line in enumerate(rows):
            put(card, line, 17, 95+i*23, .46)
        put(card, 'F12  Panduan penggunaan     U  Hide UI', 17, 246, .44, (130, 200, 245))
        self.place_card(canvas, card, round(14*scale), round(14*scale), scale)

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
        self.render_ui(canvas, state, audio, video)
        self.render_curtain(canvas, state)
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

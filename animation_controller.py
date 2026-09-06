"""Deterministic show state; no camera, audio device or window required."""
from dataclasses import dataclass, field
import math
from asset_manager import NANDO_COSTUMES, NANDO_SLEEP, IBU

RUN_SPEED = 420.0
RUN_FPS = 10.0
GRAVITY = 900.0
FOOTBALL_DURATIONS = (0.25, 0.35, 0.35, 0.16, 1.6, 0.3)
HAND_FADE_SECONDS = 0.35
BALANCED_HEIGHT = 0.46
CURTAIN_CLOSE = 0.35
CURTAIN_HOLD = 0.5
CURTAIN_OPEN = 0.65


@dataclass
class Character:
    pose: int = 1
    x: float = 0.5
    y: float = 0.88  # feet, normalized to canvas
    height: float = 0.46
    candidate: int = 0
    candidate_time: float = 0.0
    alpha: float = 0.0
    balance_pending: bool = False


@dataclass
class Ball:
    active: bool = False
    x: float = 0.0
    y: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    angle: float = 0.0
    angular_velocity: float = 480.0


@dataclass
class AnimationController:
    animation_bank: int = 1
    current_bg: int = 0
    characters: dict = field(default_factory=lambda: {
        "Right": Character(x=0.65), "Left": Character(x=0.32)})
    manual_pose: bool = False
    run_mode: bool = False
    run_frame: int = 0
    run_timer: float = 0.0
    nando_facing: int = 1
    football_active: bool = False
    football_state: int = 0
    football_timer: float = 0.0
    ball: Ball = field(default_factory=Ball)
    sleep_mode: bool = False
    sleep_start_time: float = 0.0
    hug_mode: bool = False
    hug_alpha: float = 0.0
    paused: bool = False
    fullscreen: bool = True
    show_pip: bool = True
    show_help: bool = False
    show_hud: bool = False
    show_box: bool = False
    clock: float = 0.0
    keyboard_preview: bool = False
    scale_locked: bool = False
    curtain_phase: str = 'idle'
    curtain_timer: float = 0.0
    nando_costume: str = 'SPORT'
    costume_mode: str = 'AUTO'
    last_costume_pose: dict = field(default_factory=lambda: {'SCHOOL': 1, 'SPORT': 1})

    def __post_init__(self):
        self.apply_costume_for_background()

    def set_background(self, index):
        """All background sources (keyboard, voice and internal scenes) use this entry point."""
        if not 0 <= index < 5:
            raise ValueError(f'Invalid background index: {index}')
        self.current_bg = index
        self.apply_costume_for_background()

    def set_nando_costume(self, costume, mode=None):
        if costume not in NANDO_COSTUMES or (mode is not None and mode not in ('AUTO', 'MANUAL')):
            raise ValueError('Invalid Nando costume/mode')
        previous = (self.nando_costume, self.costume_mode)
        char = self.characters['Right']
        self.last_costume_pose[self.nando_costume] = char.pose
        self.nando_costume = costume
        if mode is not None:
            self.costume_mode = mode
        if not 1 <= char.pose <= len(NANDO_COSTUMES[costume]):
            char.pose = self.last_costume_pose[costume]
            if not 1 <= char.pose <= len(NANDO_COSTUMES[costume]):
                char.pose = 6 if self.animation_bank == 2 else 1
        self.last_costume_pose[costume] = char.pose
        if previous != (self.nando_costume, self.costume_mode):
            print(f'[COSTUME] {costume} ({self.costume_mode}, BG{self.current_bg+1})')

    def toggle_nando_costume(self):
        self.set_nando_costume('SCHOOL' if self.nando_costume == 'SPORT' else 'SPORT', 'MANUAL')

    def set_costume_auto(self):
        self.set_nando_costume('SPORT' if self.current_bg < 2 else 'SCHOOL', 'AUTO')

    def apply_costume_for_background(self):
        if self.costume_mode == 'AUTO':
            self.set_costume_auto()

    def get_nando_pose(self, sleeping=False):
        if sleeping:
            return NANDO_SLEEP[self.nando_costume]
        return NANDO_COSTUMES[self.nando_costume][self.characters['Right'].pose-1]

    def toggle_scale_lock(self):
        self.scale_locked = not self.scale_locked
        for char in self.characters.values():
            char.balance_pending = False
            if self.scale_locked:
                char.height = min(0.65, max(0.25, char.height))
                char.y = min(0.98, max(char.height, char.y))
        print(f"[SCALE LOCK] {'ON' if self.scale_locked else 'OFF'}")

    def balance_scale(self):
        self.scale_locked = True
        for char in self.characters.values():
            char.balance_pending = True
        print('[SCALE] Balance to 46% stage height when hands are detected; lock ON')

    def start_curtain(self):
        if self.paused or self.curtain_phase != 'idle':
            return False
        self.curtain_phase, self.curtain_timer = 'closing', 0.0
        return True

    def update_curtain(self, dt):
        if self.curtain_phase == 'idle':
            return
        self.curtain_timer += dt
        durations = {'closing': CURTAIN_CLOSE, 'closed': CURTAIN_HOLD, 'opening': CURTAIN_OPEN}
        next_phase = {'closing': 'closed', 'closed': 'opening', 'opening': 'idle'}
        while self.curtain_phase != 'idle' and self.curtain_timer >= durations[self.curtain_phase]:
            self.curtain_timer -= durations[self.curtain_phase]
            self.curtain_phase = next_phase[self.curtain_phase]
        if self.curtain_phase == 'idle':
            self.curtain_timer = 0.0

    def toggle_bank(self):
        self.animation_bank = 3 - self.animation_bank
        print(f"[MODE] Animation Bank -> {self.animation_bank}")

    def select_pose(self, finger, label=None):
        pose = (self.animation_bank - 1) * 5 + finger
        changed = False
        if 1 <= finger <= 5:
            for name in ([label] if label else self.characters):
                limit = len(NANDO_COSTUMES[self.nando_costume]) if name == 'Right' else len(IBU)
                if not 1 <= pose <= limit:
                    continue
                self.characters[name].pose = pose
                if name == 'Right':
                    self.last_costume_pose[self.nando_costume] = pose
                changed = True
        return changed  # Empty slots independently hold each character's last valid pose.

    def debug_pose(self, finger):
        self.manual_pose = True
        self.select_pose(finger)

    def start_football(self):
        if self.football_active or self.hug_mode or self.paused:
            return False
        self.football_active = True
        self.football_state = 0
        self.football_timer = 0.0
        self.ball = Ball()
        print("[FOOTBALL] Kick started")
        return True

    def update(self, dt, hands=(), cam_res=(640, 480), screen_res=(1280, 720),
               direction=0, video_playing=False, run_half_width=0.1):
        if self.paused:
            return
        dt = max(0.0, min(dt, 0.1))
        self.update_curtain(dt)
        if video_playing:
            return
        self.clock += dt
        detected = {item['label'] for item in hands}
        for label, char in self.characters.items():
            visible = label in detected or self.keyboard_preview
            char.alpha = max(0.0, min(1.0, char.alpha + dt/HAND_FADE_SECONDS*(1 if visible else -1)))
            if not visible:
                char.candidate, char.candidate_time = 0, 0.0
        self.hug_alpha = max(0.0, min(1.0, self.hug_alpha + dt * (2 if self.hug_mode else -2)))
        if self.hug_mode or self.hug_alpha > 0:
            return
        cam_w, cam_h = cam_res
        for item in hands:
            label = item["label"]
            char = self.characters[label]
            override = label == "Right" and (self.run_mode or self.football_active)
            if not override and not self.sleep_mode:
                x1, y1, x2, y2 = item["box"]
                smooth = 1 - math.exp(-14 * dt)
                char.x += ((x1+x2)/2/cam_w - char.x) * smooth
                if char.balance_pending:
                    char.y += (0.88-char.y)*smooth
                    char.height += (BALANCED_HEIGHT-char.height)*smooth
                    if abs(char.height-BALANCED_HEIGHT) < 0.001 and abs(char.y-0.88) < 0.001:
                        char.height, char.y, char.balance_pending = BALANCED_HEIGHT, 0.88, False
                elif not self.scale_locked:
                    char.y += (y2/cam_h - char.y) * smooth
                    char.height += (min(0.8, max(0.18, (y2-y1)*1.5/cam_h))-char.height)*smooth
            if not self.manual_pose and not self.sleep_mode and not (label == "Right" and self.football_active):
                finger = item["count"]
                if char.candidate != finger:
                    char.candidate, char.candidate_time = finger, 0.0
                else:
                    char.candidate_time += dt
                if char.candidate_time >= 0.12:
                    self.select_pose(finger, label)

        nando = self.characters["Right"]
        w, h = screen_res
        if self.football_active:
            self.football_timer += dt
            while self.football_active and self.football_timer >= FOOTBALL_DURATIONS[self.football_state]:
                self.football_timer -= FOOTBALL_DURATIONS[self.football_state]
                self.football_state += 1
                if self.football_state == 4:
                    self.ball = Ball(True, nando.x*w + self.nando_facing*nando.height*h*0.28,
                                     nando.y*h - nando.height*h*0.25,
                                     self.nando_facing*550.0, -420.0,
                                     angular_velocity=self.nando_facing*480.0)
                elif self.football_state >= len(FOOTBALL_DURATIONS):
                    self.football_active = False
                    self.ball.active = False
            if self.ball.active:
                b = self.ball
                b.x += b.vx*dt
                b.y += b.vy*dt + GRAVITY*dt*dt/2
                b.vy += GRAVITY*dt
                b.angle = (b.angle + b.angular_velocity*dt) % 360
                if b.x < -60 or b.x > w+60 or b.y > h-20:
                    b.active = False
        elif not self.sleep_mode and self.run_mode:
            # Running is an active mode, not a key-repeat animation. Keep a bounded
            # continuous phase through the final frame and while arrows are released.
            self.run_timer = (self.run_timer + dt) % (5 / RUN_FPS)
            self.run_frame = int(self.run_timer * RUN_FPS) % 5
            if direction:
                self.nando_facing = 1 if direction > 0 else -1
                nando.x += direction * RUN_SPEED * dt / w
            margin = min(0.49, run_half_width)
            nando.x = min(1-margin, max(margin, nando.x))

"""Deterministic show state; no camera, audio device or window required."""
from dataclasses import dataclass, field
import math

RUN_SPEED = 420.0
RUN_FPS = 10.0
GRAVITY = 900.0
FOOTBALL_DURATIONS = (0.25, 0.35, 0.35, 0.16, 1.6, 0.3)


@dataclass
class Character:
    pose: int = 1
    x: float = 0.5
    y: float = 0.88  # feet, normalized to canvas
    height: float = 0.46
    candidate: int = 0
    candidate_time: float = 0.0


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
    show_hud: bool = True
    show_box: bool = False
    clock: float = 0.0

    def toggle_bank(self):
        self.animation_bank = 3 - self.animation_bank
        print(f"[MODE] Animation Bank -> {self.animation_bank}")

    def select_pose(self, finger, label=None):
        pose = (self.animation_bank - 1) * 5 + finger
        if 1 <= finger <= 5 and 1 <= pose <= 8:
            for name in ([label] if label else self.characters):
                self.characters[name].pose = pose
            return True
        return False  # Empty slots and closed fist hold the last valid pose.

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
        if self.paused or video_playing:
            return
        dt = max(0.0, min(dt, 0.1))
        self.clock += dt
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
            if direction:
                self.nando_facing = 1 if direction > 0 else -1
                nando.x += direction * RUN_SPEED * dt / w
                self.run_timer += dt
                self.run_frame = int(self.run_timer * RUN_FPS) % 5
            margin = min(0.49, run_half_width)
            nando.x = min(1-margin, max(margin, nando.x))

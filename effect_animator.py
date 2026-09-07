"""Special visuals using only the FIX ASSET manifest."""
import math
import cv2
import numpy as np
from asset_manager import IBU, RUN, FOOTBALL, HUG

IBU_SCALE = 1  


def overlay(canvas, sprite, center_x, feet_y, alpha=1.0):
    """BGRA over BGR, clipped at all four screen edges."""
    sh, sw = sprite.shape[:2]
    x, y = round(center_x-sw/2), round(feet_y-sh)
    h, w = canvas.shape[:2]
    x1, y1, x2, y2 = max(0, x), max(0, y), min(w, x+sw), min(h, y+sh)
    if x1 >= x2 or y1 >= y2:
        return
    src = sprite[y1-y:y2-y, x1-x:x2-x]
    dst = canvas[y1:y2, x1:x2]
    a = src[:, :, 3:4].astype(np.float32) * (alpha/255.0)
    dst[:] = (src[:, :, :3]*a + dst*(1-a)).astype(np.uint8)


class EffectAnimator:
    def __init__(self, assets):
        self.assets = assets

    def character_sprite(self, state, label, screen_h):
        char = state.characters[label]
        path = state.get_nando_pose() if label == "Right" else IBU[char.pose-1]
        flip = False
        breath = 1.0
        if label == "Right" and state.football_active:
            path = FOOTBALL[(0, 1, 2, 3, 4, 0)[state.football_state]]
            flip = state.nando_facing < 0
        elif state.sleep_mode:
            path = state.get_nando_pose(sleeping=True) if label == "Right" else IBU[5]
            breath = 1 + math.sin((state.clock-state.sleep_start_time)*2)*0.015
        elif label == "Right" and state.run_mode:
            path = RUN[state.run_frame]
            flip = state.nando_facing < 0
        elif char.manual_control or state.keyboard_preview:
            # Gentle idle breathing, offset per character so they do not move
            # in sync. The shared clock also freezes this motion when paused.
            phase = 0.0 if label == "Left" else 1.4
            breath = 1 + math.sin(state.clock * (2 * math.pi / 3.6) + phase) * 0.012
        size_scale = IBU_SCALE if label == "Left" else 1.0
        return self.assets.sprite(path, char.height*screen_h*breath*size_scale, flip)

    def render(self, canvas, state):
        h, w = canvas.shape[:2]
        if state.hug_mode or state.hug_alpha > 0:
            src = self.assets.images[HUG]
            target_h = min(h*0.8, w*0.8*src.shape[0]/src.shape[1])
            sprite = self.assets.sprite(HUG, target_h*(0.94+0.06*state.hug_alpha))
            overlay(canvas, sprite, w/2, h*0.94, state.hug_alpha)
            return canvas
        for label in ("Left", "Right"):
            char = state.characters[label]
            sprite = self.character_sprite(state, label, h)
            breathing = state.sleep_mode and not (label == "Right" and state.football_active)
            bob = math.sin((state.clock-state.sleep_start_time)*2)*2 if breathing else 0
            overlay(canvas, sprite, char.x*w, char.y*h+bob, char.alpha)
        if state.ball.active:
            ball = self.assets.sprite(FOOTBALL[5], h*0.12)
            bh, bw = ball.shape[:2]
            size = math.ceil(math.hypot(bw, bh))
            matrix = cv2.getRotationMatrix2D((bw/2, bh/2), -state.ball.angle, 1)
            matrix[:, 2] += ((size-bw)/2, (size-bh)/2)
            rotated = cv2.warpAffine(ball, matrix, (size, size), borderValue=(0, 0, 0, 0))
            overlay(canvas, rotated, state.ball.x, state.ball.y+size/2)
        return canvas

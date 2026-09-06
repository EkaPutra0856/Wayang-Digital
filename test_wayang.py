"""Regression tests for real state transitions and offscreen compositing."""
import unittest
from types import SimpleNamespace
import numpy as np
from animation_controller import AnimationController, RUN_SPEED
from asset_manager import AssetManager, NANDO, IBU, RUN, FOOTBALL, SOUNDS, VIDEOS
from audio_manager import AudioManager
from keyboard_controller import KeyboardController
from main import handle_keys
from whiteboard import WhiteboardRenderer, fit_image
from effect_animator import overlay


class StateTests(unittest.TestCase):
    def test_all_banks_and_empty_slots_hold_last_pose(self):
        state = AnimationController()
        for bank in (1, 2):
            state.animation_bank = bank
            for finger in range(1, 6):
                previous = state.characters['Right'].pose
                state.debug_pose(finger)
                expected = (bank-1)*5+finger
                for char in state.characters.values():
                    self.assertEqual(char.pose, expected if expected <= 8 else previous)

    def test_hand_mapping_and_manual_override(self):
        state = AnimationController()
        hands = [{'label': 'Right', 'box': (400, 100, 500, 350), 'count': 3},
                 {'label': 'Left', 'box': (100, 100, 200, 350), 'count': 5}]
        for _ in range(10):
            state.update(0.03, hands)
        self.assertEqual(state.characters['Right'].pose, 3)
        self.assertEqual(state.characters['Left'].pose, 5)
        state.debug_pose(2)
        for _ in range(10):
            state.update(0.03, hands)
        self.assertEqual(state.characters['Right'].pose, 2)
        state.manual_pose = False
        state.update(0.03, hands)
        self.assertEqual(state.characters['Right'].pose, 3)

    def test_run_time_step_release_and_boundaries(self):
        positions = []
        for dt in (1/30, 1/60):
            state = AnimationController(run_mode=True)
            state.characters['Right'].x = .2
            for _ in range(round(1/dt)):
                state.update(dt, direction=1)
            positions.append(state.characters['Right'].x)
            self.assertAlmostEqual(positions[-1], .2+RUN_SPEED/1280)
            frame, x = state.run_frame, positions[-1]
            state.update(.1)
            self.assertEqual((state.run_frame, state.characters['Right'].x), (frame, x))
            for _ in range(100):
                state.update(.1, direction=-1, run_half_width=.13)
            self.assertEqual(state.characters['Right'].x, .13)
            self.assertEqual(state.nando_facing, -1)
        self.assertAlmostEqual(*positions)

    def test_football_once_physics_both_directions_and_replay(self):
        for facing in (-1, 1):
            state = AnimationController(nando_facing=facing)
            self.assertTrue(state.start_football())
            self.assertFalse(state.start_football())
            observed = set()
            for _ in range(150):
                observed.add(state.football_state)
                state.update(1/30)
                if state.ball.active:
                    self.assertEqual(1 if state.ball.vx > 0 else -1, facing)
                    self.assertNotEqual(state.ball.angle, 0)
            self.assertTrue(set(range(6)).issubset(observed))
            self.assertFalse(state.football_active)
            self.assertFalse(state.ball.active)
            self.assertTrue(state.start_football())

    def test_pause_and_visual_priority(self):
        state = AnimationController(run_mode=True)
        state.start_football()
        state.update(.1)
        state.paused = True
        before = repr(state)
        state.update(.1, direction=1)
        self.assertEqual(repr(state), before)
        state.paused = False
        before = repr(state)
        state.update(.1, direction=1, video_playing=True)
        self.assertEqual(repr(state), before)
        state.hug_mode = True
        timer = state.football_timer
        state.update(.1)
        self.assertEqual(state.football_timer, timer)

    def test_held_toggle_key_needs_release(self):
        keyboard = KeyboardController()
        keyboard.edges(set())
        self.assertEqual(keyboard.edges({'R'})[0], {'R'})
        for _ in range(60):
            self.assertFalse(keyboard.edges({'R'})[0])
        keyboard.edges(set())
        self.assertEqual(keyboard.edges({'R'})[0], {'R'})
        self.assertFalse(keyboard.edges({'R'}, False)[1])
        self.assertFalse(keyboard.edges({'R'}, True)[0])


class AudioTests(unittest.TestCase):
    def setUp(self):
        self.audio = AudioManager(SimpleNamespace(tracks={
            SOUNDS[0]: np.ones((100, 2), np.int16),
            SOUNDS[1]: np.full((100, 2), 2, np.int16)}), open_device=False)

    def test_duplicate_replace_pause_completion_and_replay(self):
        self.assertTrue(self.audio.play(SOUNDS[0]))
        out = np.zeros((40, 2), np.int16)
        self.audio._callback(out, 40, None, None)
        self.assertTrue(np.all(out == 1))
        self.assertFalse(self.audio.play(SOUNDS[0]))
        self.assertEqual(self.audio.playback.cursor, 40)
        self.audio.set_paused(True)
        self.audio._callback(out, 40, None, None)
        self.assertEqual(self.audio.playback.cursor, 40)
        self.assertTrue(np.all(out == 0))
        self.audio.set_paused(False)
        self.assertTrue(self.audio.play(SOUNDS[1]))
        self.audio._callback(out, 40, None, None)
        self.assertTrue(np.all(out == 2))
        for _ in range(2):
            self.audio._callback(out, 40, None, None)
        self.assertFalse(self.audio.sound_playing)
        self.assertTrue(self.audio.play(SOUNDS[1]))
        self.audio.stop()
        self.assertIsNone(self.audio.current_sound)

    def test_cutscene_blocks_other_modes_and_sound(self):
        state = AnimationController()
        board = SimpleNamespace(set_fullscreen=lambda enabled: None)
        video = SimpleNamespace(video_playing=True)
        handle_keys({'R', 'K', 'T', 'H', 'Z', '1'}, state, board, self.audio, video)
        self.assertFalse(state.run_mode or state.football_active or state.sleep_mode or state.hug_mode)
        self.assertIsNone(self.audio.current_sound)
        handle_keys({'SPACE'}, state, board, self.audio, video)
        self.assertTrue(state.paused)


class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assets = AssetManager()

    def test_alpha_and_aspect(self):
        canvas = np.full((10, 10, 3), 100, np.uint8)
        sprite = np.zeros((4, 4, 4), np.uint8)
        sprite[:, :, :3] = 200
        overlay(canvas, sprite, 5, 7)
        self.assertTrue(np.all(canvas == 100))
        sprite[:, :, 3] = 128
        overlay(canvas, sprite, 0, 2)
        self.assertGreater(canvas[0, 0, 0], 100)
        source = np.full((100, 200, 3), 255, np.uint8)
        fitted = fit_image(source, (100, 100))
        self.assertTrue(np.all(fitted[:25] == 0))
        self.assertTrue(np.all(fitted[25:75] == 255))

    def test_all_poses_and_special_modes_render(self):
        state = AnimationController()
        board = WhiteboardRenderer(self.assets, create_window=False)
        audio = SimpleNamespace(current_sound=None)
        video = SimpleNamespace(video_playing=False, fade_frame=None, current_video=None)
        for bank in (1, 2):
            state.animation_bank = bank
            for finger in range(1, 6):
                state.debug_pose(finger)
                frame = board.render((960, 540), None, [], state, audio, video)
                self.assertEqual(frame.shape, (540, 960, 3))
        for mode in ('run_mode', 'sleep_mode', 'hug_mode'):
            setattr(state, mode, True)
            state.update(.1)
            self.assertTrue(board.render((960, 540), None, [], state, audio, video).any())
            setattr(state, mode, False)
        state.hug_alpha = 0
        state.start_football()
        for _ in range(100):
            state.update(1/30)
            board.render((960, 540), None, [], state, audio, video)
        # Actual sprite selection uses production pose IDs and inspected sleep poses.
        state.sleep_mode = True
        self.assertEqual(board.effects.character_sprite(state, 'Right', 540).shape[2], 4)


if __name__ == '__main__':
    unittest.main(verbosity=2)

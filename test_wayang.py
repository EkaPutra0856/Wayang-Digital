"""Regression tests for real state transitions and offscreen compositing."""
import unittest
from types import SimpleNamespace
import numpy as np
from animation_controller import AnimationController, RUN_SPEED
from asset_manager import AssetManager, NANDO, NANDO_SPORT, IBU, RUN, FOOTBALL, SOUNDS, VIDEOS
from audio_manager import AudioManager
from keyboard_controller import KeyboardController
from main import handle_keys
from whiteboard import WhiteboardRenderer, fit_image
from effect_animator import overlay


class StateTests(unittest.TestCase):
    def test_manual_curtain_stays_closed_until_next_i(self):
        state = AnimationController()
        video = SimpleNamespace(video_playing=False)
        handle_keys({'I'}, state, None, None, video)
        state.update_curtain(10)
        self.assertEqual(state.curtain_phase, 'closed')
        handle_keys(set(), state, None, None, video, held={'I'})
        self.assertEqual(state.curtain_phase, 'closed')
        handle_keys({'I'}, state, None, None, video)
        state.update_curtain(1)
        self.assertEqual(state.curtain_phase, 'idle')

    def test_independent_bank_keys_and_gesture_mapping(self):
        state = AnimationController()
        video = SimpleNamespace(video_playing=False)
        handle_keys({'A'}, state, None, None, video)
        self.assertEqual(state.animation_banks, {'Right': 2, 'Left': 1})
        state.debug_pose(3)
        self.assertEqual(state.characters['Right'].pose, 8)
        self.assertEqual(state.characters['Left'].pose, 3)
        state.use_gesture()
        hands = [{'label': label, 'count': 2, 'box': (100, 100, 200, 350)}
                 for label in ('Right', 'Left')]
        for _ in range(6):
            state.update(.05, hands)
        self.assertEqual(state.characters['Right'].pose, 7)
        self.assertEqual(state.characters['Left'].pose, 2)
        handle_keys({'E'}, state, None, None, video)
        self.assertEqual(state.animation_banks, {'Right': 2, 'Left': 2})
        handle_keys({'TAB'}, state, None, None, video)
        self.assertEqual(state.animation_banks, {'Right': 2, 'Left': 2})
        handle_keys({'A'}, state, None, None, video)
        self.assertEqual(state.animation_banks, {'Right': 1, 'Left': 2})
        state.paused = True
        handle_keys({'E'}, state, None, None, video)
        self.assertEqual(state.animation_banks, {'Right': 1, 'Left': 2})

    def test_keyboard_visibility_toggle_and_return_to_detection(self):
        state = AnimationController()
        state.debug_pose(3)
        for _ in range(4):
            state.update(.1)
        self.assertTrue(all(c.alpha == 1 for c in state.characters.values()))
        state.debug_pose(3)
        hands = [{'label': label, 'box': (100, 100, 200, 350), 'count': 2}
                 for label in ('Left', 'Right')]
        for _ in range(4):
            state.update(.1, hands)
        self.assertTrue(all(c.alpha == 0 for c in state.characters.values()))
        state.debug_pose(3)
        for _ in range(4):
            state.update(.1)
        self.assertTrue(all(c.alpha == 1 for c in state.characters.values()))
        state.use_gesture()
        for _ in range(4):
            state.update(.1)
        self.assertTrue(all(c.alpha == 0 for c in state.characters.values()))
        for _ in range(4):
            state.update(.1, hands)
        self.assertTrue(all(c.alpha == 1 and c.pose == 2 for c in state.characters.values()))

    def test_keyboard_combo_shows_character_without_prior_hand_detection(self):
        state = AnimationController()
        state.debug_pose(2, 'Right')
        for _ in range(8):
            state.update(.05)
        self.assertEqual(state.characters['Right'].alpha, 1)
        self.assertEqual(state.characters['Left'].alpha, 0)

    def test_missing_hands_fade_independently_and_return(self):
        state = AnimationController()
        hands = [{'label': label, 'box': (100, 100, 200, 350), 'count': 1}
                 for label in ('Left', 'Right')]
        self.assertTrue(all(c.alpha == 0 for c in state.characters.values()))
        for _ in range(12):
            state.update(1/30, hands)
        self.assertTrue(all(c.alpha == 1 for c in state.characters.values()))
        state.update(.1, hands[:1])
        self.assertTrue(0 < state.characters['Right'].alpha < 1)
        self.assertEqual(state.characters['Left'].alpha, 1)
        for _ in range(12):
            state.update(1/30)
        self.assertTrue(all(c.alpha == 0 for c in state.characters.values()))
        state.update(.1, hands)
        self.assertTrue(all(0 < c.alpha < 1 for c in state.characters.values()))

    def test_lock_scale_only_changes_horizontal_position(self):
        state = AnimationController()
        state.toggle_scale_lock()
        char = state.characters['Right']
        original = (char.height, char.y)
        for box in ((0, 0, 600, 480), (20, 30, 40, 80)):
            state.update(.1, [{'label': 'Right', 'box': box, 'count': 1}])
            self.assertEqual((char.height, char.y), original)
        self.assertNotEqual(char.x, .70)
        state.toggle_scale_lock()
        state.update(.1, [{'label': 'Right', 'box': (20, 30, 40, 80), 'count': 1}])
        self.assertNotEqual((char.height, char.y), original)

    def test_gesture_scale_nando_smaller_than_ibu(self):
        state = AnimationController()
        hands = [
            {'label': 'Right', 'box': (100, 50, 220, 350), 'count': 1},
            {'label': 'Left', 'box': (300, 50, 420, 350), 'count': 1},
        ]
        for _ in range(20):
            state.update(.05, hands)
        self.assertLess(state.characters['Right'].height, state.characters['Left'].height)
        self.assertAlmostEqual(state.characters['Right'].height / state.characters['Left'].height,
                               0.80 / 1.25, delta=.03)

    def test_balance_waits_for_each_hand_then_locks(self):
        state = AnimationController()
        state.characters['Right'].height = .75
        state.characters['Left'].height = .20
        state.balance_scale()
        state.update(.1)
        self.assertEqual(state.characters['Right'].height, .75)
        for _ in range(20):
            state.update(.1, [{'label': 'Right', 'box': (0, 0, 600, 480), 'count': 1}])
        self.assertEqual(state.characters['Right'].height, .46)
        self.assertEqual(state.characters['Left'].height, .20)
        self.assertTrue(state.characters['Left'].balance_pending)
        self.assertFalse(state.characters['Right'].balance_pending)
        self.assertTrue(state.scale_locked)

    def test_curtain_hold_pause_and_duplicate(self):
        state = AnimationController()
        self.assertTrue(state.start_curtain())
        self.assertFalse(state.start_curtain())
        for _ in range(7):
            state.update(.05)
        self.assertEqual(state.curtain_phase, 'closed')
        state.paused = True
        state.update(.1)
        self.assertAlmostEqual(state.curtain_timer, 0)
        state.paused = False
        for _ in range(24):
            state.update(.1, video_playing=True)
        self.assertEqual(state.curtain_phase, 'closed')
        state.update(.1)
        self.assertEqual(state.curtain_phase, 'opening')
        for _ in range(7):
            state.update(.1)
        self.assertEqual(state.curtain_phase, 'idle')

    def test_all_banks_and_empty_slots_hold_last_pose(self):
        state = AnimationController()
        state.set_background(2)  # Existing SCHOOL and Ibu mapping remains 8 poses.
        for bank in (1, 2):
            state.animation_banks = {'Right': bank, 'Left': bank}
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
            x = positions[-1]
            state.update(.1)
            self.assertEqual(state.characters['Right'].x, x)
            for _ in range(100):
                state.update(.1, direction=-1, run_half_width=.13)
            self.assertEqual(state.characters['Right'].x, .13)
            self.assertEqual(state.nando_facing, -1)
        self.assertAlmostEqual(*positions)

    def test_run_loops_across_cycles_without_arrow_and_pauses(self):
        state = AnimationController(run_mode=True)
        original_x = state.characters['Right'].x
        frames = []
        for _ in range(45):
            state.update(1/30)
            frames.append(state.run_frame)
        self.assertEqual(state.characters['Right'].x, original_x)
        self.assertTrue(all(set(frames[i:i+15]) == set(range(5)) for i in (0, 15, 30)))
        self.assertGreaterEqual(sum(a == 4 and b == 0 for a, b in zip(frames, frames[1:])), 2)
        state.paused = True
        before = (state.run_frame, state.run_timer)
        state.update(.1)
        self.assertEqual((state.run_frame, state.run_timer), before)

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


class CostumeTests(unittest.TestCase):
    def setUp(self):
        self.state = AnimationController()
        self.board = SimpleNamespace(set_fullscreen=lambda enabled: None)
        self.audio = SimpleNamespace(stop=lambda: None)
        self.video = SimpleNamespace(video_playing=False)

    def keys(self, *keys):
        pressed = set(keys)
        held = set(keys)
        handle_keys(pressed, self.state, self.board, self.audio, self.video, held)

    def test_auto_backgrounds_keyboard_internal_and_voice_mapping(self):
        from voice_trigger import TRIGGER_KEYWORDS
        self.assertEqual((self.state.nando_costume, self.state.costume_mode), ('SPORT', 'AUTO'))
        for index, costume in enumerate(('SPORT', 'SPORT', 'SCHOOL', 'SCHOOL', 'SCHOOL')):
            self.keys(f'F{index+1}')
            self.assertEqual(self.state.nando_costume, costume)
        self.keys(']')
        self.assertEqual(self.state.nando_costume, 'SPORT')
        self.keys('[')
        self.assertEqual(self.state.nando_costume, 'SCHOOL')
        for keyword, costume in [('taman', 'SPORT'), ('rumah', 'SPORT'), ('kelas', 'SCHOOL')]:
            self.state.set_background(TRIGGER_KEYWORDS[keyword])
            self.assertEqual(self.state.nando_costume, costume)

    def test_manual_override_and_auto_immediate(self):
        self.keys('F4')
        self.keys('Y')
        self.assertEqual((self.state.nando_costume, self.state.costume_mode), ('SPORT', 'MANUAL'))
        self.keys('F5')
        self.assertEqual(self.state.nando_costume, 'SPORT')
        self.keys('J')
        self.assertEqual((self.state.nando_costume, self.state.costume_mode), ('SCHOOL', 'AUTO'))
        self.keys('Y')
        self.keys('Y')
        self.assertEqual(self.state.nando_costume, 'SCHOOL')

    def test_sport_ten_poses_and_independent_empty_ibu_slot(self):
        for bank in (1, 2):
            self.state.animation_banks = {'Right': bank, 'Left': bank}
            for finger in range(1, 6):
                self.keys('N', str(finger))
                self.keys('O', str(finger))
                pose = (bank-1)*5+finger
                self.assertEqual(self.state.get_nando_pose(), NANDO_SPORT[pose-1])
                self.assertEqual(self.state.characters['Left'].pose, min(8, (bank-1)*5+finger))
        self.keys('Y')  # SPORT pose 9 -> last valid SCHOOL pose, never None.
        self.assertIn(self.state.get_nando_pose(), NANDO)
        self.assertLessEqual(self.state.characters['Right'].pose, 8)

    def test_same_logical_pose_switch_and_hidden_fade(self):
        self.state.animation_banks = {'Right': 2, 'Left': 2}
        self.keys('N', '2')
        self.keys('Y')
        self.assertEqual(self.state.get_nando_pose(), NANDO[6])
        self.keys('Y')
        self.assertEqual(self.state.get_nando_pose(), NANDO_SPORT[6])
        self.assertEqual(self.state.characters['Right'].alpha, 0)
        self.keys('G')
        for _ in range(8):
            self.state.update(.05, [{'label': 'Right', 'box': (100, 100, 200, 300), 'count': 4}])
        self.assertEqual(self.state.get_nando_pose(), NANDO_SPORT[8])
        self.assertEqual(self.state.characters['Right'].alpha, 1)
        for _ in range(8):
            self.state.update(.05)
        self.assertEqual(self.state.characters['Right'].alpha, 0)
        self.keys('Y')
        self.assertEqual(self.state.characters['Right'].alpha, 0)

    def test_costume_preserves_balance_lock_and_curtain(self):
        self.keys('S')
        for _ in range(20):
            self.state.update(.1, [{'label': 'Right', 'box': (100, 100, 200, 300), 'count': 1}])
        c = self.state.characters['Right']
        before = (c.x, c.y, c.height, c.balance_pending, c.alpha)
        self.keys('P', 'Y')
        self.assertEqual(before, (c.x, c.y, c.height, c.balance_pending, c.alpha))
        self.assertTrue(self.state.scale_locked)
        self.assertEqual(self.state.curtain_phase, 'closing')
        self.keys('J', 'F4')
        self.assertEqual(self.state.nando_costume, 'SCHOOL')

    def test_special_modes_never_change_permanent_costume(self):
        for costume in ('SPORT', 'SCHOOL'):
            self.state.set_nando_costume(costume, 'MANUAL')
            for key in ('R', 'T', 'H'):
                self.keys(key)
                self.state.update(.1)
                self.keys(key)
                self.assertEqual(self.state.nando_costume, costume)
            self.state.hug_alpha = 0
            self.keys('K')
            for _ in range(100):
                self.state.update(.05)
            self.assertFalse(self.state.football_active)
            self.assertEqual(self.state.nando_costume, costume)
            self.video.video_playing = True
            self.keys('Y', 'J', 'F1')
            self.state.update(.1, video_playing=True)
            self.video.video_playing = False
            self.assertEqual(self.state.nando_costume, costume)


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

    def test_costume_render_height_and_sleep_lookup(self):
        state = AnimationController()
        effects = WhiteboardRenderer(self.assets, create_window=False).effects
        for pose in range(1, 9):
            state.characters['Right'].pose = pose
            sport = effects.character_sprite(state, 'Right', 720)
            self.assertIs(sport, self.assets.sprite(NANDO_SPORT[pose-1], .46*720))
            state.toggle_nando_costume()
            school = effects.character_sprite(state, 'Right', 720)
            self.assertEqual(sport.shape[0], school.shape[0])
            self.assertIs(school, self.assets.sprite(NANDO[pose-1], .46*720))
            state.toggle_nando_costume()
        state.sleep_mode = True
        self.assertEqual(state.get_nando_pose(sleeping=True), NANDO_SPORT[2])
        self.assertIs(effects.character_sprite(state, 'Right', 720), self.assets.sprite(NANDO_SPORT[2], .46*720))
        state.toggle_nando_costume()
        self.assertEqual(state.get_nando_pose(sleeping=True), NANDO[2])

    def test_all_poses_and_special_modes_render(self):
        state = AnimationController(keyboard_preview=True)
        for _ in range(4):
            state.update(.1)
        board = WhiteboardRenderer(self.assets, create_window=False)
        audio = SimpleNamespace(current_sound=None)
        video = SimpleNamespace(video_playing=False, fade_frame=None, current_video=None)
        for bank in (1, 2):
            state.animation_banks = {'Right': bank, 'Left': bank}
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

    def test_curtain_fully_covers_then_opens_center(self):
        state = AnimationController(curtain_phase='closed')
        board = WhiteboardRenderer(self.assets, create_window=False)
        canvas = np.full((180, 321, 3), 255, np.uint8)
        board.render_curtain(canvas, state)
        self.assertTrue(np.all(canvas < 255))
        state.curtain_phase, state.curtain_timer = 'opening', .325
        canvas[:] = 255
        board.render_curtain(canvas, state)
        self.assertTrue(np.all(canvas[:, 160] == 255))
        self.assertTrue(np.any(canvas[:, 0] < 255))

    def test_ui_master_hide_and_help_on_small_and_large_canvas(self):
        state = AnimationController(show_help=True, show_hud=False)
        board = WhiteboardRenderer(self.assets, create_window=False)
        audio = SimpleNamespace(current_sound=None)
        video = SimpleNamespace(current_video=None, video_playing=False)
        for w, h in ((640, 360), (1280, 720), (1920, 1080)):
            canvas = np.full((h, w, 3), 200, np.uint8)
            board.render_ui(canvas, state, audio, video)
            self.assertTrue(np.all(canvas == 200))
            state.show_hud = True
            board.render_ui(canvas, state, audio, video)
            self.assertTrue(np.any(canvas != 200))
            state.show_hud = False
        state.show_help = False
        handle_keys({'F12'}, state, board, audio, video)
        self.assertTrue(state.show_help and state.show_hud)
        handle_keys({'F12'}, state, board, audio, video)
        self.assertFalse(state.show_help or state.show_hud)


if __name__ == '__main__':
    unittest.main(verbosity=2)

"""Integration tests decode real media; no speaker, webcam or GUI is opened."""
import unittest
import numpy as np
from asset_manager import SOUNDS, VIDEOS
from audio_manager import AudioCache, AudioManager
from video_manager import VideoManager


class MediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cache = AudioCache(SOUNDS+VIDEOS)

    @classmethod
    def tearDownClass(cls):
        cls.cache.close()

    def setUp(self):
        self.audio = AudioManager(self.cache, open_device=False)
        self.video = VideoManager(self.audio)

    def tearDown(self):
        self.video.close()
        self.audio.close()

    def test_five_real_sounds_decode_complete_and_replay(self):
        out = np.zeros((48000, 2), np.int16)
        for path in SOUNDS:
            with self.subTest(path=path.name):
                self.assertGreater(np.max(np.abs(self.cache.tracks[path].astype(np.int32))), 0)
                self.assertTrue(self.audio.play(path))
                self.assertFalse(self.audio.play(path))
                while self.audio.sound_playing:
                    self.audio._callback(out, len(out), None, None)
                self.assertTrue(self.audio.play(path))
                self.audio.stop()

    def test_five_real_videos_audio_pause_finish_skip_and_exclusivity(self):
        out = np.zeros((1600, 2), np.int16)
        for path in VIDEOS:
            with self.subTest(path=path.name):
                self.audio.play(SOUNDS[0])
                self.assertTrue(self.video.play(path))
                self.assertEqual(self.audio.current_sound, path)
                self.assertFalse(self.video.play(path))
                self.assertFalse(self.video.play(VIDEOS[(VIDEOS.index(path)+1)%5]))
                self.assertIsNotNone(self.cache.tracks[path])
                self.audio.set_paused(True)
                frame_before = self.video.frame.copy()
                self.audio._callback(out, len(out), None, None)
                self.video.update(.5, paused=True)
                self.assertEqual(self.audio.playback.cursor, 0)
                np.testing.assert_array_equal(self.video.frame, frame_before)
                self.audio.set_paused(False)
                for _ in range(600):
                    self.audio._callback(out, len(out), None, None)
                    self.video.update(1/30)
                    if not self.video.video_playing:
                        break
                self.assertFalse(self.video.video_playing)
                self.assertIsNone(self.audio.current_sound)
                self.assertIsNotNone(self.video.fade_frame)
                self.assertTrue(self.video.play(path))
                self.video.stop()
                self.assertFalse(self.video.video_playing)
                self.assertIsNone(self.audio.current_sound)


if __name__ == '__main__':
    unittest.main(verbosity=2)

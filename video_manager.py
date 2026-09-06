"""OpenCV cutscene frames synchronized to the shared PCM audio channel."""
import cv2


class VideoManager:
    def __init__(self, audio):
        self.audio = audio
        self.cap = None
        self.current_video = None
        self.elapsed = 0.0
        self.duration = 0.0
        self.frame = None
        self.frame_index = -1
        self.fade_frame = None
        self.fade_remaining = 0.0
        self.error = None

    @property
    def video_playing(self):
        return self.cap is not None

    def play(self, path, paused=False):
        if self.video_playing:
            print("[VIDEO] Trigger ignored: a cutscene is already playing")
            return False
        cap = cv2.VideoCapture(str(path))
        ok, frame = cap.read()
        if not ok:
            cap.release()
            self.error = f"[VIDEO ERROR] Cannot decode: {path}"
            print(self.error)
            return False
        self.audio.stop()
        self.cap, self.frame, self.frame_index = cap, frame, 0
        self.current_video = path
        self.elapsed = 0.0
        self.fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        video_duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / self.fps
        metadata = self.audio.cache.metadata[path]
        self.duration = max(video_duration, float(metadata.get("format", {}).get("duration", 0)))
        self.fade_frame, self.fade_remaining = None, 0.0
        self.error = None
        self.audio.play(path, paused=paused)
        print(f"[VIDEO] Playing: {path.name}")
        return True

    def update(self, dt, paused=False):
        if paused:
            return self.frame
        if not self.video_playing:
            self.fade_remaining = max(0.0, self.fade_remaining-dt)
            if self.fade_remaining == 0:
                self.fade_frame = None
            return None
        if self.audio.current_sound == self.current_video:
            self.elapsed = max(self.elapsed, self.audio.position)
        else:
            self.elapsed += dt
        if self.elapsed >= self.duration:
            self.stop(fade=True)
            return None
        target = int(self.elapsed*self.fps)
        # Seek when falling far behind; otherwise decode forward without replaying frames.
        if target - self.frame_index > 8:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, target)
            self.frame_index = target-1
        while self.frame_index < target:
            ok, frame = self.cap.read()
            if not ok:
                # A slightly longer audio stream may finish over the last video frame.
                self.frame_index = target
                break
            self.frame, self.frame_index = frame, self.frame_index+1
        return self.frame

    def stop(self, fade=False):
        if self.cap:
            self.cap.release()
        if self.current_video:
            self.audio.stop()
        self.fade_frame = self.frame if fade else None
        self.fade_remaining = 0.45 if fade else 0.0
        self.cap, self.frame, self.current_video = None, None, None

    def close(self):
        self.stop()

"""One non-blocking PCM output channel for BGM and internal MP4 audio."""
from pathlib import Path
from dataclasses import dataclass
import hashlib
import json
import shutil
import subprocess
import threading
import numpy as np
import sounddevice as sd
from asset_manager import BASE_DIR

SAMPLE_RATE = 48000


def media_probe(path):
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("[MEDIA ERROR] ffprobe not found. Install FFmpeg and add its bin folder to PATH.")
    result = subprocess.run([ffprobe, "-v", "error", "-show_streams", "-show_format",
                             "-of", "json", str(path)], capture_output=True, text=True,
                            timeout=30, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if result.returncode:
        raise RuntimeError(f"[MEDIA ERROR] {path}: {result.stderr.strip()}")
    return json.loads(result.stdout)


class AudioCache:
    def __init__(self, paths, cache_dir=None):
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError("[MEDIA ERROR] ffmpeg not found. Install FFmpeg and add its bin folder to PATH.")
        self.tracks = {}
        self.metadata = {}
        cache_dir = Path(cache_dir or BASE_DIR / ".media_cache")
        cache_dir.mkdir(parents=True, exist_ok=True)
        try:
            for path in paths:
                meta = media_probe(path)
                self.metadata[path] = meta
                if not any(s["codec_type"] == "audio" for s in meta["streams"]):
                    self.tracks[path] = None
                    print(f"[AUDIO] No internal audio: {path.name}")
                    continue
                signature = f"{path.resolve()}|{path.stat().st_size}|{path.stat().st_mtime_ns}|pcm48k-stereo-v1"
                target = cache_dir / (hashlib.sha256(signature.encode()).hexdigest() + ".pcm")
                if not target.exists() or target.stat().st_size == 0:
                    print(f"[AUDIO] Preparing cache: {path.name}", flush=True)
                    pending = target.with_suffix(".tmp")
                    result = subprocess.run([ffmpeg, "-v", "error", "-nostdin", "-y", "-i", str(path),
                        "-map", "0:a:0", "-vn", "-ac", "2", "-ar", str(SAMPLE_RATE),
                        "-acodec", "pcm_s16le", "-f", "s16le", str(pending)],
                        capture_output=True, text=True, timeout=180,
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                    if result.returncode:
                        raise RuntimeError(f"[AUDIO ERROR] {path}: {result.stderr.strip()}")
                    pending.replace(target)
                self.tracks[path] = np.memmap(target, dtype="<i2", mode="r").reshape(-1, 2)
        except Exception:
            self.close()
            raise

    def close(self):
        for data in self.tracks.values():
            if data is not None:
                data._mmap.close()
        self.tracks.clear()


@dataclass
class Playback:
    path: Path
    data: np.ndarray
    cursor: int = 0
    paused: bool = False
    finished: bool = False


class AudioManager:
    def __init__(self, cache, open_device=True):
        self.cache = cache
        self.playback = None
        self.stream = None
        self.lock = threading.Lock()
        self.underruns = 0
        if open_device:
            try:
                self.stream = sd.OutputStream(samplerate=SAMPLE_RATE, channels=2, dtype="int16",
                    blocksize=1024, latency="low", callback=self._callback)
                self.stream.start()
            except Exception:
                if self.stream:
                    self.stream.close()
                raise

    @property
    def current_sound(self):
        p = self.playback
        return p.path if p and not p.finished else None

    @property
    def sound_playing(self):
        return self.current_sound is not None

    @property
    def position(self):
        p = self.playback
        latency = self.stream.latency if self.stream else 0
        return max(0.0, p.cursor/SAMPLE_RATE - latency) if p else 0.0

    def play(self, path, paused=False):
        with self.lock:
            if self.current_sound == path:
                print("[AUDIO] Duplicate trigger ignored")
                return False
            data = self.cache.tracks.get(path)
            self.playback = Playback(path, data, paused=paused) if data is not None else None
        if data is not None:
            print(f"[AUDIO] Playing: {path.name}")
        return data is not None

    def _callback(self, outdata, frames, time_info, status):
        outdata.fill(0)
        if status:
            self.underruns += 1
        # Never wait on the real-time audio thread. UI holds this lock only for state swaps.
        if not self.lock.acquire(blocking=False):
            return
        try:
            p = self.playback
            if p is None or p.paused or p.finished:
                return
            count = min(frames, len(p.data)-p.cursor)
            outdata[:count] = p.data[p.cursor:p.cursor+count]
            p.cursor += count
            if p.cursor >= len(p.data):
                p.finished = True
        finally:
            self.lock.release()

    def set_paused(self, paused):
        with self.lock:
            if self.playback:
                self.playback.paused = paused

    def stop(self):
        with self.lock:
            self.playback = None

    def close(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.stop()

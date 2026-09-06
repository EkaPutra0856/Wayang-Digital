"""Single manifest for the production assets. Originals are never modified."""
from pathlib import Path
from collections import OrderedDict
import cv2
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
ASSET_ROOT = BASE_DIR / "FIX ASSET"
BACKGROUNDS = [ASSET_ROOT / "Asset/BG" / f"{i} akhir.png" for i in range(1, 6)]
SOUNDS = [ASSET_ROOT / "Asset/Sound" / name for name in (
    "1 opening.mp3", "2 makan.mp3", "3 brangkat sekolah.mp3",
    "4 ibu nganter buku.mp3", "5 pelukan ending.mp3")]
VIDEOS = [ASSET_ROOT / "Asset/Vid" / name for name in (
    "vid1.mp4", "vid2.mp4", "Create_a_cinematic_second_.mp4",
    "3 nganter buku.mp4", "4 ending.mp4")]
NANDO = [ASSET_ROOT / "Nando Fix Animation" / f"{i}.png" for i in range(37, 45)]
IBU = [ASSET_ROOT / "Ibu" / f"{i}.png" for i in range(58, 66)]
RUN = [ASSET_ROOT / "side with bag" / f"{i}.png" for i in range(45, 50)]
FOOTBALL = [ASSET_ROOT / "Ball" / name for name in (
    "1 without ball.png", "1 with ball.png", "2 with ball.png",
    "3 with ball.png", "3 without ball.png", "ball.png")]
HUG = ASSET_ROOT / "Asset/Pelukan.png"
GROUPS = {"Backgrounds": BACKGROUNDS, "Nando poses": NANDO, "Ibu poses": IBU,
          "Run frames": RUN, "Football sprites": FOOTBALL, "Sounds": SOUNDS,
          "Videos": VIDEOS, "Pelukan": [HUG]}


class AssetManager:
    def __init__(self):
        missing = [p for group in GROUPS.values() for p in group if not p.is_file()]
        if missing:
            raise FileNotFoundError("\n".join(f"[ASSET ERROR] Missing: {p}" for p in missing))
        self.images = {}
        self.cache = OrderedDict()
        for name, group in GROUPS.items():
            for path in group:
                if path.suffix == ".png":
                    data = cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_UNCHANGED)
                    if data is None:
                        raise ValueError(f"[ASSET ERROR] Cannot decode: {path}")
                    if path not in BACKGROUNDS:
                        if data.ndim != 3 or data.shape[2] != 4:
                            raise ValueError(f"[ASSET ERROR] PNG needs alpha: {path}")
                        # Trim only the in-memory transparent margin, never the asset file.
                        points = cv2.findNonZero(data[:, :, 3])
                        if points is None:
                            raise ValueError(f"[ASSET ERROR] Empty alpha: {path}")
                        x, y, w, h = cv2.boundingRect(points)
                        data = data[y:y+h, x:x+w]
                        scale = min(1.0, 800 / max(w, h))
                        if scale < 1:
                            data = cv2.resize(data, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
                    elif data.shape[2] == 4:
                        data = cv2.cvtColor(data, cv2.COLOR_BGRA2BGR)
                    self.images[path] = data
            print(f"[OK] {name}: {len(group)}")

    def sprite(self, path, height, flip=False):
        # Quantize to two pixels; bounded LRU prevents growth as hands change size.
        height = max(2, int(height) // 2 * 2)
        key = (path, height, flip)
        if key not in self.cache:
            src = self.images[path]
            width = max(1, round(height * src.shape[1] / src.shape[0]))
            img = cv2.resize(src, (width, height), interpolation=cv2.INTER_AREA)
            self.cache[key] = cv2.flip(img, 1) if flip else img
            if len(self.cache) > 96:
                self.cache.popitem(last=False)
        self.cache.move_to_end(key)
        return self.cache[key]

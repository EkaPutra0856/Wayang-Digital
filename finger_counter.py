# finger_counter.py
import cv2
import mediapipe as mp
import time
import math
from pathlib import Path

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

FINGERS = {
    'index': (8, 7, 6, 5),
    'middle': (12, 11, 10, 9),
    'ring': (16, 15, 14, 13),
    'pinky': (20, 19, 18, 17)
}

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17)
]

class HandDetector:
    def __init__(self, model_path=None):
        model_path = Path(model_path) if model_path else Path(__file__).resolve().parent / "hand_landmarker.task"
        if not model_path.is_file():
            raise FileNotFoundError(f"[MODEL ERROR] Missing: {model_path}")
        self.latest_result = None
        self.last_timestamp = -1
        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(model_path)),
            running_mode=VisionRunningMode.LIVE_STREAM,
            num_hands=2,
            min_hand_detection_confidence=0.4,
            min_hand_presence_confidence=0.4,
            min_tracking_confidence=0.4,
            result_callback=self._callback
        )
        self.landmarker = HandLandmarker.create_from_options(options)

    def _callback(self, result, output_image, timestamp_ms):
        self.latest_result = result

    def _get_distance(self, p1, p2):
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

    def _is_finger_extended(self, lm, tip_idx, dip_idx, pip_idx, mcp_idx, wrist_idx=0):
        tip, pip, mcp, wrist = lm[tip_idx], lm[pip_idx], lm[mcp_idx], lm[wrist_idx]
        
        # 1. Jarak ujung jari ke pergelangan tangan harus lebih panjang dari sendi PIP & MCP
        dist_tip_wrist = self._get_distance(tip, wrist)
        dist_pip_wrist = self._get_distance(pip, wrist)
        dist_mcp_wrist = self._get_distance(mcp, wrist)
        
        if dist_tip_wrist < dist_pip_wrist or dist_tip_wrist < dist_mcp_wrist * 1.15:
            return False
            
        # 2. Posisi ujung jari harus berada di atas sendi PIP pada sumbu Y
        if tip[1] > pip[1]:
            return False
            
        return True

    def _is_thumb_extended(self, lm, label):
        tip, ip, mcp, pinky_mcp, index_mcp, wrist = lm[4], lm[3], lm[2], lm[17], lm[5], lm[0]
        
        dist_tip_pinky = self._get_distance(tip, pinky_mcp)
        dist_ip_pinky = self._get_distance(ip, pinky_mcp)
        dist_tip_index = self._get_distance(tip, index_mcp)
        dist_mcp_index = self._get_distance(mcp, index_mcp)
        dist_tip_wrist = self._get_distance(tip, wrist)
        dist_ip_wrist = self._get_distance(ip, wrist)

        # Kondisi 1: Ujung jempol terentang menjauhi pangkal kelingking
        if dist_tip_pinky < dist_ip_pinky * 1.05:
            return False
            
        # Kondisi 2: Jempol tidak sedang menempel/menekuk di telapak dekat telunjuk
        if dist_tip_index < dist_mcp_index * 0.75:
            return False
            
        # Kondisi 3: Ujung jempol menjauhi pergelangan
        if dist_tip_wrist < dist_ip_wrist:
            return False
            
        # Kondisi 4: Arah horizontal (Tangan Kiri: jempol mengarah ke kanan; Tangan Kanan: jempol mengarah ke kiri)
        if label == "Left" and tip[0] < ip[0]:
            return False
        if label == "Right" and tip[0] > ip[0]:
            return False
            
        return True

    def process_frame(self, frame):
        """Memproses frame, merender skeleton pada frame kamera, dan mengembalikan metadata tangan."""
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        timestamp_ms = max(self.last_timestamp + 1, time.monotonic_ns() // 1_000_000)
        self.last_timestamp = timestamp_ms
        self.landmarker.detect_async(mp_image, timestamp_ms)

        hand_boxes = []
        counts = {"Left": None, "Right": None}

        if self.latest_result and self.latest_result.hand_landmarks and self.latest_result.handedness:
            raw_candidates = []
            for landmarks, handedness in zip(self.latest_result.hand_landmarks, self.latest_result.handedness):
                raw_label = handedness[0].category_name
                score = handedness[0].score
                # Balik label karena efek mirror kamera
                label = "Right" if raw_label == "Left" else "Left"
                lm_list = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]
                
                # Filter tangan yang posisinya mengarah ke bawah/terbalik
                if lm_list[5][1] > lm_list[0][1] and lm_list[17][1] > lm_list[0][1]:
                    continue

                raw_candidates.append({
                    "label": label,
                    "score": score,
                    "landmarks": lm_list
                })

            raw_candidates.sort(key=lambda x: x["score"], reverse=True)
            assigned_hands = {}

            # Anti-duplikasi: maksimal 1 kiri dan 1 kanan
            for candidate in raw_candidates:
                pref = candidate["label"]
                if pref not in assigned_hands:
                    assigned_hands[pref] = candidate
                else:
                    opp = "Right" if pref == "Left" else "Left"
                    if opp not in assigned_hands:
                        candidate["label"] = opp
                        assigned_hands[opp] = candidate

            for label, hand_data in assigned_hands.items():
                lm_list = hand_data["landmarks"]
                fingers_up = 0

                # Deteksi Jempol
                if self._is_thumb_extended(lm_list, label):
                    fingers_up += 1

                # Deteksi 4 Jari Utama
                for finger_name, (tip, dip, pip, mcp) in FINGERS.items():
                    if self._is_finger_extended(lm_list, tip, dip, pip, mcp):
                        fingers_up += 1

                counts[label] = fingers_up

                # Bounding Box
                x_coords = [pt[0] for pt in lm_list]
                y_coords = [pt[1] for pt in lm_list]
                pad = 20
                box = (
                    max(0, min(x_coords) - pad),
                    max(0, min(y_coords) - pad),
                    min(w, max(x_coords) + pad),
                    min(h, max(y_coords) + pad)
                )

                hand_boxes.append({
                    "label": label,
                    "box": box,
                    "count": fingers_up
                })

                # Gambar skeleton di tampilan kamera
                for p1, p2 in HAND_CONNECTIONS:
                    cv2.line(frame, lm_list[p1], lm_list[p2], (0, 255, 0), 2)
                for pt in lm_list:
                    cv2.circle(frame, pt, 4, (0, 0, 255), -1)

                wrist = lm_list[0]
                cv2.putText(frame, f"{'Kiri' if label == 'Left' else 'Kanan'}: {fingers_up}", 
                            (wrist[0] - 30, max(30, wrist[1] - 15)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        return frame, hand_boxes, counts

    def close(self):
        self.landmarker.close()

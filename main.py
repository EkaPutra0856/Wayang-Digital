# main.py
import cv2
import os
import ctypes
from voice_trigger import VoiceBackgroundManager
from finger_counter import HandDetector
from whiteboard import WhiteboardRenderer
from effect_animator import EffectAnimator
from ball_animator import BallAnimator

# ==========================================
# KONFIGURASI SISTEM (ON / OFF)
# ==========================================
SHOW_BOUNDING_BOX     = False  # True = Tampilkan kotak & label jari | False = Wayang bersih
SHOW_PIP_CAMERA       = True   # True = Tampilkan webcam mini 20% di pojok | False = Sembunyikan
ENABLE_EFFECT_VOICE   = False  # True = Voice effect aktif | False = Mode Keyboard


def get_screen_resolution():
    try:
        user32 = ctypes.windll.user32
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    except Exception:
        return 1920, 1080


def main():
    print("=" * 60)
    print("  SISTEM WAYANG DIGITAL: INTERAKTIF BOLA PANTUL & EFEK")
    print("=" * 60)

    latar_dir = os.path.join(os.path.dirname(__file__), "Latar")
    if not os.path.exists(latar_dir):
        os.makedirs(latar_dir)

    screen_w, screen_h = get_screen_resolution()
    print(f"[Display] Resolusi Layar Monitor: {screen_w}x{screen_h}")

    voice_manager = VoiceBackgroundManager(latar_dir=latar_dir)
    voice_manager.start()

    effect_mgr = EffectAnimator()
    if ENABLE_EFFECT_VOICE:
        effect_mgr.start_voice()

    ball_mgr = BallAnimator()
    detector = HandDetector()
    board = WhiteboardRenderer(
        window_name="Wayang Digital",
        show_box=SHOW_BOUNDING_BOX,
        show_pip=SHOW_PIP_CAMERA
    )

    cap = cv2.VideoCapture(0)
    last_output = ""

    print("\nKontrol Keyboard Efek:")
    print(" [1]     : Munculkan / Hilangkan Tas")
    print(" [2]     : Munculkan / Hilangkan Buku")
    print(" [3]     : Munculkan / Hilangkan Bola Pantul")
    print(" [0]     : Hilangkan SEMUA Efek Sekaligus (Reset)")
    print(" [Spasi] : Pause / Resume Posisi Wayang")
    print(" [q/Esc] : Keluar Program\n")

    try:
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                continue

            frame = cv2.flip(frame, 1)
            cam_h, cam_w, _ = frame.shape

            # Trigger Scene Latar Suara
            if voice_manager.trigger_event:
                board.set_scene(voice_manager.current_png_path, voice_manager.current_mp4_path)
                voice_manager.trigger_event = False

            # Deteksi Jari Tangan
            frame, hand_boxes, counts = detector.process_frame(frame)

            # Render Fullscreen Whiteboard (Wayang + Efek + Bola Pantul)
            board.render(
                screen_res=(screen_w, screen_h),
                cam_frame=frame,
                hand_boxes=hand_boxes,
                cam_res=(cam_w, cam_h),
                effect_mgr=effect_mgr,
                ball_mgr=ball_mgr
            )

            # Output Terminal
            l_str = f"Kiri: {counts['Left']}" if counts['Left'] is not None else "Kiri: -"
            r_str = f"Kanan: {counts['Right']}" if counts['Right'] is not None else "Kanan: -"
            total = (counts['Left'] or 0) + (counts['Right'] or 0)
            current_output = f"[{l_str}] | [{r_str}] | Total: {total}"

            if current_output != last_output:
                print(current_output)
                last_output = current_output

            # Kontrol Keyboard
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27 or board.is_closed():
                break
            elif key == ord(' '):
                board.toggle_pause()
            elif key == ord('1'):
                effect_mgr.toggle_tas()
            elif key == ord('2'):
                effect_mgr.toggle_buku()
            elif key == ord('3'):
                ball_mgr.toggle(screen_w, screen_h)
            elif key == ord('0'):
                effect_mgr.trigger_dismiss()
                ball_mgr.dismiss()

    finally:
        if ENABLE_EFFECT_VOICE:
            effect_mgr.stop_voice()
        board.close()
        detector.close()
        voice_manager.stop()
        cap.release()
        cv2.destroyAllWindows()
        print("\nSeluruh sistem berhasil dimatikan dengan aman.")


if __name__ == "__main__":
    main()
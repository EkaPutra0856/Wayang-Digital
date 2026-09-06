"""Wayang Interaktif 2D - launch with python main.py."""
import argparse
from contextlib import ExitStack
import ctypes
import time
import cv2
import numpy as np
from asset_manager import AssetManager, SOUNDS, VIDEOS, VIDEO_CUES, RUN
from animation_controller import AnimationController
from audio_manager import AudioCache, AudioManager
from video_manager import VideoManager
from voice_trigger import VoiceBackgroundManager
from finger_counter import HandDetector
from whiteboard import WhiteboardRenderer
from keyboard_controller import KeyboardController


def get_screen_resolution():
    try:
        user32 = ctypes.windll.user32
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    except AttributeError:
        return 1280, 720


def handle_keys(pressed, state, board, audio, video, held=None):
    held = pressed if held is None else held
    if 'Q' in pressed:
        return False
    if 'ESC' in pressed:
        if video.video_playing:
            video.stop()
        else:
            return False
    if 'SPACE' in pressed:
        state.paused = not state.paused
        audio.set_paused(state.paused)
        print(f"[PAUSE] {'ON' if state.paused else 'OFF'}")
    if 'F' in pressed:
        state.fullscreen = not state.fullscreen
        board.set_fullscreen(state.fullscreen)
    if 'F12' in pressed or '?' in pressed:
        state.show_help = not state.show_help
        # Panduan selalu membuka panel agar dapat dibaca, lalu menutupnya
        # kembali saat panduan ditutup sehingga tidak perlu menekan U.
        state.show_hud = state.show_help
    for key, field in [('W', 'show_pip'), ('U', 'show_hud'), ('D', 'show_box')]:
        if key in pressed:
            setattr(state, field, not getattr(state, field))
    if 'P' in pressed:
        state.start_curtain()
    if video.video_playing:
        return True  # Cutscene owns visuals and audio; no queued surprise triggers.
    if 'M' in pressed:
        audio.stop()
    if state.paused:
        return True
    if 'L' in pressed:
        state.toggle_scale_lock()
    if 'S' in pressed:
        state.balance_scale()
    if 'Y' in pressed:
        state.toggle_nando_costume()
    if 'J' in pressed:
        state.set_costume_auto()
    if 'TAB' in pressed:
        state.toggle_bank()
    if 'G' in pressed:
        state.use_gesture()
    for i in range(1, 6):
        if str(i) in pressed:
            if 'I' in held:
                state.debug_pose(i, 'Left')
            if 'N' in held:
                state.debug_pose(i, 'Right')
        if f'F{i}' in pressed:
            state.set_background(i-1)
    if '[' in pressed:
        state.set_background((state.current_bg-1) % 5)
    if ']' in pressed:
        state.set_background((state.current_bg+1) % 5)
    # Video wins if a sound and video key arrive together.
    for key, (path, background, soundtrack) in VIDEO_CUES.items():
        if key in pressed:
            if video.play(path, soundtrack=soundtrack):
                state.set_background(background)
            return True
    for key, path in zip('ZXCVB', SOUNDS):
        if key in pressed:
            audio.play(path)
            break
    for key, field, label in [('R', 'run_mode', 'RUN'), ('T', 'sleep_mode', 'SLEEP'),
                              ('H', 'hug_mode', 'ENDING')]:
        if key in pressed:
            setattr(state, field, not getattr(state, field))
            if field == 'sleep_mode' and state.sleep_mode:
                state.sleep_start_time = state.clock
            print(f"[{label}] {'ON' if getattr(state, field) else 'OFF'}")
    if 'K' in pressed:
        state.start_football()
    return True


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-camera', action='store_true', help='Keyboard pose testing without webcam')
    parser.add_argument('--no-voice', action='store_true', help='Disable microphone recognition')
    parser.add_argument('--mute', action='store_true', help='Explicit silent test mode; no output device')
    parser.add_argument('--headless', action='store_true', help='Render offscreen; no keyboard/window')
    parser.add_argument('--frames', type=int, default=0, help='Exit after N frames (0 = interactive)')
    parser.add_argument('--camera', type=int, default=0)
    parser.add_argument('--mic', type=int, default=None)
    parser.add_argument('--windowed', action='store_true')
    parser.add_argument('--validate-assets', action='store_true')
    args = parser.parse_args(argv)
    if args.headless and args.frames <= 0 and not args.validate_assets:
        parser.error('--headless requires --frames N to avoid an invisible endless process')
    return args


def main(argv=None):
    args = parse_args(argv)
    assets = AssetManager()
    if args.validate_assets:
        return 0
    with ExitStack() as cleanup:
        cache = AudioCache(SOUNDS+VIDEOS)
        cleanup.callback(cache.close)
        audio = AudioManager(cache, open_device=not args.mute)
        cleanup.callback(audio.close)
        video = VideoManager(audio)
        cleanup.callback(video.close)
        state = AnimationController(fullscreen=not args.windowed, keyboard_preview=args.no_camera)
        board = WhiteboardRenderer(assets, create_window=not args.headless)
        cleanup.callback(board.close)
        board.set_fullscreen(state.fullscreen)
        keyboard = None if args.headless else KeyboardController(board.window_name)
        cap, detector = None, None
        if not args.no_camera:
            cap = cv2.VideoCapture(args.camera)
            cleanup.callback(cap.release)
            if cap.isOpened():
                detector = HandDetector()
                cleanup.callback(detector.close)
                print('[CAMERA] Opened')
            else:
                print('[CAMERA ERROR] Cannot open webcam. Keyboard mode: 1-5; G restores gesture.')
                cap = None
        voice = None
        if not args.no_voice:
            voice = VoiceBackgroundManager(args.mic)
            cleanup.callback(voice.stop)
            voice.start()
        # Render at at most 1920x1080 while preserving the monitor aspect ratio.
        sw, sh = get_screen_resolution()
        scale = min(1.0, 1920/max(1, sw), 1080/max(1, sh))
        screen_res = (max(640, round(sw*scale)), max(360, round(sh*scale)))
        if args.headless:
            screen_res = (1280, 720)
        print('[READY] I+1-5: Ibu | N+1-5: Nando | G: gesture | U: UI | F12: help | Q: quit', flush=True)
        previous = time.perf_counter()
        frame_count, camera_failures = 0, 0
        silent_buffer = np.zeros((1600, 2), dtype=np.int16)
        while True:
            started = time.perf_counter()
            dt = min(0.1, max(0.0, started-previous))
            previous = started
            pressed, held = keyboard.poll() if keyboard else (set(), set())
            if not handle_keys(pressed, state, board, audio, video, held):
                break
            frame, hands = None, []
            if cap is not None:
                ok, frame = cap.read()
                if ok:
                    camera_failures = 0
                    frame = cv2.flip(frame, 1)
                    frame, hands, _ = detector.process_frame(frame)
                else:
                    frame = None
                    camera_failures += 1
                    if camera_failures == 30:
                        print('[CAMERA ERROR] Camera disconnected. Continuing with keyboard controls.')
                        cap.release()
                        cap = None
            if voice:
                voice.set_enabled(not video.video_playing and not audio.sound_playing and not state.paused)
                bg = voice.poll()
                if bg is not None and voice.enabled and bg != state.current_bg:
                    state.set_background(bg)
                    print(f'[VOICE] Background -> {bg+1}')
            if args.mute:
                # Advance the same PCM state for silent tests, without touching any device.
                count = max(1, round(dt*48000))
                if len(silent_buffer) < count:
                    silent_buffer = np.zeros((count, 2), dtype=np.int16)
                audio._callback(silent_buffer[:count], count, None, None)
            was_video = video.video_playing
            video.update(dt, state.paused)
            w, h = screen_res
            # Clamp using the widest run sprite so frame changes cannot cross the edges.
            nh = state.characters['Right'].height*h
            half_width = max(assets.images[p].shape[1]/assets.images[p].shape[0] for p in RUN)*nh/(2*w)
            state.update(dt, hands, (frame.shape[1], frame.shape[0]) if frame is not None else (640, 480),
                         screen_res, int('RIGHT' in held)-int('LEFT' in held), was_video, half_width)
            board.render(screen_res, frame, hands, state, audio, video)
            frame_count += 1
            if not args.headless:
                cv2.waitKeyEx(1)  # Pump HighGUI events; native polling handles key down/up.
                if board.is_closed():
                    break
            if args.frames and frame_count >= args.frames:
                break
            time.sleep(max(0, 1/30-(time.perf_counter()-started)))
        print(f'[EXIT] Clean shutdown after {frame_count} frames. Audio underruns: {audio.underruns}')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print('[EXIT] Interrupted')
    except Exception as exc:
        print(f'[STARTUP/RUNTIME ERROR] {exc}')
        raise SystemExit(1)

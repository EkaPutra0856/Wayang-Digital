"""Windows physical key edges: OS key repeat cannot re-toggle show modes."""
import ctypes
import os

KEYS = {chr(i): i for i in range(ord('A'), ord('Z')+1)}
KEYS.update({str(i): ord(str(i)) for i in range(10)})
KEYS.update({"TAB": 0x09, "SPACE": 0x20, "ESC": 0x1B, "LEFT": 0x25,
             "RIGHT": 0x27, "[": 0xDB, "]": 0xDD, "?": 0xBF,
             **{f"F{i}": 0x6F+i for i in range(1, 13)}})


class KeyboardController:
    def __init__(self, window_name="Wayang Digital"):
        if os.name != "nt":
            raise RuntimeError("This keyboard backend requires Windows.")
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.user32.GetForegroundWindow.restype = ctypes.c_void_p
        self.user32.GetWindowTextW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int]
        self.user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
        self.user32.GetAsyncKeyState.restype = ctypes.c_short
        self.window_name = window_name
        self.previous = set()
        self.focused = False

    def edges(self, held, focused=True):
        # On focus entry absorb held keys to avoid an accidental action.
        pressed = held-self.previous if focused and self.focused else set()
        self.previous = set(held)
        self.focused = focused
        return pressed, held if focused else set()

    def poll(self):
        title = ctypes.create_unicode_buffer(512)
        self.user32.GetWindowTextW(self.user32.GetForegroundWindow(), title, len(title))
        focused = title.value == self.window_name
        held = {key for key, code in KEYS.items() if self.user32.GetAsyncKeyState(code) & 0x8000}
        return self.edges(held, focused)

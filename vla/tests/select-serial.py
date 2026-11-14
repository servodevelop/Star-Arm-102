"""Select the sole USB adapter in Chromium's native chooser on the X11 test desktop.

Test-only keyboard automation. Does not read or write the serial port.
The caller verifies that /dev/serial/by-id contains exactly one USB adapter.
"""
import ctypes
import time

x11 = ctypes.CDLL("libX11.so.6")
xtst = ctypes.CDLL("libXtst.so.6")
x11.XOpenDisplay.restype = ctypes.c_void_p
x11.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
x11.XKeysymToKeycode.restype = ctypes.c_uint
x11.XFlush.argtypes = [ctypes.c_void_p]
x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
xtst.XTestFakeKeyEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
display = x11.XOpenDisplay(None)
if not display:
    raise SystemExit("X11 display unavailable")


def press(symbol, down):
    code = x11.XKeysymToKeycode(display, symbol)
    xtst.XTestFakeKeyEvent(display, code, int(down), 0)
    x11.XFlush(display)
    time.sleep(0.08)


def tap(symbol):
    press(symbol, True)
    press(symbol, False)


try:
    # Chooser focuses Cancel. Move back to the device list, select its last
    # entry (USB adapter follows the built-in ttyS ports), then Connect.
    press(0xFFE1, True)  # Shift
    tap(0xFF09)  # Tab
    tap(0xFF09)
    press(0xFFE1, False)
    tap(0xFF57)  # End
    tap(0x20)  # Space
    for _ in range(3):
        tap(0xFF09)
    tap(0xFF0D)  # Return
finally:
    x11.XCloseDisplay(display)

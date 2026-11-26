"""Focus, capture, and click a verified game window without changing its geometry."""

import ctypes
from ctypes import wintypes
from pathlib import PureWindowsPath
import time

import cv2
import numpy as np
import PIL.ImageGrab as ImageGrab
import win32gui

from vision import HEIGHT, WIDTH, canonical


user = ctypes.WinDLL("user32", use_last_error=True)
kernel = ctypes.WinDLL("kernel32", use_last_error=True)


def bind(dll, name, restype, *argtypes):
    function = getattr(dll, name)
    function.restype = restype
    function.argtypes = argtypes
    return function


foreground = bind(user, "GetForegroundWindow", wintypes.HWND)
set_foreground = bind(user, "SetForegroundWindow", wintypes.BOOL, wintypes.HWND)
show_async = bind(user, "ShowWindowAsync", wintypes.BOOL, wintypes.HWND, ctypes.c_int)
is_visible = bind(user, "IsWindowVisible", wintypes.BOOL, wintypes.HWND)
is_iconic = bind(user, "IsIconic", wintypes.BOOL, wintypes.HWND)
get_rect = bind(user, "GetClientRect", wintypes.BOOL, wintypes.HWND, ctypes.POINTER(wintypes.RECT))
to_screen = bind(user, "ClientToScreen", wintypes.BOOL, wintypes.HWND, ctypes.POINTER(wintypes.POINT))
monitor_from_rect = bind(user, "MonitorFromRect", wintypes.HMONITOR, ctypes.POINTER(wintypes.RECT), wintypes.DWORD)
get_pid = bind(user, "GetWindowThreadProcessId", wintypes.DWORD, wintypes.HWND, ctypes.POINTER(wintypes.DWORD))
window_at = bind(user, "WindowFromPoint", wintypes.HWND, wintypes.POINT)
ancestor = bind(user, "GetAncestor", wintypes.HWND, wintypes.HWND, wintypes.UINT)
cursor = bind(user, "SetCursorPos", wintypes.BOOL, ctypes.c_int, ctypes.c_int)
cursor_position = bind(user, "GetCursorPos", wintypes.BOOL, ctypes.POINTER(wintypes.POINT))
key = bind(user, "GetAsyncKeyState", ctypes.c_short, ctypes.c_int)
mouse = bind(user, "mouse_event", None, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD,
             wintypes.DWORD, ctypes.c_size_t)
open_process = bind(kernel, "OpenProcess", wintypes.HANDLE, wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
close_process = bind(kernel, "CloseHandle", wintypes.BOOL, wintypes.HANDLE)
image_name = bind(kernel, "QueryFullProcessImageNameW", wintypes.BOOL, wintypes.HANDLE, wintypes.DWORD,
                  wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD))
set_dpi = bind(user, "SetProcessDpiAwarenessContext", wintypes.BOOL, wintypes.HANDLE)


class MonitorInfo(ctypes.Structure):
    _fields_ = [("length", wintypes.DWORD), ("screen", wintypes.RECT),
                ("work", wintypes.RECT), ("flags", wintypes.DWORD)]


get_monitor_info = bind(user, "GetMonitorInfoW", wintypes.BOOL, wintypes.HMONITOR,
                        ctypes.POINTER(MonitorInfo))


def visible_client_bounds(window):
    if not is_visible(window) or is_iconic(window):
        raise OSError("游戏窗口隐藏或已最小化")
    size, origin = wintypes.RECT(), wintypes.POINT()
    if not get_rect(window, ctypes.byref(size)) or not to_screen(window, ctypes.byref(origin)):
        raise OSError("无法读取游戏客户区")
    if size.right < 1152 or size.bottom < 648:
        raise OSError(f"游戏客户区为 {size.right}×{size.bottom}，至少需要 1152×648")
    bounds = wintypes.RECT(origin.x, origin.y, origin.x + size.right, origin.y + size.bottom)
    monitor = monitor_from_rect(ctypes.byref(bounds), 0)  # Null if fully off screen.
    info = MonitorInfo()
    info.length = ctypes.sizeof(info)
    if not monitor or not get_monitor_info(monitor, ctypes.byref(info)):
        raise OSError("游戏客户区不在显示器内")
    screen = info.screen
    if (bounds.left < screen.left or bounds.top < screen.top
            or bounds.right > screen.right or bounds.bottom > screen.bottom):
        raise OSError("游戏客户区部分在显示器外或跨越了显示器")
    return bounds.left, bounds.top, bounds.right, bounds.bottom


def process_exe(window):
    pid = wintypes.DWORD()
    if not get_pid(window, ctypes.byref(pid)):
        raise OSError("无法读取前台窗口进程")
    process = open_process(0x1000, False, pid)
    if not process:
        raise OSError("无法验证前台窗口")
    try:
        name = ctypes.create_unicode_buffer(32768)
        size = wintypes.DWORD(len(name))
        if not image_name(process, 0, name, ctypes.byref(size)):
            raise OSError("无法验证前台窗口程序名")
        return PureWindowsPath(name.value).name.casefold()
    finally:
        close_process(process)


def is_game_window(window):
    try:
        return bool(window) and process_exe(window) == 'hololive-dreams.exe'
    except OSError:
        return False


def find_game_window():
    candidates = []

    def visit(window, _):
        if is_visible(window) and is_game_window(window):
            candidates.append(window)
        return True

    win32gui.EnumWindows(visit, None)
    visible = [window for window in candidates if not is_iconic(window)]
    if len(visible) == 1:
        return visible[0]
    if len(visible) > 1:
        raise OSError('找到多個遊戲視窗，請先切到要使用的視窗，再按開始快捷鍵。')
    if len(candidates) == 1:
        return candidates[0]
    if candidates:
        raise OSError('找到多個遊戲視窗，請先開啟要使用的視窗。')
    raise OSError('找不到 hololive Dreams 遊戲視窗。')


class GameWindow:
    def __init__(self, stop_requested):
        set_dpi(ctypes.c_void_p(-4))
        self.stop_requested = stop_requested
        self.check_stop()
        current = foreground()
        if is_game_window(current) and not is_iconic(current):
            self.hwnd = current
            self.bounds = self.rect()
            return
        self.hwnd = find_game_window()
        minimized = is_iconic(self.hwnd)
        original = None if minimized else visible_client_bounds(self.hwnd)
        self.check_stop()
        deadline = time.monotonic() + 1
        if minimized:
            show_async(self.hwnd, 9)  # SW_RESTORE
            while is_iconic(self.hwnd):
                self.check_stop()
                if time.monotonic() >= deadline:
                    raise OSError("無法恢復最小化的遊戲視窗。")
                time.sleep(.02)
        if foreground() != self.hwnd:
            set_foreground(self.hwnd)
        while foreground() != self.hwnd:
            self.check_stop()
            if time.monotonic() >= deadline:
                raise OSError('Windows 未切換到遊戲，請手動切回後按開始快捷鍵。')
            time.sleep(.02)
        self.bounds = self.rect()
        if original is not None and self.bounds != original:
            raise OSError("游戏窗口位置或大小已变化")

    def check_stop(self):
        if self.stop_requested() or key(0x1B) & 0x8000:
            raise InterruptedError("已停止")

    def rect(self):
        self.check_stop()
        if foreground() != self.hwnd:
            raise OSError("游戏窗口已失去焦点")
        return visible_client_bounds(self.hwnd)

    def verify_rect(self):
        if self.rect() != self.bounds:
            raise OSError("游戏窗口位置或大小已变化")

    def capture(self):
        self.verify_rect()
        frame = ImageGrab.grab(bbox=self.bounds, all_screens=True)
        self.verify_rect()
        return canonical(cv2.cvtColor(np.asarray(frame), cv2.COLOR_RGB2BGR))

    def click(self, x, y):
        self.verify_rect()
        if key(0x01) & 0x8000 or key(0x02) & 0x8000:
            raise OSError("检测到鼠标按键已按下")
        left, top, right, bottom = self.bounds
        target = wintypes.POINT(left + round(x*(right-left)/WIDTH), top + round(y*(bottom-top)/HEIGHT))
        if ancestor(window_at(target), 2) != self.hwnd:
            raise OSError("落点被其他窗口挡住")
        if not cursor(target.x, target.y):
            raise OSError("无法移动鼠标到落点")
        self.verify_rect()
        observed = wintypes.POINT()
        if not cursor_position(ctypes.byref(observed)) or (observed.x, observed.y) != (target.x, target.y):
            raise OSError("鼠标位置已变化")
        mouse(0x0002, 0, 0, 0, 0)
        mouse(0x0004, 0, 0, 0, 0)

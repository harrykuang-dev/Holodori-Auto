"""Keep the embedded High & Low capture out of Windows' restore path."""
import time


def install_window_guard(bot, windows):
    def geometry(hwnd):
        if not hwnd or not windows.IsWindowVisible(hwnd) or windows.IsIconic(hwnd):
            return None
        try:
            rect = bot._get_client_geometry(hwnd)
        except OSError:
            return None
        if rect[2] < 640 or rect[3] < 360 or windows.IsIconic(hwnd):
            return None
        return rect

    def activate(hwnd):
        if geometry(hwnd) is None:
            return False
        if windows.GetForegroundWindow() != hwnd:
            try:
                windows.SetForegroundWindow(hwnd)
            except windows.error:
                return False
        return windows.GetForegroundWindow() == hwnd and geometry(hwnd) is not None

    def capture():
        bot._capture_context = None
        window = bot.find_game_window()
        if window is None:
            return None, 0, 0
        hwnd = window._hWnd
        rect = geometry(hwnd)
        if rect is None:
            # The upstream loop waits for the next usable frame. Let the user
            # restore the window normally instead of forcing Unity to restore.
            return None, 0, 0
        left, top, width, height = rect
        try:
            image = bot._capture_client_with_printwindow(hwnd, width, height)
        except Exception as error:
            if geometry(hwnd) != rect or not activate(hwnd):
                return None, 0, 0
            print(f'[警告] 后台窗口截图失败，切换到前台截图: {error}')
            time.sleep(0.2)
            if geometry(hwnd) != rect or windows.GetForegroundWindow() != hwnd:
                return None, 0, 0
            monitor = dict(top=top, left=left, width=width, height=height)
            with bot.mss.MSS() as screen:
                image = bot.cv2.cvtColor(bot.np.array(screen.grab(monitor)), bot.cv2.COLOR_BGRA2BGR)
            if windows.GetForegroundWindow() != hwnd:
                return None, 0, 0
        if geometry(hwnd) != rect:
            return None, 0, 0
        image = bot.cv2.resize(image, (bot.REFERENCE_WIDTH, bot.REFERENCE_HEIGHT),
                               interpolation=bot.cv2.INTER_CUBIC)
        bot._capture_context = dict(hwnd=hwnd, width=width, height=height)
        return image, left, top

    bot.capture_game_window = capture
    bot._bring_game_to_front = activate

"""A declined Windows shortcut registration must leave the feature usable."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SHORTCUT = 'Ctrl+Alt+Shift+F9'


class ShortcutConflictTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform == 'win32', 'Windows feature interfaces')
    def test_conflicting_shortcut_shows_warning(self):
        for module in ('high_low', 'jump_rope'):
            with self.subTest(module=module), tempfile.TemporaryDirectory() as profile:
                result = subprocess.run(
                    [sys.executable, str(Path(__file__).resolve()), module],
                    env={**os.environ, 'LOCALAPPDATA': profile, 'APPDATA': profile, 'PYTHONUTF8': '1'},
                    capture_output=True, encoding='utf-8', timeout=30, check=False,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


def check_warning(module):
    import tkinter as tk

    sys.path.insert(0, str(ROOT / 'upstream' / module))
    import main_ui

    class Hotkey:
        def __init__(self, callback, report, value='F8'):
            self.report = report

        def start(self):
            pass

        def configure(self, **settings):
            pass

    root = tk.Tk()
    root.withdraw()
    try:
        if module == 'high_low':
            app = main_ui.HololiveBotUI(root, hotkey_factory=Hotkey)
            listener = app.start_hotkey
        else:
            main_ui.GlobalHotkey = Hotkey
            app = main_ui.JumpRopeApp(root)
            listener = app.hotkey

        app.log.delete('1.0', 'end')
        listener.report(SHORTCUT, False, 1409)  # ERROR_HOTKEY_ALREADY_REGISTERED
        app.poll()
        warning = app.log.get('1.0', 'end').strip()
        if SHORTCUT not in warning:
            raise AssertionError(f'{module} did not log the rejected shortcut: {warning!r}')
        if str(app.start_button.cget('state')) != 'normal':
            raise AssertionError(f'{module} disabled the Start button after a shortcut conflict')
    finally:
        root.destroy()


if __name__ == '__main__':
    check_warning(sys.argv[1])

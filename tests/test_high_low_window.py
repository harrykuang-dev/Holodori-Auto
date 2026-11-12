from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from holodori.high_low_window import install_window_guard


class HighLowWindowTests(unittest.TestCase):
    def setUp(self):
        self.game = SimpleNamespace(_hWnd=31, restore=Mock())
        self.bot = Mock(REFERENCE_WIDTH=1920, REFERENCE_HEIGHT=1080)
        self.bot.find_game_window.return_value = self.game
        self.bot._capture_context = {'hwnd': self.game._hWnd}
        self.bot._get_client_geometry.return_value = (100, 150, 1600, 900)
        self.windows = Mock()
        self.windows.IsWindowVisible.return_value = True
        self.windows.IsIconic.return_value = False
        self.windows.GetForegroundWindow.return_value = self.game._hWnd
        install_window_guard(self.bot, self.windows)

    def test_capture_waits_while_minimized_and_resumes_after_user_restores(self):
        self.windows.IsIconic.return_value = True
        self.assertEqual(self.bot.capture_game_window(), (None, 0, 0))
        self.assertIsNone(self.bot._capture_context)
        self.assertFalse(self.bot._bring_game_to_front(self.game._hWnd))
        self.bot._capture_client_with_printwindow.assert_not_called()
        self.windows.SetForegroundWindow.assert_not_called()
        self.game.restore.assert_not_called()

        self.windows.IsIconic.return_value = False
        self.assertEqual(self.bot.capture_game_window(),
                         (self.bot.cv2.resize.return_value, 100, 150))
        self.assertEqual(self.bot._capture_context, {'hwnd': 31, 'width': 1600, 'height': 900})

    def test_title_only_window_is_neither_captured_nor_activated(self):
        self.bot._get_client_geometry.return_value = (-31991, -31962, 181, 0)
        self.assertEqual(self.bot.capture_game_window(), (None, 0, 0))
        self.assertFalse(self.bot._bring_game_to_front(self.game._hWnd))
        self.bot._capture_client_with_printwindow.assert_not_called()
        self.windows.SetForegroundWindow.assert_not_called()
        self.assertIsNone(self.bot._capture_context)

    def test_minimize_during_failed_capture_cannot_trigger_foreground_fallback(self):
        def minimize(*_):
            self.windows.IsIconic.return_value = True
            raise RuntimeError('Capture interrupted')

        self.bot._capture_client_with_printwindow.side_effect = minimize
        self.assertEqual(self.bot.capture_game_window(), (None, 0, 0))
        self.bot.mss.MSS.assert_not_called()
        self.windows.SetForegroundWindow.assert_not_called()
        self.assertIsNone(self.bot._capture_context)

"""Check focus and shortcut behavior without operating the game."""
from importlib import import_module
from pathlib import Path
from queue import SimpleQueue
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


COMPONENT = Path(__file__).resolve().parents[1] / 'components' / 'puka_puka'
with patch.object(sys, 'path', [str(COMPONENT), *sys.path]):
    window = import_module('win_window')
    ui = import_module('puka_ui')


class ForegroundTests(unittest.TestCase):
    def test_background_window_is_brought_forward_without_restoring_or_moving(self):
        bounds = (50, 80, 1280, 790)
        switch = Mock()
        restore = Mock()
        with patch.multiple(window, set_dpi=Mock(), key=Mock(return_value=0),
                            foreground=Mock(side_effect=[10, 10, 20, 20]),
                            is_game_window=Mock(return_value=False), find_game_window=Mock(return_value=20),
                            is_iconic=Mock(return_value=False), visible_client_bounds=Mock(return_value=bounds),
                            set_foreground=switch, show_async=restore):
            game = window.GameWindow(lambda: False)
        switch.assert_called_once_with(20)
        restore.assert_not_called()
        self.assertEqual(game.bounds, bounds)

    def test_minimized_window_is_verified_after_restore(self):
        bounds = (50, 80, 1280, 790)
        restore = Mock()
        with patch.multiple(window, set_dpi=Mock(), key=Mock(return_value=0),
                            foreground=Mock(side_effect=[10, 20, 20, 20]),
                            is_game_window=Mock(return_value=False), find_game_window=Mock(return_value=20),
                            is_iconic=Mock(side_effect=[True, False]), visible_client_bounds=Mock(return_value=bounds),
                            set_foreground=Mock(), show_async=restore):
            game = window.GameWindow(lambda: False)
        restore.assert_called_once_with(20, 9)
        self.assertEqual(game.bounds, bounds)

    def test_windows_refusal_does_not_start_play(self):
        app = SimpleNamespace(messages=SimpleQueue(), stop_event=Mock())
        with patch.object(ui, 'GameWindow', side_effect=OSError('foreground refused')), \
             patch.object(ui, 'run') as run:
            ui.PukaPukaApp.play(app, 1, auto_refill=False)
        run.assert_not_called()
        self.assertEqual(app.messages.get_nowait(), ('error', 'foreground refused'))

    def test_shortcut_dispatches_only_the_current_generation(self):
        for generation, should_start in [(1, False), (2, True)]:
            with self.subTest(generation=generation):
                messages = SimpleQueue()
                messages.put(('start_shortcut', generation))
                app = SimpleNamespace(
                    messages=messages, start_generation=2, worker=None,
                    closing=False, smoke=False, stop_shortcut=((), 45), stop_held=False,
                    capturing=False, help_dialog=None, root=Mock(), start=Mock(), stop=Mock(), poll=Mock(),
                )
                with patch.object(ui, 'shortcut_down', return_value=False):
                    ui.PukaPukaApp.poll(app)
                self.assertEqual(app.start.call_count, int(should_start))

"""Check the integration boundary without reading the game or sending input."""
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from holodori.channel import read_json, write_json
from holodori import runtime
from holodori.runtime import (EmbeddedSession, apply_shared_settings, busy, change_language,
    hide_shared_controls, restore, shortcut_values, shortcuts_enabled, snapshot, validate_shared_settings)


class Variable:
    def __init__(self, value): self.value = value
    def get(self): return self.value
    def set(self, value): self.value = value


class Widget:
    def __init__(self, manager='grid', disabled=False):
        self.manager, self.disabled = manager, disabled
    def winfo_manager(self): return self.manager
    def grid_remove(self): self.manager = ''
    def pack_forget(self): self.manager = ''
    def instate(self, _states): return self.disabled


def shared_app(module_id):
    app = SimpleNamespace(
        worker=None, child=None, run_state='idle', completed=4, session=None,
        language=Variable('繁體中文'), game_language=Variable('繁體中文'),
        language_label=Widget(), language_choice=Widget(),
        start_key=Variable('F8'), stop_key=Variable('INSERT'),
        start_display=Variable('F8'), stop_display=Variable('INSERT'),
        start_shortcut_display=Variable('F8'), shortcut_display=Variable('INSERT'),
        start_entry=Widget('pack'), stop_entry=Widget('pack'),
        start_key_label=Widget(), stop_key_label=Widget(),
        start_shortcut_label=Widget(), shortcut_label=Widget(),
        start_shortcut_entry=Widget(), shortcut_entry=Widget(),
        field_frames={'start': Widget(), 'stop': Widget(), 'target': Widget()},
        closing=False, _closing=False, reset_confirming=False, help_dialog=None,
        _developer_help_dialog=None, capture_target=None, capturing=None,
        _capturing=False, _shortcut_capturing=False, _hotkey_enabled=True,
        _hotkey_generation=0, generation=0,
        counter=SimpleNamespace(total=7, run_catches=7),
        _holodori_summary={'done': 2, 'target': 3, 'inputs': 20},
        close=Mock(), configure_hotkeys=Mock(), save_settings=Mock(),
        change_language=Mock(), _apply_language=Mock(), apply_language=Mock(), translate=Mock(),
        _snapshot_settings=Mock(), _poll_start_hotkey=Mock(),
        start_hotkey=Mock(), stop_hotkey=Mock(), _hotkey=Mock(), hotkey=Mock(),
        start_listener=Mock(), stop_listener=Mock(),
    )
    if module_id == 'high_low':
        app.start_key, app.stop_key = 'F8', 'INSERT'
    def end_capture():
        app.capture_target = app.capturing = None
        app._capturing = False
    def end_fishing_capture():
        app._shortcut_capturing = False
    app.end_capture = Mock(side_effect=end_capture)
    app._end_shortcut_capture = Mock(side_effect=end_fishing_capture)
    app.form_rows = [app.language_label, app.language_choice, app.field_frames['start'], app.field_frames['target']]
    app.form_labels = [app.language_label, app.start_shortcut_label, app.shortcut_label]
    return app


class RuntimeContractTests(unittest.TestCase):
    def make_session(self, directory, running):
        app = SimpleNamespace(worker=SimpleNamespace(is_alive=lambda: running),
                              counter=SimpleNamespace(total=7, run_catches=7), close=Mock())
        root = SimpleNamespace(after=Mock())
        spec = SimpleNamespace(id='fishing', fields=())
        return EmbeddedSession(root, app, spec, directory), app

    def test_switch_cannot_interrupt_an_active_worker(self):
        with tempfile.TemporaryDirectory() as temporary:
            channel = Path(temporary)
            session, app = self.make_session(channel, True)
            write_json(channel / 'command.json', {'request': 1, 'action': 'deactivate'})
            session.poll()
            self.assertEqual(read_json(channel / 'status.json')['state'], 'blocked')
            app.close.assert_not_called()
            self.assertFalse(session.closing)

    def test_host_close_calls_original_stop_even_while_busy(self):
        with tempfile.TemporaryDirectory() as temporary:
            channel = Path(temporary)
            session, app = self.make_session(channel, True)
            write_json(channel / 'command.json', {'request': 1, 'action': 'close'})
            session.poll()
            app.close.assert_called_once()
            status = read_json(channel / 'status.json')
            self.assertEqual(status['state'], 'closing')
            self.assertEqual(status['snapshot']['_counter']['total'], 7)

    def test_cooking_ready_models_can_close_but_running_models_block_switch(self):
        app = SimpleNamespace(child=object(), run_state='ready')
        self.assertFalse(busy(app, 'cooking'))
        for state in ('loading', 'starting', 'running', 'paused', 'waiting_focus', 'stopping'):
            app.run_state = state
            self.assertTrue(busy(app, 'cooking'), state)

    def test_callback_error_stops_original_worker_and_keeps_traceback(self):
        with tempfile.TemporaryDirectory() as temporary:
            channel = Path(temporary)
            session, app = self.make_session(channel, True)
            session.callback_error(ValueError, ValueError('callback failed'), None)
            app.close.assert_called_once()
            self.assertTrue(session.closing)
            self.assertIn('callback failed', read_json(channel / 'status.json')['errors'][0])

    def test_high_low_restores_actual_shortcuts_as_well_as_labels(self):
        class Variable:
            def __init__(self, value): self.value = value
            def get(self): return self.value
            def set(self, value): self.value = value
        spec = SimpleNamespace(id='high_low', fields=('start_display', 'stop_display'))
        app = SimpleNamespace(start_key='F8', stop_key='INSERT',
            start_display=Variable('F8'), stop_display=Variable('INSERT'),
            start_hotkey=Mock(), stop_hotkey=Mock(), apply_language=Mock())
        saved = snapshot(app, spec)
        saved['_keys'] = dict(start='F7', stop='Ctrl+F10')
        restore(app, spec, saved)
        self.assertEqual(app.start_key, 'F7')
        self.assertEqual(app.stop_key, 'Ctrl+F10')
        self.assertEqual(app.start_display.get(), 'F7')
        app.start_hotkey.configure.assert_called_once_with(value='F7')
        app.stop_hotkey.configure.assert_called_once_with(value='Ctrl+F10')

    def test_shared_controls_stay_hidden_without_removing_other_fields(self):
        app = shared_app('jump_rope')
        self.assertTrue(hide_shared_controls(app))
        self.assertEqual(app.form_rows, [app.field_frames['target']])
        self.assertEqual(app.form_labels, [])
        self.assertEqual(app.field_frames['target'].winfo_manager(), 'grid')
        # The original compact layout can regrid controls during Configure.
        app.language_choice.manager = app.field_frames['start'].manager = 'grid'
        self.assertTrue(hide_shared_controls(app))
        self.assertEqual(app.language_choice.winfo_manager(), '')
        self.assertEqual(app.start_entry.winfo_manager(), '')

    def test_language_uses_each_original_handler_without_restoring_other_state(self):
        for module, handler in (('high_low', 'change_language'), ('fishing', '_apply_language'),
                                ('jump_rope', 'apply_language'), ('cooking', 'translate')):
            with self.subTest(module=module):
                app = shared_app(module)
                keys, summary = shortcut_values(app), app._holodori_summary.copy()
                change_language(app, module, '日本語')
                self.assertEqual(runtime.language_variable(app, module).get(), '日本語')
                getattr(app, handler).assert_called_once()
                self.assertEqual(shortcut_values(app), keys)
                self.assertEqual(app._holodori_summary, summary)
                self.assertEqual(app.counter.total, 7)

    def test_shared_settings_apply_actual_shortcuts_for_every_module(self):
        for module in ('high_low', 'fishing', 'jump_rope', 'cooking'):
            with self.subTest(module=module):
                app = shared_app(module)
                apply_shared_settings(app, module, 'English', 'Ctrl+F7', 'Alt+F10')
                self.assertEqual(shortcut_values(app), dict(start_key='Ctrl+F7', stop_key='Alt+F10'))
                self.assertEqual(app.start_display.get(), 'Ctrl+F7')
                self.assertEqual(app.shortcut_display.get(), 'Alt+F10')
                self.assertEqual(runtime.language_variable(app, module).get(), 'English')
                self.assertTrue(shortcuts_enabled(app, module))
                self.assertEqual(app._holodori_summary['done'], 2)

    def test_invalid_shared_settings_do_not_mutate_any_field_or_listener(self):
        for module in ('high_low', 'fishing', 'jump_rope', 'cooking'):
            with self.subTest(module=module):
                app = shared_app(module)
                with self.assertRaises(ValueError):
                    apply_shared_settings(app, module, 'English', 'F8', 'Ctrl+F8')
                self.assertEqual(shortcut_values(app), dict(start_key='F8', stop_key='INSERT'))
                self.assertEqual(runtime.language_variable(app, module).get(), '繁體中文')
                app.configure_hotkeys.assert_not_called()
                app._hotkey.configure.assert_not_called()

    def test_original_key_contract_distinguishes_windows_alt_from_num_lock(self):
        validate_shared_settings('English', 'F8', 'INSERT')
        capture = runtime._HOTKEY_CONTRACT.captured_hotkey
        self.assertEqual(capture('F8', 0x08, 0x77), 'F8')
        self.assertEqual(capture('F8', 0x20000, 0x77), 'Alt+F8')

    def test_capture_suspends_original_listeners_and_settings_commit_ends_capture(self):
        for module in ('high_low', 'fishing', 'jump_rope', 'cooking'):
            with self.subTest(module=module), tempfile.TemporaryDirectory() as temporary:
                channel = Path(temporary)
                app = shared_app(module)
                root = SimpleNamespace(after=Mock(), after_idle=Mock(), bind=Mock())
                session = EmbeddedSession(root, app, SimpleNamespace(id=module, fields=()), channel)
                write_json(channel / 'command.json', {'request': 1, 'action': 'capture', 'enabled': True, 'target': 'stop'})
                session.poll()
                status = read_json(channel / 'status.json')
                self.assertTrue(status['capture_active'])
                self.assertTrue(status['capture_accepted'])
                listener = {'high_low': app.start_hotkey, 'fishing': app._hotkey,
                            'jump_rope': app.hotkey, 'cooking': app.start_listener}[module]
                listener.configure.assert_any_call(enabled=False)
                write_json(channel / 'command.json', {'request': 2, 'action': 'settings',
                    'language': 'English', 'start_key': 'F7', 'stop_key': 'Ctrl+F10'})
                session.poll()
                status = read_json(channel / 'status.json')
                self.assertTrue(status['settings_accepted'])
                self.assertFalse(status['capture_active'])
                self.assertTrue(status['shared_controls_hidden'])
                self.assertEqual(status['start_key'], 'F7')
                self.assertEqual(status['stop_key'], 'Ctrl+F10')

    def test_live_worker_capture_is_rejected_without_disabling_stop(self):
        with tempfile.TemporaryDirectory() as temporary:
            channel = Path(temporary)
            app = shared_app('high_low')
            app.worker = SimpleNamespace(is_alive=lambda: True)
            session = EmbeddedSession(SimpleNamespace(after=Mock()), app,
                                      SimpleNamespace(id='high_low', fields=()), channel)
            write_json(channel / 'command.json', {'request': 1, 'action': 'capture', 'enabled': True})
            session.poll()
            self.assertFalse(read_json(channel / 'status.json')['capture_accepted'])
            app.start_hotkey.configure.assert_not_called()
            app.stop_hotkey.configure.assert_not_called()

    def test_loaded_cooking_models_and_original_help_block_shortcut_changes(self):
        app = shared_app('cooking')
        app.child = object()
        self.assertFalse(shortcuts_enabled(app, 'cooking'))
        app.child = None
        app.help_dialog = object()
        self.assertFalse(shortcuts_enabled(app, 'cooking'))
        app.help_dialog = None
        app.start_entry.disabled = True
        self.assertFalse(shortcuts_enabled(app, 'cooking'))

    def test_original_high_low_tk_entries_use_native_state_contract(self):
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        try:
            app = shared_app('high_low')
            app.start_entry = tk.Entry(root, state='readonly')
            self.assertTrue(shortcuts_enabled(app, 'high_low'))
            app.start_entry.configure(state='disabled')
            self.assertFalse(shortcuts_enabled(app, 'high_low'))
        finally:
            root.destroy()

    def test_permission_updates_are_conditional_and_keep_dialog_result(self):
        with tempfile.TemporaryDirectory() as temporary:
            channel = Path(temporary)
            app = shared_app('fishing')
            root = SimpleNamespace(after=Mock(), after_idle=Mock(), bind=Mock())
            session = EmbeddedSession(root, app, SimpleNamespace(id='fishing', fields=()), channel)
            session.publish('ready', dialog_checked=True)
            with patch('holodori.runtime.write_json', wraps=write_json) as write:
                session.poll()
                self.assertEqual(write.call_count, 0)
                app.language_choice.disabled = True
                session.poll()
                self.assertEqual(write.call_count, 1)
                status = read_json(channel / 'status.json')
                self.assertFalse(status['language_enabled'])
                self.assertTrue(status['dialog_checked'])
                session.poll()
                self.assertEqual(write.call_count, 1)

    def test_changed_status_is_republished_without_a_settings_change(self):
        class Caption(Widget):
            text = 'Ready'
            def cget(self, name): return self.text if name == 'text' else '#6D43AA'
        with tempfile.TemporaryDirectory() as temporary:
            channel = Path(temporary)
            app = shared_app('fishing')
            app.instructions, app.status = Caption(), Caption()
            session = EmbeddedSession(SimpleNamespace(after=Mock()), app,
                SimpleNamespace(id='fishing', fields=()), channel)
            app.status.text = 'Running'
            session.poll()
            self.assertEqual(read_json(channel / 'status.json')['display_status'], 'Running')


if __name__ == '__main__':
    unittest.main()

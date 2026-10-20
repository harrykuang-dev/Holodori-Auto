"""Shared preference persistence and Windows physical shortcut regression tests."""
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from holodori import settings


class SharedSettingsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.data = Path(self.temporary.name)
        self.environment = mock.patch.dict(os.environ, LOCALAPPDATA=str(self.data))
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.shared = self.data / 'HolodoriAuto' / 'settings.json'
        self.legacy = self.data / 'HololiveDreamsHighLowAuto' / 'settings.json'

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')

    def test_defaults_without_creating_settings_or_changing_returned_defaults(self):
        self.assertEqual(settings.settings_path(), self.shared)
        loaded = settings.load_settings()
        self.assertEqual(loaded, {'language': '繁體中文', 'start_key': 'F8', 'stop_key': 'INSERT'})
        loaded['language'] = 'English'
        self.assertEqual(settings.load_settings()['language'], '繁體中文')
        self.assertFalse(self.shared.exists())

    def test_first_launch_seeds_valid_legacy_preferences_without_writes(self):
        legacy = {'language': 'English', 'start_key': 'alt + ctrl + f7', 'stop_key': 'esc', 'strategy': 1}
        self.write(self.legacy, legacy)
        records = self.legacy.with_name('daily_coins.json')
        records.write_bytes(b'original records')
        before = self.legacy.read_bytes()
        loaded = settings.load_settings()
        self.assertEqual(loaded, {'language': 'English', 'start_key': 'Ctrl+Alt+F7', 'stop_key': 'ESC'})
        self.assertEqual(self.legacy.read_bytes(), before)
        self.assertEqual(records.read_bytes(), b'original records')
        self.assertFalse(self.shared.exists())

    def test_shared_settings_take_precedence_over_legacy(self):
        self.write(self.legacy, {'language': 'English', 'start_key': 'F9', 'stop_key': 'F10'})
        settings.save_settings({'language': '日本語', 'start_key': 'Shift+F8', 'stop_key': 'INSERT'})
        self.assertEqual(settings.load_settings(), {'language': '日本語', 'start_key': 'Shift+F8', 'stop_key': 'INSERT'})

    def test_invalid_shared_data_falls_back_without_overwriting_shared_or_legacy(self):
        self.write(self.legacy, {'language': 'English', 'start_key': 'F9', 'stop_key': 'F10'})
        legacy_before = self.legacy.read_bytes()
        invalid_documents = (
            '{invalid json',
            '[]',
            'null',
            json.dumps({'language': 'French', 'start_key': 'F8', 'stop_key': 'F9'}),
            json.dumps({'language': 'English', 'start_key': 'Ctrl+Alt+A', 'stop_key': 'Alt+Ctrl+A'}),
            json.dumps({'language': 'English', 'start_key': 'F8', 'stop_key': 'Alt+F8'}),
            json.dumps({'language': 'English', 'start_key': None, 'stop_key': 'F9'}),
            json.dumps({'language': 'English', 'start_key': 'Alt', 'stop_key': 'F9'}),
        )
        self.shared.parent.mkdir(parents=True)
        for document in invalid_documents:
            with self.subTest(document=document):
                self.shared.write_text(document, encoding='utf-8')
                before = self.shared.read_bytes()
                self.assertEqual(settings.load_settings(), settings.DEFAULT_SETTINGS)
                self.assertEqual(self.shared.read_bytes(), before)
                self.assertEqual(self.legacy.read_bytes(), legacy_before)

    def test_invalid_legacy_preferences_do_not_create_or_overwrite_files(self):
        invalid_legacy = (
            {'language': 'unsupported', 'start_key': 'F8', 'stop_key': 'F9'},
            {'language': 'English', 'start_key': 'Shift+Ctrl+1', 'stop_key': 'Ctrl+Shift+1'},
            {'language': 'English', 'start_key': 'F8'},
        )
        for legacy in invalid_legacy:
            with self.subTest(legacy=legacy):
                self.write(self.legacy, legacy)
                before = self.legacy.read_bytes()
                self.assertEqual(settings.load_settings(), settings.DEFAULT_SETTINGS)
                self.assertEqual(self.legacy.read_bytes(), before)
                self.assertFalse(self.shared.exists())
        self.legacy.write_text('{broken', encoding='utf-8')
        self.assertEqual(settings.load_settings(), settings.DEFAULT_SETTINGS)
        self.assertEqual(self.legacy.read_text(encoding='utf-8'), '{broken')

    def test_atomic_save_preserves_legacy_data_and_round_trips_all_languages(self):
        self.write(self.legacy, {'language': 'English', 'start_key': 'F9', 'stop_key': 'F10'})
        legacy_before = self.legacy.read_bytes()
        for language in settings.LANGUAGES:
            with self.subTest(language=language):
                settings.save_settings({'language': language, 'start_key': 'shift + ctrl + a', 'stop_key': 'Escape'})
                self.assertEqual(settings.load_settings(), {'language': language, 'start_key': 'Ctrl+Shift+A', 'stop_key': 'ESC'})
        self.assertEqual(self.legacy.read_bytes(), legacy_before)
        self.assertEqual(list(self.shared.parent.glob('.settings-*.tmp')), [])

    def test_atomic_replace_failure_preserves_old_settings_and_removes_temporary(self):
        settings.save_settings(settings.DEFAULT_SETTINGS)
        before = self.shared.read_bytes()
        with mock.patch.object(settings.os, 'replace', side_effect=OSError('simulated locked destination')):
            with self.assertRaises(OSError):
                settings.save_settings({'language': 'English', 'start_key': 'F7', 'stop_key': 'F10'})
        self.assertEqual(self.shared.read_bytes(), before)
        self.assertEqual(list(self.shared.parent.glob('.settings-*.tmp')), [])

    def test_invalid_save_fails_before_any_file_changes(self):
        for bad in (
            {'language': 'French', 'start_key': 'F8', 'stop_key': 'F9'},
            {'language': 'English', 'start_key': 'Ctrl+Alt+A', 'stop_key': 'Alt+Ctrl+A'},
            {'language': 'English', 'start_key': 'F8', 'stop_key': 'Alt+F8'},
            {'language': 'English', 'start_key': 'Alt', 'stop_key': 'F9'},
        ):
            with self.subTest(settings=bad), self.assertRaises(ValueError):
                settings.save_settings(bad)
        self.assertFalse(self.shared.parent.exists())

    def test_num_lock_bit_is_not_alt(self):
        self.assertEqual(settings.captured_hotkey('a', 0x8, 0x41), 'A')
        self.assertEqual(settings.captured_hotkey('F8', 0x8, 0x77), 'F8')

    def test_alt_bit_and_num_lock_plus_alt_produce_alt_once(self):
        self.assertEqual(settings.captured_hotkey('a', 0x20000, 0x41), 'Alt+A')
        self.assertEqual(settings.captured_hotkey('a', 0x20008, 0x41), 'Alt+A')

    def test_modifier_only_keys_are_ignored_and_bare_alt_is_invalid(self):
        for keysym, keycode in (('Alt_L', 0x12), ('Alt_R', 0x12), ('Control_L', 0x11), ('Shift_R', 0x10)):
            with self.subTest(keysym=keysym):
                self.assertIsNone(settings.captured_hotkey(keysym, 0x2000D, keycode))
        with self.assertRaises(ValueError):
            settings.parse_stop_hotkey('Alt')

    def test_shifted_character_uses_its_physical_key(self):
        self.assertEqual(settings.captured_hotkey('exclam', 0x1, 0x31), 'Shift+1')
        self.assertEqual(settings.captured_hotkey('exclam', 0x9, 0x31), 'Shift+1')

    def test_ctrl_alt_combination_and_canonical_conflicts(self):
        self.assertEqual(settings.captured_hotkey('a', 0x20004, 0x41), 'Ctrl+Alt+A')
        self.assertTrue(settings.hotkeys_conflict('Ctrl+Alt+A', 'alt + ctrl + a'))
        self.assertTrue(settings.hotkeys_conflict('Escape', 'ESC'))
        self.assertFalse(settings.hotkeys_conflict('Ctrl+A', 'Alt+A'))
        self.assertEqual(settings.canonical_hotkey('Shift+Alt+Ctrl+f8'), 'Ctrl+Alt+Shift+F8')

    def test_shortcuts_with_subset_modifiers_conflict_like_original_workers(self):
        for first, second in (('F8', 'Alt+F8'), ('Alt+F8', 'F8'), ('Ctrl+A', 'Ctrl+Alt+A')):
            with self.subTest(first=first, second=second):
                self.assertTrue(settings.hotkeys_conflict(first, second))
        self.assertFalse(settings.hotkeys_conflict('Ctrl+A', 'Alt+A'))
        self.assertFalse(settings.hotkeys_conflict('Ctrl+Alt+A', 'Ctrl+Shift+A'))

    def test_helper_load_isolated_from_other_upstream_module_names(self):
        conflicting = SimpleNamespace(parse_stop_hotkey=mock.Mock(side_effect=AssertionError('wrong helper')))
        with mock.patch.dict(sys.modules, hotkey_settings=conflicting):
            self.assertEqual(settings.parse_stop_hotkey('F8'), ((), 0x77))
        conflicting.parse_stop_hotkey.assert_not_called()


if __name__ == '__main__':
    unittest.main()

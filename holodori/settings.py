"""Shared interface language and physical shortcuts for Holodori-Auto.

Keyboard conversion uses the pinned High & Low implementation directly. The
shared preferences have their own data directory; original module data is read
only when seeding the first launch.
"""
from __future__ import annotations

from functools import lru_cache
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile

from .modules import BY_ID


LANGUAGES = ('繁體中文', 'English', '日本語', '한국어', 'Indonesian', '简体中文')
DEFAULT_SETTINGS = {'language': '繁體中文', 'start_key': 'F8', 'stop_key': 'INSERT'}


def _data_root() -> Path:
    return Path(os.environ.get('LOCALAPPDATA') or Path.home() / 'AppData' / 'Local')


def settings_path() -> Path:
    return _data_root() / 'HolodoriAuto' / 'settings.json'


@lru_cache(maxsize=1)
def _load_helper(path: str):
    # A distinct name avoids collisions with other modules' shortcut helpers.
    name = '_holodori_upstream_high_low_hotkey_settings'
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f'Cannot load the upstream shortcut helper: {path}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[name] = module
    return module


def _helper():
    return _load_helper(str(BY_ID['high_low'].path / 'hotkey_settings.py'))


def parse_stop_hotkey(value: str):
    if not isinstance(value, str):
        raise ValueError('A shortcut must be a string')
    return _helper().parse_stop_hotkey(value)


def captured_hotkey(keysym: str, state: int = 0, keycode: int = 0):
    """Use Windows Tk modifier bits and physical keys from the original helper."""
    return _helper().captured_hotkey(keysym, state, keycode)


def hotkeys_conflict(first: str, second: str) -> bool:
    first_modifiers, first_key = parse_stop_hotkey(first)
    second_modifiers, second_key = parse_stop_hotkey(second)
    first_set, second_set = set(first_modifiers), set(second_modifiers)
    # Original worker stop polling accepts extra held modifiers. A bare key
    # and a modified version of that key therefore overlap during gameplay.
    return first_key == second_key and (first_set <= second_set or second_set <= first_set)


def canonical_hotkey(value: str) -> str:
    modifiers, keycode = parse_stop_hotkey(value)
    if 0x70 <= keycode <= 0x87:
        key = f'F{keycode - 0x70 + 1}'
    elif 0x60 <= keycode <= 0x69:
        key = f'NUM{keycode - 0x60}'
    elif 0x30 <= keycode <= 0x39 or 0x41 <= keycode <= 0x5A:
        key = chr(keycode)
    else:
        key = next(name for name, code in _helper().NAMED_KEYS.items() if code == keycode)
    prefixes = [name for code, name in ((0x11, 'Ctrl'), (0x12, 'Alt'), (0x10, 'Shift')) if code in modifiers]
    return '+'.join([*prefixes, key])


def normalize_settings(settings: dict) -> dict:
    if not isinstance(settings, dict):
        raise ValueError('Settings must be an object')
    language = settings.get('language')
    if not isinstance(language, str) or language not in LANGUAGES:
        raise ValueError('Unsupported interface language')
    try:
        start = canonical_hotkey(settings['start_key'])
        stop = canonical_hotkey(settings['stop_key'])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError('Invalid start or stop shortcut') from error
    if hotkeys_conflict(start, stop):
        raise ValueError('Start and stop shortcuts must not overlap')
    return {'language': language, 'start_key': start, 'stop_key': stop}


def _read_settings(path: Path) -> dict:
    return normalize_settings(json.loads(path.read_text(encoding='utf-8-sig')))


def load_settings() -> dict:
    """Read shared preferences, optionally seed from valid legacy preferences.

    Loading never writes files. A damaged existing shared file falls back to
    defaults; only an absent shared file permits first-launch legacy seeding.
    """
    try:
        return _read_settings(settings_path())
    except FileNotFoundError:
        legacy = _data_root() / 'HololiveDreamsHighLowAuto' / 'settings.json'
        try:
            return _read_settings(legacy)
        except (OSError, UnicodeError, ValueError, TypeError):
            return DEFAULT_SETTINGS.copy()
    except (OSError, UnicodeError, ValueError, TypeError):
        return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict) -> None:
    """Validate first, then atomically replace only the shared settings file."""
    normalized = normalize_settings(settings)
    destination = settings_path()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='w', encoding='utf-8', dir=destination.parent,
            prefix='.settings-', suffix='.tmp', delete=False,
        ) as stream:
            temporary = Path(stream.name)
            json.dump(normalized, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

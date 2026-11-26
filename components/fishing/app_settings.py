"""In-memory counters and validated, persistent shortcut preferences."""
import json
import os
from pathlib import Path
import tempfile

from holodori.physical_keys import NAMED_KEYS, captured_hotkey, parse_stop_hotkey

DEFAULT_SHORTCUTS = {'start_key': 'F8', 'stop_key': 'F9'}


def shortcuts_path():
    return Path(os.environ.get('LOCALAPPDATA', Path.home()/'AppData'/'Local'))/'HololiveFishingAuto'/'shortcuts.json'


def validated_shortcuts(values):
    if not isinstance(values, dict):
        raise ValueError('Shortcut preferences must be an object')
    result = {key: values.get(key) for key in DEFAULT_SHORTCUTS}
    if not all(isinstance(value, str) for value in result.values()):
        raise ValueError('Start and stop shortcuts must be strings')
    result = {key: value.strip() for key, value in result.items()}
    if hotkeys_conflict(result['start_key'], result['stop_key']):
        raise ValueError('Start and stop shortcuts must not overlap')
    return result


def load_shortcuts():
    try:
        return validated_shortcuts(json.loads(shortcuts_path().read_text(encoding='utf-8-sig')))
    except (OSError, UnicodeError, ValueError, TypeError):
        return DEFAULT_SHORTCUTS.copy()


def save_shortcuts(values):
    normalized = validated_shortcuts(values)
    destination = shortcuts_path()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=destination.parent,
                                         prefix='.shortcuts-', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(normalized, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

def stop_hotkey_pressed(value, get_state):
    modifiers,vk = parse_stop_hotkey(value)
    return bool(get_state(vk)&0x8000) and all(get_state(m)&0x8000 for m in modifiers)


def hotkeys_conflict(first, second):
    a, av = parse_stop_hotkey(first)
    b, bv = parse_stop_hotkey(second)
    return av == bv and (set(a) <= set(b) or set(b) <= set(a))


class StartHotkey:
    """Consume held keys even when disabled; only a fresh press can start."""
    def __init__(self):
        self.binding = None
        self.armed = False

    def disarm(self):
        self.armed = False

    def poll(self, value, get_state, enabled=True):
        mods, key = parse_stop_hotkey(value)
        binding = (frozenset(mods), key)
        if binding != self.binding:
            self.binding = binding
            self.armed = False
        if not get_state(key) & 0x8000:
            self.armed = True
            return False
        exact = all(bool(get_state(m) & 0x8000) == (m in mods)
                    for m in (0x11, 0x12, 0x10))
        exact = exact and not any(get_state(m) & 0x8000 for m in (0x5B, 0x5C))
        fire = self.armed and enabled and exact
        self.armed = False
        return fire


class FishingCounter:
    """In-memory count for one start; never reads/writes files."""
    def __init__(self):
        self.total = 0
        self.run_catches = 0

    def begin_run(self):
        self.total = 0
        self.run_catches = 0

    def update(self, catches):
        if catches < self.run_catches:
            raise ValueError('Catch count moved backwards within a run')
        self.total += catches-self.run_catches
        self.run_catches = catches
        return self.total

    def remaining(self, target):
        return max(0,target-self.total) if target else 0

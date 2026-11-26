"""In-memory UI counters and validated global shortcuts."""
from holodori.physical_keys import NAMED_KEYS, captured_hotkey, parse_stop_hotkey


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

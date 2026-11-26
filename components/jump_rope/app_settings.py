"""Global stop shortcut settings for the jump-rope assistant."""
from holodori.physical_keys import NAMED_KEYS, captured_hotkey, parse_stop_hotkey


def stop_hotkey_pressed(value, get_state):
    modifiers,vk = parse_stop_hotkey(value)
    return bool(get_state(vk)&0x8000) and all(get_state(m)&0x8000 for m in modifiers)

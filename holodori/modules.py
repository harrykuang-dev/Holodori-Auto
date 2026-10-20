"""Small integration contract; game algorithms live in the original projects."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import sys

ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))


@dataclass(frozen=True)
class Module:
    id: str
    entry: str
    app_class: str
    accent: str
    icon: str
    fields: tuple[str, ...]

    @property
    def path(self):
        return ROOT / 'upstream' / self.id


MODULES = (
    Module('high_low', 'main_ui', 'HololiveBotUI', '#6D43AA', 'icon_transparent.png',
           ('language', 'strategy', 'start_display', 'stop_display')),
    Module('fishing', 'gui', 'FishingApp', '#72B6E8', 'assets/fishing-hook.png',
           ('game_language', 'target_mode', 'target_amount', 'target', 'start_key',
            'start_shortcut_display', 'stop_key', 'shortcut_display', 'diagnostics')),
    Module('jump_rope', 'main_ui', 'JumpRopeApp', '#FFE36A', 'assets/jump-rope.png',
           ('language', 'target', 'start_key', 'start_shortcut_display', 'stop_key',
            'shortcut_display', 'diagnostics', 'timing')),
    Module('cooking', 'gui', 'CookingApp', '#F15B60', 'assets/cooking-icon.png',
           ('language', 'model', 'games', 'developer_mode', 'start_key', 'stop_key',
            'start_display', 'stop_display')),
)
BY_ID = {module.id: module for module in MODULES}


def versions():
    try:
        return json.loads((ROOT / 'upstream-lock.json').read_text(encoding='utf-8'))['modules']
    except (OSError, ValueError, KeyError):
        return {}

"""Atomic, session-local IPC. No game data is transferred or rewritten."""
from __future__ import annotations

import json
from pathlib import Path


def write_json(path: Path, data):
    temporary = path.with_suffix('.pending')
    temporary.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    temporary.replace(path)


def read_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return default

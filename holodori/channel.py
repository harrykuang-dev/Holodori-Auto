"""Atomic, session-local IPC. No game data is transferred or rewritten."""
from __future__ import annotations

import json
from pathlib import Path
import time


def write_json(path: Path, data):
    temporary = path.with_suffix('.pending')
    temporary.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    # Windows can briefly deny replacement while the other process reads it.
    for attempt in range(10):
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if attempt == 9:
                raise
            time.sleep(0.01)


def read_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return default

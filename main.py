"""Holodori-Auto desktop entry point and isolated upstream dispatch."""
from __future__ import annotations

import multiprocessing
import sys


def main():
    multiprocessing.freeze_support()
    if '--check-jump-model-only' in sys.argv:
        from holodori.runtime import check_jump_model
        check_jump_model()
    elif '--worker' in sys.argv:
        from holodori.runtime import cooking_worker
        cooking_worker()
    elif '--embedded' in sys.argv:
        from holodori.runtime import embedded_main
        embedded_main()
    else:
        from holodori.app import main as desktop_main
        desktop_main()


if __name__ == '__main__':
    main()

"""Entry point for YT-TUI."""
from __future__ import annotations

import sys


def _check_python() -> None:
    if sys.version_info < (3, 10):
        sys.exit(f"[yt-tui] Python 3.10+ required (got {sys.version})")


def main() -> None:
    _check_python()
    incognito = len(sys.argv) > 1 and sys.argv[1] in ("incog", "incognito", "--incog")
    from yt_tui.ui import YtApp
    YtApp(incognito=incognito).run()


if __name__ == "__main__":
    main()

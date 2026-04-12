"""Entry point for YT-CLI."""
from __future__ import annotations

import sys


def _check_python() -> None:
    if sys.version_info < (3, 10):
        sys.exit(f"[yt-cli] Python 3.10+ required (got {sys.version})")


def main() -> None:
    _check_python()
    from ui import YtApp
    YtApp().run()


if __name__ == "__main__":
    main()

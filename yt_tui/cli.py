"""Entry point for YT-TUI."""
from __future__ import annotations

import argparse
import sys

from yt_tui import __version__


def _check_python() -> None:
    if sys.version_info < (3, 10):
        sys.exit(f"[yt-tui] Python 3.10+ required (got {sys.version})")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="yt-tui",
        description="Terminal-native YouTube client — search, preview, and stream videos.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"yt-tui {__version__}",
    )
    parser.add_argument(
        "incog",
        nargs="?",
        const="incog",
        default=None,
        help="Run in incognito mode (no history saved)",
    )
    return parser


def main() -> None:
    _check_python()
    parser = _build_parser()
    args = parser.parse_args()

    incognito = args.incog in ("incog", "incognito", "--incog")

    from yt_tui.ui import YtApp

    YtApp(incognito=incognito).run()


if __name__ == "__main__":
    main()

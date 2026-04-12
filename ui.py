"""Textual TUI layer for YT-CLI."""
from __future__ import annotations

import asyncio
import sys
from typing import ClassVar

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Static,
    Button,
)

import player
import search
import thumbnail
from utils import fmt_duration, fmt_views

LOGO = """\
 ██╗   ██╗████████╗      ██████╗██╗     ██╗
 ╚██╗ ██╔╝╚══██╔══╝     ██╔════╝██║     ██║
  ╚████╔╝    ██║   █████╗██║     ██║     ██║
   ╚██╔╝     ██║   ╚════╝██║     ██║     ██║
    ██║      ██║         ╚██████╗███████╗██║
    ╚═╝      ╚═╝          ╚═════╝╚══════╝╚═╝"""

HELP_TEXT = """\
[b]Keyboard Reference[/b]

  [yellow]/[/yellow]          Focus search bar
  [yellow]↑ / ↓[/yellow]      Move through results
  [yellow]Enter[/yellow]      Play selected video
  [yellow]q[/yellow]          Quit
  [yellow]?[/yellow]          Toggle this help screen

[b]During mpv playback[/b]

  [yellow]Space[/yellow]      Pause / resume
  [yellow]← / →[/yellow]      Seek backward / forward
  [yellow]↑ / ↓[/yellow]      Volume up / down
  [yellow]q[/yellow]          Stop and return to YT-CLI
"""


class HelpScreen(ModalScreen):
    BINDINGS: ClassVar = [Binding("escape,q,?", "dismiss", "Close")]

    def compose(self) -> ComposeResult:
        yield Static(HELP_TEXT, id="help-box")

    def on_mount(self) -> None:
        self.query_one("#help-box").styles.padding = (2, 4)


class PlaybackChoice(ModalScreen[bool]):
    def compose(self) -> ComposeResult:
        with Vertical(id="choice-dialog"):
            yield Label("Play as:", id="choice-title")
            with Horizontal(id="choice-buttons"):
                yield Button("Video", variant="primary", id="video")
                yield Button("Audio", variant="success", id="audio")
            yield Label("Press Escape to cancel", id="choice-hint")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "video":
            self.dismiss(False)
        else:
            self.dismiss(True)



class YtApp(App):
    CSS = """
    Screen { background: $surface; }

    #logo { color: $accent; text-align: center; padding: 1 0 0 0; }

    #search-bar { dock: top; height: 3; padding: 0 1; }

    #main { height: 1fr; }

    #results { width: 2fr; border: solid $primary; }

    #info-panel {
        width: 1fr;
        border-left: solid $primary;
        padding: 1 2;
        overflow-y: auto;
    }

    #thumb {
        height: 18;
        width: 100%;
        margin-bottom: 1;
        border: round $accent;
        overflow: hidden;
    }

    #info-title {
        text-style: bold;
        margin-bottom: 1;
    }

    #info-meta {
        margin-bottom: 1;
    }

    #status {
        dock: bottom;
        height: 1;
        background: $primary;
        color: $text;
        padding: 0 1;
    }

    HelpScreen > Static {
        background: $surface;
        border: double $accent;
        width: 60;
        height: auto;
        margin: 4 8;
    }

    #choice-dialog {
        background: $surface;
        border: thick $primary;
        width: 40;
        height: auto;
        padding: 1 2;
        content-align: center middle;
    }

    #choice-title {
        text-style: bold;
        margin-bottom: 1;
    }

    #choice-buttons {
        height: auto;
        align: center middle;
        margin-bottom: 1;
    }

    #choice-buttons Button {
        margin: 0 1;
    }

    #choice-hint {
        color: $text-muted;
    }

    """

    BINDINGS: ClassVar = [
        Binding("/", "focus_search", "Search", show=True),
        Binding("a", "toggle_autoplay", "Autoplay", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("?", "help", "Help", show=True),
    ]


    def __init__(self) -> None:
        super().__init__()
        self._results: list[dict] = []
        self._current_thumb_task: asyncio.Task | None = None
        self._autoplay: bool = False
        self._is_playlist_mode: bool = False
        self._audio_only_pref: bool = False

    # ── Layout ────────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(LOGO, id="logo")
        yield Input(placeholder="Search YouTube…  (press / to focus)", id="search-bar")
        with Horizontal(id="main"):
            yield DataTable(id="results", cursor_type="row", zebra_stripes=True)
            with Vertical(id="info-panel"):
                yield Static("", id="thumb")
                yield Label("Select a video to preview", id="info-title")
                yield Label("", id="info-meta")
        yield Static("Ready", id="status")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Title", "Channel", "Duration", "Views")
        self.query_one("#search-bar", Input).focus()

    # ── Search ────────────────────────────────────────────────────────────────

    @on(Input.Submitted, "#search-bar")
    def handle_search(self, event: Input.Submitted) -> None:
        query = event.value.strip()
        if not query:
            return
        self._set_status(f"Searching: {query}…")
        self._do_search(query)

    @work(thread=True)
    def _do_search(self, query: str) -> None:
        try:
            results, is_playlist = search.search_youtube(query)
        except Exception as exc:
            self.call_from_thread(self._set_status, f"Search error: {exc}")
            return
        self.call_from_thread(self._populate_results, results, is_playlist)

    def _populate_results(self, results: list[dict], is_playlist: bool) -> None:
        self._results = results
        self._is_playlist_mode = is_playlist
        if is_playlist:
            self._autoplay = True
        
        table = self.query_one(DataTable)
        table.clear()
        if not results:
            self._set_status("No results found.")
            return
        for r in results:
            table.add_row(
                r["title"][:60],
                r["channel"][:30],
                fmt_duration(r["duration"]),
                fmt_views(r["views"]),
            )
        self._set_status(f"{len(results)} results")
        table.focus()
        table.move_cursor(row=0)

    # ── Info panel + thumbnail ────────────────────────────────────────────────

    @on(DataTable.RowHighlighted, "#results")
    def handle_highlight(self, event: DataTable.RowHighlighted) -> None:
        idx = event.cursor_row
        if idx < 0 or idx >= len(self._results):
            return
        r = self._results[idx]
        self.query_one("#info-title", Label).update(r["title"])
        self.query_one("#info-meta", Label).update(
            f"[cyan]{r['channel']}[/cyan]  "
            f"[yellow]{fmt_duration(r['duration'])}[/yellow]  "
            f"{fmt_views(r['views'])} views"
        )
        self.query_one("#thumb", Static).update("")
        if r.get("thumbnail"):
            self._fetch_thumb(r["thumbnail"])

    @work(exclusive=True)
    async def _fetch_thumb(self, url: str) -> None:
        from rich.text import Text
        rendered = await thumbnail.render(url, width=36)
        if rendered:
            self.query_one("#thumb", Static).update(Text.from_ansi(rendered))

    # ── Playback ──────────────────────────────────────────────────────────────

    @on(DataTable.RowSelected, "#results")
    def handle_select(self, event: DataTable.RowSelected) -> None:
        idx = event.cursor_row
        if idx < 0 or idx >= len(self._results):
            return
        
        def check_choice(audio_only: bool | None) -> None:
            if audio_only is not None:
                self._audio_only_pref = audio_only
                self._play_session(idx)

        self.push_screen(PlaybackChoice(), check_choice)

    @work(thread=False, exclusive=True)
    async def _play_session(self, start_idx: int) -> None:
        import asyncio
        table = self.query_one(DataTable)
        
        for i in range(start_idx, len(self._results)):
            item = self._results[i]
            
            # Sync table selection so user knows what is playing
            self.call_from_thread(table.move_cursor, row=i)
            self._set_status(f"Playing [{i+1}/{len(self._results)}]: {item['title']}")
            
            with self.app.suspend():
                cmd = ["mpv", "--really-quiet", item["url"]]
                if self._audio_only_pref:
                    cmd.append("--no-video")
                proc = await asyncio.create_subprocess_exec(*cmd)
                await proc.wait()
            
            if not self._autoplay:
                break
                
        self._set_status("Finished playback session")


    # ── Actions ───────────────────────────────────────────────────────────────

    def action_toggle_autoplay(self) -> None:
        self._autoplay = not self._autoplay
        self._set_status(f"Autoplay: {'ON' if self._autoplay else 'OFF'}")

    def action_focus_search(self) -> None:
        self.query_one("#search-bar", Input).focus()

    def action_help(self) -> None:
        self.push_screen(HelpScreen())

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _set_status(self, msg: str) -> None:
        ap_status = "[green]AP:ON[/]" if self._autoplay else "[red]AP:OFF[/]"
        self.query_one("#status", Static).update(f"{ap_status} | {msg}")

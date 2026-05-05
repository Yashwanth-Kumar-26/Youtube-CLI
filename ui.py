"""Textual TUI layer for YT-CLI."""
from __future__ import annotations

import asyncio
import os
import shutil
import sys
from typing import ClassVar

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, Container, ContentSwitcher
from textual.screen import ModalScreen
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Static,
    Button,
    LoadingIndicator,
    TabbedContent,
    TabPane,
    ListItem,
    ListView,
)

import player
import search
import thumbnail
from utils import fmt_duration, fmt_views, HistoryManager

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
    $accent-primary: #89b4fa;
    $accent-secondary: #f5c2e7;
    $bg-main: #1e1e2e;
    $bg-sidebar: #181825;
    $fg-main: #cdd6f4;
    $fg-muted: #7f849c;

    Screen {
        background: $bg-main;
        color: $fg-main;
    }

    #sidebar {
        width: 25;
        background: $bg-sidebar;
        border-right: solid #313244;
        dock: left;
    }

    #sidebar-logo {
        height: 6;
        content-align: center middle;
        color: $accent-primary;
        text-style: bold;
        border-bottom: solid #313244;
    }

    #nav-list {
        background: transparent;
    }

    #nav-list ListItem {
        padding: 1 2;
    }

    #nav-list ListItem:hover {
        background: #313244;
    }

    #nav-list ListItem.--highlight {
        background: $accent-primary;
        color: $bg-main;
        text-style: bold;
    }

    #content {
        height: 1fr;
    }

    #search-view, #history-view {
        height: 1fr;
    }

    #search-header {
        height: 3;
        padding: 0 1;
        margin-bottom: 1;
    }

    #results-container {
        height: 1fr;
    }

    #results {
        border: none;
        background: transparent;
    }

    #info-panel {
        width: 40;
        border-left: solid #313244;
        padding: 1 2;
        background: $bg-sidebar;
    }

    #thumb {
        height: 15;
        width: 100%;
        margin-bottom: 1;
        border: solid $accent-primary;
        content-align: center middle;
    }

    #info-title {
        text-style: bold;
        color: $accent-secondary;
        margin-bottom: 1;
    }

    #status {
        dock: bottom;
        height: 1;
        background: $accent-primary;
        color: $bg-main;
        padding: 0 1;
        text-style: bold;
    }

    #loading-overlay {
        width: 100%;
        height: 100%;
        content-align: center middle;
        background: rgba(30, 30, 46, 0.7);
        display: none;
    }

    #loading-overlay.visible {
        display: block;
    }

    HelpScreen > Static {
        background: $bg-sidebar;
        border: double $accent-primary;
        width: 60;
        height: auto;
        padding: 1 2;
    }

    #choice-dialog {
        background: $bg-sidebar;
        border: thick $accent-primary;
        width: 40;
        height: auto;
        padding: 1 2;
    }

    .section-title {
        text-style: bold;
        color: $accent-primary;
        padding: 1 2;
        background: #313244;
        width: 100%;
    }
    """

    BINDINGS: ClassVar = [
        Binding("/", "focus_search", "Search", show=True),
        Binding("a", "toggle_autoplay", "Autoplay", show=True),
        Binding("h", "switch_view('history')", "History", show=True),
        Binding("s", "switch_view('search')", "Search Tab", show=True),
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
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Static("YT-CLI", id="sidebar-logo")
                with ListView(id="nav-list"):
                    yield ListItem(Label("🔍 Search"), id="nav-search")
                    yield ListItem(Label("📜 History"), id="nav-history")
            
            with Vertical(id="content"):
                with ContentSwitcher(initial="search"):
                    with Vertical(id="search"):
                        yield Input(placeholder="Search YouTube…", id="search-bar")
                        with Horizontal(id="results-container"):
                            yield DataTable(id="results", cursor_type="row", zebra_stripes=True)
                            with Vertical(id="info-panel"):
                                yield Static("No Preview", id="thumb")
                                yield Label("Select a video", id="info-title")
                                yield Label("", id="info-meta")
                        with Container(id="loading-overlay"):
                            yield LoadingIndicator()
                    
                    with Vertical(id="history"):
                        yield Label("Search History", classes="section-title")
                        yield DataTable(id="history-table", cursor_type="row", zebra_stripes=True)

        yield Static("Ready", id="status")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#results", DataTable)
        table.add_columns("Title", "Channel", "Duration", "Views")
        
        hist_table = self.query_one("#history-table", DataTable)
        hist_table.add_columns("Query", "Timestamp")
        self._refresh_history()
        
        self.query_one("#search-bar", Input).focus()

    def _refresh_history(self) -> None:
        hist_table = self.query_one("#history-table", DataTable)
        hist_table.clear()
        for h in HistoryManager.get_search_history():
            hist_table.add_row(h["query"], h["timestamp"])

    # ── Search ────────────────────────────────────────────────────────────────

    @on(Input.Submitted, "#search-bar")
    def handle_search(self, event: Input.Submitted) -> None:
        query = event.value.strip()
        if not query:
            return
        HistoryManager.add_search(query)
        self._refresh_history()
        self.query_one("#loading-overlay").add_class("visible")
        self._set_status(f"Searching: {query}…")
        self._do_search(query)

    @work(thread=True)
    def _do_search(self, query: str) -> None:
        try:
            results, is_playlist = search.search_youtube(query)
        except Exception as exc:
            self.call_from_thread(self._handle_search_error, exc)
            return
        self.call_from_thread(self._populate_results, results, is_playlist)

    def _handle_search_error(self, exc: Exception) -> None:
        self.query_one("#loading-overlay").remove_class("visible")
        self._set_status(f"Search error: {exc}")

    def _populate_results(self, results: list[dict], is_playlist: bool) -> None:
        self.query_one("#loading-overlay").remove_class("visible")
        self._results = results
        self._is_playlist_mode = is_playlist
        if is_playlist:
            self._autoplay = True
        
        table = self.query_one("#results", DataTable)
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
        try:
            table = self.query_one("#results", DataTable)
            ytdl_path = player.find_tool("yt-dlp")
            
            for i in range(start_idx, len(self._results)):
                item = self._results[i]
                table.move_cursor(row=i)
                self._set_status(f"Playing [{i+1}/{len(self._results)}]: {item['title']}")
                HistoryManager.add_watch(item)
                
                with self.app.suspend():
                    exit_code = player.play(
                        item["url"], 
                        audio_only=self._audio_only_pref,
                        ytdl_path=ytdl_path
                    )
                
                if not self._autoplay or exit_code == 4: # 4 is user quit in mpv
                    break
                    
        except Exception as e:
            self._set_status(f"Playback error: {e}")
                
        self._set_status("Finished playback session")


    # ── Actions ───────────────────────────────────────────────────────────────

    def action_toggle_autoplay(self) -> None:
        self._autoplay = not self._autoplay
        self._set_status(f"Autoplay: {'ON' if self._autoplay else 'OFF'}")

    def action_focus_search(self) -> None:
        self.action_switch_view("search")
        self.query_one("#search-bar", Input).focus()

    def action_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_switch_view(self, view: str) -> None:
        self.query_one(ContentSwitcher).current = view
        if view == "search":
            self.query_one("#nav-list").index = 0
            self.query_one("#search-bar").focus()
        else:
            self.query_one("#nav-list").index = 1
            self.query_one("#history-table").focus()
            self._refresh_history()

    @on(ListView.Selected, "#nav-list")
    def handle_nav(self, event: ListView.Selected) -> None:
        if event.item.id == "nav-search":
            self.action_switch_view("search")
        elif event.item.id == "nav-history":
            self.action_switch_view("history")

    @on(DataTable.RowSelected, "#history-table")
    def handle_history_select(self, event: DataTable.RowSelected) -> None:
        row_data = self.query_one("#history-table", DataTable).get_row_at(event.cursor_row)
        query = row_data[0]
        self.query_one("#search-bar", Input).value = str(query)
        self.action_switch_view("search")
        self.handle_search(Input.Submitted(self.query_one("#search-bar", Input), str(query)))

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _set_status(self, msg: str) -> None:
        ap_status = "[green]AP:ON[/]" if self._autoplay else "[red]AP:OFF[/]"
        self.query_one("#status", Static).update(f"{ap_status} | {msg}")

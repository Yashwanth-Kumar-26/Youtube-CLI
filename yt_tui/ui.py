"""Textual TUI layer for YT-TUI."""
from __future__ import annotations

import asyncio
import logging
from typing import ClassVar

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, Container
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    ContentSwitcher,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    LoadingIndicator,
    Static,
)

import yt_tui.player as player
import yt_tui.search as search
import yt_tui.thumbnail as thumbnail
from yt_tui.search import SearchResult
from yt_tui.utils import fmt_duration, fmt_views, HistoryManager

logger = logging.getLogger(__name__)

LOGO = """\
 ██╗   ██╗████████╗      ██████╗██╗     ██╗
 ╚██╗ ██╔╝╚══██╔══╝     ██╔════╝██║     ██║
  ╚████╔╝    ██║   █████╗██║     ██║     ██║
   ╚██╔╝     ██║   ╚════╝██║     ██║     ██║
    ██║      ██║         ╚██████╗███████╗██║
    ╚═╝      ╚═╝          ╚═════╝╚══════╝╚═╝"""

HELP_TEXT = """\
[b]Keyboard Reference[/b]

  [yellow]F1[/yellow]          Toggle this help screen
  [yellow]/[/yellow]          Focus search bar
  [yellow]↑ / ↓[/yellow]      Move through results
  [yellow]Enter[/yellow]      Play selected video
  [yellow]Ctrl+Q[/yellow]     Quit

[b]During mpv playback[/b]

  [yellow]Space[/yellow]      Pause / resume
  [yellow]← / →[/yellow]      Seek backward / forward
  [yellow]↑ / ↓[/yellow]      Volume up / down
  [yellow]q[/yellow]          Stop and return to YT-TUI
"""


class HelpScreen(ModalScreen):
    BINDINGS: ClassVar = [Binding("escape,?", "dismiss", "Close")]

    def compose(self) -> ComposeResult:
        yield Static(HELP_TEXT, id="help-box")

    def on_mount(self) -> None:
        self.query_one("#help-box").styles.padding = (2, 4)


class PlaybackChoice(ModalScreen[bool | None]):
    BINDINGS: ClassVar = [Binding("escape", "cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        with Vertical(id="choice-dialog"):
            yield Label("Play as:", id="choice-title")
            with Horizontal(id="choice-buttons"):
                yield Button("Video", variant="primary", id="video")
                yield Button("Audio", variant="success", id="audio")
            yield Label("Press Escape to cancel", id="choice-hint")

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "video":
            self.dismiss(False)
        else:
            self.dismiss(True)



class YtApp(App):
    CSS_PATH = "ui.tcss"

    BINDINGS: ClassVar = [
        Binding("/", "focus_search", "Search", show=True),
        Binding("a", "toggle_autoplay", "Autoplay", show=True),
        Binding("h", "switch_view('history')", "History", show=True),
        Binding("s", "switch_view('search')", "Search Tab", show=True),
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("f1", "help", "Help", show=True),
    ]


    def __init__(self, incognito: bool = False) -> None:
        super().__init__()
        self._incognito = incognito
        self._results: list[SearchResult] = []
        self._current_thumb_task: asyncio.Task | None = None
        self._autoplay: bool = False
        self._is_playlist_mode: bool = False
        self._audio_only_pref: bool = False

    # ── Layout ────────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Static("YT-TUI INCOG" if self._incognito else "YT-TUI", id="sidebar-logo")
                with ListView(id="nav-list"):
                    yield ListItem(Label("Search"), id="nav-search")
                    yield ListItem(Label("History"), id="nav-history")
            
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
        if self._incognito:
            return
        for h in HistoryManager.get_search_history():
            hist_table.add_row(h["query"], h["timestamp"])

    # ── Search ────────────────────────────────────────────────────────────────

    def _execute_search(self, query: str) -> None:
        """Initiate a search for the given query string."""
        if not self._incognito:
            HistoryManager.add_search(query)
        self._refresh_history()
        self.query_one("#loading-overlay").add_class("visible")
        self._set_status(f"Searching: {query}…")
        self._do_search(query)

    @on(Input.Submitted, "#search-bar")
    def handle_search(self, event: Input.Submitted) -> None:
        query = event.value.strip()
        if not query:
            return
        self._execute_search(query)

    @work(thread=True)
    def _do_search(self, query: str) -> None:
        try:
            results, is_playlist = search.search_youtube(query, max_results=50)
        except Exception as exc:
            self.call_from_thread(self._handle_search_error, exc)
            return
        self.call_from_thread(self._populate_results, results, is_playlist)

    def _handle_search_error(self, exc: Exception) -> None:
        self.query_one("#loading-overlay").remove_class("visible")
        self._set_status(f"Search error: {exc}")

    def _populate_results(self, results: list[SearchResult], is_playlist: bool) -> None:
        self.query_one("#loading-overlay").remove_class("visible")
        self._results = results
        self._is_playlist_mode = is_playlist
        if is_playlist and not self._autoplay:
            self._autoplay = True
            self._set_status("Playlist loaded — Autoplay ON")

        table = self.query_one("#results", DataTable)
        table.clear()
        if not results:
            self._set_status("No results found.")
            return
        for r in results:
            table.add_row(
                r.title[:60],
                r.channel[:30],
                fmt_duration(r.duration),
                fmt_views(r.views),
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
        self.query_one("#info-title", Label).update(r.title)
        self.query_one("#info-meta", Label).update(
            f"[cyan]{r.channel}[/cyan]  "
            f"[yellow]{fmt_duration(r.duration)}[/yellow]  "
            f"{fmt_views(r.views)} views"
        )
        self.query_one("#thumb", Static).update("")
        logger.debug(f"handle_highlight: thumbnail URL: {r.thumbnail}")
        if r.thumbnail:
            self._fetch_thumb(r.thumbnail)

    @work(exclusive=True)
    async def _fetch_thumb(self, url: str) -> None:
        from rich.text import Text
        from textual.content import Content
        thumb_widget = self.query_one("#thumb", Static)
        thumb_widget.update(Text("Loading thumbnail...", style="italic cyan"))
        logger.debug(f"_fetch_thumb: url={url}")

        rendered = await thumbnail.render(url, width=38)
        logger.debug(f"_fetch_thumb: rendered length={len(rendered)}")
        if rendered:
            thumb_widget.update(Content.from_rich_text(Text.from_ansi(rendered)))
        else:
            thumb_widget.update(Text("Preview unavailable", style="red"))

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
                self._set_status(f"Playing [{i+1}/{len(self._results)}]: {item.title}")
                if not self._incognito:
                    HistoryManager.add_watch({
                        "id": item.id,
                        "title": item.title,
                        "channel": item.channel,
                        "url": item.url,
                        "duration": item.duration,
                        "views": item.views,
                    })

                if self._audio_only_pref:
                    # Audio: await each track before starting the next
                    await self._play_audio_track(item.url, ytdl_path)
                    self._set_status(f"Audio: {item.title}")
                    if not self._autoplay:
                        break
                    continue

                with self.app.suspend():
                    exit_code = await player.play_async(
                        item.url,
                        audio_only=False,
                        ytdl_path=ytdl_path
                    )

                if not self._autoplay or exit_code == 4:
                    break

        except Exception as e:
            self._set_status(f"Playback error: {e}")

        self._set_status("Finished playback session")

    async def _play_audio_track(self, url: str, ytdl_path: str | None) -> None:
        """Play one audio track, awaiting mpv to finish (keeps TUI responsive)."""
        try:
            await player.play_async(url, audio_only=True, ytdl_path=ytdl_path)
        except asyncio.CancelledError:
            raise
        except Exception:
            self._set_status("Audio playback failed")


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
        query = str(row_data[0])
        self.query_one("#search-bar", Input).value = query
        self.action_switch_view("search")
        self._execute_search(query)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _set_status(self, msg: str) -> None:
        ap_status = "[green]AP:ON[/]" if self._autoplay else "[red]AP:OFF[/]"
        incog_prefix = f"[yellow]INCOG[/] {ap_status}" if self._incognito else ap_status
        self.query_one("#status", Static).update(f"{incog_prefix} | {msg}")

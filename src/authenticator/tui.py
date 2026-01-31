from __future__ import annotations

from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable, Footer, Header, Static

from authenticator.core import TOTPGenerator
from authenticator.storage import Storage


class TotpApp(App):
    CSS = """
    Screen {
        background: #0d1117;
        color: #c9d1d9;
    }

    #main {
        padding: 1 2;
        height: 100%;
    }

    #title {
        text-style: bold;
        color: #58a6ff;
        margin-bottom: 1;
    }

    #hint {
        color: #8b949e;
        margin-top: 1;
    }

    DataTable {
        background: #0b0f14;
        border: round #30363d;
        padding: 1;
        height: 1fr;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("escape", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._storage = Storage()
        self._keys: dict[str, str] = {}
        self._generators: dict[str, TOTPGenerator] = {}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="main"):
            yield Static("TOTP Dashboard", id="title")
            yield DataTable(id="table")
            yield Static("Press q or Esc to return", id="hint")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_column("NAME", width=24)
        table.add_column("CODE")
        table.add_column("VALID")
        table.add_column("RING")
        table.zebra_stripes = True
        self._reload_keys()
        self.refresh_table()
        self.set_interval(1, self.refresh_table)

    def _reload_keys(self) -> None:
        self._keys = self._storage.list_keys()
        self._generators = {
            name: TOTPGenerator(secret) for name, secret in self._keys.items()
        }

    @staticmethod
    def _ring(remaining: int, period: int = 30) -> str:
        steps = ["○", "◔", "◑", "◕", "●"]
        progress = 1 - (remaining / period)
        index = int(progress * (len(steps) - 1))
        index = max(0, min(index, len(steps) - 1))
        return steps[index]

    def refresh_table(self) -> None:
        table = self.query_one(DataTable)
        latest_keys = self._storage.list_keys()
        if latest_keys != self._keys:
            self._reload_keys()

        table.clear()
        if not self._keys:
            table.add_row("No stored secrets", "-", "-", "-")
            return

        for name in sorted(self._generators.keys()):
            gen = self._generators[name]
            code = gen.now()
            remaining = gen.remaining()

            if remaining <= 5:
                color = "red"
            elif remaining <= 10:
                color = "yellow"
            else:
                color = "green"

            code_text = Text(code, style=f"bold {color}")
            remaining_text = Text(f"{remaining:2d}s", style=color)
            ring_text = Text(self._ring(remaining), style=color)

            table.add_row(name, code_text, remaining_text, ring_text)


def run_panel() -> None:
    TotpApp().run()

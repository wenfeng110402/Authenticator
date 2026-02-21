from __future__ import annotations

import pyperclip
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable, Footer, Header, Static
from textual.coordinate import Coordinate

from authenticator.core import TOTPGenerator
from authenticator.storage import Storage


class Panel(App):
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
        ("c", "copy_password", "Copy Code"),
        ("enter", "copy_password", "Copy Code"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._storage = Storage()
        self._keys: dict[str, str] = {}
        self._generators: dict[str, TOTPGenerator] = {}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="main"):
            yield Static("Authenticator Dashboard", id="title")
            yield DataTable(id="table", cursor_type="row")
            yield Static("Press 'c' or 'Enter' to copy • 'q' to quit", id="hint")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        # Add columns with explicit keys for easier updating
        table.add_column("NAME", width=24, key="name")
        table.add_column("CODE", key="code")
        table.add_column("VALID", key="valid")
        table.add_column("RING", key="ring")
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
        
        # If keys changed (added/removed), reload and clear table structure
        if latest_keys != self._keys:
            self._reload_keys()
            table.clear() 

        if not self._keys:
            if table.row_count == 0:
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

            row_key = name
            
            try:
                # Try to get the row to see if it exists
                # Using get_row_index is one way to check existence without iterating
                _ = table.get_row_index(row_key)
                
                # If we get here, the row exists, so update cells
                table.update_cell(row_key, "code", code_text)
                table.update_cell(row_key, "valid", remaining_text)
                table.update_cell(row_key, "ring", ring_text)
            except Exception:
                # Row likely doesn't exist, or API is different. 
                # Try to add it.
                try:
                    table.add_row(name, code_text, remaining_text, ring_text, key=row_key)
                except Exception:
                    # If add fails (e.g. duplicate key but get_row_index failed for some reason), 
                    # we can try to force update or just ignore.
                    pass

    def action_copy_password(self) -> None:
        table = self.query_one(DataTable)
        
        # Check if cursor is active
        try:
            row_index = table.cursor_row
            if row_index is None:
                return

            # Get content from the "code" column (index 1)
            val = table.get_cell_at(Coordinate(row_index, 1))
            code_str = str(val)
            
            pyperclip.copy(code_str)
            self.notify(f"Copied {code_str} to clipboard!", title="Success", timeout=2)
            
        except Exception as e:
            self.notify(f"Error copying: {e}", severity="error")


def run_panel() -> None:
    Panel().run()

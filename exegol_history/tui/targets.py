import importlib
import xml.etree.ElementTree as ET
from pathlib import Path

from textual.app import App, ComposeResult, SystemCommand
from textual.keys import Keys
from textual.theme import Theme
from textual.binding import Binding
from textual.screen import ModalScreen, Screen
from textual.containers import Container
from textual.widgets import Footer, Header, Input, Rule, Static, Button
from textual.widgets._data_table import RowDoesNotExist

from exegol_history.config.config import AppConfig
from exegol_history.tui.screens.open_file import OpenFileScreen
from exegol_history.tui.widgets.action_buttons import (
    ActionButtons,
    ID_CANCEL_BUTTON,
    ID_CONFIRM_BUTTON,
)
from exegol_history.tui.widgets.object_datatable import ObjectsDataTable

TOOLTIP_IMPORT_NMAP = "Import IPv4/IPv6 addresses from an Nmap XML report (-oX)"


class TargetsDataTable(ObjectsDataTable):
    """Same as ObjectsDataTable but only the IP/host cell is used for $TARGET."""

    def action_select_cursor(self) -> None:
        # Skip ObjectsDataTable.exit(row) which passes the whole row tuple.
        super(ObjectsDataTable, self).action_select_cursor()
        selected_row = self.cursor_coordinate.row
        try:
            row_data = self.get_row_at(selected_row)
            ip = str(row_data[0]).strip()
            self.app.exit(ip if ip else None)
        except RowDoesNotExist:
            self.app.exit(None)


ID_TARGET_IP_INPUT = "target_ip_input"
ID_TARGET_COMMENT_INPUT = "target_comment_input"


class AddTargetScreen(ModalScreen[tuple[str, str] | None]):
    def __init__(self):
        super().__init__(id="add-target-screen")

    def compose(self) -> ComposeResult:
        container = Container()
        container.border_title = f"{self.app.config.theme.add_icon} Adding a target"

        with container:
            yield Static("IP / hostname", id="add_target_question_ip")
            yield Input(placeholder="10.10.10.10", id=ID_TARGET_IP_INPUT)
            yield Static("Comment (optional)", id="add_target_question_comment")
            yield Input(placeholder="Lab / VPN / HTB", id=ID_TARGET_COMMENT_INPUT)
            yield ActionButtons()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == ID_CONFIRM_BUTTON:
            ip = self.query_one(f"#{ID_TARGET_IP_INPUT}", Input).value.strip()
            comment = self.query_one(f"#{ID_TARGET_COMMENT_INPUT}", Input).value.strip()
            if not ip:
                return
            self.dismiss((ip, comment))
        elif event.button.id == ID_CANCEL_BUTTON:
            self.dismiss(None)


class ConfirmDeleteTargetScreen(ModalScreen[bool]):
    def __init__(self, ip: str):
        super().__init__(id="delete-target-screen")
        self.ip = ip

    def compose(self) -> ComposeResult:
        container = Container()
        container.border_title = f"{self.app.config.theme.delete_icon} Deleting target"
        with container:
            yield Static(f"Delete target '{self.ip}' ?", id="delete_target_question")
            yield ActionButtons()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == ID_CONFIRM_BUTTON:
            self.dismiss(True)
        elif event.button.id == ID_CANCEL_BUTTON:
            self.dismiss(False)


class TargetsApp(App):
    config = AppConfig()
    BINDINGS = [
        Binding(Keys.F3, "add_target", f"{config.theme.add_icon} target", id="add_target"),
        Binding(
            Keys.F4,
            "delete_target",
            f"{config.theme.delete_icon} target",
            id="delete_target",
        ),
        Binding(
            Keys.F5,
            "import_nmap",
            f"{config.theme.export_icon} nmap.xml",
            id="import_nmap",
            tooltip=TOOLTIP_IMPORT_NMAP,
        ),
        Binding(Keys.ControlC, "quit", "Quit", show=False, priority=True),
    ]

    def __init__(self, config: AppConfig):
        self.CSS_PATH = "css/general.tcss"
        self.TITLE = (
            f"🎯 Exegol-history v{importlib.metadata.version('exegol-history')} targets"
        )
        super().__init__()
        self.config = config
        self.custom_theme = Theme(
            name="custom",
            primary=config.theme.primary,
            secondary=config.theme.secondary,
            accent=config.theme.accent,
            foreground=config.theme.foreground,
            background=config.theme.background,
            success=config.theme.success,
            warning=config.theme.warning,
            error=config.theme.error,
            surface=config.theme.surface,
            panel=config.theme.panel,
            dark=config.theme.dark,
        )

    def compose(self) -> ComposeResult:
        yield Header()
        yield TargetsDataTable()
        yield Rule(line_style="heavy")
        yield Input(placeholder="🔍 Search...", id="search-bar")
        yield Footer()

    def on_mount(self) -> None:
        self.register_theme(self.custom_theme)
        self.theme = "custom"

        table = self.screen.query_one(TargetsDataTable)
        table.add_columns("ip", "comment")
        self._refresh_table()

        self.set_keymap(self.config.keybindings)

    def get_system_commands(self, screen: Screen):
        yield SystemCommand("Import Nmap XML", TOOLTIP_IMPORT_NMAP, self.action_import_nmap)

    def _refresh_table(self) -> None:
        table = self.screen.query_one(TargetsDataTable)
        table.clear()
        rows = [(t.ip, t.comment) for t in self.config.targets]
        self.original_data = rows
        if rows:
            table.add_rows(rows)

    def on_input_changed(self, event: Input.Changed) -> None:
        try:
            search_query = event.value.lower()
            table = self.screen.query_one(TargetsDataTable)
            table.clear()
            filtered = [
                row
                for row in self.original_data
                if any(search_query in str(cell).lower() for cell in row)
            ]
            for row in filtered:
                table.add_row(*map(str, row))
        except Exception:
            pass

    def action_add_target(self) -> None:
        def on_added(result: tuple[str, str] | None):
            if not result:
                return
            ip, comment = result
            try:
                self.config.add_target(ip, comment)
            except Exception:
                return
            self._refresh_table()

        self.push_screen(AddTargetScreen(), on_added)

    def action_delete_target(self) -> None:
        table = self.screen.query_one(TargetsDataTable)
        selected_row = table.cursor_row
        try:
            row = table.get_row_at(selected_row)
        except Exception:
            return
        ip = str(row[0])

        def on_confirm(ok: bool):
            if not ok:
                return
            self.config.remove_target(ip)
            self._refresh_table()

        self.push_screen(ConfirmDeleteTargetScreen(ip), on_confirm)

    def action_import_nmap(self) -> None:
        def on_path_chosen(path: str | None) -> None:
            if not path or not str(path).strip():
                return
            p = Path(str(path).strip()).expanduser().resolve()
            if not p.is_file():
                self.notify("Please select an Nmap XML file.", severity="error")
                return
            try:
                added = self.config.import_targets_from_nmap_xml(p)
            except ET.ParseError as e:
                self.notify(f"Invalid Nmap XML: {e}", severity="error")
                return
            self.notify(
                f"Imported {added} new target(s) from {p.name}.",
                severity="information",
            )
            self._refresh_table()

        self.push_screen(
            OpenFileScreen("Choose an Nmap XML file (-oX):"),
            on_path_chosen,
        )

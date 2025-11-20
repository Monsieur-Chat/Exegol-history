from textual.screen import ModalScreen
from textual.app import ComposeResult
from exegol_history.db_api.utils import parse_ids
from exegol_history.tui.widgets.action_buttons import ActionButtons
from textual.widgets import Static, Input, Button
from textual.containers import Container

"""
This screen is used to sync objects
"""
ID_IDS_INPUT = "ids_input"

ID_CONFIRM_BUTTON = "confirm_button"
ID_CONFIRM_RANGE_BUTTON = "confirm_range_button"
ID_CANCEL_BUTTON = "cancel_button"

ID_SINGLE_TAB = "single_tab"
ID_RANGE_TAB = "range_tab"


class SyncObjectScreen(ModalScreen):
    def __init__(self):
        super().__init__()

    def compose(self) -> ComposeResult:
        container = Container()
        container.border_title = (
            f"{self.app.config['theme']['sync_icon']} Synchronizing objects"
        )

        with container:
            yield Static(
                "Are you sure you want to remove that object?",
                id="question",
            )
            yield ActionButtons()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if self.selected_tab == f"--content-tab-{ID_RANGE_TAB}":
            ids = self.screen.query_one(f"#{ID_IDS_INPUT}", Input).value
            self.ids = parse_ids(ids)

        if event.button.id in (ID_CONFIRM_BUTTON, ID_CONFIRM_RANGE_BUTTON):
            self.screen.dismiss(self.ids)

from pathlib import Path

from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import Static, DirectoryTree, Button, Input
from textual.containers import Container
from exegol_history.tui.widgets.action_buttons import ActionButtons, ID_CONFIRM_BUTTON

ID_PATH_INPUT = "select_path_input"


def _tree_root_path(root: str | Path | None) -> Path:
    """Directory shown at the top of the tree (default: current working directory)."""
    if root is None:
        cwd = Path.cwd().resolve()
        return cwd if cwd.is_dir() else Path.home()
    p = Path(root).expanduser().resolve()
    if not p.exists():
        cwd = Path.cwd().resolve()
        return cwd if cwd.is_dir() else Path.home()
    if p.is_file():
        return p.parent
    return p


class OpenFileScreen(ModalScreen):
    def __init__(self, message: str = "", root: str | Path | None = None):
        super().__init__()
        self.message = message
        self._tree_root = str(_tree_root_path(root))

    def compose(self) -> ComposeResult:
        container = Container()
        container.border_title = "📁 Opening a file/folder"
        with container:
            yield Static(
                self.message,
                id="question",
            )
            yield DirectoryTree(self._tree_root, id="directory_tree")
            yield Input(placeholder="Selected path...", id=ID_PATH_INPUT)
            yield ActionButtons()

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        self.screen.query_one(f"#{ID_PATH_INPUT}", Input).value = f"{event.path}"

    def on_directory_tree_directory_selected(
        self, event: DirectoryTree.DirectorySelected
    ) -> None:
        self.screen.query_one(f"#{ID_PATH_INPUT}", Input).value = f"{event.path}"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == ID_CONFIRM_BUTTON:
            self.screen.dismiss(self.screen.query_one(f"#{ID_PATH_INPUT}", Input).value)

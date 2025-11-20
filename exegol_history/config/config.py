import platform
import secrets
import shutil
import tomllib
from pathlib import Path
from typing import Any
from exegol_history.connectors.metasploit.metasploit_sync import MetasploitSyncer
from exegol_history.connectors.netexec.netexec_sync import NetexecSyncer
from sqlalchemy import Engine, create_engine
from exegol_history.db_api.creds import Base


class ConfigTest:
    def __init__(self, config_raw: dict[str, Any]):
        self.paths = ConfigPaths(**config_raw["paths"])
        self.keybindings = ConfigKeybindings(**config_raw["keybindings"])
        self.sync = [
            ConfigSyncNetexec(**config_raw["sync"][NetexecSyncer.CONNECTOR_NAME]),
            ConfigSyncMetasploit(**config_raw["sync"][MetasploitSyncer.CONNECTOR_NAME]),
        ]
        self.theme = ConfigTheme(**config_raw["theme"])


class ConfigPaths:
    def __init__(self, db_name: str, db_key_name: str, profile_sh_path: str):
        self.db_name = db_name
        self.db_key_name = db_key_name
        self.profile_sh_path = profile_sh_path


class ConfigKeybindings:
    def __init__(
        self,
        copy_username_clipboard: str,
        copy_password_clipboard: str,
        copy_hash_clipboard: str,
        add_credential: str,
        delete_credential: str,
        edit_credential: str,
        export_credential: str,
        copy_ip_clipboard: str,
        copy_hostname_clipboard: str,
        add_host: str,
        delete_host: str,
        edit_host: str,
        export_host: str,
        quit: str,
    ):
        self.copy_username_clipboard = copy_username_clipboard
        self.copy_password_clipboard = copy_password_clipboard
        self.copy_hash_clipboard = copy_hash_clipboard
        self.add_credential = add_credential
        self.delete_credential = delete_credential
        self.edit_credential = edit_credential
        self.export_credential = export_credential
        self.copy_ip_clipboard = copy_ip_clipboard
        self.copy_hostname_clipboard = copy_hostname_clipboard
        self.add_host = add_host
        self.delete_host = delete_host
        self.edit_host = edit_host
        self.export_host = export_host
        self.quit = quit


class ConfigSyncNetexec:
    def __init__(self, enabled: bool, workspace_path: str):
        self.enabled = enabled
        self.workspace_path = workspace_path


class ConfigSyncMetasploit:
    def __init__(self, enabled: bool, db_config_path: str):
        self.enabled = enabled
        self.db_config_path = db_config_path


class ConfigTheme:
    def __init__(
        self,
        primary: str,
        secondary: str,
        accent: str,
        foreground: str,
        background: str,
        success: str,
        warning: str,
        error: str,
        surface: str,
        panel: str,
        dark: str,
        clipboard_icon: str,
        add_icon: str,
        delete_icon: str,
        edit_icon: str,
        export_icon: str,
        inline: bool,
    ):
        self.primary: str = primary
        self.secondary = secondary
        self.accent = accent
        self.foreground = foreground
        self.background = background
        self.success = success
        self.warning = warning
        self.error = error
        self.surface = surface
        self.panel = panel
        self.dark = dark
        self.clipboard_icon = clipboard_icon
        self.add_icon = add_icon
        self.delete_icon = delete_icon
        self.edit_icon = edit_icon
        self.export_icon = export_icon
        self.inline = inline


class AppConfig:
    __config_data = None

    EXEGOL_HISTORY_HOME_FOLDER_NAME = Path.home() / ".exegol_history"
    CONFIG_FILENAME = "config.toml"
    PROFILE_SH_FILENAME_UNIX = "profile.sh"
    PROFILE_SH_FILENAME_WINDOWS = "profile.ps1"

    @classmethod
    def setup_db(cls, db_path: str, db_key_path: str) -> Engine:
        path = Path(db_path)

        if path.is_absolute():
            engine = create_engine(f"sqlite:////{db_path}")
        else:
            engine = create_engine(f"sqlite:///{db_path}")

        Base.metadata.create_all(engine)

        return engine

    @staticmethod
    def __setup_generate_keyfile(db_key_path: str) -> None:
        random_bytes = secrets.token_bytes(256)

        if not Path(db_key_path).is_file():
            Path(db_key_path).parent.mkdir(parents=True, exist_ok=True)
            with open(db_key_path, "wb") as key_file:
                key_file.write(random_bytes)

    @classmethod
    def setup_profile(cls, profile_path: str):
        if not Path(profile_path).exists():
            Path(profile_path).parent.mkdir(exist_ok=True, parents=True)

            default_config_path = (
                Path(__file__).parent.parent.parent / cls.PROFILE_SH_FILENAME_WINDOWS
                if platform.system() == "Windows"
                else Path(__file__).parent.parent.parent / cls.PROFILE_SH_FILENAME_UNIX
            )
            shutil.copy(default_config_path, Path(profile_path))

    @classmethod
    def load_config(cls, config_path: str = None) -> dict[str, Any]:
        if cls.__config_data is None:
            config_path = (
                config_path
                if config_path
                else cls.EXEGOL_HISTORY_HOME_FOLDER_NAME / cls.CONFIG_FILENAME
            )

            if not Path(config_path).is_file():
                Path(config_path).parent.mkdir(exist_ok=True)

                default_config_path = Path(__file__).parent / cls.CONFIG_FILENAME
                shutil.copy(default_config_path, config_path)

            with open(config_path, "rb") as config_file:
                config_data = tomllib.load(config_file)
        return config_data

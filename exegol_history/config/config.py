import platform
import shutil
import tomllib
from pathlib import Path
from ipaddress import ip_address
from exegol_history.connectors.metasploit.metasploit_sync import MetasploitSyncer
from exegol_history.connectors.netexec.netexec_sync import NetexecSyncer
from sqlalchemy import Engine, create_engine
from exegol_history.db_api.creds import Base
from tomlkit import aot, dumps, parse

DEFAULT_KEYBINDS = {
    "copy_username_clipboard": "f1",
    "copy_password_clipboard": "f2",
    "copy_hash_clipboard": "f3",
    "add_credential": "f4",
    "delete_credential": "f5",
    "edit_credential": "f6",
    "export_credential": "f7",
    "copy_ip_clipboard": "f1",
    "copy_hostname_clipboard": "f2",
    "add_host": "f3",
    "delete_host": "f4",
    "edit_host": "f5",
    "export_host": "f6",
    "quit": "ctrl+c",
}


class AppConfig:
    EXEGOL_HISTORY_HOME_FOLDER_NAME = Path.home() / ".exegol_history"
    CONFIG_FILENAME = "config.toml"
    PROFILE_SH_FILENAME_UNIX = "profile.sh"
    PROFILE_SH_FILENAME_WINDOWS = "profile.ps1"

    def __init__(
        self, config_path: str = EXEGOL_HISTORY_HOME_FOLDER_NAME / CONFIG_FILENAME
    ):
        self.config_path = Path(config_path).expanduser()
        if not self.config_path.is_file():
            self.config_path.parent.mkdir(exist_ok=True)

            default_config_path = Path(__file__).parent / AppConfig.CONFIG_FILENAME
            shutil.copy(default_config_path, self.config_path)

        with open(self.config_path, "rb") as config_file:
            config_data = tomllib.load(config_file)

        self.paths = ConfigPaths(**config_data["paths"])
        self.keybindings = config_data["keybindings"]
        self.sync = [
            ConfigSyncNetexec(**config_data["sync"][NetexecSyncer.CONNECTOR_NAME]),
            ConfigSyncMetasploit(
                **config_data["sync"][MetasploitSyncer.CONNECTOR_NAME]
            ),
        ]
        self.theme = ConfigTheme(**config_data["theme"])
        self.targets = [
            ConfigTarget(**t) for t in config_data.get("targets", []) if isinstance(t, dict)
        ]

    def _load_tomlkit(self):
        if not self.config_path.exists():
            return parse("")
        try:
            return parse(self.config_path.read_text(encoding="utf-8"))
        except Exception:
            return parse("")

    def save(self) -> None:
        doc = self._load_tomlkit()

        doc["paths"] = {
            "db_name": self.paths.db_name,
            "profile_sh_path": self.paths.profile_sh_path,
        }
        doc["keybindings"] = self.keybindings

        if "sync" not in doc:
            doc["sync"] = {}
        doc["sync"][NetexecSyncer.CONNECTOR_NAME] = {
            "enabled": getattr(self.sync[0], "enabled", True),
            "workspace_path": getattr(self.sync[0], "workspace_path", "~/.nxc/workspaces/"),
        }
        doc["sync"][MetasploitSyncer.CONNECTOR_NAME] = {
            "enabled": getattr(self.sync[1], "enabled", False),
            "db_config_path": getattr(self.sync[1], "db_config_path", "/var/lib/postgresql/.msf4/database.yml"),
        }

        theme_dict = {
            "primary": self.theme.primary,
            "secondary": self.theme.secondary,
            "accent": self.theme.accent,
            "foreground": self.theme.foreground,
            "background": self.theme.background,
            "success": self.theme.success,
            "warning": self.theme.warning,
            "error": self.theme.error,
            "surface": self.theme.surface,
            "panel": self.theme.panel,
            "dark": self.theme.dark,
            "clipboard_icon": self.theme.clipboard_icon,
            "add_icon": self.theme.add_icon,
            "delete_icon": self.theme.delete_icon,
            "edit_icon": self.theme.edit_icon,
            "export_icon": self.theme.export_icon,
            "inline": self.theme.inline,
        }
        doc["theme"] = {k: v for k, v in theme_dict.items() if v is not None}

        targets_aot = aot()
        for t in self.targets:
            targets_aot.append({"ip": t.ip, "comment": t.comment})
        doc["targets"] = targets_aot

        self.config_path.write_text(dumps(doc).rstrip() + "\n", encoding="utf-8")

    def add_target(self, ip: str, comment: str = "") -> None:
        ip = ip.strip()
        if not ip:
            raise ValueError("Target IP can't be empty.")
        # Accept both IP and hostnames; validate if it's an IP
        try:
            ip_address(ip)
        except ValueError:
            pass

        if any(t.ip == ip for t in self.targets):
            return
        self.targets.append(ConfigTarget(ip=ip, comment=comment or ""))
        self.save()

    def remove_target(self, ip: str) -> None:
        before = len(self.targets)
        self.targets = [t for t in self.targets if t.ip != ip]
        if len(self.targets) != before:
            self.save()

    def import_targets_from_nmap_xml(self, path: Path) -> int:
        from exegol_history.targets.nmap_xml import parse_nmap_xml

        entries = parse_nmap_xml(path)
        existing = {t.ip for t in self.targets}
        added = 0
        for ip, comment in entries:
            if ip in existing:
                continue
            self.targets.append(ConfigTarget(ip=ip, comment=comment or ""))
            existing.add(ip)
            added += 1
        if added:
            self.save()
        return added

    @staticmethod
    def setup_db(db_path: str) -> Engine:
        path = Path(db_path)

        if path.is_absolute():
            engine = create_engine(f"sqlite:////{db_path}")
        else:
            engine = create_engine(f"sqlite:///{db_path}")

        Base.metadata.create_all(engine)

        return engine

    @staticmethod
    def setup_profile(profile_path: str) -> Path:
        profile_path_p = Path(profile_path).expanduser()

        default_profile_path = (
            Path(__file__).parent.parent.parent
            / AppConfig.PROFILE_SH_FILENAME_WINDOWS
            if platform.system() == "Windows"
            else Path(__file__).parent.parent.parent / AppConfig.PROFILE_SH_FILENAME_UNIX
        )

        def ensure_profile(target: Path) -> Path:
            if not target.exists():
                target.parent.mkdir(exist_ok=True, parents=True)
                shutil.copy(default_profile_path, target)
            return target

        try:
            return ensure_profile(profile_path_p)
        except PermissionError:
            fallback = AppConfig.EXEGOL_HISTORY_HOME_FOLDER_NAME / profile_path_p.name
            return ensure_profile(fallback)


class ConfigPaths:
    def __init__(
        self,
        db_name: str = "exh.db",
        profile_sh_path: str = str(AppConfig.EXEGOL_HISTORY_HOME_FOLDER_NAME / "profile.sh"),
    ):
        self.db_name = db_name
        self.profile_sh_path = profile_sh_path


class ConfigSyncNetexec:
    CONNECTOR_NAME = NetexecSyncer.CONNECTOR_NAME

    def __init__(
        self, enabled: bool = True, workspace_path: str = "~/.nxc/workspaces/"
    ):
        self.enabled = enabled
        self.workspace_path = workspace_path


class ConfigSyncMetasploit:
    CONNECTOR_NAME = MetasploitSyncer.CONNECTOR_NAME

    def __init__(
        self,
        enabled: bool = False,
        db_config_path: str = "/var/lib/postgresql/.msf4/database.yml",
    ):
        self.enabled = enabled
        self.db_config_path = db_config_path


class ConfigTheme:
    def __init__(
        self,
        primary: str = "#0178D4",
        secondary: str = "#004578",
        accent: str = "#ffa62b",
        foreground: str = "#e0e0e0",
        background: str = None,
        success: str = "#4EBF71",
        warning: str = "#ffa62b",
        error: str = "#ba3c5b",
        surface: str = None,
        panel: str = None,
        dark: bool = True,
        clipboard_icon: str = "📋",
        add_icon: str = "➕",
        delete_icon: str = "➖",
        edit_icon: str = "📝",
        export_icon: str = "📤",
        inline: bool = True,
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


class ConfigTarget:
    def __init__(self, ip: str, comment: str = ""):
        self.ip = str(ip).strip()
        self.comment = "" if comment is None else str(comment)

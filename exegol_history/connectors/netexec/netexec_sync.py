from enum import Enum
from pathlib import Path
import sqlite3
from sqlalchemy import Engine
from exegol_history.cli.utils import console_error, console_success
from exegol_history.db_api.creds import Credential, add_credentials
from rich.console import Console
from exegol_history.db_api.hosts import Host, add_hosts

PATH_NETEXEC_WORKSPACE = "~/.nxc/workspaces/"


class NetexecCredType(Enum):
    HASH = "hash"
    PASSWORD = "plaintext"
    KEY = "key"


class NetexecSyncer:
    def __init__(
        self,
        engine: Engine,
        console: Console,
        workspaces_dir: str = PATH_NETEXEC_WORKSPACE,
        sync_credentials: bool = False,
        sync_hosts: bool = False,
    ):
        self.workspaces_dir = Path(workspaces_dir).expanduser()
        self.engine = engine
        self.console = console
        self.sync_credentials = sync_credentials
        self.sync_hosts = sync_hosts
        self.db_files = {
            "smb.db": (
                "SELECT username, password, domain, credtype FROM users",
                "SELECT ip, hostname FROM hosts",
            ),
            "ftp.db": (
                "SELECT username, password FROM credentials",
                "SELECT ip, hostname FROM hosts",
            ),
            "mssql.db": (
                "SELECT username, password, domain, credtype FROM users",
                "SELECT ip, hostname FROM hosts",
            ),
            "ssh.db": (
                "SELECT username, password, credtype FROM credentials",
                "SELECT ip, hostname FROM hosts",
            ),
            "winrm.db": (
                "SELECT username, password, domain, credtype FROM users",
                "SELECT ip, hostname FROM hosts",
            ),
            "ldap.db": (
                "SELECT username, password, domain, credtype FROM users",
                "SELECT ip, hostname FROM hosts",
            ),
            "rdp.db": (
                "SELECT username, password FROM credentials",
                "SELECT ip, hostname FROM hosts",
            ),
            "nfs.db": (
                "SELECT username, password FROM credentials",
                "SELECT ip, hostname FROM hosts",
            ),
            "vnc.db": (
                "SELECT username, password FROM credentials",
                "SELECT ip, hostname FROM hosts",
            ),
            "wmi.db": (
                "SELECT username, password FROM credentials",
                "SELECT ip, hostname FROM hosts",
            ),
        }

    def sync(self):
        if self.workspaces_dir.exists():
            for workspace in self.workspaces_dir.iterdir():
                workspace_path = self.workspaces_dir / workspace
                if workspace_path.is_dir():
                    self.process_workspace(workspace_path)
        else:
            self.console.print(
                console_error(f"No workspaces directory found at {self.workspaces_dir}")
            )

    def process_workspace(self, workspace_path: Path):
        for db_file, queries in self.db_files.items():
            db_file_path = workspace_path / Path(db_file)

            if db_file_path.is_file():
                if self.sync_credentials:
                    self.extract_and_add_credentials(db_file_path, queries[0])

                if self.sync_hosts:
                    self.extract_and_add_hosts(db_file_path, queries[1])
            else:
                self.console.print(console_error(f"Missing: {db_file}"))

    def extract_and_add_credentials(self, db_file_path: str, query: str):
        try:
            conn = sqlite3.connect(db_file_path)
            cursor = conn.cursor()
            credentials = []

            cursor.execute(query)

            columns = [desc[0] for desc in cursor.description]

            for row in cursor.fetchall():
                username = password = domain = credtype = None

                if ("domain" in columns) and ("credtype" in columns):
                    username, password, domain, credtype = row
                elif "credtype" in columns:
                    username, password, credtype = row
                else:
                    username, password = row

                credential = Credential.dict(None, username, None, None, domain)

                if credtype == NetexecCredType.HASH.value:
                    credential["hash"] = password
                elif credtype == NetexecCredType.PASSWORD.value:
                    credential["password"] = password

                credentials.append(credential)

            add_credentials(self.engine, credentials)
            conn.close()
        except Exception as e:
            self.console.print(
                console_error(
                    f"Error synchronizing Netexec credentials from {db_file_path}: {e}"
                )
            )

        self.console.print(
            console_success(
                f"{len(credentials)} Netexec credentials synchronized from {db_file_path} !"
            )
        )

    def extract_and_add_hosts(self, db_file_path: str, query: str):
        try:
            conn = sqlite3.connect(db_file_path)
            cursor = conn.cursor()
            hosts = []

            cursor.execute(query)
            rows = cursor.fetchall()

            for row in rows:
                ip, hostname = row

                hosts.append(Host.dict(ip=ip, hostname=hostname))

            add_hosts(self.engine, hosts)
            conn.close()
        except Exception as e:
            self.console.print(
                console_error(f"Error extracting from {db_file_path}: {e}")
            )

        self.console.print(
            console_success(
                f"{len(hosts)} Netexec credentials synchronized from {db_file_path} !"
            )
        )

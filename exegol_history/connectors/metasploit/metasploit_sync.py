from sqlalchemy import Engine
import psycopg
from psycopg.errors import UndefinedTable
from exegol_history.cli.utils import console_error, console_success
from exegol_history.db_api.creds import Credential, add_credentials
from rich.console import Console
from exegol_history.connectors.metasploit.utils import (
    MSF_DB_CONFIG_PATH,
    get_msf_postgres_db_infos,
    is_private_data_hash,
    MSF_DB_CREDENTIAL_QUERY,
    MetasploitCredentialType,
)


class MetasploitSyncer:
    def __init__(
        self, engine: Engine, console: Console, config_path: str = MSF_DB_CONFIG_PATH
    ):
        (
            self.msf_db_name,
            self.msf_db_port,
            self.msf_db_username,
            self.msf_db_password,
        ) = get_msf_postgres_db_infos(config_path)
        self.engine = engine
        self.console = console

    def sync(self):
        try:
            conn = psycopg.connect(
                f"dbname={self.msf_db_name} user={self.msf_db_username} port={self.msf_db_port} password={self.msf_db_password} host=localhost"
            )
            cursor = conn.cursor()
            credentials = []

            try:
                cursor.execute(MSF_DB_CREDENTIAL_QUERY)
            except UndefinedTable:
                return  # If the table is not there, it means the Metasploit DB is empty

            for record in cursor.fetchall():
                username = record[1]
                password = None
                hash = None
                private_data = record[2]
                private_data_type = record[3]
                domain = record[4]

                if is_private_data_hash(private_data_type):
                    hash = private_data
                elif private_data_type == MetasploitCredentialType.Password:
                    password = private_data

                credentials.append(
                    Credential.dict(
                        username=username,
                        password=password,
                        hash=hash,
                        domain=domain,
                    )
                )

            add_credentials(self.engine, credentials)
            conn.close()
        except Exception as e:
            self.console.print(
                console_error(f"Error synchronizing Metasploit credentials: {e}")
            )

        self.console.print(
            console_success(f"{len(credentials)} Metasploit credentials synchronized !")
        )

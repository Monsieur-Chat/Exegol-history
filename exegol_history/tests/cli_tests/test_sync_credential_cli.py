import io
from unittest.mock import patch
from rich.console import Console
from sqlalchemy import Engine
from exegol_history.connectors.metasploit.metasploit_sync import MetasploitSyncer
from exegol_history.connectors.metasploit.utils import MetasploitCredentialType
from exegol_history.connectors.netexec.netexec_sync import (
    NetexecCredType,
    NetexecSyncer,
)
from exegol_history.db_api.creds import Credential, get_credentials
from exegol_history.tests.common import (
    DOMAIN_TEST_VALUE,
    GET_PG_DB_INFOS_PATCH_PATH,
    PASSWORD_TEST_VALUE,
    PSYCOPG_PATCH_PATH,
    SQLITE3_PATCH_PATH,
    TEST_NETEXEC_WORKSPACE,
    USERNAME_TEST_VALUE,
)
import time

NETEXEC_CREDENTIALS_COLUMNS = [["username"], ["password"], ["domain"], ["credtype"]]


# Syncing should not take too much time for large amount of credentials
def test_sync_credential_netexec_big(engine: Engine):
    console = Console(file=io.StringIO())
    syncer = NetexecSyncer(
        engine, console, workspaces_dir=TEST_NETEXEC_WORKSPACE, sync_credentials=True
    )
    credentials = []
    credentials2 = []

    for i in range(1, 2000):
        credentials.append(
            Credential(
                credential_id=i,
                username=USERNAME_TEST_VALUE + str(i),
                password=PASSWORD_TEST_VALUE,
                domain=DOMAIN_TEST_VALUE,
            )
        )
        credentials2.append(
            (
                USERNAME_TEST_VALUE + str(i),
                PASSWORD_TEST_VALUE,
                DOMAIN_TEST_VALUE,
                NetexecCredType.PASSWORD.value,
            )
        )

    start_time = time.time()

    with patch(SQLITE3_PATCH_PATH) as mocksqlite3:
        mocksqlite3.connect().cursor().fetchall.return_value = credentials2
        mocksqlite3.connect().cursor().description = NETEXEC_CREDENTIALS_COLUMNS
        syncer.sync()

    end_time = time.time()

    assert get_credentials(engine) == credentials
    assert (end_time - start_time) < 1


# Here we are also updating some random credential
def test_sync_credential_netexec_big_update(engine: Engine):
    console = Console(file=io.StringIO())
    syncer = NetexecSyncer(
        engine, console, workspaces_dir=TEST_NETEXEC_WORKSPACE, sync_credentials=True
    )
    credentials = []
    credentials2 = []

    for i in range(1, 2000):
        credentials.append(
            Credential(
                credential_id=i,
                username=USERNAME_TEST_VALUE + str(i),
                password=PASSWORD_TEST_VALUE,
                domain=DOMAIN_TEST_VALUE,
            )
        )
        credentials2.append(
            (
                USERNAME_TEST_VALUE + str(i),
                PASSWORD_TEST_VALUE,
                DOMAIN_TEST_VALUE,
                NetexecCredType.PASSWORD.value,
            )
        )

    with patch(SQLITE3_PATCH_PATH) as mocksqlite3:
        mocksqlite3.connect().cursor().fetchall.return_value = credentials2
        mocksqlite3.connect().cursor().description = NETEXEC_CREDENTIALS_COLUMNS
        syncer.sync()

    # Updating some credential
    credentials[456].password = PASSWORD_TEST_VALUE + "53465456775675"
    credentials2[456] = (
        USERNAME_TEST_VALUE + "457",
        PASSWORD_TEST_VALUE + "53465456775675",
        DOMAIN_TEST_VALUE,
        NetexecCredType.PASSWORD.value,
    )

    credentials[865].password = PASSWORD_TEST_VALUE + "21312123412"
    credentials2[865] = (
        USERNAME_TEST_VALUE + "866",
        PASSWORD_TEST_VALUE + "21312123412",
        DOMAIN_TEST_VALUE,
        NetexecCredType.PASSWORD.value,
    )

    start_time = time.time()

    with patch(SQLITE3_PATCH_PATH) as mocksqlite3:
        mocksqlite3.connect().cursor().fetchall.return_value = credentials2
        mocksqlite3.connect().cursor().description = NETEXEC_CREDENTIALS_COLUMNS
        syncer.sync()

    end_time = time.time()

    assert get_credentials(engine) == credentials
    assert (end_time - start_time) < 1


def test_sync_credential_netexec(engine: Engine):
    console = Console(file=io.StringIO())
    syncer = NetexecSyncer(
        engine, console, workspaces_dir=TEST_NETEXEC_WORKSPACE, sync_credentials=True
    )

    with patch(SQLITE3_PATCH_PATH) as mocksqlite3:
        mocksqlite3.connect().cursor().fetchall.return_value = [
            (
                USERNAME_TEST_VALUE,
                PASSWORD_TEST_VALUE,
                DOMAIN_TEST_VALUE,
                NetexecCredType.PASSWORD.value,
            )
        ]
        mocksqlite3.connect().cursor().description = NETEXEC_CREDENTIALS_COLUMNS
        syncer.sync()

    assert get_credentials(engine) == [
        Credential(
            credential_id=1,
            username=USERNAME_TEST_VALUE,
            password=PASSWORD_TEST_VALUE,
            domain=DOMAIN_TEST_VALUE,
        )
    ]


def test_sync_credential_netexec_empty(engine: Engine):
    console = Console(file=io.StringIO())
    syncer = NetexecSyncer(
        engine, console, workspaces_dir=TEST_NETEXEC_WORKSPACE, sync_credentials=True
    )

    with patch(SQLITE3_PATCH_PATH) as mocksqlite3:
        mocksqlite3.connect().cursor().fetchall.return_value = []
        mocksqlite3.connect().cursor().description = NETEXEC_CREDENTIALS_COLUMNS
        syncer.sync()

    assert not get_credentials(engine)


def test_sync_credential_metasploit_big(engine: Engine):
    console = Console(file=io.StringIO())
    credentials = []
    credentials2 = []

    for i in range(1, 2000):
        credentials.append(
            Credential(
                credential_id=i,
                username=USERNAME_TEST_VALUE + str(i),
                password=PASSWORD_TEST_VALUE,
                domain=DOMAIN_TEST_VALUE,
            )
        )
        credentials2.append(
            (
                None,
                USERNAME_TEST_VALUE + str(i),
                PASSWORD_TEST_VALUE,
                MetasploitCredentialType.Password,
                DOMAIN_TEST_VALUE,
            )
        )

    start_time = time.time()

    with patch(PSYCOPG_PATCH_PATH) as mockpsycopg:
        with patch(GET_PG_DB_INFOS_PATCH_PATH) as get_msf_postgres_db_infos:
            mockpsycopg.connect().cursor().fetchall.return_value = credentials2
            get_msf_postgres_db_infos.return_value = ("", "", "", "")
            syncer = MetasploitSyncer(
                engine,
                console,
                config_path=TEST_NETEXEC_WORKSPACE / "test_workspace" / "smb.db",
            )
            syncer.sync()

    end_time = time.time()

    assert get_credentials(engine) == credentials
    assert (end_time - start_time) < 1


def test_sync_credential_metasploit_big_update(engine: Engine):
    console = Console(file=io.StringIO())
    credentials = []
    credentials2 = []

    for i in range(1, 2000):
        credentials.append(
            Credential(
                credential_id=i,
                username=USERNAME_TEST_VALUE + str(i),
                password=PASSWORD_TEST_VALUE,
                domain=DOMAIN_TEST_VALUE,
            )
        )
        credentials2.append(
            (
                None,
                USERNAME_TEST_VALUE + str(i),
                PASSWORD_TEST_VALUE,
                MetasploitCredentialType.Password,
                DOMAIN_TEST_VALUE,
            )
        )

    with patch(PSYCOPG_PATCH_PATH) as mockpsycopg:
        with patch(GET_PG_DB_INFOS_PATCH_PATH) as get_msf_postgres_db_infos:
            mockpsycopg.connect().cursor().fetchall.return_value = credentials2
            get_msf_postgres_db_infos.return_value = ("", "", "", "")
            syncer = MetasploitSyncer(
                engine,
                console,
                config_path=TEST_NETEXEC_WORKSPACE / "test_workspace" / "smb.db",
            )
            syncer.sync()

    # Updating some credential
    credentials[456].password = PASSWORD_TEST_VALUE + "53465456775675"
    credentials2[456] = (
        None,
        USERNAME_TEST_VALUE + "457",
        PASSWORD_TEST_VALUE + "53465456775675",
        MetasploitCredentialType.Password,
        DOMAIN_TEST_VALUE,
    )

    credentials[865].password = PASSWORD_TEST_VALUE + "21312123412"
    credentials2[865] = (
        None,
        USERNAME_TEST_VALUE + "866",
        PASSWORD_TEST_VALUE + "21312123412",
        MetasploitCredentialType.Password,
        DOMAIN_TEST_VALUE,
    )

    start_time = time.time()

    with patch(PSYCOPG_PATCH_PATH) as mockpsycopg:
        with patch(GET_PG_DB_INFOS_PATCH_PATH) as get_msf_postgres_db_infos:
            mockpsycopg.connect().cursor().fetchall.return_value = credentials2
            get_msf_postgres_db_infos.return_value = ("", "", "", "")
            syncer = MetasploitSyncer(
                engine,
                console,
                config_path=TEST_NETEXEC_WORKSPACE / "test_workspace" / "smb.db",
            )
            syncer.sync()

    end_time = time.time()

    assert get_credentials(engine) == credentials
    assert (end_time - start_time) < 1


def test_sync_credential_metasploit(engine: Engine):
    console = Console(file=io.StringIO())

    with patch(PSYCOPG_PATCH_PATH) as mockpsycopg:
        with patch(GET_PG_DB_INFOS_PATCH_PATH) as get_msf_postgres_db_infos:
            mockpsycopg.connect().cursor().fetchall.return_value = [
                (
                    None,
                    USERNAME_TEST_VALUE,
                    PASSWORD_TEST_VALUE,
                    MetasploitCredentialType.Password,
                    DOMAIN_TEST_VALUE,
                )
            ]
            get_msf_postgres_db_infos.return_value = ("", "", "", "")
            syncer = MetasploitSyncer(
                engine,
                console,
                config_path=TEST_NETEXEC_WORKSPACE / "test_workspace" / "smb.db",
            )
            syncer.sync()

    assert get_credentials(engine) == [
        Credential(
            credential_id=1,
            username=USERNAME_TEST_VALUE,
            password=PASSWORD_TEST_VALUE,
            domain=DOMAIN_TEST_VALUE,
        )
    ]


def test_sync_credential_metasploit_empty(engine: Engine):
    console = Console(file=io.StringIO())

    with patch(PSYCOPG_PATCH_PATH) as mockpsycopg:
        with patch(GET_PG_DB_INFOS_PATCH_PATH) as get_msf_postgres_db_infos:
            mockpsycopg.connect().cursor().fetchall.return_value = []
            get_msf_postgres_db_infos.return_value = ("", "", "", "")
            syncer = MetasploitSyncer(
                engine,
                console,
                config_path=TEST_NETEXEC_WORKSPACE / "test_workspace" / "smb.db",
            )
            syncer.sync()

    assert not get_credentials(engine)

import io
import time
from unittest.mock import patch
from sqlalchemy import Engine
from exegol_history.connectors.netexec.netexec_sync import NetexecSyncer
from exegol_history.db_api.hosts import Host, get_hosts
from exegol_history.tests.common import (
    HOSTNAME_TEST_VALUE,
    IP_TEST_VALUE,
    SQLITE3_PATCH_PATH,
    TEST_NETEXEC_WORKSPACE,
)
from rich.console import Console

# def test_sync_host_netexec(engine: Engine):
#    console = Console(file=io.StringIO())
#    syncer = NetexecSyncer(engine, console, workspaces_dir=TEST_NETEXEC_WORKSPACE, sync_hosts=True)
#
#    with patch(SQLITE3_PATCH_PATH) as mocksqlite3:
#        mocksqlite3.connect().cursor().fetchall.return_value = [(IP_TEST_VALUE, HOSTNAME_TEST_VALUE)]
#        syncer.sync()
#
#    assert get_hosts(engine) == [Host(host_id=1, ip=IP_TEST_VALUE, hostname=HOSTNAME_TEST_VALUE)]
#


# Syncing should not take too much time for large amount of credentials
def test_sync_host_netexec_big(engine: Engine):
    console = Console(file=io.StringIO())
    syncer = NetexecSyncer(
        engine, console, workspaces_dir=TEST_NETEXEC_WORKSPACE, sync_hosts=True
    )
    hosts = []
    hosts2 = []

    for i in range(1, 2000):
        hosts.append(
            Host(host_id=i, ip=IP_TEST_VALUE + str(i), hostname=HOSTNAME_TEST_VALUE)
        )
        hosts2.append((IP_TEST_VALUE + str(i), HOSTNAME_TEST_VALUE))

    start_time = time.time()

    with patch(SQLITE3_PATCH_PATH) as mocksqlite3:
        mocksqlite3.connect().cursor().fetchall.return_value = hosts2
        syncer.sync()

    end_time = time.time()

    assert get_hosts(engine) == hosts
    assert (end_time - start_time) < 1


def test_sync_host_netexec(engine: Engine):
    console = Console(file=io.StringIO())
    syncer = NetexecSyncer(
        engine, console, workspaces_dir=TEST_NETEXEC_WORKSPACE, sync_hosts=True
    )

    with patch(SQLITE3_PATCH_PATH) as mocksqlite3:
        mocksqlite3.connect().cursor().fetchall.return_value = [
            (IP_TEST_VALUE, HOSTNAME_TEST_VALUE)
        ]
        syncer.sync()

    assert get_hosts(engine) == [
        Host(host_id=1, ip=IP_TEST_VALUE, hostname=HOSTNAME_TEST_VALUE)
    ]


def test_sync_host_netexec_empty(engine: Engine):
    console = Console(file=io.StringIO())
    syncer = NetexecSyncer(
        engine, console, workspaces_dir=TEST_NETEXEC_WORKSPACE, sync_hosts=True
    )

    with patch(SQLITE3_PATCH_PATH) as mocksqlite3:
        mocksqlite3.connect().cursor().fetchall.return_value = []
        syncer.sync()

    assert not get_hosts(engine)

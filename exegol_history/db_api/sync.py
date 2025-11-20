from typing import Any
from sqlalchemy import Engine

from exegol_history.connectors.metasploit.metasploit_sync import MetasploitSyncer
from exegol_history.connectors.netexec.netexec_sync import NetexecSyncer
from exegol_history.db_api.creds import add_credentials
from exegol_history.db_api.hosts import add_hosts


def sync_objects(
    engine: Engine,
    config: dict[str, Any],
    sync_credentials: bool = False,
    sync_hosts: bool = False,
):
    credentials = []
    hosts = []

    for connector in config["sync"]:
        if (
            connector == NetexecSyncer.CONNECTOR_NAME
            and config["sync"][connector]["enabled"]
        ):
            syncer = NetexecSyncer(engine, config, sync_credentials, sync_hosts)
            (tmp1, tmp2) = syncer.sync()
            credentials += tmp1
            hosts += tmp2
        elif (
            connector == MetasploitSyncer.CONNECTOR_NAME
            and config["sync"][connector]["enabled"]
        ):
            syncer = MetasploitSyncer(engine, config)
            (tmp1, tmp2) = syncer.sync()
            credentials += tmp1
            hosts += tmp2

    add_credentials(engine, credentials)
    add_hosts(engine, hosts)

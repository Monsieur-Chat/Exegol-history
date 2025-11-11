import io
from rich.console import Console
from sqlalchemy import Engine
from exegol_history.cli.arguments import parse_arguments
from exegol_history.cli.functions import (
    DELETE_SUBCOMMAND,
    HOSTS_SUBCOMMAND,
    delete_objects,
)
from exegol_history.db_api.hosts import Host, add_hosts, get_hosts
from exegol_history.db_api.utils import MESSAGE_ID_NOT_EXIST
from exegol_history.tests.common import (
    HOSTNAME_TEST_VALUE,
    IP_TEST_VALUE,
)


def test_delete_host(engine: Engine):
    host1 = Host(id=1, ip=IP_TEST_VALUE + "2", hostname=HOSTNAME_TEST_VALUE + "2")
    host2 = Host(id=2, ip=IP_TEST_VALUE)
    host3 = Host(id=3, ip=IP_TEST_VALUE, hostname=HOSTNAME_TEST_VALUE)

    add_hosts(engine, [host1, host2, host3])

    command_line = f"{DELETE_SUBCOMMAND} {HOSTS_SUBCOMMAND} -i 2".split()
    args = parse_arguments().parse_args(command_line)

    delete_objects(args, engine, {})

    assert get_hosts(engine) == [host1, host3]


def test_delete_host_range(engine: Engine):
    host1 = Host(id=1, ip=IP_TEST_VALUE + "2", hostname=HOSTNAME_TEST_VALUE + "2")
    host2 = Host(id=2, ip=IP_TEST_VALUE)
    host3 = Host(id=3, ip=IP_TEST_VALUE, hostname=HOSTNAME_TEST_VALUE)
    host4 = Host(id=4, ip=IP_TEST_VALUE + "4", hostname=HOSTNAME_TEST_VALUE)
    host5 = Host(id=5, ip=IP_TEST_VALUE + "5", hostname=HOSTNAME_TEST_VALUE)

    add_hosts(engine, [host1, host2, host3, host4, host5])

    command_line = f"{DELETE_SUBCOMMAND} {HOSTS_SUBCOMMAND} -i 1-3,5".split()
    args = parse_arguments().parse_args(command_line)

    delete_objects(args, engine, {})

    assert get_hosts(engine) == [host4]


def test_delete_host_not_exist(engine: Engine):
    console = Console(file=io.StringIO())

    command_line = f"{DELETE_SUBCOMMAND} {HOSTS_SUBCOMMAND} -i 999".split()
    args = parse_arguments().parse_args(command_line)

    delete_objects(args, engine, console)

    assert MESSAGE_ID_NOT_EXIST in console.file.getvalue().replace("\n", "")
    assert len(get_hosts(engine)) == 0

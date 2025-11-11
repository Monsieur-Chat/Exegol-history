from sqlalchemy import Engine
from sqlalchemy.orm import Session
from textual.keys import Keys
from exegol_history.db_api.creds import Credential
from exegol_history.db_api.hosts import Host
from pathlib import Path


IP_TEST_VALUE = "127.0.0.1"
HOSTNAME_TEST_VALUE = "DC01"
ROLE_TEST_VALUE = "DC"

USERNAME_TEST_VALUE = "username"
PASSWORD_TEST_VALUE = "password"
HASH_TEST_VALUE = "hash"
DOMAIN_TEST_VALUE = "test.local"
CREDENTIALS_TEST_VALUE = [
    Credential(
        id=1,
        username=USERNAME_TEST_VALUE + "7",
    ),
    Credential(
        id=2,
        username=USERNAME_TEST_VALUE,
        password=PASSWORD_TEST_VALUE,
        hash=HASH_TEST_VALUE,
        domain=DOMAIN_TEST_VALUE,
    ),
    Credential(
        id=3, username=USERNAME_TEST_VALUE + "2", password=PASSWORD_TEST_VALUE + "2"
    ),
    Credential(
        id=4,
        username=USERNAME_TEST_VALUE + "3",
        password=PASSWORD_TEST_VALUE,
        hash=HASH_TEST_VALUE,
    ),
    Credential(id=5, username=USERNAME_TEST_VALUE + "4"),
    Credential(id=6, username=USERNAME_TEST_VALUE),
    Credential(
        id=7,
        username=USERNAME_TEST_VALUE + "6",
        password=PASSWORD_TEST_VALUE + "6",
        hash=HASH_TEST_VALUE + "6",
        domain=DOMAIN_TEST_VALUE + "6",
    ),
]
CREDENTIALS_TEST_VALUE_GOAD_PYPYKATZ = [
    Credential(
        id=1, username="DC$", hash="0b65cc18dde1c5548f06b8db074a76b3", domain="SCCMLAB"
    ),
    Credential(
        id=2,
        username="localuser",
        password="password",
        hash="8846f7eaee8fb117ad06bdd830b7586c",
        domain="SCCMLAB",
    ),
]

CREDENTIALS_TEST_VALUE_KDBX = [
    Credential(id=1, username=USERNAME_TEST_VALUE, password=PASSWORD_TEST_VALUE),
    Credential(
        id=2, username=USERNAME_TEST_VALUE + "2", password=PASSWORD_TEST_VALUE + "2"
    ),
]
CREDENTIAL1 = Credential(username=USERNAME_TEST_VALUE, hash=HASH_TEST_VALUE)
CREDENTIAL2 = Credential(
    username=USERNAME_TEST_VALUE + "2",
    password=PASSWORD_TEST_VALUE,
    hash=HASH_TEST_VALUE,
    domain=DOMAIN_TEST_VALUE,
)

HOSTS_TEST_VALUE = [
    Host(id=1, ip=IP_TEST_VALUE, hostname=HOSTNAME_TEST_VALUE, role=ROLE_TEST_VALUE),
    Host(id=2, ip=IP_TEST_VALUE + "2"),
    Host(id=3, ip=IP_TEST_VALUE + "2", hostname=HOSTNAME_TEST_VALUE + "2"),
    Host(id=4, ip=IP_TEST_VALUE + "3"),
]

TEST_ARTIFACTS_PATH = Path(__file__).parent / "artifacts"
TEST_HOSTS_CSV_COMMA = TEST_ARTIFACTS_PATH / "hosts_comma.csv"
TEST_HOSTS_CSV_COLON = TEST_ARTIFACTS_PATH / "hosts_colon.csv"
TEST_HOSTS_JSON = TEST_ARTIFACTS_PATH / "hosts.json"
TEST_CREDS_CSV_COMMA = TEST_ARTIFACTS_PATH / "creds_comma.csv"
TEST_CREDS_CSV_COLON = TEST_ARTIFACTS_PATH / "creds_colon.csv"
TEST_CREDS_CSV_EXPORT = TEST_ARTIFACTS_PATH / "creds_export.csv"
TEST_CREDS_JSON = TEST_ARTIFACTS_PATH / "creds.json"
TEST_CREDS_PYPYKATZ_JSON = TEST_ARTIFACTS_PATH / "pypykatz.json"
TEST_CREDS_SECRETSDUMP = TEST_ARTIFACTS_PATH / "secretsdump.dsv"
TEST_CREDS_KDBX = TEST_ARTIFACTS_PATH / "import.kdbx"
TEST_CREDS_KDBX_KEYFILE = TEST_ARTIFACTS_PATH / "import.key"


async def select_input_and_enter_text(pilot, input_id, input_text):
    await pilot.click(input_id)
    for character in list(input_text):
        if character == "\n":
            character = Keys.Enter

        await pilot.press(character)


async def select_input_erase_and_enter_text(pilot, input_id, input_text):
    await pilot.click(input_id)
    await pilot.press(Keys.ControlK)
    await pilot.press(*list(input_text))


async def select_select_index(pilot, input_id, select_index):
    await pilot.click(input_id)

    for i in range(0, select_index - 1):
        await pilot.press(Keys.Down)

    await pilot.press(Keys.Enter)


def delete_all_entries(engine: Engine):
    with Session(engine) as session:
        session.query(Credential).delete()
        session.query(Host).delete()
        session.commit()

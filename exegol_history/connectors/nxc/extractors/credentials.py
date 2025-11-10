from enum import Enum
import sqlite3
from exegol_history.db_api.creds import (
    Credential,
    add_credentials,
    edit_credentials,
)
from sqlalchemy import exc, select
from sqlalchemy.orm import Session


class NXCCredType(Enum):
    HASH = "hash"
    PASSWORD = "plaintext"
    KEY = "key"


class NXC_Credentials_Extractor:
    def __init__(self, db_file_path, kp, service_name):
        self.db_file_path = db_file_path
        self.kp = kp
        self.service_name = service_name

    def extract_and_add_credentials(self):
        try:
            conn = sqlite3.connect(self.db_file_path)
            cursor = conn.cursor()

            query = "SELECT username, password, domain, credtype FROM users"
            cursor.execute(query)
            rows = cursor.fetchall()

            for row in rows:
                username, password, domain, credtype = row

                credential = Credential(username=username, domain=domain)

                if credtype == NXCCredType.HASH:
                    credential.hash = password
                else:
                    credential.password = password

                try:
                    add_credentials(self.kp, [credential])
                    print("Add")
                except exc.IntegrityError:
                    with Session(self.kp) as session:
                        tmp = select(Credential).where(
                            Credential.username == username
                            and Credential.domain == domain
                        )
                        credential.id = session.scalars(tmp).one().id
                        edit_credentials(self.kp, [credential])
                        print("Edit")

            print(f"Synced {self.service_name} credentials")

            conn.close()
        except Exception as e:
            print(f"Error extracting from {self.db_file_path}: {e}")

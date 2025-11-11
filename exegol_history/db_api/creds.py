from sqlalchemy.orm import Mapped, mapped_column, Session
from sqlalchemy import select, UniqueConstraint, Engine
from sqlalchemy.dialects.sqlite import insert
from exegol_history.db_api.base import Base
from exegol_history.db_api.utils import MESSAGE_ID_NOT_EXIST


class Credential(Base):
    __tablename__ = "credentials"
    __table_args__ = (UniqueConstraint("username", "domain"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(nullable=True)
    password: Mapped[str] = mapped_column(nullable=True)
    hash: Mapped[str] = mapped_column(nullable=True)
    domain: Mapped[str] = mapped_column(nullable=True)

    REDACT_SEPARATOR = "*"

    def __init__(
        self,
        id: int = None,
        username: str = None,
        password: str = None,
        hash: str = None,
        domain: str = None,
    ):
        self.id = id
        self.username = username
        self.password = password
        self.hash = hash
        self.domain = domain

    def __eq__(self, value):
        return (
            (self.id == value.id)
            and (self.username == value.username)
            and (self.password == value.password)
            and (self.hash == value.hash)
            and (self.domain == value.domain)
        )

    def __repr__(self) -> str:
        return f"Credential(id={self.id}, username={self.username}, password={self.password}, hash={self.hash}, domain={self.domain})"

    # Reference: https://stackoverflow.com/questions/5022066/how-to-serialize-sqlalchemy-result-to-json
    def as_dict(self):
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def __iter__(self):
        return iter([self.id, self.username, self.password, self.hash, self.domain])


def add_credentials(engine: Engine, credentials: list[Credential]):
    with Session(engine, expire_on_commit=False) as session:
        for credential in credentials:
            query = insert(Credential).values(**credential.as_dict())
            tmp = credential.as_dict()
            tmp.pop("id", None)
            query = query.on_conflict_do_update(
                index_elements=["username", "domain"], set_=tmp
            )
            session.execute(query)

        session.commit()


def get_credentials(
    engine: Engine, id: str = None, redacted: bool = False
) -> list[Credential]:
    credentials = []

    if id:
        query = select(Credential).where(Credential.id == id)
    else:
        query = select(Credential)

    with Session(engine, expire_on_commit=False) as session:
        for credential in session.scalars(query):
            session.expunge(credential)
            if redacted:
                credential.password = Credential.REDACT_SEPARATOR * 8
                credential.hash = Credential.REDACT_SEPARATOR * 8

            credentials.append(credential)

        return credentials


def delete_credentials(engine: Engine, ids: list[str] = list()):
    with Session(engine, expire_on_commit=False) as session:
        query = Credential.__table__.delete().where(Credential.id.in_(ids))
        result = session.execute(query)

        session.commit()

    if result.rowcount <= 0:
        raise RuntimeError(MESSAGE_ID_NOT_EXIST)


def edit_credentials(engine: Engine, credentials: list[Credential]):
    with Session(engine, expire_on_commit=False) as session:
        for credential in credentials:
            credential_to_modify = session.get(Credential, credential.id)

            if not credential_to_modify:
                raise RuntimeError(MESSAGE_ID_NOT_EXIST)

            for attr in Credential.__table__.columns.keys():
                if attr == "id":
                    continue

                value = getattr(credential, attr, None)

                if value:
                    setattr(credential_to_modify, attr, value)

        session.commit()

from sqlalchemy.orm import Mapped, mapped_column, Session
from sqlalchemy import select, UniqueConstraint, Engine
from exegol_history.db_api.base import Base
from exegol_history.db_api.utils import MESSAGE_ID_NOT_EXIST
from sqlalchemy.dialects.sqlite import insert


class Host(Base):
    __tablename__ = "hosts"
    __table_args__ = (UniqueConstraint("ip", "hostname"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ip: Mapped[str] = mapped_column(nullable=True)
    hostname: Mapped[str] = mapped_column(nullable=True)
    role: Mapped[str] = mapped_column(nullable=True)

    def __init__(
        self, id: int = None, ip: str = None, hostname: str = None, role: str = None
    ):
        self.id = id
        self.ip = ip
        self.hostname = hostname
        self.role = role

    def __eq__(self, value):
        return (
            (self.id == value.id)
            and (self.ip == value.ip)
            and (self.hostname == value.hostname)
            and (self.role == value.role)
        )

    # Reference: https://stackoverflow.com/questions/5022066/how-to-serialize-sqlalchemy-result-to-json
    def as_dict(self):
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def __repr__(self) -> str:
        return f"Host(id={self.id}, ip={self.ip}, hostname={self.hostname}, role={self.role})"

    def __iter__(self):
        return iter([self.id, self.ip, self.hostname, self.role])


def add_hosts(engine: Engine, hosts: list[Host]):
    with Session(engine, expire_on_commit=False) as session:
        for host in hosts:
            query = insert(Host).values(**host.as_dict())
            tmp = host.as_dict()
            tmp.pop("id", None)
            query = query.on_conflict_do_update(
                index_elements=["ip", "hostname"], set_=tmp
            )
            session.execute(query)

        session.commit()


def get_hosts(engine: Engine, id: str = None) -> list[Host]:
    hosts = []

    if id:
        query = select(Host).where(Host.id == id)
    else:
        query = select(Host)

    with Session(engine, expire_on_commit=False) as session:
        for host in session.scalars(query):
            session.expunge(host)
            hosts.append(host)

        return hosts


def delete_hosts(engine: Engine, ids: list[str] = list()):
    with Session(engine, expire_on_commit=False) as session:
        query = Host.__table__.delete().where(Host.id.in_(ids))
        result = session.execute(query)

        session.commit()

    if result.rowcount <= 0:
        raise RuntimeError(MESSAGE_ID_NOT_EXIST)


def edit_hosts(engine: Engine, hosts: list[Host]):
    with Session(engine, expire_on_commit=False) as session:
        for host in hosts:
            credential_to_modify = session.get(Host, host.id)

            if not credential_to_modify:
                raise RuntimeError(MESSAGE_ID_NOT_EXIST)

            for attr in Host.__table__.columns.keys():
                if attr == "id":
                    continue

                value = getattr(host, attr, None)

                if value:
                    setattr(credential_to_modify, attr, value)

        session.commit()

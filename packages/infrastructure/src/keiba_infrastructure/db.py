from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker


def create_database_engine(database_url: str, *, echo: bool = False) -> Engine:
    engine = create_engine(database_url, echo=echo, future=True)
    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def enable_sqlite_foreign_keys(dbapi_connection: object, _: object) -> None:
            cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

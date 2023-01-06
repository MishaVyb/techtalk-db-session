import contextlib
import functools
import sys
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from models import MyModel  # type: ignore

sys.path.append(str(Path(__file__).resolve().parent))
url = 'postgresql+psycopg2://vybornyy:vbrn7788@localhost:5432/default'
engine = create_engine(url, pool_pre_ping=True, echo=True, echo_pool=True)

SessionLocal = sessionmaker(bind=engine)


def get_db(echo=None) -> Generator[Session, None, None]:
    with SessionLocal.begin() as session:
        yield session


@contextlib.contextmanager
def get_db_as_context(echo=None) -> Generator[Session, None, None]:
    with SessionLocal.begin() as session:
        yield session


class _DBSessionContext(contextlib._GeneratorContextManager[Session]):
    ...


def _db_session_context_factory(func):
    @functools.wraps(func)
    def helper(*args, **kwds):
        return _DBSessionContext(func, args, kwds)

    return helper


db_session = _db_session_context_factory(get_db)
db_session_v2 = contextlib.contextmanager(get_db)


@db_session()
def get_some_things_from_db(aaa: int = 12):
    ...


@db_session()
def get_some_things_from_db_v2(aaa: int = 12):
    ...


# !!!
# Unfortunately, brackets are necessary when you construct decorator via __call__
# they also are used at official documentation:
# https://docs.python.org/3/library/contextlib.html#contextlib.ContextDecorator
#
@get_db_as_context()
def get_some_things_from_db_v3(aaa: int = 12):
    ...


if __name__ == '__main__':
    with db_session() as session:
        session

    get_some_things_from_db()
    get_some_things_from_db_v2()
    get_some_things_from_db_v3()

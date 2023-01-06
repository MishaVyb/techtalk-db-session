import contextlib
import functools
import sys
from pathlib import Path
from typing import Callable, Generator, TypeVar, overload

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


# What if use contextlib.ContextDecorator
#
# NOTE:
# it is already a mixin for _GeneratorContextManager
# but it has no sense as we cannot pass Session object yield-ed from get_db generator
db_session_useless = contextlib.contextmanager(get_db)


@db_session_useless
def get_some_things_from_db(age: int, name: str, db: Session = ...) -> list[MyModel]:
    ...


# make it useable...
class _SessionScopeMaker(contextlib._GeneratorContextManager[Session]):
    def __init__(self) -> None:
        super().__init__(get_db)

    def __call__(self, func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            with self as session:
                # TODO
                self._assign_session(func, session)
                return func(*args, **kwargs)

        return inner

    @staticmethod
    def _assign_session(func, session):
        """
        Bring session to wrapped function arguments.
        """
        # TODO
        # [1] func is function
        # [2] func is method


# !!! brackets
@_SessionScopeMaker()
def get_some_things_from_db(aaa: int = 12):
    return aaa


########################################################################################
# v2 no brackets
########################################################################################

_Function = TypeVar('_Function', bound=Callable[..., object])


@overload
def db_session(func: _Function, *, bbb: int = -3) -> _Function:
    ...


@overload
def db_session(func: None = ..., *, bbb: int = -3) -> _SessionScopeMaker:
    ...


def db_session(func: _Function | None = None, *, bbb: int = -3) -> _Function | _SessionScopeMaker:
    scope_maker = _SessionScopeMaker()

    # decorator @db_session without brackets (or direct decoration assignment)
    if func:
        return scope_maker(func)

    # decorator @db_session() with brackets (or context manager usage)
    return scope_maker


@db_session
def get_some_things_from_db_v2(aaa: int = 12):
    return aaa


if __name__ == '__main__':
    with db_session() as session:
        session

    aaa = get_some_things_from_db_v2()

import contextlib
import functools
import sys
from pathlib import Path
from typing import Callable, Generator

from models import MyModel  # type: ignore
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

sys.path.append(str(Path(__file__).resolve().parent))
url = 'postgresql+psycopg2://vybornyy:vbrn7788@localhost:5432/default'
engine = create_engine(url, pool_pre_ping=True, echo=True, echo_pool=True)

SessionLocal = sessionmaker(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Here is one single function where we describe ALL session bahaviour logic.
    Handled as context manager. Usage:

    >>> fastapi.Depends(get_db)
    """
    # <extra setup>
    # do something if we will need it in a future
    #
    with SessionLocal.begin() as session:
        yield session

    #
    # <extra teardown>
    # do something if we will need it in a future


def db_session(using: Callable | None = None):

    # !!!
    Context = contextlib.contextmanager(get_db)
    if callable(using):
        # [1] @db_session -- it's decorator
        @functools.wraps(wrapped=using)
        def wrapper(self, *args, **kwargs):
            with Context() as session:
                self.session = session
                result = using(self, *args, **kwargs)
            return result

        return wrapper
    else:
        # [2] with db_session() -- it's context manager
        return Context()


########################################################################################
# # EXAMPLE 1 -- as context manager
########################################################################################

if __name__ == '__main__':
    with db_session() as session:
        result = session.query(MyModel).all()
    print(f'result len: {len(result)}')

########################################################################################
# EXAMPLE 2 -- as method decorator
########################################################################################


class MyService:
    session: Session

    def run(self):
        ...
        instance = MyModel(aaa='new instance')
        ...
        ...
        self.store([instance])

    @db_session
    def store(self, records: list[MyModel]):
        with db_session() as session:
            ...
        # NOTE
        # Why decorator, not context inside that method?..
        # because it's more verbose: we separate service logic from session handling
        # and getting rid of extra 4-spaces block

        self.session.add_all(records)
        ...
        return records


if __name__ == '__main__':
    MyService().run()

########################################################################################
# EXAMPLE 3 -- as function decorator
########################################################################################


@db_session
def get_some_things_from_db(session: Session):
    return session.query(MyModel).all()


if __name__ == '__main__':
    result = get_some_things_from_db()
    print(f'result len: {len(result)}')

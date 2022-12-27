import contextlib
import functools
import sys
from pathlib import Path
from typing import Callable, Generator

import requests
import uvicorn
from fastapi import Depends, FastAPI, HTTPException
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


# BONUS
# the same decorator logic for functions, not methods
# could be combined
def db_session(using: Callable):
    Context = contextlib.contextmanager(get_db)

    # find out session key-word-argument
    annotations = using.__annotations__
    session_attrs = {key for key, val in annotations.items() if val == Session}
    attr_name = session_attrs.pop()
    if len(session_attrs) != 1:
        raise RuntimeError()

    # TODO: check default
    using.__defaults__

    @functools.wraps(wrapped=using)
    def wrapper(*args, **kwargs):
        with Context() as session:
            kwargs[attr_name] = session
            result = using(*args, **kwargs)
        return result

    return wrapper


########################################################################################
# EXAMPLE 3 -- as function decorator
########################################################################################

# NOTE Naming:
# Name session argument as you want, it could be 'db' or 'session' or what ever?
# But important part is to type :Session annotation
#
@db_session
def get_some_things_from_db(age: int, name: str, db: Session = ...) -> list[MyModel]:
    print(f'filtering with args: {age=}, {name=}')
    return db.query(MyModel).all()


if __name__ == '__main__':
    result = get_some_things_from_db(12, 'asdf')
    print(f'result len: {len(result)}')

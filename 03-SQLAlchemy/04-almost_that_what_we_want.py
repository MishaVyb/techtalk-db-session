import sys
from pathlib import Path
from time import sleep
from typing import Generator

import requests
import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from models import MyModel
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

sys.path.append(Path(__file__).resolve().parent)
url = 'postgresql+psycopg2://vybornyy:vbrn7788@localhost:5432/default'
engine = create_engine(url, pool_pre_ping=True, echo=True, echo_pool=True)

SessionLocal = sessionmaker(bind=engine)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal.begin() as session:
        yield session


# NOTE: almost what we want but not yet..
#
def work_with_db_v3(session_generator):
    # [1] prepare session
    session = next(session_generator)

    # [2] work with session
    session.add(MyModel(aaa='new object'))
    # NOTE: does not matter autocommit=True/False if will be committed
    # session.commit()


# it's not good, because we have to catch and pass any exception into generator:
def work_with_db_v3_with_error(session_generator):
    # [1] prepare session
    session = next(session_generator)

    # [2] work with session
    session.add(MyModel(aaa='new object'))

    # [3] bad things happend:
    # [3.1] wrong way
    # raise ValueError('oops')

    # [3.2] right way
    try:
        session_generator.throw(ValueError('oops'))
    except ValueError:
        print('handle exception after session was closed and rolled back')


if __name__ == '__main__':
    #
    # NOTE: create generator at outer level for presentation purposes
    # yes, if we create it inside function scope, garbage collector will almost always
    # destroy generator which invoke __exit__ method for our session context
    # BUT it's also not good idea...
    #
    session_generator = get_db()

    try:
        work_with_db_v3(session_generator)
    except ValueError:
        print('handle exception after session was closed and rolled back')
    finally:
        print('close our get_db() decorator')
        # And how to close session?..

        # option 1:
        session_generator.close()

        # option 2:
        try:
            session_generator.throw(GeneratorExit)
        except GeneratorExit:
            pass

        # option 3
        try:
            next(session_generator)
        except StopIteration:
            pass

    sleep(20)

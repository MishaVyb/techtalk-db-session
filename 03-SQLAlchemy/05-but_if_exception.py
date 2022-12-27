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


# NOTE: it's not good, because we have to catch and pass any exception into generator
#
def work_with_db_v3_with_error(session_generator):
    # [1] prepare session
    session = next(session_generator)

    # [2] work with session
    session.add(MyModel(aaa='new object'))

    # [3] how to rice exceptions:
    # [3.1] wrong way
    # raise ValueError('oops')

    # [3.2] right way
    session_generator.throw(ValueError('oops'))


if __name__ == '__main__':
    session_generator = get_db()

    try:
        work_with_db_v3_with_error(session_generator)
    except ValueError:
        print('handle exception after session was closed and rolled back')
    finally:
        print('close our get_db() decorator')

        # NOTE:
        # noting hapend here, as generator already closed after .throw(..)
        session_generator.close()

    sleep(20)

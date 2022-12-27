import sys
from pathlib import Path
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

# NOTE
# For now we wont db session without fastAPI, how to do that?
# first of all, negative examples
def get_db() -> Generator[Session, None, None]:
    with SessionLocal.begin() as session:
        yield session


def work_with_db_v1(session=next(get_db())):
    # session here is Depends object, not sql Session
    raise ValueError
    session.query(MyModel).all()


# DO NOT DO THAT AND NOW WE KNOW WHY
def work_with_db_v2(session):
    session = next(get_db())
    session.query(MyModel).all()


if __name__ == '__main__':
    work_with_db_v1()

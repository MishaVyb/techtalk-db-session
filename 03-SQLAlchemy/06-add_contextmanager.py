import contextlib
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


def get_db() -> Generator[Session, None, None]:
    with SessionLocal.begin() as session:
        yield session


# AND NOW IT WORKS HOW WE WANT IT
db_session_context = contextlib.contextmanager(get_db)

# if __name__ == '__main__':
#     print('app start')
#     with db_session_context() as session:
#         session.add(MyModel(aaa='new object'))
#     print('app end')

if __name__ == '__main__':
    print('app start')
    with db_session_context() as session:
        session.add(MyModel(aaa='new object'))
        raise ValueError('oops')
    print('app end')

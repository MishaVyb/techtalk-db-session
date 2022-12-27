import sys
from pathlib import Path
from threading import Thread
from time import sleep

import requests
import uvicorn
from fastapi import Depends, FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

sys.path.append(Path(__file__).resolve().parent)
url = 'postgresql+psycopg2://vybornyy:vbrn7788@localhost:5432/default'
engine = create_engine(url, pool_pre_ping=True, echo=True, echo_pool=True)
app = FastAPI()


SessionLocal = sessionmaker(
    autocommit=True,  # ???
    autoflush=False,  # ???
    bind=engine,
)


def get_db_v1():
    db: Session = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_v2():
    engine.dispose()  # ???

    # We call for Session.begin() which produce another context manager and
    # implemantation similar to:
    """
    >>> @contextlib.contextmanager
    >>> def begin()
    >>>     with session():  # open session
    >>>         with self.begin():  # begin session
    >>>             yield self
    """
    # detail: https://docs.sqlalchemy.org/en/20/orm/session_basics.html#framing-out-a-begin-commit-rollback-block

    with SessionLocal.begin() as session:
        yield session
        # NOTE:
        # inner context calls session.commit(), if there were no exceptions
        # outer context calls session.close()

    # XXX
    # we do not need this, as session bind to engine already, but if we want unbind
    # Session class, that syntaxis could be used insted
    # with SessionLocal(engine) as session, session.begin():
    #     yield session


########################################################################################
# route
########################################################################################


@app.get("/")
def read_root(d=Depends(get_db_v2)):
    return {'value': str(d)}


if __name__ == '__main__':
    run = lambda: uvicorn.run(app, host='0.0.0.0', port=5001)
    Thread(target=run).start()

if __name__ == '__main__':
    sleep(1)
    response = requests.get('http://0.0.0.0:5001')
    print(response, response.json())

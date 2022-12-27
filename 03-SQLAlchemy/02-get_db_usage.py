import sys
from pathlib import Path
from threading import Thread
from time import sleep

import requests
import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from models import MyModel
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

sys.path.append(Path(__file__).resolve().parent)
url = 'postgresql+psycopg2://vybornyy:vbrn7788@localhost:5432/default'
engine = create_engine(url, pool_pre_ping=True, echo=True, echo_pool=True)
app = FastAPI()


# NOTE:
# to avoid conflicts with Session for type annotations. call it SessionLocal
SessionLocal = sessionmaker(
    autocommit=False,  # ??? anyway will be committed if .begin()
    autoflush=False,  # ???
    bind=engine,
)


def get_db():
    with SessionLocal.begin() as session:
        yield session


@app.get("/")
def read_root(db: Session = Depends(get_db)):
    return {'value': 'none'}


@app.get("/add")
def read_root(db: Session = Depends(get_db)):
    db.add(MyModel(aaa='aaa'))
    db.add(MyModel(bbb=123))
    return {'value': 'created'}


@app.get("/get")
def read_root(db: Session = Depends(get_db)):
    result = db.query(MyModel).all()
    return {'value': len(result)}


@app.get("/error")
def read_root(db: Session = Depends(get_db)):
    db.add(MyModel(bbb=123))
    raise HTTPException(400, 'bad things')
    return {'value': len(result)}


if __name__ == '__main__':
    run = lambda: uvicorn.run(app, host='0.0.0.0', port=5001)
    Thread(target=run).start()

if __name__ == '__main__':
    sleep(1)
    response = requests.get('http://0.0.0.0:5001/error')
    print(response, response.json())

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import session_context
from models import MyModel
from session_context import db_context

url = 'postgresql+psycopg2://vybornyy:vbrn7788@localhost:5432/default'
url_2 = 'postgresql+psycopg2://vybornyy:vbrn7788@localhost:5432/default_2'

session_context.engine = create_engine(url, pool_pre_ping=True, echo=True, echo_pool=True)
engine = create_engine(url, pool_pre_ping=True, echo=True, echo_pool=True)


logging.basicConfig(format='%(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__file__)


# app = FastAPI()


# @app.get('/')
# def read_root(
#     db: Session = Depends(get_db),
# ):
#     return db.query(MyModel).first()


# @db_context
# def get_some_things_from_db(aaa: str = 'bbb'):
#     return session.query(MyModel).limit(1).all()


class MyService:
    session: Session

    @db_context
    def get_some_things_from_db_as_bound_method(self, aaa: str = 'bbb'):
        return self.session.query(MyModel).limit(1).all()


# if __name__ == '__main__':
#     run = lambda: uvicorn.run(app, host='0.0.0.0', port=5001)
#     Thread(target=run).start()


# if __name__ == '__main__':
#     sleep(1)
#     response = requests.get('http://0.0.0.0:5001')
#     print(response, response.json())


if __name__ == '__main__':
    # ...
    # with db_context(bind=engine) as session:
    #     result = session.query(MyModel).limit(1).all()
    #     # raise ValueError

    # result = get_some_things_from_db()

    service = MyService()
    result = service.get_some_things_from_db_as_bound_method(
        'misha',
    )

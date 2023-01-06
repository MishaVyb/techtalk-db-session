import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import session
from models import MyModel
from session import db_scope

url = 'postgresql+psycopg2://vybornyy:vbrn7788@localhost:5432/default'
url_2 = 'postgresql+psycopg2://vybornyy:vbrn7788@localhost:5432/default_2'

# session.engine = create_engine(url, pool_pre_ping=True, echo=True, echo_pool=True)
another_db_using = create_engine(
    url,
    pool_pre_ping=True,
    echo=True,
    echo_pool=True,
)


logging.basicConfig(
    format='%(levelname)s - %(message)s',
    level=logging.DEBUG,
)
logger = logging.getLogger(__file__)


@db_scope
def get_some_things_from_db(aaa: str = 'bbb', *, db: Session = ...):
    print(type(db), db)
    return aaa


class MyService:
    db: Session

    @db_scope
    def get_some_things_from_db_as_bound_method(self, aaa: str = 'bbb'):
        print(type(self.db), self.db)
        self.get_extra()
        return aaa

    @db_scope
    def get_extra(self, *, aaa: Session = ...):
        print(type(aaa), aaa)
        return


if __name__ == '__main__':
    with db_scope(using=another_db_using) as session:
        r = session.query(MyModel).limit(1).all()
        print('!!!!', r)
        # raise ValueError

    # aaa = get_some_things_from_db('qwerty')
    # aaa = MyService().get_some_things_from_db_as_bound_method()
    # aaa = MyService().get_some_things_from_db_as_bound_method()

    # s = MyService()
    # s.get_some_things_from_db_as_bound_method()
    # s.get_some_things_from_db_as_bound_method()

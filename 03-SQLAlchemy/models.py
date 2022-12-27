# type: ignore

from sqlalchemy import VARCHAR, Column, Integer, create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy_utils import create_database, database_exists

url = 'postgresql+psycopg2://vybornyy:vbrn7788@localhost:5432/default'
engine = create_engine(url, pool_pre_ping=True, echo=True, echo_pool=True)
Base = declarative_base()


class MyModel(Base):
    __tablename__ = 'mymodel'

    id = Column(Integer, primary_key=True, nullable=False)
    aaa = Column(VARCHAR(255))
    bbb = Column(Integer)


def create_db():
    """
    creates DB test_collector,
    creates tables,
    allows to make queries,
    when test is done, drops DB
    """

    if not database_exists(engine.url):
        create_database(engine.url)

    Base.metadata.create_all(bind=engine)


# if __name__ == '__main__':
#     create_db()

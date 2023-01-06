import contextlib
import functools
import sys
from pathlib import Path
from typing import Callable, Generator, TypeVar, overload

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from models import MyModel  # type: ignore

sys.path.append(str(Path(__file__).resolve().parent))
url = 'postgresql+psycopg2://vybornyy:vbrn7788@localhost:5432/default'
engine = create_engine(url, pool_pre_ping=True, echo=True, echo_pool=True)


def get_db(*, using: Engine | None = None) -> Generator[Session, None, None]:
    using = using or engine
    print(type(using))
    with Session(using) as session, session.begin():
        yield session


_C = TypeVar('_C', bound=Callable)


class _SessionScopeMaker(contextlib._GeneratorContextManager[Session]):
    _instance: object | None = None
    _instance_session_attr: str | None = None

    def __init__(self, func=get_db, args=[], kwargs={}) -> None:
        super().__init__(func, args, kwargs)

    def __call__(self, func: _C):

        # almost the same implemantation as for super().__call__, but with _assign_session(..) call
        @functools.wraps(func)
        def inner(*args, **kwargs):
            recreated = self._recreate_cm()
            with recreated as session:
                recreated._assign_session(func, session, args, kwargs)
                return func(*args, **kwargs)

        return inner

    def __exit__(self, typ, value, traceback) -> bool | None:
        # NOTE:
        # When _SessionScopeMaker is used as decorator for methods, session objects is assigned to instance attribute.
        # And before session scope will be closed, we have to release session attribute to avoid ambiguity.
        if self._instance:
            delattr(self._instance, self._instance_session_attr)

        return super().__exit__(typ, value, traceback)

    def _assign_session(self, func: _C, session: Session, args: tuple, kwargs: dict):
        """
        Bring session to wrapped function argument, so it could be used inside function.
        """
        # find out session key-word-argument by its annotation
        annotations = func.__annotations__
        session_args = {key for key, val in annotations.items() if val == Session}

        if session_args:
            session_arg = session_args.pop()
            if session_args:
                raise RuntimeError(f'{func} has many arguments annotated as `Session`. Must be the only one. ')
            self._assign_session_to_argument(func, session, args, kwargs, session_arg)

        else:
            if not args:
                raise RuntimeError(f'{func} must have `self` argument or argument with `Session` annotation. ')
            instance = args[0]
            self._assign_session_to_instance(instance, session)

    def _assign_session_to_instance(self, instance: object, session: Session):
        annotations = getattr(instance, '__annotations__', {})
        session_attrs = {key for key, val in annotations.items() if val == Session}

        if not session_attrs:
            raise RuntimeError(f'{instance} must define attribute with `Session` annotation. ')

        session_attr = session_attrs.pop()
        if session_attrs:
            raise RuntimeError(f'{instance} has many attributes annotated as `Session`. Must be the only one. ')
        if hasattr(instance, session_attr):
            raise RuntimeError(
                f'{instance} already has `Session`. Do not call inside scoped function for another @db_scope function. '
            )

        # store values to relieve them at self.__exit__
        self._instance = instance
        self._instance_session_attr = session_attr
        setattr(instance, session_attr, session)

    def _assign_session_to_argument(self, func: _C, session: Session, args: tuple, kwargs: dict, arg_name: str):
        defaults = func.__kwdefaults__ or {}  # check defaults after start (*) symbol

        if defaults.get(arg_name) is not Ellipsis:
            raise RuntimeError(f'{func} mast have `Session` argument as key-word argument and define it as Elipsis. ')
        if kwargs.get(arg_name):
            raise RuntimeError(f'Do not pass session to {func} directly. ')

        kwargs[arg_name] = session


@overload
def db_scope(func: _C, *, using: Engine | None = None) -> _C:
    ...


@overload
def db_scope(func: None = ..., *, using: Engine | None = None) -> _SessionScopeMaker:
    ...


def db_scope(func: _C | None = None, *, using: Engine | None = None) -> _C | _SessionScopeMaker:
    scope_maker = _SessionScopeMaker(kwargs=dict(using=using))

    # decorator @db_scope without brackets (or direct decoration assignment)
    if func:
        return scope_maker(func)

    # decorator @db_scope() with brackets (or context manager usage)
    return scope_maker


########################################################################################
# Test & Examples
########################################################################################


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
    # with db_scope() as session:
    #     session

    # aaa = get_some_things_from_db('qwerty')
    # aaa = MyService().get_some_things_from_db_as_bound_method()
    # aaa = MyService().get_some_things_from_db_as_bound_method()

    s = MyService()
    s.get_some_things_from_db_as_bound_method()
    # s.get_some_things_from_db_as_bound_method()

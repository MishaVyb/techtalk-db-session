"""
Essential tools to operate SQLAlchemy session scope.

Use `get_db` for `fastapi.Depends` and `db_scope` for non API server sessions. Session will be committed or rolled back
in case of exception and closed after all.
"""

import contextlib
import functools
import logging
from typing import Callable, Generator, TypeVar, overload

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

__all__ = ['engine', 'get_db', 'db_scope']

logger = logging.getLogger(__name__)

engine: Engine | None = None
"""
Default engine using. Bind `get_db` and `db_scope` to global engine by module attribute assignment:

>>> import session
>>> session.engine = sqlalchemy.create_engine(...)
"""


def get_db(*, using: Engine | None = None) -> Generator[Session, None, None]:
    """
    Generator factory to build context manager via contextlib.contextmanager or fastapi.Depends. Usage:

    >>> @app.get('/')
    >>> def read_root(d=Depends(get_db))
    """
    using = using or engine
    if not using:
        raise RuntimeError('Define global engine or pass using engine directly. ')

    with Session(using) as session, session.begin():
        yield session


_C = TypeVar('_C', bound=Callable)


class _SessionScopeMaker(contextlib._GeneratorContextManager[Session]):
    _instance: object | None = None
    _instance_session_attr: str | None = None

    def __enter__(self):
        using = self.kwds.get('using') or engine
        logger.debug(f'Enter into session scope with {using}. ')

        return super().__enter__()

    def __exit__(self, typ, value, traceback):
        exc_detail = f'Exception was received: {typ}. Session will be rolled back. ' if typ else ''
        logger.debug(f'Exit from session scope. {exc_detail}')

        # NOTE:
        # When _SessionScopeMaker is used as decorator for methods, session objects is assigned to instance attribute.
        # And before session scope will be closed, we have to release session attribute to avoid ambiguity.
        if self._instance:
            delattr(self._instance, self._instance_session_attr)
        return super().__exit__(typ, value, traceback)

    def __call__(self, func: _C):
        # almost the same implemantation as for super().__call__, but with _assign_session(..) call
        @functools.wraps(func)
        def inner(*args, **kwargs):
            recreated = self._recreate_cm()
            with recreated as session:
                recreated._assign_session(func, session, args, kwargs)
                return func(*args, **kwargs)

        return inner

    @staticmethod
    def _get_session_annotation(obj: object) -> set[str]:
        """
        Find out session keyword arguments by its annotation. Return arguments names.
        """
        annotations = getattr(obj, '__annotations__', {})
        return {key for key, val in annotations.items() if val == Session}

    def _assign_session(self, func: _C, session: Session, args: tuple, kwargs: dict):
        """
        Bring session to wrapped function argument, so it could be used inside function.
        """
        session_args = self._get_session_annotation(func)
        if session_args:
            session_arg = session_args.pop()
            if session_args:
                raise RuntimeError(f'{func} has many arguments annotated as `Session`. Must be the only one. ')
            self._assign_session_to_argument(func, session, args, kwargs, session_arg)

        else:
            # if func is not expecting for Session argument, assing it to session attribute of self object
            if not args:
                raise RuntimeError(f'{func} must have `self` argument or argument with `Session` annotation. ')
            instance = args[0]
            self._assign_session_to_instance(instance, session)

    def _assign_session_to_instance(self, instance: object, session: Session):
        session_attrs = self._get_session_annotation(instance)
        if not session_attrs:
            raise RuntimeError(f'{instance} must define attribute with `Session` annotation. ')

        session_attr = session_attrs.pop()
        if session_attrs:
            raise RuntimeError(f'{instance} has many attributes annotated as `Session`. Must be the only one. ')
        if hasattr(instance, session_attr):
            raise RuntimeError(
                f'{instance} already has `Session`. Do not call inside scoped function for another @db_scope function. '
            )

        # memorize values to release them at self.__exit__
        self._instance = instance
        self._instance_session_attr = session_attr
        setattr(instance, session_attr, session)

    def _assign_session_to_argument(self, func: _C, session: Session, args: tuple, kwargs: dict, arg_name: str):
        defaults = func.__kwdefaults__ or {}  # check function defaults after star (*) symbol

        if defaults.get(arg_name) is not Ellipsis:
            raise RuntimeError(f'{func} mast have `Session` argument as keyword argument and define it as Elipsis. ')
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
    """
    Database session scope. Session will be open, committed and closed internally. And rolled back in case of exception.
    ### Usage:

    * First of all, assign engine to this module. This step could be omitted by passing engine using directly.

    >>> import session
    >>> session.engine = sqlalchemy.create_engine(...)

    * As function decorator.

    >>> @db_scope
    ... def get_something_from_db(limit: int = 10, *, db: Session = ...):
    ...     return db.query(MyModel).limit(10).all()

    * As method decorator.

    >>> class MyService:
    ...     db: Session
    ...
    ...     @db_scope
    ...     def get_something_from_db(limit: int = 10):
    ...         return self.db.query(MyModel).limit(10).all()

    NOTE:
    Session attribute (argument) can be named as you like. Important part is type Session annotation to it.

    * Also it can be used as usual context manager.

    >>> with db_scope() as session:
    ...     result = session.query(MyModel).limit(10).all()

    * If your app operating with several databases, pass engine directly.

    >>> @db_scope(using=another_db_engine)
    ... def get_something_from_db(...):
    ...     ...
    """
    scope_maker = _SessionScopeMaker(func=get_db, args=[], kwds=dict(using=using))

    # decorator @db_scope without brackets (or direct decoration assignment), __call__ invokes in that way
    if func:
        return scope_maker(func)

    # db_scope as context manager or as decorator @db_scope() with brackets.
    # if decorator, scope_maker.__call__(func) will be invoked by python infernally.
    return scope_maker

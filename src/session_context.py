"""
Essential tools to operate sqlalchemy Session scope in different situation.

Please, read the guide before usage: https://gitlab.datafort.ru/dev/datafort_utils/-/wikis/session-context

### FastAPI
>>> Depends(get_db)

### Local Session Context
>>> @db_context                       # decorator usage
>>> with db_context() as session:     # or context manager as usual

### Flask
There are no special tool is necessary to handle session for flask applications.
You should use `flask_sqlalchemy.SQLAlchemy` object, which operate its `db.session` as `sqlalchemy.orm.scoped_session`.

NOTE: `scoped_session` has special logic for sharing the same Session instances among different threads and
`flask_sqlalchemy.SQLAlchemy` do all that stuff internally, including open/close/commit and rolling back.

### Tests
* Replace global engine with tested one by monkeypatch fixture.

>>> @pytest.fixture()
>>> def patch_engine(monkeypatch: pytest.MonkeyPatch):
...     monkeypatch.setattr(datafort_utils.database.session_context, 'engine', TestEngine)

* Or, even easer, just re-assign engine globally in fixture or at conftest.py file.

>>> datafort_utils.database.session_context.engine = TestEngine
"""
from __future__ import annotations

import contextlib
import functools
import inspect
import logging
from typing import Callable, Generator, TypeVar, overload

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

engine: Engine | None = None
"""
Default engine. Bind `get_db` and `db_context` to global engine by module attribute assignment:

>>> import datafort_utils
>>> datafort_utils.database.session_context.engine = sqlalchemy.create_engine(...)
"""


def get_db(**session_kwargs) -> Generator[Session, None, None]:
    """
    Generator factory to build context manager via `contextlib.contextmanager` or `fastapi.Depends`.

    Docs: https://gitlab.datafort.ru/dev/datafort_utils/-/wikis/session-context

    ### Usage.
    >>> @app.get('/')
    >>> def read_root(d=Depends(get_db))

    ### Engine.
    Assign engine to this module before usage.
    >>> import datafort_utils
    >>> datafort_utils.database.session_context.engine = sqlalchemy.create_engine(...)
    """
    session_kwargs.setdefault('bind', engine)
    if not session_kwargs['bind']:
        raise RuntimeError('Assign global engine to this module or pass using engine directly. ')

    with Session(**session_kwargs) as session, session.begin():
        yield session


_C = TypeVar('_C', bound=Callable)


class _SessionScopeMaker(contextlib._GeneratorContextManager[Session]):
    """
    This is a private api and you do not have to use it directly.

    Docs: https://gitlab.datafort.ru/dev/datafort_utils/-/wikis/session-context

    ### Implementation Notes:
    This accessory class inherit all functionality from `_GeneratorContextManager` and do *almost* the same things.
    Extended behavior:
    * logging at `__enter__` and `__exit__` for debugging
    * invoke `self._assign_session(...)` when `SessionScopeMaker` is used as decorator via `@db_context`
    * release expired `Session` attribute from class instance which method wrapped into `@db_context`

    Why that custom implementation for `__call__` and what is `_assign_session(..)` for?
    * `_SessionScopeMaker` is a context manager for open/close/commit/rollback sessions.
    * Also `_SessionScopeMaker` is a decorator(!). We define __call__ to implement that behavior.
    * By the way, base class `GeneratorContextManager` from contextlib do the same. But there are one small difference.
    * When we use self context manager, we receive ready-to-use session object.

    >>> with self as session:
    ...     return func(*args, **kwargs)    # calling for wrapped function

    * But how to bring that opened session to wrapped function where it actually will be used?
    * That the reason to define `_assign_session(..)` method where could be 2 ways of behavior:
        1. Assign session to wrapped function argument.
        The logic is to find any argument with `session: Session` type annotation and assign session to it.
        2. If there are no such annotations, we take first function argument which should be class instance (`self`).
        And then the same logic: find class attribute with `session: Session` type annotation and assign session to it.
    """

    _instance: object | None = None
    _instance_session_attr: str | None = None

    def __enter__(self) -> Session:
        using = self.kwds.get('bind', engine)
        logger.debug(f'Enter into session scope with {using}. ')

        return super().__enter__()

    def __exit__(self, typ, value, traceback) -> bool:
        exc_detail = f'Exception was received: {typ}. Session will be rolled back. ' if typ else ''
        logger.debug(f'Exit from session scope. {exc_detail}')

        # NOTE:
        # When _SessionScopeMaker is used as decorator for methods, session objects is assigned to instance attribute.
        # And before session scope will be closed, we have to release session attribute to avoid ambiguity.
        if self._instance:
            delattr(self._instance, self._instance_session_attr)
        return super().__exit__(typ, value, traceback)

    def __call__(self, func: _C) -> _C:
        @functools.wraps(func)
        def inner(*args, **kwargs):
            # NOTE
            # We need to recreate self every time when decorated function is called, otherwise it cannot be used for
            # more than one function. recreate_cm() return shallow copy of self and that's all.
            # super().__call__ do the same.
            #
            # See _GeneratorContextManagerBase._recreate_cm() for more detail. If going deeper, that implementation
            # is necessary, because of deleting self.args, self.kwds, self.func in super().__enter__() method.
            #
            recreated = self._recreate_cm()
            with recreated as session:
                recreated._assign_session(func, session, args, kwargs)
                return func(*args, **kwargs)

        return inner

    @staticmethod
    def _get_session_annotation(obj: object) -> str:
        """
        Find out session keyword arguments (or session class attribute) by its annotation. Return argument name.

        Implementation notes: https://docs.python.org/3/howto/annotations.html#annotations-howto
        """

        annotations = getattr(obj, '__annotations__', {})
        if any(map(lambda type_hint: isinstance(type_hint, str), annotations.values())):
            # TODO https://jira.datafort.ru/browse/DEV-2607
            #
            # Manually Un-Stringizing Stringized Annotations
            # How-To: https://docs.python.org/3/howto/annotations.html#manually-un-stringizing-stringized-annotations
            #
            # Or use inspect.get_annotations (only for python 3.10 and above)
            raise NotImplementedError(
                'Postponed evaluation of annotations are not supported. Discard: `from __future__ import annotations`. '
                'Detail: https://peps.python.org/pep-0563/'
            )

        arg_names = {key for key, val in annotations.items() if val == Session}
        if not arg_names:
            raise RuntimeError(f'{obj} must define argument (attribute) with `Session` annotation. ')

        # take the only one Session argument (attribute):
        arg_name = arg_names.pop()
        if arg_names:
            raise RuntimeError(f'{obj} has many arguments (attributes) annotated as `Session`. Must be the only one. ')
        return arg_name

    def _assign_session(self, func: _C, session: Session, args: tuple, kwargs: dict) -> None:
        """
        Bring session to wrapped function, so it could be used inside.
        """
        signature = inspect.signature(func, eval_str=True)
        class_instance = signature.bind_partial(*args, **kwargs).arguments.get('self')

        if class_instance is None:  # simple function (not method) case:
            self._assign_session_to_argument(func, session, args, kwargs)

        else:  # class method case:
            self._assign_session_to_instance(class_instance, session)

    def _assign_session_to_instance(self, instance: object, session: Session) -> None:
        attr_name = self._get_session_annotation(instance)
        if hasattr(instance, attr_name):
            raise RuntimeError(
                f'{instance} already has Session. Do not call inside scoped function for another @db_context function. '
            )

        # memorize values to release them at self.__exit__
        self._instance = instance
        self._instance_session_attr = attr_name
        setattr(instance, attr_name, session)

    def _assign_session_to_argument(self, func: _C, session: Session, args: tuple, kwargs: dict) -> None:
        arg_name = self._get_session_annotation(func)
        defaults = func.__kwdefaults__ or {}  # check function defaults after star (*) symbol

        if defaults.get(arg_name) is not Ellipsis:
            raise RuntimeError(f'{func} mast have `Session` argument as keyword argument with `Ellipsis` as default. ')
        if kwargs.get(arg_name):
            raise RuntimeError(f'Do not pass `Session` to {func} directly. ')

        kwargs[arg_name] = session


@overload
def db_context(func: _C, **session_kwargs) -> _C:
    ...


@overload
def db_context(func: None = None, **session_kwargs) -> _SessionScopeMaker:
    ...


def db_context(func: _C | None = None, **session_kwargs) -> _C | _SessionScopeMaker:
    """
    Database session scope. Session will be open, committed and closed internally. And rolled back in case of exception.

    Docs: https://gitlab.datafort.ru/dev/datafort_utils/-/wikis/session-context

    ### Usage:
    * As function decorator.

    >>> @db_context
    ... def get_something_from_db(limit: int = 10, *, db: Session = ...):
    ...     return db.query(MyModel).limit(10).all()

    * As method decorator.

    >>> class MyService:
    ...     session: Session
    ...
    ...     @db_context
    ...     def get_something_from_db(self, limit: int = 10):
    ...         return self.session.query(MyModel).limit(10).all()

    NOTE:
    Session attribute (argument) can be named as you like. Important part is type Session annotation to it.

    * Also it can be used as usual context manager.

    >>> with db_context() as session:
    ...     result = session.query(MyModel).limit(10).all()

    ### Engine.
    * Assign engine to this module before usage.

    >>> import datafort_utils
    >>> datafort_utils.database.session_context.engine = sqlalchemy.create_engine(...)

    * Or, if your app operating with several databases, pass engine directly.

    >>> @db_context(bind=another_db_engine)
    ... def get_something_from_db(...):
    ...     ...
    """
    scope_maker = _SessionScopeMaker(func=get_db, args=[], kwds=session_kwargs)

    # decorator @db_context without brackets (or direct decoration assignment), __call__ invokes in that way
    if func:
        return scope_maker(func)

    # db_context as context manager or as decorator @db_context() with brackets.
    # if decorator, scope_maker.__call__(func) will be invoked by python infernally.
    return scope_maker

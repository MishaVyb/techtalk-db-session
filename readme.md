## Tech Talk
# How to work with SQLAlchemy session (with and without FastAPI)

## мотивация
Хочется иметь такой иснтрументы чтобы он:
* был универсальным (единый иструмент как для работы с FastAPI так и без)
* отрабатывал все необходимые действия
    * открыть сессию
    * закоммитеть и закрыть сессию
    * откатить в случае ошибки
* занимал мало места и не отвлекал (1 строчка, без вложенной структуры)
* покрывал следующие области применения:
    * сессия закрывается и открывается внутри одной функции
    * сессия закрывается и открывается внутри одного метода
    * сессия открывается в одном методе класса, а закрывается в другом..
* можно было реализовать pytest с тестовй БД

##  содержание
### генераторы \ контекст менеджеры
1. вспомним, что такое генераторы и как они работают.
    `generator.throw()` `generator.close()`
2. и как отрабоатывает тот же генератор, но обернутый внутрь контекст менеджера
3. как вбросить ошибку в генератор и почему генератор ее не отлавливается, если пишем просто `raise SomeError(...)`

### Depends в FastAPI
1. рассмотрим варианты через `try/except` и через `with Context:`
2. посмотрим, как FastAPI использует `contextlib.contextmanager` из коробки

### Session in SQLAlchemy
1. рассмотрим инструмент `get_db` для FastAPI (реализованный через `try/except` и через `with Session.begin() as session:`)
2. посмотрим, как можно и как не стоит пользоваться `get_db` за рамками FastAPI
3. реализуем дополнительный инструмент, который работает как контекст менеджер и как декоратор.
    `db_session = contextlib.contextmanager(get_db)`

## links
* [article about context managers in general](https://rednafi.github.io/digressions/python/2020/03/26/python-contextmanager.html)
* [built-in contextlib](https://docs.python.org/3/library/contextlib.html)
* [FastAPI dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/#dependencies-with-yield)
* [the way to open/close SQLAlcemy sessions](https://docs.sqlalchemy.org/en/20/orm/session_basics.html#using-a-sessionmaker)
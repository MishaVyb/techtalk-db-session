from threading import Thread
from time import sleep

import requests
import uvicorn
from fastapi import Depends, FastAPI

app = FastAPI()


class MyContext:
    def __enter__(self):
        print('my context enter')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print(f'my context exit: {exc_type, exc_value, traceback}')


# NOTE
# the same as simple dependence, that generator wrapped into @contextlib.contextmanager
# but thanks MyContext(..) we have more ways to control context behavior
#
def my_dependence():
    print('dependence in')
    with MyContext() as context:
        yield '<hi, i`m in context>'
    print('dependence out')


@app.get("/")
def read_root(d=Depends(my_dependence)):
    return {'value': str(d)}


if __name__ == '__main__':
    run = lambda: uvicorn.run(app, host='0.0.0.0', port=5001)
    Thread(target=run).start()

if __name__ == '__main__':
    sleep(1)
    response = requests.get('http://0.0.0.0:5001')
    print(response, response.json())

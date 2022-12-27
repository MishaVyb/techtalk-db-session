from threading import Thread
from time import sleep

import requests
import uvicorn
from fastapi import Depends, FastAPI

app = FastAPI()

# NOTE:
# that generator wrapped into @contextlib.contextmanager by fastAPI internally
# when it passe to Depends(..)
#
def my_dependence():
    print('dependence in')
    yield 'depended value'
    print('dependence out')


def my_custom_file_open():
    ...


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

import contextlib
from threading import Thread
from time import sleep

import requests
import uvicorn
from fastapi import Depends, FastAPI, HTTPException

app = FastAPI()

########################################################################################
# option 1
########################################################################################

# NOTE
# v1 and v2 almost the same thing, only syntaxis is different
#

contextlib.contextmanager


def my_dependence_v1():
    print('dependence in')
    try:
        yield '<hi, i`m in context>'
    except Exception as e:
        print(f'except 1: {e}')
        raise e
    finally:
        print('dependence out')


########################################################################################
# option 2
########################################################################################


# class MyContext:
#     def __enter__(self):
#         print('my context enter')
#         return self

#     def __exit__(self, exc_type, exc_value, traceback):
#         print(f'my context exit: {exc_type, exc_value, traceback}')

#         if exc_type == GeneratorExit:
#             return  # nothing to handle

#         print('do something with exception at context level')
#         # return True
#         # NOTE:
#         # we do not handle that exception totally and do not prevent continuous
#         # exception behavior (for example let FastAPI return response with 400 code)


# def my_dependence_v2():
#     print('dependence in')
#     with MyContext() as context:
#         yield '<hi, i`m in context>'
#     print('dependence out')


########################################################################################
# route
########################################################################################


@app.get("/")
def read_root(d=Depends(my_dependence_v1)):
    raise HTTPException(400, 'bad thing')
    # raise ValueError  # make respone with 500 status code
    return {'value': str(d)}


if __name__ == '__main__':
    run = lambda: uvicorn.run(app, host='0.0.0.0', port=5001)
    Thread(target=run).start()

if __name__ == '__main__':
    sleep(1)
    response = requests.get('http://0.0.0.0:5001')
    print(response, response.json())

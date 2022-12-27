class Context:
    def __enter__(self):
        print('context enter')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print(f'context exit: {exc_type, exc_value, traceback}')

        # # NOTE: no re-rising exception, just return None
        # return

        # NOTE: if we handle exception here, any True value mast be returned
        # print('exception handled at context level')
        # return True


def foo():
    with Context() as c:
        print('do something... oops, bad thing happened')
        raise ValueError


if __name__ == '__main__':
    try:
        foo()
    except ValueError:
        print('exception handled at outer level')

import functools

import pytest


def say_type(aaa: int = 12):
    ...


class CountCalls:
    def __init__(self, func, description=None):
        functools.update_wrapper(self, func)
        self.func = func
        self.num_calls = 0
        self.description = description

    # @functools.wraps(say_type)
    def __call__(self, *args, **kwargs):
        self.num_calls += 1
        print(f"<Call {self.num_calls} of {self.func.__name__} ({self.description})>")
        return self.func(*args, **kwargs)


@CountCalls(description='.......')
def say(aaa: int = 12):
    """
    Say something...
    """
    print("Whee!")


if __name__ == '__main__':
    print(say.__name__)
    print(say.__doc__)
    print(say.__annotations__)

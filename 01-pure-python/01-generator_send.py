# usefull for coroutine
def generator_send():
    value = yield 'hello'
    print(f'value send in generator: {value}')
    return 'value to exit'


if __name__ == '__main__':
    generator = generator_send()

    generator.send(None)  # only None is available: ~ generator.__next__() --> 'hello'
    try:
        generator.send('goodby')
    except StopIteration as e:
        e.value == 'value to exit'

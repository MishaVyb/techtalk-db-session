def generator_close():
    yield '1'
    yield '2'
    yield '3'
    yield '4'
    ...

    return 'closed'


if __name__ == '__main__':
    generator = generator_close()
    print(next(generator))
    generator.close()
    try:
        next(generator)
    except StopIteration as e:
        print(e.value)  # None

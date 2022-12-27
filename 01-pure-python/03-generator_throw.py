def generator_throw():
    try:
        yield '1'
        ...
    except ValueError:
        print('catch exception')

    yield '2'
    yield '3'
    yield '4'
    return 'closed'


if __name__ == '__main__':
    generator = generator_throw()
    print(next(generator))
    generator.throw(ValueError)

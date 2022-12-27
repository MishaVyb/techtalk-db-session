class Context:
    def __enter__(self):
        print('context enter')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print(f'context exit: {exc_type, exc_value, traceback}')

        if exc_type == GeneratorExit:
            return  # nothing to handle

        print('exception handled at context level')
        return True


def generator_with_context():
    print('generator in')
    with Context() as context:
        try:
            yield '<hi, i`m in context>'
        except ValueError:
            print('!!!!!!')
    print('generator out')


def do_some_inside_context():
    generator = generator_with_context()
    value = next(generator)
    print(f'do something with {value}... oops, bad thing happened')

    # And how to give exception handling to generantor....?

    # [1] option 1 -- not working
    # raise ValueError # ???

    # [2] option 2 -- almost working
    # generator.throw(ValueError)

    # [3] option 3 -- proper way
    try:
        generator.throw(ValueError)
    except StopIteration:
        pass

    # NOTE: generator already closed by .throw(..)
    # generator.close()


if __name__ == '__main__':
    do_some_inside_context()

    print('do staff after all things')

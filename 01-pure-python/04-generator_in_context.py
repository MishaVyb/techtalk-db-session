class Context:
    def __enter__(self):
        print('context enter')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print(f'context exit: {exc_type, exc_value, traceback}')


def generator_with_context():
    print('generator in')
    with Context() as context:
        yield '<hi, i`m in context>'
    print('generator out')


if __name__ == '__main__':
    print('\n\t [1] proper way. ')

    generator = generator_with_context()
    value = next(generator)
    print(f'do staff with {value}')
    generator.close()
    print('do staff after closing')

# if __name__ == '__main__':
#     print('\n\t [2] NOT proper way. ')

#     value = next(generator_with_context())
#     # NOTE
#     # generator already closed, as nothing is point to generator object and garbage
#     # collector destroy it right after next(..)
#     #
#     print(f'do staff with {value}')
#     ...
#     print('do staff after closing?? not way, already closed!')

# if __name__ == '__main__':
#     print('\n\t [3] almost proper way. ')

#     generator = generator_with_context()
#     value = next(generator)
#     print(f'do staff with {value}')
#     # NOTE:
#     # generator is closing after program execution by garbage collector, but we do not
#     # control it explicitly
#     #
#     # generator.close()
#     # print('do staff after closing')

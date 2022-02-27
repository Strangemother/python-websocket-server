

def accept(one=None):
    if one:
        print('container value truthy:', one)

    if one is None:
        print('Container value asserts None')


accept(one=1)
accept()
accept(None)
accept(one=None)

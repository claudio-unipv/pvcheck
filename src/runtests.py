import os

_TESTDIR = '../test'

if __name__ == '__main__':
    import doctest
    for f in os.listdir(_TESTDIR):
        if f.endswith('.txt'):
            doctest.testfile(os.path.join(_TESTDIR, f))

#!/usr/bin/env python3

"""Run tests over the pvcheck source files.

Use the '-v' option for a more complete output.
"""

import os
import sys
import doctest


SRCDIR = "../src"
TESTDIR = '.'

sys.path.insert(0, SRCDIR)
failed = 0
attempted = 0
files = 0
for f in os.listdir(TESTDIR):
    if f.endswith('.txt'):
        result = doctest.testfile(os.path.join(TESTDIR, f))
        failed += result.failed
        attempted += result.attempted
        files += 1

print("{} tests in {} files.".format(attempted, files))
print("{} passed and {} failed.".format(attempted - failed, failed))
print("Test passed." if failed == 0 else "Test failed.")


# python3 -m unittest discover -s . -p 'test_*.py'

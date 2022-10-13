import unittest
import sys
sys.path.insert(0, '..')
import io
from pvcheck.pvcheck import *
from pvcheck.testdata import *
from pvcheck.formatter import *
from pvcheck.executor import *


class TestPVCheck(unittest.TestCase):
    def test_exec_single_test(self):
        dst = io.StringIO()
        fmt = TextFormatter(destination=dst)
        pv = PvCheck(Executor(), fmt)

        test = TestCase("echo", [
            Section(".ARGS", ["[OUT]\nfoo"]),
            Section("OUT", ["foo"])
        ])

        ok = pv.exec_single_test(test, ["echo"])
        exp = """TEST: echo
COMMAND LINE:
echo [OUT]
foo
OUT: OK
"""
        self.assertTrue(ok)
        self.assertEqual(dst.getvalue(), exp)

    def test_exec_suite(self):
        dst = io.StringIO()
        verb = TextFormatter.SUCCESS
        fmt = TextFormatter(destination=dst,
                                      verbosity=verb)
        pv = PvCheck(Executor(), fmt)

        sections = [
            Section(".TEST", ["echo1"]),
            Section(".ARGS", ["[OUT]\nfoo"]),
            Section("OUT", ["foo"]),
            Section(".TEST", ["echo2"]),
            Section(".ARGS", ["[OUT]\nbar"]),
            Section("OUT", ["foo"]),
            Section(".TEST", ["echo3"]),
            Section(".ARGS", ["[OUT]\nfoo"]),
            Section("OUT", ["foo"]),
            Section("NOTFOUND", ["notfound"])
        ]
        failures = pv.exec_suite(TestSuite(sections), ["echo"])
        exp = """OUT: OK
OUT: line 1 is wrong  (expected 'foo', got 'bar')
OUT: OK
NOTFOUND: missing section
"""
        self.assertEqual(failures, 2)
        self.assertEqual(dst.getvalue(), exp)


if __name__ == '__main__':
    unittest.main()

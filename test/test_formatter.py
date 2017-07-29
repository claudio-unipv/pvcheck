import unittest
import sys
sys.path.insert(0, '../src')
import io
from formatter import *
from testdata import Section
import executor


class TestTextFormatter(unittest.TestCase):
    def test_empty_session(self):
        dst = io.StringIO()
        f = TextFormatter(destination=dst)
        f.begin_session()
        f.end_session()
        self.assertEqual(dst.getvalue(), '')

    def test_single_case(self):
        dst = io.StringIO()
        f = TextFormatter(destination=dst)
        f.begin_session()
        f.begin_test("description", ["a b c"], "1\n2\n3\n", "x\ny\n")
        f.end_session()
        exp = """TEST: description
COMMAND LINE: a b c
INPUT:
1
2
3
TEMPORARY FILE:
x
y
"""
        self.assertEqual(dst.getvalue(), exp)

    def test_errors(self):
        dst = io.StringIO()
        f = TextFormatter(destination=dst,
                          verbosity=TextFormatter.ERROR)
        f.begin_session()

        f.begin_test("description", ["abc"], "1\n", "")
        res = executor.ExecResult(executor.ER_OK, 0, "", "")
        f.execution_result(["prog"], res)
        f.end_test()
        
        f.begin_test("description", ["abc"], "1\n", "")
        res = executor.ExecResult(executor.ER_SEGFAULT, -1, "", "")
        f.execution_result(["prog"], res)
        f.end_test()

        f.begin_test("description", ["abc"], "1\n", "")
        res = executor.ExecResult(executor.ER_TIMEOUT, 0, "", "")
        f.execution_result(["prog"], res)
        f.end_test()

        f.begin_test("description", ["abc"], "1\n", "")
        res = executor.ExecResult(executor.ER_ERROR, 42, "", "")
        f.execution_result(["prog"], res)
        f.end_test()

        f.begin_test("description", ["abc"], "1\n", "")
        res = executor.ExecResult(executor.ER_NOTFILE, 1, "", "")
        f.execution_result(["prog"], res)
        f.end_test()
        
        f.end_session()
        exp = """PROCESS ENDED WITH A FAILURE (SEGMENTATION FAULT)
TIMEOUT EXPIRED: PROCESS TERMINATED
PROCESS ENDED WITH A FAILURE (ERROR CODE 42)
FAILED TO RUN THE FILE 'prog' (the file does not exist)
"""
        self.assertEqual(dst.getvalue(), exp)

    def test_missing_section(self):
        dst = io.StringIO()
        f = TextFormatter(destination=dst,
                          verbosity=TextFormatter.WARNING)
        f.begin_session()

        f.begin_test("description", ["abc"], "1\n", "")
        res = executor.ExecResult(executor.ER_OK, 0, "", "")
        f.execution_result(["prog"], res)
        f.missing_section(Section("NOTEXISTING", []))

        f.end_session()
        exp = "NOTEXISTING: missing section\n"
        self.assertEqual(dst.getvalue(), exp)
        
    def test_comparison1(self):
        dst = io.StringIO()
        f = TextFormatter(destination=dst,
                          verbosity=TextFormatter.WARNING)
        f.begin_session()

        f.begin_test("description", ["abc"], "1\n", "")
        res = executor.ExecResult(executor.ER_OK, 0, "", "")
        f.execution_result(["prog"], res)
        f.comparison_result(
            Section("EXPECTED", ["1", "2"]),
            Section("GOT", ["3", "2", "4"]),
            [1, 0, 1], ["1", "2", None])
        f.end_session()
        exp = """EXPECTED: wrong number of lines (expected 2, got 3)
EXPECTED: line 1 is wrong  (expected '1', got '3')
EXPECTED: unexpected line '4'
"""
        self.assertEqual(dst.getvalue(), exp)

    def test_comparison2(self):
        dst = io.StringIO()
        f = TextFormatter(destination=dst,
                          verbosity=TextFormatter.WARNING,
                          maxerrors=4)
        f.begin_session()

        f.begin_test("description", ["abc"], "1\n", "")
        res = executor.ExecResult(executor.ER_OK, 0, "", "")
        f.execution_result(["prog"], res)
        f.comparison_result(
            Section("EXPECTED", ["1", "2", "3", "4", "5", "6"]),
            Section("GOT", ["6", "1", "2", "3", "4", "5"]),
            [1] * 6, ["1", "2", "3", "4", "5", "6"])
        f.end_session()
        exp = """EXPECTED: line 1 is wrong  (expected '1', got '6')
EXPECTED: line 2 is wrong  (expected '2', got '1')
EXPECTED: line 3 is wrong  (expected '3', got '2')
(... plus other 3 errors ...)
"""
        self.assertEqual(dst.getvalue(), exp)

    def test_comparison3(self):
        dst = io.StringIO()
        f = TextFormatter(destination=dst,
                          verbosity=TextFormatter.WARNING,
                          maxerrors=4)
        f.begin_session()

        f.begin_test("description", ["abc"], "1\n", "")
        res = executor.ExecResult(executor.ER_OK, 0, "", "")
        f.execution_result(["prog"], res)
        f.comparison_result(
            Section("EXPECTED", ["1", "2"]),
            Section("GOT", []),
            [1, 1], ["1", "2"])
        f.end_session()
        exp = """EXPECTED: wrong number of lines (expected 2, got 0)
EXPECTED: missing line (expected '1')
EXPECTED: missing line (expected '2')
"""
        self.assertEqual(dst.getvalue(), exp)

    def test_comparison4(self):
        dst = io.StringIO()
        f = TextFormatter(destination=dst,
                          verbosity=TextFormatter.WARNING,
                          maxerrors=4)
        f.begin_session()

        f.begin_test("description", ["abc"], "1\n", "")
        res = executor.ExecResult(executor.ER_OK, 0, "", "")
        f.execution_result(["prog"], res)
        f.comparison_result(
            Section("EXPECTED", ["1", "2"]),
            Section("GOT", ["2", "3"]),
            [0, 1, 1], ["2", None, "1"])
        f.end_session()
        exp = """EXPECTED: unexpected line '3'
EXPECTED: missing line (expected '1')
"""
        self.assertEqual(dst.getvalue(), exp)


if __name__ == '__main__':
    unittest.main()

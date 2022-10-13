import unittest
import sys
sys.path.insert(0, '../src')
from executor import *


class TestExecutor(unittest.TestCase):
    def test_exec_process1(self):
        r = Executor().exec_process(['echo', 'abc'], '')
        self.assertEqual(r.result, ER_OK)
        self.assertEqual(r.status, 0)
        self.assertEqual(r.output, 'abc\n')

    def test_exec_process2(self):
        r = Executor().exec_process(['cat'], 'test test test\n')
        self.assertEqual(r.result, ER_OK)
        self.assertEqual(r.status, 0)
        self.assertEqual(r.output, 'test test test\n')

    def test_exec_process3(self):
        r = Executor().exec_process(['cat', ARG_TMPFILE], '',
                                    tmpfile='1\n2\n3\n4')
        self.assertEqual(r.result, ER_OK)
        self.assertEqual(r.status, 0)
        self.assertEqual(r.output, '1\n2\n3\n4')

    def test_exec_process4(self):
        r = Executor().exec_process(['sleep', '10'], '', timeout=0.01)
        self.assertEqual(r.result, ER_TIMEOUT)

    def test_exec_process5(self):
        r = Executor().exec_process(['__zzzzz'], '')
        self.assertEqual(r.result, ER_NOTFILE)

    def test_exec_process6(self):
        r = Executor().exec_process(['grep', 'pattern'], '')
        self.assertEqual(r.result, ER_ERROR)
        self.assertNotEqual(r.status, 0)

    def test_exec_process7(self):
        r = Executor().exec_process(['seq', '10'], '', output_limit=5)
        self.assertEqual(r.result, ER_OUTPUT_LIMIT)
        self.assertEqual(r.output, '1\n2\n3\n4\n5\n')
        self.assertEqual(r.status, 0)


if __name__ == '__main__':
    unittest.main()

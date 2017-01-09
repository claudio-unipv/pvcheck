import unittest
import sys
sys.path.insert(0, '../src')
from match import *

class TestOrderedComparisons(unittest.TestCase):
    def test_compare_sections1(self):
        exp = ['a b c d', 'efg hij']
        diffs, matches = compare_sections(['a b c d', 'efg hij'], exp)
        self.assertEqual(diffs, [0.0, 0.0])
        self.assertEqual(matches, ['a b c d', 'efg hij'])

    def test_compare_sections2(self):
        exp = ['a b c d', 'efg hij']
        diffs, matches = compare_sections(['b c a d', 'efg hij'], exp)
        self.assertEqual(diffs, [0.75, 0.0])
        self.assertEqual(matches, ['a b c d', 'efg hij'])

    def test_compare_sections3(self):
        exp = ['a b c d', 'efg hij']
        diffs, matches = compare_sections(['a b c d'], exp)
        self.assertEqual(diffs, [0.0, 1.0])
        self.assertEqual(matches, ['a b c d', 'efg hij'])

    def test_compare_sections4(self):
        exp = ['a b c d', 'efg hij']
        diffs, matches = compare_sections(['efg hij'], exp)
        self.assertEqual(diffs, [1.0, 1.0])
        self.assertEqual(matches, ['a b c d', 'efg hij'])

    def test_compare_sections5(self):
        exp = ['a b c d', 'efg hij']
        diffs, matches = compare_sections(['a b c d', 'efg hij',
                                           'extra'], exp)
        self.assertEqual(diffs, [0.0, 0.0, 1.0])
        self.assertEqual(matches, ['a b c d', 'efg hij', None])

    def test_compare_sections6(self):
        exp = ['a b c d', 'efg hij']
        diffs, matches = compare_sections([], exp)
        self.assertEqual(diffs, [1.0, 1.0])
        self.assertEqual(matches, ['a b c d', 'efg hij'])

    def test_compare_sections7(self):
        diffs, matches = compare_sections(['a b c d', 'efg hij'], [])
        self.assertEqual(diffs, [1.0, 1.0])
        self.assertEqual(matches, [None, None])

    def test_compare_sections7(self):
        diffs, matches = compare_sections([], [])
        self.assertEqual(diffs, [])
        self.assertEqual(matches, [])


class TestUnorderedComparisons(unittest.TestCase):
    def test_compare_sections1(self):
        exp = ['a', 'b', 'c']
        diffs, matches = compare_sections(['a', 'b', 'c'], exp, False)
        self.assertEqual(diffs, [0.0, 0.0, 0.0])
        self.assertEqual(matches, ['a', 'b', 'c'])

    def test_compare_sections2(self):
        exp = ['a', 'b', 'c']
        diffs, matches = compare_sections(['b', 'a', 'c'], exp, False)
        self.assertEqual(diffs, [0.0, 0.0, 0.0])
        self.assertEqual(matches, ['b', 'a', 'c'])

    def test_compare_sections3(self):
        exp = ['a', 'b', 'c']
        diffs, matches = compare_sections(['b', 'c', 'a'], exp, False)
        self.assertEqual(diffs, [0.0, 0.0, 0.0])
        self.assertEqual(matches, ['b', 'c', 'a'])

    def test_compare_sections4(self):
        exp = ['a', 'b', 'c']
        diffs, matches = compare_sections(['a', 'c', 'x'], exp, False)
        self.assertEqual(diffs, [0.0, 0.0, 1.0, 1.0])
        self.assertEqual(matches, ['a', 'c', None, 'b'])

    def test_compare_sections5(self):
        exp = ['a', 'b', 'c']
        diffs, matches = compare_sections(['aa', 'c', 'b'], exp, False)
        self.assertEqual(diffs, [1.0, 0.0, 0.0, 1.0])
        self.assertEqual(matches, [None, 'c', 'b', 'a'])

    def test_compare_sections6(self):
        exp = ['a', 'b', 'c']
        diffs, matches = compare_sections(['x', 'y'], exp, False)
        self.assertEqual(diffs, [1.0, 1.0, 1.0, 1.0, 1.0])
        self.assertEqual(matches, [None, None, 'a', 'b', 'c'])

    def test_compare_sections7(self):
        exp = ['a', 'b', 'c']
        diffs, matches = compare_sections([], exp, False)
        self.assertEqual(diffs, [1.0, 1.0, 1.0])
        self.assertEqual(matches, ['a', 'b', 'c'])

    def test_compare_sections8(self):
        diffs, matches = compare_sections(['x', 'y'], [], False)
        self.assertEqual(diffs, [1.0, 1.0])
        self.assertEqual(matches, [None, None])

    def test_compare_sections9(self):
        diffs, matches = compare_sections([], [], False)
        self.assertEqual(diffs, [])
        self.assertEqual(matches, [])


class TestFieldComparisons(unittest.TestCase):
    def test_compare_text1(self):
        diffs, matches = compare_sections(['  abc\t\tdef '],
                                          ['   abc   def'])
        self.assertEqual(diffs, [0.0])
        self.assertEqual(matches, ['   abc   def'])

    def test_compare_text2(self):
        diffs, matches = compare_sections(['ABC'], ['abc'])
        self.assertEqual(diffs, [1.0])
        self.assertEqual(matches, ['abc'])

    def test_compare_int1(self):
        diffs, matches = compare_sections(['42', '+42', '042'],
                                          ['42', '42', '42'])
        self.assertEqual(diffs, [0.0] * 3)
        self.assertEqual(matches, ['42'] * 3)

    def test_compare_int2(self):
        diffs, matches = compare_sections(['0', '+0', '-0', '00'],
                                          ['0'] * 4)
        self.assertEqual(diffs, [0.0] * 4)
        self.assertEqual(matches, ['0'] * 4)

    def test_compare_float1(self):
        exp = '3. 3.1 3.14 3.141 31.1415'.split()
        diffs, matches = compare_sections(['3.14'] * 5, exp)
        self.assertEqual(diffs, [0.0, 0.0, 0.0, 1.0, 1.0])
        self.assertEqual(matches, exp)

    def test_compare_float2(self):
        diffs, matches = compare_sections(['3.5'], ['+4.'])
        self.assertEqual(diffs, [0.0])
        self.assertEqual(matches, ['+4.'])

    def test_compare_float3(self):
        diffs, matches = compare_sections(['3.4999999'], ['+4.'])
        self.assertEqual(diffs, [1.0])
        self.assertEqual(matches, ['+4.'])

    def test_compare_float4(self):
        diffs, matches = compare_sections(['-3.5'], ['-4.'])
        self.assertEqual(diffs, [0.0])
        self.assertEqual(matches, ['-4.'])

    def test_compare_float5(self):
        diffs, matches = compare_sections(['-3.4999999'], ['-4.'])
        self.assertEqual(diffs, [1.0])
        self.assertEqual(matches, ['-4.'])


if __name__ == '__main__':
    unittest.main()

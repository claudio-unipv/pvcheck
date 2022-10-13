import unittest
import sys
sys.path.insert(0, '../src')
from parser import *


class TestParser(unittest.TestCase):
    def test_parse_section1(self):
        l = list(parse_sections('''[SIMPLE]
line1
line2
'''.splitlines()))
        self.assertEqual(len(l), 1)
        self.assertEqual(l[0].tag, 'SIMPLE')
        self.assertEqual(l[0].content, ['line1', 'line2'])

    def test_parse_section2(self):
        l = list(parse_sections('''[SECTION1]
line1
[SECTION2]
line2
'''.splitlines()))
        self.assertEqual(len(l), 2)
        self.assertEqual(l[0].tag, 'SECTION1')
        self.assertEqual(l[0].content, ['line1'])
        self.assertEqual(l[1].tag, 'SECTION2')
        self.assertEqual(l[1].content, ['line2'])

    def test_parse_section3(self):
        l = list(parse_sections('''line1
line2
line3

[SECTION]
line4
'''.splitlines()))
        self.assertEqual(len(l), 2)
        self.assertEqual(l[0].tag, '')
        self.assertEqual(l[0].content, ['line1', 'line2', 'line3'])
        self.assertEqual(l[1].tag, 'SECTION')
        self.assertEqual(l[1].content, ['line4'])

    def test_parse_section4(self):
        l = list(parse_sections('''
[EMPTY]

'''.splitlines()))
        self.assertEqual(len(l), 1)
        self.assertEqual(l[0].tag, 'EMPTY')
        self.assertEqual(l[0].content, [])

    def test_parse_section_with_hyphens(self):
        l = list(parse_sections('''[GREAT-TEST]
great-test 1
great-test 2

[ANOTHER-BRICK-IN-THE-WALL]
another
brick
in the wall
'''.splitlines()))
        self.assertEqual(len(l), 2)
        self.assertEqual(l[0].tag, 'GREAT-TEST')
        self.assertEqual(l[0].content, ['great-test 1', 'great-test 2'])
        self.assertEqual(l[1].tag, 'ANOTHER-BRICK-IN-THE-WALL')
        self.assertEqual(l[1].content, ['another', 'brick', 'in the wall'])
        

if __name__ == '__main__':
    unittest.main()

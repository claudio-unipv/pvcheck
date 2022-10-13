import unittest
import sys
sys.path.insert(0, '../src')
from testdata import *


class TestSection(unittest.TestCase):
    def test_init(self):
        s = Section('name', ['line1', 'line2'])
        self.assertEqual(s.tag, 'name')
        self.assertEqual(s.content, ['line1', 'line2'])

    def test_copy(self):
        t = Section('name', ['line1', 'line2'])
        s = t.copy()
        self.assertEqual(s.tag, 'name')
        self.assertEqual(s.content, ['line1', 'line2'])


class TestTestCase(unittest.TestCase):
    def test_init(self):
        s = Section('name', ['line1', 'line2'])
        t = TestCase('desc', [s])
        self.assertEqual(t.description, 'desc')
        self.assertEqual(len(t.sections()), 1)
        s2 = t.sections()[0]
        self.assertEqual(s2.tag, 'name')
        self.assertEqual(s.content, s2.content)

    def test_init2(self):
        t = TestCase()
        self.assertIsNone(t.description)
        self.assertEqual(len(t.sections()), 0)

    def test_add_section(self):
        t = TestCase()
        t.add_section(Section('A', ['line1']))
        self.assertEqual(len(t.sections()), 1)
        self.assertEqual(t.sections()[0].tag, 'A')
        t.add_section(Section('A', ['line2']))
        self.assertEqual(len(t.sections()), 1)
        self.assertEqual(t.sections()[0].tag, 'A')
        self.assertEqual(t.sections()[0].content, ['line1', 'line2'])

    def test_find_section(self):
        t = TestCase('desc', [
            Section('A', ['lineA1', 'lineA2']),
            Section('B', ['lineB1', 'lineB2']),
            Section('C', ['lineC1', 'lineC2'])
        ])
        s = t.find_section('B')
        self.assertEqual(s.tag, 'B')
        s = t.find_section('X')
        self.assertIsNone(s)
        cs = t.find_section_content('C')
        self.assertEqual(cs, 'lineC1\nlineC2\n')
        cs = t.find_section_content('Y', 'foo')
        self.assertEqual(cs, 'foo')
        
    def test_special(self):
        t = TestCase('desc', [
            Section('.A', ['lineA1', 'lineA2']),
            Section('B', ['lineB1', 'lineB2']),
            Section('.C', ['lineC1', 'lineC2'])
        ])
        ss = t.sections(exclude_special=False)
        self.assertEqual(len(ss), 3)
        ss = t.sections(exclude_special=True)
        self.assertEqual(len(ss), 1)
        self.assertEqual(ss[0].tag, 'B')

    def test_options(self):
        t = TestCase('desc', [
            Section('A', ['lineA1', 'lineA2']),
            Section('.SECTIONS', ['A a b c', 'B xx yy']),
            Section('B', ['lineB1', 'lineB2']),
            Section('C', ['lineC1', 'lineC2'])
        ])
        opts = t.section_options('A')
        self.assertEqual(opts, set(['a', 'b', 'c']))
        opts = t.section_options('B')
        self.assertEqual(opts, set(['xx', 'yy']))
        opts = t.section_options('C')
        self.assertEqual(opts, set())
        opts = t.section_options('X')
        self.assertEqual(opts, set())


class TestTestSuite(unittest.TestCase):
    def test_test_cases(self):
        suite = TestSuite()
        tc = suite.test_cases()
        self.assertEqual(len(tc), 1)
        self.assertIsNone(tc[0].description)
        self.assertEqual(len(tc[0].sections()), 0)

    def test_test_cases2(self):
        suite = TestSuite([Section('name', ['line1', 'line2'])])
        tc = suite.test_cases()
        self.assertEqual(len(tc), 1)
        self.assertIsNone(tc[0].description)
        self.assertEqual(len(tc[0].sections()), 1)
        
    def test_test_cases3(self):
        suite = TestSuite([Section('.TEST', ['test1']),
                           Section('AAA', ['line1', 'line2']),
   		           Section('BBB', ['line3'])
        ])
        tc = suite.test_cases()
        self.assertEqual(len(tc), 1)
        self.assertEqual(tc[0].description, 'test1')
        self.assertEqual(len(tc[0].sections()), 2)
        self.assertEqual(tc[0].sections()[0].tag, 'AAA')
        self.assertEqual(tc[0].sections()[1].tag, 'BBB')

    def test_test_cases4(self):
        suite = TestSuite([
            Section('AAA', ['pre1', 'pre2', 'pre3']),
  	    Section('.TEST', ['test1']),
            Section('AAA', ['line1', 'line2']),
   	    Section('BBB', ['line3']),
  	    Section('.TEST', ['test2']),
   	    Section('BBB', ['line4'])
        ])
        tc = suite.test_cases()
        self.assertEqual(len(tc), 2)

        self.assertEqual(tc[0].description, 'test1')
        self.assertEqual(len(tc[0].sections()), 2)
        self.assertEqual(tc[0].sections()[0].tag, 'AAA')
        self.assertEqual(tc[0].sections()[0].content,
                         ['pre1', 'pre2', 'pre3', 'line1', 'line2'])
        self.assertEqual(tc[0].sections()[1].tag, 'BBB')
        
        self.assertEqual(tc[1].description, 'test2')
        self.assertEqual(len(tc[1].sections()), 2)
        self.assertEqual(tc[1].sections()[0].tag, 'AAA')
        self.assertEqual(tc[1].sections()[0].content,
                         ['pre1', 'pre2', 'pre3'])
        self.assertEqual(tc[1].sections()[1].tag, 'BBB')


if __name__ == '__main__':
    unittest.main()

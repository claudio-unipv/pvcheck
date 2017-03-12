import unittest
from src.csvformatter import CSVFormatter


class Expected:
    def __init__(self, nome):
        self.tag = nome


class TestCSVFormatter(unittest.TestCase):
    def setUp(self):
        self.csv = CSVFormatter()
        self.expected1 = Expected('section1')
        self.expected2 = Expected('section2')

    def test(self):
        self.csv.begin_session()
        self.csv.begin_test('Test1', "not_used", "not_used", "not_used")
        self.csv.execution_result("not_used", "not_used")
        self.csv.comparison_result(self.expected1, "not_used", [0, 0], "not_used")
        self.csv.begin_test('Test2', "not_used", "not_used", "not_used")
        self.csv.execution_result("not_used", "not_used")
        self.csv.comparison_result(self.expected2, "not_used", [10, 90], "not_used")
        self.csv.end_session()


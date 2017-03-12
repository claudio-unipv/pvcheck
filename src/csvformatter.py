"""Formatter producing CSV data."""

import sys
import csv
from collections import OrderedDict
from src import formatter, executor

# TO BE DEFINED
# - wrong lines
# - return_code/code/section status
# - difference/similarity


class CSVFormatter(formatter.Formatter):
    _RESULT_TABLE = {
        executor.ER_OK: "ok",
        executor.ER_TIMEOUT: "TIMEOUT EXPIRED: PROCESS TERMINATED",
        executor.ER_SEGFAULT:
            "PROCESS ENDED WITH A FAILURE (SEGMENTATION FAULT)",
        executor.ER_ERROR:
            "PROCESS ENDED WITH A FAILURE (ERROR CODE {status})",
        executor.ER_NOTFILE:
            "FAILED TO RUN THE FILE '{progname}' (the file does not exist)"
    }

    def __init__(self, destination=sys.stdout):
        self._dest = destination
        self._obj = None
        self.section_number = 0
        self._tests = []

    def _proc_args(self, args):
        return [(a if a is not executor.ARG_TMPFILE
                 else "<temp.file>")
                for a in args]

    def begin_session(self):
        self._tests = []

    def _header_builder(self):
        header = ["Test"]
        section_names = list(self._tests[0]["sections"].keys())
        for name in section_names:
            header.append(name)
        return header

    def _row_builder(self, test, header):
        row = [test["title"]]
        for head in header:
            if head != 'Test':
                try:
                    row.append(test["sections"][head]["similar"])
                except KeyError:
                    row.append("missing")
        return row

    def end_session(self):
        header = self._header_builder()
        fp = csv.writer(self._dest)
        fp.writerow(header)
        for test in self._tests:
            row = self._row_builder(test, header)
            fp.writerow(row)

    def begin_test(self, description, cmdline_args, input, tempfile):
        self.section_number = 0
        t = OrderedDict([
            ("title", description.replace('\n', ' '))
        ])
        self._tests.append(t)

    def execution_result(self, cmdline_args, execution_result):
        t = self._tests[-1]
        self._sections = OrderedDict()
        t["sections"] = self._sections

    def comparison_result(self, expected, got, diffs, matches):

            s = OrderedDict([
                ("similar", 100 - sum(diffs)),
                ("number", self.section_number)
            ])
            self.section_number += 1
            self._sections[expected.tag] = s

    def missing_section(self, expected):
            s = OrderedDict([("section status", "missing")])
            self._sections["expected.tag"] = s

"""Formatter producing CSV data."""

import sys
import csv
from collections import OrderedDict
import formatter
import executor

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
        self._tests = []

    def _proc_args(self, args):
        return [(a if a is not executor.ARG_TMPFILE
                 else "<temp.file>")
                for a in args]

    def begin_session(self):
        self._tests = []

    def _header_builder(self):
        """Build the header.

        If there is only a test omits the header 'TEST'.

        """
        if len(self._tests) > 1:
            header = ["TEST"]
        else:
            header = []
        for test in self._tests:
            section_names = list(test["sections"].keys())
            for name in section_names:
                if name not in header:
                    header.append(name)
        return header

    def _row_builder(self, test, header):
        """Build a row.

        If there is only a test omits the test's name.

        """
        if len(self._tests) > 1:
            row = [test["title"]]
        else:
            row = []
        for element in header:
            if element != "TEST":
                try:
                    row.append(test["sections"][element]["equality"])
                except KeyError:
                    row.append("MISS")
        return row

    def _statistics_row_builder(self, header):
        """Build a row containing the arithmetic mean of equality for each section."""
        row = ['TOTAL']
        for head in header:
            if head != "TEST":
                values = []
                for test in self._tests:
                    if test["sections"][head]["equality"] != 'MISS':
                        values.append(float(test["sections"][head]["equality"]))
                try:
                    row.append('%.2f' % (sum(values)/len(values)))
                except ZeroDivisionError:
                    row.append('%.2f' % 0)
        return row

    def end_session(self):
        header = self._header_builder()
        fp = csv.writer(self._dest)
        fp.writerow(header)
        for test in self._tests:
            row = self._row_builder(test, header)
            fp.writerow(row)
        if len(self._tests) > 1:
            fp.writerow(self._statistics_row_builder(header))

    def begin_test(self, description, cmdline_args, input, tempfile):
        t = OrderedDict([
            ("title", description)
        ])
        self._tests.append(t)

    def execution_result(self, cmdline_args, execution_result):
        if execution_result.result != executor.ER_OK:
            info = {
                "progname": cmdline_args[0],
                "status": execution_result.status
            }
            msg = self._RESULT_TABLE[execution_result.result]
            print(msg.format(**info))
        t = self._tests[-1]
        self._sections = OrderedDict()
        t["sections"] = self._sections

    def comparison_result(self, expected, got, diffs, matches):
        percent_correct = '%.2f' % (((len(diffs) - sum(diffs)) * 100)/len(diffs))
        s = OrderedDict([
            ("equality", percent_correct)
        ])
        self._sections[expected.tag] = s

    def missing_section(self, expected):
        s = OrderedDict([("equality", "MISS")])
        self._sections[expected.tag] = s

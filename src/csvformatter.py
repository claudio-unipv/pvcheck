"""Formatter producing CSV data."""

import sys
import csv
from collections import OrderedDict
import formatter
import executor
from i18n import translate as _

# TO BE DEFINED
# - wrong lines
# - return_code/code/section status
# - difference/similarity


class CSVFormatter(formatter.Formatter):
    _RESULT_TABLE = {
        executor.ER_OK: "0",
        executor.ER_TIMEOUT: "1",
        executor.ER_SEGFAULT:
        "2",
        executor.ER_ERROR:
        "3",
        executor.ER_NOTFILE:
        "4"
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
        header.append(_("CODE"))
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
            if element == _("CODE"):
                row.append(test["status"])
            elif element != "TEST":
                try:
                    row.append(test["sections"][element]["equality"])
                except KeyError:
                    row.append("")
        return row

    def _statistics_row_builder(self, header):
        """Build a row containing the arithmetic mean of equality for each section."""
        row = [_("TOTAL"), ""]
        for head in header:
            if head not in ("TEST", _("CODE")):
                values = []
                for test in self._tests:
                    try:
                        if test["sections"][head]["equality"] != 'MISS':
                            values.append(float(test["sections"][head]["equality"]))
                        else:
                            values.append(0)
                    except KeyError:
                        values.append(None)
                try:
                    # takes into account the sections that actually exist
                    values_2 = [v for v in values if v is not None]
                    row.append('%.2f' % (sum(values_2)/len(values_2)))
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
        t = self._tests[-1]
        self._sections = OrderedDict()
        t["status"] = self._RESULT_TABLE[execution_result.result]
        t["sections"] = self._sections

    def comparison_result(self, expected, got, diffs, matches):
        if len(diffs) != 0:
            percent_correct = '%.2f' % (((len(diffs) - sum(diffs)) * 100)/len(diffs))
        else:
            percent_correct = '100.00'
        s = OrderedDict([
            ("equality", percent_correct)
        ])
        self._sections[expected.tag] = s

    def missing_section(self, expected):
        s = OrderedDict([("equality", "MISS")])
        self._sections[expected.tag] = s

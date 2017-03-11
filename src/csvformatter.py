"""Formatter producing CSV data."""

import sys
import datetime
import csv
from collections import OrderedDict
from itertools import zip_longest
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

    def __init__(self, destination=sys.stdout, indent=None):
        self._dest = destination
        self._indent = indent
        self._obj = None
        self._tests = []

    def _proc_args(self, args):
        return [(a if a is not executor.ARG_TMPFILE
                 else "<temp.file>")
                for a in args]

    def begin_session(self):
        self._tests = []

    def end_session(self):
        fp = csv.DictWriter(self._dest, self._tests[0].keys(), dialect='unix')
        fp.writeheader()
        for element in self._tests:
            fp.writerow(element)

    def begin_test(self, description, cmdline_args, input, tempfile):
        t = OrderedDict([
            ("title", description.replace('\n', ' ')),
            ("command_line", self._proc_args(cmdline_args)),
            ("input_text", input.replace('\n', ' ')),
            ("file_text", tempfile),
            ("input_file_name",  # not available here
             (None if tempfile is None else "<temp.file>"))
        ])
        self._tests.append(t)

    def execution_result(self, cmdline_args, execution_result):
        t = self._tests[-1]
        info = {
            "progname": cmdline_args[0],
            "status": execution_result.status
        }
        msg = self._RESULT_TABLE[execution_result.result]
        t["return_code"] = execution_result.status
        t["error_message"] = msg.format(**info).replace('\n', ' ')
        t["output"] = execution_result.output.replace('\n', ' ')

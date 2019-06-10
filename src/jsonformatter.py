"""Formatter producing JSON data."""
import os
import sys
import json
import datetime
from collections import OrderedDict
from itertools import zip_longest
import formatter
import executor


JSON_FORMAT_VER = "2.1.0"


# TO BE DEFINED
# - wrong lines
# - return_code/code/section status
# - difference/similarity


class JSONFormatter(formatter.Formatter):
    _RESULT_TABLE = {
        executor.ER_OK: "ok",
        executor.ER_TIMEOUT: "TIMEOUT EXPIRED: PROCESS TERMINATED",
        executor.ER_OUTPUT_LIMIT: "TOO MANY OUTPUT LINES",
        executor.ER_SEGFAULT:
        "PROCESS ENDED WITH A FAILURE (SEGMENTATION FAULT)",
        executor.ER_ERROR:
        "PROCESS ENDED WITH A FAILURE (ERROR CODE {status})",
        executor.ER_NOTFILE:
        "FAILED TO RUN THE FILE '{progname}' (the file does not exist)"
    }

    def __init__(self, destination=sys.stdout, indent=None, test_file=None):
        self._dest = destination
        self._indent = indent
        self._obj = None
        self._tests = []
        self._work_dir = os.getcwd()
        self._test_file = self._work_dir
        if test_file is not None:
            self._test_file += "/" + test_file
        else:
            self._test_file += "/pvcheck.test"

    def _now(self):
        now = datetime.datetime.now()
        (dt, micro) = now.strftime("%Y-%m-%d %H:%M:%S.%f").split(".")
        return "%s.%03d" % (dt, int(micro) / 1000)

    def _proc_args(self, args):
        return [(a if a is not executor.ARG_TMPFILE
                 else "<temp.file>")
                for a in args]
    
    def begin_session(self):
        self._tests = []
        self._obj = OrderedDict([
            ("created_at", self._now()),
            ("version", JSON_FORMAT_VER),
            ("working_directory", self._work_dir),
            ("test_file", self._test_file),
            ("tests", self._tests)
        ])

    def end_session(self):
        json.dump(self._obj, self._dest, indent=self._indent)

    def begin_test(self, description, cmdline_args, input, tempfile):
        t = OrderedDict([
            ("title", description),
            ("command_line", self._proc_args(cmdline_args)),
            ("input_text", input),
            ("file_text", tempfile),
            ("input_file_name",      # not available here
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
        t["error_message"] = msg.format(**info)
        t["output"] = execution_result.output
        self._sections = OrderedDict()
        t["sections"] = self._sections

    def comparison_result(self, expected, got, diffs, matches):
        status = ("ok" if max(diffs, default=0) == 0
                  else "error")   # ???

        wrong = [(n, a, b) for (n, a, b, d)
                 in zip_longest(range(len(diffs)), got.content,
                                matches, diffs)
                 if d > 0]
            
        s = OrderedDict([
            ("section status", status),
            ("expected", expected.content),
            ("generated", got.content),
            ("wrong_lines", wrong),
	    ("difference", sum(diffs))
        ])
        self._sections[expected.tag] = s
        
    def missing_section(self, expected):
        s = OrderedDict([("section status", "missing")])
        self._sections[expected.tag] = s

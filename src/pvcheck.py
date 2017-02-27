"""Main PvCheck class."""

import os
import json
import datetime

import match
import parser
import executor
from i18n import translate as _


class PvCheck:
    """Main class that runs the tests."""

    def __init__(self, executor, formatter):
        self._exec = executor
        self._fmt = formatter

    def exec_suite(self, suite, args, timeout=None):
        """Verify the program with a collection of test cases."""
        self._fmt.begin_session()
        try:
            for test in suite.test_cases():
                self._exec_test(test, args, timeout=timeout)
        finally:
            self._fmt.end_session()

    def exec_single_test(self, test, args, timeout=None):
        """Verify the program on a single test case."""
        self._fmt.begin_session()
        try:
            self._exec_test(test, args, timeout=None)
        finally:
            self._fmt.end_session()

    def _exec_test(self, test, args, timeout=None):
        """Run the program and verify it according to the test case."""
        input = test.find_section_content(".INPUT", "")
        tmpfile = test.find_section_content(".FILE", None)
        args = list(args)
        arg_sect = test.find_section(".ARGS")
        if arg_sect is not None:
            args.extend(map(str.strip, arg_sect.content))
            if tmpfile is not None:
                args = [(a if a != ".FILE" else executor.ARG_TMPFILE)
                        for a in args]

        self._fmt.begin_test(test.description, args, input, tmpfile)

        exec_result = self._exec.exec_process(
            args, input, tmpfile=tmpfile,
            timeout=timeout
        )
        self._fmt.execution_result(args, exec_result)
        if exec_result.result == executor.ER_OK:
            self._check_output(test, exec_result.output)

    def _check_output(self, test, output):
        answers = list(parser.parse_sections(output.splitlines()))
        for s in test.sections(exclude_special=True):
            for ans in answers:
                if ans.tag != s.tag:
                    continue
                ordered = ("unordered" not in test.section_options(s.tag))
                diffs, matches = match.compare_sections(
                    ans.content, s.content, ordered=ordered
                )
                self._fmt.comparison_result(s, ans, diffs,
                                            matches)
                break
            else:
                self._fmt.missing_section(s)

"""Main PvCheck class."""

import os
import json
import datetime

import pvcheck.match
import pvcheck.parser
import pvcheck.executor
from pvcheck.i18n import translate as _


class PvCheck:
    """Main class that runs the tests."""

    def __init__(self, executor, formatter):
        self._exec = executor
        self._fmt = formatter

    def exec_suite(self, suite, args, timeout=None, output_limit=None):
        """Verify the program with a collection of test cases.

        Return the number of failed tests.
        """
        self._fmt.begin_session()
        failures = 0
        try:
            for test in suite.test_cases():
                if not self._exec_test(test, args, timeout=timeout,
                                       output_limit=output_limit):
                    failures += 1
                self._fmt.end_test()
        finally:
            self._fmt.end_session()
        return failures

    def exec_single_test(self, test, args, timeout=None, output_limit=None):
        """Verify the program on a single test case.

        Return True if the test has been successfully passed.
        """
        self._fmt.begin_session()
        success = False
        try:
            success = self._exec_test(test, args, timeout=timeout,
                                      output_limit=output_limit)
        finally:
            self._fmt.end_test()
            self._fmt.end_session()
        return success

    def _exec_test(self, test, args, timeout=None, output_limit=None):
        # Run the program and verify it according to the test case.
        # Return True if the test is successful.
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
            timeout=timeout,
            output_limit=output_limit
        )
        self._fmt.execution_result(args, exec_result, test)
        if exec_result.result == pvcheck.executor.ER_OK:
            return self._check_output(test, exec_result.output)
        else:
            return False

    def _check_output(self, test, output):
        # Return True if the test has been passed.
        success = True
        answers = list(pvcheck.parser.parse_sections(output.splitlines()))
        for s in test.sections(exclude_special=True):
            for ans in answers:
                if ans.tag != s.tag:
                    continue
                ordered = ("unordered" not in test.section_options(s.tag))
                diffs, matches = pvcheck.match.compare_sections(
                    ans.content, s.content, ordered=ordered
                )
                self._fmt.comparison_result(s, ans, diffs,
                                            matches)
                success = success and (max(diffs, default=0.0) == 0)
                break
            else:
                success = False
                self._fmt.missing_section(s)
        return success

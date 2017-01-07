"""Main PvCheck class."""

import subprocess
import signal
import os
import sys
import logging
import tempfile
import json
from itertools import count, zip_longest
from collections import Counter, defaultdict
import datetime

import match
import parser
import testdata
import executor
from i18n import translate as _


class PvCheck:
    """Main class that runs the tests."""

    def __init__(self, formatter):
        self._fmt = formatter

    def exec_suite(self, suite, args, timeout=None):
        """Verify the program with a collection of test cases."""
        for test in suite.test_cases():
            self.exec_test(test, args, timeout=timeout)

    def exec_test(self, test, args, timeout=None):
        """Run the program and verify it according to the test case."""
        input = test.find_section_content(".INPUT", "")
        tmpfile = test.find_section_content(".FILE", None)
        args = list(args)
        arg_sect = test.find_section(".ARGS")
        if arg_sect is not None:
            args.extend(map(str.strip, arg_sect.content))

        self._fmt.begin_test(test.description, args, input, tmpfile)
        
        exec_result = executor.exec_process(
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
                    ans.content, s.content, ordered = ordered
                )
                self._fmt.comparison_result(s, ans, diffs,
                                            matches)
                break
            else:
                self._fmt.missing_section(s)




############################################################
# DRIVER
############################################################
def ________bah():   ## !!!!


    # Check the result
    if error_message is None:
        check_res_out = check_result(result, target, flags,
                               opts['maxerrors'])
        summary = check_res_out['summary']
        summary[_("<program>")] = max(summary.values(),
                                      default=ResultType.SUCCESS)
    else:
        check_res_out = {}
        summary = {_("<program>"): ResultType.FATAL }

    outDict = {
        'summary': summary,
        'error_message': error_message,
        'input_text': input_text,
        'file_text': file_text,
        'output': output,
    }
    outDict.update(check_res_out)

    if opts['valgrind']:
        (verr, vwarn) = parse_valgrind(valgrind_report)
        if verr > 0:
            summary[_("<valgrind>")] = ResultType.ERROR
        elif vwarn > 0:
            summary[_("<valgrind>")] = ResultType.WARNING
        else:
            summary[_("<valgrind>")] = ResultType.SUCCESS
        outDict['valgrind'] = {'errors': verr, 'warnings': vwarn}

    if tmpfile is not None:
        outDict['input_file_name'] = tmpfile.name
    else:
        outDict['input_file_name'] = args[2] if len(args) > 2 else ""

    return outDict


def print_final_summary(tests):
    summary = defaultdict(Counter)
    for test in tests:
        results = test['summary']
        for sec in results:
            summary[sec][results[sec]] += 1

    log.info('')
    log.info("=" * 60)
    log.info('')
    log.info(_("SUMMARY"))
    for k in sorted(summary):
        errs = (summary[k][ResultType.ERROR] +
                summary[k][ResultType.FATAL])
        fmt = "%s:  \t%d %s,\t%d %s,\t %d %s"
        a = [k]
        a += [summary[k][ResultType.SUCCESS], _("successes")]
        a += [summary[k][ResultType.WARNING], _("warnings")]
        a += [errs, _("errors")]
        log.info(fmt % tuple(a))
    log.info('')


def print_resume(all_tests, args, opts):
    """ Print the resume."""
    for i, test in enumerate(all_tests):
        if i > 0:
            log.info('-' * 60)
        error_message = test['error_message']
        input_text = test['input_text']
        file_text = test['file_text']
        output = test['output']

        print_header(test['title'], error_message, test['input_file_name'], args)
        print_lines(input_text, file_text, output, opts)

        if error_message is not None:
            continue

        sections = test['sections']
        for key, sect in sections.items():
            if sect['section status'] == 'ok':
                if sect['code'] == ResultType.SUCCESS:
                    log.success(_("OK"), extra={'section':key})
                else:
                    print_resume_ordered_check(key, sect['generated'], sect['expected'], maxerrors=None)
            elif sect['section status'] == 'missing':
                log.warning(_("missing section"), extra={'section':key})
            elif sect['section status'] == 'empty':
                log.error(_("empty section"), extra={'section':key})
            else:
                log.error(_("Internal Error: wrong section status"), extra={'section':key})

    # In the case of multiple tests print a summary
    if len(all_tests) > 1:
        print_final_summary(all_tests)


def main():
       
    #### !!!!! TO BE CONTINUED ...

    all_tests = []
    # Run the individual tests in the suite
    for i, (testname, target) in enumerate(tests):
        dotest_out = dotest(testname, target, args, opts)
        dotest_out['title'] = testname
        all_tests.append(dotest_out)

    global_out = {}

    global_out['tests'] = all_tests
    (dt, micro) = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f').split('.')
    dt = "%s.%03d" % (dt, int(micro) / 1000)
    global_out['created_at'] = dt
    global_out['version'] = JSON_FORMAT_VER
    if opts['output'] == 'RESUME':
        print_resume(all_tests, args, opts)
    elif opts['output'] == 'JSON':
        s = json.dumps(global_out)
        print(s)

    # TODO: add option or config file to configure this logging feature
    home = os.path.expanduser("~")
    with open(home + "/.pvcheck.log", "a") as logfile:
        logfile.write(json.dumps(global_out) + '\n')

if __name__ == '__main__':
    main()

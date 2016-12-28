#!/usr/bin/env python3

import subprocess
import signal
import os
import sys
import getopt
import logging
import tempfile
import json
from itertools import count, zip_longest
from collections import OrderedDict, Counter, defaultdict
from functools import wraps
import datetime

import match
import parser
import testdata
import i18n

__doc__ = i18n.HELP_en

_ = i18n.translate

JSON_FORMAT_VER = '2.0.0'


############################################################
# FORMATTED OUTPUT
############################################################

# Install a new logging level named "SUCCESS"
SUCCESS = logging.INFO-1
logging.addLevelName(SUCCESS, "SUCCESS")
def success(self, message, *args, **kws):
    # Yes, logger takes its '*args' as 'args'.
    if self.isEnabledFor(SUCCESS):
        self._log(SUCCESS, message, args, **kws)
logging.Logger.success = success
log = logging.getLogger()

# Enable colored output for the logger
class ColorLog(logging.Formatter):
    """Format log messages.

    Allow colored output and optionally print a section name in front
    of the message.

    """

    BLUE = '\033[94m'
    DARK_BLUE = '\033[34m'
    YELLOW = '\033[93m'
    DARK_YELLOW = '\033[33m'
    GREEN = '\033[92m'
    DARK_GREEN = '\033[92m'
    RED = '\033[91m'
    DARK_RED = '\033[91m'
    GRAY = '\033[97m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

    COLORS = {
        logging.FATAL: BOLD+DARK_RED,
        logging.ERROR: BOLD+RED,
        logging.WARNING: BOLD+DARK_YELLOW,
        logging.INFO: "",
        SUCCESS: BOLD+DARK_GREEN,
        logging.DEBUG: BLUE,
        logging.NOTSET: ""
    }

    def __init__(self, color):
        if color:
            self._format = self.colored_format
        else:
            self._format = self.simple_format

    def format(self, record):
        return self._format(record)

    def simple_format(self, record):
        if hasattr(record, "section"):
            return ("%s: %s" % (record.section, record.msg))
        else:
            return record.msg

    def colored_format(self, record):
        msg = record.msg
        idx = min(x for x in self.COLORS if x >= record.levelno)
        if hasattr(record, "section"):
            return ("%s%s: %s%s" % (self.COLORS[idx], record.section,
                                    msg, self.ENDC))
        else:
            return ("%s%s%s" % (self.COLORS[idx], msg, self.ENDC))


def setup_logging(level, color):
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(ColorLog(color))
    log.addHandler(ch)
    log.setLevel(level)


class ResultType:
    """Possible results for individual and combined tests."""
    SUCCESS = 0
    WARNING = 1
    ERROR = 2
    FATAL = 3

    TYPES = list(range(FATAL+1))

    _TXT = [_(s) for s in "OK WARNING! ERROR ERROR".split()]

    @staticmethod
    def tostr(i):
        """String representation of an error type."""
        return ResultType._TXT[i]



def interpret_section_flags(lines):
    """Interpret the sequence lines as flags related to sections.

    [ lines ] -> { secname: [flags] }
    """
    flags = {}
    for line in lines:
        toks = line.split()
        if toks:
            flags.setdefault(toks[0], []).extend(toks[1:])
    return flags


############################################################
# MATCHING
############################################################


def check_result(result, target, flags, maxerrors=None):
    """Compare result against the target output.

    Print messages to show matches and mismatches.  Return a summary
    of the results obtained for each section.

    """
    summary = {}
    res = {}
    check_data = {}
    for (name, content) in result:
        res.setdefault(name, []).extend(content)

    for (key, t) in target:
        if key.startswith('.'):
            continue  # skip special sessions
        check_data[key] = {}
        try:
            r = res[key]
        except KeyError:
            summary[key] = ResultType.WARNING
            check_data[key]['section status'] = 'missing'
            continue
        if not r and t:
            summary[key] = ResultType.ERROR
            check_data[key]['section status'] = 'empty'
            continue
        check_data[key]['section status'] = 'ok'

        ordered = ("unordered" not in flags.get(key, ()))
        diffs, matches = match.compare_sections(r, t, ordered)
        
        ### !!!! To be fixed

        secresult = (ResultType.SUCCESS if max(diffs) == 0
                     else ResultType.ERROR)

        sym = float(len(diffs) - sum(diffs)) / max(len(diffs), 1)
        wrong = [(i, rr, tt) for (i, d, rr, tt) in
                 zip(count(), diffs, r, matches) if d > 0]
        out = {
            'code': secresult
            'wrong lines': wrong,
            'generated': r,
            'expected': t,
            'similarity': sym
        }
        
        check_data[key].update(out)
        summary[key] = secresult

    extra = set(x[0] for x in result) - set(x[0] for x in target)
    for item in extra:
        log.debug(_("extra section"), extra={'section':item[0]})
    check_data[key]['extra'] = list(extra)
    check_dict = {
        'summary': summary,
        'sections': check_data
    }
    return check_dict


############################################################
# DRIVER
############################################################

def parse_options():
    """Parse the command line."""

    shortopts = "hc:t:v:m:C:Vo:"
    longopts = ["help", "config=", "timeout=", "verbosity=",
                "max-errors=", "color=", "valgrind", "output="]
    try:
        opts, args = getopt.getopt(sys.argv[1:], shortopts, longopts)
    except getopt.GetoptError as err:
        print(str(err))
        print(_(i18n.USAGE_en))
        sys.exit(2)
    opts = dict(opts)

    if '-h' in opts or '--help' in opts:
        print(_(i18n.USAGE_en))
        print()
        print(_(i18n.HELP_en))
        sys.exit(0)

    if len(args) < 2:
        print(_(i18n.USAGE_en))
        sys.exit(2)

    def optval(key1, key2, default=None, result_type=None):
        x = opts.get(key1, opts.get(key2, default))
        if result_type is None:
            return x
        try:
            return result_type(x)
        except ValueError as err:
            print(_("Invalid parameter ('%s')") % x)
            sys.exit(2)

    verbosity = optval('-v', '--verbosity', '3', int)
    if verbosity < 0 or verbosity > 4:
        print(_("Invalid parameter ('%d')") % verbosity)
        sys.exit(2)

    timeout = optval('-t', '--timeout', '10', float)
    if timeout < 0:
        print(_("Invalid parameter ('%f')") % timeout)
        sys.exit(2)

    maxerrors = optval('-m', '--max-errors', '4', int)
    if maxerrors < 0:
        print(_("Invalid parameter ('%d')") % maxerrors)
        sys.exit(2)

    config = optval('-c', '--config', '', str)

    color = optval('-C', '--color', 'AUTO', str).upper()
    if color not in ("YES", "NO", "AUTO"):
        print(_("Invalid parameter ('%s')") % color)
        sys.exit(2)
    color = (color == "YES" or (color == "AUTO" and sys.stdout.isatty()))

    output = optval('-o', '--output', 'resume', str).upper()
    if output not in ("RESUME", "JSON"):
        print(_("Invalid parameter ('%s')") % output)
        sys.exit(2)

    valgrind = (True if '-V' in opts or '--valgrind' in opts else False)
    opts = dict(config=config,
                verbosity=verbosity,
                timeout=timeout,
                maxerrors=maxerrors,
                color=color,
                valgrind=valgrind,
                output=output
                )

    return (args, opts)


def parse_valgrind(report):
    """Analyse the report by Valgrind and log the result."""
    warnings = 0
    errors = 0
    for line in report:
        if not line.startswith('=='):
            continue
        f = line.split()
        if "in use at exit" in line:
            bytes_ = int(f[5].replace(',', ''))
            if bytes_ > 0:
                log.warning("VALGRIND: memory %s" % " ".join(f[1:]))
                warnings += 1
            else:
                log.debug("VALGRIND: memory %s" % " ".join(f[1:]))
        elif "total heap usage" in line:
            allocs = int(f[4].replace(',', ''))
            frees = int(f[6].replace(',', ''))
            if allocs != frees:
                log.warning("VALGRIND: %s" % " ".join(f[1:]))
                warnings += 1
            else:
                log.debug("VALGRIND: %s" % " ".join(f[1:]))

        elif "ERROR SUMMARY" in line:
            errs = int(f[3].replace(',', ''))
            if errs > 0:
                log.error("VALGRIND: %s" % " ".join(f[3:]))
                errors += errs
            else:
                log.debug("VALGRIND: %s" % " ".join(f[3:]))
    return (errors, warnings)


def log_lines(header, lines, max_lines=None):
    """Log each line after the header.

    Only the first max_lines lines will be logged (when the parameter
    is given).

    """
    if max_lines is None:
        max_lines = len(lines)
    if len(lines) == 1:
        log.info(header + ": " + lines[0])
    else:
        log.info(header + ":")
        for line in lines[:max_lines]:
            log.info(line)
        if len(lines) > max_lines:
            extra = len(lines) - max_lines
            log.info(_("(... plus other %d lines ...)") % extra)


def exist_section(sections, name):
    """Check if a section exists."""
    for (secname, lines) in sections:
        if secname == name:
            return True
    return False


def dotest(testname, target, args, opts):
    """Execute the process and verify its output against target."""

    if exist_section(target, ".INPUT"):
        input_text = ("".join(group_sections_by_name(target, ".INPUT")))
        input_bytes = input_text.encode('utf8')
    else:
        input_text = None
        input_bytes = bytes()

    if exist_section(target, ".FILE"):
        file_text = ("".join(group_sections_by_name(target, ".FILE")))
        tmpfile = tempfile.NamedTemporaryFile(suffix=".pvcheck.tmp",
                                              delete=False)
        tmpfile.write(file_text.encode('utf8'))
        tmpfile.close()
    else:
        file_text = None
        tmpfile = None

    args = args[:]
    extra = map(str.strip, group_sections_by_name(target, ".ARGS"))
    args.extend(extra)
    if tmpfile is not None:
        args = [(a if a != ".FILE" else tmpfile.name) for a in args]

    flags = interpret_section_flags(group_sections_by_name(target, ".SECTIONS"))

    kwargs = dict(input=input_bytes,
                  timeout=opts['timeout'])

    if opts['valgrind']:
        args.insert(1, "valgrind")
        valgrind_out = tempfile.NamedTemporaryFile(suffix=".pvcheck.valgrind",
                                                   delete=False)
        kwargs['stderr'] = valgrind_out
    else:
        valgrind_out = None

    # Execute the process and parse its output
    error_message = None
    try:
        output = subprocess.check_output(args[1:], **kwargs)
    except subprocess.TimeoutExpired as e:
        error_message = _("TIMEOUT EXPIRED: PROCESS TERMINATED")
        output = e.output
    except subprocess.CalledProcessError as e:
        if e.returncode == -signal.SIGSEGV:
            error_message = _("PROCESS ENDED WITH A FAILURE")
            error_message += " " + _("(SEGMENTATION FAULT)")
        else:
            error_message = _("PROCESS ENDED WITH A FAILURE")
            error_message += " " + _("(ERROR CODE %d)") % e.returncode
        output = e.output
    except FileNotFoundError:
        output = bytes()
        error_message = _("FAILED TO RUN THE FILE '%s' ") % sys.argv[2]
        error_message += _("(the file does not exist)")

    if tmpfile is not None:
        os.remove(tmpfile.name)

    if valgrind_out is not None:
        valgrind_out.close()
        with open(valgrind_out.name, "rt") as f:
            valgrind_report = [x for x in f]
        os.remove(valgrind_out.name)
    else:
        valgrind_report = []

    output = output.decode('utf-8', errors='replace').split('\n')
    result = parse_results(output)

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


def print_header(testname, error_message, input_file_name, args):
    """ Print a header for the test."""
    if testname is not None:
        if error_message is None:
            log.info(_("TEST") + ": " + testname)
        else:
            fmt = "%s: %s (error: '%s')"
            log.fatal(fmt % (_("TEST"), testname, error_message))
    elif error_message is not None:
        log.fatal(error_message)
    log.info(_("COMMAND LINE") + ": " + " ".join(args[1:]) + " " + str(input_file_name))


def print_lines(input_text, file_text, output, opts):
    max_lines = (10000 if opts['verbosity'] >= 4 else 5)
    if input_text is not None:
        log_lines(_("INPUT"), input_text.splitlines(),
                  max_lines=max_lines)

    if file_text is not None:
        lines = file_text.splitlines()
        log_lines(_("TEMPORARY FILE"), file_text.splitlines(),
                  max_lines=max_lines)

    log.debug(_("OUTPUT") + ":")
    for line in output:
        log.debug("> " + line)


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


def print_resume_ordered_check(key, result, target, maxerrors=None):
    """Line by line comparison of result and target.

    Print messages to show matches and mismatches.
    """
    if maxerrors is None:
        maxerrors = len(result) + len(target)
    rescode = ResultType.SUCCESS

    fmt = "%-30s| %-30s"
    log.debug(_("detailed comparison"), extra={'section':key})
    log.debug(fmt % (_("EXPECTED OUTPUT"), _("ACTUAL OUTPUT")))
    for t, r in zip_longest(target, result):
        st = (t.rstrip() if t is not None else _("<nothing>"))
        sr = (r.rstrip() if r is not None else _("<nothing>"))
        if len(st) > 30:
            st = st[:26] + "..."
        if len(sr) > 30:
            sr = sr[:26] + "..."
        log.debug(fmt % (st, sr))

    if len(result) != len(target):
        fmt = _("wrong number of lines (expected %d, got %d)")
        log.error(fmt % (len(target), len(result)),
                  extra={'section':key})
        rescode = ResultType.ERROR
    mm = match.check_lines(result, target)
    if len(mm) > 0:
        fmt = _("line %d is wrong  (expected '%s', got '%s')")
        for (n, got, exp) in mm[:maxerrors]:
            log.error(fmt % (n+1, exp, got), extra={'section':key})
        if len(mm) > maxerrors:
            log.error(_("(... plus other %d errors ...)") %
                      (len(mm) - maxerrors),
                      extra={'section':key})
        rescode = ResultType.ERROR
    else:
        if len(result) > 0 and len(result) != len(target):
            log.warning(_("The first %d lines matched correctly") %
                        min(len(result), len(target)),
                        extra={'section':key})


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
    (args, opts) = parse_options()
    lvl = [logging.ERROR, logging.WARNING, logging.INFO,
           SUCCESS, logging.DEBUG][opts['verbosity']]
    setup_logging(lvl, opts['color'])

    # Parse the configuration file (if given)
    cfgfile = opts['config']
    if not cfgfile:
        cfg = []
    else:
        try:
            with open(cfgfile, "rt") as f:
                cfg = list(parser.parse_sections(f))
        except FileNotFoundError as e:
            print(e)
            sys.exit(1)

    # Parse the expected output from the given file
    try:
        with open(args[0], "rt") as f:
            target = list(parser.parse_sections(f))
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)

    suite = testdata.TestSuite(cfg + target)
    sys.exit(0)  ### !!!

    # Run the individual tests in the suite
    for test in suite:
        dotest(test, args, opts)

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

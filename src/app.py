#!/usr/bin/env python3

import sys
import getopt
import argparse
import os
import math
import pvcheck
import parser
import testdata
import formatter
import jsonformatter
import csvformatter
import executor
import valgrind
import i18n
import exporter

__doc__ = i18n.HELP_en
_ = i18n.translate

_DEFAULT_LOG_FILE = os.path.expanduser("~/.pvcheck.log")


def parse_options():
    """Parse the command line."""
    argparser = argparse.ArgumentParser(description=_("Run tests to verify the correctness of a program."), add_help=False)
    argparser.add_argument("-h", "--help", help=_("print this message and exit."), action='help')
    argparser.add_argument("-c", "--config", help=_("uses the specified configuration file."), nargs='?', const='',
                           default='')
    argparser.add_argument("-t", "--timeout", help=_("set how many seconds it should be waited for the termination of the program.  The default is 10 seconds."),
                           nargs='?', const='10', default='10', type=float)
    argparser.add_argument("-v", "--verbosity", help=_("set the verbosity level, where the level must be an integer between 0 (minimum) and 4 (maximum). The default value is 3."),
                           nargs='?', const='3', default='3', type=int)
    argparser.add_argument("-m", "--max_errors", help=_("reports up to N errors per section (default 4)."), nargs='?',
                           const='4', default='4', type=int)
    argparser.add_argument("-C", "--color", help=_("enable or disable colored output (default AUTO)."), nargs='?',
                           const='AUTO', default='AUTO')
    argparser.add_argument("-V", "--valgrind", help=_("use Valgrind (if installed) to check memory usage."),
                           action='store_true')
    argparser.add_argument("-f", "--format", help=_("select the output type."), nargs='?', const='resume',
                           default='resume')
    argparser.add_argument("-l", "--log", help=_("specify the name of the file used for logging.  The default is ~/.pvcheck.log."),
                           nargs='?', const=_DEFAULT_LOG_FILE, default=_DEFAULT_LOG_FILE)
    argparser.add_argument("-ls", "--list", help=_("list all the available tests."), action='store_true')
    argparser.add_argument("-r", "--run", help=_("run only the selected test."), nargs="?", type=int)
    argparser.add_argument("-e", "--export", help=_("export in a file the input arguments from the selected test."),
                           nargs="?", type=int)
    argparser.add_argument("test_file", help="file contenente i test da eseguire")
    argparser.add_argument("program", help="programma da testare [seguito da argomenti].", nargs='*')

    args = argparser.parse_args()

    verbosity = args.verbosity
    if verbosity < 0 or verbosity > 4:
        print(_("Invalid parameter ('%d')") % verbosity)
        sys.exit(2)

    timeout = args.timeout
    if timeout < 0:
        print(_("Invalid parameter ('%f')") % timeout)
        sys.exit(2)

    maxerrors = args.max_errors
    if maxerrors < 1:
        print(_("Invalid parameter ('%d')") % maxerrors)
        sys.exit(2)

    config = args.config

    color = args.color
    if color not in ("YES", "NO", "AUTO"):
        print(_("Invalid parameter ('%s')") % color)
        sys.exit(2)
    color = (color == "YES" or (color == "AUTO" and sys.stdout.isatty()))

    format = args.format
    if format not in ("resume", "json", "csv"):
        print(_("Invalid parameter ('%s')") % format)
        sys.exit(2)

    logfile = args.log
        
    valgrind = args.valgrind
    test_file = args.test_file
    program = args.program
    run = args.run
    export = args.export
    list = args.list

    args = dict(test_file=test_file, program=program,
                list=list)
    opts = dict(config=config, verbosity=verbosity, timeout=timeout,
                maxerrors=maxerrors, color=color, valgrind=valgrind,
                format=format, logfile=logfile, list=list, run=run, export=export)

    return (args, opts)


def parse_file(filename):
    """Read the content of a file containing tests."""
    if filename == "":
        return []
    try:
        with open(filename, "rt") as f:
            return list(parser.parse_sections(f))
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)


def test_names_list(test_suite):
    """Build a list containing all the test names of a test suite."""
    test_names = []
    for test in test_suite.test_cases():
        test_names.append(test.description)
    return test_names


def print_test_names_list(test_suite):
    """Print a list containing all the test names of a test suite."""
    test_names = test_names_list(test_suite)
    test_number = 1
    number_of_spaces = int(math.log10(len(test_names)) + 1)
    for test_name in test_names:
        try:
            print('{:{align}{width}}'.format(str(test_number), align='>', width=number_of_spaces) + ' ' + test_name)
        except TypeError:
            print('{:{align}{width}}'.format(str(test_number), align='>', width=number_of_spaces) + ' ' + 'NoName')
        test_number += 1
    exit(0)


def initialize_single_test(args):
    """Setup the environment to test only one test of a test suite.

    Return: - the test's index
            - a test file parsed

    """
    test_number = int(args[0]) - 1
    td = parse_file(args[2])
    return test_number, td


def main():
    """Setup the environment and starts the test session."""
    (args, opts) = parse_options()

    single_test_index = None

    cfg = parse_file(opts["config"])

    if args["list"]:
        td = parse_file(args["test_file"])
        suite = testdata.TestSuite(cfg + td)
        print_test_names_list(suite)
        exit(0)

    td = parse_file(args["test_file"])

    if opts['valgrind']:
        cfg.append(testdata.Section('VALGRIND', []))

    suite = testdata.TestSuite(cfg + td)

    if single_test_index is not None:
        suite = suite.test_case(single_test_index)

    if opts['export']:
        exporter.export(suite, single_test_index)

    execlass = (valgrind.ValgrindExecutor if opts["valgrind"]
                else executor.Executor)
    exe = execlass()

    if opts["format"] == "json":
        fmt = jsonformatter.JSONFormatter(indent=4)
    elif opts["format"] == "csv":
        fmt = csvformatter.CSVFormatter()
    else:
        fmtclass = (formatter.ColoredTextFormatter if opts["color"]
                    else formatter.TextFormatter)
        fmt = fmtclass(verbosity=opts["verbosity"],
                       maxerrors=opts["maxerrors"])

    # Pvcheck returns as exit code the number of failed tests.
    # 255 represents a generic error.
    retcode = 255
    args = args['program']
    with open(opts["logfile"], "at") as logfile:
        logfmt = jsonformatter.JSONFormatter(logfile)
        combfmt = formatter.CombinedFormatter([fmt, logfmt])
        pvc = pvcheck.PvCheck(exe, combfmt)
        if single_test_index is None:
            failures = pvc.exec_suite(suite, args,
                                      timeout=opts["timeout"])
        else:
            failures = pvc.exec_single_test(suite, args,
                                            timeout=opts["timeout"])

        retcode = min(failures, 254)
        logfile.write("\n")
    sys.exit(retcode)

if __name__ == "__main__":
    main()

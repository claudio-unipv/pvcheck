#!/usr/bin/env python3

import sys
from argparser import ArgParser
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


_ = i18n.translate
_DEFAULT_LOG_FILE = os.path.expanduser("~/.pvcheck.log")


def parse_options():
    """Parse the command line."""
    argparser = _initialized_argparser()
    args = argparser.parse_args()

    verbosity = args.verbosity
    timeout = args.timeout
    config = args.config
    color = args.color
    color = (color == "YES" or (color == "AUTO" and sys.stdout.isatty()))
    format = args.format
    logfile = args.log
    valgrind = args.valgrind
    run = args.run
    export = args.export
    list = args.list
    test_file = args.file
    program = args.program
    program_arguments = args.program_arguments

    if timeout < 0:
        print(_("Invalid parameter ('%f')") % timeout)
        sys.exit(2)
    maxerrors = args.max_errors

    if maxerrors < 1:
        print(_("Invalid parameter ('%d')") % maxerrors)
        sys.exit(2)

    args = dict(test_file=test_file, program=program, program_arguments=program_arguments
                )
    opts = dict(config=config, verbosity=verbosity, timeout=timeout,
                maxerrors=maxerrors, color=color, valgrind=valgrind,
                format=format, logfile=logfile, list=list, run=run, export=export)

    return args, opts


def _initialized_argparser():
    argparser = ArgParser(description=_("Run tests to verify the correctness of a program."))

    subparsers = argparser.add_subparsers(help=_('[test|test_info] --help for subcommand'))

    # create the parser for the "test" command
    parser_test = subparsers.add_parser('test', help=_('test a program.'))

    parser_test.add_argument("-c", "--config", help=_("uses the specified configuration file."), nargs='?', const='',
                             default='')
    parser_test.add_argument("-t", "--timeout", help=_("set how many seconds it should be waited for the termination "
                             "of the program.  The default is 10 seconds."), nargs='?', const=10, default=10,
                             type=float)
    parser_test.add_argument("-v", "--verbosity", help=_("set the verbosity level, where the level must be an integer "
                             "between 0 (minimum) and 4 (maximum). The default value is 3."), nargs='?', const=3,
                             default=3, type=int, choices=range(0, 4))
    parser_test.add_argument("-m", "--max_errors", help=_("reports up to N errors per section (default 4)."), nargs='?',
                             const=4, default=4, type=int)
    parser_test.add_argument("-V", "--valgrind", help=_("use Valgrind (if installed) to check memory usage."),
                             action='store_true')
    parser_test.add_argument("-l", "--log", help=_("specify the name of the file used for logging.  The default is "
                             "~/.pvcheck.log."), nargs='?', const=_DEFAULT_LOG_FILE, default=_DEFAULT_LOG_FILE)
    parser_test.add_argument("-r", "--run", help=_("run only the selected test."), nargs="?", type=int)
    parser_test.add_argument("-f", "--file", help=_("file containing the tests to be performed (default pvcheck.test).")
                             , default="pvcheck.test")

    exclusive_test = parser_test.add_mutually_exclusive_group()

    exclusive_test.add_argument("-F", "--format", help=_("select the output type."), nargs='?', const='resume',
                                default='resume', choices=('json', 'csv'))
    exclusive_test.add_argument("-C", "--color", help=_("enable or disable colored output (default AUTO)."), nargs='?',
                                const='AUTO', default='AUTO', choices=('YES', 'NO'))

    parser_test.add_argument("program", help=_("program to be tested."))
    parser_test.add_argument("program_arguments", help=_("any arguments of the program to be tested."), nargs='*')

    parser_test.set_defaults(export=None, list=False)

    # create the parser for the "test_info" command
    parser_test_info = subparsers.add_parser('test_info', help=_('get information about a test file.'))
    exclusive_test_info = parser_test_info.add_mutually_exclusive_group(required=True)

    exclusive_test_info.add_argument("-e", "--export", help=_("export in a file the input arguments from the selected "
                                     "test."), nargs="?", type=int)
    exclusive_test_info.add_argument("-ls", "--list", help=_("list all the available tests."), action='store_true')

    parser_test_info.add_argument("-f", "--file", help=_("file containing the tests to be performed "
                                  "(default pvcheck.test)."), default="pvcheck.test")
    parser_test_info.set_defaults(config='', timeout=10, verbosity=3, max_errors=4, color='AUTO', valgrind=False,
                              format='resume', log=_DEFAULT_LOG_FILE, run=None, program=None, program_arguments=None)

    return argparser


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


def main():
    """Setup the environment and starts the test session."""
    (args, opts) = parse_options()

    single_test_index = None

    cfg = parse_file(opts["config"])

    if opts["list"]:
        td = parse_file(args["test_file"])
        suite = testdata.TestSuite(cfg + td)
        print_test_names_list(suite)
        exit(0)

    td = parse_file(args["test_file"])

    if opts['valgrind']:
        cfg.append(testdata.Section('VALGRIND', []))

    suite = testdata.TestSuite(cfg + td)

    if opts['run'] is not None and opts['export'] is None:
        single_test_index = opts['run'] - 1
        suite = suite.test_case(single_test_index)

    if opts['export'] is not None:
        single_test_index = opts['export'] - 1
        suite = suite.test_case(single_test_index)
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
    program = [args['program']]
    if args['program_arguments'] is not None:
        program.extend(args['program_arguments'])

    with open(opts["logfile"], "at") as logfile:
        logfmt = jsonformatter.JSONFormatter(logfile)
        combfmt = formatter.CombinedFormatter([fmt, logfmt])
        pvc = pvcheck.PvCheck(exe, combfmt)
        if single_test_index is None:
            failures = pvc.exec_suite(suite, program,
                                      timeout=opts["timeout"])
        else:
            failures = pvc.exec_single_test(suite, program,
                                            timeout=opts["timeout"])

        retcode = min(failures, 254)
        logfile.write("\n")
    sys.exit(retcode)

if __name__ == "__main__":
    main()

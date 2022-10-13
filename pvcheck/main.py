#!/usr/bin/env python3
import argparse
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
import htmlformatter
import interactiveformatter
import executor
import valgrind
import i18n
import exporter


_ = i18n.translate
_DEFAULT_LOG_FILE = os.path.expanduser("~/.pvcheck.log")


def parse_options():
    """Parse the command line."""
    argparser = _initialized_argparser()
    argparser.set_default_subparser("run")
    args = argparser.parse_args()

    verbosity = args.verbosity
    timeout = args.timeout
    config = args.config
    color = args.color
    color = (color == "YES" or (color == "AUTO" and sys.stdout.isatty()))
    format = args.format
    logfile = args.log
    valgrind = args.valgrind
    run = args.test
    export = args.test_number
    list = args.info
    test_file = args.file
    program = args.program
    program_arguments = args.program_arguments
    maxerrors = args.errors
    output_limit = args.output_limit

    args = dict(test_file=test_file, program=program, program_arguments=program_arguments
                )
    opts = dict(config=config, verbosity=verbosity, timeout=timeout,
                maxerrors=maxerrors, color=color, valgrind=valgrind,
                format=format, logfile=logfile, list=list, run=run, export=export, output_limit=output_limit)
    return args, opts


def _initialized_argparser():
    argparser = ArgParser(description=_("Run tests to verify the correctness of a program."))

    subparsers = argparser.add_subparsers(help=_('[run|info|export] --help for command help (default=run)'))

    # create the parser for the "run" command
    parser_run = subparsers.add_parser('run', help=_('test a program.'))
    a = parser_run.add_argument
    a("program", help=_("program to be tested."))
    a("program_arguments", help=_("any arguments of the program to be tested."), nargs='*')

    a("-f", "--file", help=_("file containing the tests to be performed (default pvcheck.test).")
                            , default="pvcheck.test")
    a("-T", "--test", help=_("run only the selected test."), nargs="?", type=int)
    a("-t", "--timeout", help=_("set how many seconds it should be waited for the termination "
                            "of the program.  The default is 10 seconds."), nargs='?', const=10, default=10,
                            type=check_float_non_negative)
    a("-e", "--errors", help=_("reports up to N errors per section (default 4)."), nargs='?',
                             const=4, default=4, type=check_int_greater_than_one)
    a("-v", "--verbosity", help=_("set the verbosity level, where the level must be an integer "
                            "between 0 (minimum) and 4 (maximum). The default value is 3."), nargs='?', const=3,
                            default=3, type=int, choices=range(0, 5))
    a("-V", "--valgrind", help=_("use Valgrind (if installed) to check memory usage."),
                            action='store_true')
    a("-l", "--log", help=_("specify the name of the file used for logging.  The default is "
                            "~/.pvcheck.log."), nargs='?', const=_DEFAULT_LOG_FILE, default=_DEFAULT_LOG_FILE)
    a("-L", "--output_limit", help=_("cut the output of the program to a maximum of L lines.  "
                            "The default is 10000."), nargs='?', const=10000, default=10000,
                            type=check_int_non_negative)
    a("-c", "--config", help=_("uses the specified configuration file."), nargs='?', const='',
                            default='')
    a("-F", "--format", help=_("select the output type."), default='interactive',
      choices=('interactive', 'text', 'json', 'csv', 'html'))
    a("-C", "--color", help=_("enable or disable colored output (default AUTO)."), nargs='?',
                               const='AUTO', default='AUTO', choices=('YES', 'NO', 'AUTO'))

    parser_run.set_defaults(test_number=None, info=False)

    # create the parser for the "info" command
    parser_info = subparsers.add_parser('info', help=_("list all the available tests."))

    parser_info.add_argument("file", help=_("file containing the tests to be performed."))
    parser_info.set_defaults(config='', timeout=10, verbosity=3, errors=4, color='AUTO', valgrind=False,
                             format='text', log=_DEFAULT_LOG_FILE, test=None, program=None, program_arguments=None,
                             test_number=None, info=True, output_limit=10000)

    # create the parser for the "export" command
    parser_export = subparsers.add_parser('export', help=_("export in a file the input arguments from the selected "
                                          "test."))
    parser_export.add_argument("test_number", type=int)
    parser_export.add_argument("file", help=_("file containing the tests to be performed."))
    parser_export.set_defaults(config='', timeout=10, verbosity=3, errors=4, color='AUTO', valgrind=False,
                               format='text', log=_DEFAULT_LOG_FILE, test=None, program=None, program_arguments=None,
                               info=False, output_limit=10000)

    return argparser


def check_float_non_negative(value):
    fvalue = float(value)
    if fvalue < 0:
        raise argparse.ArgumentTypeError((_("Invalid parameter"), "('%s')" % value))
    return fvalue


def check_int_non_negative(value):
    ivalue = int(value)
    if ivalue < 0:
        raise argparse.ArgumentTypeError((_("Invalid parameter"), "('%s')" % value))
    return ivalue


def check_int_greater_than_one(value):
    ivalue = int(value)
    if ivalue < 1:
        raise argparse.ArgumentTypeError((_("Invalid parameter"), "('%s')" % value))
    return ivalue


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

    if opts["format"] == "interactive":
        fmt = interactiveformatter.InteractiveFormatter()
    elif opts["format"] == "json":
        fmt = jsonformatter.JSONFormatter(indent=4, test_file=args["test_file"])
    elif opts["format"] == "csv":
        fmt = csvformatter.CSVFormatter()
    elif opts["format"] == "html":
        fmt = htmlformatter.HTMLFormatter()
    elif opts["format"] == "text":
        fmtclass = (formatter.ColoredTextFormatter if opts["color"]
                    else formatter.TextFormatter)
        fmt = fmtclass(verbosity=opts["verbosity"],
                       maxerrors=opts["maxerrors"])
    else:
        raise ValueError("Unknown format '{}'".format(opts["format"]))
    # Pvcheck returns as exit code the number of failed tests.
    # 255 represents a generic error.
    retcode = 255
    program = [args['program']]
    if args['program_arguments'] is not None:
        program.extend(args['program_arguments'])

    with open(opts["logfile"], "at") as logfile:
        logfmt = jsonformatter.JSONFormatter(logfile,
                                             test_file=args["test_file"])
        combfmt = formatter.CombinedFormatter([fmt, logfmt])
        pvc = pvcheck.PvCheck(exe, combfmt)
        try:
            if single_test_index is None:
                failures = pvc.exec_suite(suite, program,
                                          timeout=opts["timeout"],
                                          output_limit=opts["output_limit"])
            else:
                failures = pvc.exec_single_test(suite, program,
                                                timeout=opts["timeout"],
                                                output_limit=opts["output_limit"])
            retcode = min(failures, 254)
        finally:
            # in case of exception (e.g. tested a non executable file) write a
            # newline to the json log
            logfile.write("\n")
    sys.exit(retcode)


if __name__ == "__main__":
    main()

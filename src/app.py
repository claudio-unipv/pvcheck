#!/usr/bin/env python3

import sys
import getopt
import os

import pvcheck
import parser
import testdata
import formatter
import jsonformatter
import executor
import valgrind
import i18n


__doc__ = i18n.HELP_en
_ = i18n.translate

_DEFAULT_LOG_FILE = os.path.expanduser("~/.pvcheck.log")


def parse_options():
    """Parse the command line."""

    shortopts = "hc:t:v:m:C:Vo:l:L:"
    longopts = ["help", "config=", "timeout=", "verbosity=",
                "max-errors=", "color=", "valgrind", "output=",
                "log=", "output-limit="]
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

    def invalid(cond, fmt, val):
        if cond:
            print(_("Invalid parameter"), "('%s')" % (fmt % val))
            sys.exit(2)

    def optval(key1, key2, default=None, result_type=None):
        x = opts.get(key1, opts.get(key2, default))
        if result_type is None:
            return x
        try:
            return result_type(x)
        except ValueError:
            invalid(True, '%s', x)

    verbosity = optval('-v', '--verbosity', '3', int)
    invalid(verbosity < 0 or verbosity > 4, '%d', verbosity)

    timeout = optval('-t', '--timeout', '10', float)
    invalid(timeout < 0, '%f', timeout)

    maxerrors = optval('-m', '--max-errors', '4', int)
    invalid(maxerrors < 1, '%d', maxerrors)

    config = optval('-c', '--config', '', str)

    color = optval('-C', '--color', 'AUTO', str)
    invalid(color.upper() not in ("YES", "NO", "AUTO"), '%s', color)
    color = (color.upper() == "YES" or
             (color.upper() == "AUTO" and sys.stdout.isatty()))

    output = optval('-o', '--output', 'resume', str).upper()
    invalid(output not in ("RESUME", "JSON"), '%s', output)

    logfile = optval('-l', '--log', _DEFAULT_LOG_FILE, str)

    output_limit = optval('-L', '--output-limit', 10000, int)
    invalid(output_limit < 0, '%d', output_limit)

    valgrind = (True if '-V' in opts or '--valgrind' in opts else False)
    opts = dict(config=config, verbosity=verbosity, timeout=timeout,
                maxerrors=maxerrors, color=color, valgrind=valgrind,
                output=output, logfile=logfile,
                output_limit=output_limit)

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


def main():
    """Setup the environment and starts the test session."""
    (args, opts) = parse_options()

    cfg = parse_file(opts["config"])
    td = parse_file(args[0])
    if opts['valgrind']:
        cfg.append(testdata.Section('VALGRIND', []))
    suite = testdata.TestSuite(cfg + td)

    execlass = (valgrind.ValgrindExecutor if opts["valgrind"]
                else executor.Executor)
    exe = execlass()


    if opts["output"] == "JSON":
        fmt = jsonformatter.JSONFormatter(indent=4)
    else:
        fmtclass = (formatter.ColoredTextFormatter if opts["color"]
                    else formatter.TextFormatter)
        fmt = fmtclass(verbosity=opts["verbosity"],
                       maxerrors=opts["maxerrors"])

    # Pvcheck returns as exit code the number of failed tests.
    # 255 represents a generic error.
    retcode = 255
    with open(opts["logfile"], "at") as logfile:
        logfmt = jsonformatter.JSONFormatter(logfile)
        combfmt = formatter.CombinedFormatter([fmt, logfmt])
        pvc = pvcheck.PvCheck(exe, combfmt)
        failures = pvc.exec_suite(suite, args[1:],
                                  timeout=opts["timeout"],
                                  output_limit=opts["output_limit"])
        retcode = min(failures, 254)
        logfile.write("\n")
    sys.exit(retcode)

if __name__ == "__main__":
    main()

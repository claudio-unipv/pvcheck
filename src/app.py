#!/usr/bin/env python3

import sys
import getopt

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
        except ValueError:
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
    if maxerrors < 1:
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
    opts = dict(config=config, verbosity=verbosity, timeout=timeout,
                maxerrors=maxerrors, color=color, valgrind=valgrind,
                output=output)

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
    pvc = pvcheck.PvCheck(exe, fmt)
    pvc.exec_suite(suite, args[1:], timeout=opts["timeout"])


if __name__ == "__main__":
    main()

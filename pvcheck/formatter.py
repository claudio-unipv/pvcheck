"""Classes that communicate the results."""

import sys
from itertools import zip_longest
from collections import defaultdict
import pvcheck.executor
from pvcheck.i18n import translate as _


class Formatter:
    """Abstract base class for all the formatters.

    The client is supposed to call the methods in the following order:

    1) begin_session
    2) <repeat zero or more times>
    2a)  begin_test
    2b)  execution_result
    2c)  zero or more of comparison_result or missing_section
    2d)  end_test
    3) end_session

    """

    def begin_session(self):
        """Called when starting a new test session."""
        pass

    def end_session(self):
        """Called at the end of a test session."""
        pass

    def begin_test(self, description, cmdline_args, input, tempfile):
        """Called when a new test begins."""
        pass

    def end_test(self):
        """Called when a test finishes."""
        pass

    def execution_result(self, cmdline_args, execution_result, test):
        """Called when the execution of a test is terminated."""
        pass

    def comparison_result(self, expected, got, diffs, matches):
        """Called after the comparison of a section.

        - expected: the expected result
        - got: the output of the program
        - diffs: distance measures between the two sets of lines
        - matches: lines matching those in 'got'
        """
        pass

    def missing_section(self, expected):
        """Called when no answer has been provided for a section.

        - expected: the expected result
        """
        pass


class TextFormatter(Formatter):
    """Formatter that writes the results as plain text."""

    # Message priority levels, corresponding to the verbosity.
    DEBUG = 4
    INFO = 3
    SUCCESS = 2
    WARNING = 1
    ERROR = 0
    FATAL = -1

    _RESULT_TABLE = {
        pvcheck.executor.ER_OK: (DEBUG, []),
        pvcheck.executor.ER_TIMEOUT:
        (ERROR, [_("TIMEOUT EXPIRED: PROCESS TERMINATED")]),
        pvcheck.executor.ER_OUTPUT_LIMIT:
        (ERROR, [_("TOO MANY OUTPUT LINES")]),
        pvcheck.executor.ER_SEGFAULT:
        (ERROR, [_("PROCESS ENDED WITH A FAILURE"),
                 _("(SEGMENTATION FAULT)")]),
        pvcheck.executor.ER_ERROR:
        (ERROR, [_("PROCESS ENDED WITH A FAILURE"),
                 _("(ERROR CODE {status})")]),
        pvcheck.executor.ER_NOTFILE:
        (ERROR, [_("FAILED TO RUN THE FILE '{progname}'"),
                 _("(the file does not exist)")])
    }

    def __init__(self, destination=sys.stdout, verbosity=None,
                 maxerrors=None):
        """Create the text formatter.

        - destination: file-like object receiving the text messages
        - verbosity: set the amount of information to write
        - maxerrors: maximum number of errors to print (per section)

        verbosity must be in the range 0-4.  maxerrors must be at
        least 1 (or None to print an unlimited number of errors).

        """
        self.set_verbosity(verbosity)
        self._dst = destination
        self._maxerrors = maxerrors
        self._testcount = 0
        self._test_status = None

    def set_verbosity(self, verbosity=None):
        """Set a new verbosity level (0-4)."""
        self._verbosity = (verbosity if verbosity is not None
                           else self.INFO)

    def message(self, level, text):
        """Write a text message with the given level."""
        if self.level_enabled(level):
            self._dst.write(text)
            self._dst.write('\n')

    def level_enabled(self, level):
        """Return true if the output level is enabled."""
        return (self._verbosity >= level)

    def debug(self, text):
        """Write a message with the debug level."""
        self.message(self.DEBUG, text)

    def info(self, text):
        """Write a message with the info level."""
        self.message(self.INFO, text)

    def success(self, text):
        """Write a message with the success level."""
        self.message(self.SUCCESS, text)

    def warning(self, text):
        """Write a message with the warning level."""
        self.message(self.WARNING, text)

    def error(self, text):
        """Write a message with the error level."""
        self.message(self.ERROR, text)

    def fatal(self, text):
        """Write a message with the fatal level."""
        self._message(self.FATAL, text)

    def _format_section(self, title, content, maxlines=5):
        """Compose a text session.

        If there are too many lines the string is truncated with a
        message.

        """
        lines = list(map(str.rstrip, content.splitlines()))
        n = len(lines)
        if n == 0:
            return "{}: <empty>".format(title)
        if n == 1:
            return "{}: {}".format(title, lines[0])
        if maxlines is not None and n > maxlines:
            lines = lines[:maxlines]
            extra = n - maxlines + 1
            lines[-1] = _("(... plus other %d lines ...)") % extra
        return "{}:\n{}".format(title, "\n".join(lines))

    def begin_session(self):
        # Initialize the counters for the summary
        self._testcount = 0
        self._sect_results = []

    def _unique(self, seq):
        # Unique elements in seq, preserving their order of occurrence
        seen = set()
        for x in seq:
            if x in seen:
                continue
            seen.add(x)
            yield x

    def _count_results(self, tag, label):
        return sum(1 for x in self._sect_results if x == (tag, label))

    def end_session(self):
        if self._testcount < 2:
            return

        # Write a summary of the session
        self.info("")
        self.info("=" * 60)
        self.info("")
        self.info(_("SUMMARY"))

        tags = list(self._unique(x[0] for x in self._sect_results))
        l = max(map(len, tags))
        for t in tags:
            row = ["{:{}}:".format(t, l)]

            row.append("%2d %s," % (self._count_results(t, "ok"), _("successes")))
            row.append("%2d %s," % (self._count_results(t, "warning"), _("warnings")))
            row.append("%2d %s" % (self._count_results(t, "error"), _("errors")))
            self.info("  ".join(row))
        self.info("")
        self._testcount = 0

    def _proc_args(self, args):
        return [(a if a is not pvcheck.executor.ARG_TMPFILE
                 else _("<temp.file>"))
                for a in args]

    def begin_test(self, description, cmdline_args, input, tempfile):
        if self._testcount > 0:
            self.info("-" * 60)
        self._testcount += 1
        maxlines = (None if self.level_enabled(self.DEBUG) else 5)
        f = lambda tit,con: self._format_section(tit, con, maxlines)
        if description is not None:
            self.info(f(_("TEST"), description))
        arglist = " ".join(self._proc_args(cmdline_args))
        self.info(f(_("COMMAND LINE"), arglist))
        if input is not None and input.strip():
            self.info(f(_("INPUT"), input))
        if tempfile is not None:
            self.info(f(_("TEMPORARY FILE"), tempfile))
        self._test_status = None  # initialize test status

    def end_test(self):
        if self._test_status == "ok":
            self._sect_results.append((_("<program>"), "ok"))
        elif self._test_status == "warning":
            self._sect_results.append((_("<program>"), "warning"))
        else:
            self._sect_results.append((_("<program>"), "error"))

    def execution_result(self, cmdline_args, execution_result, test):
        info = {
            'progname': cmdline_args[0],
            'status': execution_result.status
        }
        level, lines = self._RESULT_TABLE[execution_result.result]
        msg = " ".join(lines).format(**info)
        if msg:
            self.message(level, msg)
        if execution_result.output and self.level_enabled(self.DEBUG):
            # This can be a lot of data, so do it only when the DEBUG
            # level is enabled.
            lines = "\n".join("> " + line for line
                     in execution_result.output.splitlines())
            self.debug(self._format_section(_("OUTPUT"),
                                            lines,
                                            maxlines=None))

    def comparison_result(self, expected, got, diffs, matches):
        if max(diffs, default=0) == 0:
            self._sect_results.append((expected.tag, "ok"))
            if self._test_status is None:
                self._test_status = "ok"
            self.success("{}: {}".format(expected.tag, _("OK")))
        else:
            self._sect_results.append((expected.tag, "error"))
            self._test_status = "error"
            if len(expected.content) != len(got.content):
                fmt = _("wrong number of lines (expected %d, got %d)")
                msg = fmt % (len(expected.content), len(got.content))
                self.error(expected.tag + ": " + msg)

            err_diff = _("line %d is wrong  (expected '%s', got '%s')")
            err_un = _("unexpected line '%s'")
            err_mis = _("missing line (expected '%s')")
            lines = []
            for (i, d) in enumerate(diffs):
                if d <= 0:
                    continue
                if matches[i] is None:
                    msg = err_un % got.content[i]
                elif i >= len(got.content):
                    msg = err_mis % matches[i]
                else:
                    msg = err_diff % (i + 1, matches[i], got.content[i])
                lines.append(expected.tag + ": " + msg)

            disp = (len(lines) if self._maxerrors is None
                    else (len(lines) if len(lines) < self._maxerrors
                          else self._maxerrors - 1))
            extra = len(lines) - disp
            for line in lines[:disp]:
                self.error(line)
            if extra > 0:
                self.error(_("(... plus other %d errors ...)") % extra)
            if len(got.content) > 0 and max(diffs[:len(got.content)]) == 0:
                fmt = _("The first %d lines matched correctly")
                msg = fmt % len(got.content)
                self.warning(expected.tag + ": " + msg)

        # Extra information to be skipped unless the DEBUG level is
        # enabled.
        if self.level_enabled(self.DEBUG):
            self._detailed_comparison(expected, got, matches)

    def _detailed_comparison(self, expected, got, matches):
        fmt = "%-30s| %-30s"
        def prnt(s):
            s = (s.rstrip() if s is not None else _("<nothing>"))
            return (s if len(s) <= 30 else s[:26] + "...")

        self.debug(expected.tag + ": " +  _("detailed comparison"))
        self.debug(fmt % (_("EXPECTED OUTPUT"), _("ACTUAL OUTPUT")))

        for (e, a) in zip_longest(matches, got.content):
            self.debug(fmt % (prnt(e), prnt(a)))

    def missing_section(self, expected):
        if self._test_status != "ok" or self._test_status is None:
            self._test_status = "warning"
        self._sect_results.append((expected.tag, "warning"))
        self.warning(expected.tag + ": " + _("missing section"))


class ColoredTextFormatter(TextFormatter):
    """A formatter that outputs colored messages.

    The color is chosen according to the type of the message.
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
        TextFormatter.FATAL: BOLD + DARK_RED,
        TextFormatter.ERROR: BOLD + RED,
        TextFormatter.WARNING: BOLD + DARK_YELLOW,
        TextFormatter.INFO: "",
        TextFormatter.SUCCESS: BOLD + DARK_GREEN,
        TextFormatter.DEBUG: BLUE
    }

    def message(self, level, text):
        super().message(level, self.COLORS[level] + text + self.ENDC)


class CombinedFormatter(Formatter):
    """A formatter that broadcasts the messages to other formatters."""

    def __init__(self, formatters=()):
        """Create the formatter."""
        self.formatters = list(formatters)

    def begin_session(self):
        for f in self.formatters:
            f.begin_session()

    def end_session(self):
        for f in self.formatters:
            f.end_session()

    def begin_test(self, *args):
        for f in self.formatters:
            f.begin_test(*args)

    def end_test(self):
        for f in self.formatters:
            f.end_test()

    def execution_result(self, *args):
        for f in self.formatters:
            f.execution_result(*args)

    def comparison_result(self, *args):
        for f in self.formatters:
            f.comparison_result(*args)

    def missing_section(self, *args):
        for f in self.formatters:
            f.missing_section(*args)

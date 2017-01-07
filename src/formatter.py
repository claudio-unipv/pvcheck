"""Classes to be used to communicate the results."""

import sys
from itertools import zip_longest
import i18n
import executor

from i18n import translate as _

# Possibile execution results"
ER_OK = "OK"
ER_EXECUTION_ERROR = "EXE_ERROR"
ER_SEGMENTATION_FAULT = "SEGFAULT"
ER_TIMEOUT = "TIMEOUT"
ER_ERROR_CODE = "ERR_CODE"


class Formatter:
    """Abstract base class for all the formatters."""

    def begin_session(self):
        """Called when starting a new test session."""
        pass

    def begin_test(self, description, cmdline_args, input, tempfile):
        """Called when a new test begins."""
        pass

    def execution_result(self, execution_result):
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
        executor.ER_OK: (DEBUG, []),
        executor.ER_TIMEOUT:
        (ERROR, [_("TIMEOUT EXPIRED: PROCESS TERMINATED")]),
        executor.ER_SEGFAULT:
        (ERROR, [_("PROCESS ENDED WITH A FAILURE"),
                 _("(SEGMENTATION FAULT)")]),
        executor.ER_ERROR:
        (ERROR, [_("PROCESS ENDED WITH A FAILURE"),
                 _("(ERROR CODE {status})")]),
        executor.ER_NOTFILE:
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
        self._verbosity = (verbosity if verbosity is not None else self.INFO)
        self._dst = destination
        self._maxerrors = maxerrors

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
            lines[-1] = _("(... plus other %d lines ...)")
        return "{}:\n{}".format(title, "\n".join(lines))

    def begin_test(self, description, cmdline_args, input, tempfile):
        maxlines = (None if self._verbosity == self.DEBUG else 5)
        f = lambda tit,con: self._format_section(tit, con, maxlines)
        if description is not None:
            self.info(f(_("TEST"), description))
        self.info(f(_("COMMAND LINE"), " ".join(cmdline_args)))
        if input is not None and input.strip():
            self.info(f(_("INPUT"), input))
        if tempfile is not None:
            self.info(f(_("TEMPORARY FILE"), tempfile))

    def execution_result(self, cmdline_args, execution_result):
        info = {
            'progname': cmdline_args[0],
            'status': execution_result.status
        }
        level, lines = self._RESULT_TABLE[execution_result.result]
        msg = " ".join(lines).format(**info)
        if msg:
            self.message(level, msg + "\n")
        if execution_result.output and self.level_enabled(self.DEBUG):
            # This can be a lot of data, so do it only when the DEBUG
            # level is enabled.
            lines = "\n".join("> " + line for line
                     in execution_result.output.splitlines())
            self.debug(self._format_section(_("OUTPUT"),
                                            lines,
                                            maxlines=None))

    def comparison_result(self, expected, got, diffs, matches):
        if max(diffs) == 0:
            self.success("{}: {}".format(expected.tag, _("OK")))
        else:
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
                msg = fmt % min(len(got.content))
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


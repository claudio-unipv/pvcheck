"""Classes to be used to communicate the results."""

import sys
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
    """Base class for all the formatters."""

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
    
    def __init__(self, destination=sys.stdout, verbosity=3):
        self._verbosity = verbosity
        self._dst = destination

    def message(self, level, text):
        """Write a text message with the given level."""
        if self._verbosity >= level:
            self._dst.write(text)

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
            return "{}: {}\n".format(title, lines[0])
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
        if execution_result.output:
            self.debug(self._format_section(_("OUTPUT"),
                                            execution_result.output,
                                            maxlines=None))

    def comparison_result(self, expected, got, diffs, matches):
        if max(diffs) == 0:
            self.success("[{}] {}".format(expected.tag, _("OK")))
        return
        fmt = _("wrong number of lines (expected %d, got %d)")
        log.error(fmt % (len(target), len(result)),
                  extra={'section':key})


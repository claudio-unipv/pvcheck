"""Classes that communicate the results."""

import curses
import threading
import formatter
import executor
import functools
from i18n import translate as _


# TODO: thread mutex
# TODO: cmdline_args, input, tempfile in begin_test
# TODO: help page
# TODO: summary page
# TODO: test info page
# TODO: i18n


_CALLBACKS = {}


def _register_key(*keys):
    """Decorator registering key->callback pairs.

    Keys can be strings or character codes."""
    def decorator(f):
        for k in keys:
            if isinstance(k, str):
                k = ord(k)
            _CALLBACKS[k] = f
        return f
    return decorator


def _synchronized(f):
    @functools.wraps(f)
    def decorated(self, *args, **kwargs):
        with self._mutex:
            return f(self, *args, **kwargs)
    return decorated


class InteractiveFormatter(formatter.Formatter):
    """Formatter that uses curses to report the result."""

    FOOTER_H = 2  # height of the footer
    MAX_W = 512   # max line length

    COLOR_OK = 1
    COLOR_WARN = 2
    COLOR_ERR = 3

    _RESULT_TABLE = {
        executor.ER_OK: None,
        executor.ER_TIMEOUT: _("TIMEOUT EXPIRED: PROCESS TERMINATED"),
        executor.ER_OUTPUT_LIMIT: _("TOO MANY OUTPUT LINES"),
        executor.ER_SEGFAULT: _("PROCESS ENDED WITH A FAILURE (SEGMENTATION FAULT)"),
        executor.ER_ERROR: ("PROCESS ENDED WITH A FAILURE (ERROR CODE {status})"),
        executor.ER_NOTFILE: _("FAILED TO RUN THE FILE '{progname}' the file does not exist)")
    }

    def __init__(self):
        """Create the interactive formatter."""
        self._reports = []
        self._report_index = 0
        self._screen = None
        self._mutex = threading.Lock()

    @_register_key("q", "Q", 27)  # 27 -> ESC
    def _quit(self):
        self._stop = True

    @_register_key("p", "P", curses.KEY_UP)
    def scroll_line_up(self):
        self._reports[self._report_index].scroll(self._text_height(), -1)
        self._update()

    @_register_key("n", "N", curses.KEY_DOWN, 10)  # 10 -> ENTER
    def scroll_line_down(self):
        self._reports[self._report_index].scroll(self._text_height(), 1)
        self._update()

    @_register_key(curses.KEY_PPAGE)
    def scroll_page_up(self):
        self._reports[self._report_index].scroll(self._text_height(), pages=-1)
        self._update()

    @_register_key(curses.KEY_NPAGE)
    def scroll_page_down(self):
        self._reports[self._report_index].scroll(self._text_height(), pages=1)
        self._update()

    @_register_key(curses.KEY_HOME)
    def scroll_begin(self):
        self._reports[self._report_index].scroll(self._text_height(), documents=-1)
        self._update()

    @_register_key(curses.KEY_END)
    def scroll_end(self):
        self._reports[self._report_index].scroll(self._text_height(), documents=1)
        self._update()

    @_register_key("r", "R", curses.KEY_RESIZE)
    def resize(self):
        self._update()

    @_register_key(curses.KEY_LEFT)
    def previous_document(self):
        self._screen.clear()
        if len(self._reports) > 1:
            self._report_index = max(self._report_index - 1, 1)
        self._update()

    @_register_key(curses.KEY_RIGHT)
    def next_document(self):
        self._screen.clear()
        self._report_index = min(self._report_index + 1, len(self._reports) - 1)
        self._update()

    def _thread_body(self):
        """UI thread."""
        self._stop = False
        curses.wrapper(self._main_loop)

    def _main_loop(self, screen):
        """Main loop managing the interaction with the user."""
        with self._mutex:
            self._screen = screen
            curses.use_default_colors()
            curses.init_pair(self.COLOR_OK, curses.COLOR_GREEN, -1)
            curses.init_pair(self.COLOR_WARN, curses.COLOR_YELLOW, -1)
            curses.init_pair(self.COLOR_ERR, curses.COLOR_RED, -1)
            self._footer = curses.newwin(self.FOOTER_H, self._text_width(), self._text_height(), 0)
            self._footer.bkgd(" ", curses.A_REVERSE)
            self._reports.append(Report("PVCHECK", self.MAX_W))
            self._reports[-1].add_line("Waiting for test results...")
            self._report_index = 0
            self._update()
        while not self._stop:
            ch = screen.getch()
            with self._mutex:
                _CALLBACKS.get(ch, lambda self: None)(self)

    def _text_height(self):
        """Number of text lines displayed."""
        return self._screen.getmaxyx()[0] - self.FOOTER_H

    def _text_width(self):
        """Width of the displayed text."""
        return min(self._screen.getmaxyx()[1], self.MAX_W)

    def _add_footer(self, line, align, text, *extra):
        k = self._text_width() - 1 - len(text)
        pos = max(0, (0 if align == "left" else (k if align == "right" else k //2 )))
        self._footer.addnstr(line, pos, text, self._text_width() - 1 - pos, *extra)

    def _add_short_report(self):
        texts = [
            "%3d " % self._ok_count, _(" passes, "),
            "%3d " % self._warn_count, _(" warnings, "),
            "%3d " % self._err_count, _(" errors")
        ]
        styles = [
            [curses.color_pair(self.COLOR_OK)], [],
            [curses.color_pair(self.COLOR_WARN)], [],
            [curses.color_pair(self.COLOR_ERR)], []
        ]
        n = self._text_width() - 1
        pos = 0
        for t, s in zip (texts, styles):
            self._footer.addnstr(1, pos, t, n, *s)
            pos += len(t)
            n -= len(t)
        
    def _update(self):
        """Redraw everything."""
        if self._screen is None:
            return
        self._screen.refresh()
        height = self._text_height()
        width = self._text_width()
        doc = self._reports[self._report_index]
        self._footer.mvwin(height, 0)
        doc.refresh(self._text_height(), self._text_width())
        self._footer.clear()
        self._add_footer(0, "center", _("[Press 'h' for help]"), curses.A_DIM)
        text = _("Test case %d of %d (%s) ") % (self._report_index, len(self._reports) - 1, doc.title)
        self._add_footer(0, "left", text)
        text = _("Lines {%d}-{%d}/{%d}") % (doc.top(), doc.bottom(height), doc.length())
        self._add_footer(0, "right", text)
        self._add_short_report()
        if self._running:
            tot = self._err_count + self._warn_count + self._ok_count
            text = "TEST RUNNING..." + "|/-\\"[tot % 4]
        else:
            text = "TEST COMPLETED"
        self._add_footer(1, "right", text, curses.A_BOLD)
        self._footer.refresh()

    def begin_session(self):
        self._err_count = self._warn_count = self._ok_count = 0
        self._running = True
        # Start the UI thread
        self._thread = threading.Thread(target=self._thread_body)
        self._thread.start()
        for _ in range(10 ** 7):
            pass

    def end_session(self):
        # Wait the termination of the UI thread
        with self._mutex:
            self._running = False
            self._update()
        self._thread.join()

    @_synchronized
    def begin_test(self, description, cmdline_args, input, tempfile):
        description = description or ""
        self._reports.append(Report(description, self.MAX_W))
        if self._report_index == 0:
            self._report_index = 1
        self._update()

    @_synchronized
    def end_test(self):
        pass

    @_synchronized
    def execution_result(self, cmdline_args, execution_result):
        info = {
            'progname': cmdline_args[0],
            'status': execution_result.status
        }
        message = self._RESULT_TABLE[execution_result.result]
        if execution_result.result != executor.ER_OK:
            self._err_count += 1
            message = message.format(**info)
            for line in message.splitlines():
                self._reports[-1].add_line(line, curses.color_pair(self.COLOR_ERR))
        self._update()

    @_synchronized
    def comparison_result(self, expected, got, diffs, matches):
        add = self._reports[-1].add_line
        all_ok = (max(diffs, default=0) <= 0)
        if all_ok:
            self._ok_count += 1
        else:
            self._err_count += 1
        color = curses.color_pair(self.COLOR_OK if all_ok else self.COLOR_ERR)
        add("[%s]" % expected.tag, color | curses.A_BOLD)

        err_diff = _("%s\t\t(expected '%s')")
        err_un = _("%s\t\t(this line was not expected)")
        err_mis = _("\t\t(missing line '%s')")

        for (i, d) in enumerate(diffs):
            if d <= 0:
                # Correct
                add(got.content[i], curses.color_pair(self.COLOR_OK))
            elif matches[i] is None:
                # Extra line
                add(err_un % got.content[i], curses.color_pair(self.COLOR_ERR))
            elif i >= len(got.content):
                # Missing line
                add(err_mis % matches[i], curses.color_pair(self.COLOR_ERR))
            else:
                # Mismatching lines
                add(err_diff % (got.content[i], matches[i]), curses.color_pair(self.COLOR_ERR))
        add("")
        self._update()

    @_synchronized
    def missing_section(self, expected):
        self._warn_count += 1
        message = _("\t\t(section [%s] is missing)") % expected.tag
        self._reports[-1].add_line(message, curses.color_pair(self.COLOR_WARN))
        self._reports[-1].add_line("")
        self._update()


class Report:
    """Test result displayed on the screen."""

    def __init__(self, title, max_width):
        """Create a new report with the given title.

        Lines are truncated to max_width.
        """
        self.title = title
        self._length = 0
        self._max_width = max_width
        self._pad = curses.newpad(1, max_width)
        self._position = 0

    def add_line(self, line, *extra):
        """Add a line at the bottom of the document."""
        self._pad.resize(self._length + 1, self._max_width)
        self._pad.addnstr(self._length, 0, line, self._max_width, *extra)
        self._length += 1

    def scroll(self, page_height, lines=0, pages=0, documents=0):
        """Scroll up or down."""
        amount = lines + page_height * pages + documents * self._length
        self._position = max(0, min(self._position + amount, self._length - page_height))

    def refresh(self, page_height, page_width):
        """Redraw the document on the screen."""
        self._pad.refresh(self._position, 0, 0, 0, page_height - 1, page_width - 1)

    def top(self):
        """Index of the first line on the screen (starting from 1)."""
        return self._position + 1

    def bottom(self, page_height):
        """Index of the last line on the screen."""
        return min(self._position + page_height, self._length)

    def length(self):
        """Number of lines in the document."""
        return self._length

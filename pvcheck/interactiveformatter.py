# -*- coding: utf-8 -*-

"""Interactive interface."""

import curses
import threading
import pvcheck.formatter
import pvcheck.executor
import functools
import pvcheck.i18n

_ = pvcheck.i18n.translate


# TODO: i18n
# TODO: refactoring with Formatter + separate UI class


HELP_MESSAGE = """

PVCHECK automatic verification of computer programs
===================================================


Keybord controls:

  RIGHT    switch to the next test in the suite
  
  LEFT     switch to the previous test in the suite

  DOWN, n  scroll one line down

  UP, p    scroll one line up

  PgDN     scroll one page down
  
  PgUP     scroll one page up
  
  HOME     scroll to the beginning
  
  END      scroll to the end
  
  r        redraw the screen
  
  q, ESC   close the program
  
  s        show a summary of the results
  
  i        show info about the test case
  
  o        show the program's output
  
  h, ?     show this page  

"""

HELP_MESSAGE_IT = """

PVCHECK verifica automatica di programmi 
===================================================


Controlli tramite tastiera

  DESTRA   passa al test successivo nella suite

  SINISTRA passa al test precedente nella suite

  GIU`, n  scorre una riga in giu`

  SU, p    scorre una riga in su

  PgDN     scorre una pagina in giu`

  PgUP     scorre una pagina in su

  HOME     scorre all'inizio

  END      scorre alla fine

  r        ridisegna lo schermo

  q, ESC   chiude il programma
  
  s        mostra un riepilogo dei risultati
  
  i        mostra informazioni sul caso di test
  
  o        mostra l'output del programma

  h, ?     mostra questa pagina

"""


pvcheck.i18n.register_translation(HELP_MESSAGE, "it", HELP_MESSAGE_IT)


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
    """Makes the calls to the method acquire a lock owned by the class instance."""
    @functools.wraps(f)
    def decorated(self, *args, **kwargs):
        with self._mutex:
            return f(self, *args, **kwargs)
    return decorated


class InteractiveFormatter(pvcheck.formatter.Formatter):
    """Formatter that uses curses to report the result."""

    FOOTER_H = 2  # height of the footer
    MAX_W = 512   # max line length

    COLOR_OK = 1
    COLOR_WARN = 2
    COLOR_ERR = 3

    _RESULT_TABLE = {
        pvcheck.executor.ER_OK: None,
        pvcheck.executor.ER_TIMEOUT: _("TIMEOUT EXPIRED: PROCESS TERMINATED"),
        pvcheck.executor.ER_OUTPUT_LIMIT: _("TOO MANY OUTPUT LINES"),
        pvcheck.executor.ER_SEGFAULT: _("PROCESS ENDED WITH A FAILURE (SEGMENTATION FAULT)"),
        pvcheck.executor.ER_ERROR: ("PROCESS ENDED WITH A FAILURE (ERROR CODE {status})"),
        pvcheck.executor.ER_NOTFILE: _("FAILED TO RUN THE FILE '{progname}' the file does not exist)")
    }

    def __init__(self):
        """Create the interactive formatter."""
        self._reports = []
        self._report_index = 0
        self._screen = None
        self._mutex = threading.Lock()
        self._initialization_barrier = None
        self._sections = []
        self._err_counts = {}
        self._warn_counts = {}
        self._ok_counts = {}
        self._error_count = 0
        self._warn_count = 0
        self._ok_count = 0

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
    def resize_terminal(self):
        self._update()

    @_register_key(curses.KEY_LEFT)
    def previous_report(self):
        self._screen.clear()
        if len(self._reports) > 1:
            self._report_index = max(self._report_index - 1, 1)
        self._update()

    @_register_key(curses.KEY_RIGHT)
    def next_report(self):
        self._screen.clear()
        self._report_index = min(self._report_index + 1, len(self._reports) - 1)
        self._update()

    @_register_key("h", "H", "?")
    def next_report(self):
        self._screen.clear()
        self._show_info(_(HELP_MESSAGE))
        self._screen.clear()
        self._update()

    @_register_key("i", "I")
    def next_report(self):
        self._screen.clear()
        doc = self._reports[self._report_index]
        self._show_info(doc.info())
        self._screen.clear()
        self._update()

    @_register_key("o", "O")
    def next_report(self):
        self._screen.clear()
        doc = self._reports[self._report_index]
        text = _("PROGRAM'S OUTPUT:")
        self._show_info(text + "\n" + doc.output)
        self._screen.clear()
        self._update()

    @_register_key("s", "S")
    def next_report(self):
        self._screen.clear()
        doc = self._reports[self._report_index]
        text = [_("SUMMARY:"), ""]
        for s in self._sections:
            line = "%20s %3d ok  %3d warnings  %3d errors" % (s, self._ok_counts[s], self._warn_counts[s], self._err_counts[s])
            text.append(line)
        text.append(" ")
        self._show_info("\n".join(text))
        self._screen.clear()
        self._update()

    def _thread_body(self):
        """UI thread."""
        curses.wrapper(self._main_loop)

    def _main_loop(self, screen):
        """Main loop managing the interaction with the user."""
        # First setup curses
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
        self._stop = False
        # This reactivate the main thread
        self._initialization_barrier.wait()
        # Event loop
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
        """Add some text in the footer."""
        k = self._text_width() - 1 - len(text)
        pos = max(0, (0 if align == "left" else (k if align == "right" else k //2 )))
        self._footer.addnstr(line, pos, text, self._text_width() - 1 - pos, *extra)

    def _add_short_report(self):
        """Insert ok, warnings, errors counters in the footer."""
        texts = [
            "%3d " % self._ok_count, " %s, " % _("passes"),
            "%3d " % self._warn_count, " %s, " % _("warnings"),
            "%3d " % self._err_count, " %s" % _("errors")
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
        text = _("Test case %d of %d (%s)") % (self._report_index, len(self._reports) - 1, doc.title) + " "
        self._add_footer(0, "left", text)
        text = _("Lines %d-%d/%d") % (doc.top(), doc.bottom(height), doc.length())
        self._add_footer(0, "right", text)
        self._add_short_report()
        if self._running:
            tot = self._err_count + self._warn_count + self._ok_count
            text = _("TEST RUNNING") + "..." + "|/-\\"[tot % 4]
        else:
            text = _("TEST COMPLETED")
        self._add_footer(1, "right", text, curses.A_BOLD)
        self._footer.refresh()

    def _show_info(self, text):
        """Show some text on the screen temporarily disabling the main interface."""
        self._screen.refresh()
        lines = text.splitlines()
        content_pad = curses.newpad(len(lines), 1 + max(map(len, lines)))
        for n, line in enumerate(lines):
            content_pad.addstr(n, 0, line)
        start_line = 0
        while True:
            height, width = self._screen.getmaxyx()
            start_line = max(0, start_line)
            start_line = min(len(lines) - height, start_line)
            content_pad.refresh(start_line, 0, 0, 0, height - 1, width - 1)
            ch = self._screen.getch()
            if ch in (curses.KEY_DOWN, ord("n"), ord("N")):
                start_line += 1
            elif ch in (curses.KEY_UP, ord("p"), ord("P")):
                start_line -= 1
            elif ch == curses.KEY_NPAGE:
                start_line += height
            elif ch == curses.KEY_PPAGE:
                start_line -= height
            elif ch == curses.KEY_END:
                start_line += len(lines)
            elif ch == curses.KEY_HOME:
                start_line = 0
            else:
                break

    # -- Formatter interface --------------------------------------------------
        
    def begin_session(self):
        self._err_count = self._warn_count = self._ok_count = 0
        self._running = True
        # Start the UI thread
        self._initialization_barrier = threading.Barrier(2)
        self._thread = threading.Thread(target=self._thread_body)
        self._thread.start()
        self._initialization_barrier.wait()

    def end_session(self):
        # Wait the termination of the UI thread
        with self._mutex:
            self._running = False
            self._update()
        self._thread.join()

    @_synchronized
    def begin_test(self, description, cmdline_args, input, tempfile):
        description = description or ""
        self._reports.append(Report(description, self.MAX_W, cmdline_args, input, tempfile))
        if self._report_index == 0:
            self._report_index = 1
        self._update()

    @_synchronized
    def end_test(self):
        pass

    @_synchronized
    def execution_result(self, cmdline_args, execution_result, test):
        info = {
            'progname': cmdline_args[0],
            'status': execution_result.status
        }
        message = self._RESULT_TABLE[execution_result.result]
        if execution_result.result != pvcheck.executor.ER_OK:
            self._err_count += 1
            message = message.format(**info)
            for line in message.splitlines():
                self._reports[-1].add_line(line, curses.color_pair(self.COLOR_ERR))
        self._reports[-1].output = execution_result.output
        self._update()

    def _new_section(self, section_name):
        if section_name not in self._sections:
            self._sections.append(section_name)
            self._err_counts[section_name] = 0
            self._warn_counts[section_name] = 0
            self._ok_counts[section_name] = 0

    @_synchronized
    def comparison_result(self, expected, got, diffs, matches):
        add = self._reports[-1].add_line
        all_ok = (max(diffs, default=0) <= 0)
        self._new_section(expected.tag)
        if all_ok:
            self._ok_count += 1
            self._ok_counts[expected.tag] += 1
        else:
            self._err_count += 1
            self._err_counts[expected.tag] += 1
        color = curses.color_pair(self.COLOR_OK if all_ok else self.COLOR_ERR)
        add("[%s]" % expected.tag, color | curses.A_BOLD)

        err_diff = "%s\t\t(" +_("expected") + " '%s')"
        err_un = "%s\t\t(" + _("this line was not expected") + ")"
        err_mis = "\t\t(" + _("missing line") + " '%s'"

        for (i, d) in enumerate(diffs):
            try:
                out_string = pvcheck.formatter.handle_non_printable_chars(got.content[i])
            except IndexError:
                out_string = ''
            if d <= 0:
                # Correct
                add(out_string, curses.color_pair(self.COLOR_OK))
            elif matches[i] is None:
                # Extra line
                add(err_un % out_string, curses.color_pair(self.COLOR_ERR))
            elif i >= len(got.content):
                # Missing line
                add(err_mis % matches[i], curses.color_pair(self.COLOR_ERR))
            else:
                # Mismatching lines

                add(err_diff % (out_string, matches[i]), curses.color_pair(self.COLOR_ERR))
        add("")
        self._update()

    @_synchronized
    def missing_section(self, expected):
        self._new_section(expected.tag)
        self._warn_count += 1
        self._warn_counts[expected.tag] += 1
        message = ("\t\t(" + _("section [%s] is missing") + ")") % expected.tag
        self._reports[-1].add_line(message, curses.color_pair(self.COLOR_WARN))
        self._reports[-1].add_line("")
        self._update()


class Report:
    """Test result displayed on the screen."""

    def __init__(self, title, max_width, cmdline_args="", input="", tempfile=""):
        """Create a new report with the given title.

        Lines are truncated to max_width.
        """
        self.title = title
        self._length = 0
        self._max_width = max_width
        self._pad = curses.newpad(1, max_width)
        self._position = 0
        self._cmdline_args = cmdline_args
        self._input = input
        self._tempfile = tempfile
        self.output = ""

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

    def info(self):
        lines = [_("Test title: %s") % self.title]
        # , "", _("Command line: %s") % " ".join(self._cmdline_args)]
        if self._cmdline_args:
            lines.append("")
            args = [_("TEMP_FILE") if x is pvcheck.executor.ARG_TMPFILE else x for x in self._cmdline_args]
            lines.append(_("Command line: %s") % " ".join(args))
        if self._input and self._input.strip():
            lines.extend(["", _("Input:")])
            lines.extend(self._input.splitlines())
        if self._tempfile:
            lines.extend(["", _("Temporary file:")])
            lines.extend(self._tempfile.splitlines())
        return "\n".join(lines)

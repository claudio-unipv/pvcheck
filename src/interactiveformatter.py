"""Classes that communicate the results."""

import curses
import threading
import formatter
from i18n import translate as _


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


class InteractiveFormatter(formatter.Formatter):
    """Formatter that uses curses to report the result."""

    def __init__(self):
        """Create the interactive formatter."""
        self._reports = []
        self._report_index = 0
        self._screen = None

    @_register_key("q", "Q", 27)  # 27 -> ESC
    def _quit(self):
        self._stop = True

    def _thread_body(self):
        """UI thread."""
        self._stop = False
        curses.wrapper(self._main_loop)

    def _main_loop(self, screen):
        """Main loop managing the interaction with the user."""
        self._screen = screen
        self._update()
        while not self._stop:
            ch = screen.getch()
            _CALLBACKS.get(ch, lambda self: None)(self)

    def _update(self):
        """Redraw everything."""
        self._screen.refresh()
        self._screen.addstr("OK")  # !!!

    def begin_session(self):
        # Start the UI thread
        self._thread = threading.Thread(target=self._thread_body)
        self._thread.start()

    def end_session(self):
        # Wait the termination of the UI thread
        self._thread.join()


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

    def add_line(self, line):
        """Add a line at the bottom of the document."""
        self._pad.resize(self._length + 1, self._max_width)
        self._pad.addnstr(self._length, 0, line, self._max_width)
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

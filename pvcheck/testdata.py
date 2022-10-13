"""Classes defining test cases and test suites."""

from collections import OrderedDict
from itertools import chain
from pvcheck.i18n import translate as _


class Section:
    """A section denoted by a tag and with some content."""
    def __init__(self, tag, content):
        self.tag = tag
        self.content = content

    def copy(self):
        return Section(self.tag, self.content[:])

    def text(self):
        if not self.content:
            return ""
        else:
            return "\n".join(self.content) + "\n"

    def __repr__(self):
        return ("Section('%s')" % self.tag)


class TestCase:
    """A test case with an optional description."""
    def __init__(self, description=None, sections=()):
        """Create a new test case with the given description."""
        self.description = description
        self._sections = OrderedDict()
        self._section_options = {}
        for s in sections:
            self.add_section(s)

    def add_section(self, section):
        """Add a section to the test case.

        If a section with the same tag already exists, then the
        content of the two are merged.  The content of the special
        '.SECTIONS' section is parsed and recorded as the options of
        the test case.

        """
        if section.tag == ".SECTIONS":
            opts = self._parse_section_options(section.content)
            self._section_options.update(opts)
        elif section.tag in self._sections:
            self._sections[section.tag].content.extend(section.content)
        else:
            self._sections[section.tag] = section.copy()

    def find_section(self, tag):
        """Search for a section with the given tag name."""
        return self._sections.get(tag)

    def find_section_content(self, tag, default=""):
        """Search for a section with the given tag name."""
        s = self._sections.get(tag)
        return (s.text() if s is not None else default)

    def section_options(self, tag):
        """Return the special options for a section."""
        return self._section_options.get(tag, set())

    def sections(self, exclude_special=False):
        """Return the sections in the test case.

        Special sections can be excluded.

        """
        if exclude_special:
            return [s for s in self._sections.values() if s.tag and not
                    s.tag.startswith(".")]
        else:
            return list(self._sections.values())

    def _parse_section_options(self, lines):
        opts = dict((s[0], set(s[1:]))
                    for s in (l.split() for l in lines) if s)
        return opts


class TestSuite:
    """A set of test cases.

    Includes an optional prefix of sections, that are replicated for
    each case.

    """

    def __init__(self, sections=()):
        """Create a suite from a sequence of sections."""
        it = self._group_tests(sections)
        prefix = next(it, (None, []))[1]

        self._cases = []
        for testname, secs in it:
            c = TestCase(testname)
            for s in chain(prefix, secs):
                c.add_section(s)
            self._cases.append(c)
        if not self._cases:
            # When no test is found, the prefix becomes a single
            # unnamed test case.
            c = TestCase()
            for s in prefix:
                c.add_section(s)
            self._cases.append(c)

    def test_cases(self):
        """Return the list of test cases in the suite."""
        return self._cases

    def test_case(self, test_number):
        """Return a test case."""
        try:
            if test_number < 0:
                raise IndexError
            test_case = self.test_cases()[test_number]
        except IndexError:
            fmt = _("Test number %d doesn't exist.")
            msg = fmt % (test_number + 1)
            print("\n" + msg + "\n")
            print(_("Use './pvcheck info' to list all the available tests.") + "\n")
            exit(2)
        return test_case

    def _group_tests(self, sections):
        name = None
        lst = []
        n = 0
        for s in sections:
            if s.tag == '.TEST':
                yield (name, lst)
                lst = []
                n += 1
                name = (s.content[0].strip() if len(s.content) > 0
                        else "Test-%d" % n)
            else:
                lst.append(s)
        if n > 0 or lst:
            yield (name, lst)

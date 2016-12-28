"""Classes defining test cases and test suites."""

from collections import OrderedDict
from itertools import chain


class Section:
    """A section denoted by a tag and with some content."""
    def __init__(self, tag, content):
        self.tag = tag
        self.content = content

    def copy(self):
        return Section(self.tag, self.content[:])

    def __repr__(self):
        return ("Section('%s')" % self.tag)


class TestCase:
    """A test case with an optional description."""
    def __init__(self, description=None, sections=None):
        self.description = description
        self.sections = ([] if sections is None else sections)

    def find_section(self, tag, default=None):
        for s in self.sections:
            if s.tag == tag:
                return s
        return default


class TestSuite:
    """A set of test cases.

    Includes an optional prefix of sections, that are replicated for
    each case.

    """
    def __init__(self, sections=()):
        """Create a suite from a sequence of sections."""
        self._cases = []
        self._prefix = []
        dest = self._prefix

        for s in sections:
            if s.tag == ".TEST":
                # Create a new test case
                desc = (s.content[0].strip() if len(s.content) > 0
                        else "Test-%d" % (len(self._cases) + 1))
                self._cases.append(TestCase(desc))
                dest = self._cases[-1].sections
            else:
                # Extend the current test case, or the prefix
                dest.append(s)

        if len(self._cases) == 0:
            # When no test is found, the prefix becomes a single
            # unnamed test case.
            self._cases.append(TestCase(None))
            self._cases[-1].sections = self._prefix
            self._prefix = []

    def __iter__(self):
        """Generate the sequence of test cases.

        The common prefix if included in each generated test case.
        Duplicated sections are merged.

        """

        for case in self._cases:
            sects = OrderedDict()
            for s in chain(self._prefix, case.sections):
                if s.tag not in sects:
                    sects[s.tag] = s.copy()
                else:
                    sects[s.tag].content.extend(s.content)
            yield TestCase(case.description, list(sects.values()))


if __name__ == '__main__':
    import doctest
    doctest.testfile("../test/testdata.txt")

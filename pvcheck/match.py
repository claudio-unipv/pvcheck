"""Matching functions.

Used to compare the expected and the actual outputs.
"""

import re
from itertools import zip_longest


_RE_INT = re.compile(r'(-|\+)?[0-9]+')
_RE_REAL = re.compile(r'(-|\+)?[0-9]+\.(?P<frac>[0-9]*)')


def compare_sections(actual, expected, ordered=True):
    """Compare the content of two sections.

    The 'ordered' parameter indicates whether or not the order of the
    expected lines matter.  The function returns a pair of lists: a
    list of differences and a list of matches.

    The list of difference contains difference measures between given
    and expected lines of text (with 0 being a perfect match).

    The list of matches contains elements from the 'expected' section,
    in the order in which they have been matched to the elements of
    the 'actual' section.  The lists may contain 'None' values when
    actual lines have not been successfully matched.  The list cannot
    be shorter than the first parameter, but may also be longer when
    expected lines are not matched.  When 'ordered' is True this list
    is a copy of the elements in 'expected', possibly with trailing
    Nones.

    In practice a call to zip_longest with the 'actual' lines and the
    returned matches would produce a side-by-side comparison of the
    matched lines, with None values filling the holes.

    """
    if ordered:
        matched = list(expected)
        diffs = _compare_ordered_sections(actual, matched)
        matched.extend([None] * (len(actual) - len(matched)))
    else:
        diffs, matched = _compare_unordered_sections(actual, expected)
    return (diffs, matched)


def _compare_elements(value, expected):
    """Compare a pair of elements.

    Return true if value matches expected value.  The type of
    comparison (numerical with a set precision or textual) is inferred
    from the expected value.

    """
    m = _RE_REAL.fullmatch(expected)
    if m is not None:
        # If the expected value is a fractional number, compare the
        # result up to the given number of digits.
        digits = len(m.group('frac'))
        try:
            return float(expected) == round(float(value), digits)
        except ValueError:
            return False
    elif _RE_INT.fullmatch(expected):
        # If the expected value is an integer, compare by value so
        # that 15, +15 and 015 are considered as equivalent.
        try:
            return int(expected) == int(value)
        except ValueError:
            return False
    else:
        # In the general case just compare the strings.
        return (value == expected)


def _compare_lines(actual, expected):
    """Return the difference between the given and the expected lines.

    The result is in the range [0, 1], with 0 denoting a perfect
    match.

    """
    act = actual.split()
    exp = expected.split()
    ok = sum(1 for a, e in zip(act, exp) if _compare_elements(a, e))
    den = max(len(act), len(exp))
    return float(den - ok) / max(den, 1)


def _compare_ordered_sections(actual, expected):
    """Compare the content of two sections.

    The result is a list of distance measures between pairs of actual
    and expected lines.  The length of the list is the same of the
    longest of the two sections.

    """
    return [1.0 if x[0] is None or x[1] is None
            else _compare_lines(x[0], x[1])
            for (i, x) in enumerate(zip_longest(actual, expected))]


def _compare_unordered_sections(actual, expected):
    """Compare two sections without considering the order of their lines.

    The result is a pair of lists: the first list contains the
    distance measures between pairs of actual and expected lines.  The
    second list contains the expected lines reordered to match the
    actual ones, possibily with the inclusion of additional None
    values where no match is found.  The tow lists have the same
    length.

    """
    expected = set(enumerate(expected))
    diffs = []
    ordered = []
    for x in actual:
        for (n, y) in expected:
            d = _compare_lines(x, y)
            if d == 0:
                diffs.append(d)
                ordered.append(y)
                expected.remove((n, y))
                break
        else:
            diffs.append(1.0)
            ordered.append(None)
    for (n, y) in sorted(expected):
        diffs.append(1.0)
        ordered.append(y)
    return (diffs, ordered)

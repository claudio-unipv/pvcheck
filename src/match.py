"""Matching functions.

Used to compare the expected and the actual outputs.
"""

import re
from itertools import count, zip_longest


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


if __name__ == "__main__":
    import doctest
    doctest.testfile("../test/match.txt")


# def check_unordered_section(key, lines, target, maxerrors=None):
#     """Compare the two sets of lines disregarding their order.

#     Print messages to show matches and mismatches.

#     Return the number of errors (this is going to change).
#     """

#     fmt = "%-30s| %-30s"
#     _log.debug(_("detailed comparison"), extra={'section':key})
#     _log.debug(fmt % (_("EXPECTED OUTPUT"), _("ACTUAL OUTPUT")))

#     def dbg(t, r):
#         t = t.rstrip() if t is not None else _("<nothing>")
#         r = r.rstrip() if r is not None else _("<nothing>")
#         if len(t) > 30:
#             t = t[:26] + "..."
#         if len(r) > 30:
#             r = r[:26] + "..."
#         fmt = "%-30s| %-30s"
#         _log.debug(fmt % (t, r))

#     if maxerrors is None:
#         maxerrors = len(lines) + len(target)
#     errors = []
#     if len(lines) != len(target):
#         fmt = _("wrong number of lines (expected %d, got %d)")
#         errors.append(fmt % (len(target), len(lines)))

#     lines = set(lines)
#     for i, t in enumerate(target):
#         found = None
#         for r in lines:
#             if check_line(r, t):
#                 found = r
#                 dbg(t, r)
#                 lines.remove(found)
#                 break
#         else:
#             fmt = _("missing line (expected '%s')")
#             errors.append(fmt % t.strip())
#             dbg(t, None)
#     for r in lines:
#         fmt = _("unexpected line '%s'")
#         errors.append(fmt % r.strip())
#         dbg(None, r)

#     for e in errors[:maxerrors]:
#         _log.error(e, extra={'section':key})
#     if len(errors) > maxerrors:
#         _log.error(_("(... plus other %d errors ...)") %
#                   (len(errors) - maxerrors),
#                   extra={'section':key})
#     return len(errors)




# def check_ordered(key, lines, target, maxerrors=None):
#     """Line by line comparison of result and target.

#     Print messages to show matches and mismatches.

#     Return the number of errors (this is going to change).
#     """
#     if maxerrors is None:
#         maxerrors = len(result) + len(target)
#     num_errs = 0

#     fmt = "%-30s| %-30s"
#     _log.debug(_("detailed comparison"), extra={'section':key})
#     _log.debug(fmt % (_("EXPECTED OUTPUT"), _("ACTUAL OUTPUT")))

#     if len(lines) != len(target):
#         num_errs += 1
#     mm = check_lines(lines, target)
#     wd_output = check_wdiff(lines, target)
#     if wd_output['code'] in (0, 1):
#         similarity = parse_wdiff_output(str(wd_output['output']))
#     else:
#         similarity = None

#     if len(mm) > 0:
#         num_errs = len(mm)

#     ret = {
#         'code': num_errs,
#         'wrong lines': mm,
#         'generated': lines,
#         'expected': target,
#         'similarity': similarity
#     }
#     return ret

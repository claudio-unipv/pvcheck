"""Matching functions.

Used to compare the expected and the actual outputs.
"""

import re
import tempfile
import logging
import subprocess
import i18n
from itertools import count

_ = i18n.translate

_log = logging.getLogger()

RE_INT = re.compile(r'(-|\+)?[0-9]+')
RE_REAL = re.compile(r'(-|\+)?[0-9]+\.(?P<frac>[0-9]*)')
RE_NUMBER = re.compile(r'(-|\+)?[0-9]+(\.[0-9]*)')


def check_element(value, target):
    """Compare single elements.

    Return true if value matches target.  The type of comparison
    (numerical with a set precision or textual) is inferred from the
    target value.

    """
    m = RE_REAL.fullmatch(target)
    if m is not None:
        # If the target is a fractional number, compare the result up
        # to the given number of digits.
        digits = len(m.group('frac'))
        try:
            return float(target) == round(float(value), digits)
        except ValueError:
            return False
    elif RE_INT.fullmatch(target):
        # If the target is an integer, compare by value so that 15,
        # +15 and 015 are considered as equivalent.
        try:
            return int(target) == int(value)
        except ValueError:
            return False
    else:
        # In the general case just compare the strings.
        return (value == target)


def check_line(line, target):
    """Compare the result line with the expected target."""
    line_elts = line.split()
    target_elts = target.split()
    return (len(line_elts) == len(target_elts)
            and all(map(check_element, line_elts, target_elts)))


def check_lines(section, target):
    """Compare the content of a section with the expected target.

    [str],[str] -> [ (int, str, str) ]

    Return the list of non-matching triplets (line_number, given_line,
    expected_line)

    """
    diffs = []
    for (i, line, target_line) in zip(count(), section, target):
        if not check_line(line, target_line):
            diffs.append((i, line.strip(), target_line.strip()))
    return diffs


def check_unordered_section(key, lines, target, maxerrors=None):
    """Compare the two sets of lines disregarding their order.

    Print messages to show matches and mismatches.

    Return the number of errors (this is going to change).
    """

    fmt = "%-30s| %-30s"
    _log.debug(_("detailed comparison"), extra={'section':key})
    _log.debug(fmt % (_("EXPECTED OUTPUT"), _("ACTUAL OUTPUT")))

    def dbg(t, r):
        t = t.rstrip() if t is not None else _("<nothing>")
        r = r.rstrip() if r is not None else _("<nothing>")
        if len(t) > 30:
            t = t[:26] + "..."
        if len(r) > 30:
            r = r[:26] + "..."
        fmt = "%-30s| %-30s"
        _log.debug(fmt % (t, r))

    if maxerrors is None:
        maxerrors = len(lines) + len(target)
    errors = []
    if len(lines) != len(target):
        fmt = _("wrong number of lines (expected %d, got %d)")
        errors.append(fmt % (len(target), len(lines)))

    lines = set(lines)
    for i, t in enumerate(target):
        found = None
        for r in lines:
            if check_line(r, t):
                found = r
                dbg(t, r)
                lines.remove(found)
                break
        else:
            fmt = _("missing line (expected '%s')")
            errors.append(fmt % t.strip())
            dbg(t, None)
    for r in lines:
        fmt = _("unexpected line '%s'")
        errors.append(fmt % r.strip())
        dbg(None, r)

    for e in errors[:maxerrors]:
        _log.error(e, extra={'section':key})
    if len(errors) > maxerrors:
        _log.error(_("(... plus other %d errors ...)") %
                  (len(errors) - maxerrors),
                  extra={'section':key})
    return len(errors)


def parse_wdiff_output(wd_str):
    """Generic function to parse wdiff -s output"""
    tokens = wd_str.split()
    n1 = float(tokens[4][:-1])
    n2 = float(tokens[15][:-1])
    return (n1 + n2) / 2


def check_wdiff(res, target):
    file_text = ("\n".join(res))
    tmpfile1 = tempfile.NamedTemporaryFile(suffix=".res.pvcheck.tmp",
                                          delete=False)
    tmpfile1.write(file_text.encode('utf8'))
    tmpfile1.close()

    file_text = ("\n".join(target))
    tmpfile2 = tempfile.NamedTemporaryFile(suffix=".target.pvcheck.tmp",
                                          delete=False)
    tmpfile2.write(file_text.encode('utf8'))
    tmpfile2.close()

    ret = {}
    try:
        p = subprocess.Popen(['wdiff', '-s123', tmpfile1.name,
                              tmpfile2.name],
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, bufsize=-1)
        output, error = p.communicate()
        ret['code'] = p.returncode
        if p.returncode <= 1:
           ret['output'] = str(output)
        else:
           ret['output'] = "Error occurred in wdiff"
        _log.debug("wdiff: " + str(((output, p.returncode))))
    except FileNotFoundError:
        _log.debug("wdiff: command not found")
        ret['code'] = -1
        ret['output'] = "wdiff command not found"

    return ret


def check_ordered(key, lines, target, maxerrors=None):
    """Line by line comparison of result and target.

    Print messages to show matches and mismatches.

    Return the number of errors (this is going to change).
    """
    if maxerrors is None:
        maxerrors = len(result) + len(target)
    num_errs = 0

    fmt = "%-30s| %-30s"
    _log.debug(_("detailed comparison"), extra={'section':key})
    _log.debug(fmt % (_("EXPECTED OUTPUT"), _("ACTUAL OUTPUT")))

    if len(lines) != len(target):
        num_errs += 1
    mm = check_lines(lines, target)
    wd_output = check_wdiff(lines, target)
    if wd_output['code'] in (0, 1):
        similarity = parse_wdiff_output(str(wd_output['output']))
    else:
        similarity = None
    
    if len(mm) > 0:
        num_errs = len(mm)

    ret = {
        'code': num_errs,
        'wrong lines': mm,
        'generated': lines,
        'expected': target,
        'similarity': similarity
    }
    return ret

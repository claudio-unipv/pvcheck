"""Parse text representing sections."""

import re
import pvcheck.testdata


# Any character is allowed before '[', otherwise the header will be
# missed after a scanf (or other input) where the newline is taken
# from the stdin and is not part of the stdout.  In practice, the
# condition to deal with is 
#
# ...
# printf("Enter n: ");
# scanf("%d", &n);
# printf("[SECTION]\n%d\n", n);
# ...
#
# whose output is:
#
# Enter n:  [SECTION]
# 42
#
_RE_HEADER = re.compile(r"[^[]*\[\s*(?P<tag>[-._a-zA-Z][-._\w]*)\s*\]\s*")


def parse_sections(f):
    """Parse the lines in f and generates sections.

    When non-empty lines are found before the first section header,
    they are placed into a section with an empty name.

    """
    content = []
    tag = ""
    for line in f:
        l = line.strip()
        if not l or l[0] == '#':
            continue  # Skip empty lines and comments
        m = _RE_HEADER.match(line)
        if m:
            if tag != "" or len(content) > 0:
                yield pvcheck.testdata.Section(tag, content)
            # A new section
            tag = m.group("tag")
            content = []
        else:
            content.append(line.rstrip())
    if tag != "" or len(content) > 0:
        yield pvcheck.testdata.Section(tag, content)

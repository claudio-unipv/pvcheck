import re
import testdata


RE_HEADER = re.compile(r"\s*\[\s*(?P<tag>[._a-zA-Z][._\w]*)\s*\]\s*")


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
        m = RE_HEADER.match(line)
        if m:
            if tag != "" or len(content) > 0:
                yield testdata.Section(tag, content)
            # A new section
            tag = m.group("tag")
            content = []
        else:
            content.append(line)
    yield testdata.Section(tag, content)

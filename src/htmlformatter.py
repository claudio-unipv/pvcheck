"""Formatter producing HTML data"""
from jsonformatter import JSONFormatter


class HTMLFormatter(JSONFormatter):

    def end_session(self):
        print("""<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8">
        <title>PvCheck Result</title>
        <link href="minimal-table.css" rel="stylesheet" type="text/css">
    </head>
    <body>
        <table align="center">
            <tr>""")

        header = self._header_builder()

        for head in header:
            print("                <th>{}</th>".format(head))

        print("            </tr>")

        i = 0
        for test in self._tests:
            row = self._row_builder(test, header)
            print("            <tr>")
            if len(self._tests) > 1:
                print('                <td><a href="#{}">{}</a></td>'.format(row[0], row[0]))
                i = 1
            for element in row[i:]:
                if element == "ok":
                    color = "green"
                elif element == "error":
                    color = "red"
                elif element == "missing":
                    color = "orange"
                else:
                    color = "black"
                print('                <td><font color="{}">{}</font></td>'.format(color, element))
            print("            </tr>")
        print("        </table>")
        print("    </body>")
        print('</html>')

    def _header_builder(self):
        """Build the header.

        If there is only a test omits the header 'TEST'.

        """
        if len(self._tests) > 1:
            header = ["TEST"]
        else:
            header = []
        for test in self._tests:
            section_names = list(test["sections"].keys())
            for name in section_names:
                if name not in header:
                    header.append(name)
        return header

    def _row_builder(self, test, header):
        """Build a row.

        If there is only a test omits the test's name.

        """
        if len(self._tests) > 1:
            row = [test["title"]]
        else:
            row = []
        for element in header:
            if element != "TEST":
                try:
                    row.append(test["sections"][element]["section status"])
                except KeyError:
                    row.append("")
        return row

"""Formatter producing HTML data"""
from jsonformatter import JSONFormatter


class HTMLFormatter(JSONFormatter):

    def end_session(self):
        self.initial_printing()
        self.print_tests_table()
        print("        <hr>")
        print("    </body>")
        print('</html>')

    @staticmethod
    def initial_printing():
        print("""<!DOCTYPE html>
        <html>
            <head>
                <meta charset="utf-8">
                <title>PvCheck Result</title>
                <style rel="stylesheet" type="text/css">
                    html {
                      font-family: sans-serif;
                    }

                    table {
                      border-collapse: collapse;
                      border: 2px solid rgb(200,200,200);
                      letter-spacing: 1px;
                      font-size: 0.8rem;
                    }

                    td, th {
                      border: 1px solid rgb(190,190,190);
                      padding: 10px 20px;
                    }

                    th {
                      background-color: rgb(235,235,235);
                    }

                    td {
                      text-align: center;
                    }

                    tr:nth-child(even) td {
                      background-color: rgb(250,250,250);
                    }

                    tr:nth-child(odd) td {
                      background-color: rgb(245,245,245);
                    }

                    caption {
                      padding: 10px;
                    }
                </style>
            </head>
            <body>""")

    def print_tests_table(self):
        print('                <table align="center">')
        print('                    <tr>')
        tests_table_header = self._tests_table_header_builder()
        self._print_tests_table_header(tests_table_header)
        self._print_tests_table_rows(tests_table_header)
        print("        </table>")

    def _tests_table_header_builder(self):
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

    @staticmethod
    def _print_tests_table_header(tests_table_header):
        for element in tests_table_header:
            print("                <th>{}</th>".format(element))
        print("            </tr>")

    def _print_tests_table_rows(self, tests_table_header):
        i = 0
        for test in self._tests:
            row = self._test_table_row_builder(test, tests_table_header)
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

    def _test_table_row_builder(self, test, header):
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

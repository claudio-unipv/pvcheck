"""Formatter producing HTML data"""

from jsonformatter import JSONFormatter

_trans_dic = {"\n": "<br>", "–": "&ndash;", "—": "&mdash;", "&": "&amp;", ">": "&gt;", "<": "&lt;"}
_trantab = str.maketrans(_trans_dic)

section_summary = {}
total_summary = {"ok": 0, "warning": 0, "error": 0}


class HTMLFormatter(JSONFormatter):
    def end_session(self):

        header = self._tests_table_header_builder()
        for element in header:
            if element != "TEST":
                section_summary[element] = {"ok": 0, "warning": 0, "error": 0}

        self.initial_printing()
        self.print_tests_table()
        self.print_tests_information()
        self.print_summary_table()
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
            print("                <th>{}</th>".format(element.translate(_trantab)))
        print("            </tr>")

    def _print_tests_table_rows(self, tests_table_header):
        if len(self._tests) > 1:
            print_test_name = True
            first_element_index = 1
        else:
            print_test_name = False
            first_element_index = 0
        for test in self._tests:
            row = self._test_table_row_builder(test, tests_table_header)
            print("            <tr>")
            if print_test_name:
                print('                <td><a href="#{}">{}</a></td>'.format(row[0].translate(_trantab),
                                                                             row[0].translate(_trantab)))
            for element in row[first_element_index:]:
                if element == "ok":
                    color = "green"
                elif element == "error":
                    color = "red"
                elif element == "missing":
                    color = "orange"
                else:
                    color = "black"
                print('                <td><font color="{}">{}</font></td>'.format(color, element.translate(_trantab)))
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

    def print_tests_information(self):
        if self._tests[0]["error_message"] != "ok":
            print("        <hr>")
            print("        <p><font color='red'>{}</font></p>".format(self._tests[0]["error_message"]))
            print("        <hr>")
            print("    </body>")
            print('</html>')
            exit(0)
        header = self._tests_table_header_builder()
        for test in self._tests:
            print("        <hr>")
            if len(self._tests) > 1:
                print('        <p><a name="{}"><b>Test:</b> {}</a><br>'.format(test["title"].translate(_trantab),
                                                                        test["title"].translate(_trantab)))
            command_line = ""
            for element in test["command_line"]:
                command_line += " " + element
            print('           <b>Riga di comando:</b> {}<br>'.format(command_line.translate(_trantab)))
            if len(test["input_text"]) > 0:
                print('            <b>Input:</b> {}<br>'.format(test["input_text"].translate(_trantab)))
            if test["input_file_name"] is not None:
                if test["input_file_name"] == "<temp.file>":
                    input_file_name = "File Temporaneo"
                else:
                    input_file_name = test["input_file_name"]

                print('            <b>{}:</b><br> {}<br>'.format(input_file_name.translate(_trantab),
                                                          test["file_text"].translate(_trantab)))
            for section in header:
                if section != "TEST":
                    if test["sections"][section]["section status"] == "ok":

                        section_summary[section]["ok"] += 1
                        total_summary["ok"] += 1

                        msg = "OK"
                        color = "green"
                        print('            <b><font color="{}">{}: </b>{}</font><br>'.format(color, section, msg))
                    elif test["sections"][section]["section status"] == "error":

                        section_summary[section]["error"] += 1
                        total_summary["error"] += 1

                        for wrong_line in test["sections"][section]['wrong_lines']:
                            if wrong_line[2] is None:
                                msg = "riga {} inattesa".format(wrong_line[0] + 1)
                            elif wrong_line[1] is None:
                                msg = "riga mancante (atteso '{}')".format(wrong_line[0] + 1, wrong_line[2])
                            else:
                                msg = "riga {} errata (atteso '{}', ottenuto '{}')".format(wrong_line[0] + 1, wrong_line[2],
                                                                                           wrong_line[1])
                            color = "red"
                            print('            <b><font color="{}">{}: </b>{}</font><br>'.format(color, section, msg))
                    else:

                        section_summary[section]["warning"] += 1
                        total_summary["warning"] += 1

                        msg = "missing section"
                        color = "orange"
                        print('            <b><font color="{}">{}: </b>{}</font><br>'.format(color, section, msg))

            print('        </p>')
        print("        <hr>")

    def print_summary_table(self):
        self._print_summary_table_header()
        header = self._tests_table_header_builder()
        for section in header:
            if section != "TEST":
                print("            <tr>")
                print('                <td>{}</td>'.format(section))
                print('                <td>{}</td>'.format(section_summary[section]["ok"]))
                print('                <td>{}</td>'.format(section_summary[section]["warning"]))
                print('                <td>{}</td>'.format(section_summary[section]["error"]))
                print("            </tr>")

        print("            <tr>")
        print('                <td>{}</td>'.format("TOTAL"))
        print('                <td>{}</td>'.format(total_summary["ok"]))
        print('                <td>{}</td>'.format(total_summary["warning"]))
        print('                <td>{}</td>'.format(total_summary["error"]))
        print("            </tr>")

        print("        </table>")

    @staticmethod
    def _print_summary_table_header():
        print("""        <table align="center">
            <tr>
                <th>&nbsp;</th>
                <th><font color= "green">Success</font></th>
                <th><font color = "orange">Warning</font></th>
                <th><font color = "red">Errors</font></th>
            </tr>""")


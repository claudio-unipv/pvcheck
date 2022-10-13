"""Formatter producing HTML data"""

from pvcheck.jsonformatter import JSONFormatter
import pvcheck.i18n


_ = pvcheck.i18n.translate
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

        self.print_html_header()
        self.print_tests_table()
        self.print_tests_information()
        self.print_summary_table()
        print("    </body>")
        print('</html>')

    @staticmethod
    def print_html_header():
        """Print header and style."""
        print("""<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8">
        <title>PvCheck Result</title>
        <style rel="stylesheet" type="text/css">

            html {
              font-family: sans-serif;
            }
            
            h1 {
             overflow: hidden;
             text-align: center;
            }
            h1:before,
            h1:after {
             background-color: #333;
             content: "";
             display: inline-block;
             height: 1px;
             position: relative;
             vertical-align: middle;
             width: 50%;
            }
            h1:before {
             right: 0.5em;
             margin-left: -50%;
            }
            h1:after {
             left: 0.5em;
             margin-right: -50%;
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
        print("""       <h1>PvCheck</h1>
        <ul>
            <li><a href="#summary">{}</a></li>
            <li><a href="#info">info</a></li>
        </ul>""".format(_("summary")))

    def print_tests_table(self):
        """Print a table containing tests' results."""
        print('        <h2 align="center">{}</h2>'.format(_("Test Result")))
        print('        <table align="center">')
        print('            <tr>')

        tests_table_header = self._tests_table_header_builder()

        self._print_tests_table_header(tests_table_header)
        self._print_tests_table_rows(tests_table_header)

        print("        </table>")
        print("        <br>")

    def _tests_table_header_builder(self):
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
            self._print_test_table_row(print_test_name, first_element_index, row)

    def _test_table_row_builder(self, test, header):
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

    def _print_test_table_row(self, print_test_name, first_element_index, row):
        print("            <tr>")
        if print_test_name:
            print('                <td><a href="#{}">{}</a></td>'.format(row[0].translate(_trantab),
                                                                         row[0].translate(_trantab)))
        for element in row[first_element_index:]:
            self._print_section_status(element)
        print("            </tr>")

    @staticmethod
    def _print_section_status(section):
        if section == "ok":
            color = "green"
        elif section == "error":
            color = "red"
        elif section == "exec_error":
            section = "execution failed"
            color = "red"
        elif section == "missing":
            color = "orange"
        else:
            color = "black"
        print('                <td><font color="{}">{}</font></td>'.format(color, section.translate(_trantab)))

    def print_tests_information(self):
        """Print a section for each test containing results' information."""
        print('        <h2><a name="info">Info</a></h2>')
        if self._tests[0]["error_message"] != "ok":
            self._print_error_message()
            exit(0)
        header = self._tests_table_header_builder()
        for test in self._tests:
            self._print_test_information(test, header)
        print("        <hr>")

    def _print_error_message(self):
        print("        <hr>")
        print("        <p><font color='red'>{}</font></p>".format(self._tests[0]["error_message"]))
        print("        <hr>")
        print("    </body>")
        print('</html>')

    def _print_test_information(self, test, sections):
        print("        <hr>")
        if len(self._tests) > 1:
            self._print_test_name(test)
        self._print_command_line(test)
        if len(test["input_text"]) > 0:
            self._print_input_text(test)
        if test["input_file_name"] is not None:
            self._print_input_file_name(test)
        for section in sections:
            if section != "TEST":
                self._print_section_status_message(test, section)
        print('        </p>')

    @staticmethod
    def _print_test_name(test):
        print('        <p><a name="{}"><b>TEST:</b> {}</a><br>'.format(test["title"].translate(_trantab),
                                                                       test["title"].translate(_trantab)))

    @staticmethod
    def _print_command_line(test):
        command_line = ""
        for element in test["command_line"]:
            command_line += " " + element
        print('            <b>{}:</b> {}<br>'.format(_("COMMAND LINE"), command_line.translate(_trantab)))

    @staticmethod
    def _print_input_text(test):
        print('            <b>INPUT:</b> {}<br>'.format(test["input_text"].translate(_trantab)))

    @staticmethod
    def _print_input_file_name(test):
        if test["input_file_name"] == "<temp.file>":
            input_file_name = _("TEMPORARY FILE")
        else:
            input_file_name = test["input_file_name"]

        print('            <b>{}:</b><br> {}<br>'.format(input_file_name.translate(_trantab),
                                                         test["file_text"].translate(_trantab)))

    def _print_section_status_message(self, test, section):
        if test["sections"][section]["section status"] == "ok":
            section_summary[section]["ok"] += 1
            total_summary["ok"] += 1
            self._print_section_ok_message(section)
        elif test["sections"][section]["section status"] == "error":
            section_summary[section]["error"] += 1
            total_summary["error"] += 1
            for wrong_line in test["sections"][section]['wrong_lines']:
                self._print_section_error_message(wrong_line, section)
        elif test["sections"][section]["section status"] == "exec_error":
            section_summary[section]["error"] += 1
            total_summary["error"] += 1
            self._print_section_exec_error_message(section)
        else:
            section_summary[section]["warning"] += 1
            total_summary["warning"] += 1
            self._print_section_warning_message(section)

    @staticmethod
    def _print_section_ok_message(section):
        msg = "OK"
        color = "green"
        print('            <b><font color="{}">{}: </b>{}</font><br>'.format(color, section, msg))

    @staticmethod
    def _print_section_error_message(wrong_line, section):
        if wrong_line[2] is None:
            msg = _("unexpected line '%s'") % (wrong_line[0] + 1)
        elif wrong_line[1] is None:
            msg = _("missing line (expected '%s')") % (wrong_line[2])
        else:
            msg = _("line %d is wrong  (expected '%s', got '%s')") % (wrong_line[0] + 1, wrong_line[2],
                                                                      wrong_line[1])
        color = "red"
        print('            <b><font color="{}">{}: </b>{}</font><br>'.format(color, section, msg))

    @staticmethod
    def _print_section_exec_error_message(section):
        msg = _("execution failed")
        color = "red"
        print('            <b><font color="{}">{}: </b>{}</font><br>'.format(color, section, msg))

    @staticmethod
    def _print_section_warning_message(section):
        msg = _("missing section")
        color = "orange"
        print('            <b><font color="{}">{}: </b>{}</font><br>'.format(color, section, msg))

    def print_summary_table(self):
        """Print a test summary table."""
        self._print_summary_table_header()
        header = self._tests_table_header_builder()
        for section in header:
            if section != "TEST":
                self._print_section_summary_row(section)
        self._print_total_summary_row()
        print("        </table>")

    @staticmethod
    def _print_summary_table_header():
        print("""        <a name="summary"><h2 align="center">{}</h2>
        <table align="center">
            <tr>
                <th>&nbsp;</th>
                <th><font color= "green">{}</font></th>
                <th><font color = "orange">{}</font></th>
                <th><font color = "red">{}</font></th>
            </tr>""".format(_("Summary"), _("Successes"), _("Warnings"), _("Errors")))

    @staticmethod
    def _print_section_summary_row(section):
        print("            <tr>")
        print('                <td>{}</td>'.format(section))
        print('                <td>{}</td>'.format(section_summary[section]["ok"]))
        print('                <td>{}</td>'.format(section_summary[section]["warning"]))
        print('                <td>{}</td>'.format(section_summary[section]["error"]))
        print("            </tr>")

    @staticmethod
    def _print_total_summary_row():
        print("            <tr>")
        print('                <td>{}</td>'.format(_("TOTAL")))
        print('                <td>{}</td>'.format(total_summary["ok"]))
        print('                <td>{}</td>'.format(total_summary["warning"]))
        print('                <td>{}</td>'.format(total_summary["error"]))
        print("            </tr>")

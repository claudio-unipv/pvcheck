from i18n import translate as _


def export(test, test_index):
    output_file_name = _file_name_builder(test.description)
    _input, _file = _get_data(test)
    if (_input is not None) or (_file is not None):
        with open(output_file_name, 'w') as f:
            _write_data(f, _input, _file)
        exit(0)
    else:
        _print_error_message(test_index)
        exit(1)


def _file_name_builder(test_name):
    try:
        file_name = (test_name + ".dat").replace(' ', '_')
    except TypeError:
        file_name = ("NoName" + ".dat")
    return file_name


def _get_data(test):
    _input = test.find_section_content(".INPUT", None)
    _file = test.find_section_content(".FILE", None)
    return _input, _file


def _write_data(output_file, _input, _file):
    if _input is not None:
        output_file.write(_input)
    if _file is not None:
        output_file.write(_file)


def _print_error_message(test_index):
    fmt = _("Error: Can't export test number %d.")
    msg = fmt % (test_index + 1)
    print("\n" + msg + "\n")

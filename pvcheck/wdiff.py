import tempfile
import logging
import subprocess

_log = logging.getLogger()


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

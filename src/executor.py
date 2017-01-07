"""Execution of the child process."""


import subprocess
import contextlib
import tempfile
import signal
import os
import collections


# Execution results
ER_OK = "ER_OK"
ER_TIMEOUT = "ER_TIMEOUT"
ER_SEGFAULT = "ER_SEGFAULT"
ER_ERROR = "ER_ERROR"
ER_NOTFILE = "ER_NOTFILE"

# Placeholder for the name of the temporary file
ARG_TMPFILE = object()


@contextlib.contextmanager
def _make_temp_file(content):
    tmp = tempfile.NamedTemporaryFile(
        mode="wt",
        suffix=".pvcheck.tmp",
        delete=False
    )
    name = tmp.name
    try:
        tmp.write(content)
        tmp.close()
        yield name
    finally:
        os.remove(name)


def _replace_placeholder(args, name):
    return [(name if a is ARG_TMPFILE else a) for a in args]


ExecResult = collections.namedtuple(
    'ExecResult', ['result', 'status', 'output']
)


def exec_process(args, input, tmpfile=None, timeout=None):
    """Execute a process.

    Parameters:
      args    - list of arguments (the first being the process name)
      input   - text to be sent on the standard input
      tmpfile - optional temporary file (can be None)
      timeout - in seconds, None for unlimited time

    When one of the arguments is the placehoder 'ARG_TMPFILE' it gets
    replaced by the name of a temporary file having the content
    specified by the tmpfile parameter.

    Return an ExecResult object, that is, a named tuple with the
    result of the execution, the status code of the terminated
    process, and the output produced by the process.

    """
    with contextlib.ExitStack() as stack:
        if tmpfile is not None:
            tmpname = stack.enter_context(_make_temp_file(tmpfile))
            args = _replace_placeholder(args, tmpname)
        kwargs = dict(input=input.encode('utf8'),
                      timeout=timeout)
        ret_code = 0
        er = ER_OK
        output = bytes()
        try:
            output = subprocess.check_output(args, **kwargs)
        except subprocess.TimeoutExpired as e:
            er = ER_TIMEOUT
            output = e.output
        except subprocess.CalledProcessError as e:
            ret_code = e.returncode
            output = e.output
            er = (ER_SEGFAULT if e.returncode == -signal.SIGSEGV
                  else ER_ERROR)
        except FileNotFoundError:
            er = ER_NOTFILE
    output = str(output, 'utf-8', errors='replace')
    return ExecResult(er, ret_code, output)


if __name__ == "__main__":
    import doctest
    doctest.testfile("../test/executor.txt")

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
    tmp = tempfile.NamedTemporaryFile(mode="wt",
                                      suffix=".pvcheck.tmp",
                                      delete=False)
    name = tmp.name
    try:
        tmp.write(content)
        tmp.close()
        yield name
    finally:
        os.remove(name)


ExecResult = collections.namedtuple(
    'ExecResult', ['result', 'status', 'output', 'stderr']
)


class Executor:
    """Class capable of executing a process."""
    
    def exec_process(self, args, input, tmpfile=None, timeout=None):
        """Execute a process.

        Parameters:
        args    - list of arguments (the first being the process name)
        input   - text to be sent on the standard input
        tmpfile - optional temporary file (can be None)
        timeout - in seconds, None for unlimited time

        When one of the arguments is the placehoder 'ARG_TMPFILE' it
        gets replaced by the name of a temporary file having the
        content specified by the tmpfile parameter.

        Return an ExecResult object, that is, a named tuple with the
        result of the execution, the status code of the terminated
        process, and the output produced by the process.

        """
        with contextlib.ExitStack() as stack:
            if tmpfile is not None:
                tmpname = stack.enter_context(_make_temp_file(tmpfile))
                args = self._replace_placeholder(args, tmpname)
            output = ""
            error = ""
            ret_code = 0
            try:
                proc = subprocess.Popen(args,
                                        universal_newlines=True,
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
                output, error = proc.communicate(input, timeout)
                codes = {0: ER_OK, -signal.SIGSEGV: ER_SEGFAULT}
                er = codes.get(proc.returncode, ER_ERROR)
                ret_code = proc.returncode
            except subprocess.TimeoutExpired:
                er = ER_TIMEOUT
                proc.kill()
                proc.stdin.close()
                proc.stdout.close()
                proc.stderr.close()
            except FileNotFoundError:
                er = ER_NOTFILE
            
        return ExecResult(er, ret_code, output, error)

    def _replace_placeholder(self, args, name):
        return [(name if a is ARG_TMPFILE else a) for a in args]



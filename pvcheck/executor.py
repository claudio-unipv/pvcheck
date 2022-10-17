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
ER_OUTPUT_LIMIT = "ER_OUTPUT_LIMIT"
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
    
    def exec_process(self, args, input, tmpfile=None, timeout=None,
                     output_limit=None):
        """Execute a process.

        Parameters:
        args    - list of arguments (the first being the process name)
        input   - text to be sent on the standard input
        tmpfile - optional temporary file (can be None)
        timeout - in seconds, None for unlimited time
        output_limit - maximum number of output lines, None if unlimited

        When one of the arguments is the placehoder 'ARG_TMPFILE' it
        gets replaced by the name of a temporary file having the
        content specified by the tmpfile parameter.

        Return an ExecResult object, that is, a named tuple with the
        result of the execution, the status code of the terminated
        process, and the output produced by the process.

        The output limit is applied independently to stdout and stderr.
        When exceeded the execution is considered as failed.

        """
        with contextlib.ExitStack() as stack:
            if tmpfile is not None:
                tmpname = stack.enter_context(_make_temp_file(tmpfile))
                args = self._replace_placeholder(args, tmpname)
            outputb = b""
            errorb = b""
            ret_code = 0
            try:
                proc = subprocess.Popen(args,
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
                inputb = input.encode('utf-8', errors='ignore')
                outputb, errorb = proc.communicate(inputb, timeout)
                codes = {0: ER_OK, -signal.SIGSEGV: ER_SEGFAULT}
                er = codes.get(proc.returncode, ER_ERROR)
                ret_code = proc.returncode
            except subprocess.TimeoutExpired:
                er = ER_TIMEOUT
                proc.kill()
                proc.stdin.close()
                proc.stdout.close()
                proc.stderr.close()
                proc.wait()
            except FileNotFoundError:
                er = ER_NOTFILE
        output = outputb.decode('utf-8', errors='ignore')
        error = errorb.decode('utf-8', errors='ignore')
        if output_limit is not None:
            lines = output.splitlines(True) 
            if len(lines) > output_limit:
                output = "".join(lines[:output_limit])
                er = ER_OUTPUT_LIMIT
            lines = error.splitlines(True) 
            if len(lines)  > output_limit:
                error = "".join(lines[:output_limit])
                er = ER_OUTPUT_LIMIT
        return ExecResult(er, ret_code, output, error)

    def _replace_placeholder(self, args, name):
        return [(name if a is ARG_TMPFILE else a) for a in args]



"""Executor using the valgrind memory checker tool."""

import pvcheck.executor


class ValgrindExecutor(pvcheck.executor.Executor):
    """Executor that uses valgrind to check the memory usage.
    
    Output from valgrind is detected and used to form a new 'VALGRIND'
    section at the end of the regular process output.  In absence of
    errors that section would be empty.

    Valgrind need to be installed in the system.

    """
    
    def exec_process(self, args, *rest, **kwargs):
        res = super().exec_process(["valgrind"]+args, *rest, **kwargs)
        out, err = self._process_output(res.output, res.stderr)
        return res._replace(output=out, stderr=err)

    def _process_output(self, stdout, stderr):
        extraout = ["\n[VALGRIND]\n"]
        newerr = []
        for line in stderr.splitlines(keepends=True):
            if not line.startswith("=="):
                newerr.append(line)
                continue
            if "in use at exit" in line:
                f = line.split()
                bytes_ = int(f[5].replace(',', ''))
                if bytes_ > 0:
                    extraout.append(line)
            elif "total heap usage" in line:
                f = line.split()
                allocs = int(f[4].replace(',', ''))
                frees = int(f[6].replace(',', ''))
                if allocs != frees:
                    extraout.append(line)
            elif "ERROR SUMMARY" in line:
                f = line.split()
                errs = int(f[3].replace(',', ''))
                if errs > 0:
                    extraout.append(line)

        newout = stdout + "".join(extraout)
        return (newout, "".join(newerr))

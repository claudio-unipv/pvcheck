

### !!! TO BE REFACTORED



"""
    ...
    if opts['valgrind']:
        args.insert(1, "valgrind")
        valgrind_out = tempfile.NamedTemporaryFile(suffix=".pvcheck.valgrind",
                                                   delete=False)
        kwargs['stderr'] = valgrind_out
    else:
        valgrind_out = None
    ...



    if valgrind_out is not None:
        valgrind_out.close()
        with open(valgrind_out.name, "rt") as f:
            valgrind_report = [x for x in f]
        os.remove(valgrind_out.name)
    else:
        valgrind_report = []

"""


def parse_valgrind(report):
    """Analyse the report by Valgrind and log the result."""
    warnings = 0
    errors = 0
    for line in report:
        if not line.startswith('=='):
            continue
        f = line.split()
        if "in use at exit" in line:
            bytes_ = int(f[5].replace(',', ''))
            if bytes_ > 0:
                log.warning("VALGRIND: memory %s" % " ".join(f[1:]))
                warnings += 1
            else:
                log.debug("VALGRIND: memory %s" % " ".join(f[1:]))
        elif "total heap usage" in line:
            allocs = int(f[4].replace(',', ''))
            frees = int(f[6].replace(',', ''))
            if allocs != frees:
                log.warning("VALGRIND: %s" % " ".join(f[1:]))
                warnings += 1
            else:
                log.debug("VALGRIND: %s" % " ".join(f[1:]))

        elif "ERROR SUMMARY" in line:
            errs = int(f[3].replace(',', ''))
            if errs > 0:
                log.error("VALGRIND: %s" % " ".join(f[3:]))
                errors += errs
            else:
                log.debug("VALGRIND: %s" % " ".join(f[3:]))
    return (errors, warnings)

# pvcheck
pvcheck is a tool for the automated testing of computer programs developed and used at the University of Pavia

The tool requires a Python interpreter (tried with version 3.4.3) and
can be executed as a standalone application without any installation
(just copy the script where it can be executed).

To execute the tool, launch it from the command line with the
following parameters:
- the file defining the test case(s);
- the program to be verified;
- other parameters to be passed to the program under verification
  (optional).

For instance, after the compilation of 'program.c', the tool ca be tried by typing the command:

```
./pvcheck example.test ./program 3
```

where "3" is an argument to be passed to 'program' (it accepts as
argument the numbers in the range 0..8, where each number causes
a different behavior of the program).

Multiple tests (a "suite") can be run with a single invocation,
provided that they are suitably defined:

```
./pvcheck example2.test ./program2
```
    
The format of test definition files is very simple.  The examples
include comments that describe it briefly.

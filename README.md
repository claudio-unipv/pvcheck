pvcheck
=======

pvcheck is a tool that automates the testing of computer programs by checking the textual output of the program under testing with a set of user-defined test cases.

pvcheck has been developed to be used as automatic correction tool in the courses of Principles of Computer Programming at the University of Pavia.

Requirements
-------------

pvcheck requires a Python interpreter and can be executed as a standalone application.
The current version has been tested with Python 3.4.3.

Installation
------------

To install pvcheck:

```
cd pvcheck
make
```

To compile all the sample programs:

```
cd examples
make
```

Usage
-----

pvcheck has 3 main arguments ([run](#run), [info](#info) and [export](#export)) .

### help ###

To see the main help:

```
pvcheck -h
```

or 

```
pvcheck --help
```

To see the help of a specific command:

```
pvcheck argument -h
```

or

```
pvcheck argument --help
```

### the <a name="run"></a>run argument ###

The run argument, being the default argument, also works without explicit invocation. So

```
pvcheck run ./program
```

is the same as:

```
pvcheck ./program
```

#### test a program with a default test file ####

If you have a [test file](#testfile) with the default name *pvcheck.test* located in the pvcheck folder, you can test your program simply by using:

```
pvcheck ./program
```

#### test a program with any test file ####

If you want to test a program using a specific [test file](#testfile):

```
pvcheck -f testfile ./program
```
```
pvcheck --file testfile ./program
```

#### test a program with a specific test of a test suite ####

If you want to test a program using a specific test contained in a test suite, you can use the [info argument](#info) to list all the available tests. Then you can use:

```
pvcheck -T testnumber ./program
``` 
```
pvcheck --test testnumber ./program
``` 

to use only the desired test.

#### select a different output format ####

pvcheck lets you choose the output format. The formats available are [json](https://github.com/claudio-unipv/pvcheck/wiki/JSON-data-format), csv and html. To choose the ouput format:

```
pvcheck -F format ./program
``` 
```
pvcheck --format format ./program
``` 

#### change timeout ####

You can set how many seconds it should be waited for the termination of the program:

```
pvcheck -t timeout ./program
```
```
pvcheck --timeout timeout ./program
``` 

The default is 10 seconds.

#### change the number of reported errors #####

To report up to N errors per section:

```
pvcheck -e N ./program
``` 
```
pvcheck --errors N ./program
``` 

The default is 4.

#### set the verbosity level ####

To set the verbosity level, where the level must be an integer between 0 (minimum) and 4 (maximum):

```
pvcheck -v verbositylevel ./program
``` 
```
pvcheck --verbosity verbositylevel ./program
``` 

The default is 3.

#### use valgrind ####

To use Valgrind (if installed) to check memory usage:

```
pvcheck -V ./program
``` 
```
pvcheck --valgrind ./program
``` 

#### use a log file ####

To specify the name of the file used for logging:

```
pvcheck -l logfile ./program
``` 
```
pvcheck --log logfile ./program
``` 

The default is ~/.pvcheck.log.

#### set an output limit ####

To cut the output of the program to a maximum of L lines:

```
pvcheck -L L ./program
``` 
```
pvcheck --output_limit L ./program
```

The default is 10000.

#### use a configuration file ####

To use the specified configuration file:


```
pvcheck -c configurationfile ./program
``` 
```
pvcheck --config configurationfile ./program
``` 

#### change output color setting ####

To enable or disable colored output:

```
pvcheck -C option ./program
```
```
pvcheck --color option ./program
```

The options available are *YES*, *NO* and *AUTO*. The default value is *AUTO*.

### the <a name="info"></a>info argument ###

The info argument lists all the available tests in a test file. 

To see all the tests available in a test file:

```
pvcheck info testfile
``` 

### the <a name="export"></a>export argument ###

The export argument allows you to export in a file the input arguments from the selected test.

To export the input argument from a test, you can use the [info argument](#info) to list all the available tests. Then you can use:

```
pvcheck export testnumber testfile
``` 

The output file is saved into the current directory with the name testname.dat .

Test File<a name="testfile"></a>
---------

A test file is a file containing one or more test cases.

The format of test definition files is very simple and this examples include comments that describe it briefly:

* [single test case](https://github.com/claudio-unipv/pvcheck/blob/master/examples/example.test) 
* [multiple test cases](https://github.com/claudio-unipv/pvcheck/blob/master/examples/example2.test)
* [multiple output lines](https://github.com/claudio-unipv/pvcheck/blob/master/examples/example3.test)
* [temporary files](https://github.com/claudio-unipv/pvcheck/blob/master/examples/example4.test)

Wiki
----

For more information, please visit the [wiki](https://github.com/claudio-unipv/pvcheck/wiki) of the project.


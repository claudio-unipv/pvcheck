import argparse
import os
import i18n
_ = i18n.translate
_DEFAULT_LOG_FILE = os.path.expanduser("~/.pvcheck.log")


class ArgParser(argparse.ArgumentParser):
    def initialize(self):
        self.add_argument("-h", "--help", help=_("print this message and exit."), action='help')
        self.add_argument("-c", "--config", help=_("uses the specified configuration file."), nargs='?', const='',
                          default='')
        self.add_argument("-t", "--timeout", help=_(
                          "set how many seconds it should be waited for the termination of the program.  The default "
                          "is 10 seconds."), nargs='?', const='10', default='10', type=float)
        self.add_argument("-v", "--verbosity", help=_(
                          "set the verbosity level, where the level must be an integer between 0 (minimum) and 4 "
                          "(maximum). The default value is 3."),
                          nargs='?', const='3', default='3', type=int)
        self.add_argument("-m", "--max_errors", help=_("reports up to N errors per section (default 4)."), nargs='?',
                          const='4', default='4', type=int)
        self.add_argument("-C", "--color", help=_("enable or disable colored output (default AUTO)."), nargs='?',
                          const='AUTO', default='AUTO')
        self.add_argument("-V", "--valgrind", help=_("use Valgrind (if installed) to check memory usage."),
                          action='store_true')
        self.add_argument("-f", "--format", help=_("select the output type."), nargs='?', const='resume',
                          default='resume')
        self.add_argument("-l", "--log", help=_(
                          "specify the name of the file used for logging.  The default is ~/.pvcheck.log."),
                          nargs='?', const=_DEFAULT_LOG_FILE, default=_DEFAULT_LOG_FILE)
        self.add_argument("-ls", "--list", help=_("list all the available tests."), action='store_true')
        self.add_argument("-r", "--run", help=_("run only the selected test."), nargs="?", type=int)
        self.add_argument("-e", "--export", help=_("export in a file the input arguments from the selected test."),
                          nargs="?", type=int)
        self.add_argument("test_file", help=_("file containing the tests to be performed (default pvcheck.test)."),
                          default="pvcheck.test")
        self.add_argument("program", help=_("program to be tested."))
        self.add_argument("program_arguments", help="any arguments of the program to be tested.", nargs='*')

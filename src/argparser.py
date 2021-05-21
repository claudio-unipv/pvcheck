"""ArgumentParser with Italian translation."""

import argparse
import sys


def _callable(obj):
    return hasattr(obj, '__call__') or hasattr(obj, '__bases__')


class ArgParser(argparse.ArgumentParser):
    def __init__(self,
                 prog=None,
                 usage=None,
                 description=None,
                 epilog=None,
                 parents=None,
                 formatter_class=argparse.HelpFormatter,
                 prefix_chars='-',
                 fromfile_prefix_chars=None,
                 argument_default=None,
                 conflict_handler='error',
                 add_help=True,
                 allow_abbrev=True,
                 exit_on_error=True):
        if parents is None:
            parents = []
        super().__init__(prog, usage, description, epilog, parents, formatter_class,
                         prefix_chars, fromfile_prefix_chars, argument_default,
                         conflict_handler, add_help, allow_abbrev, exit_on_error)

    def set_default_subparser(self, name, args=None):
        """
        Default subparser selection.

        name: is the name of the subparser to call by default
        args: if set is the argument list handed to parse_args()
        """
        subparser_found = False
        for arg in sys.argv[1:]:
            if arg in ['-h', '--help']:  # global help if no subparser
                break
        else:
            for x in self._subparsers._actions:
                if not isinstance(x, argparse._SubParsersAction):
                    continue
                for sp_name in x._name_parser_map.keys():
                    if sp_name in sys.argv[1:]:
                        subparser_found = True
            if not subparser_found:
                # insert default in first position, this implies no
                # global options without a sub_parsers specified
                if args is None:
                    sys.argv.insert(1, name)
                else:
                    args.insert(0, name)
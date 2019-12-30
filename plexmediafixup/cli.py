#!/usr/bin/env python
"""
plexmediafixup script. Invoke with --help for usage.
"""

from __future__ import print_function, absolute_import

import sys
from pprint import pprint
import argparse
from ._smart_formatter import SmartFormatter
from ._config_file import print_help_config_file, ConfigFile, ConfigFileError


def create_parser(prog):
    """
    Return an argparse command line parser for this script.
    """

    usage = "%(prog)s [options] CONFIG_FILE"

    desc = "Run configurable fixups against the media database of a " \
           "Plex Media Server."

    epilog = ""

    argparser = argparse.ArgumentParser(
        prog=prog, usage=usage, description=desc, epilog=epilog,
        add_help=False, formatter_class=SmartFormatter)

    pos_arggroup = argparser.add_argument_group(
        'Positional arguments')
    pos_arggroup.add_argument(
        'config_file', metavar='CONFIG_FILE',
        help='Config file for the script.')

    general_arggroup = argparser.add_argument_group(
        'General options')
    general_arggroup.add_argument(
        '-v', '--verbose', dest='verbose',
        action='store_true', default=False,
        help='Print more messages while processing')
    general_arggroup.add_argument(
        '-h', '--help', action='help',
        help='Show this help message and exit')
    general_arggroup.add_argument(
        '--help-config', dest='help_config',
        action='store_true', default=False,
        help='Print help on the config file')

    return argparser


def main():
    """
    Main function of the script.
    """

    prog = sys.argv[0]

    argparser = create_parser(prog)
    args = argparser.parse_args()

    if args.help_config:
        print_help_config_file()
        return 2

    try:
        config_file = ConfigFile(args.config_file)
    except ConfigFileError as exc:
        print("Error: {}".format(exc))
        return 1

    print("Debug: config_data:")
    pprint(config_file.data)

    return 0


if __name__ == '__main__':
    sys.exit(main())

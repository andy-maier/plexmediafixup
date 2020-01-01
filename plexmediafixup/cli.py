#!/usr/bin/env python
"""
plexmediafixup script. Invoke with --help for usage.
"""

from __future__ import print_function, absolute_import

import sys
from pprint import pprint
import argparse
import json
import plexapi
import plexapi.myplex
import plexapi.exceptions
from ._reuse._smart_formatter import SmartFormatter
from ._reuse._config_file import ConfigFile, ConfigFileError
from ._fixup import FixupManager
from ._version import __version__


# JSON schema describing the structure of config files
CONFIG_FILE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://example.com/root.json",
    "definitions": {},
    "type": "object",
    "title": "plexmediafixup config file",
    "required": [
        "servername",
        "username",
        "password",
    ],
    "additionalProperties": False,
    "properties": {
        "servername": {
            "$id": "#/properties/server",
            "type": "string",
            "title": "Server name of the Plex Media Server. This is not the "
            "IP address or host name, but the server name that can be found "
            "in the top left corner of the GUI.",
            "examples": [
                "MyPlex"
            ],
        },
        "username": {
            "$id": "#/properties/username",
            "type": "string",
            "title": "Username (email) of the Plex Account",
            "examples": [
                "john.doe@gmx.de"
            ],
        },
        "password": {
            "$id": "#/properties/password",
            "type": "string",
            "title": "Password of the Plex Account",
            "examples": [
                "password"
            ],
        },
        "fixups": {
            "$id": "#/properties/fixups",
            "type": "array",
            "title": "List of fixup items to be executed in list order",
            "default": [],
            "items": {
                "$id": "#/properties/fixups/items",
                "type": "object",
                "required": [
                    "name",
                    "title",
                    "enabled",
                ],
                "additionalProperties": True,
                "properties": {
                    "name": {
                        "$id": "#/properties/fixups/items/properties/name",
                        "type": "string",
                        "title": "Name of the fixup (unique within config "
                        "file)",
                        "examples": [
                            "example_fixup"
                        ],
                    },
                    "title": {
                        "$id": "#/properties/fixups/items/"
                        "properties/title",
                        "type": "string",
                        "title": "One-line title of the fixup",
                        "examples": [
                            "Example fixup"
                        ],
                    },
                    "enabled": {
                        "$id": "#/properties/fixups/items/"
                        "properties/enabled",
                        "type": "boolean",
                        "title": "Flag controlling whether the fixup is "
                        "enabled (i.e. will run)",
                        "examples": [
                            "true", "false"
                        ],
                    },
                    "dryrun": {
                        "$id": "#/properties/fixups/items/"
                        "properties/dryrun",
                        "type": "boolean",
                        "title": "Flag passed to the fixup controlling "
                        "whether it actually performs its work vs just "
                        "reporting it",
                        "default": "false",
                        "examples": [
                            "true", "false"
                        ],
                    },
                    "kwargs": {
                        "$id": "#/properties/fixups/items/"
                        "properties/kwargs",
                        "type": "object",
                        "title": "Keyword arguments for passing on to the "
                        "fixup",
                    },
                }
            }
        }
    }
}


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
        dest='config_file', metavar='CONFIG_FILE',
        action='store', nargs='?', default=None,
        help='Config file for the script.')

    general_arggroup = argparser.add_argument_group(
        'General options')
    general_arggroup.add_argument(
        '-v', '--verbose', dest='verbose',
        action='store_true', default=False,
        help='Print more messages while processing')
    general_arggroup.add_argument(
        '--version', dest='version',
        action='store_true', default=False,
        help='Print version of this program and exit')
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

    config = ConfigFile(args.config_file, CONFIG_FILE_SCHEMA)

    if args.version:
        print("{v}".format(v=__version__))
        return 0

    if args.help_config:
        print(config.help())
        return 0

    if args.config_file is None:
        print("Error: Config file must be specified.")
        return 1

    try:
        config.load()
    except ConfigFileError as exc:
        print("Error: {}".format(exc))
        return 1

    if args.verbose:
        print("Loaded config file {file}".
              format(file=config.filepath))

    servername = config.data['servername']  # required item
    username = config.data['username']  # required item
    password = config.data['password']  # required item
    fixups = config.data.get('fixups', [])
    fixup_mgr = FixupManager()

    # Verify that the fixups can be loaded
    for fixup in fixups:
        name = fixup['name']  # required item
        enabled = fixup['enabled']  # required item
        dryrun = fixup['dryrun']  # optional but defaulted item
        if enabled:
            fixup_mgr.get_fixup(name)
            if args.verbose:
                print("Loaded fixup: {name} (dryrun={dryrun})".
                      format(name=name, dryrun=dryrun))

    plexapi.TIMEOUT = 300

    try:
        plex_account = plexapi.myplex.MyPlexAccount(username, password)
    except plexapi.exceptions.PlexApiException as exc:
        print("Error: Cannot login to Plex account {user}: {msg}".
              format(user=username, msg=exc))
        return 1

    try:
        plex = plex_account.resource(servername).connect()
    except plexapi.exceptions.PlexApiException as exc:
        print("Error: Cannot connect to server {srv} of Plex account {user}: "
              "{msg}".
              format(srv=servername, user=username, msg=exc))
        return 1

    if args.verbose:
        print("Connected to server {srv} of Plex account {user}".
              format(srv=servername, user=username))

    for fixup in fixups:
        name = fixup['name']  # required item
        enabled = fixup['enabled']  # required item
        dryrun = fixup['dryrun']  # optional but defaulted item
        kwargs = fixup.get('kwargs', dict())
        if enabled:
            fixup = fixup_mgr.get_fixup(name)
            if args.verbose:
                print("Executing fixup: {name} (dryrun={dryrun})".
                      format(name=name, dryrun=dryrun))
            fixup.run(plex=plex, dryrun=dryrun, verbose=args.verbose, **kwargs)

    return 0


if __name__ == '__main__':
    sys.exit(main())

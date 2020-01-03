#!/usr/bin/env python
"""
plexmediafixup script. Invoke with --help for usage.
"""

from __future__ import print_function, absolute_import

import sys
import argparse
import plexapi
import plexapi.myplex
import plexapi.exceptions
from .utils.smart_formatter import SmartFormatter
from .utils.config_file import ConfigFile, ConfigFileError
from .fixup import FixupManager
from .version import __version__


# JSON schema describing the structure of config files
CONFIG_FILE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://example.com/root.json",
    "definitions": {},
    "type": "object",
    "title": "plexmediafixup config file",
    "required": [
        "plexapi_config_path",
        "direct_connection",
    ],
    "additionalProperties": False,
    "properties": {
        "plexapi_config_path": {
            "$id": "#/properties/plexapi_config_path",
            "type": ["null", "string"],
            "title": "Path name of PlexAPI config file. Specifying null causes "
                     "the default to be used (i.e. env var PLEXAPI_CONFIG_PATH "
                     "or ~/.config/plexapi/config.ini)",
            "examples": [
                "null", "my-plexapi-config.ini"
            ],
        },
        "direct_connection": {
            "$id": "#/properties/direct_connection",
            "type": "boolean",
            "title": "Flag controlling whether connection is directly to the "
                     "Plex Media Server (true) or indirectly via the Plex web "
                     "site (false). Using direct connection requires the "
                     "PlexAPI config file parameters auth.server_baseurl and "
                     "auth.server_token to be set. Using indirect connection "
                     "requires the PlexAPI config file parameters "
                     "auth.myplex_username and auth.myplex_password to be set, "
                     "as well as the server_name parameter in this config "
                     "file.",
            "examples": [
                "true", "false"
            ],
        },
        "server_name": {
            "$id": "#/properties/server_name",
            "type": ["null", "string"],
            "default": None,
            "title": "Server name of the Plex Media Server. This is not the "
                     "IP address or host name, but the server name that can be "
                     "found in the top left corner of the Plex web GUI. This "
                     "parameter is only required for indirect connection.",
            "examples": [
                "MyPlex"
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
                    "enabled",
                ],
                "additionalProperties": False,
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
                    "kwargs": {
                        "$id": "#/properties/fixups/items/"
                               "properties/kwargs",
                        "type": "object",
                        "default": [],
                        "title": "Keyword arguments for passing on to the "
                                 "fixup",
                    },
                }
            }
        }
    }
}


def parse_args():
    """
    Parse command line arguments for this script and return the result of
    argparse.ArgumentParser.parse_args().
    """

    prog = sys.argv[0]

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
        '-n', '--dryrun', dest='dryrun',
        action='store_true', default=False,
        help='Run fixups in dryrun mode (Print what would be done)')
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

    args = argparser.parse_args()

    return args


def main():
    """
    Main function of the script.
    """

    args = parse_args()

    if args.version:
        print("{v}".format(v=__version__))
        return 0

    config = ConfigFile(args.config_file, CONFIG_FILE_SCHEMA)

    if args.help_config:
        print(config.help())
        return 0

    if args.config_file is None:
        print("Error: Config file must be specified.")
        return 1

    print("Using plexmediafixup config file: {file}".
          format(file=args.config_file))
    try:
        config.load()
    except ConfigFileError as exc:
        print("Error: {}".format(exc))
        return 1
    plexapi_config_path = config.data['plexapi_config_path']  # required item
    direct_connection = config.data['direct_connection']  # required item
    server_name = config.data['server_name']  # optional but defaulted item
    fixups = config.data['fixups']  # optional but defaulted item
    fixup_mgr = FixupManager()

    if not plexapi_config_path:
        plexapi_config_path = plexapi.CONFIG_PATH
    print("Using PlexAPI config file: {file}".
          format(file=plexapi_config_path))
    plexapi_config = plexapi.config.PlexConfig(plexapi_config_path)

    # Verify that the fixups can be loaded
    for fixup in fixups:
        name = fixup['name']  # required item
        enabled = fixup['enabled']  # required item
        if enabled:
            print("Loading fixup: {name}".format(name=name))
            fixup_mgr.get_fixup(name)

    if direct_connection:

        server_baseurl = plexapi_config.get('auth.server_baseurl', None)
        if server_baseurl is None:
            print("Error: Parameter auth.server_baseurl is required for "
                  "direct connection but is not set in PlexAPI config file "
                  "{file}".
                  format(file=plexapi_config_path))
            return 1

        server_token = plexapi_config.get('auth.server_token', None)
        if server_token is None:
            print("Error: Parameter auth.server_token is required for "
                  "direct connection but is not set in PlexAPI config file "
                  "{file}".
                  format(file=plexapi_config_path))
            return 1

        try:
            plex = plexapi.server.PlexServer()
        except plexapi.exceptions.PlexApiException as exc:
            print("Error: Cannot connect to Plex server at {url}: {msg}".
                  format(url=server_baseurl, msg=exc))
            return 1

        print("Connected directly to Plex Media Server at {url}".
              format(url=server_baseurl))

    else:

        myplex_username = plexapi_config.get('auth.myplex_username', None)
        if not myplex_username:
            print("Error: Parameter auth.myplex_username is required for "
                  "indirect connection but is not set in PlexAPI config file "
                  "{file}".
                  format(file=plexapi_config_path))
            return 1

        myplex_password = plexapi_config.get('auth.myplex_password', None)
        if not myplex_username:
            print("Error: Parameter auth.myplex_password is required for "
                  "indirect connection but is not set in PlexAPI config file "
                  "{file}".
                  format(file=plexapi_config_path))
            return 1

        if not server_name:
            print("Error: Parameter server_name is required for "
                  "indirect connection but is not set in plexmediafixup "
                  "config file {file}".
                  format(file=config.filepath))
            return 1

        try:
            account = plexapi.myplex.MyPlexAccount(
                myplex_username, myplex_password)
        except plexapi.exceptions.PlexApiException as exc:
            print("Error: Cannot login to Plex account {user}: {msg}".
                  format(user=myplex_username, msg=exc))
            return 1

        try:
            plex = account.resource(server_name).connect()
        except plexapi.exceptions.PlexApiException as exc:
            print("Error: Cannot connect to server {srv} of Plex account "
                  "{user}: {msg}".
                  format(srv=server_name, user=myplex_username, msg=exc))
            return 1

        print("Connected indirectly to server {srv} of Plex account {user}".
              format(srv=server_name, user=myplex_username))

    plexapi.TIMEOUT = 300

    for fixup in fixups:
        name = fixup['name']  # required item
        enabled = fixup['enabled']  # required item
        dryrun = args.dryrun
        kwargs = fixup.get('kwargs', dict())
        if enabled:
            fixup = fixup_mgr.get_fixup(name)
            print("Executing fixup: {name} (dryrun={dryrun})".
                  format(name=name, dryrun=dryrun))
            rc = fixup.run(plex=plex, dryrun=dryrun, verbose=args.verbose,
                           **kwargs)
            if rc:
                print("Error: Fixup {name} has encountered errors - aborting".
                      format(name=name))
                return 1
            print("Fixup succeeded: {name} (dryrun={dryrun})".
                  format(name=name, dryrun=dryrun))

    return 0


if __name__ == '__main__':
    sys.exit(main())

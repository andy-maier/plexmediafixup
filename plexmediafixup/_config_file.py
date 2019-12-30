"""
Encapsulation of the config file.
"""

from __future__ import print_function, absolute_import

import errno
import yaml
import yamlloader


def print_help_config_file():
    """
    Print help for the config file.
    """
    print("TODO: help for config file")


class ConfigFileError(Exception):
    """
    An error in the config file.
    """
    pass


class ConfigFile(object):
    """
    Encapsulation of the config file.
    """

    def __init__(self, filepath):
        self._filepath = filepath
        self._data = None
        self.load_file()

    @property
    def filepath(self):
        """
        Path name of the config file.
        """
        return self._filepath

    @property
    def data(self):
        """
        Data in the config file.
        """
        return self._data

    def load_file(self):
        """
        Load the config file and set the configuration in this object.
        """
        try:
            with open(self.filepath) as fp:
                try:
                    data = yaml.load(
                        fp, Loader=yamlloader.ordereddict.CSafeLoader)
                except (yaml.parser.ParserError,
                        yaml.scanner.ScannerError) as exc:
                    raise ConfigFileError(
                        "Invalid YAML syntax in config file {0!r}: {1}: {2}".
                        format(self.filepath, exc.__class__.__name__, exc))
        except IOError as exc:
            if exc.errno == errno.ENOENT:
                raise ConfigFileError(
                    "Config file {0!r} was not found".
                    format(self.filepath))
            else:
                raise ConfigFileError(
                    "Config file {0!r} could not be opened: {1}".
                    format(self.filepath, exc))

        # TODO: JSON schema validation of config file

        self._data = data

"""
Support for config files in YAML format that are validated using JSON schema.
"""

from __future__ import print_function, absolute_import
import errno
import yaml  # PyYAML package
import yamlloader
import jsonschema
from .json_schema_defaults import extend_with_default


class ConfigFileError(Exception):
    """
    An error in the config file.
    """
    pass


class ConfigFile(object):
    """
    A config file in YAML format that is validated using JSON schema.
    """

    def __init__(self, filepath, json_schema):
        """
        Initialize the object. Does not yet load the config file.

        Parameters:

            filepath (string): Path name of config file in YAML format.

            json_schema (dict): JSON schema describing the structure of the
              config file. See jsonschema package for details.
        """
        self._filepath = filepath
        self._json_schema = json_schema
        self._data = None

    @property
    def filepath(self):
        """
        string: Path name of the config file.
        """
        return self._filepath

    @property
    def data(self):
        """
        dict: Data in the config file, resulting from loading the JSON file into
        Python objects. Initially None, will be set after calling load().
        """
        return self._data

    @property
    def json_schema(self):
        """
        dict: JSON schema of the config file. See jsonschema package for
        details.
        """
        return self._json_schema

    def help(self):
        """
        Returns a help text string explaining the structure of the config file,
        based on its JSON schema.
        """
        return "TODO: Create help text from JSON schema"

    def load(self):
        """
        Load the config file and set the configuration data in this object.

        Raises:
            ConfigFileError: Raised for various errors with opening, loading and
              validating the config file.
        """

        # Load the config file
        try:
            with open(self.filepath) as fp:
                try:
                    data = yaml.load(
                        fp, Loader=yamlloader.ordereddict.CSafeLoader)
                except (yaml.parser.ParserError,
                        yaml.scanner.ScannerError) as exc:
                    raise ConfigFileError(
                        "Invalid YAML syntax in config file {file}: "
                        "{exc}: {msg}".
                        format(file=self.filepath,
                               exc=exc.__class__.__name__,
                               msg=exc))
        except IOError as exc:
            if exc.errno == errno.ENOENT:
                raise ConfigFileError(
                    "Config file not found: {file}".
                    format(file=self.filepath))
            else:
                raise ConfigFileError(
                    "Config file {file} could not be opened: {msg}".
                    format(file=self.filepath, msg=exc))

        # Validate config file data against JSON schema
        ValidatorWithDefaults = extend_with_default(jsonschema.Draft7Validator)
        validator = ValidatorWithDefaults(self._json_schema)
        try:
            validator.validate(data)
        except jsonschema.exceptions.ValidationError as exc:
            parm_str = ''
            for p in exc.absolute_path:
                # Path contains list index numbers as integers
                if isinstance(p, int):
                    parm_str += '[{}]'.format(p)
                else:
                    if parm_str != '':
                        parm_str += '.'
                    parm_str += p
            raise ConfigFileError(
                "Config file {file} contains an invalid item {parm}: {msg} "
                "(Validation details: Schema item: {schema_item}; "
                "Failing validator: {val_name}={val_value})".
                format(
                    file=self.filepath,
                    msg=exc.message,
                    parm=parm_str,
                    schema_item='.'.join(exc.absolute_schema_path),
                    val_name=exc.validator,
                    val_value=exc.validator_value))

        # Persist config file data in this object
        self._data = data

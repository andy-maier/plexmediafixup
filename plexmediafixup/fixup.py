"""
Fixup support.

Fixups are plugins that can be dynamically loaded and perform some function
on the Plex Media Server.
"""

import importlib
import inspect


class FixupManager(object):
    # pylint: disable=too-few-public-methods
    """
    Manager class for fixups.

    This class can load fixups from the 'fixups' sub-package and can look them
    up by name.
    """

    def __init__(self):
        self._fixup_package_path = 'plexmediafixup.fixups'
        self._fixup_objects = dict()  # Loaded fixup objects by fixup name

    def get_fixup(self, name):
        """
        Return the fixup object for the specified fixup name.

        If a fixup object for that fixup name already exists in the manager,
        it is returned.

        Otherwise, the fixup module with that name is imported, a fixup object
        is created, and the fixup object is added to the manager.

        Parameters:

            name (string): Name of the fixup.

        Returns:

            Fixup: Fixup object.

        Raises:

            ImportError: Fixup module not found
        """
        try:
            return self._fixup_objects[name]
        except KeyError:
            rel_name = '.' + name
            fixup_module = importlib.import_module(
                rel_name, package=self._fixup_package_path)
            for _name, _obj in inspect.getmembers(fixup_module):
                if inspect.isclass(_obj) and \
                        issubclass(_obj, Fixup) and _obj != Fixup:
                    fixup_object = _obj()
                    self._fixup_objects[_name] = fixup_object
                    return fixup_object


class Fixup(object):
    # pylint: disable=too-few-public-methods
    """
    Base class for fixup classes in fixup modules.
    """

    def __init__(self, name):
        """
        Init function, must be called by fixup subclass.

        Parameters:

          name (string): Name of the fixup.
        """
        self.name = name

    def run(self, plex, dryrun, verbose, config, fixup_kwargs):
        """
        Funxtion to execute the fixup. Must be implemented in fixup subclass.

        Parameters:

          plex (plexapi.PlexServer): PMS to work against.

          dryrun (bool): Dryrun flag from command line.

          verbose (bool): Verbose flag from command line.

          config (dict): The entire config file.

          fixup_kwargs (dict): The kwargs config parameter for the fixup.
        """
        raise NotImplementedError

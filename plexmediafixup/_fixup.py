"""
Fixup support.

Fixups are plugins that can be dynamically loaded and perform some function
on the Plex Media Server.
"""

import importlib
import inspect


class FixupManager(object):
    """
    Manager class for fixups.

    This class can load fixups from the 'fixups' sub-package and can look them
    up by name.
    """

    def __init__(self):
        self._fixup_package_path = 'plexmediafixup.fixups'
        self._fixup_objects = dict()  # Loaded fixup objects by fixup name

    def get_fixup(self, name, kwargs):
        """
        Return the fixup object for the specified fixup name.

        If a fixup object for that fixup name already exists in the manager,
        it is returned.

        Otherwise, the fixup module with that name is imported, a fixup object
        is created (passing on the kwargs), and the fixup object is added
        to the manager.

        Parameters:

            name (string): Name of the fixup.

            kwargs (dict): Keyword args that are passed on to initialize the
              fixup.

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
            for name, obj in inspect.getmembers(fixup_module):
                if inspect.isclass(obj) and \
                        issubclass(obj, Fixup) and obj != Fixup:
                    fixup_object = obj(kwargs)
                    self._fixup_objects[name] = fixup_object
                    return fixup_object


class Fixup(object):
    """
    Base class for fixup classes in fixup modules.
    """

    def __init__(self, name, kwargs):
        """
        Init function, must be called by fixup subclass.

        Parameters:

          name (string): Name of the fixup.

          kwargs (dict): Keyword arguments to initialize the fixup.
        """
        self.name = name
        self.kwargs = kwargs

    def run(self, plex_server):
        """
        Funxtion to execute the fixup. Must be implemented in fixup subclass.
        """
        raise NotImplementedError

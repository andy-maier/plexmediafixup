"""
Context manager for watching its body.
"""

from __future__ import print_function, absolute_import
from datetime import datetime


class Watcher(object):
    """
    Context manager for watching its body, producing duration, a debug
    string and exception information.
    """

    def __init__(self):
        self._dt1 = None

        # Exposed attributes:
        self.exc_type = None  # Exception type
        self.exc_value = None  # Exception type
        self.traceback = None  # Traceback object
        self.exc_class = None  # string that is module.classname of exception
        self.duration = None  # Duration of body as timedelta object
        self.debug_str = None  # Debug string including time

    def __enter__(self):
        self._dt1 = datetime.now()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.exc_type = exc_type
        self.exc_value = exc_value
        self.traceback = traceback
        dur = datetime.now() - self._dt1
        self.duration = dur
        if exc_value:
            self.exc_class = "{t.__module__}.{t.__name__}".format(t=exc_type)
            self.debug_str = "raised {exc} after {dur}s". \
                    format(exc=self.exc_class, dur=dur.seconds)
        else:
            self.exc_class = None
            self.debug_str = "succeeded after {dur}s". \
                    format(dur=dur.seconds)
        return False  # re-raise any exceptions

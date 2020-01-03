"""
PlexMediaFixup - Run configurable fixups against the media database of a
Plex Media Server
"""

# There are submodules, but users shouldn't need to know about them.
# Importing just this module is enough.

from __future__ import absolute_import
import sys

#: The full version of this package including any development levels, as a
#: :term:`string`.
#:
#: Possible formats for this version string are:
#:
#: * "M.N.P.dev1": Development level 1 of a not yet released version M.N.P
#: * "M.N.P": A released version M.N.P
__version__ = '0.1.0.dev1'

_PY_M = sys.version_info[0]
_PY_N = sys.version_info[1]

# Keep these Python versions in sync with setup.py
if _PY_M == 2 and _PY_N < 7:
    raise RuntimeError(
        "On Python 2, plexmediafixup requires Python 2.7")
elif _PY_M == 3 and _PY_N < 5:
    raise RuntimeError(
        "On Python 3, plexmediafixup requires Python 3.5 or higher")

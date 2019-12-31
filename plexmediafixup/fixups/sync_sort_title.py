"""
Fixup sync_sort_title.
"""

from __future__ import print_function, absolute_import
from .._fixup import Fixup


class SyncSortTitle(Fixup):
    """
    Fixup class that sets the sort title field to the value of the title field.
    """

    def __init__(self):
        super(SyncSortTitle, self).__init__('sync_sort_title')

    def run(self, plex_server):
        print("TODO: Implement sync_sort_title fixup run()")

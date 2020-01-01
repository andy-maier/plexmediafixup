"""
Fixup sync_sort_title.
"""

from __future__ import print_function, absolute_import
from .._fixup import Fixup
import re


class SyncSortTitle(Fixup):
    """
    Fixup class that sets the sort title field to the value of the title field.
    """

    def __init__(self):
        super(SyncSortTitle, self).__init__('sync_sort_title')

    def run(self, plex, dryrun, verbose, section_type='movie',
            section_title_pattern=None, title_pattern=None):
        dryrun_str = "Dryrun: " if dryrun else ""
        for section in plex.library.sections():
            if section.type != section_type:
                continue
            if section_title_pattern is not None and \
                    re.search(section_title_pattern, section.title) is None:
                continue
            if verbose:
                print("Processing {s.type} library section: {s.title!r}".
                      format(s=section))
            all_items = section.all()
            for item in all_items:
                if title_pattern is not None and \
                        re.search(title_pattern, item.title) is None:
                    continue
                if not item.title or item.title == item.titleSort:
                    continue
                if verbose:
                    print("{d}Syncing sort title field of movie "
                          "{i.title!r} (was: {i.titleSort!r})".
                          format(d=dryrun_str, t=type(item), i=item))
                if not dryrun:
                    # key = '/:/rate?key=%s&identifier=com.plexapp.plugins.library&rating=%s' % (self.ratingKey, rate)

                    # item._server.query(key)
                    # item.reload()
                    pass
                break  # TODO: For now, process only the first one

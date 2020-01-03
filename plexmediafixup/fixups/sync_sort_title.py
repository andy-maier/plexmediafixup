"""
Fixup sync_sort_title.
"""

from __future__ import print_function, absolute_import
import re
import json
import six
import plexapi
import plexapi.exceptions
import plexapi.utils
from plexmediafixup.fixup import Fixup
from plexmediafixup.utils.unicode import ensure_bytes


class SyncSortTitle(Fixup):
    """
    Fixup class that sets the sort title field to the value of the title field.
    """

    def __init__(self):
        super(SyncSortTitle, self).__init__('sync_sort_title')

    def run(self, plex, dryrun, verbose, section_types=None,
            section_title_pattern=None, title_pattern=None):

        if isinstance(section_types, six.string_types):
            section_types = [section_types]

        for section in plex.library.sections():

            if section_types is not None and section.type not in section_types:
                continue
            if section_title_pattern is not None and \
                    re.search(section_title_pattern, section.title) is None:
                continue

            if verbose:
                print("Processing library section of type {s.type}: "
                      "{s.title!r}".
                      format(s=section))

            items = section.all()
            for item in items:
                if item.type == 'movie':
                    rc = process_item(section, dryrun, verbose, item,
                                      title_pattern)
                    if rc:
                        return rc
                elif item.type == 'show':
                    ep_items = item.episodes()
                    for ep_item in ep_items:
                        rc = process_item(section, dryrun, verbose, ep_item,
                                          title_pattern)
                        if rc:
                            return rc
                else:
                    print("Error: Invalid section type: {type} for this fixup".
                          format(type=item.type))
                    return 1

        return 0


def process_item(section, dryrun, verbose, item, title_pattern):
    """
    Process one movie or episode item
    """
    if title_pattern is not None and \
            re.search(title_pattern, item.title) is None:
        return 0
    if not item.title or item.title == item.titleSort:
        return 0

    dryrun_str = "Dryrun: " if dryrun else ""

    if verbose:
        print("{d}Syncing sort title field of {i.type} item "
              "{i.title!r} (was: {i.titleSort!r})".
              format(d=dryrun_str, i=item))

    if not dryrun:

        # Change the sort title field
        new_title_sort = item.title
        new_title_sort_bytes = ensure_bytes(new_title_sort)
        parm_type = plexapi.utils.SEARCHTYPES[item.type]
        parms = {
            'type': parm_type,
            'id': item.ratingKey,
            'titleSort.value': new_title_sort_bytes,
            'titleSort.locked': 1,
        }
        try:
            item.edit(**parms)
        except plexapi.exceptions.PlexApiException as exc:
            print("Error: Cannot set the sort title field of "
                  "{i.type} item to {new_title!r}: {msg}".
                  format(i=item, new_title=new_title_sort, msg=exc))
            return 1

        # Verify the sort title field was changed
        item.reload()
        if item.titleSort != new_title_sort:
            print("Error: Attempt to set the sort title field of "
                  "{i.type} item to {new_title!r} did not stick, "
                  "it is still {i.titleSort!r}".
                  format(i=item, new_title=new_title_sort))
            return 1

    return 0

"""
Fixup that walks through the movie, show and episode items of the configured
library sections, and syncs the "sort title" field of each item by setting it
to the value of its "title" field.
"""

from __future__ import print_function, absolute_import
import os
import re
import json
import six
import plexapi
import plexapi.exceptions
import plexapi.utils
from plexmediafixup.fixup import Fixup
from plexmediafixup.utils.unicode import ensure_bytes


FIXUP_NAME = os.path.splitext(os.path.basename(__file__))[0]


class SyncSortTitle(Fixup):

    def __init__(self):
        super(SyncSortTitle, self).__init__(FIXUP_NAME)

    def run(self, plex, dryrun, verbose, section_types=None,
            section_pattern=None):
        """
        Standard parameters:

          plex (plexapi.PlexServer): PMS to work against.

          dryrun (bool): Dryrun flag.

          verbose (bool): Verbose flag.

        Fixup-specific parameters (kwargs in config):

          section_types (string or iterable(string)):
            The library section types that should be processed. Valid values
            are: 'movie', 'show'. For 'show', both the show item itself and its
            episodes will be processed. A value of None (null in config file)
            means to process all valid section types. Optional, default is None.

          section_pattern (string):
            Regex pattern defining library section names that should be
            processed within the configured section types. A value of None
            (null in config file) means to process all library sections of the
            configured types. Optional, default is None.
        """

        if section_types is None:
           section_types = ['movie', 'show']
        elif isinstance(section_types, six.string_types):
            section_types = [section_types]
        for st in section_types:
            if st not in ['movie', 'show']:
                print("Error: Invalid section type specified for fixup "
                      "{fixup}: {type}".
                      format(fixup=FIXUP_NAME, type=st))
                return 1

        for section in plex.library.sections():

            if section.type not in section_types:
                continue
            if section_pattern is not None and \
                    re.search(section_pattern, section.title) is None:
                if verbose:
                    print("Skipping {s.type} library section {s.title!r} "
                          "that does not match the specified pattern".
                          format(s=section))
                continue

            print("Processing library section of type {s.type}: "
                  "{s.title!r}".
                  format(s=section))

            items = section.all()
            for item in items:
                if item.type == 'movie':
                    rc = process_item(dryrun, verbose, item)
                    if rc:
                        return rc
                elif item.type == 'show':
                    rc = process_item(dryrun, verbose, item)
                    if rc:
                        return rc
                    ep_items = item.episodes()
                    for ep_item in ep_items:
                        rc = process_item(dryrun, verbose, ep_item)
                        if rc:
                            return rc
                else:
                    print("Error: Invalid section type {type!r} encountered in "
                          "library section {s.title!r}".
                          format(type=item.type, s=section))
                    return 1

        return 0


def process_item(dryrun, verbose, item):
    """
    Process one movie, show or episode item
    """

    # If the item has no title, we cannot sync from it
    if not item.title:
        if verbose:
            print("Skipping {i.type} item that has no title set: "
            "id {i.ratingKey}, sort title {i.titleSort!r}".
                  format(i=item))
        return 0

    # If the sort title field is already synced, nothing needs to be done
    if item.titleSort == item.title:
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

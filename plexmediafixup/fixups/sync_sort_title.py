"""
Fixup sync_sort_title.
"""

from __future__ import print_function, absolute_import
from .._fixup import Fixup
from .._reuse.unicode import ensure_bytes
import re
import json
import six
import plexapi
import plexapi.exceptions


class SyncSortTitle(Fixup):
    """
    Fixup class that sets the sort title field to the value of the title field.
    """

    def __init__(self):
        super(SyncSortTitle, self).__init__('sync_sort_title')

    def run(self, plex, dryrun, verbose, section_types=None,
            section_title_pattern=None, title_pattern=None):

        dryrun_str = "Dryrun: " if dryrun else ""

        if section_types is None:
            section_types = []
        elif isinstance(section_types, six.string_types):
            section_types = [section_types]

        for section in plex.library.sections():

            if section.type not in section_types:
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

                    # Change the sort title field
                    new_title_sort = item.title
                    new_title_sort_bytes = ensure_bytes(new_title_sort)
                    parms = {
                        'type': 1,  # TODO: Find out what this is
                        'id': item.ratingKey,
                        'titleSort.value': new_title_sort_bytes,
                        'titleSort.locked': 1,
                        # 'agent': 'com.plexapp.agents.none',
                    }
                    # print("Debug: edit() kwargs:")
                    # print(json.dumps(parms, indent=2))
                    try:
                        section.edit(**parms)
                    except plexapi.exceptions.PlexApiException as exc:
                        print("Error: Cannot set the sort title to "
                              "{title!r}: {msg}".
                              format(title=new_title_sort, msg=exc))
                        return 1

                    # Verify the sort title field was changed
                    item.reload()
                    if item.titleSort != new_title_sort:
                        print("Error: Attempt to set the sort title to "
                              "{new_title!r} did not stick, it is still "
                              "{old_title!r}".
                              format(new_title=new_title_sort,
                                     old_title=item.titleSort))
                        return 1

        return 0

"""
Fixup that walks through the movie, show and episode items of the configured
library sections, and syncs the "sort title" field of each item by setting it
to the value of its "title" field. Optionally, non-ASCII characters can be
normalized to corresponding ASCII characters, and special characters can be
removed.
"""

from __future__ import print_function, absolute_import
import os
import re
import json
import six
from unidecode import unidecode
import plexapi
import plexapi.exceptions
import plexapi.utils
import requests.exceptions
from plexmediafixup.fixup import Fixup
from plexmediafixup.utils.unicode import ensure_bytes, ensure_unicode
from plexmediafixup.utils.watcher import Watcher


FIXUP_NAME = os.path.splitext(os.path.basename(__file__))[0]

# Translation table for special characters that are replaced with space
SPECIALS = u"^()[]{}!.,-+*$'~%&=?!#;:_"
SPECIALS_TABLE = dict()
for c in SPECIALS:
    SPECIALS_TABLE[ord(c)] = u' '


def title_sort(title, as_ascii, remove_specials):
    """
    Return the new sort title from the title.
    """
    ret_title = ensure_unicode(title)

    if as_ascii:
        ret_title = ensure_unicode(unidecode(ret_title))

    if remove_specials:
        ret_title = ret_title.translate(SPECIALS_TABLE)

    ret_title = ret_title.replace(u'  ', u' ').replace(u'  ', u' '). \
        replace(u'  ', u' ').strip()

    return ret_title


class SyncSortTitle(Fixup):

    def __init__(self):
        super(SyncSortTitle, self).__init__(FIXUP_NAME)

    def run(self, plex, dryrun, verbose, config, fixup_kwargs):
        """
        Parameters:

          plex (plexapi.PlexServer): PMS to work against.

          dryrun (bool): Dryrun flag from command line.

          verbose (bool): Verbose flag from command line.

          config (dict): The entire config file.

          fixup_kwargs (dict): The kwargs config parameter for the fixup,
            with the following items:

            section_types (string or iterable(string)):
              The library section types that should be processed. Valid values
              are: 'movie', 'show'. For 'show', both the show item itself and
              its episodes will be processed. A value of None (null in config
              file) means to process all valid section types. Optional, default
              is None.

            section_pattern (string):
              Regex pattern defining library section names that should be
              processed within the configured section types. A value of None
              (null in config file) means to process all library sections of
              the configured types. Optional, default is None.

            as_ascii (bool):
              Boolean that controls whether the sort title is translated to
              7-bit ASCII characters using unidecode. Optional, default is
              False.

            remove_specials (bool):
              Boolean that controls whether special characters in the sort
              title will be replaced with space. Optional, default is False.
        """

        section_types = fixup_kwargs.get('section_types', None)
        section_pattern = fixup_kwargs.get('section_pattern', None)
        as_ascii = fixup_kwargs.get('as_ascii', False)
        remove_specials = fixup_kwargs.get('remove_specials', False)

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

        try:
            with Watcher() as w:
                sections = plex.library.sections()
        except (plexapi.exceptions.PlexApiException,
                requests.exceptions.RequestException) as exc:
            print("Error: Cannot list sections: {msg} ({w.debug_str})".
                  format(msg=exc, w=w))
            return 1

        for section in sections:

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

            try:
                with Watcher() as w:
                    items = section.all()
            except (plexapi.exceptions.PlexApiException,
                    requests.exceptions.RequestException) as exc:
                print("Error: Cannot list all items in section of type "
                      "{s.type}: {s.title!r}: {msg} ({w.debug_str})".
                      format(s=section, msg=exc, w=w))
                return 1

            for item in items:
                if item.type == 'movie':
                    rc = process_item(dryrun, verbose, item, as_ascii,
                                      remove_specials)
                    if rc:
                        return rc
                elif item.type == 'show':
                    rc = process_item(dryrun, verbose, item, as_ascii,
                                      remove_specials)
                    if rc:
                        return rc

                    try:
                        with Watcher() as w:
                            ep_items = item.episodes()
                    except (plexapi.exceptions.PlexApiException,
                            requests.exceptions.RequestException) as exc:
                        print("Error: Cannot list episodes of show {show!r}: "
                              "{msg} ({w.debug_str})".
                              format(show=item.title, msg=exc, w=w))
                        return 1

                    for ep_item in ep_items:
                        rc = process_item(dryrun, verbose, ep_item, as_ascii,
                                          remove_specials)
                        if rc:
                            return rc
                else:
                    print("Error: Invalid section type {type!r} encountered in "
                          "library section {s.title!r}".
                          format(type=item.type, s=section))
                    return 1

        return 0


def process_item(dryrun, verbose, item, as_ascii, remove_specials):
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

    new_title_sort = title_sort(item.title, as_ascii, remove_specials)

    # If the sort title field is already synced, nothing needs to be done
    if item.titleSort == new_title_sort:
        return 0

    dryrun_str = "Dryrun: " if dryrun else ""

    print("{d}Changing sort title field of {i.type} {i.title!r} from "
          "{i.titleSort!r} to {new!r}".
          format(d=dryrun_str, i=item, new=new_title_sort))

    if not dryrun:

        # Change the sort title field
        new_title_sort_bytes = ensure_bytes(new_title_sort)
        parm_type = plexapi.utils.SEARCHTYPES[item.type]
        parms = {
            'type': parm_type,
            'id': item.ratingKey,
            'titleSort.value': new_title_sort_bytes,
            'titleSort.locked': 1,
        }

        try:
            with Watcher() as w:
                item.edit(**parms)
        except (plexapi.exceptions.PlexApiException,
                requests.exceptions.RequestException) as exc:
            print("Error: Cannot set the sort title field of "
                  "{i.type} item to {new_title!r}: {msg} ({w.debug_str})".
                  format(i=item, new_title=new_title_sort, msg=exc, w=w))
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

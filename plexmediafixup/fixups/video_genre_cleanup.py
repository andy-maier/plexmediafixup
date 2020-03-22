"""
Fixup that walks through the movie and show items of the configured library
sections, and cleans up the "Genres" field of each item. It can consolidate
genres into a defined list of genres, remove useless genres, and set a default
genre if the list of genres is empty.
These changes can be configured in the config file.
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


def reversed_change_dict(change):
    """
    Return the dictionary of genre changes, whereby keys and values have
    swapped their roles.

    Parameters:

      change (dict): Original dictionary of genre changes, with:
        * key (string): desired genre.
        * value (list of string): None, or list of genres to be changed to
          desired genre. None counts as an empty list.

    Returns:

      dict: Reversed dictionary of genre changes, with:
        * key (string): genre to be changed.
        * value (list of string): list of desired genres.
    """
    change_rev = dict()
    for desired_genre in change:
        org_genres = change[desired_genre]
        if org_genres:
            for org_genre in org_genres:
                if org_genre not in change_rev:
                    change_rev[org_genre] = []
                change_rev[org_genre].append(desired_genre)
    return change_rev


class CleanupGenre(Fixup):

    def __init__(self):
        super(CleanupGenre, self).__init__(FIXUP_NAME)

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
              String or list of strings that specify the library section types
              that should be processed. Valid values are: 'movie', 'show'. For
              'show', only the show items will be processed, but not the
              episodes (they do not define a separate genre). A value of None
              (null in config file) means to process all valid section types.
              Optional, default is None.

            section_pattern (string):
              Regex pattern defining library section names that should be
              processed within the configured section types. A value of None
              (null in config file) means to process all library sections of
              the configured types. Optional, default is None.

            language (string):
              Language to be used to select the genre cleanup definitions from
              the "video_genre_cleanup" config parameter, using the two-letter
              language codes defined in ISO 639-1.
        """

        video_genre_cleanup = config.get('video_genre_cleanup', [])

        section_types = fixup_kwargs.get('section_types', None)
        section_pattern = fixup_kwargs.get('section_pattern', None)
        language = fixup_kwargs.get('language', None)

        if not language:
            print("Error: No 'language' config parameter specified for fixup "
                  "{fixup}".
                  format(fixup=FIXUP_NAME))
            return 1

        config_cleanup = None
        for cc in video_genre_cleanup:
            if cc['language'] == language:
                config_cleanup = cc

        if not config_cleanup:
            print("Error: 'video_genre_cleanup' config parameter does not "
                  "specify an item with language {lang} in fixup {fixup}".
                  format(lang=language, fixup=FIXUP_NAME))
            return 1

        change = config_cleanup['change']
        remove = config_cleanup['remove']
        if_empty = config_cleanup['if_empty']

        change_rev = reversed_change_dict(change)

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
                    rc = process_item(dryrun, verbose, item, change,
                                      change_rev, remove, if_empty)
                    if rc:
                        return rc
                elif item.type == 'show':
                    rc = process_item(dryrun, verbose, item, change,
                                      change_rev, remove, if_empty)
                    if rc:
                        return rc
                else:
                    print("Error: Invalid section type {type!r} encountered in "
                          "library section {s.title!r}".
                          format(type=item.type, s=section))
                    return 1

        return 0


def process_item(dryrun, verbose, item, change, change_rev, remove, if_empty):
    """
    Process one movie or show item.

    Parameters:

      item (plexapi.video.Movie or plexapi.video.Show): movie or show item to
        be processed.

      change (dict): Original dictionary of genre changes, with:
        * key (string): Desired genre to change to.
        * value (list of string): List of original genres to be changed.

      change_rev (dict): Reversed dictionary of genre changes, with:
        * key (string): Original genre to be changed.
        * value (list of string): List of desired genres to change to.

      remove (list of string): List of genres to be removed.

      if_empty (None or string): Genre to be set if list of genres is empty.
        None means not to set a genre if list is empty.
    """

    dryrun_str = "Dryrun: " if dryrun else ""

    # If the item is not fully loaded, it may show only a subset of genres.
    if not item.isFullObject():
        item.reload()

    genre_objs = item.genres or []

    act_genre_strs = [g.tag for g in genre_objs]
    new_genre_strs = []
    unknown_genre_strs = []
    for genre_obj in genre_objs:
        genre_str = genre_obj.tag
        if not genre_str:
            continue
        if genre_str == if_empty:
            # Remove that one for now (will be added again if still needed)
            continue
        if genre_str in remove:
            # Do not add any genres (= remove)
            continue
        if genre_str in change_rev:
            # Add the desired genres, if not yet in (= change)
            for new_genre_str in change_rev[genre_str]:
                if new_genre_str not in new_genre_strs:
                    new_genre_strs.append(new_genre_str)
            continue
        # Add the original genre, if not yet in (= unchanged)
        if genre_str not in new_genre_strs:
            new_genre_strs.append(genre_str)
        if genre_str not in change:
            unknown_genre_strs.append(genre_str)

    if not new_genre_strs:
        if if_empty:
            new_genre_strs.append(if_empty)

    if unknown_genre_strs:
        print("{d}Unknown genres on {i.type} {i.title!r}: {unknown!r}".
              format(d=dryrun_str, i=item, unknown=unknown_genre_strs))

    if new_genre_strs != act_genre_strs:

        print("{d}Changing genres of {i.type} {i.title!r} from "
              "{act!r} to {new!r}".
              format(d=dryrun_str, i=item, act=act_genre_strs,
                     new=new_genre_strs))

        if not dryrun:

            parm_type = plexapi.utils.SEARCHTYPES[item.type]

            # Delete the actual genres and add the new genres
            parms = {
                'type': parm_type,
                'id': item.ratingKey,
                # This deletes the actual genres:
                'genre[].tag.tag-': ensure_bytes(','.join(act_genre_strs)),
            }
            for i, g_str in enumerate(new_genre_strs):
                # This adds the new genres:
                parms['genre[{i}].tag.tag'.format(i=i)] = ensure_bytes(g_str)
            try:
                with Watcher() as w:
                    item.edit(**parms)
            except (plexapi.exceptions.PlexApiException,
                    requests.exceptions.RequestException) as exc:
                print("Error: Cannot change the genres field of "
                      "{i.type} {i.title!r} from {act!r} to {new!r}: "
                      "{msg} ({w.debug_str})".
                      format(i=item, act=act_genre_strs, new=new_genre_strs,
                             msg=exc, w=w))
                return 1

            # Verify the genres field was changed
            item.reload()
            ver_genre_strs = [g.tag for g in item.genres]
            if ver_genre_strs != new_genre_strs:
                print("Error: Attempt to change the genres field of "
                      "{i.type} {i.title!r} from {act!r} to {new!r} "
                      "did not work, it is now {ver!r}".
                      format(i=item, new=new_genre_strs, act=act_genre_strs,
                             ver=ver_genre_strs))
                return 1

    return 0

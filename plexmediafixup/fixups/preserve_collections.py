"""
Fixup that walks through the movie and show items of the configured library
sections, and preserves the tags of each item. This is done by syncing the tags
between a collections file and PMS.
The file name of the collections file can be configured in the config file.
"""

from __future__ import print_function, absolute_import
import os
import re
import json
import six
import yaml  # PyYAML package
import yamlloader
from unidecode import unidecode
import plexapi
import plexapi.exceptions
import plexapi.utils
import requests.exceptions
from plexmediafixup.fixup import Fixup
from plexmediafixup.utils.unicode import ensure_bytes, ensure_unicode
from plexmediafixup.utils.watcher import Watcher


FIXUP_NAME = os.path.splitext(os.path.basename(__file__))[0]


class PreserveCollections(Fixup):

    def __init__(self):
        super(PreserveCollections, self).__init__(FIXUP_NAME)

    def run(self, plex, dryrun, verbose, config, fixup_kwargs):
        """
        Parameters:

          plex (plexapi.PlexServer): PMS to work against.

          dryrun (bool): Dryrun flag from command line.

          verbose (bool): Verbose flag from command line.

          config (ConfigFile): The config file.

          fixup_kwargs (dict): The kwargs config parameter for the fixup,
            with the following items:

            section_types (string or iterable(string)):
              String or list of strings that specify the library section types
              that should be processed. Valid values are: 'movie', 'show'. For
              'show', only the show items will be processed, but not the
              episodes (they do not define a separate collection). A value of
              None (null in config file) means to process all valid section
              types. Optional, default is None.

            section_pattern (string):
              Regex pattern defining library section names that should be
              processed within the configured section types. A value of None
              (null in config file) means to process all library sections of
              the configured types. Optional, default is None.

            collections_file (string):
              Path name of collections file. Relative file paths are interpreted
              relative to the directory of the config file. The collections
              file is created if needed, and has a YAML format.
        """

        section_types = fixup_kwargs.get('section_types', None)
        section_pattern = fixup_kwargs.get('section_pattern', None)
        coll_file = fixup_kwargs.get('collections_file', None)

        if not coll_file:
            print("Error: No 'collections_file' config parameter specified for "
                  "fixup {fixup}".
                  format(fixup=FIXUP_NAME))
            return 1

        if not os.path.isabs(coll_file):
            coll_file = os.path.join(
                os.path.dirname(config.filepath),
                coll_file)
        print("Using collections file: {f}".format(f=coll_file))

        try:
            with open(coll_file, 'r', encoding='utf-8') as fp:
                if verbose:
                    print("Reading collections file: {f}".format(f=coll_file))
                coll_dict = yaml.safe_load(fp)
                if coll_dict is None:
                    coll_dict = {}
        except FileNotFoundError as exc:
            coll_dict = {}
        except (OSError, IOError) as exc:
            print("Error: Cannot open collections file {f} for reading: {msg}".
                  format(f=coll_file, msg=exc))
            return 1
        except yaml.YAMLError as exc:
            print("Error: Cannot parse collections file {f} as YAML: {msg}".
                  format(f=coll_file, msg=exc))
            return 1

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
                    print("Skipping {s.type} section {s.title!r} "
                          "that does not match the specified pattern".
                          format(s=section))
                continue

            print("Processing {s.type} section {s.title!r}".
                  format(s=section))

            try:
                with Watcher() as w:
                    items = section.all()
            except (plexapi.exceptions.PlexApiException,
                    requests.exceptions.RequestException) as exc:
                print("Error: Cannot list all items in {s.type} section "
                      "{s.title!r}: {msg} ({w.debug_str})".
                      format(s=section, msg=exc, w=w))
                return 1

            for item in items:
                if item.type == 'movie':
                    rc = process_item(dryrun, verbose, item, coll_dict)
                    if rc:
                        return rc
                elif item.type == 'show':
                    rc = process_item(dryrun, verbose, item, coll_dict)
                    if rc:
                        return rc
                else:
                    print("Error: Invalid section type {type!r} encountered in "
                          "section {s.title!r}".
                          format(type=item.type, s=section))
                    return 1

        if not dryrun:
            data = yaml.dump(
                coll_dict, encoding=None, allow_unicode=True,
                default_flow_style=False, indent=4,
                Dumper=yamlloader.ordereddict.CSafeDumper)
            try:
                with open(coll_file, 'w', encoding='utf-8') as fp:
                    if verbose:
                        print("Writing collections file: {f}".
                              format(f=coll_file))
                    fp.write(data)
            except (OSError, IOError) as exc:
                print("Error: Cannot open collections file {f} for writing: "
                      "{msg}".format(f=coll_file, msg=exc))
                return 1

        return 0


def process_item(dryrun, verbose, item, coll_dict):
    """
    Process one movie or show item.

    Parameters:

      item (plexapi.video.Movie or plexapi.video.Show): movie or show item to
        be processed.

      coll_dict (dict): Collections dictionary from the collections file, with:
        * key (string): ID of the item
        * value (dict): Attributes of the item, as follows:
          - 'section': Title of the section of the item
          - 'title': Title of the item
          - 'year': Year of the item
          - 'collections': List of collection names of the item
    """

    dryrun_str = "Dryrun: " if dryrun else ""

    # If the item is not fully loaded, it may show only a subset of collections.
    if not item.isFullObject():
        item.reload()

    item_collections = []  # List of collection names in item
    if item.collections:
        for c in item.collections:  # list of plexapi.media.Collection
            t = c.tag
            if isinstance(t, six.binary_type):
                t = t.decode('utf-8')
            item_collections.append(t)

    item_id = item.key.split('/')[-1]
    item_section = item.section().title
    item_title = item.title
    item_year = item.year

    if item_id not in coll_dict:
        if verbose:
            print("{d}Creating {s!r} item in collections file: {t!r} ({y})".
                  format(d=dryrun_str, s=item_section, t=item_title,
                         y=item_year))
        coll_dict[item_id] = {
            'section': item_section,
            'title': item_title,
            'year': item_year,
            'collections': [],
        }
        file_item_dict = coll_dict[item_id]
    else:
        file_item_dict = coll_dict[item_id]
        if item_section != file_item_dict.get('section', None) or \
                item_title != file_item_dict.get('title', None) or \
                item_year != file_item_dict.get('year', None):
            if verbose:
                print("{d}Updating section/title/year in collections file for "
                      "{s!r} item: {t!r} ({y})".
                      format(d=dryrun_str, s=item_section, t=item_title,
                             y=item_year))
            file_item_dict['section'] = item_section
            file_item_dict['title'] = item_title
            file_item_dict['year'] = item_year

    # Sync collections from PMS to collections file
    for coll in item_collections:
        if coll not in file_item_dict['collections']:
            if verbose:
                print("{d}Saving collection {c!r} to collections file for "
                      "{s!r} item: {t!r} ({y})".
                      format(d=dryrun_str, c=coll, s=item_section,
                             t=item_title, y=item_year))
            file_item_dict['collections'].append(coll)

    # Sync collections from collections file to PMS
    for coll in file_item_dict['collections']:
        if coll not in item_collections:
            if verbose:
                print("{d}Restoring collection '{c}' from collections file for "
                      "{s!r} item: {t!r} ({y})".
                      format(d=dryrun_str, c=coll, s=item_section,
                             t=item_title, y=item_year))
            item_collections.append(coll)
            if not dryrun:
                item.addCollection(coll)

    return 0

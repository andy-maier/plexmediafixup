"""
Fixup that walks through the movie and episode items of the configured library
sections, and syncs the "title" field of each item by setting it to the title
tag found in the media file.
"""

from __future__ import print_function, absolute_import
import os
import sys
import locale
import re
import json
import six
import ffmpy
import subprocess
import plexapi
import plexapi.exceptions
import plexapi.utils
import requests.exceptions
from plexmediafixup.fixup import Fixup
from plexmediafixup.utils.unicode import ensure_bytes, ensure_unicode
from plexmediafixup.utils.watcher import Watcher


FIXUP_NAME = os.path.splitext(os.path.basename(__file__))[0]

# Encodings that will be tried in order when decoding the metadata of any AVI
# files.
AVI_METADATA_ENCODINGS = ['cp1252', 'utf-8']


class SyncTitle(Fixup):

    def __init__(self):
        super(SyncTitle, self).__init__(FIXUP_NAME)

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
              are: 'movie', 'show'. For 'show', only its episodes will be
              processed (not the show item itself). A value of None (null in
              config file) means to process all valid section types. Optional,
              default is None.

            section_pattern (string):
              Regex pattern defining library section names that should be
              processed within the configured section types. A value of None
              (null in config file) means to process all library sections of
              the configured types. Optional, default is None.
        """

        path_mappings = config.get('path_mappings', [])

        section_types = fixup_kwargs.get('section_types', None)
        section_pattern = fixup_kwargs.get('section_pattern', None)

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
                    sys.stdout.flush()
                continue

            print("Processing library section of type {s.type}: "
                  "{s.title!r}".
                  format(s=section))
            sys.stdout.flush()

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
                    rc = process_item(
                        dryrun, verbose, item, path_mappings)
                    if rc:
                        return rc
                elif item.type == 'show':

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
                        rc = process_item(
                            dryrun, verbose, ep_item, path_mappings)
                        if rc:
                            return rc
                else:
                    print("Error: Invalid section type {type!r} encountered in "
                          "library section {s.title!r}".
                          format(type=item.type, s=section))
                    return 1

        return 0


def local_path(server_path, path_mappings):
    """
    Return the local path for a server_path, translating it using the
    specified path_mappings.
    """
    for mapping in path_mappings:
        server_root = mapping.get('server')
        if not server_root.endswith(os.path.sep):
            server_root += os.path.sep
        local_root = mapping.get('local')
        if not local_root.endswith(os.path.sep):
            local_root += os.path.sep
        if server_path.startswith(server_root):
            relpath = server_path[len(server_root):]
            return os.path.join(local_root, relpath)
    return None


def get_title_tag(media_file):
    """
    Retrieve the title tag from the metadata of the specified media_file
    using the ffprobe command and return it as a unicode string.
    """

    media_file = ensure_unicode(media_file)

    ext = os.path.splitext(media_file)[1].lower()

    # When invoking a system command, its command line arguments need to be
    # byte strings in file system encoding. If we pass command line
    # arguments as unicode strings, the subcommand package implementation
    # encodes them to byte strings using the 'ascii' encoder, which fails
    # if they contain non-ASCII characters.
    media_file_b = media_file.encode(sys.getfilesystemencoding())

    # The title tag (INAM) in AVI files very often does not use UTF-8 encoding,
    # but cp1252 or the like. The ffprobe command assumes the title tag is
    # encoded in UTF-8. When non-ASCII characters are in the title tag, the
    # ffprobe command by default issues a warning and replaces the character
    # with the Unicode replacement character (U+FFFD). The 'sv=ignore' writer
    # option causes ffprobe to ignore non-ASCII characters and to return them
    # unchanged.
    ffprobe = ffmpy.FFprobe(
        global_options=['-hide_banner', '-show_format',
                        '-of', 'json=sv=ignore'],
        inputs={media_file_b: None})

    try:
        stdout, stderr = ffprobe.run(
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    except (UnicodeDecodeError, UnicodeEncodeError) as exc:
        print("Error: Unicode conversion issue when invoking {cmd!r}: "
              "{msg!r}".
              format(cmd=ffprobe.cmd, msg=exc))
        return 1
    except ffmpy.FFRuntimeError as exc:
        print("Error: ffprobe failed on media file {file!r}: {msg!r}".
              format(file=media_file, msg=exc))
        return 1

    if ext == '.avi':
        stdout_u = None
        for enc in AVI_METADATA_ENCODINGS:
            try:
                stdout_u = ensure_unicode(stdout, encoding=enc)
            except UnicodeDecodeError as exc:
                continue
        if stdout_u is None:
            print("Error: Cannot decode ffprobe metadata output for AVI file "
                  "{file!r} using any of the encodings {enc}: {out!r}".
                  format(file=media_file, out=stdout,
                         encs=','.joinAVI_METADATA_ENCODINGS()))
            return 1
    else:
        stdout_u = ensure_unicode(stdout)  # UTF-8 by default

    try:
        out = json.loads(stdout_u)
    except ValueError:
        print("Error: ffprobe returned invalid JSON for media file "
              "{file!r}: {out!r}".
              format(file=media_file, out=stdout_u))
        return 1

    tags = out['format'].get('tags', dict())
    title_tag = tags.get('title', None)

    return title_tag


def process_item(dryrun, verbose, item, path_mappings):
    """
    Process one movie or episode item
    """

    title_info_list = []  # list items: tuple(local_file, title_tag)

    for part in item.iterParts():

        # Get title tag from metadata in file.

        # Note: part.file is a byte string if it only contains 7-bit ASCII
        # characers, or otherwise a unicode string.
        server_file = ensure_unicode(part.file)

        local_file = local_path(server_file, path_mappings)
        if local_file is None:
            print("Error: Cannot map server file {sf!r} using path "
                  "mappings {pm!r}".
                  format(sf=part.file, pm=path_mappings))
            return 1
        if not os.path.exists(local_file):
            print("Error: Cannot find local media file {lf!r} for {i.type} "
                  "{i.title!r}".
                  format(i=item, lf=local_file))
            return 1
        title_tag = get_title_tag(local_file)
        title_info_list.append((local_file, title_tag))

    title_tag = None
    for _local_file, _title_tag in title_info_list:
        if title_tag is None:
            title_tag = _title_tag
        elif title_tag != _title_tag:
            if verbose:
                print("Skipping {i.type} {i.title!r} with multiple media "
                      "files that have different title tags set "
                      "(file, title): {info}".
                      format(i=item, info=title_info_list))
                sys.stdout.flush()
            return 0

    # If the file has no title tag set, we cannot sync from it
    if not title_tag:
        if verbose:
            print("Skipping {i.type} {i.title!r} that has no title tag "
                  "set in media file {file!r}".
                  format(i=item, file=local_file))
            sys.stdout.flush()
        return 0

    # If the title field is already synced, nothing needs to be done
    if item.title == title_tag:
        return 0

    dryrun_str = "Dryrun: " if dryrun else ""

    print("{d}Changing title field of {i.type} {i.title!r} "
          "to {title_tag!r}".
          format(d=dryrun_str, title_tag=title_tag, i=item))
    sys.stdout.flush()

    if not dryrun:

        # Change the title field
        new_title = title_tag
        new_title_b = ensure_bytes(new_title)
        parm_type = plexapi.utils.SEARCHTYPES[item.type]
        parms = {
            'type': parm_type,
            'id': item.ratingKey,
            'title.value': new_title_b,
            'title.locked': 1,
        }

        try:
            with Watcher() as w:
                item.edit(**parms)
        except (plexapi.exceptions.PlexApiException,
                requests.exceptions.RequestException) as exc:
            print("Error: Cannot set the title field of {i.type} {i.title!r} "
                  "to {new_title!r}: {msg} ({w.debug_str})".
                  format(i=item, new_title=new_title, msg=exc, w=w))
            return 1

        # Verify the title field was changed
        item.reload()
        if item.title != new_title:
            print("Error: Attempt to set the title field of {i.type} "
                  "{i.title!r} to {new_title!r} did not stick".
                  format(i=item, new_title=new_title))
            return 1

    return 0

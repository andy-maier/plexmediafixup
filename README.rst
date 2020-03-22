PlexMediaFixup - Run configurable fixups against the media database of a Plex Media Server
==========================================================================================

.. image:: https://img.shields.io/pypi/v/plexmediafixup.svg
    :target: https://pypi.python.org/pypi/plexmediafixup/
    :alt: Version on Pypi

.. image:: https://travis-ci.org/andy-maier/plexmediafixup.svg?branch=master
    :target: https://travis-ci.org/andy-maier/plexmediafixup
    :alt: Travis test status (master)

.. # .. image:: https://ci.appveyor.com/api/projects/status/i022iaeu3dao8j5x/branch/master?svg=true
.. #     :target: https://ci.appveyor.com/project/andy-maier/plexmediafixup
.. #     :alt: Appveyor test status (master)

.. # .. image:: https://img.shields.io/coveralls/plexmediafixup/plexmediafixup.svg
.. #     :target: https://coveralls.io/r/plexmediafixup/plexmediafixup
.. #     :alt: Test coverage (master)


Overview
--------

The PlexMediaFixup project provides a command named ``plexmediafixup`` that
performs certain changes in the media database of a `Plex Media Server`_.

The functionality to perform these changes is organized in plugins called
*fixups*. Each fixup can be enabled or disabled and configured as needed.

Currently supported fixups are:

* sync_title:

  This fixup walks through the movie and episode items of the configured
  library sections of the Plex Media Server, and syncs the "title" field of
  each item by setting it to the value of the title tag found in the
  corresponding media files. The ffprobe command is used to get the title
  tag from the media files.

  Use this fixup if you properly maintain the title tags in your media files
  and are not happy with the titles that get set from the metadata sites.

* sync_sort_title:

  This fixup walks through the movie, show and episode items of the configured
  library sections of the Plex Media Server, and syncs the "sort title" field of
  each item by setting it to the value of its "title" field.

  Use this fixup if you are not happy with the fact that PMS removes leading
  articles and other words from the sort title.

* video_genre_cleanup:

  This fixup walks through the movie and show items of the configured library
  sections of the Plex Media Server, and cleans up the "Genres" field of each
  item. It can consolidate differently spelled genres into a single genre,
  remove useless genres, and set a default genre if the list of genres is empty.
  These changes can be configured in the config file.

Look at the example plexmediafixup config file `example_config_file.yml`_ if
you want to see what can be configured. It describes each parameter.

This project uses the `python-PlexAPI package`_, and access to the Plex Media
Server is specified in the `PlexAPI config file`_. The ``plexmediafixup``
command supports a choice of using a direct connection to a network-accessible
Plex Media Server (which is the faster choice) or using an indirect connection
through the Plex web site (which works from anywhere but is slower).


Installation and configuration
------------------------------

1.  Install the latest released version of the plexmediafixup Python package
    into your active Python environment:

    .. code-block:: bash

        $ pip install plexmediafixup

    This will also install any prerequisite Python packages, including the
    `python-PlexAPI package`_.

2.  If this is the first time you use the `python-PlexAPI package`_, create its
    `PlexAPI config file`_ as follows.

    If you want to use direct connections to a network-accessible Plex Media
    Server, specify the following parameters:

    .. code-block:: text

        [auth]
        server_baseurl = <URL of your PMS>
        server_token = <server auth token of your PMS>

    The server auth token of your PMS can be found as described in
    `Finding your server auth token`_.

    If you want to use indirect connections through the Plex web site, specify
    the following parameters. This is simpler to set up compared to direct
    connections, but every request goes through the Plex web site and from there
    to your Plex Media Server:

    .. code-block:: text

        [auth]
        myplex_username = <your plex account username/email>
        myplex_password = <your plex account password>

    The `PlexAPI environment variables`_ can also be used.

3.  Create a plexmediafixup config file.

    A plexmediafixup config file is in `YAML format`_ and specifies some general
    parameters (such as whether to use direct or indirect connections, or the
    location of the `PlexAPI config file`_) and the fixups that should be run,
    including any parameters for the fixups.

    An example plexmediafixup config file is provided as
    `example_config_file.yml`_. This example config file contains descriptions
    for all parameters, and describes all supported fixups.

    Create your plexmediafixup config file by copying that example file and
    modifying it as needed.

    The copy of the example file should work without further modifications.
    By default, it uses a direct connection and has all fixups enabled and
    configured to process all items. However, please review your copy
    carefully and make changes as needed.

4. Install the ffprobe command

   This command is only used by the sync_title fixup.

   On Windows with Chocolatey, on MacOS with HomeBrew, and on most Linux
   distros, the package containing this command is named ``ffmpeg``.
   Alternatively, download it from https://ffmpeg.org/download.html.


Usage
-----

To explore the command line options and general usage of the ``plexmediafixup``
command, invoke:

.. code-block:: bash

    $ plexmediafixup --help

The following commands assume that ``my_config_file.yml`` is the plexmediafixup
config file you have created.

First, invoke the ``plexmediafixup`` command in dry-run mode. This shows you
what would be changed in a real run without actually doing any changes:

.. code-block:: bash

    $ plexmediafixup my_config_file.yml --verbose --dryrun

If you are satisfied with what you see, perform the changes:

.. code-block:: bash

    $ plexmediafixup my_config_file.yml --verbose


Simplified setup and run script
-------------------------------

If you want to run the ``plexmediafixup`` command regularly, this GitHub repo
contains a ``run_plexmediafixup.sh`` script that simplifies the setup somewhat.
Copy that script to a directory in your PATH and modify it as needed.
That script has the following prerequisites:

* The plexmediafixup config file exists as ``$HOME/.config/plexmediafixup.yml``
* The `PlexAPI config file`_ exists
* The ``ffprobe`` and ``virtualenv`` commands are available

That script performs all the setup that is needed, such as checking if the
``virtualenv`` and ``ffprobe`` commands are available, creating a Python virtual
environment, activating it, installing the plexmediafixup package into that
virtual environment, checking if the plexmediafixup config file exists, and
finally running the ``plexmediafixup`` command with that config file.


Bugs and features
-----------------

Please report any bugs and request features via the `issue tracker`_.


Contributing
------------

Contributions to the PlexMediaFixup project are welcome; for details see
`Development`_.


License
-------

The PlexMediaFixup project is provided under the
`Apache Software License 2.0`_.


.. _Plex Media Server: https://en.wikipedia.org/wiki/Plex_(software)
.. _python-PlexAPI package: https://python-plexapi.readthedocs.io/en/latest/introduction.html
.. _PlexAPI config file: https://python-plexapi.readthedocs.io/en/latest/configuration.html
.. _PlexAPI environment variables: https://python-plexapi.readthedocs.io/en/latest/configuration.html#environment-variables
.. _Finding your server auth token: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/
.. _YAML format: https://yaml.org/start.html

.. _issue tracker: https://github.com/andy-maier/plexmediafixup/issues
.. _example_config_file.yml: https://github.com/andy-maier/plexmediafixup/blob/master/example_config_file.yml
.. _Apache Software License 2.0: https://github.com/andy-maier/plexmediafixup/blob/master/LICENSE
.. _Development: https://github.com/andy-maier/plexmediafixup/blob/master/DEVELOPMENT.rst

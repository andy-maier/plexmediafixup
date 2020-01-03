PlexMediaFixup - Run configurable fixups against the media database of a Plex Media Server
==========================================================================================

.. image:: https://img.shields.io/pypi/v/plexmediafixup.svg
    :target: https://pypi.python.org/pypi/plexmediafixup/
    :alt: Version on Pypi

.. # .. image:: https://travis-ci.org/plexmediafixup/plexmediafixup.svg?branch=master
.. #     :target: https://travis-ci.org/plexmediafixup/plexmediafixup
.. #     :alt: Travis test status (master)

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

The functionality to perform these changes in the media database of the Plex
Media Server are organized in plugins called `fixups`. Each fixup can be enabled
or disabled and configured as needed.

Currently supported fixups are:

* sync_sort_title:

  This fixup walks through the movie, show and episode items of the configured
  library sections of the Plex Media Server, and syncs the "sort title" field of
  each item by setting it to the value of the "title" field.

  Use this fixup if you are not happy with the fact that PMS removes leading
  articles and other words from the sort title.

This project uses the `python-PlexAPI package`_, and access to the Plex Media
Server is specified in the `PlexAPI config file`_. The ``plexmediafixup``
command supports a choice of using a direct connection to a network-accessible
Plex Media Server (which is the faster choice) or using an indirect connection
through the Plex web site (which works from anywhere but is slower).


Installation
------------

1.  Install the latest released version of the plexmediafixup Python package
    into your active Python environment:

    .. code-block:: bash

        $ pip install plexmediafixup

    This will also install any prerequisite Python packages, including the
    `python-PlexAPI package`_.

2.  If this is the first time you use the `python-PlexAPI package`_, create the
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

3.  Create a plexmediafixup config file by copying the
    example config file `example_config_file.yml`_ and modifying it as needed.
    The parameters are described within the file.


Usage
-----

To run the ``plexmediafixup`` command, invoke it with the path name of your
plexmediafixup config file:

.. code-block:: bash

    $ plexmediafixup my_config_file.yml

where ``my_config_file.yml`` is the plexmediafixup config file you created.

To explore its command line options, invoke:

.. code-block:: bash

    $ plexmediafixup --help


Configuration
-------------

The plexmediafixup config file is in `YAML format`_. It specifies some general
parameters (such as whether to use direct or indirect connections, or the
location of the `PlexAPI config file`_) and the fixups that should be run,
including parameters for the fixups.

An example plexmediafixup config file is provided as `example_config_file.yml`_.
The example config file describes all of its parameters.


License
-------

The PlexMediaFixup project is provided under the
`Apache Software License 2.0 <https://raw.githubusercontent.com/andy-maier/plexmediafixup/master/LICENSE>`_.

.. _Plex Media Server: https://en.wikipedia.org/wiki/Plex_(software)
.. _python-PlexAPI package: https://python-plexapi.readthedocs.io/en/latest/introduction.html
.. _PlexAPI config file: https://python-plexapi.readthedocs.io/en/latest/configuration.html
.. _Finding your server auth token: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/

.. _example_config_file.yml: https://raw.githubusercontent.com/andy-maier/plexmediafixup/master/example_config_file.yml
.. _YAML format: https://yaml.org/start.html

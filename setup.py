#!/usr/bin/env python
"""
Python setup script for the PlexMediaFixup project.
"""

import os
import re
import setuptools


def get_version(version_file):
    """
    Execute the specified version file and return the value of the __version__
    global variable that is set in the version file.

    Note: Make sure the version file does not depend on any packages in the
    requirements list of this package (otherwise it cannot be executed in
    a fresh Python environment).
    """
    with open(version_file, 'r') as fp:
        version_source = fp.read()
    _globals = {}
    exec(version_source, _globals)  # pylint: disable=exec-used
    return _globals['__version__']


def get_requirements(requirements_file):
    """
    Parse the specified requirements file and return a list of its non-empty,
    non-comment lines. The returned lines are without any trailing newline
    characters.
    """
    with open(requirements_file, 'r') as fp:
        lines = fp.readlines()
    reqs = []
    for line in lines:
        line = line.strip('\n')
        if not line.startswith('#') and line != '':
            reqs.append(line)
    return reqs


def read_file(a_file):
    """
    Read the specified file and return its content as one string.
    """
    with open(a_file, 'r') as fp:
        content = fp.read()
    return content


# pylint: disable=invalid-name
requirements = get_requirements('requirements.txt')
install_requires = [req for req in requirements
                    if req and not re.match(r'[^:]+://', req)]
dependency_links = [req for req in requirements
                    if req and re.match(r'[^:]+://', req)]
package_version = get_version(os.path.join('plexmediafixup', 'version.py'))

# Docs on setup():
# * https://docs.python.org/2.7/distutils/apiref.html?
#   highlight=setup#distutils.core.setup
# * https://setuptools.readthedocs.io/en/latest/setuptools.html#
#   new-and-changed-setup-keywords
setuptools.setup(
    name='plexmediafixup',
    version=package_version,
    packages=[
        'plexmediafixup',
        'plexmediafixup/fixups',
        'plexmediafixup/utils',
    ],
    include_package_data=True,  # as specified in MANIFEST.in
    scripts=[
        # add any scripts
    ],
    install_requires=install_requires,
    dependency_links=dependency_links,

    description="Run configurable fixups against the media database of a "
    "Plex Media Server",
    long_description=read_file('README.rst'),
    long_description_content_type='text/x-rst',
    license="Apache Software License 2.0",
    author="Andreas Maier",
    author_email='andreas.r.maier@gmx.de',
    maintainer="Andreas Maier",
    maintainer_email='andreas.r.maier@gmx.de',
    url='https://github.com/andy-maier/plexmediafixup',
    project_urls={},
    entry_points={
        'console_scripts': [
            'plexmediafixup=plexmediafixup.cli:main',
        ],
    },

    options={'bdist_wheel': {'universal': True}},
    zip_safe=True,  # This package can safely be installed from a zip file
    platforms='any',

    # Keep these Python versions in sync with plexmediafixup/__init__.py
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Multimedia',
        'Topic :: Utilities',
    ]
)

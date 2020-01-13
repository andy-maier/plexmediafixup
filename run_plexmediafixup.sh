#!/bin/bash
# Run the plexmediafixup script after setting up the environment if needed.

# Customize these variables as needed

# Name of Python virtualenv that is created:
venv_name="plex27"

# Python command to use (with absolute path or in PATH):
venv_python="python2.7"

# plexmediafixup config file to be used:
config_file="$HOME/.config/plexmediafixup.yml"

# Package source to install from:
# pkg_source="git+https://github.com/andy-maier/plexmediafixup.git@master#egg=plexmediafixup"
pkg_source="plexmediafixup"

# End of customization variables

function setup_venv {

  venv_name="$1"
  venv_python="$2"
  package_name="$3"
  package_source="$4"

  if ! [[ -x "$(command -v virtualenv)" ]]; then
    echo "Error: The virtualenv command is not available. Install the Python virtualenv package"
    return 1
  fi

  if ! [[ -x "$(command -v ffprobe)" ]]; then
    echo "Error: The ffprobe command is not available. Install the ffmpeg OS-level package"
    return 1
  fi

  if [[ -z "$WORKON_HOME" ]]; then
    echo "Error: The WORKON_HOME environment variable is not set. Set it to the virtualenv directory"
    return 1
  fi

  venv_dir=$WORKON_HOME/$venv_name
  activate=$venv_dir/bin/activate

  if ! [[ -f "$activate" ]]; then
    echo "Creating virtualenv $venv_name with Python command $venv_python"
    virtualenv $venv_dir -p $venv_python || return 1
  fi

  if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "Activating virtualenv $venv_name"
    source $activate || return 1
  fi

  pip show $package_name >/dev/null 2>&1
  if [[ $? != 0 ]]; then
    echo "Installing Python package $package_name"
    pip install $package_source || return 1
  fi

  return 0
}

setup_venv "$venv_name" "$venv_python" "plexmediafixup" "$pkg_source" || exit 1

if ! [[ -f "$config_file" ]]; then
  echo "Cannot find plexmediafixup config file: $config_file"
  exit 1
fi

echo "Running plexmediafixup with config file $config_file"
plexmediafixup $config_file || exit 1

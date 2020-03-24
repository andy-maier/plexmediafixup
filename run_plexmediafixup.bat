@rem Run the plexmediafixup script after setting up the environment if needed.
@setlocal
@echo off

rem Customize these variables as needed

rem Name of Python virtualenv that is created:
set venv_name=plexmediafixup

rem Python command to use (with absolute path or in PATH):
set venv_python=python

rem plexmediafixup config file to be used:
set config_file=%HOMEDRIVE%%HOMEPATH%\.config\plexmediafixup.yml

rem Package source to install from:
rem set package_source=git+https://github.com/andy-maier/plexmediafixup.git@master#egg=plexmediafixup
set package_source=plexmediafixup

rem End of customization variables

where virtualenv >nul
if errorlevel 1 (
  echo Error: The virtualenv command is not available. Install the Python virtualenv package
  exit /b 1
)

where ffprobe >nul
if errorlevel 1 (
  echo Error: The ffprobe command is not available. Install the ffmpeg OS-level package
  exit /b 1
)

if "%WORKON_HOME%"=="" (
  echo Error: The WORKON_HOME environment variable is not set. Set it to the virtualenv directory
  exit /b 1
)

set venv_dir=%WORKON_HOME%\%venv_name%
set activate=%venv_dir%\Scripts\activate.bat
set package_name=plexmediafixup

if not exist %activate% (
  echo Creating virtualenv %venv_name% with Python command %venv_python%
  virtualenv %venv_dir% -p %venv_python%
  if errorlevel 1 exit /b 1
)

if "%VIRTUAL_ENV%"=="" (
  echo Activating virtualenv %venv_name%
  call %activate%
  if errorlevel 1 exit /b 1
)

pip show %package_name% >nul 2>&1
if errorlevel 1 (
  echo Installing Python package %package_name% from %package_source%
  pip install %package_source%
  if errorlevel 1 exit /b 1
) else (
  echo Upgrading Python package %package_name% from %package_source%
  pip install --upgrade %package_source%
  if errorlevel 1 exit /b 1
)

if not exist %config_file% (
  echo Cannot find plexmediafixup config file: %config_file%
  exit /b 1
)

echo Running plexmediafixup with config file %config_file%
plexmediafixup %config_file%
if errorlevel 1 exit /b 1

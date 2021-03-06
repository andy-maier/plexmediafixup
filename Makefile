# Makefile for the PlexMediaFixup project.
#
# Supported OS platforms for this Makefile:
#     Linux (any distro)
#     OS-X
#     Windows with UNIX-like env such as CygWin (with a UNIX-like shell and
#       Python in the UNIX-like env)
#     native Windows (with the native Windows command processor and Python in
#       Windows)
#
# Prerequisites for running this Makefile:
#   These commands are used on all supported OS platforms. On native Windows,
#   they may be provided by UNIX-like environments such as CygWin:
#     make (GNU make)
#     python (This Makefile uses the active Python environment, virtual Python
#       environments are supported)
#     pip (in the active Python environment)
#     twine (in the active Python environment)
#   These additional commands are used on Linux, OS-X and on Windows with
#   UNIX-like environments:
#     uname
#     rm, find, xargs, cp
#   These additional commands are used on native Windows:
#     del, copy, rmdir

# No built-in rules needed:
MAKEFLAGS += --no-builtin-rules
.SUFFIXES:

# Python / Pip commands
ifndef PYTHON_CMD
  PYTHON_CMD := python
endif
ifndef PIP_CMD
  PIP_CMD := pip
endif

# Package level
ifndef PACKAGE_LEVEL
  PACKAGE_LEVEL := latest
endif
ifeq ($(PACKAGE_LEVEL),minimum)
  pip_level_opts := -c minimum-constraints.txt
else
  ifeq ($(PACKAGE_LEVEL),latest)
    pip_level_opts := --upgrade
  else
    $(error Error: Invalid value for PACKAGE_LEVEL variable: $(PACKAGE_LEVEL))
  endif
endif

# Make variables are case sensitive and some native Windows environments have
# ComSpec set instead of COMSPEC.
ifndef COMSPEC
  ifdef ComSpec
    COMSPEC = $(ComSpec)
  endif
endif

# Determine OS platform make runs on.
#
# The PLATFORM variable is set to one of:
# * Windows_native: Windows native environment (the Windows command processor
#   is used as shell and its internal commands are used, such as "del").
# * Windows_UNIX: A UNIX-like envieonment on Windows (the UNIX shell and its
#   internal commands are used, such as "rm").
# * Linux: Some Linux distribution
# * Darwin: OS-X / macOS
#
# This in turn determines the type of shell that is used by make when invoking
# commands, and the set of internal shell commands that is assumed to be
# available (e.g. "del" for the Windows native command processor and "rm" for
# a UNIX-like shell). Note that GNU make always uses the value of the SHELL
# make variable to invoke the shell for its commands, but it does not always
# read that variable from the environment. In fact, the approach GNU make uses
# to set the SHELL make variable is very special, see
# https://www.gnu.org/software/make/manual/html_node/Choosing-the-Shell.html.
# On native Windows this seems to be implemented differently than described:
# SHELL is not set to COMSPEC, so we do that here.
#
# Note: Native Windows and CygWin are hard to distinguish: The native Windows
# envvars are set in CygWin as well. COMSPEC (or ComSpec) is set on both
# platforms. Using "uname" will display CYGWIN_NT-.. on both platforms. If the
# CygWin make is used on native Windows, most of the CygWin behavior is visible
# in context of that make (e.g. a SHELL variable is set, PATH gets converted to
# UNIX syntax, execution of batch files requires execute permission, etc.).
ifeq ($(OS),Windows_NT)
  ifdef PWD
    PLATFORM := Windows_UNIX
  else
    PLATFORM := Windows_native
    ifdef COMSPEC
      SHELL := $(subst \,/,$(COMSPEC))
    else
      SHELL := cmd.exe
    endif
    .SHELLFLAGS := /c
  endif
else
  # Values: Linux, Darwin
  PLATFORM := $(shell uname -s)
endif

ifeq ($(PLATFORM),Windows_native)
  # Note: The substituted backslashes must be doubled.
  # Remove files (blank-separated list of wildcard path specs)
  RM_FUNC = del /f /q $(subst /,\\,$(1))
  # Remove files recursively (single wildcard path spec)
  RM_R_FUNC = del /f /q /s $(subst /,\\,$(1))
  # Remove directories (blank-separated list of wildcard path specs)
  RMDIR_FUNC = rmdir /q /s $(subst /,\\,$(1))
  # Remove directories recursively (single wildcard path spec)
  RMDIR_R_FUNC = rmdir /q /s $(subst /,\\,$(1))
  # Copy a file, preserving the modified date
  CP_FUNC = copy /y $(subst /,\\,$(1)) $(subst /,\\,$(2))
  ENV = set
  WHICH = where
else
  RM_FUNC = rm -f $(1)
  RM_R_FUNC = find . -type f -name '$(1)' -delete
  RMDIR_FUNC = rm -rf $(1)
  RMDIR_R_FUNC = find . -type d -name '$(1)' | xargs -n 1 rm -rf
  CP_FUNC = cp -r $(1) $(2)
  ENV = env | sort
  WHICH = which
endif

# Name of this project
project_name := PlexMediaFixup

# Name of this Python package
package_name := plexmediafixup

# Determine if coverage details report generated
# The variable can be passed in as either an environment variable or
# command line variable. When set, generates a set of reports of the
# Python source files showing line by line coverage.
ifdef COVERAGE_REPORT
  coverage_report := --cov-report=annotate --cov-report=html
else
  coverage_report :=
endif

# Directory for coverage html output. Must be in sync with the one in coveragerc.
coverage_html_dir := coverage_html

# Package version (full version, including any pre-release suffixes, e.g. "0.1.0.dev1").
# Note: The package version is defined in version.py.
package_version := $(shell $(PYTHON_CMD) setup.py --version)

# Python versions and bit size
python_full_version := $(shell $(PYTHON_CMD) -c "import sys; sys.stdout.write('{v[0]}.{v[1]}.{v[2]}'.format(v=sys.version_info))")
python_mn_version := $(shell $(PYTHON_CMD) -c "import sys; sys.stdout.write('py{v[0]}{v[1]}'.format(v=sys.version_info))")
python_m_version := $(shell $(PYTHON_CMD) -c "import sys; sys.stdout.write('{v[0]}'.format(v=sys.version_info))")
python_bitsize := $(shell $(PYTHON_CMD) -c "import sys,ctypes; sys.stdout.write('{s}'.format(s=ctypes.sizeof(ctypes.c_void_p)*8))")

# Directory for the generated distribution files
dist_dir := dist

# Distribution archives
# These variables are set with "=" for the same reason as package_version.
bdist_file = $(dist_dir)/$(package_name)-$(package_version)-py2.py3-none-any.whl
sdist_file = $(dist_dir)/$(package_name)-$(package_version).tar.gz

dist_files = $(bdist_file) $(sdist_file)

# Source files in the packages
package_py_files := \
    $(wildcard $(package_name)/*.py) \
    $(wildcard $(package_name)/*/*.py) \

# PyLint config file
pylint_rc_file := pylintrc

# Flake8 config file
flake8_rc_file := .flake8

# Python source files to be checked by PyLint and Flake8
py_src_files := \
    setup.py \
    $(wildcard $(package_name)/*.py) \
    $(wildcard tests/*.py) \
    $(wildcard tests/*/*.py) \
    $(wildcard tests/*/*/*.py) \
    $(wildcard tests/*/*/*/*.py) \

ifdef TESTCASES
  pytest_opts := $(TESTOPTS) -k $(TESTCASES)
else
  pytest_opts := $(TESTOPTS)
endif
pytest_end2end_opts := -v --tb=short $(pytest_opts)

ifeq ($(python_m_version),3)
  pytest_warning_opts := -W default -W ignore::PendingDeprecationWarning -W ignore::ResourceWarning
  pytest_end2end_warning_opts := $(pytest_warning_opts)
else
  pytest_warning_opts := -W default -W ignore::PendingDeprecationWarning
  pytest_end2end_warning_opts := $(pytest_warning_opts)
endif

# Files to be put into distribution archive.
# This is also used for 'include' statements in MANIFEST.in.
dist_included_files := \
    LICENSE \
    README.rst \
    $(wildcard *.py) \
    $(wildcard $(package_name)/*.py) \

PIP_INSTALL_CMD := $(PYTHON_CMD) -m pip install

.PHONY: help
help:
	@echo "Makefile for $(project_name) project"
	@echo "$(package_name) package version: $(package_version)"
	@echo ""
	@echo "Make targets:"
	@echo "  install    - Install $(package_name) (as editable) and its dependent packages"
	@echo "  develop    - Set up development of $(project_name) project"
	@echo "  build      - Build the distribution archive files in: $(dist_dir)"
	@echo "  check      - Run Flake8 on Python sources"
	@echo "  pylint     - Run PyLint on Python sources"
	@echo "  test       - Run unit tests"
	@echo "  all        - Do all of the above"
	@echo "  end2end    - Run end2end tests"
	@echo "  upload     - build + upload the distribution archive files to PyPI"
	@echo "  clean      - Remove any temporary files"
	@echo "  clobber    - Remove everything created to ensure clean start"
	@echo "  pip_list   - Display the installed Python packages as seen by make"
	@echo "  platform   - Display the information about the platform as seen by make"
	@echo "  env        - Display the environment as seen by make"
	@echo ""
	@echo "Environment variables:"
	@echo "  COVERAGE_REPORT - When non-empty, the 'test' target creates a coverage report as"
	@echo "      annotated html files showing lines covered and missed, in the directory:"
	@echo "      $(coverage_html_dir)"
	@echo "      Optional, defaults to no such coverage report."
	@echo "  TESTCASES - When non-empty, 'test' target runs only the specified test cases. The"
	@echo "      value is used for the -k option of pytest (see 'pytest --help')."
	@echo "      Optional, defaults to running all tests."
	@echo "  TESTOPTS - Optional: Additional options for py.tests (see 'pytest --help')."
	@echo "  TEST_INSTALLED - When non-empty, run any tests using the installed version of $(package_name)"
	@echo "      and assume all Python and OS-level prerequisites are already installed."
	@echo "      When set to 'DEBUG', print location from where the $(package_name) package is loaded."
	@echo "  PACKAGE_LEVEL - Package level to be used for installing dependent Python"
	@echo "      packages in 'install' and 'develop' targets:"
	@echo "        latest - Latest package versions available on Pypi"
	@echo "        minimum - A minimum version as defined in minimum-constraints.txt"
	@echo "      Optional, defaults to 'latest'."
	@echo "  PYTHON_CMD - Python command to be used. Useful for Python 3 in some envs."
	@echo "      Optional, defaults to 'python'."
	@echo "  PIP_CMD - Pip command to be used. Useful for Python 3 in some envs."
	@echo "      Optional, defaults to 'pip'."

.PHONY: platform
platform:
	@echo "Makefile: Platform related information as seen by make:"
	@echo "Platform: $(PLATFORM)"
	@echo "Shell used for commands: $(SHELL)"
	@echo "Shell flags: $(.SHELLFLAGS)"
	@echo "Make command location: $(MAKE)"
	@echo "Make version: $(MAKE_VERSION)"
	@echo "Python command name: $(PYTHON_CMD)"
	@echo "Python command location: $(shell $(WHICH) $(PYTHON_CMD))"
	@echo "Python version: $(python_full_version)"
	@echo "Python bite size: $(python_bitsize)"
	@echo "Pip command name: $(PIP_CMD)"
	@echo "Pip command location: $(shell $(WHICH) $(PIP_CMD))"
	@echo "$(package_name) package version: $(package_version)"

.PHONY: pip_list
pip_list:
	@echo "Makefile: Python packages as seen by make:"
	$(PIP_CMD) list

.PHONY: env
env:
	@echo "Makefile: Environment as seen by make:"
	$(ENV)

.PHONY: _check_version
_check_version:
ifeq (,$(package_version))
	$(error Package version could not be determined)
endif

pip_upgrade_$(python_mn_version).done: Makefile
	@echo "Makefile: Installing/upgrading Pip with PACKAGE_LEVEL=$(PACKAGE_LEVEL)"
	-$(call RM_FUNC,$@)
	$(PIP_INSTALL_CMD) $(pip_level_opts) pip
	echo "done" >$@
	@echo "Makefile: Done installing/upgrading Pip"

install_basic_$(python_mn_version).done: Makefile pip_upgrade_$(python_mn_version).done
	@echo "Makefile: Installing/upgrading basic Python packages with PACKAGE_LEVEL=$(PACKAGE_LEVEL)"
	-$(call RM_FUNC,$@)
	$(PYTHON_CMD) tools/remove_duplicate_setuptools.py
	$(PIP_INSTALL_CMD) $(pip_level_opts) setuptools wheel
	echo "done" >$@
	@echo "Makefile: Done installing/upgrading basic Python packages"

install_package_$(python_mn_version).done: Makefile pip_upgrade_$(python_mn_version).done requirements.txt setup.py
	-$(call RM_FUNC,$@)
ifdef TEST_INSTALLED
	@echo "Makefile: Skipping installation of $(package_name) and its Python runtime prerequisites because TEST_INSTALLED is set"
	@echo "Makefile: Checking whether $(package_name) is actually installed:"
	$(PIP_CMD) show $(package_name)
else
	@echo "Makefile: Installing $(package_name) (as editable) and its Python installation prerequisites (with PACKAGE_LEVEL=$(PACKAGE_LEVEL))"
	-$(call RMDIR_FUNC,build $(package_name).egg-info .eggs)
	$(PIP_INSTALL_CMD) $(pip_level_opts) -r requirements.txt
	$(PIP_INSTALL_CMD) $(pip_level_opts) -e .
	@echo "Makefile: Done installing $(package_name) and its Python runtime prerequisites"
endif
	echo "done" >$@

.PHONY: install
install: install_$(python_mn_version).done
	@echo "Makefile: Target $@ done."

install_$(python_mn_version).done: Makefile install_basic_$(python_mn_version).done install_package_$(python_mn_version).done
	@echo "Makefile: Verifying installation of $(package_name) package"
	-$(call RM_FUNC,$@)
	$(PYTHON_CMD) -c "import $(package_name)"
	echo "done" >$@
	@echo "Makefile: Done verifying installation of $(package_name) package"

.PHONY: develop
develop: develop_$(python_mn_version).done
	@echo "Makefile: Target $@ done."

develop_$(python_mn_version).done: pip_upgrade_$(python_mn_version).done install_$(python_mn_version).done install_basic_$(python_mn_version).done dev-requirements.txt
	@echo "Makefile: Installing/upgrading development requirements (with PACKAGE_LEVEL=$(PACKAGE_LEVEL))"
	-$(call RM_FUNC,$@)
	$(PIP_INSTALL_CMD) $(pip_level_opts) -r dev-requirements.txt
	echo "done" >$@
	@echo "Makefile: Done installing/upgrading development requirements"

.PHONY: build
build: $(bdist_file) $(sdist_file)
	@echo "Makefile: Target $@ done."

.PHONY: check
check: flake8_$(python_mn_version).done safety_$(python_mn_version).done
	@echo "Makefile: Target $@ done."

.PHONY: pylint
pylint: pylint_$(python_mn_version).done
	@echo "Makefile: Target $@ done."

.PHONY: all
all: install develop build check pylint test
	@echo "Makefile: Target $@ done."

.PHONY: clobber
clobber: clean
	@echo "Makefile: Removing everything for a fresh start"
	-$(call RM_FUNC,*.done $(dist_files) $(dist_dir)/$(package_name)-$(package_version)*.egg $(package_name)/*cover)
	-$(call RMDIR_FUNC,.tox $(coverage_html_dir))
	@echo "Makefile: Done removing everything for a fresh start"
	@echo "Makefile: Target $@ done."

# Also remove any build products that are dependent on the Python version
.PHONY: clean
clean:
	@echo "Makefile: Removing temporary build products"
	-$(call RM_R_FUNC,*.pyc)
	-$(call RMDIR_R_FUNC,__pycache__)
	-$(call RM_FUNC,MANIFEST parser.out .coverage $(package_name)/parser.out)
	-$(call RMDIR_FUNC,build .cache $(package_name).egg-info .eggs)
	@echo "Makefile: Done removing temporary build products"
	@echo "Makefile: Target $@ done."

.PHONY: upload
upload: _check_version $(dist_files)
	@echo "Makefile: Checking files before uploading to PyPI"
	twine check $(dist_files)
	@echo "Makefile: Uploading to PyPI: $(package_name) $(package_version)"
	twine upload $(dist_files)
	@echo "Makefile: Done uploading to PyPI"
	@echo "Makefile: Target $@ done."

# Note: distutils depends on the right files specified in MANIFEST.in, even when
# they are already specified e.g. in 'package_data' in setup.py.
# We generate the MANIFEST.in file automatically, to have a single point of
# control (this Makefile) for what gets into the distribution archive.
MANIFEST.in: Makefile $(dist_included_files)
	@echo "Makefile: Creating the manifest input file"
	echo "# MANIFEST.in file generated by Makefile - DO NOT EDIT!!" >$@
ifeq ($(PLATFORM),Windows_native)
	for %%f in ($(dist_included_files)) do (echo include %%f >>$@)
else
	echo "$(dist_included_files)" |xargs -n 1 echo include >>$@
endif
	@echo "Makefile: Done creating the manifest input file: $@"

# Distribution archives.
# Note: Deleting MANIFEST causes distutils (setup.py) to read MANIFEST.in and to
# regenerate MANIFEST. Otherwise, changes in MANIFEST.in will not be used.
# Note: Deleting build is a safeguard against picking up partial build products
# which can lead to incorrect hashbangs in scripts in wheel archives.
$(bdist_file) $(sdist_file): _check_version setup.py MANIFEST.in $(dist_included_files)
	@echo "Makefile: Creating the distribution archive files"
	-$(call RM_FUNC,MANIFEST)
	-$(call RMDIR_FUNC,build $(package_name).egg-info .eggs)
	$(PYTHON_CMD) setup.py sdist -d $(dist_dir) bdist_wheel -d $(dist_dir) --universal
	@echo "Makefile: Done creating the distribution archive files: $(bdist_file) $(sdist_file)"

# TODO: Once pylint has no more errors, remove the dash "-"
# PyLint status codes:
# * 0 if everything went fine
# * 1 if fatal messages issued
# * 2 if error messages issued
# * 4 if warning messages issued
# * 8 if refactor messages issued
# * 16 if convention messages issued
# * 32 on usage error
# Status 1 to 16 will be bit-ORed.
# The make command checks for statuses: 1,2,32
pylint_$(python_mn_version).done: develop_$(python_mn_version).done Makefile $(pylint_rc_file) $(py_src_files)
	@echo "Makefile: Running Pylint"
	-$(call RM_FUNC,$@)
	pylint --version
	-pylint --rcfile=$(pylint_rc_file) $(py_src_files)
	echo "done" >$@
	@echo "Makefile: Done running Pylint"

flake8_$(python_mn_version).done: develop_$(python_mn_version).done Makefile $(flake8_rc_file) $(py_src_files)
	@echo "Makefile: Running Flake8"
	-$(call RM_FUNC,$@)
	flake8 --version
	flake8 --statistics --config=$(flake8_rc_file) --filename='*' $(py_src_files)
	echo "done" >$@
	@echo "Makefile: Done running Flake8"

safety_$(python_mn_version).done: develop_$(python_mn_version).done Makefile minimum-constraints.txt
	@echo "Makefile: Running pyup.io safety check"
	-$(call RM_FUNC,$@)
	-safety check -r minimum-constraints.txt --full-report
	echo "done" >$@
	@echo "Makefile: Done running pyup.io safety check"

ifdef TEST_INSTALLED
  test_deps =
else
  test_deps = develop_$(python_mn_version).done
endif

.PHONY: test
test: $(test_deps)
	@echo "Makefile: Running unit tests"
	py.test --color=yes --cov $(package_name) $(coverage_report) --cov-config coveragerc $(pytest_warning_opts) $(pytest_opts) tests/unittest -s
	@echo "Makefile: Done running unit tests"

.PHONY: end2end
end2end: develop_$(python_mn_version).done
	@echo "Makefile: Running end2end tests"
	py.test --color=yes $(pytest_end2end_warning_opts) $(pytest_end2end_opts) tests/end2endtest -s
	@echo "Makefile: Done running end2end tests"

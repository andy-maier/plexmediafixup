"""
Formatter class for argparse package that respects newlines in help strings.
"""

from __future__ import print_function, absolute_import

import argparse


class SmartFormatter(argparse.HelpFormatter):
    """
    Formatter class for argparse package that respects newlines in help
    strings.

    Idea and code from: https://stackoverflow.com/a/22157136

    Usage:
        If an argparse argument help text starts with 'R|', it will be treated
        as a *raw* string that does line formatting on its own by specifying
        newlines appropriately. The string should not exceed 55 characters per
        line. Indentation handling is still applied automatically and does not
        need to be specified within the string.

        Otherwise, the strings are formatted as normal and newlines are
        treated like blanks.

    Limitations:
        It seems this only works for the `help` argument of
        `ArgumentParser.add_argument()`, and not for group descriptions,
        and usage, description, and epilog of ArgumentParser.
    """

    def _split_lines(self, text, width):
        if text.startswith('R|'):
            return text[2:].splitlines()
        return argparse.HelpFormatter._split_lines(self, text, width)

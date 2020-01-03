"""
Formatter class for argparse package that respects newlines in help strings.

Idea and code from: https://stackoverflow.com/a/22157136
"""

from __future__ import print_function, absolute_import
import argparse


class SmartFormatter(argparse.HelpFormatter):
    """
    Formatter class for argparse package that respects newlines in help text
    strings.

    Usage:

        If an argparse argument help text starts with 'R|', it will be treated
        as a *raw* string that does line formatting on its own by specifying
        newlines appropriately. The resulting lines in the help text string
        should not exceed 55 characters per line. Indentation is still applied
        automatically and does not need to be specified within the help text
        string.

        Otherwise, the strings are formatted as normal (which means that
        newlines are treated like blanks).

    Limitations:

        This only works for the `help` argument of `add_argument()`, but not
        for group descriptions, or usage, description, and epilog of
        `ArgumentParser`.

    Example:

        import argparse

        argparser = argparse.ArgumentParser(. . .,
                                            formatter_class=SmartFormatter)

        argparser.add_argument(
            'server', metavar='SERVER',
            help='R|Host name or URL of the server, in this format:\\n'
                 '    [{scheme}://]{host}[:{port}]\\n'
                 '- scheme: Protocol to be used:\\n'
                 '    - "https" for HTTPS protocol (default)\\n'
                 '    - "http" for HTTP protocol\\n'
                 '- host: Host name, as follows:\\n'
                 '    - short or fully qualified DNS hostname\\n'
                 '    - literal IPv4 address (dotted)\\n'
                 '    - literal IPv6 address (RFC 3986) with zone\\n'
                 '      identifier extensions (RFC 6874)\\n'
                 '      supporting "-" or "%" for the delimiter\\n'
                 '- port: Port to be used, with these defaults:\\n'
                 '    - 5988 for HTTP protocol\\n'
                 '    - 5989 for HTTPS protocol\\n')
    """

    def _split_lines(self, text, width):
        if text.startswith('R|'):
            return text[2:].splitlines()
        return argparse.HelpFormatter._split_lines(self, text, width)

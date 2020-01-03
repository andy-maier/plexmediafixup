"""
Unicode conversion functions.
"""

import six


def ensure_unicode(obj, encoding="utf-8"):
    """
    Return the input string as a unicode string.

    Binary strings are converted to unicode strings using the specified
    encoding.

    Non-strings are returned unchanged.
    """
    if isinstance(obj, six.binary_type):
        return obj.decode(encoding)
    return obj


def ensure_bytes(obj, encoding="utf-8"):
    """
    Return the input string as a byte string.

    Unicode strings are converted to byte strings using the specified
    encoding.

    Byte strings are returned unchanged, so if they have a different encoding
    than the specified encoding, they keep their encoding.

    Non-strings are returned unchanged.
    """
    if isinstance(obj, six.text_type):
        return obj.encode(encoding)
    return obj

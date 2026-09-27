"""Escape sequence handling for INI file values.

This module interprets backslash escape sequences as they appear in INI
file values and can re-encode arbitrary strings back into escaped form.

Design decisions
----------------
1. Only the escapes documented below are recognised. An unrecognised
   escape (e.g. ``\\q``) raises EscapeError rather than guessing, so that
   typos surface immediately instead of silently corrupting data.
2. A lone backslash at the end of a value is an error: an unfinished
   escape sequence has no defined meaning.
3. ``\\xNN`` reads exactly two hexadecimal digits. If fewer than two hex
   digits follow, the sequence is rejected. This avoids ambiguity between
   ``\\x1`` followed by the literal character ``2`` and ``\\x12``.
4. ``\\uNNNN`` reads exactly four hexadecimal digits, for the same reason.
5. ``escape()`` is the inverse of ``unescape()`` for every input that
   ``unescape`` can produce. It encodes control characters and
   non-ASCII characters with ``\\x`` / ``\\u`` so the output is safe to
   store in an INI file read by a Latin-1 or ASCII-aware parser.
"""


import re


class EscapeError(ValueError):
    """Raised when an escape sequence is malformed or unrecognised."""


# Maps a single-character escape code to its literal value.
# Kept as a module-level constant so escape() and unescape() stay in lockstep.
_SIMPLE = {
    "0": "\x00",
    "a": "\a",
    "b": "\b",
    "t": "\t",
    "n": "\n",
    "v": "\v",
    "f": "\f",
    "r": "\r",
    '"': '"',
    "'": "'",
    "\\": "\\",
    "=": "=",
    ";": ";",
    "#": "#",
    ":": ":",
}

# Reverse of _SIMPLE. Built once at import time. If two codes map to the
# same character (none currently do, but guard against future additions),
# the first one encountered wins, which is arbitrary but deterministic.
_SIMPLE_REVERSE = {}
for _code, _char in _SIMPLE.items():
    _SIMPLE_REVERSE.setdefault(_char, _code)
del _code, _char


_HEX_RE = re.compile(r"[0-9A-Fa-f]")


def _hex_value(digits, source, pos):
    """Convert a string of hex digits to an integer, or raise EscapeError."""
    if not _HEX_RE.match(digits):
        raise EscapeError(
            "invalid hex digit(s) at position %d: %r" % (pos, digits)
        )
    return int(digits, 16)


def unescape(value):
    """Interpret backslash escapes in *value* and return the decoded string.

    Recognised escapes::

        \\0  \\a  \\b  \\t  \\n  \\v  \\f  \\r
        \\"  \\'  \\\\  \\=  \\;  \\#  \\:
        \\xNN        (exactly two hex digits)
        \\uNNNN      (exactly four hex digits)

    Any other backslash-prefixed sequence, a trailing lone backslash, or a
    short ``\\x`` / ``\\u`` sequence raises :class:`EscapeError`.
    """
    if not isinstance(value, str):
        raise TypeError("unescape() expects str, got %s" % type(value).__name__)

    out = []
    i = 0
    n = len(value)
    while i < n:
        ch = value[i]
        if ch != "\\":
            out.append(ch)
            i += 1
            continue

        # ch == backslash
        if i + 1 >= n:
            raise EscapeError("trailing backslash at position %d" % i)

        code = value[i + 1]

        if code in _SIMPLE:
            out.append(_SIMPLE[code])
            i += 2
            continue

        if code == "x":
            if i + 3 >= n:
                raise EscapeError(
                    "\\x needs two hex digits at position %d" % i
                )
            digits = value[i + 2 : i + 4]
            cp = _hex_value(digits, value, i)
            if cp > 0xFF:
                # int(..., 16) would not produce >0xFF for two digits, but
                # guard anyway in case the digit set is ever widened.
                raise EscapeError("\\x value out of range at position %d" % i)
            out.append(chr(cp))
            i += 4
            continue

        if code == "u":
            if i + 5 >= n:
                raise EscapeError(
                    "\\u needs four hex digits at position %d" % i
                )
            digits = value[i + 2 : i + 6]
            cp = _hex_value(digits, value, i)
            if cp > 0x10FFFF:
                raise EscapeError("\\u value out of range at position %d" % i)
            out.append(chr(cp))
            i += 6
            continue

        raise EscapeError(
            "unknown escape \\%r at position %d" % (code, i)
        )

    # Recombine lone surrogates so astral-plane characters round-trip.
    return "".join(out).encode("utf-16", "surrogatepass").decode("utf-16")


def escape(value):
    """Return *value* with special characters encoded as backslash escapes.

    The output is accepted by :func:`unescape` unchanged and contains only
    ASCII characters: control characters become ``\\t`` / ``\\n`` etc.,
    non-ASCII characters become ``\\xNN`` or ``\\uNNNN``.
    """
    if not isinstance(value, str):
        raise TypeError("escape() expects str, got %s" % type(value).__name__)

    out = []
    for ch in value:
        if ch in _SIMPLE_REVERSE:
            out.append("\\" + _SIMPLE_REVERSE[ch])
        elif 0x20 <= ord(ch) <= 0x7E:
            out.append(ch)
        else:
            cp = ord(ch)
            if cp <= 0xFF:
                out.append("\\x%02X" % cp)
            elif cp <= 0xFFFF:
                out.append("\\u%04X" % cp)
            else:
                # Surrogate-pair encode so the output stays within BMP and
                # round-trips through unescape().
                hi = 0xD800 + (cp - 0x10000) // 0x400
                lo = 0xDC00 + (cp - 0x10000) % 0x400
                out.append("\\u%04X\\u%04X" % (hi, lo))
    return "".join(out)

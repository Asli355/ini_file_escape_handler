# INI File Escape Handler

Interprets and re-encodes backslash escape sequences in INI file values.

```python
from ini_file_escape_handler import unescape, escape, EscapeError

unescape("line1\\nline2\\t\\\\done")   # 'line1\nline2\t\\done'
unescape("\\x41\\u00E9")               # 'Aé'
escape("a\tb\\c=d")                   # 'a\\tb\\\\c\\=d'
```

## Why this exists

INI parsers split values on `=` and treat `;` / `#` as comment markers. When
a value needs to contain those characters literally, or needs newlines and
tabs, the only portable encoding is backslash escapes. Python's
`configparser` does not interpret them, leaving that to the caller. This
library is that caller.

The trade-off: this is a single, strict interpretation. It does not try to
mimic any specific INI dialect's quirks. Recognised escapes are `\0 \a \b \t
\n \v \f \r \" \' \\ \= \; \# \:`, plus `\xNN` (two hex digits) and `\uNNNN`
(four hex digits). Anything else is an error.

## The awkward edge

`\x` reads **exactly two** hex digits and `\u` reads **exactly four**. So
`\x411` decodes to `A1` (the escape `\x41` plus a literal `1`), not to the
character U+0411. If you need a hex escape followed immediately by a literal
hex digit, separate them with `\\` or restructure the value. A trailing
backslash with nothing after it is also an error, not a literal backslash.

## Exports

- `unescape(value: str) -> str` — decode escape sequences.
- `escape(value: str) -> str` — encode a string so `unescape` recovers it.
- `EscapeError` — subclass of `ValueError`, raised on malformed input.

import unittest

from ini_file_escape_handler import unescape, escape, EscapeError


class TestUnescapeSimple(unittest.TestCase):
    def test_plain_string_passes_through(self):
        self.assertEqual(unescape("hello world"), "hello world")

    def test_empty_string(self):
        self.assertEqual(unescape(""), "")

    def test_tab_escape(self):
        self.assertEqual(unescape("a\\tb"), "a\tb")

    def test_newline_escape(self):
        self.assertEqual(unescape("line1\\nline2"), "line1\nline2")

    def test_carriage_return_escape(self):
        self.assertEqual(unescape("a\\rb"), "a\rb")

    def test_backspace_escape(self):
        self.assertEqual(unescape("a\\bb"), "a\bb")

    def test_form_feed_escape(self):
        self.assertEqual(unescape("a\\fb"), "a\fb")

    def test_vertical_tab_escape(self):
        self.assertEqual(unescape("a\\vb"), "a\vb")

    def test_null_escape(self):
        self.assertEqual(unescape("a\\0b"), "a\x00b")

    def test_bell_escape(self):
        self.assertEqual(unescape("a\\ab"), "a\ab")

    def test_escaped_backslash(self):
        self.assertEqual(unescape("a\\\\b"), "a\\b")

    def test_escaped_double_quote(self):
        self.assertEqual(unescape('a\\"b'), 'a"b')

    def test_escaped_single_quote(self):
        self.assertEqual(unescape("a\\'b"), "a'b")

    def test_escaped_equals(self):
        self.assertEqual(unescape("a\\=b"), "a=b")

    def test_escaped_semicolon(self):
        self.assertEqual(unescape("a\\;b"), "a;b")

    def test_escaped_hash(self):
        self.assertEqual(unescape("a\\#b"), "a#b")

    def test_escaped_colon(self):
        self.assertEqual(unescape("a\\:b"), "a:b")

    def test_multiple_escapes_in_sequence(self):
        self.assertEqual(unescape("\\t\\n\\\\"), "\t\n\\")


class TestUnescapeHex(unittest.TestCase):
    def test_hex_lowercase(self):
        self.assertEqual(unescape("\\x41"), "A")

    def test_hex_uppercase(self):
        self.assertEqual(unescape("\\x6A"), "j")

    def test_hex_zero(self):
        self.assertEqual(unescape("\\x00"), "\x00")

    def test_hex_max_byte(self):
        self.assertEqual(unescape("\\xFF"), "\xFF")

    def test_hex_followed_by_literal_hex_letter(self):
        # \x41 is 'A', the following '1' is a literal character, not part
        # of the escape.
        self.assertEqual(unescape("\\x411"), "A1")

    def test_hex_too_short_raises(self):
        with self.assertRaises(EscapeError):
            unescape("\\x4")

    def test_hex_missing_digits_raises(self):
        with self.assertRaises(EscapeError):
            unescape("\\x")

    def test_hex_invalid_digit_raises(self):
        with self.assertRaises(EscapeError):
            unescape("\\xZZ")


class TestUnescapeUnicode(unittest.TestCase):
    def test_unicode_basic(self):
        self.assertEqual(unescape("\\u00E9"), "é")

    def test_unicode_cjk(self):
        self.assertEqual(unescape("\\u4E2D"), "中")

    def test_unicode_max_bmp(self):
        self.assertEqual(unescape("\\uFFFF"), "\uFFFF")

    def test_unicode_too_short_raises(self):
        with self.assertRaises(EscapeError):
            unescape("\\u00E")

    def test_unicode_missing_digits_raises(self):
        with self.assertRaises(EscapeError):
            unescape("\\u")

    def test_unicode_invalid_digit_raises(self):
        with self.assertRaises(EscapeError):
            unescape("\\uGGGG")


class TestUnescapeErrors(unittest.TestCase):
    def test_trailing_backslash_raises(self):
        with self.assertRaises(EscapeError):
            unescape("abc\\")

    def test_unknown_escape_raises(self):
        with self.assertRaises(EscapeError):
            unescape("\\q")

    def test_unknown_escape_message_contains_position(self):
        try:
            unescape("xy\\q")
        except EscapeError as exc:
            self.assertIn("2", str(exc))
        else:
            self.fail("expected EscapeError")

    def test_type_error_on_non_string(self):
        with self.assertRaises(TypeError):
            unescape(123)


class TestEscape(unittest.TestCase):
    def test_plain_string(self):
        self.assertEqual(escape("hello"), "hello")

    def test_empty_string(self):
        self.assertEqual(escape(""), "")

    def test_tab(self):
        self.assertEqual(escape("\t"), "\\t")

    def test_newline(self):
        self.assertEqual(escape("\n"), "\\n")

    def test_backslash(self):
        self.assertEqual(escape("\\"), "\\\\")

    def test_equals(self):
        self.assertEqual(escape("="), "\\=")

    def test_semicolon(self):
        self.assertEqual(escape(";"), "\\;")

    def test_non_ascii_latin1(self):
        self.assertEqual(escape("é"), "\\xE9")

    def test_non_ascii_bmp(self):
        self.assertEqual(escape("中"), "\\u4E2D")

    def test_control_char_null(self):
        self.assertEqual(escape("\x00"), "\\0")

    def test_control_char_del(self):
        # DEL (0x7F) has no simple-code mapping, so it uses \x.
        self.assertEqual(escape("\x7F"), "\\x7F")

    def test_type_error_on_non_string(self):
        with self.assertRaises(TypeError):
            escape(None)


class TestRoundTrip(unittest.TestCase):
    def _round_trip(self, original):
        encoded = escape(original)
        decoded = unescape(encoded)
        self.assertEqual(decoded, original,
                         "round-trip failed: %r -> %r -> %r"
                         % (original, encoded, decoded))

    def test_plain(self):
        self._round_trip("hello world")

    def test_with_tab_and_newline(self):
        self._round_trip("col1\tcol2\nrow2")

    def test_with_backslash(self):
        self._round_trip("path\\to\\file")

    def test_with_special_chars(self):
        self._round_trip("key=value;comment #section:done")

    def test_with_latin1(self):
        self._round_trip("café résumé")

    def test_with_cjk(self):
        self._round_trip("中文测试")

    def test_with_emoji(self):
        # Astral plane character: requires surrogate-pair encoding.
        self._round_trip("😀")

    def test_mixed(self):
        self._round_trip("a\tb=c\\d;é中😀")

    def test_empty(self):
        self._round_trip("")

    def test_all_control_chars(self):
        self._round_trip("".join(chr(i) for i in range(0x20)))

    def test_all_latin1(self):
        self._round_trip("".join(chr(i) for i in range(256)))


class TestDoubleEscape(unittest.TestCase):
    def test_escaped_backslash_then_real_escape(self):
        # \\t means literal backslash followed by 't'.
        self.assertEqual(unescape("\\\\t"), "\\t")

    def test_escaped_backslash_then_newline_escape(self):
        # \\ \n means literal backslash then newline.
        self.assertEqual(unescape("\\\\\\n"), "\\\n")


if __name__ == "__main__":
    unittest.main()

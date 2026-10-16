import html
import re

# The signatures. ISFOC is the old font we decode (legacy_hindi.ISFOC_MAP);
# FONT2 is the second, unsupported one.
ISFOC_RE = re.compile(r"BÉE|àÉ|ãÉ|ºÉ")
FONT2_RE = re.compile(r"Eò|®ú|½þ")


# Verbatim from LS13/2/6815: an old-font page with glyphs stored as HTML named entities.
_ENTITY_ENCODED = (
    "(J&Eacute;V&Eacute;&Ouml;&reg;&uacute;&Eacute;&frac12;&thorn;&Eacute;&auml;)"
)


class TestTheEncodingIsMixed:
    def test_named_entities_hide_the_old_font_from_a_literal_regex(self):
        assert not ISFOC_RE.search(_ENTITY_ENCODED) and not FONT2_RE.search(
            _ENTITY_ENCODED
        ), "raw regex must find nothing here -- that is what made it lie"
        decoded = html.unescape(_ENTITY_ENCODED)
        assert FONT2_RE.search(decoded), "after unescape the font is visible"

    def test_unescape_is_what_makes_the_glyphs_appear(self):
        assert "&Eacute;" in _ENTITY_ENCODED
        assert "É" not in _ENTITY_ENCODED
        assert "É" in html.unescape(_ENTITY_ENCODED)

    def test_literal_pages_also_exist_so_you_cannot_just_swap_the_regex(self):
        literal = "<P>BÉE&#136;àÉ ºÉ</P>"
        assert ISFOC_RE.search(literal), "literal pages match without decoding"
        # unescape leaves literal glyphs alone, so decoding first is safe for both kinds.
        assert ISFOC_RE.search(html.unescape(literal))


class TestDevanagariIsNumericEntities:
    def test_devanagari_is_stored_as_numeric_entities(self):
        stored = "&#2358;&#2381;&#2352;&#2368;"  # श्री
        assert "श्री" not in stored
        assert html.unescape(stored) == "श्री"


class TestRoutingIsSafeToGrep:
    def test_the_anchor_tag_is_pure_ascii_so_a_regex_can_see_it(self):
        from debate_fetch_legacy import MODERN_ANCHOR_RE, looks_legacy

        modern = '<p><A name="225*1">HON. SPEAKER:</p>'
        legacy = '<p><A name="4444">MR. SPEAKER:</p>'

        assert MODERN_ANCHOR_RE.search(modern)
        assert not MODERN_ANCHOR_RE.search(legacy)
        assert not looks_legacy(modern)
        assert looks_legacy(legacy)

    def test_routing_survives_entity_encoding(self):
        from debate_fetch_legacy import looks_legacy

        page = '<p><A name="225*1">' + _ENTITY_ENCODED + "</p>"
        assert not looks_legacy(page)
        assert not looks_legacy(html.unescape(page))

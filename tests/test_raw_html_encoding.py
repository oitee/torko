"""How `debates.raw_html` stores non-ASCII -- and why grepping it lies.

This pins the fact behind the correction in db/init/05-debates.sql. The old
guidance (recommended in that file AND in .claude/STATE.md, which called the
query "the highest-value query in the project") measured old-font pages with a
literal-glyph regex over raw_html. That regex found ~1% of them and reported it
as the whole corpus:

    LS13 old-font debates:  regex said 43   truth 4,443
    second font:            regex said  7   truth   370

The cause is that this source mixes representations. Most old-font pages store
their glyphs as HTML NAMED entities (&Eacute;), a minority store them
literally, and Unicode Devanagari is stored as NUMERIC entities (&#2358;).

The parser was never affected -- both readers go through BeautifulSoup, which
decodes entities before matching. Only hand-written SQL over raw_html was. That
is precisely the tooling used to decide what to work on next, which is what
made a silent 100x undercount expensive.

These tests are offline and use verbatim fragments from the real corpus.
"""
import html
import re

# The signatures. ISFOC is the old font we decode (legacy_hindi.ISFOC_MAP);
# FONT2 is the second, unsupported one.
ISFOC_RE = re.compile(r"BÉE|àÉ|ãÉ|ºÉ")
FONT2_RE = re.compile(r"Eò|®ú|½þ")


# VERBATIM from LS13 / session 2 / dbslno 6815 -- a real old-font page whose
# glyphs are stored as HTML named entities. Decoded it reads
# "(JÉVÉÖ®úÉ½þÉä)", which in the second font is the constituency खजुराहो
# (Khajuraho). Note "&reg;&uacute;" -> "®ú" and "&frac12;&thorn;" -> "½þ":
# both are second-font signature pairs, and both are invisible until decoded.
_ENTITY_ENCODED = (
    "(J&Eacute;V&Eacute;&Ouml;&reg;&uacute;&Eacute;&frac12;&thorn;&Eacute;&auml;)"
)


class TestTheEncodingIsMixed:
    def test_named_entities_hide_the_old_font_from_a_literal_regex(self):
        """The whole bug in one assertion."""
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
        """A minority of pages ARE stored literally. Any correct measurement
        must handle both, which is why the answer is 'decode first', not
        'write a cleverer regex'."""
        literal = "<P>BÉE&#136;àÉ ºÉ</P>"
        assert ISFOC_RE.search(literal), "literal pages match without decoding"
        # unescape leaves an already-literal page's glyphs alone, so decoding
        # first is safe for both kinds -- it is strictly the better default.
        assert ISFOC_RE.search(html.unescape(literal))


class TestDevanagariIsNumericEntities:
    def test_devanagari_is_stored_as_numeric_entities(self):
        """`WHERE raw_html LIKE '%श्री%'` returns ZERO over all 64,921 rows.
        This is why."""
        stored = "&#2358;&#2381;&#2352;&#2368;"  # श्री
        assert "श्री" not in stored
        assert html.unescape(stored) == "श्री"


class TestRoutingIsSafeToGrep:
    def test_the_anchor_tag_is_pure_ascii_so_a_regex_can_see_it(self):
        """Routing is the one question a plain SQL regex CAN answer, because
        the anchor carries no non-ASCII. This is the real decision the code
        makes: looks_legacy() == not MODERN_ANCHOR_RE.search(html)."""
        from debate_fetch_legacy import MODERN_ANCHOR_RE, looks_legacy

        modern = '<p><A name="225*1">HON. SPEAKER:</p>'
        legacy = '<p><A name="4444">MR. SPEAKER:</p>'

        assert MODERN_ANCHOR_RE.search(modern)
        assert not MODERN_ANCHOR_RE.search(legacy)
        assert not looks_legacy(modern)
        assert looks_legacy(legacy)

    def test_routing_survives_entity_encoding(self):
        """An old-font page can still carry a modern anchor -- 4,115 LS14
        debates do. Entity-encoding the body must not change the routing."""
        from debate_fetch_legacy import looks_legacy

        page = '<p><A name="225*1">' + _ENTITY_ENCODED + "</p>"
        assert not looks_legacy(page)
        assert not looks_legacy(html.unescape(page))

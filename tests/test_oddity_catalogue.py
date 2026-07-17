"""
Pins every worked example in internal_docs/021_ODDITY_CATALOGUE.md.

The catalogue is a list of *classes* of problem, each with a reproduced example.
An example nobody re-runs is how this project has twice ended up quoting a
confident claim that had stopped being true. These tests are what stop that:
if an oddity is fixed, or drifts, the matching test fails and the doc gets
updated rather than quietly rotting.

So a failure here is NOT necessarily a bug. Several of these assert that
something is still broken (entries 1 and 6). If one of those goes green,
something got fixed and the catalogue entry should be marked retired.
"""
from db_roster import load_db_roster
from debate_fetch import _folded_key, _folded_lookup
from legacy_hindi import ISFOC_MAP, decode_legacy_hindi


class TestSecondFont:
    """Catalogue entry 1 — a second old font, with its own conflicting table.

    Asserts the font is still UNHANDLED. These go green when it gets support.
    """

    def test_second_font_mahoday_does_not_decode(self):
        # Should be महोदय ("sir"). Our ISFOC table has no idea.
        assert decode_legacy_hindi("¨É½þÉänùªÉ") != "महोदय"

    def test_second_font_bijapur_is_almost_readable(self):
        # The trap: shared letters decode, so it reads as slightly-broken Hindi
        # rather than as a foreign font, and gets misfiled as a missing row.
        assert decode_legacy_hindi("¤ÉÒVÉÉ{ÉÖ®ú") == "बÒजापुरú"

    def test_our_rows_are_confidently_wrong_on_second_font_text(self):
        # LS13/2/6946: a row added in 60cfd6d turns Prakash into फ्रòाश.
        # Garbage either way, no turn moved -- but recorded, not rediscovered.
        assert decode_legacy_hindi("|ÉEòÉ¶É") == "फ्रòाश"


class TestMisroutedEra:
    """Catalogue entry 2 — a debate sorted into the wrong era.

    The point: the text is fine, the routing was wrong.
    """

    def test_misrouted_label_decodes_perfectly(self):
        # Jagdambika Pal, a real MP, from the debate that was handled as recent
        # while actually being in the old font. Nothing wrong with the data.
        assert decode_legacy_hindi("* gÉÉÒ VÉMÉnÉÎà¤ÉBÉEÉ {ÉÉãÉ") == "। श्री जगदम्बिका पाल"


class TestSquashCollisions:
    """Catalogue entry 3 — two people, one squashed key. A ceiling, not a bug."""

    def _collisions(self):
        groups: dict[str, set] = {}
        for m in load_db_roster(13):
            key = _folded_key(m["mpName"])
            if key:
                groups.setdefault(key, set()).add(m["mpCode"])
        return {k: v for k, v in groups.items() if len(v) > 1}

    def test_twenty_six_keys_name_more_than_one_person(self):
        assert len(self._collisions()) == 26

    def test_every_colliding_key_is_dropped(self):
        # Never guess, proven over the full roster: not one survives the lookup.
        index = _folded_lookup(load_db_roster(13))
        assert [k for k in self._collisions() if k in index] == []

    def test_four_radhakrishnans_collide(self):
        assert len(self._collisions()["rdhkrishnan"]) == 4

    def test_there_are_four_triples_not_three(self):
        # Earlier docs list three. `rajendran` was never written down.
        triples = {k for k, v in self._collisions().items() if len(v) == 3}
        assert triples == {"chaudhry", "elngovan", "rajendran"}


class TestIdenticalNames:
    """Catalogue entry 4 — two people, one *name*. A ceiling the data imposes."""

    def test_two_distinct_mps_are_both_called_chandra_shekhar(self):
        codes = {m["mpCode"] for m in load_db_roster(13) if m["mpName"] == "Chandra Shekhar"}
        assert codes == {"72", "5647"}


class TestWholeWordRowsDestroyedAfterSubstitution:
    """Catalogue entry 6 — rows that substitute correctly, then get mangled.

    The rule is mechanical: every row whose output contains a `ि` is re-shifted
    by the visual->logical rule, which cannot tell final text from intermediate
    state. Asserts the rows are still dead; green means someone fixed it.
    """

    def _whole_word_rows(self):
        return {k: v for k, v in ISFOC_MAP.items() if len(v) > 3 and len(k) > 1}

    def test_rows_with_a_matra_are_dead(self):
        dead = {v for k, v in self._whole_word_rows().items() if decode_legacy_hindi(k) != v}
        assert dead == {"क्रिश्चियन", "क्रिश्चियन्स", "बालिका", "कमिटमेंट"}

    def test_exactly_the_matra_rows_are_the_dead_ones(self):
        # Not a coincidence to be spot-fixed: the `ि` is the whole predictor.
        for word, intended in self._whole_word_rows().items():
            survives = decode_legacy_hindi(word) == intended
            assert survives is ("ि" not in intended), intended

    def test_balika_shifts_its_matra_back(self):
        assert decode_legacy_hindi("¤ÉÉÉÊãÉBÉEÉ") == "बालकिा"  # wanted बालिका

    def test_bare_latin_letters_are_protected_not_dead(self):
        # The false alarm the catalogue records: testing rows in isolation flags
        # F/j/Y as dead. They are fine in context -- a bare Latin letter is
        # correctly protected as English by the f6f134f guard.
        assert decode_legacy_hindi("F") == "F"
        assert decode_legacy_hindi("FÉ") == "क्ष"
        assert decode_legacy_hindi("jÉ") == "त्र"
        assert decode_legacy_hindi("YÉ") == "ज्ञ"

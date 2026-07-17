from db_roster import load_db_roster
from debate_fetch import _folded_key, _folded_lookup
from legacy_hindi import ISFOC_MAP, decode_legacy_hindi


class TestSecondFont:
    def test_second_font_mahoday_does_not_decode(self):
        # Should decode to महोदय ("sir").
        assert decode_legacy_hindi("¨É½þÉänùªÉ") != "महोदय"

    def test_second_font_bijapur_is_almost_readable(self):
        # Shared letters decode, so it reads as slightly broken Hindi, not as a foreign font.
        assert decode_legacy_hindi("¤ÉÒVÉÉ{ÉÖ®ú") == "बÒजापुरú"

    def test_our_rows_are_confidently_wrong_on_second_font_text(self):
        # LS13/2/6946: Prakash decodes to फ्रòाश.
        assert decode_legacy_hindi("|ÉEòÉ¶É") == "फ्रòाश"


class TestMisroutedEra:
    def test_misrouted_label_decodes_perfectly(self):
        # Real case: Jagdambika Pal, from a debate in the old font.
        assert decode_legacy_hindi("* gÉÉÒ VÉMÉnÉÎà¤ÉBÉEÉ {ÉÉãÉ") == "। श्री जगदम्बिका पाल"


class TestSquashCollisions:
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
        # No ambiguous name survives the lookup over the full roster.
        index = _folded_lookup(load_db_roster(13))
        assert [k for k in self._collisions() if k in index] == []

    def test_four_radhakrishnans_collide(self):
        assert len(self._collisions()["rdhkrishnan"]) == 4

    def test_there_are_four_triples_not_three(self):
        triples = {k for k, v in self._collisions().items() if len(v) == 3}
        assert triples == {"chaudhry", "elngovan", "rajendran"}


class TestIdenticalNames:
    def test_two_distinct_mps_are_both_called_chandra_shekhar(self):
        codes = {m["mpCode"] for m in load_db_roster(13) if m["mpName"] == "Chandra Shekhar"}
        assert codes == {"72", "5647"}


class TestWholeWordRowsDestroyedAfterSubstitution:
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
        # A bare Latin letter is protected as English, so F/j/Y are not dead rows.
        assert decode_legacy_hindi("F") == "F"
        assert decode_legacy_hindi("FÉ") == "क्ष"
        assert decode_legacy_hindi("jÉ") == "त्र"
        assert decode_legacy_hindi("YÉ") == "ज्ञ"

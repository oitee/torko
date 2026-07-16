"""
Rule-based Devanagari -> Latin transliteration and spelling-insensitive folding.

  has_devanagari — does the string contain any Devanagari?
  to_latin       — transliterate Devanagari, pass other scripts through
  fold           — squash a Latin token into a comparison key
"""
from translit import fold, has_devanagari, to_latin


class TestHasDevanagari:
    def test_true_for_devanagari(self):
        assert has_devanagari("सिंह") is True

    def test_false_for_latin(self):
        assert has_devanagari("Singh") is False

    def test_false_for_empty(self):
        assert has_devanagari("") is False


class TestToLatin:
    def test_consonant_carries_inherent_a(self):
        assert to_latin("क") == "ka"

    def test_matra_replaces_inherent_vowel(self):
        assert to_latin("का") == "kaa"

    def test_virama_drops_the_vowel(self):
        assert to_latin("क्") == "k"

    def test_standalone_vowel(self):
        assert to_latin("अ") == "a"

    def test_devanagari_digits_become_ascii(self):
        assert to_latin("१२३") == "123"

    def test_latin_passes_through_unchanged(self):
        assert to_latin("Singh") == "Singh"


class TestFold:
    def test_drops_trailing_inherent_a(self):
        # "Yadav" and its transliterated form collapse to the same key
        assert fold("Yadav") == "yadav"
        assert fold("yaadava") == "yadav"

    def test_w_folds_to_v(self):
        assert fold("Wadav") == fold("Vadav")

    def test_z_folds_to_j(self):
        assert fold("Ziya") == fold("Jiya")

    def test_doubled_letters_collapse(self):
        assert fold("Allah") == "alah"

    def test_strips_non_letters(self):
        assert fold("S.K.") == "sk"

    def test_nasal_ngh_folds_to_nh(self):
        # "सिंह" transliterates to "sinha"; the roman spelling writes "ngh"
        assert fold("Singh") == fold(to_latin("सिंह")) == "sinh"

    def test_inherent_a_inside_a_cluster_is_dropped(self):
        # a roman spelling may write the inherent "a" a conjunct implies
        assert fold("Meenakashi") == fold(to_latin("मीनाक्षी"))
        assert fold("Mahant") == fold(to_latin("महंत"))

    def test_inherent_a_is_kept_when_no_cluster_follows(self):
        # plain consonant-vowel syllables are never touched: "Yadav" keeps both
        # a's because each is followed by a consonant + vowel, not a cluster
        assert fold("Yadav") == "yadav"
        assert fold("Sharad") == "sharad"

    def test_cluster_folding_keeps_different_names_apart(self):
        assert fold("Sharad") != fold("Sharda")
        assert fold("Karan") != fold("Karn")

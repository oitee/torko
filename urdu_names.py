"""
Urdu-script speaker labels: a hand-verified name lookup.

Lok Sabha transcripts are mostly English and Devanagari, but a few members are
recorded in Urdu -- `جناب اسدالدین اویسی ( حیدرآباد )`. That is a third script,
and `translit.to_latin` only knows Devanagari, so an Urdu label reduces to no
usable name at all. Before `5f9bd3c` that emptiness was read as agreement and
Asaduddin Owaisi's speech was credited to Kiren Rijiju; today it is honestly
unresolved. This module is how those labels get read instead of merely not
being got wrong.

**Why a lookup table and not transliteration.** Urdu is an abjad: short vowels
are simply not written. `اویسی` is the letters a-w-y-s-y, and nothing in the
string says "Owaisi" rather than "Awaisi", "Uwaisi" or "Owesi". Character-level
transliteration cannot recover a spelling that was never encoded, so the folded
key it produced would not meet the roster's romanisation. That is a property of
the writing system, not a gap in our table -- no amount of rule-writing fixes
it. A curated name-to-name map sidesteps the vowels entirely.

**This table is deliberately incomplete, and that is safe.** It covers the
labels we have actually seen and verified. An Urdu label that is not in it
returns None and the speaker stays unresolved -- exactly the state they are in
today. So the table can only ever reduce the number of misses; it can never
introduce a wrong answer for a name it does not know.

To add an entry: take the constituency printed in the label, look up that seat
for the debate's term in the members table, and confirm it names exactly one
person whose name matches your reading. The matcher never reads the
constituency column, so it is an independent check rather than a restatement of
what we already believe. If the seat names two people, or none, do not add the
entry -- an honest miss beats a plausible wrong name.

**Rare, measured.** 5 labels across 2 of 158 sampled debates (LS13-18). Urdu is
not a large surface, which is why hand-curation is proportionate here rather
than reaching for a transliteration library.

Values are plain romanised names, not member ids, on purpose: the caller feeds
the value back into the ordinary name-matching path, so the never-guess rule
(a name matching two people is dropped, never guessed) and the term scoping
still apply. Mapping straight to an id would bypass both guards -- and the
Owaisi entry is exactly why that matters: `Sultan Salahuddin Owaisi` and
`Asaduddin Owaisi`, father and son, both sat for Hyderabad. The constituency
alone does not identify either of them.
"""
import re

# Urdu name -> romanised name as the members table spells it.
#
# Every entry was verified by matching the constituency printed in the label
# against the constituency recorded for that member, in the term the debate
# belongs to -- a field the matcher itself never reads, so it is an
# independent check. Keys are the exact strings seen in transcripts, with the
# "] " artifact and the "( constituency )" suffix stripped by _name_part below.
URDU_SPEAKER_NAMES = {
    # LS18/3/1758 and LS17/5/5464. Label says حیدرآباد (Hyderabad); db id 4091,
    # Asaduddin Owaisi, Hyderabad, term 18. NB db id 281, Sultan Salahuddin
    # Owaisi, is ALSO Hyderabad (term 13) -- the given name is what separates
    # them, which is why this maps to a full name and lets the roster decide.
    "جناب اسدالدین اویسی": "Asaduddin Owaisi",
    # LS18/3/1758. Label says سنبھل (Sambhal); db id 5822, Zia Ur Rehman,
    # Sambhal, term 18.
    "جناب ضیاءالرحمان": "Zia Ur Rehman",
    # LS17/5/5464. Label says امروہہ (Amroha); db id 5134, Kunwar Danish Ali,
    # Amroha, term 17. کنور is Kunwar, part of the recorded name rather than an
    # honorific to drop.
    "کنور دانش علی": "Kunwar Danish Ali",
    # LS17/5/5464. Label says سہارنپور (Saharanpur); db id 5161, Haji Fazlur
    # Rehman, Saharanpur, term 17. حاجی (Haji) likewise is part of the name.
    "جناب حاجی فضل الرحمٰن صاحب": "Haji Fazlur Rehman",
}

# Any Arabic-script character: Arabic, Arabic Supplement, Extended-A.
_ARABIC_RE = re.compile(r"[؀-ۿݐ-ݿࢠ-ࣿ]")
# "( حیدرآباد )" -- the constituency, in either script's brackets.
_PAREN_RE = re.compile(r"[(（][^)）]*[)）]")
# A stray "]" opens several real labels: "] جناب ضیاءالرحمان ( سنبھل )".
_LEADING_JUNK_RE = re.compile(r"^[\]\[\s\*]+")


def looks_urdu(label: str) -> bool:
    """True if `label` carries Arabic-script letters (so Devanagari rules can't read it)."""
    return bool(label) and bool(_ARABIC_RE.search(label))


def _name_part(label: str) -> str:
    """The bare Urdu name: no leading junk, no constituency, single-spaced."""
    label = _LEADING_JUNK_RE.sub("", label)
    label = _PAREN_RE.sub(" ", label)
    return re.sub(r"\s+", " ", label).strip()


def urdu_label_to_name(label: str) -> str | None:
    """The romanised name for an Urdu speaker label, or None if we can't read it.

    None is the honest answer for an unknown name and leaves the speaker
    unresolved. It is never a guess: this returns a name only for a label whose
    identity has been verified by hand and written into URDU_SPEAKER_NAMES.
    """
    if not looks_urdu(label):
        return None
    return URDU_SPEAKER_NAMES.get(_name_part(label))

import re

# Urdu name -> romanised name as the members table spells it.
# Values are names, not ids, so the matcher still applies its collision and term rules.
# Keys are the label with the "] " prefix and the "( constituency )" suffix removed.
URDU_SPEAKER_NAMES = {
    # Sultan Salahuddin Owaisi also sat for Hyderabad, so the full name is needed.
    "جناب اسدالدین اویسی": "Asaduddin Owaisi",
    "جناب ضیاءالرحمان": "Zia Ur Rehman",
    # کنور (Kunwar) and حاجی (Haji) are part of the recorded name, not honorifics.
    "کنور دانش علی": "Kunwar Danish Ali",
    "جناب حاجی فضل الرحمٰن صاحب": "Haji Fazlur Rehman",
}

# Any Arabic-script character: Arabic, Arabic Supplement, Extended-A.
_ARABIC_RE = re.compile(r"[؀-ۿݐ-ݿࢠ-ࣿ]")
# "( حیدرآباد )" -- the constituency, in either script's brackets.
_PAREN_RE = re.compile(r"[(（][^)）]*[)）]")
# A stray "]" opens several real labels: "] جناب ضیاءالرحمان ( سنبھل )".
_LEADING_JUNK_RE = re.compile(r"^[\]\[\s\*]+")


def looks_urdu(label: str) -> bool:
    return bool(label) and bool(_ARABIC_RE.search(label))


def _name_part(label: str) -> str:
    label = _LEADING_JUNK_RE.sub("", label)
    label = _PAREN_RE.sub(" ", label)
    return re.sub(r"\s+", " ", label).strip()


def urdu_label_to_name(label: str) -> str | None:
    """The romanised name, or None if the label is not in URDU_SPEAKER_NAMES."""
    if not looks_urdu(label):
        return None
    return URDU_SPEAKER_NAMES.get(_name_part(label))

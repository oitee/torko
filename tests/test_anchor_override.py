"""The anchor-override guard: when a turn's <A name> anchor names a different
person than the printed label independently resolves to, the visible label wins
and the contradicted anchor is discarded (internal_docs 033).

This bug is invisible on the debate page -- the label reads correctly while the
turn is filed under someone else's mpCode -- so it needs heavy test cover. Every
case below drives annotate_speakers directly with hand-built segments and a
controlled participant list, so resolve_speaker's index is fully determined.

Never-guess boundary, restated as the cases that must NOT override:
  * no printed label, or an unresolvable label -> keep the anchor (no evidence)
  * a transliteration/spelling variant of the SAME person -> keep the anchor
  * an ambiguous label (collides in the roster) -> keep the anchor
Only a positive re-identification to a DIFFERENT specific person overrides.
"""
from debate_fetch import annotate_speakers


def _seg(mp_code, label, mp_name=None):
    # split_by_speaker sets mpName to the list's canonical name, or the label
    # itself when the anchor code is absent from the list. Mirror that.
    return {
        "mpCode": mp_code,
        "speakerLabel": label,
        "mpName": mp_name if mp_name is not None else label,
        "text": "some words",
    }


def _annotate(segs, mp_list, roster=None):
    annotate_speakers(segs, mp_list, roster)
    return segs


# ---------- the core poison case ----------

def test_anchor_naming_different_person_is_overridden_by_label():
    # Real case (debate 38403): label "DR. UDIT RAJ" carries code 4717 = Lekhi.
    segs = [_seg("4717", "DR. UDIT RAJ (NORTH WEST DELHI)", mp_name="DR. UDIT RAJ (NORTH WEST DELHI)")]
    mp_list = [{"mpCode": 4764, "mpName": "Dr. Udit Raj"}]
    _annotate(segs, mp_list)
    assert segs[0]["mpCode"] == "4764"
    assert segs[0]["mpName"] == "Dr. Udit Raj"
    assert segs[0]["nameSource"] == "anchor-overridden"
    assert segs[0]["anchorRejected"] == "4717"


def test_override_records_the_rejected_code():
    segs = [_seg("999", "SHRI RAHUL GANDHI")]
    mp_list = [{"mpCode": 4074, "mpName": "Rahul Gandhi"}]
    _annotate(segs, mp_list)
    assert segs[0]["anchorRejected"] == "999"
    assert segs[0]["mpCode"] == "4074"


def test_overridden_name_is_canonical_not_the_label():
    segs = [_seg("999", "SHRI JOHN BARLA (ALIPURDUARS)")]
    mp_list = [{"mpCode": 4716, "mpName": "John Barla"}]
    _annotate(segs, mp_list)
    assert segs[0]["mpName"] == "John Barla"  # canonical, not the raw label


# ---------- must NOT override (never-guess) ----------

def test_agreeing_anchor_is_kept_as_anchor():
    # Anchor code matches the person the label names -> plain "anchor".
    segs = [_seg("4764", "DR. UDIT RAJ (NORTH WEST DELHI)", mp_name="Dr. Udit Raj")]
    mp_list = [{"mpCode": 4764, "mpName": "Dr. Udit Raj"}]
    _annotate(segs, mp_list)
    assert segs[0]["mpCode"] == "4764"
    assert segs[0]["nameSource"] == "anchor"
    assert "anchorRejected" not in segs[0]


def test_translit_variant_same_person_is_not_overridden():
    # Anchor is correct; label is a Devanagari spelling of the SAME person.
    # resolve_speaker must not return a DIFFERENT person, so the anchor stands.
    segs = [_seg("475", "श्री रामजीलाल सुमन", mp_name="Ramji Lal Suman")]
    mp_list = [{"mpCode": 475, "mpName": "Ramji Lal Suman"}]
    _annotate(segs, mp_list)
    assert segs[0]["mpCode"] == "475"
    assert segs[0]["nameSource"] == "anchor"
    assert "anchorRejected" not in segs[0]


def test_unresolvable_label_keeps_anchor_no_evidence():
    # Label names nobody in the list/roster -> no positive re-id -> keep anchor.
    segs = [_seg("4717", "SHRI SOMEBODY NOBODY HAS HEARD OF")]
    mp_list = [{"mpCode": 4717, "mpName": "Meenakashi Lekhi"}]
    _annotate(segs, mp_list)
    assert segs[0]["mpCode"] == "4717"
    assert segs[0]["nameSource"] == "anchor"


def test_anchor_with_no_label_is_kept():
    # No printed label to check against -> anchor stands.
    seg = {"mpCode": "4717", "speakerLabel": None, "mpName": "Meenakashi Lekhi", "text": "hi"}
    _annotate([seg], [{"mpCode": 4717, "mpName": "Meenakashi Lekhi"}])
    assert seg["mpCode"] == "4717"
    assert seg["nameSource"] == "anchor"


def test_empty_label_is_kept():
    seg = {"mpCode": "4717", "speakerLabel": "", "mpName": "Meenakashi Lekhi", "text": "hi"}
    _annotate([seg], [{"mpCode": 4717, "mpName": "Meenakashi Lekhi"}])
    assert seg["mpCode"] == "4717"
    assert seg["nameSource"] == "anchor"


def test_ambiguous_label_does_not_override():
    # Two people share the label's folded key -> resolve_speaker drops it
    # (never-guess) -> returns None -> the anchor is NOT overridden.
    segs = [_seg("999", "SHRI CHANDRA SHEKHAR")]
    mp_list = [
        {"mpCode": 72, "mpName": "Chandra Shekhar"},
        {"mpCode": 5647, "mpName": "Chandra Shekhar"},
    ]
    _annotate(segs, mp_list)
    assert segs[0]["mpCode"] == "999"
    assert segs[0]["nameSource"] == "anchor"


def test_same_person_two_spellings_of_own_name_not_overridden():
    # Anchor code correct; label is an initials form of the same person.
    segs = [_seg("67", "SHRI AJOY CHAKRABORTY (BASIRHAT)", mp_name="Ajay Chakraborty")]
    mp_list = [{"mpCode": 67, "mpName": "Ajay Chakraborty"}]
    _annotate(segs, mp_list)
    # Either kept as anchor, or (if it self-resolves to 67) still 67 -- never a
    # different person.
    assert segs[0]["mpCode"] == "67"


# ---------- override via the roster fallback, not just the list ----------

def test_db_roster_match_never_overrides_an_anchor():
    # The real person is NOT in this debate's list, only in the wider DB roster
    # (a name-db match). That tier is weaker than an anchor the source printed,
    # so it must NOT override -- the anchor stands. Only the debate's OWN list
    # may contradict an anchor. (Mirrors test_sample_replay's invariant.)
    segs = [_seg("4717", "SHRI JOHN BARLA (ALIPURDUARS)")]
    mp_list = [{"mpCode": 4717, "mpName": "Meenakashi Lekhi"}]
    roster = [{"mpCode": "4716", "mpName": "John Barla"}]
    _annotate(segs, mp_list, roster)
    assert segs[0]["mpCode"] == "4717"
    assert segs[0]["nameSource"] == "anchor"
    assert "anchorRejected" not in segs[0]


# ---------- interaction with the rest of the pipeline ----------

def test_mixed_segments_only_the_contradicted_one_moves():
    segs = [
        _seg("4764", "DR. UDIT RAJ", mp_name="Dr. Udit Raj"),         # agrees
        _seg("999", "SHRI RAHUL GANDHI"),                              # contradicts
        {"mpCode": None, "speakerLabel": "MR. SPEAKER", "mpName": None, "text": "order"},  # presiding
    ]
    mp_list = [{"mpCode": 4764, "mpName": "Dr. Udit Raj"}, {"mpCode": 4074, "mpName": "Rahul Gandhi"}]
    _annotate(segs, mp_list)
    assert segs[0]["nameSource"] == "anchor"
    assert segs[1]["mpCode"] == "4074" and segs[1]["nameSource"] == "anchor-overridden"
    assert segs[2]["nameSource"] == "presiding"


def test_override_person_is_resolvable_to_persons_downstream():
    # The overridden mpCode must be a real list/roster code (so persons lookup
    # in populate_turns can attach a person_id), never left as the bogus one.
    segs = [_seg("999", "MS. BANSURI SWARAJ (NEW DELHI)")]
    mp_list = [{"mpCode": 4751, "mpName": "Bansuri Swaraj"}]
    _annotate(segs, mp_list)
    assert segs[0]["mpCode"] == "4751"
    assert segs[0]["anchorRejected"] == "999"


def test_no_double_override_is_stable_on_reannotate():
    segs = [_seg("999", "SHRI RAHUL GANDHI")]
    mp_list = [{"mpCode": 4074, "mpName": "Rahul Gandhi"}]
    _annotate(segs, mp_list)
    first = dict(segs[0])
    # annotate is not meant to be re-run, but if it were, an already-correct
    # mpCode must not be re-overridden into nonsense.
    _annotate(segs, mp_list)
    assert segs[0]["mpCode"] == first["mpCode"] == "4074"

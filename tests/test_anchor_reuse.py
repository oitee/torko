"""
Carrying and reusing speaker anchors across paragraphs.

sansad.in anchors a speaker only on their first turn (and often parks that
anchor in an empty <p> just before the speech). These helpers spread that
anchor to the speaker's later, unanchored turns:

  _name_agreement          — do two names match? None when nothing was compared
  anchor_contradicts_label — may we DISCARD an anchor the source printed?
  labels_name_same_person  — may we CLAIM two labels are one person?
  reuse_anchors            — propagate an anchored mpCode to matching turns
  split_by_speaker         — carrying an anchor from an empty <p> to the text

The two predicates ask opposite questions and must disagree about the
no-evidence case. Discarding an anchor needs a positive contradiction; claiming
a new attribution needs positive agreement. One bool served both for a while,
returning True when nothing had been compared — see TestNoEvidenceIsNotAgreement
for what that cost.
"""
from debate_fetch import (
    _name_parts,
    _name_agreement,
    anchor_contradicts_label,
    labels_name_same_person,
    reuse_anchors,
    split_by_speaker,
)

ROSTER = [{"mpName": "Shri Kodikunnil Suresh", "mpCode": 100, "mpPartCode": 1}]


class TestNameAgreement:
    """A whole-word match is required; initials only pad the coverage."""

    def test_identical_names_agree(self):
        assert _name_agreement("SHRI A. RAJA", "Shri A. Raja") is True

    def test_initials_in_label_count_towards_coverage(self):
        # "S.K." supplies the initials, "KHARVENTHAN" the whole-word match
        assert _name_agreement(
            "S.K. KHARVENTHAN", "Salarapatty Kuppusamy Kharventhan"
        ) is True

    def test_only_initials_is_not_enough(self):
        # no whole word matches, so the anchor is not believed
        assert _name_agreement("S. K.", "Salarapatty Kuppusamy") is False

    def test_different_people_disagree(self):
        assert _name_agreement("SHRI RAM KUMAR", "Shri Shyam Verma") is False

    def test_no_usable_name_is_none_not_a_verdict(self):
        # the distinction the whole bug turned on: nothing was compared, so
        # there is no verdict to give. None is not False and not True.
        assert _name_agreement("MR. SPEAKER", "") is None


class TestAnInitialCannotCarryAnUnexplainedWord:
    """The misattribution found by measuring the 80% path (internal_docs/026).

    Every case here is real and was pulled out of the corpus, not invented. The
    rule they force: an initial is the weakest evidence in the file, so it stops
    counting the moment the roster name has a word the label explains in no way
    at all.
    """

    def test_a_shared_surname_plus_a_lucky_initial_is_not_a_person(self):
        # LS15/10/6421. "kumar" matched outright, the initial "p" happened to
        # agree with "pavan", and "bnsal" matched nothing whatsoever -- 2 of 3
        # words "covered", over the 0.6 bar. That filed Pawan Kumar Bansal's
        # words under P. Kumar (mpCode 4546): two different human beings, and
        # the exact sin never-guess exists to prevent.
        assert labels_name_same_person(
            "संसदीय कार्य मंत्री तथा जल संसाधन मंत्री (श्री पवन कुमार बंसल)",
            "* SHRI P. KUMAR (TIRUCHIRAPPALLI)",
        ) is False

    def test_the_unexplained_word_is_what_kills_it_not_the_initial(self):
        # Same shape as the Bansal case but with nothing left over: every roster
        # word is either matched or explained by an initial. This must survive,
        # and it is why the fix is not simply "distrust initials".
        assert labels_name_same_person(
            "S.K. KHARVENTHAN", "Salarapatty Kuppusamy Kharventhan"
        ) is True

    def test_an_initial_still_covers_when_the_rest_matches_outright(self):
        # LS14/9/6375: A.K. Antony IS Arakkaparambil Kurien Antony. The initial
        # "a" carries "arakkaparambil" -- legitimately, because nothing is
        # unexplained once "Sri" is read as the honorific it is.
        assert labels_name_same_person(
            "THE MINISTER OF DEFENCE (SHRI A.K. ANTONY)", "Sri Arakkaparambil Antony"
        ) is True

    def test_an_unmatched_word_alone_does_not_reject_when_no_initial_props_it_up(self):
        # LS17/1/127. "chowdhury"/"choudhari" transliterate too far apart to
        # score 0.8, so it is unexplained -- but two whole words matched and no
        # initial is doing the work, so this stays a match. Requiring full
        # coverage instead would have thrown this away (and 4.4% of all carried
        # anchors with it).
        assert labels_name_same_person(
            "श्री अधीर रंजन चौधरी", "SHRI ADHIR RANJAN CHOWDHURY (BAHARAMPUR)"
        ) is True

    def test_a_longer_roster_name_still_matches_a_shorter_label(self):
        # LS17/1/1289: Ravi Kishan is Ravi Kishan Shukla.
        assert labels_name_same_person(
            "श्री रवि किशन", "श्री रवि किशन शुक्ला ( गोरखपुर )"
        ) is True


class TestSriIsAnHonorificOnlyWhenItLeads:
    """`Sri` is both an honorific and a name particle. Position separates them."""

    def test_leading_sri_is_dropped_as_an_honorific(self):
        # How the DB roster spells it. Left in, it is a word the label can never
        # match, so it drags coverage down and loses real people.
        assert _name_parts("Sri Arakkaparambil Antony") == (["arkprmbil", "antony"], set())

    def test_sri_inside_a_name_is_kept_as_part_of_the_name(self):
        # Shri Lavu Sri Krishna Devarayalu, mpCode 200 -- a real MP whose name
        # contains "Sri". Dropping it wherever it appears breaks this person.
        full, _initials = _name_parts("Shri Lavu Sri Krishna Devarayalu")
        assert "sri" in full


class TestReuseRefusesToPickBetweenTwoAnchors:
    """One label matching two anchored people is evidence for two humans."""

    def test_a_label_matching_two_different_people_resolves_to_neither(self):
        # The old loop took the FIRST match and stopped, so dict order decided
        # which human being got the words. Nothing in `ambiguous` catches this:
        # it guards one label printed for two mpCodes, not one label fuzzy-
        # matching two separate anchors.
        segs = [
            {"mpCode": "11", "speakerLabel": "SHRI RAM KUMAR SINGH",
             "mpName": "Shri Ram Kumar Singh", "nameSource": "anchor"},
            {"mpCode": "22", "speakerLabel": "SHRI RAM KUMAR SINHA",
             "mpName": "Shri Ram Kumar Sinha", "nameSource": "anchor"},
            {"mpCode": None, "speakerLabel": "SHRI RAM KUMAR", "mpName": None},
        ]
        out = reuse_anchors(segs)
        assert out[2]["mpCode"] is None
        assert out[2].get("nameSource") != "anchor-reuse"

    def test_one_person_anchored_under_two_spellings_still_resolves(self):
        # The counterpart that keeps the guard honest. LS18/4/2819 prints
        # Harsimrat Kaur Badal both with and without her constituency; two
        # labels, two mpCodes in the roster, one human. Keying the candidates
        # by mpCode is what would make this ambiguous -- so this test pins the
        # single-person case, where both labels carry the SAME code.
        segs = [
            {"mpCode": "5107", "speakerLabel": "SHRIMATI HARSIMRAT KAUR BADAL (BATHINDA)",
             "mpName": "Shrimati Harsimrat Kaur Badal", "nameSource": "anchor"},
            {"mpCode": "5107", "speakerLabel": "SHRIMATI HARSIMRAT KAUR BADAL",
             "mpName": "Shrimati Harsimrat Kaur Badal", "nameSource": "anchor"},
            {"mpCode": None, "speakerLabel": "श्रीमती हरसिमरत कौर बादल", "mpName": None},
        ]
        out = reuse_anchors(segs)
        assert out[2]["mpCode"] == "5107"
        assert out[2]["nameSource"] == "anchor-reuse"

    def test_a_single_unambiguous_anchor_still_carries(self):
        segs = [
            {"mpCode": "100", "speakerLabel": "SHRI KODIKUNNIL SURESH",
             "mpName": "Shri Kodikunnil Suresh", "nameSource": "anchor"},
            {"mpCode": None, "speakerLabel": "SHRI KODIKUNNIL SURESH", "mpName": None},
        ]
        assert reuse_anchors(segs)[1]["mpCode"] == "100"


class TestAMinisterialTitleIsNotAName:
    """A title describes a job. It is never evidence of who holds it."""

    def test_two_different_ministers_do_not_match_on_office_boilerplate(self):
        # LS16/8/6812, and a misattribution until it was measured. The name in
        # the second label sits in SQUARE brackets, which the title-collapse
        # rule could not see, so the whole title stood as name words. The two
        # labels then agreed on the/minister/state/ministry/and: six "strong"
        # word matches, not one of them a name, and Rao Inderjit Singh's words
        # were filed under Col. Rajyavardhan Rathore (mpCode 4782).
        assert labels_name_same_person(
            "THE MINISTER OF STATE OF THE MINISTRY OF PLANNING AND MINISTER OF STATE "
            "IN THE MINISTRY OF DEFENCE (RAO INDERJIT SINGH)",
            "THE MINISTER OF STATE IN THE MINISTRY OF INFORMATION AND BROADCASTING "
            "[COL. RAJYAVARDHAN RATHORE (Retd.)]",
        ) is False

    def test_a_title_with_the_name_in_square_brackets_collapses_to_the_name(self):
        assert _name_parts(
            "THE MINISTER OF STATE IN THE MINISTRY OF INFORMATION AND BROADCASTING "
            "[COL. RAJYAVARDHAN RATHORE (Retd.)]"
        ) == (["rjyvrdhan", "rthore"], set())

    def test_the_round_bracket_form_still_collapses(self):
        full, initials = _name_parts("THE MINISTER OF HOUSING [SHRI M. VENKAIAH NAIDU]")
        assert full == ["venkaiah", "naidu"] and initials == {"m"}

    def test_office_words_are_dropped_before_folding_not_after(self):
        # The trap: fold() strips the cluster-internal inherent "a", so the real
        # name "Anand" folds to "and" -- an office word. Filtering after the fold
        # deleted the name, collapsed "Anand Kumar" to the key "kumar", and
        # squashed him into "P. Kumar": a collision between two real people,
        # manufactured by a stopword list.
        full, _initials = _name_parts("Shri Anand Kumar")
        assert full == ["and", "kumar"]


class TestNoEvidenceIsNotAgreement:
    """The two callers need opposite answers when nothing could be compared.

    LS14/5/2711 is routed to the modern reader while its text is still in the
    legacy font, so its labels never get decoded and fold to nothing. When "no
    evidence" was reported as agreement, one name that *had* resolved seeded the
    reuse map and then matched every undecodable label in the debate: 303 turns,
    28,501 words, all credited to Shri Mohan Singh -- including Lalu Prasad's,
    Nitish Kumar's, and the Deputy Speaker's.
    """

    def test_an_undecodable_label_names_nobody(self):
        # raw legacy-font bytes: fold to no usable word at all
        raw_a = "gÉÉÒ xÉÉÒiÉÉÒ¶É BÉÖEàÉÉ®"        # श्री नीतीश कुमार
        raw_b = "gÉÉÒ àÉÉäcxÉ ÉËºÉc (nä´ÉÉÊ®ªÉÉ)"  # श्री मोहन सिंह (देवरिया)
        assert _name_agreement(raw_a, raw_b) is None
        assert labels_name_same_person(raw_a, raw_b) is False

    def test_no_evidence_never_claims_a_new_attribution(self):
        assert labels_name_same_person("MR. SPEAKER", "") is False

    def test_no_evidence_never_discards_a_printed_anchor(self):
        # the opposite call: an anchor is the source's own evidence, so only a
        # positive disagreement may throw it away
        assert anchor_contradicts_label("MR. SPEAKER", "") is False

    def test_a_real_disagreement_still_discards_the_anchor(self):
        assert anchor_contradicts_label("SHRI RAM KUMAR", "Shri Shyam Verma") is True

    def test_reuse_does_not_stamp_one_name_across_undecodable_labels(self):
        # the end-to-end shape of the 2711 bug, in miniature
        segs = [
            {"mpCode": "77", "speakerLabel": "gÉÉÒ àÉÉäcxÉ ÉËºÉc",
             "mpName": "Shri Mohan Singh", "nameSource": "name-translit"},
            {"mpCode": None, "speakerLabel": "gÉÉÒ xÉÉÒiÉÉÒ¶É BÉÖEàÉÉ®", "mpName": None},
            {"mpCode": None, "speakerLabel": "+ÉvªÉFÉ àÉcÉänªÉ", "mpName": None},
        ]
        reuse_anchors(segs)
        assert [s["mpCode"] for s in segs] == ["77", None, None]


class TestReuseAnchors:
    def test_propagates_mpcode_to_later_unanchored_turn(self):
        segs = [
            {"mpCode": "500", "speakerLabel": "SHRI NEW MEMBER", "mpName": "Shri New Member"},
            {"mpCode": None, "speakerLabel": "SHRI NEW MEMBER", "mpName": "SHRI NEW MEMBER"},
        ]
        reuse_anchors(segs)
        assert segs[1]["mpCode"] == "500"
        assert segs[1]["mpName"] == "Shri New Member"
        assert segs[1]["nameSource"] == "anchor-reuse"

    def test_label_anchored_to_two_people_is_left_untouched(self):
        segs = [
            {"mpCode": "1", "speakerLabel": "SHRI KUMAR", "mpName": "Shri Ram Kumar"},
            {"mpCode": "2", "speakerLabel": "SHRI KUMAR", "mpName": "Shri Shyam Kumar"},
            {"mpCode": None, "speakerLabel": "SHRI KUMAR", "mpName": "SHRI KUMAR"},
        ]
        reuse_anchors(segs)
        assert segs[2]["mpCode"] is None

    def test_unrelated_label_is_not_resolved(self):
        segs = [
            {"mpCode": "500", "speakerLabel": "SHRI NEW MEMBER", "mpName": "Shri New Member"},
            {"mpCode": None, "speakerLabel": "MR. SPEAKER", "mpName": "MR. SPEAKER"},
        ]
        reuse_anchors(segs)
        assert segs[1]["mpCode"] is None

    def test_this_debates_anchor_beats_a_last_resort_name_db_match(self):
        # annotate_speakers runs before this pass, so the "name-db" tier can
        # claim a turn that an anchor printed in this very debate also names.
        # The anchor is the stronger evidence and must win.
        segs = [
            {
                "mpCode": "500",
                "speakerLabel": "SHRI NEW MEMBER",
                "mpName": "Shri New Member",
                "nameSource": "anchor",
            },
            {
                "mpCode": "777",
                "speakerLabel": "SHRI NEW MEMBER",
                "mpName": "Shri New Member",
                "nameSource": "name-db",
            },
        ]
        reuse_anchors(segs)
        assert segs[1]["mpCode"] == "500"
        assert segs[1]["nameSource"] == "anchor-reuse"

    def test_a_name_db_match_never_makes_a_label_look_ambiguous(self):
        # A name-db guess must not seed the anchored-label map: if it did, the
        # label would look anchored to two people and reuse would bail out,
        # silently costing a resolution the anchor alone would have made.
        segs = [
            {
                "mpCode": "500",
                "speakerLabel": "SHRI NEW MEMBER",
                "mpName": "Shri New Member",
                "nameSource": "anchor",
            },
            {
                "mpCode": "777",
                "speakerLabel": "SHRI NEW MEMBER",
                "mpName": "Shri New Member",
                "nameSource": "name-db",
            },
            {"mpCode": None, "speakerLabel": "SHRI NEW MEMBER", "mpName": "SHRI NEW MEMBER"},
        ]
        reuse_anchors(segs)
        assert segs[2]["mpCode"] == "500"

    def test_an_earlier_tiers_match_is_never_overridden(self):
        # Only "name-db" is reconsidered; a name-exact answer keeps its code.
        segs = [
            {
                "mpCode": "500",
                "speakerLabel": "SHRI NEW MEMBER",
                "mpName": "Shri New Member",
                "nameSource": "anchor",
            },
            {
                "mpCode": "600",
                "speakerLabel": "SHRI NEW MEMBER",
                "mpName": "Shri New Member",
                "nameSource": "name-exact",
            },
        ]
        reuse_anchors(segs)
        assert segs[1]["mpCode"] == "600"
        assert segs[1]["nameSource"] == "name-exact"


class TestCarriedAnchor:
    """An anchor alone in an empty <p> attaches to the next paragraph with text."""

    def test_anchor_in_empty_p_is_carried_to_the_speech(self):
        html = (
            '<p><a name="100*1"></a></p>'
            "<p><b>SHRI KODIKUNNIL SURESH:</b> The speech.</p>"
        )
        (seg,) = split_by_speaker(html, ROSTER)
        assert seg["mpCode"] == "100"
        assert seg["text"] == "The speech."

    def test_carried_anchor_is_rejected_when_the_name_disagrees(self):
        # anchor names person 100, but the next paragraph is a different speaker
        html = (
            '<p><a name="100*1"></a></p>'
            "<p><b>SHRI SOMEONE ELSE:</b> Not Suresh.</p>"
        )
        (seg,) = split_by_speaker(html, ROSTER)
        assert seg["mpCode"] is None
        assert seg["anchorRejected"] == "100"

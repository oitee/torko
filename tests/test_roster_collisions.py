"""
Whole-roster collision baseline for `fold`.

`_folded_key` squashes a name into a spelling-insensitive key so a Devanagari
label and a romanised roster name meet. Every rule added to `fold` widens that
squash, and a wider squash risks the opposite failure: two *different* people
landing on one key.

This pins the collision set over the real roster (2177 members, snapshotted from
the persons table into data/persons_roster.tsv). It is a baseline, not a
judgement -- every group below has been looked at and accepted. When a fold rule
changes, this test either stays green (the rule was safe) or names the exact
people it merged, so the call is made deliberately rather than discovered later
in a sample.

Note these keys are all *guarded*: build_speaker_index drops any folded key
naming more than one mpCode, so a collision here costs recall (those members
stop resolving) but never causes a misattribution. That applies to both folded
tables -- `by_folded` (the debate's own member list, via name-translit) and
`by_folded_db` (the wide DB roster, via name-db) -- because both are built by
the same `_folded_lookup`. The guard test below is parametrised over both so
that shared guarantee is proven rather than assumed: name-db is the only tier
that ever matches against all 2177 names at once, so it is the one where a
dropped guard would cost most. See internal_docs/014_MODE_B_FOLD_REFINEMENTS.md
and 016_COLLISION_BASELINE.md.

Measured against the live persons table (2177 rows, matching this snapshot):
the guard drops 26 keys covering 57 people. That is the price of never
guessing, and internal_docs/018_WHERE_THINGS_STAND.md §6.5 is where it gets
weighed.
"""
import collections
import pathlib

import pytest

import debate_fetch

_ROSTER = pathlib.Path(__file__).parent / "data" / "persons_roster.tsv"

# Folded key -> the distinct members sharing it. Grouped by why we accept it.
EXPECTED_COLLISIONS = {
    # Same name, two different people. The roster genuinely holds both.
    "bholsinh": ["Bhola Singh", "Bhola Singh"],
    "chndrshekhar": ["Chandra Shekhar", "Chandra Shekhar"],
    "devivin": ["Veena Devi", "Veena Devi"],
    "hrshvrdhan": ["Harsh Vardhan", "Harsh Vardhan"],
    "jitendrsinh": ["Jitendra Singh", "Jitendra Singh"],
    "kumarmanoj": ["Manoj Kumar", "Manoj Kumar"],
    "mnvendrsinh": ["Manvendra Singh", "Manvendra Singh"],
    "palsinhsty": ["Satya Pal Singh", "Satya Pal Singh"],
    "rajeshverm": ["Rajesh Verma", "Rajesh Verma"],
    "rmpalsinh": ["Rampal Singh", "Rampal Singh"],
    "sinhvirendr": ["Virendra Singh", "Virendra Singh"],
    # Distinguished only by initials, which _name_parts drops (len < 3).
    "chaudhry": ["C.R. Chaudhary", "P P Chaudhary", "R K Chaudhary"],
    "elngovan": ["E.V.K.S. Elangovan", "P.D. Elangovan", "T.K.S. Elangovan"],
    "karunakaran": ["K. Karunakaran", "P. Karunakaran"],
    "rajendran": ["C. Rajendran", "P. Rajendran", "S. Rajendran"],
    "rdhkrishnan": [
        "C.P. Radhakrishnan",
        "K Radhakrishnan",
        "R. Radhakrishnan",
        "T. Radhakrishnan",
    ],
    "ramesh": ["C M Ramesh", "T.R.V.S. Ramesh"],
    "thomas": ["P. T. Thomas", "P.C. Thomas"],
    # Spelling variants the fold is meant to bridge, colliding across people.
    "ajaykumar": ["Ajay Kumar", "S. Ajaya Kumar"],
    "krishnsvmy": ["A. Krishnaswamy", "M. Krishnasswamy"],
    "kumarvirendr": ["M.P. Veerendra Kumar", "Virendra Kumar"],
    "brijendrsinh": ["Brijendra Singh", "Brijendra Singh Ola"],
    "jaiprksh": ["Jai Parkash", "Jai Prakash"],
    # Singh/Sinha: unavoidable. "सिंह" transliterates to "sinha", and the
    # trailing-"a" rule makes that identical to "Sinha". Accepted knowingly.
    "renuksinh": ["Renuka Singh", "Renuka Sinha"],
    "sinhyshvnt": ["Yashwant Singh", "Yashwant Sinha"],
    # "Malla" folds to "ml" -- under 3 chars, so _name_parts demotes it to an
    # initial and the key collapses to the surname alone. The cluster-"a" rule
    # can shorten a token out of significance; this is the only roster case.
    "redy": ["Ch. Malla Reddy", "S.P.Y. Reddy"],
}


def _roster():
    rows = []
    for line in _ROSTER.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        sansad_id, name = line.split("\t")
        rows.append((int(sansad_id), name))
    return rows


def _collisions():
    """Folded key -> names, for every key claimed by more than one member."""
    by_key: dict[str, set] = collections.defaultdict(set)
    names: dict[str, list] = collections.defaultdict(list)
    for sansad_id, name in _roster():
        key = debate_fetch._folded_key(name)
        if not key:
            continue
        by_key[key].add(sansad_id)
        names[key].append(name)
    return {k: sorted(names[k]) for k, v in by_key.items() if len(v) > 1}


class TestRosterCollisions:
    def test_roster_snapshot_is_intact(self):
        rows = _roster()
        assert len(rows) == 2177
        assert len({sansad_id for sansad_id, _ in rows}) == 2177

    def test_folded_collisions_match_the_accepted_baseline(self):
        actual = _collisions()

        added = {k: v for k, v in actual.items() if k not in EXPECTED_COLLISIONS}
        removed = {k: v for k, v in EXPECTED_COLLISIONS.items() if k not in actual}
        assert not added, (
            "fold now merges members it did not before -- review each pair, then "
            f"add it to EXPECTED_COLLISIONS if acceptable: {added}"
        )
        assert not removed, (
            "these collisions are gone; if that was the intent, drop them from "
            f"EXPECTED_COLLISIONS: {removed}"
        )
        assert actual == EXPECTED_COLLISIONS

    @pytest.mark.parametrize("table_name", ["by_folded", "by_folded_db"])
    def test_every_collision_is_guarded_by_the_index(self, table_name):
        """A collision must cost recall, never resolve to the wrong person.

        `by_folded` (fed by a debate's own mpPartDetailList, via the
        name-translit tier) and `by_folded_db` (fed by the wide DB roster, via
        the last-resort name-db tier) are built by two separate calls to
        `_folded_lookup`. Both must honour the "never guess" rule -- if the
        DB-roster call were ever specialised to skip the multi-mpCode filter,
        this is the case that would catch it.
        """
        roster = [
            {"mpCode": str(sansad_id), "mpName": name} for sansad_id, name in _roster()
        ]
        index = debate_fetch.build_speaker_index(roster, db_roster=roster)
        table = index[table_name]
        for key in EXPECTED_COLLISIONS:
            assert key not in table, f"{key!r} resolves despite naming two members"

    def test_resolve_speaker_refuses_a_db_only_collision(self):
        """Pin the consequence, not just the table contents.

        A name that collides in the DB roster and is absent from the debate's
        own member list must come back unresolved from resolve_speaker, not
        silently attributed to whichever of the two people happened to be
        inserted first. This is the assertion that would actually catch a
        misattribution if `by_folded_db` ever stopped being guarded.
        """
        db_roster = [
            {"mpCode": "1", "mpName": "Bhola Singh"},
            {"mpCode": "2", "mpName": "Bhola Singh"},
        ]
        index = debate_fetch.build_speaker_index([], db_roster=db_roster)
        assert index["by_folded_db"] == {}
        result = debate_fetch.resolve_speaker("Bhola Singh", index)
        assert result == (None, None)

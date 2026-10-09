import pytest

from scripts.embed_summaries import estimate_tokens, to_embed
from scripts.summary_tags_review import pick_random, render_speech
from tag_embed import input_hash


def row(i, summary):
    return {"extraction_id": i, "speech_id": i * 10, "summary": summary}


def test_a_summary_with_no_vector_is_embedded():
    todo = to_embed([row(1, "A speech on roads.")], {})
    assert [t["extraction_id"] for t in todo] == [1]
    assert todo[0]["hash"] == input_hash("A speech on roads.")


def test_a_summary_with_the_same_hash_is_skipped():
    assert to_embed([row(1, "A speech on roads.")], {1: input_hash("A speech on roads.")}) == []


def test_a_summary_with_a_changed_hash_is_embedded_again():
    todo = to_embed([row(1, "New text.")], {1: input_hash("Old text.")})
    assert len(todo) == 1


def test_outer_spaces_do_not_change_the_hash_and_an_empty_summary_is_skipped():
    assert to_embed([row(1, "  Same.  ")], {1: input_hash("Same.")}) == []
    assert to_embed([row(2, "   "), row(3, "")], {}) == []


def test_token_estimate_is_about_one_token_for_four_characters():
    assert estimate_tokens(["a" * 400, "b" * 40]) == 110


def test_random_pick_is_fixed_for_a_seed_and_skips_the_excluded_ids():
    pool = list(range(1, 200))
    a = pick_random(pool, {1, 2, 3}, 15, seed=5)
    assert a == pick_random(list(reversed(pool)), {1, 2, 3}, 15, seed=5)
    assert len(a) == 15 and not {1, 2, 3} & set(a)


def test_random_pick_fails_when_the_pool_is_too_small():
    with pytest.raises(ValueError):
        pick_random([1, 2], set(), 5, seed=1)


def test_review_entry_has_an_empty_mark_for_each_tag_and_escapes_table_bars():
    sp = {"speech_id": 7, "member": None, "debate_date": "2019-01-07", "loksabha": 16, "word_count": 300,
          "title": "T", "source_url": "https://sansad.in/x", "model": "m", "summary": "S.", "items": []}
    tags = [{"rank": 1, "distance": 0.25, "tag": "A|B", "description": "d"}]
    text = render_speech(1, sp, tags)
    assert "unattributed" in text and "| [ ] | 1 | 0.250 | A/B | d |" in text

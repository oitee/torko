"""site_head writes the title and the description of one page into the HTML shell."""
import datetime

import site_head

SHELL = ('<title>Torko</title>\n<meta name="description" content="General." />\n'
         '<meta property="og:title" content="Torko · Lok Sabha debates" />\n'
         '<meta property="og:description" content="General." />')


def test_the_title_is_member_date_and_torko_as_in_the_browser():
    assert site_head.speech_title("Mahua Moitra", datetime.date(2025, 12, 17)) == "Mahua Moitra · 17 Dec 2025 · Torko"


def test_a_speech_with_no_member_is_called_speech():
    assert site_head.speech_title(None, datetime.date(2001, 3, 5)) == "Speech · 5 Mar 2001 · Torko"


def test_render_replaces_the_title_and_both_descriptions():
    out = site_head.render(SHELL, {"title": "T", "description": "D"})
    assert "<title>T</title>" in out
    assert 'name="description" content="D"' in out
    assert 'property="og:title" content="T"' in out
    assert 'property="og:description" content="D"' in out
    assert "General." not in out


def test_render_escapes_quotes_and_tags():
    out = site_head.render(SHELL, {"title": "<b>A</b>", "description": 'He said "no" & left'})
    assert "<title>&lt;b&gt;A&lt;/b&gt;</title>" in out
    assert 'content="He said &quot;no&quot; &amp; left"' in out


def test_an_empty_description_keeps_the_general_one():
    out = site_head.render(SHELL, {"title": "T", "description": ""})
    assert 'name="description" content="General."' in out


def test_a_long_description_is_cut_at_a_whole_word():
    out = site_head.shorten("word " * 100, limit=22)
    assert out == "word word word word…"


def test_tags_and_entities_of_a_debate_title_are_removed():
    raw = "Verma, member, 6<sup>th</sup> and <span style='mso-bidi-font-weight:bold'>Government&#8217;s move</span>"
    assert site_head.plain(raw) == "Verma, member, 6th and Government’s move"

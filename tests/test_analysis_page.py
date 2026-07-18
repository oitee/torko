"""Tests for the standalone corpus-analysis page and its number coercion.

The heavy aggregation in scripts/analyze_speeches.py needs a DB and is verified
live; these pin the two things that break silently without one: the Decimal->
JSON coercion, and the template/route contract (the __DATA__ placeholder must
exist exactly once and be filled with valid JSON)."""
import json
import pathlib

from scripts.analyze_speeches import num

STATIC = pathlib.Path(__file__).resolve().parent.parent / "static" / "analysis.html"


def test_num_coerces_decimal_and_float():
    from decimal import Decimal
    assert num(Decimal("175")) == 175
    assert isinstance(num(Decimal("175")), int)
    assert num(Decimal("408.97")) == 408.97
    assert num(3.0) == 3
    assert num(None) is None


def test_template_has_exactly_one_data_placeholder():
    html = STATIC.read_text()
    assert html.count("__DATA__") == 1, "route replaces __DATA__ exactly once"
    assert 'id="analysis-data"' in html


def test_route_injects_valid_json_and_leaves_no_placeholder():
    import server

    client = server.app.test_client()
    resp = client.get("/analysis")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "__DATA__" not in body  # placeholder was filled
    # the injected JSON block parses and carries the expected top-level shape
    start = body.index('id="analysis-data"')
    open_tag = body.index(">", start) + 1
    close_tag = body.index("</script>", open_tag)
    data = json.loads(body[open_tag:close_tag])
    assert {"overview", "size", "skew", "speakers", "large", "keywords"} <= set(data)

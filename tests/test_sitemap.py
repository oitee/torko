import xml.etree.ElementTree as ET

import sitemap


def tag(i, name, kind="topic", n=0, status="reviewed"):
    return (i, name, kind, status, n)


def test_top_tags_rank_by_speeches_and_leave_out_place_role_and_person_tags(monkeypatch):
    monkeypatch.setattr(sitemap, "TOP_TAGS", 2)
    tags = [tag(1, "Farmers", n=900), tag(2, "Railways", n=50), tag(3, "Water", n=400),
            tag(4, "Bihar", "place", 5000), tag(5, "Speaker", "role", 9000), tag(6, "Somebody", "person", 9000)]
    top, _ = sitemap.tag_paths(tags)
    assert top == ["/tag/farmers", "/tag/water"]


def test_equal_counts_keep_the_lower_tag_id_first(monkeypatch):
    monkeypatch.setattr(sitemap, "TOP_TAGS", 1)
    top, _ = sitemap.tag_paths([tag(9, "Later", n=10), tag(3, "Earlier", n=10)])
    assert top == ["/tag/earlier"]


def test_places_need_the_minimum_number_of_speeches():
    m = sitemap.MIN_PLACE_SPEECHES
    _, places = sitemap.tag_paths([tag(1, "Uttar Pradesh", "place", m), tag(2, "Tiny Village", "place", m - 1)])
    assert places == ["/place/uttar-pradesh"]


def test_merged_rejected_and_unused_tags_are_left_out():
    tags = [tag(1, "Old Name", n=500, status="merged"), tag(2, "Bad", n=500, status="rejected"), tag(3, "Unused", n=0)]
    assert sitemap.tag_paths(tags) == ([], [])


def test_a_shared_slug_is_listed_only_for_the_tag_that_the_page_opens():
    # "Coal" and "coal" share the slug "coal". The page opens the live tag with the lowest id (4).
    top, _ = sitemap.tag_paths([tag(4, "Coal", n=10), tag(7, "coal", n=900)])
    assert top == ["/tag/coal"]
    top, _ = sitemap.tag_paths([tag(4, "Coal", "role", 10), tag(7, "coal", n=900)])
    assert top == []


def test_render_gives_valid_xml_with_escaped_addresses():
    xml = sitemap.render("https://torko.in", ["/", "/party/A%26B"])
    root = ET.fromstring(xml)
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    assert [e.text for e in root.findall("s:url/s:loc", ns)] == ["https://torko.in/", "https://torko.in/party/A%26B"]


def test_site_url_reads_vite_site_url_and_drops_the_last_slash():
    assert sitemap.site_url({"VITE_SITE_URL": "https://example.org/"}) == "https://example.org"
    assert sitemap.site_url({}) == "https://torko.in"

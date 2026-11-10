from urllib.robotparser import RobotFileParser

import robots

BASE = "https://torko.in"


def parser():
    p = RobotFileParser()
    p.parse(robots.render(BASE).splitlines())
    return p


def test_search_engines_may_read_the_pages_and_the_data_that_the_pages_load():
    p = parser()
    for path in ["/", "/method", "/member/12", "/tag/farmers", "/place/bihar", "/party/BJP",
                 "/speech/5", "/api/member/12", "/api/tag/farmers", "/api/speeches?tag=farmers", "/assets/index.js"]:
        assert p.can_fetch("Googlebot", BASE + path), path
        assert p.can_fetch("bingbot", BASE + path), path


def test_search_pages_paid_calls_and_the_old_dashboard_are_blocked():
    p = parser()
    for path in ["/search", "/search?q=water", "/my-mp?q=pune", "/api/search?q=coal",
                 "/api/distribution?loksabha=18", "/api/dashboard/debates", "/analysis", "/dashboard.html",
                 "/search.html", "/index.html"]:
        assert not p.can_fetch("Googlebot", BASE + path), path


def test_ai_training_bots_may_read_nothing_but_ai_search_agents_may_read_the_pages():
    p = parser()
    for bot in robots.AI_TRAINING_BOTS:
        assert not p.can_fetch(bot, BASE + "/member/12"), bot
    for agent in ["OAI-SearchBot", "ChatGPT-User", "Claude-SearchBot", "Claude-User", "PerplexityBot"]:
        assert p.can_fetch(agent, BASE + "/member/12"), agent
        assert not p.can_fetch(agent, BASE + "/search"), agent


def test_the_sitemap_address_is_given():
    assert parser().site_maps() == [BASE + "/sitemap.xml"]

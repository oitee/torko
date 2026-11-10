"""The robots.txt of the public site: which crawlers may read which addresses.

robots.txt is a request, not a lock. Large companies obey it. A scraper that ignores it needs a rate limit in the web server.

The policy:
- Search engines may read the whole site, except the addresses in BLOCKED.
  /api/ stays open, because a search engine runs the JavaScript of a page, and the page reads its data from /api/.
- BLOCKED holds addresses with no page worth indexing, or with a cost for each call:
  the Search and Your MP pages (each search text makes a new address), the question reader and the search
  suggestions (they can call a paid model), the old dashboard, and its live read from the official site.
- AI_TRAINING_BOTS may read nothing. They collect text to train models and send no reader to the site.
  The agents of AI search tools are not in the list: they fetch a page for a user's question and link to it.
- The last line gives the address of the sitemap.
"""

BLOCKED = [
    "/search",           # also /search.html of the old dashboard
    "/my-mp",
    "/api/search",
    "/api/distribution",
    "/api/dashboard/",
    "/analysis",         # also /analysis.html
    "/dashboard.html",
    "/debate.html",
    "/speaker.html",
    "/index.html",
]

# Crawlers that collect training data for AI models. Google-Extended and Applebot-Extended are not crawlers:
# they are names that Google and Apple read to decide about training. A block on them does not change search results.
AI_TRAINING_BOTS = [
    "GPTBot",
    "ClaudeBot",
    "anthropic-ai",
    "CCBot",
    "Google-Extended",
    "Applebot-Extended",
    "Bytespider",
    "meta-externalagent",
    "Amazonbot",
    "cohere-training-data-crawler",
]


def render(base):
    """The robots.txt text for the given site address, with no "/" at the end."""
    lines = ["User-agent: *"] + [f"Disallow: {p}" for p in BLOCKED] + [""]
    lines += [f"User-agent: {bot}" for bot in AI_TRAINING_BOTS] + ["Disallow: /", ""]
    lines += [f"Sitemap: {base}/sitemap.xml", ""]
    return "\n".join(lines)

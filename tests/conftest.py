"""Shared helpers for the parser test-suite."""
from bs4 import BeautifulSoup


def first_block(html: str, tag: str = "p"):
    """Parse `html` and return the first `<tag>` element (a BeautifulSoup node).

    The label/anchor helpers in debate_fetch operate on a single paragraph
    node, so most Part-2 tests need one parsed block to hand them.
    """
    return BeautifulSoup(html, "lxml").find(tag)

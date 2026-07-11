from bs4 import BeautifulSoup


def first_block(html: str, tag: str = "p"):
    return BeautifulSoup(html, "lxml").find(tag)

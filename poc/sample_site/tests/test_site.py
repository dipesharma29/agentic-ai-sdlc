"""Checks for the sample site. Standard library only, so they run anywhere Python runs."""

import unittest
from html.parser import HTMLParser
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
PAGES = sorted(SITE.glob("*.html"))


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.images, self.inputs, self.title, self._in_title = [], [], [], "", False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and "href" in a:
            self.links.append(a["href"])
        elif tag == "img":
            self.images.append(a)
        elif tag == "input":
            self.inputs.append(a)
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def parse(page: Path) -> PageParser:
    p = PageParser()
    p.feed(page.read_text(encoding="utf-8"))
    return p


class SiteTests(unittest.TestCase):
    def test_every_page_has_a_title(self):
        for page in PAGES:
            with self.subTest(page=page.name):
                self.assertTrue(parse(page).title.strip())

    def test_local_links_point_to_existing_files(self):
        for page in PAGES:
            for href in parse(page).links:
                if href.startswith(("http", "#", "mailto:")):
                    continue
                with self.subTest(page=page.name, href=href):
                    self.assertTrue((SITE / href).exists(), f"{page.name} links to missing file {href}")

    def test_images_have_alt_text_and_exist(self):
        for page in PAGES:
            for img in parse(page).images:
                with self.subTest(page=page.name, src=img.get("src")):
                    self.assertTrue(img.get("alt"), "image is missing alt text")
                    self.assertTrue((SITE / img["src"]).exists(), f"missing image {img['src']}")


if __name__ == "__main__":
    unittest.main()

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
        self.tags = []            # every tag name seen, open or close

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
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
        self.tags.append(tag)
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def parse(page: Path) -> PageParser:
    p = PageParser()
    p.feed(page.read_text(encoding="utf-8"))
    return p


# The tags a page in this site is allowed to use. A typo in a tag name - opening
# or closing - shows up as a name that is not in here.
KNOWN_TAGS = {
    "html", "head", "body", "title", "meta", "link", "style", "script",
    "header", "nav", "main", "section", "article", "footer", "aside",
    "h1", "h2", "h3", "h4", "h5", "h6", "p", "span", "div", "br", "hr",
    "a", "img", "svg", "path", "ul", "ol", "li", "strong", "em",
    "form", "label", "input", "textarea", "button", "select", "option", "table",
    "thead", "tbody", "tr", "th", "td",
}


class SiteTests(unittest.TestCase):
    def test_every_page_has_a_title(self):
        for page in PAGES:
            with self.subTest(page=page.name):
                self.assertTrue(parse(page).title.strip())

    def test_no_page_uses_a_misspelled_tag(self):
        """Catches typos like </htmll>, which browsers swallow silently."""
        for page in PAGES:
            for tag in parse(page).tags:
                with self.subTest(page=page.name, tag=tag):
                    self.assertIn(tag, KNOWN_TAGS,
                                  f"{page.name} uses <{tag}>, which is not a valid tag here")

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

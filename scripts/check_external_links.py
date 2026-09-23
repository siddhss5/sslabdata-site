#!/usr/bin/env python3
"""
Report the external links in a built site that do not answer. Never fails.

Reads every http(s) href in the site's HTML pages, requests each URL once
and prints those that give an error, with the pages that link them. It needs
the network, so it runs on demand (.github/workflows/external-links.yml),
never on a pull request, and exits 0 whatever it finds:

    python scripts/check_external_links.py _site
"""

import argparse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path


class Hrefs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = set()

    def handle_starttag(self, tag, attrs):
        href = dict(attrs).get("href") if tag == "a" else None
        if href and href.lower().startswith(("http://", "https://")):
            self.urls.add(href)


def external_links(site: Path) -> dict:
    """Map each external URL in the site's HTML to the pages that link it."""
    pages = {}
    for page in sorted(site.rglob("*.html")):
        parser = Hrefs()
        parser.feed(page.read_text(encoding="utf-8"))
        for url in parser.urls:
            pages.setdefault(url, []).append(str(page.relative_to(site)))
    return pages


def check(url: str):
    """None if the URL answers, otherwise the error."""
    request = urllib.request.Request(url, headers={"User-Agent": "external-link-check"})
    try:
        with urllib.request.urlopen(request, timeout=20):
            return None
    except Exception as error:  # report every failure, whatever its kind
        return str(error)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("site", type=Path, help="the built site directory")
    links = external_links(parser.parse_args(argv).site)
    with ThreadPoolExecutor(max_workers=8) as pool:
        errors = dict(zip(links, pool.map(check, links)))
    broken = {url: error for url, error in errors.items() if error}
    for url, error in sorted(broken.items()):
        print(f"{url}\n  {error}\n  linked from: {', '.join(links[url])}")
    print(f"{len(broken)} of {len(links)} external links did not answer.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

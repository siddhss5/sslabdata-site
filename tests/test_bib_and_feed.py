"""The .bib downloads on person and project pages, and the works feed.

Each person and project page with works links to a .bib holding exactly the
BibTeX of the works it lists, byte for byte as the data file carries it; the
feed at /feed.xml, which the theme's footer and head link to, is Atom and
lists every work that has a year, newest first. The built-site checks reuse
the builds in test_site_build.py and are skipped with them when Bundler or the
pinned Jekyll is not installed.
"""

import copy
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import yaml

from test_site_build import FIXTURE, NEWCOMER, PI, PLAIN, REPO_ROOT, build, demo, demo_data, page  # noqa: F401
from test_site_template_source import allowlist, unescaped_outputs, unsafe_link_targets

ATOM = "{http://www.w3.org/2005/Atom}"
FEED = REPO_ROOT / "site" / "feed.xml"

# BibTeX that Liquid, YAML, HTML or XML could each misread.
TRICKY_BIBTEX = ("@misc{tricky,\n  title = {{{ site.title }} {% raw %} <b>&amp;</b> Côté 87\\% ---},\n"
                 "  note = \"tab\there, trailing space \" \n}")


def expected_bib(document, entity):
    works = {w["bib_id"]: w for w in document["works"]}
    return "\n\n".join(works[i]["bibtex"] for i in entity["work_ids"]) + "\n"


def check_bibs(built, document, keys_are_ids=False):
    checked = 0
    for section, entities in [("people", document["people"]), ("projects", document["projects"])]:
        for e in entities:
            html = page(built, f"{section}/{e['id']}")
            bib = built / section / f"{e['id']}.bib"
            if not e.get("work_ids"):
                assert not bib.exists(), bib
                assert ".bib" not in html, e["id"]
                continue
            assert f'<a href="/{section}/{e["id"]}.bib" download>' in html, e["id"]
            text = bib.read_bytes().decode("utf-8")
            assert text == expected_bib(document, e), e["id"]
            if keys_are_ids:
                assert re.findall(r"^@\w+\{([^,\s]+),", text, re.MULTILINE) == e["work_ids"], e["id"]
            checked += 1
    assert checked


# An Atom date: the feed dates each work by the first day of its year.
DATE = re.compile(r"\d{4}-01-01T00:00:00Z")


def feed_entries(built):
    root = ET.parse(built / "feed.xml").getroot()
    assert root.tag == ATOM + "feed"
    assert DATE.fullmatch(root.findtext(ATOM + "updated"))
    for e in root.findall(ATOM + "entry"):
        assert DATE.fullmatch(e.findtext(ATOM + "updated")), e.findtext(ATOM + "id")
    return [{"id": e.findtext(ATOM + "id"), "title": e.findtext(ATOM + "title"),
             "link": e.find(ATOM + "link").get("href"),
             "authors": [a.findtext(ATOM + "name") for a in e.findall(ATOM + "author")],
             "summary": e.findtext(ATOM + "summary")} for e in root.findall(ATOM + "entry")]


def check_feed(built, document, url):
    entries = feed_entries(built)
    works = {w["bib_id"]: w for w in document["works"] if w["year"] is not None}
    ids = [e["id"].removeprefix(f"{url}/publications/").removesuffix("/") for e in entries]
    assert sorted(ids) == sorted(works)
    years = [works[i]["year"] for i in ids]
    assert years == sorted(years, reverse=True)
    for i, e in zip(ids, entries):
        w = works[i]
        assert e["link"] == e["id"] == f"{url}/publications/{i}/"
        assert (built / "publications" / i / "index.html").is_file(), i
        assert e["title"] == w["title"]
        assert e["authors"] == [a["name"] for a in w["authors"]]
        assert e["summary"] == (f"{w['venue']['name']}, {w['year']}" if w["venue"] else str(w["year"]))


@pytest.fixture(scope="module")
def tricky(tmp_path_factory):
    """The fixture, with a work whose BibTeX is hard to copy unchanged."""
    document = copy.deepcopy(FIXTURE)
    next(w for w in document["works"] if w["bib_id"] == PLAIN)["bibtex"] = TRICKY_BIBTEX
    built = build(tmp_path_factory.mktemp("tricky"), yaml.safe_dump(document, allow_unicode=True))
    return built, document


@pytest.fixture(scope="module")
def themed(tmp_path_factory):
    """The demo built with the theme, whose footer and head link to the feed."""
    tmp = tmp_path_factory.mktemp("themed")
    data, people_groups = demo_data(tmp)
    return build(tmp, data, people_groups, theme=True), yaml.safe_load(data)


def test_demo_bibs_hold_exactly_the_works_each_page_lists(demo):
    check_bibs(*demo, keys_are_ids=True)


def test_bibs_copy_bibtex_byte_for_byte(tricky):
    built, document = tricky
    check_bibs(built, document)
    assert TRICKY_BIBTEX in (built / "people" / f"{PI}.bib").read_bytes().decode("utf-8")
    assert not (built / "people" / f"{NEWCOMER}.bib").exists()


def test_demo_feed_lists_every_work_newest_first(demo):
    check_feed(*demo, "https://fixture.invalid")


def test_feed_is_well_formed_and_escapes_the_data(tricky):
    check_feed(*tricky, "https://fixture.invalid")
    text = (tricky[0] / "feed.xml").read_text(encoding="utf-8")
    assert "<script>" not in text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in text


@pytest.mark.parametrize("undated", ["one", "every"])
def test_feed_leaves_out_undated_works_and_stays_valid(undated, tmp_path):
    document = copy.deepcopy(FIXTURE)
    for w in document["works"]:
        if undated == "every" or w["bib_id"] == PLAIN:
            w["year"] = None
    built = build(tmp_path, yaml.safe_dump(document, allow_unicode=True))
    check_feed(built, document, "https://fixture.invalid")
    root = ET.parse(built / "feed.xml").getroot()
    if undated == "every":
        assert root.findall(ATOM + "entry") == []
        assert root.findtext(ATOM + "updated") == "1970-01-01T00:00:00Z"
    else:
        assert f"/publications/{PLAIN}/" not in (built / "feed.xml").read_text(encoding="utf-8")


def test_theme_footer_and_head_link_to_the_works_feed(themed):
    built, document = themed
    html = page(built, "")
    assert '<link href="/feed.xml" type="application/atom+xml" rel="alternate"' in html
    assert re.search(r'<li><a href="/feed.xml"><i [^>]*></i> Feed</a></li>', html)
    check_feed(built, document, "https://fixture.invalid")


def test_themed_build_is_deterministic(themed, tmp_path):
    first, _ = themed
    second = build(tmp_path, *demo_data(tmp_path), theme=True)
    outputs = sorted(p.relative_to(first) for p in first.rglob("*.bib")) + [Path("feed.xml")]
    assert len(outputs) > 1
    for p in outputs:
        assert (first / p).read_bytes() == (second / p).read_bytes(), p


def test_feed_template_escapes_every_data_output():
    source = FEED.read_text(encoding="utf-8")
    unescaped = unescaped_outputs(source)
    assert unescaped == allowlist(source).keys()
    assert all("absolute_url" in e for e in unescaped), unescaped
    assert unsafe_link_targets(source) == []

"""Build the Jekyll site from a fixture data file and check the HTML it writes.

The fixture is a hand-written sslabdata document whose strings carry HTML and
Markdown, and whose links cover each origin and verification status. The site
is copied to a temporary directory with the fixture as `_data/lab.yml` and
built with the pinned gems (`site/Gemfile.lock`). The theme is switched off so
the checks cover only this repository. In its place a stub `single` layout
prints the page title and the navigation from `_data/navigation.yml`, the two
values the theme's layout takes from this repository; the other checks are on
page content, which the theme does not produce.

Before each build, scripts/generate_pages.py writes the entity pages from the
data file. The same build is also run on the demo document the pinned
sslabdata emits, to check which of its links are shown and that its entity
pages link each relationship both ways. The demo is also built once with the
theme, to check that no page loads anything from another host.

Skipped when Bundler or the pinned Jekyll is not installed.
"""

import html
import os
import re
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

import pytest
import yaml


REPO_ROOT = Path(__file__).parent.parent
SITE = REPO_ROOT / "site"
GEMFILE = SITE / "Gemfile"

SCRIPT_TITLE = "<script>alert(1)</script> and a tidy kitchen"
NOTE = "*emphasis* & <b>bold</b>"
PERSON_NAME = "*Ada* <i>Lovelace</i>"

# Derived links: DOI and arXiv are built from a declared identifier; a PDF is
# guessed from a pattern.
DOI_UNCHECKED = "https://doi-derived.invalid/10.1/x"
ARXIV_UNCHECKED = "https://arxiv-derived.invalid/abs/2401.00001"
PDF_UNCHECKED = "https://pdf-unchecked.invalid/script2024.pdf"
PDF_MISSING = "https://pdf-missing.invalid/missing2024.pdf"
PDF_VERIFIED = "https://pdf-verified.invalid/plain2024.pdf"
SIDECAR_UNCHECKED = "https://sidecar-unchecked.invalid/abs/1"
INPUT_UNCHECKED = "https://input-unchecked.invalid/talk"
INPUT_VERIFIED = "https://input-verified.invalid/talk"
INPUT_MISSING = "https://input-missing.invalid/talk"
INPUT_MISSING_WEB = "https://input-missing.invalid/site"

# Only http, https and mailto become links; anything else is not rendered.
BAD_URLS = ["javascript:alert(1)", "data:text/html;base64,PHNjcmlwdD4=",
            "vbscript:msgbox(1)", "JaVaScRiPt:alert(2)", "relative/page.html"]
GOOD_URLS = ["http://http.invalid/", "https://https.invalid/", "mailto:ada@mail.invalid"]


def link(url, origin, status):
    return {"url": url, "label": None, "origin": origin,
            "verification": {"status": status, "checked_at": None}}


def work(bib_id, title, links, note=None):
    return {
        "bib_id": bib_id, "title": title, "year": 2024,
        "authors": [{"name": PERSON_NAME, "person_id": "ada"},
                    {"name": "<u>Grace</u> Hopper", "person_id": None}],
        "venue": {"kind": "journal", "name": "*Journal* <em>of</em> Tests"},
        "category": "<b>Journal</b> Papers", "note": note,
        "abstract": "An abstract with <img src=x onerror=alert(2)>.",
        "links": links, "project_ids": ["demo"], "bibtex": "@article{x}",
    }


FIXTURE = {
    "lab": {"name": "Fixture <Lab>", "department": "*Dept*",
            "university": "U & U", "description": "<b>desc</b>",
            "website": GOOD_URLS[0], "github": BAD_URLS[3], "youtube": BAD_URLS[1]},
    "works": [
        work("script2024", SCRIPT_TITLE, note=NOTE, links={
            "pdf": [link(PDF_UNCHECKED, "derived", "unchecked")],
            "doi": [link(DOI_UNCHECKED, "derived", "unchecked")],
            "arxiv": [link(SIDECAR_UNCHECKED, "sidecar", "unchecked"),
                      link(ARXIV_UNCHECKED, "derived", "unchecked")],
            "video": [link(INPUT_UNCHECKED, "input", "unchecked")],
            "url": [link(BAD_URLS[0], "input", "unchecked")],
        }),
        work("plain2024", "A plain title", links={
            "pdf": [link(PDF_VERIFIED, "derived", "verified")],
            "doi": [link(GOOD_URLS[1], "derived", "unchecked")],
            "url": [link(INPUT_VERIFIED, "input", "verified")],
            "video": [link(INPUT_VERIFIED, "input", "verified")],
        }),
        work("missing2024", "An input link nobody found", links={
            "pdf": [link(PDF_MISSING, "derived", "missing")],
            "url": [link(INPUT_MISSING_WEB, "input", "missing")],
            "video": [link(INPUT_MISSING, "input", "missing")],
        }),
    ],
    "people": [
        {"id": "ada", "name": PERSON_NAME, "role": "phd_student",
         "status": "current", "thesis_title": "*Thesis* <b>x</b>",
         "co_advisor": "<i>Someone</i>", "start_year": 2020,
         "website": BAD_URLS[2]},
        {"id": "pi", "name": "<b>The</b> *PI*", "role": "professor",
         "status": "current", "website": GOOD_URLS[2]},
        # Roles and statuses a fixed list of groups would drop.
        {"id": "visitor", "name": "Vera Visitor", "role": "visiting_scholar", "status": "current"},
        {"id": "postdoc", "name": "Paul Postdoc", "role": "postdoc", "status": "current"},
        {"id": "emeritus", "name": "Emma Emeritus", "role": "professor", "status": "alumni"},
        {"id": "engineer", "name": "Eli Engineer", "role": "engineer", "status": "current"},
    ],
    "projects": [
        {"id": "demo", "title": "*Project* <b>One</b>",
         "description": "Project _description_ <script>x</script>",
         "status": "active", "website": BAD_URLS[4], "work_ids": ["script2024", "plain2024", "missing2024"]},
    ],
    # Optional fields are left out or null: no work_ids or people_ids.
    "collaborators": [{"key": "collab", "name": "<b>Collab</b> *Orator*", "work_ids": None}],
}


# People groups for the fixture build. `professor` and `engineer` are each
# named twice; `visiting_scholar` and the other roles are not named.
PEOPLE_GROUPS = [{"title": "Faculty", "roles": ["professor"]},
                 {"title": "Research Staff", "roles": ["engineer", "professor"]},
                 {"title": "Engineers", "roles": ["engineer"]}]


# The title is filtered as the theme's seo.html and single.html filter it.
STUB_LAYOUT = """<!doctype html>
<title>{{ page.title | markdownify | strip_html | strip_newlines | escape_once }}</title>
<nav>{% for item in site.data.navigation.main %}<a href="{{ item.url | relative_url }}">{{ item.title | escape }}</a>{% endfor %}</nav>
<h1 class="page-title">{{ page.title | markdownify | remove: "<p>" | remove: "</p>" | strip }}</h1>
{{ content }}
"""


def _jekyll_available():
    if shutil.which("bundle") is None:
        return False
    env = dict(os.environ, BUNDLE_GEMFILE=str(GEMFILE))
    result = subprocess.run(["bundle", "exec", "jekyll", "--version"],
                            capture_output=True, env=env, cwd=SITE)
    return result.returncode == 0


def build(tmp, data, people_groups=None, theme=False):
    """Build a copy of site/ with `data` as _data/lab.yml; return the output."""
    if not _jekyll_available():
        pytest.skip("bundle exec jekyll is not available")
    source = tmp / "site"
    shutil.copytree(SITE, source, ignore=shutil.ignore_patterns(
        "_site", ".jekyll-cache", ".jekyll-metadata", ".bundle", "vendor",
        "lab.yml", "_config.generated.yml", "_entities"))
    (source / "_data" / "lab.yml").write_text(data, encoding="utf-8")
    subprocess.run([sys.executable, "scripts/generate_pages.py", source / "_data" / "lab.yml",
                    source / "_entities"], check=True, cwd=REPO_ROOT)
    if not theme:
        # Drop the theme, whose layouts these checks do not cover; a later
        # config file cannot unset it.
        config = source / "_config.yml"
        lines = config.read_text(encoding="utf-8").splitlines(keepends=True)
        config.write_text("".join(l for l in lines if not l.startswith("theme:")),
                          encoding="utf-8")
        (source / "_layouts").mkdir()
        (source / "_layouts" / "single.html").write_text(STUB_LAYOUT, encoding="utf-8")
    (source / "_config.test.yml").write_text(
        "title: Fixture\nurl: https://fixture.invalid\nbaseurl: ''\n"
        "repository: fixture/fixture\n" +
        (yaml.safe_dump({"people_groups": people_groups}) if people_groups else ""),
        encoding="utf-8")
    dest = tmp / "_site"
    env = dict(os.environ, BUNDLE_GEMFILE=str(GEMFILE), BUNDLE_FROZEN="true",
               JEKYLL_ENV="production")
    result = subprocess.run(
        ["bundle", "exec", "jekyll", "build", "--source", str(source),
         "--destination", str(dest),
         "--config", f"{source / '_config.yml'},{source / '_config.test.yml'}"],
        capture_output=True, text=True, env=env, cwd=SITE)
    assert result.returncode == 0, result.stdout + result.stderr
    return dest


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    return build(tmp_path_factory.mktemp("site"),
                 yaml.safe_dump(FIXTURE, allow_unicode=True), PEOPLE_GROUPS)


@pytest.fixture(scope="module")
def unconfigured(tmp_path_factory):
    """The fixture built with no people_groups at all."""
    return build(tmp_path_factory.mktemp("unconfigured"),
                 yaml.safe_dump(FIXTURE, allow_unicode=True))


def demo_data(tmp):
    """The demo document the pinned sslabdata emits, as text, and the
    people_groups generate_site_config.py writes from demo/lab.yaml."""
    data = tmp / "lab.yml"
    result = subprocess.run(
        [str(Path(sys.executable).parent / "sslabdata"), "--config", "demo/lab.yaml",
         "--output", str(data)], capture_output=True, text=True, cwd=REPO_ROOT)
    assert result.returncode == 0, result.stdout + result.stderr
    config = tmp / "_config.generated.yml"
    subprocess.run([sys.executable, "scripts/generate_site_config.py", "demo/lab.yaml", config],
                   check=True, cwd=REPO_ROOT)
    people_groups = yaml.safe_load(config.read_text(encoding="utf-8"))["people_groups"]
    return data.read_text(encoding="utf-8"), people_groups


@pytest.fixture(scope="module")
def demo(tmp_path_factory):
    """The site built from the demo document the pinned sslabdata emits."""
    tmp = tmp_path_factory.mktemp("demo")
    data, people_groups = demo_data(tmp)
    return build(tmp, data, people_groups), yaml.safe_load(data)


def page(built, path):
    return (built / path / "index.html").read_text(encoding="utf-8")


def all_html(built):
    return "\n".join(p.read_text(encoding="utf-8") for p in built.rglob("*.html"))


PAGES = ["", "publications", "projects"]


@pytest.mark.parametrize("path", PAGES)
def test_title_is_literal_text(built, path):
    html = page(built, path)
    assert "&lt;script&gt;alert(1)&lt;/script&gt; and a tidy kitchen" in html
    assert "<script>alert(1)</script>" not in html


@pytest.mark.parametrize("path", PAGES)
def test_note_is_plain_text_not_markdown(built, path):
    html = page(built, path)
    assert "*emphasis* &amp; &lt;b&gt;bold&lt;/b&gt;" in html
    assert "<em>emphasis</em>" not in html
    assert "<b>bold</b>" not in html


def test_no_markup_from_data_reaches_the_site(built):
    html = all_html(built)
    for raw in ["<script>x</script>", "<b>", "<i>", "<u>", "<em>of</em>",
                "<img src=x", "<em>Ada</em>", "<em>Dept</em>", "<em>PI</em>",
                "<em>Project</em>", "<em>description</em>", "<em>Thesis</em>",
                "<em>Orator</em>", "<em>Journal</em>", "<Lab>"]:
        assert raw not in html, raw
    for literal in ["*Ada* &lt;i&gt;Lovelace&lt;/i&gt;", "*Thesis* &lt;b&gt;x&lt;/b&gt;",
                    "&lt;b&gt;The&lt;/b&gt; *PI*", "*Project* &lt;b&gt;One&lt;/b&gt;",
                    "Project _description_ &lt;script&gt;x&lt;/script&gt;",
                    "&lt;b&gt;Collab&lt;/b&gt; *Orator*", "*Journal* &lt;em&gt;of&lt;/em&gt; Tests",
                    "&lt;b&gt;Journal&lt;/b&gt; Papers", "Fixture &lt;Lab&gt;"]:
        assert literal in html, literal


@pytest.mark.parametrize("url", [PDF_UNCHECKED, PDF_MISSING, SIDECAR_UNCHECKED])
def test_unverified_guessed_and_other_origin_links_are_not_rendered(built, url):
    for p in built.rglob("*"):
        if p.is_file():
            assert url not in p.read_text(encoding="utf-8", errors="replace"), p


@pytest.mark.parametrize("path", ["", "publications"])
def test_identifier_links_are_rendered_without_label(built, path):
    """Derived DOI and arXiv links are rendered though unchecked, unlabelled."""
    html = page(built, path)
    for url, text in [(DOI_UNCHECKED, "DOI"), (ARXIV_UNCHECKED, "arXiv")]:
        anchor = f'<a href="{url}" class="btn btn--inverse btn--small" target="_blank">{text}</a>'
        assert anchor in html, text
        assert anchor + " <small" not in html, text


def test_verified_guessed_link_is_rendered_without_label(built):
    for path, anchor in [
        ("publications", f'<strong><a href="{PDF_VERIFIED}">A plain title</a></strong>'),
        ("projects", f'<a href="{PDF_VERIFIED}">A plain title</a>'),
    ]:
        html = page(built, path)
        assert anchor in html, path
        assert anchor + " <small" not in html, path


def test_unverified_input_link_is_labelled_unchecked(built):
    for path, anchor in [
        ("publications", f'<a href="{INPUT_UNCHECKED}" class="btn btn--inverse btn--small" target="_blank">Video</a>'),
        ("projects", f'<a href="{INPUT_UNCHECKED}" style="margin-right: 0.6em;">Video</a>'),
    ]:
        html = page(built, path)
        assert anchor + ' <small class="link-status" style="color: #8a6d3b;">(unchecked)</small>' in html, path


def test_missing_input_link_is_labelled_unchecked(built):
    for path, anchors in [
        ("publications", [f'<a href="{INPUT_MISSING}" class="btn btn--inverse btn--small" target="_blank">Video</a>']),
        ("projects", [f'<a href="{INPUT_MISSING_WEB}" style="margin-right: 0.6em;">Website</a>',
                      f'<a href="{INPUT_MISSING}" style="margin-right: 0.6em;">Video</a>']),
    ]:
        html = page(built, path)
        for anchor in anchors:
            assert anchor + ' <small class="link-status" style="color: #8a6d3b;">(unchecked)</small>' in html, path
        assert "(missing)" not in html, path


def test_verified_input_link_has_no_label(built):
    html = page(built, "projects")
    for text in ["Website", "Video"]:
        anchor = f'<a href="{INPUT_VERIFIED}" style="margin-right: 0.6em;">{text}</a>'
        assert anchor in html
        assert anchor + " <small" not in html


def test_only_http_https_and_mailto_urls_become_links(built):
    html = all_html(built)
    for url in BAD_URLS:
        assert url not in html, url
    for url in GOOD_URLS:
        assert f'href="{url}"' in html, url
    targets = re.findall(r'(?:href|src)="([^"]*)"', html)
    assert all(t.startswith(("http://", "https://", "mailto:", "/")) for t in targets), targets


def test_works_not_publications(built):
    html = all_html(built)
    assert "Publications" not in html
    works = page(built, "publications")
    assert "<title>Works</title>" in works
    assert '<h1 class="page-title">Works</h1>' in works
    for path in PAGES + ["people"]:
        assert '<a href="/publications/">Works</a>' in page(built, path), path
    assert "Recent Works" in page(built, "")
    assert "Works (3)</summary>" in page(built, "projects")


def test_demo_shows_identifier_links_and_hides_guessed_pdfs(demo):
    built, document = demo
    html = all_html(built)
    links = [(kind, l) for w in document["works"]
             for kind, records in (w.get("links") or {}).items() for l in records]
    by_kind = {kind: [l for k, l in links if k == kind] for kind in ("doi", "arxiv", "pdf")}
    # The pinned sslabdata builds all three as derived and unchecked.
    assert all(l["origin"] == "derived" and l["verification"]["status"] == "unchecked"
               for records in by_kind.values() for l in records)
    assert by_kind["doi"] and by_kind["arxiv"] and by_kind["pdf"]
    for kind, text in [("doi", "DOI"), ("arxiv", "arXiv")]:
        for l in by_kind[kind]:
            anchor = f'<a href="{l["url"]}" class="btn btn--inverse btn--small" target="_blank">{text}</a>'
            assert anchor in html, l["url"]
            assert anchor + " <small" not in html, l["url"]
    for l in by_kind["pdf"]:
        assert l["url"] not in html, l["url"]


def test_demo_entity_pages_link_both_ways(demo):
    """Every work, person, project and co-author has a page; each relationship
    in the data file is linked from both ends; every internal link resolves."""
    built, document = demo
    url = {"work": "/publications/{}/", "person": "/people/{}/",
           "project": "/projects/{}/", "coauthor": "/coauthors/{}/"}
    works = {w["bib_id"]: w for w in document["works"]}
    pages = [url["work"].format(i) for i in works]
    edges = set()
    for w in works.values():
        work = url["work"].format(w["bib_id"])
        for a in w["authors"]:
            edges.add((work, url["person"].format(a["person_id"]) if a["person_id"]
                       else url["coauthor"].format(a["collaborator_key"])))
        edges |= {(work, url["project"].format(i)) for i in w["project_ids"]}
    for kind, key, entities in [("person", "id", document["people"]),
                                ("project", "id", document["projects"]),
                                ("coauthor", "key", document["collaborators"])]:
        for e in entities:
            here = url[kind].format(e[key])
            pages.append(here)
            for wid in e["work_ids"]:
                edges.add((here, url["work"].format(wid)))
                for a in works[wid]["authors"]:
                    if kind == "person" and a["collaborator_key"]:
                        edges.add((here, url["coauthor"].format(a["collaborator_key"])))
                    if kind == "coauthor" and a["person_id"]:
                        edges.add((here, url["person"].format(a["person_id"])))
            edges |= {(here, url["person"].format(i)) for i in e.get("people_ids", [])}
    for p in pages:
        assert (built / p.strip("/") / "index.html").is_file(), p

    def links(path):
        return set(re.findall(r'href="(/[^"#]*)', (built / path.strip("/") / "index.html").read_text(encoding="utf-8")))

    for a, b in edges:
        assert b in links(a), (a, b)
        assert a in links(b), (b, a)
    for f in built.rglob("*.html"):
        for target in re.findall(r'href="(/[^"#]*)', f.read_text(encoding="utf-8")):
            assert (built / target.lstrip("/") / "index.html").is_file() or \
                (built / target.lstrip("/")).is_file(), (f, target)


def assert_titled(text, name):
    """The page's title and heading are `name` as escaped text; returns the title."""
    title = re.search(r"<title>(.*)</title>", text)[1]
    heading = re.search(r'<h1 class="page-title">(.*)</h1>', text)[1]
    for shown in (title, heading):
        assert html.unescape(shown) == name and "<" not in shown, (shown, name)
    return title


def test_demo_entity_pages_are_titled_by_their_entity(demo):
    """Each entity page's title and heading are its entity's name, escaped, and
    no two pages of a kind share a title."""
    built, document = demo
    for path, key, name, entities in [("publications", "bib_id", "title", document["works"]),
                                      ("people", "id", "name", document["people"]),
                                      ("projects", "id", "title", document["projects"]),
                                      ("coauthors", "key", "name", document["collaborators"])]:
        titles = [assert_titled(page(built, f"{path}/{e[key]}"), e[name]) for e in entities]
        assert len(set(titles)) == len(titles) == len(entities), path


def test_fixture_entity_titles_are_literal_text(built):
    for path, name in [("people/ada", PERSON_NAME), ("publications/script2024", SCRIPT_TITLE),
                       ("projects/demo", "*Project* <b>One</b>"),
                       ("coauthors/collab", "<b>Collab</b> *Orator*")]:
        assert_titled(page(built, path), name)


def test_demo_coauthor_pages_show_other_spellings_only_when_there_are_some(demo):
    built, document = demo
    for c in document["collaborators"]:
        text = page(built, f"coauthors/{c['key']}")
        assert "not a verified person" in text, c["name"]
        if len(c["name_variants"]) == 1:
            assert "Also written as" not in text, c["name"]
    priya = next(c for c in document["collaborators"] if c["name"] == "Priya Patel")
    assert "<p>Also written as P. Patel.</p>" in page(built, f"coauthors/{priya['key']}")


def test_demo_coauthor_index_links_every_coauthor(demo):
    built, document = demo
    text = page(built, "coauthors")
    assert "not a verified person" in text
    for c in document["collaborators"]:
        assert f'<a href="/coauthors/{c["key"]}/">{html.escape(c["name"])}</a>' in text, c["name"]


def people_sections(built):
    """The People page's headings, in order, each with the ids of the people under it."""
    text = page(built, "people").split("Collaborators")[0]
    sections = []
    for m in re.finditer(r'<h[23][^>]*>(.*?)</h[23]>|<span id="([^"]+)"><a href="/people/', text):
        if m[1] is not None:
            sections.append((html.unescape(m[1]), []))
        else:
            sections[-1][1].append(m[2])
    return sections


@pytest.mark.parametrize("site", ["built", "unconfigured", "demo"])
def test_every_person_appears_exactly_once_on_the_people_page(site, request):
    built = request.getfixturevalue(site)
    people = built[1]["people"] if site == "demo" else FIXTURE["people"]
    built = built[0] if site == "demo" else built
    shown = [i for _, ids in people_sections(built) for i in ids]
    assert sorted(shown) == sorted(p["id"] for p in people)


def test_people_groups_title_and_order_and_show_each_role_once(built):
    assert people_sections(built) == [
        ("Faculty", ["pi"]), ("Research Staff", ["engineer"]),
        ("Phd Student", ["ada"]), ("Visiting Scholar", ["visitor"]), ("Postdoc", ["postdoc"]),
        ("Alumni", []), ("Faculty", ["emeritus"]),
    ]


def test_without_people_groups_each_role_is_titled_from_its_name(unconfigured):
    assert people_sections(unconfigured) == [
        ("Phd Student", ["ada"]), ("Professor", ["pi"]), ("Visiting Scholar", ["visitor"]),
        ("Postdoc", ["postdoc"]), ("Engineer", ["engineer"]),
        ("Alumni", []), ("Professor", ["emeritus"]),
    ]


def test_demo_people_page_groups(demo):
    built, document = demo

    def ids(status, role):
        return [p["id"] for p in document["people"] if p["status"] == status and p["role"] == role]

    assert people_sections(built) == [
        ("Principal Investigator", ids("current", "professor")),
        ("PhD Students", ids("current", "phd_student")),
        ("MS Students", ids("current", "ms_student")),
        ("Alumni", []),
        ("Postdocs", ids("alumni", "postdoc")),
        ("PhD Students", ids("alumni", "phd_student")),
        ("MS Students", ids("alumni", "ms_student")),
    ]


class Loads(HTMLParser):
    """Every URL a browser fetches to show the page: src, srcset, poster,
    <object data>, <link href> other than plain references, and CSS url()."""

    REFERENCES = {"alternate", "canonical", "author", "license", "me"}

    def __init__(self):
        super().__init__()
        self.urls = []
        self.in_style = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.in_style = tag == "style"
        for name in ("src", "poster"):
            if attrs.get(name):
                self.urls.append(attrs[name])
        for name in ("srcset", "imagesrcset"):
            self.urls += [c.split()[0] for c in (attrs.get(name) or "").split(",") if c.strip()]
        if tag == "object" and attrs.get("data"):
            self.urls.append(attrs["data"])
        if tag == "link" and attrs.get("href") and \
                not set((attrs.get("rel") or "").lower().split()) <= self.REFERENCES:
            self.urls.append(attrs["href"])
        self.css(attrs.get("style") or "")

    def handle_data(self, data):
        if self.in_style:
            self.css(data)

    def handle_endtag(self, tag):
        self.in_style = False

    def css(self, text):
        self.urls += re.findall(r"url\(\s*['\"]?([^'\")]+)", text)


def test_demo_with_theme_loads_nothing_from_another_host(tmp_path):
    """Built with the theme, no demo page fetches a resource from a host other
    than the site's own, and none names an unpinned @latest version."""
    built = build(tmp_path, *demo_data(tmp_path), theme=True)
    pages = sorted(built.rglob("*.html"))
    assert pages
    for p in pages:
        text = p.read_text(encoding="utf-8")
        assert "@latest" not in text, p
        # The heading permalink icon Font Awesome drew is now CSS.
        assert 'class="page__content' not in text or ".header-link .fa-link::before" in text, p
        parser = Loads()
        parser.feed(text)
        foreign = [u for u in parser.urls
                   if urlsplit(u).netloc not in ("", "fixture.invalid")]
        assert foreign == [], p

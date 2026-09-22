"""Build the Jekyll site from a fixture data file and check the HTML it writes.

The fixture is a hand-written sslabdata document whose strings carry HTML and
Markdown, and whose links cover each origin and verification status. The site
is copied to a temporary directory with the fixture as `_data/lab.yml` and
built with the pinned gems (`site/Gemfile.lock`). The remote theme is switched
off so the build needs no network; the checks are on page content, which the
theme's layouts do not produce.

Skipped when Bundler or the pinned Jekyll is not installed.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).parent.parent
SITE = REPO_ROOT / "site"
GEMFILE = SITE / "Gemfile"

SCRIPT_TITLE = "<script>alert(1)</script> and a tidy kitchen"
NOTE = "*emphasis* & <b>bold</b>"
PERSON_NAME = "*Ada* <i>Lovelace</i>"

DERIVED_UNCHECKED = "https://derived-unchecked.invalid/paper.pdf"
DERIVED_MISSING = "https://derived-missing.invalid/10.1/x"
DERIVED_VERIFIED = "https://derived-verified.invalid/10.1/y"
SIDECAR_UNCHECKED = "https://sidecar-unchecked.invalid/abs/1"
INPUT_UNCHECKED = "https://input-unchecked.invalid/talk"
INPUT_VERIFIED = "https://input-verified.invalid/talk"


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
            "university": "U & U", "description": "<b>desc</b>"},
    "works": [
        work("script2024", SCRIPT_TITLE, note=NOTE, links={
            "pdf": [link(DERIVED_UNCHECKED, "derived", "unchecked")],
            "doi": [link(DERIVED_MISSING, "derived", "missing"),
                    link(DERIVED_VERIFIED, "derived", "verified")],
            "arxiv": [link(SIDECAR_UNCHECKED, "sidecar", "unchecked")],
            "video": [link(INPUT_UNCHECKED, "input", "unchecked")],
        }),
        work("plain2024", "A plain title", links={
            "url": [link(INPUT_VERIFIED, "input", "verified")],
            "video": [link(INPUT_VERIFIED, "input", "verified")],
        }),
    ],
    "people": [
        {"id": "ada", "name": PERSON_NAME, "role": "phd_student",
         "status": "current", "thesis_title": "*Thesis* <b>x</b>",
         "co_advisor": "<i>Someone</i>", "start_year": 2020},
        {"id": "pi", "name": "<b>The</b> *PI*", "role": "professor",
         "status": "current"},
    ],
    "projects": [
        {"id": "demo", "title": "*Project* <b>One</b>",
         "description": "Project _description_ <script>x</script>",
         "status": "active", "work_ids": ["script2024", "plain2024"]},
    ],
    "collaborators": [{"name": "<b>Collab</b> *Orator*"}],
}


def _jekyll_available():
    if shutil.which("bundle") is None:
        return False
    env = dict(os.environ, BUNDLE_GEMFILE=str(GEMFILE))
    result = subprocess.run(["bundle", "exec", "jekyll", "--version"],
                            capture_output=True, env=env, cwd=SITE)
    return result.returncode == 0


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    if not _jekyll_available():
        pytest.skip("bundle exec jekyll is not available")
    tmp = tmp_path_factory.mktemp("site")
    source = tmp / "site"
    shutil.copytree(SITE, source, ignore=shutil.ignore_patterns(
        "_site", ".jekyll-cache", ".jekyll-metadata", ".bundle", "vendor",
        "lab.yml", "_config.generated.yml"))
    (source / "_data" / "lab.yml").write_text(
        yaml.safe_dump(FIXTURE, allow_unicode=True), encoding="utf-8")
    # Drop the remote theme, which is fetched at build time; a later config
    # file cannot unset it.
    config = source / "_config.yml"
    lines = config.read_text(encoding="utf-8").splitlines(keepends=True)
    config.write_text("".join(l for l in lines if not l.startswith("remote_theme:")),
                      encoding="utf-8")
    (source / "_config.test.yml").write_text(
        "title: Fixture\nurl: https://fixture.invalid\nbaseurl: ''\n"
        "repository: fixture/fixture\n", encoding="utf-8")
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


@pytest.mark.parametrize("url", [DERIVED_UNCHECKED, DERIVED_MISSING, SIDECAR_UNCHECKED])
def test_unverified_non_input_links_are_not_rendered(built, url):
    for p in built.rglob("*"):
        if p.is_file():
            assert url not in p.read_text(encoding="utf-8", errors="replace"), p


def test_verified_derived_link_is_rendered_without_label(built):
    html = page(built, "publications")
    assert f'<a href="{DERIVED_VERIFIED}" class="btn btn--inverse btn--small" target="_blank">DOI</a>' in html
    assert f'>DOI</a> <small' not in html


def test_unverified_input_link_is_labelled_unchecked(built):
    for path, anchor in [
        ("publications", f'<a href="{INPUT_UNCHECKED}" class="btn btn--inverse btn--small" target="_blank">Video</a>'),
        ("projects", f'<a href="{INPUT_UNCHECKED}" style="margin-right: 0.6em;">Video</a>'),
    ]:
        html = page(built, path)
        assert anchor + ' <small class="link-status link-status--unchecked"' in html, path
        assert "(unchecked)</small>" in html, path


def test_verified_input_link_has_no_label(built):
    html = page(built, "projects")
    for text in ["Website", "Video"]:
        anchor = f'<a href="{INPUT_VERIFIED}" style="margin-right: 0.6em;">{text}</a>'
        assert anchor in html
        assert anchor + " <small" not in html

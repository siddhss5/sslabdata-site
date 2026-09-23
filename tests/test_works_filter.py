"""Check the works filter on /publications/.

The demo is built once, with the stub layout test_site_build.py uses. The
static HTML is checked as a browser without JavaScript sees it: every work
listed, nothing hidden but the filter form.

The filtering itself is checked by running the shipped script,
site/assets/js/works-filter.js, under node. STUB below stands in for the
browser: it builds one fake element per `.pub-entry` and per section from the
attributes parsed out of the built page, a fake form with the fields the page
has, and `location` and `history` over a URL; then it runs the script and
prints which entries it left visible. The expected works are read from the
data file, not from the page.

Skipped when Bundler, the pinned Jekyll or node is not installed.
"""

import json
import re
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode

import pytest
import yaml

from test_site_build import build, demo_data


SCRIPT = Path(__file__).parent.parent / "site" / "assets" / "js" / "works-filter.js"

STUB = r"""
const fs = require('fs'), vm = require('vm');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const entries = input.entries.map(a => ({hidden: false, getAttribute: n => a[n] ?? null}));
const sections = input.sections.map(ids => ({hidden: false, querySelectorAll: s => {
  if (s !== '.pub-entry') throw new Error(s);
  return ids.map(i => entries[i]);
}}));
const elements = Object.fromEntries(input.fields.map(n => [n, {value: ''}]));
const listeners = {};
const form = {hidden: true, elements, addEventListener: (t, f) => { listeners[t] = f; }};
const count = {textContent: ''};
const url = new URL(input.url);
globalThis.location = url;
globalThis.history = {replaceState: (s, t, u) => { url.href = new URL(u, url).href; }};
globalThis.document = {
  getElementById: id => ({'works-filter': form, 'works-filter-count': count})[id] ?? null,
  querySelectorAll: s => {
    if (s === '.pub-entry') return entries;
    if (s === '.pub-year-section, .pub-category-section') return sections;
    throw new Error(s);
  },
};
const state = () => ({
  shown: entries.flatMap((e, i) => e.hidden ? [] : [i]),
  hiddenSections: sections.flatMap((s, i) => s.hidden ? [i] : []),
  values: Object.fromEntries(input.fields.map(n => [n, elements[n].value])),
  formHidden: form.hidden, count: count.textContent, url: url.pathname + url.search,
});
vm.runInThisContext(fs.readFileSync(process.argv[1], 'utf8'));
const out = [state()];
if (input.set) {
  Object.assign(elements, Object.fromEntries(Object.entries(input.set).map(([n, v]) => [n, {value: v}])));
  listeners.input();
  out.push(state());
}
console.log(JSON.stringify(out));
"""


class WorksPage(HTMLParser):
    """The works list as built: each entry's attributes and links, the entries
    in each year and category section, the filter form and its fields, the
    page's script tags and the elements it marks hidden."""

    def __init__(self):
        super().__init__()
        self.entries, self.sections, self.fields, self.scripts, self.hidden = [], [], [], [], []
        self.form = None
        self.open = []  # per open <div>: a section's index, "entry" or None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = (attrs.get("class") or "").split()
        if tag == "script":
            self.scripts.append(attrs)
        if "hidden" in attrs:
            self.hidden.append(tag)
        if tag == "form" and attrs.get("id") == "works-filter":
            self.form = attrs
        if tag in ("select", "input") and self.form is not None and attrs.get("name"):
            self.fields.append(attrs["name"])
        if tag == "a" and "entry" in self.open:
            self.entries[-1]["hrefs"].append(attrs.get("href"))
        if tag != "div":
            return
        if "pub-entry" in classes:
            for s in self.open:
                if isinstance(s, int):
                    self.sections[s].append(len(self.entries))
            self.entries.append({"attrs": attrs, "hrefs": []})
            self.open.append("entry")
        elif {"pub-year-section", "pub-category-section"} & set(classes):
            self.sections.append([])
            self.open.append(len(self.sections) - 1)
        else:
            self.open.append(None)

    def handle_endtag(self, tag):
        if tag == "div":
            self.open.pop()

    def bib_id(self, i):
        """The work an entry is, from its Details link."""
        ids = [m[1] for h in self.entries[i]["hrefs"] if (m := re.fullmatch(r"/publications/([^/]+)/", h or ""))]
        assert len(ids) == 1, self.entries[i]
        return ids[0]


@pytest.fixture(scope="module")
def demo(tmp_path_factory):
    """The demo's built /publications/ page, parsed, and its data file."""
    tmp = tmp_path_factory.mktemp("works")
    data, people_groups = demo_data(tmp)
    built = build(tmp, data, people_groups)
    text = (built / "publications" / "index.html").read_text(encoding="utf-8")
    page = WorksPage()
    page.feed(text)
    return page, text, yaml.safe_load(data)


def run_filter(page, query, inputs=None):
    """Run the shipped script on `page` at /publications/?`query`; if `inputs`
    is given, then fill in those form fields as a reader would. Returns the
    state after load, and after the input if there was one."""
    if shutil.which("node") is None:
        pytest.skip("node is not available")
    payload = {"url": "https://fixture.invalid/publications/" + (f"?{query}" if query else ""),
               "fields": page.fields, "entries": [e["attrs"] for e in page.entries],
               "sections": page.sections, "set": inputs}
    result = subprocess.run(["node", "-e", STUB, str(SCRIPT)], input=json.dumps(payload),
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    states = json.loads(result.stdout)
    for s in states:
        s["works"] = {page.bib_id(i) for i in s["shown"]}
        # A section is hidden exactly when none of its works is shown.
        assert s["hiddenSections"] == [i for i, ids in enumerate(page.sections)
                                       if not set(ids) & set(s["shown"])], s
        assert s["count"] == f"Showing {len(s['shown'])} of {len(page.entries)} works"
        assert s["formHidden"] is False
    return states


def matching(document, year=None, type=None, project=None, person=None):
    """The bib_ids of the works in the data file matching every given filter."""
    return {w["bib_id"] for w in document["works"]
            if (year is None or str(w["year"]) == year)
            and (type is None or w["category"] == type)
            and (project is None or project in w["project_ids"])
            and (person is None or person in [a["person_id"] for a in w["authors"]])}


def test_without_javascript_every_work_is_listed_and_shown(demo):
    page, _, document = demo
    works = [page.bib_id(i) for i in range(len(page.entries))]
    assert sorted(works) == sorted(w["bib_id"] for w in document["works"])
    # Nothing is hidden but the form, which only the script reveals.
    assert page.form is not None and page.hidden == ["form"]
    assert "display: none" not in " ".join(e["attrs"].get("style") or "" for e in page.entries)


def test_page_content_adds_only_the_local_filter_script(demo):
    # Under the stub layout, so the theme's own scripts are not on the page.
    page, _, _ = demo
    assert page.scripts == [{"src": "/assets/js/works-filter.js"}]
    source = SCRIPT.read_text(encoding="utf-8")
    assert not re.search(r"\bimport\b|require\(|https?:|fetch\(|XMLHttpRequest|\.src\b|eval\(",
                         source)


def test_no_parameters_shows_every_work(demo):
    page, _, document = demo
    [state] = run_filter(page, "")
    assert state["works"] == matching(document)
    assert state["url"] == "/publications/"


def filter_values(document):
    """Every value of each filter the data file offers."""
    works = document["works"]
    return ([("year", str(w["year"])) for w in works]
            + [("type", w["category"]) for w in works]
            + [("project", p["id"]) for p in document["projects"]]
            + [("person", p["id"]) for p in document["people"] if p["work_ids"]])


def test_each_filter_value_shows_exactly_its_works(demo):
    page, _, document = demo
    values = sorted(set(filter_values(document)))
    assert {n for n, _ in values} == {"year", "type", "project", "person"}
    for name, value in values:
        [state] = run_filter(page, urlencode({name: value}))
        expected = matching(document, **{name: value})
        assert expected and state["works"] == expected, (name, value)
        assert state["values"][name] == value


@pytest.mark.parametrize("filters", [
    {"person": "aadams", "type": "Conference Papers"},
    {"year": "2021", "project": "legged", "person": "hhughes"},
    {"year": "2025", "type": "Journal Papers", "project": "homebot", "person": "ccote"},
    {"year": "2019", "person": "jjones"},
])
def test_filters_combine(demo, filters):
    page, _, document = demo
    [state] = run_filter(page, urlencode(filters))
    assert state["works"] == matching(document, **filters)


def test_unknown_value_matches_nothing(demo):
    page, _, _ = demo
    [state] = run_filter(page, "person=nobody")
    assert state["works"] == set()
    assert state["count"] == f"Showing 0 of {len(page.entries)} works"


def test_text_search_is_a_filter_too(demo):
    page, _, document = demo
    [state] = run_filter(page, urlencode({"q": "  TIDY "}))
    assert state["works"] == {w["bib_id"] for w in document["works"] if "tidy" in w["title"].lower()}
    assert state["works"]


def test_changing_the_form_writes_the_state_to_the_url(demo):
    page, _, document = demo
    before, after = run_filter(page, "year=2025&person=bbrown",
                               inputs={"year": "2021", "type": "Journal Papers", "person": ""})
    assert before["works"] == matching(document, year="2025", person="bbrown")
    assert after["url"] == "/publications/?" + urlencode({"year": "2021", "type": "Journal Papers"})
    assert after["works"] == matching(document, year="2021", type="Journal Papers")
    # The written URL, loaded afresh, shows the same works.
    [reloaded] = run_filter(page, after["url"].split("?", 1)[1])
    assert reloaded["works"] == after["works"]

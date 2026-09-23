"""The co-author graph page: its table and its SVG carry the co-authorship
edges of the data file, and nothing from the data file is read as markup.

The built-site checks reuse the fixture build in test_site_build.py and are
skipped with it when Bundler or the pinned Jekyll is not installed.
"""

import copy
import html
import re
import subprocess
import sys
from pathlib import Path

import yaml

from test_site_build import COLLAB, FIXTURE, REPO_ROOT, build, demo, page  # noqa: F401


def expected_edges(document):
    """(person id, co-author key) -> number of distinct works they share,
    computed from the works' authors."""
    shared = {}
    for w in document["works"]:
        for a in w["authors"]:
            for b in w["authors"]:
                if a.get("person_id") and b.get("collaborator_key"):
                    shared.setdefault((a["person_id"], b["collaborator_key"]), set()).add(w["bib_id"])
    return {edge: len(works) for edge, works in shared.items()}


def table_edges(text):
    body = re.search(r"<tbody>(.*?)</tbody>", text, re.DOTALL)[1]
    rows = re.findall(r'<tr><td><a href="/people/([^"]*)/">.*?</a></td>'
                      r'<td><a href="/coauthors/([^"]*)/">.*?</a></td><td>(\d+)</td></tr>', body)
    assert len(rows) == body.count("<tr>")
    return {(p, c): int(n) for p, c, n in rows}


def svg(text):
    return re.search(r"<svg .*?</svg>", text, re.DOTALL)[0]


def test_demo_table_edges_equal_the_authorship_edges(demo):
    built, document = demo
    expected = expected_edges(document)
    assert expected
    assert table_edges(page(built, "coauthor-graph")) == expected


def test_demo_graph_draws_each_edge_and_links_each_node(demo):
    built, document = demo
    text = page(built, "coauthor-graph")
    graph = svg(text)
    edges = expected_edges(document)
    assert graph.count("<line ") == len(edges)
    people = re.findall(r'<a href="/people/([^"]*)/"><circle ', graph)
    coauthors = re.findall(r'<a href="/coauthors/([^"]*)/"><rect ', graph)
    assert sorted(people) == sorted({p for p, _ in edges})
    assert sorted(coauthors) == sorted({c for _, c in edges})
    for p in people:
        assert (built / "people" / p / "index.html").is_file(), p
    for c in coauthors:
        assert (built / "coauthors" / c / "index.html").is_file(), c


def test_demo_graph_needs_no_script_and_has_a_text_alternative(demo):
    built, _ = demo
    text = page(built, "coauthor-graph")
    assert "<script" not in text
    graph = svg(text)
    assert 'aria-labelledby="coauthor-graph-title"' in graph
    assert '<title id="coauthor-graph-title">' in graph
    assert '<desc id="coauthor-graph-desc">' in graph and "The table below lists the same pairs." in graph
    assert "groups author names by their spelling" in text and "not a verified person" in text


def test_graph_and_table_show_names_as_text(tmp_path):
    fixture = copy.deepcopy(FIXTURE)
    name = "<b>Co</b> *author* {{ site.title }}"
    next(c for c in fixture["collaborators"] if c["key"] == COLLAB)["name"] = name
    text = page(build(tmp_path, yaml.safe_dump(fixture, allow_unicode=True)), "coauthor-graph")
    edges = expected_edges(fixture)
    assert table_edges(text) == edges
    escaped = html.escape(name, quote=False)
    assert svg(text).count(escaped) == 1
    assert text.count(escaped) == 1 + sum(1 for _, c in edges if c == COLLAB)
    assert "<b>" not in text and "<i>" not in text


def test_layout_does_not_depend_on_input_order(tmp_path):
    data = tmp_path / "lab.yml"
    subprocess.run([str(Path(sys.executable).parent / "sslabdata"), "--config", "demo/lab.yaml",
                    "--output", str(data)], check=True, capture_output=True, cwd=REPO_ROOT)
    document = yaml.safe_load(data.read_text(encoding="utf-8"))
    for key in ("works", "people", "collaborators"):
        document[key].reverse()
    for w in document["works"]:
        w["authors"].reverse()
    reversed_data = tmp_path / "reversed.yml"
    reversed_data.write_text(yaml.safe_dump(document, allow_unicode=True), encoding="utf-8")
    pages = []
    for source in (data, data, reversed_data):
        out = tmp_path / f"out{len(pages)}"
        subprocess.run([sys.executable, "scripts/generate_pages.py", source, out], check=True, cwd=REPO_ROOT)
        pages.append((out / "coauthor-graph.html").read_text(encoding="utf-8"))
    assert pages[0] == pages[1] == pages[2]

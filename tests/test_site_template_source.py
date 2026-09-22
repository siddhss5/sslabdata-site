"""Source-level checks on the Jekyll templates in site/.

These read the template text. They do not render Liquid and do not build the
site, so what they establish is that the templates ask for the star and for the
note, and that both are driven by the `equal_contribution` field rather than
being hard-coded — not that a built page shows them. Verifying rendered output
(HTML snapshots, internal links, accessibility) is siddhss5/sslabdata#36.

sslabdata's product is the data file; this repository is an example renderer
that consumes it, which is why these checks stay at the source level and pull
in nothing to render with.
"""

import re
from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent
AUTHOR_LIST = REPO_ROOT / "site" / "_includes" / "author_list.html"
PROJECTS = REPO_ROOT / "site" / "_pages" / "projects.md"

STAR = "{% if author.equal_contribution %}<sup>*</sup>{% endif %}"
MARKED = '| where: "equal_contribution", true'
NOTE = "equal contribution"


def test_author_list_source_stars_marked_authors():
    """The include stars an author whose `equal_contribution` is true."""
    source = AUTHOR_LIST.read_text(encoding="utf-8")
    assert STAR in source, source
    assert source.index("{{ author.name | escape }}") < source.index(STAR), source


def test_author_list_source_notes_equal_contribution():
    """The note is written once per list, and only when somebody is marked."""
    source = AUTHOR_LIST.read_text(encoding="utf-8")
    assert MARKED in source, source
    assert "{% if equal_authors.size > 0 %}" in source, source
    assert source.count(NOTE) == 1, source


def test_projects_page_source_stars_and_notes_marked_authors():
    """The projects page repeats both in its own author loop."""
    source = PROJECTS.read_text(encoding="utf-8")
    assert STAR in source, source
    assert MARKED in source, source
    assert "{% if equal_authors.size > 0 %}" in source, source
    assert source.count(NOTE) == 1, source


# Every `{{ ... }}` in the templates is escaped, unless its expression is one
# of these. None of them is a string from the data file: no data field is
# allowed to carry markup.
UNESCAPED_ALLOWLIST = {
    # HTML captured from work_link.html, which escapes the URL and the text.
    "title_link", "web_link", "video_link",
    # Values the templates assign from literals.
    "sep", "status",
    # Counts.
    "pubs.size", "current.size", "alumni.size", "projects.size",
    "project.work_ids.size", "collaborators.size",
    # Literal site paths.
    "'/people/' | relative_url", "'/projects/' | relative_url",
    "'/publications/' | relative_url",
    # A literal space.
    '" "',
}
ESCAPED = re.compile(r"\|\s*(escape|xml_escape)\s*$")


def test_every_output_is_escaped_or_allowlisted():
    templates = sorted((REPO_ROOT / "site" / "_includes").glob("*.html"))
    templates += sorted((REPO_ROOT / "site" / "_pages").glob("*.md"))
    for path in templates:
        for expr in re.findall(r"\{\{-?\s*(.*?)\s*-?\}\}", path.read_text(encoding="utf-8")):
            assert ESCAPED.search(expr) or expr in UNESCAPED_ALLOWLIST, f"{path.name}: {{{{ {expr} }}}}"

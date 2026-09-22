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

import pytest


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


# Every `{{ ... }}` in the templates is escaped, unless the template names it
# in an allowlist comment with a reason:
#
#   {%- comment -%}
#   Unescaped outputs. Every output not listed here is escaped.
#   - `title_link`: HTML captured from work_link.html, which escapes ...
#   {%- endcomment -%}
#
# The templates are the source of truth; this test only holds them to it.
TEMPLATES = sorted((REPO_ROOT / "site" / "_includes").glob("*.html")) + \
    sorted((REPO_ROOT / "site" / "_pages").glob("*.md"))
COMMENT = re.compile(r"\{%-?\s*comment\s*-?%\}(.*?)\{%-?\s*endcomment\s*-?%\}", re.DOTALL)
OUTPUT = re.compile(r"\{\{-?\s*(.*?)\s*-?\}\}", re.DOTALL)
ALLOWLIST_ENTRY = re.compile(r"^- `(.+?)`: (\S.*)$", re.MULTILINE)
ESCAPED = re.compile(r"\|\s*(escape|xml_escape)\s*$")


def allowlist(source):
    """Expressions the template's allowlist comments name, each with a reason."""
    entries = {}
    for body in COMMENT.findall(source):
        if "Unescaped outputs." in body:
            entries.update(ALLOWLIST_ENTRY.findall(body))
    return entries


def unescaped_outputs(source):
    """Every unescaped output expression outside comments, whitespace-normalised."""
    code = COMMENT.sub("", source)
    exprs = (" ".join(e.split()) for e in OUTPUT.findall(code))
    return {e for e in exprs if not ESCAPED.search(e)}


@pytest.mark.parametrize("path", TEMPLATES, ids=lambda p: p.name)
def test_every_unescaped_output_is_allowlisted_in_the_template(path):
    source = path.read_text(encoding="utf-8")
    listed = allowlist(source)
    unescaped = unescaped_outputs(source)
    assert unescaped <= listed.keys(), f"not escaped and not allowlisted: {unescaped - listed.keys()}"
    assert listed.keys() <= unescaped, f"allowlisted but not output: {listed.keys() - unescaped}"


def test_unescaped_output_check_sees_multiline_outputs():
    source = "{{\n  work.title\n}} {{ work.note\n  | escape }}"
    assert unescaped_outputs(source) == {"work.title"}


def test_allowlist_is_read_from_comments_only():
    source = "- `work.title`: not in a comment\n{{ work.title }}"
    assert allowlist(source) == {}

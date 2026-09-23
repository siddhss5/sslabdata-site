"""Checks on scripts/generate_pages.py that need no Jekyll: the document it
refuses, and that a refused document leaves everything as it was."""

import subprocess
import sys

import pytest
import yaml
from sslabdata.models import SCHEMA_VERSION

from test_site_build import ADA, COLLAB, FIXTURE, PROJECT, REPO_ROOT, SCRIPT

ENTITIES = {"work": ("works", "bib_id", SCRIPT), "person": ("people", "id", ADA),
            "project": ("projects", "id", PROJECT), "co-author": ("collaborators", "key", COLLAB)}


def generate(tmp_path, document):
    """Run the generator on `document` into an output directory that already
    holds a page; return the result and that directory."""
    data = tmp_path / "lab.yml"
    data.write_text(yaml.safe_dump(document, allow_unicode=True), encoding="utf-8")
    out = tmp_path / "site" / "_entities"
    (out / "people").mkdir(parents=True)
    (out / "people" / "old.html").write_text("old", encoding="utf-8")
    result = subprocess.run([sys.executable, "scripts/generate_pages.py", data, out],
                            capture_output=True, text=True, cwd=REPO_ROOT)
    return result, out


def assert_nothing_written(tmp_path, out):
    assert sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*")) == \
        ["lab.yml", "site", "site/_entities", "site/_entities/people", "site/_entities/people/old.html"]


@pytest.mark.parametrize("id_", ["../../escaped", "a/b", "two words", "Zoë", ".hidden", "_x", "-x", ""])
@pytest.mark.parametrize("kind", ENTITIES)
def test_an_id_that_is_not_one_path_segment_is_refused(kind, id_, tmp_path):
    collection, key, old = ENTITIES[kind]
    document = yaml.safe_load(yaml.safe_dump(FIXTURE))
    next(e for e in document[collection] if e[key] == old)[key] = id_
    result, out = generate(tmp_path, document)
    assert result.returncode == 1
    assert f"{kind} id {id_!r} is not one path segment" in result.stderr
    assert_nothing_written(tmp_path, out)


@pytest.mark.parametrize("version", [SCHEMA_VERSION - 1, SCHEMA_VERSION + 1, None])
def test_an_unsupported_schema_version_is_refused(version, tmp_path):
    result, out = generate(tmp_path, {**FIXTURE, "schema_version": version})
    assert result.returncode == 1
    assert f"schema_version {version!r} is not supported" in result.stderr
    assert f"reads schema_version {SCHEMA_VERSION}" in result.stderr
    assert_nothing_written(tmp_path, out)

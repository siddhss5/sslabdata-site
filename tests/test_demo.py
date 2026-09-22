"""Checks on what the pinned sslabdata makes of the demo lab."""

import subprocess
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).parent.parent
SSLABDATA = Path(sys.executable).parent / "sslabdata"


def run(*args):
    result = subprocess.run([str(SSLABDATA), "--config", "demo/lab.yaml", *args],
                            capture_output=True, text=True, cwd=REPO_ROOT)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout + result.stderr


def test_p_patel_is_not_ambiguous():
    """demo/collaborators.yaml declares P. Patel as a spelling of Priya Patel."""
    output = run("--unresolved")
    assert "ID-GROUPING-INITIALS-AMBIGUOUS" not in output, output
    assert not [line for line in output.splitlines()
                if "Patel" in line and "ambiguous" in line.lower()], output


def test_priya_patel_is_one_collaborator(tmp_path):
    out = tmp_path / "lab.yml"
    run("--output", str(out))
    collaborators = yaml.safe_load(out.read_text(encoding="utf-8"))["collaborators"]
    priya = [c for c in collaborators if "P. Patel" in c["name_variants"]]
    assert len(priya) == 1
    assert priya[0]["name"] == "Priya Patel"
    assert priya[0]["name_variants"] == ["P. Patel", "Priya Patel"]

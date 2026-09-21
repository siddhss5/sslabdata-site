# labdata-site

A demo Jekyll renderer for the document that
[labdata](https://github.com/siddhss5/labdata) emits.

labdata compiles BibTeX and a little YAML into one schema-specified document.
This repository is one **optional downstream consumer** of that document: a
set of Jekyll templates (Minimal Mistakes theme) that render it as
publications, people and projects pages. It is not part of labdata and not
part of what labdata promises; labdata does not depend on it.

It renders the fictional **Example Lab** in [`demo/`](demo/), deployed at
<https://siddhss5.github.io/labdata-site/>.

It is a worked example, not a polished template for other labs to adopt
(that is [labdata#37](https://github.com/siddhss5/labdata/issues/37)), and it
is not the owner's real lab site.

## Layout

| Path | What it is |
|------|------------|
| [`site/`](site/) | The Jekyll site: `_config.yml`, `_pages/`, `_includes/`, `_data/navigation.yml`, and the `Gemfile` / `Gemfile.lock` that pin Jekyll |
| [`demo/`](demo/) | Example Lab's `lab.yaml`, `people.yaml`, `projects.yaml` and `bib/` |
| [`scripts/generate_site_config.py`](scripts/generate_site_config.py) | Writes the Jekyll settings that come from `lab.yaml` to `site/_config.generated.yml` |
| [`tests/`](tests/) | Tests for `generate_site_config.py` |
| [`.github/workflows/`](.github/workflows/) | `build.yml` (the build), `pages.yml` (build on PRs, deploy from `main`), `release-gate.yml` (build against a candidate labdata) |

`scripts/generate_site_config.py` reads the optional `site:` section of
`lab.yaml` (`url` and `baseurl`) and writes it, with the lab name and
description, into `site/_config.generated.yml`. labdata itself ignores that
section.

## The labdata pin

labdata has no package release, so this repository installs it from an
immutable git tag. The pin lives in one place, the dependency in
[`pyproject.toml`](pyproject.toml):

```toml
"labdata @ git+https://github.com/siddhss5/labdata@schema-v4",
```

`schema-v4` is commit `c5adb3e`; `uv.lock` records the resolved commit. To
bump the pin, change the ref in `pyproject.toml` to the new tag, then run
`uv lock` and commit both files. Run the release gate (below) against the new
ref first.

## Build locally

You need [uv](https://docs.astral.sh/uv/) and Ruby with Bundler. Run from the
repository root, where `demo/lab.yaml`'s relative paths point:

```bash
uv sync --frozen
uv run --frozen pytest
uv run --frozen labdata --config demo/lab.yaml --validate
uv run --frozen labdata --config demo/lab.yaml --output site/_data/lab.yml
uv run --frozen python scripts/generate_site_config.py demo/lab.yaml site/_config.generated.yml
cd site
bundle install
bundle exec jekyll serve --config _config.yml,_config.generated.yml
```

The site is served under `/labdata-site/`, the demo's `baseurl`.

## Deployment

[`pages.yml`](.github/workflows/pages.yml) builds the demo on every pull
request and on push to `main`, and deploys it to GitHub Pages on push to
`main` or when run by hand. Pull requests build but never deploy.

## Release gate

[`release-gate.yml`](.github/workflows/release-gate.yml) builds this site
against a candidate labdata git ref — a tag, branch or commit — before that
ref is tagged or pinned here. It runs the same build as `pages.yml` (tests,
`--validate`, data and config generation, Jekyll build) and never deploys.
Leaving the ref empty builds against the pin.

From the Actions tab, choose **Release gate**, then **Run workflow**, and
enter the ref. Or with the GitHub CLI:

```bash
gh workflow run release-gate.yml -R siddhss5/labdata-site -f labdata_ref=<ref>
gh run watch -R siddhss5/labdata-site
```

The log's "Show labdata version" step prints the commit that was built.

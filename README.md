# sslabdata-site

A demo Jekyll renderer for the document that
[sslabdata](https://github.com/siddhss5/sslabdata) emits.

sslabdata compiles BibTeX and a little YAML into one schema-specified document.
This repository is one **optional downstream consumer** of that document: a
set of Jekyll templates (Minimal Mistakes theme) that render it as
works, people and projects pages. It is not part of sslabdata and not
part of what sslabdata promises; sslabdata does not depend on it.

It renders the fictional **Example Lab** in [`demo/`](demo/), deployed at
<https://siddhss5.github.io/sslabdata-site/>.

It is a worked example, not a polished template for other labs to adopt
(that is [sslabdata#37](https://github.com/siddhss5/sslabdata/issues/37)), and it
is not the owner's real lab site.

## Layout

| Path | What it is |
|------|------------|
| [`site/`](site/) | The Jekyll site: `_config.yml`, `_pages/`, `_includes/`, `_data/navigation.yml`, and the `Gemfile` / `Gemfile.lock` that pin Jekyll |
| [`demo/`](demo/) | Example Lab's `lab.yaml`, `people.yaml`, `projects.yaml`, `collaborators.yaml` and `bib/` |
| [`scripts/generate_site_config.py`](scripts/generate_site_config.py) | Writes the Jekyll settings that come from `lab.yaml` to `site/_config.generated.yml` |
| [`tests/`](tests/) | Tests for `generate_site_config.py`, source-level checks on the templates, and checks on the HTML Jekyll builds from a fixture data file |
| [`.github/workflows/`](.github/workflows/) | `build.yml` (the build), `pages.yml` (build on PRs, deploy from `main`), `release-gate.yml` (build against a candidate sslabdata) |

`scripts/generate_site_config.py` reads the optional `site:` section of
`lab.yaml` (`url` and `baseurl`) and writes it, with the lab name and
description, into `site/_config.generated.yml`. sslabdata itself ignores that
section.

## Rendering rules

- **Every string is text.** Every string taken from the data file is escaped
  where it is printed, `note` included; none is read as HTML or Markdown.
  A template that prints anything unescaped names it, with the reason, in an
  "Unescaped outputs." comment; only values the templates make themselves
  (counts, literal paths, HTML built by `work_link.html`, URLs from
  `safe_url.html`) are listed, never a data field.
  `tests/test_site_template_source.py` fails on any output that is neither
  escaped nor listed.
- **Only http, https and mailto links.** A URL from the data file becomes a
  link only through [`site/_includes/safe_url.html`](site/_includes/safe_url.html),
  which drops any other scheme and any relative path.
- **Links that are not guesses.** A work's link is shown when it is written in
  the input (`origin: input`), when its `verification.status` is `verified`,
  or when sslabdata built it from an identifier the entry declares: the
  `derived` links of kind `doi` (from `doi`) and `arxiv` (from `eprint`),
  which are shown unlabelled. Any other `derived` link, such as the PDF link
  guessed from `pdf_base_url` and the citation key, is not shown until it is
  verified; nor is a link of another origin (`sidecar`, `enrichment`,
  `inferred` or one added later). An input link that is not verified is shown
  labelled "(unchecked)", whatever its status. See
  [`site/_includes/work_link.html`](site/_includes/work_link.html), which
  names the identifier kinds in an explicit list.

## The sslabdata pin

sslabdata has no package release, so this repository installs it from an
immutable git tag or commit. The pin is authored in one place: the `sslabdata`
dependency in [`pyproject.toml`](pyproject.toml). `uv.lock` is its generated
resolution, recording the exact commit; do not edit it by hand.

To bump the pin, run the release gate (below) against the new sslabdata tag,
then change the tag in the `sslabdata` dependency in `pyproject.toml`, run
`uv lock`, and commit both files. The build uses `uv sync --locked`, so a pin
changed without regenerating `uv.lock` fails rather than building the old
commit.

## Build locally

You need [uv](https://docs.astral.sh/uv/) and Ruby with Bundler. Run from the
repository root, where `demo/lab.yaml`'s relative paths point:

```bash
uv sync --locked
uv run --frozen pytest
uv run --frozen sslabdata --config demo/lab.yaml --validate
uv run --frozen sslabdata --config demo/lab.yaml --output site/_data/lab.yml
uv run --frozen python scripts/generate_site_config.py demo/lab.yaml site/_config.generated.yml
cd site
bundle install
bundle exec jekyll serve --config _config.yml,_config.generated.yml
```

The site is served under `/sslabdata-site/`, the demo's `baseurl`.

## Deployment

[`pages.yml`](.github/workflows/pages.yml) builds the demo on every pull
request and on push to `main`, and deploys it to GitHub Pages on push to
`main` or when run by hand. Pull requests build but never deploy.

## Release gate

[`release-gate.yml`](.github/workflows/release-gate.yml) builds this site
against a candidate sslabdata git ref — a tag, branch or commit — before that
ref is tagged or pinned here. It runs the same build as `pages.yml` (tests,
`--validate`, data and config generation, Jekyll build) and never deploys.
Leaving the ref empty builds against the pin.

From the Actions tab, choose **Release gate**, then **Run workflow**, and
enter the ref. Or with the GitHub CLI:

```bash
gh workflow run release-gate.yml -R siddhss5/sslabdata-site -f sslabdata_ref=<ref>
gh run watch -R siddhss5/sslabdata-site
```

The log's "Show sslabdata version" step prints the commit that was built.

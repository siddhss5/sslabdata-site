"""Write one Jekyll page per work, person, project and co-author.

Reads the document sslabdata emits and writes a page for each entity into the
output directory, replacing what was there. A page's front matter holds the
entity and the entities it links to; every relationship is read from the
document, and this only joins them. The templates in site/_includes/*_page.html
lay the pages out.

Usage: generate_pages.py site/_data/lab.yml site/_entities
"""

import shutil
import sys
from pathlib import Path

import yaml


# Literal titles, not data strings: the theme reads a page title as Markdown.
TITLES = {"work": "Work", "person": "Person", "project": "Project", "coauthor": "Co-author"}


def main(data_file, out_dir):
    doc = yaml.safe_load(Path(data_file).read_text(encoding="utf-8"))
    works = {w["bib_id"]: w for w in doc.get("works") or []}
    people = doc.get("people") or []
    projects = doc.get("projects") or []
    coauthors = doc.get("collaborators") or []

    def works_of(entity):
        return [works[i] for i in entity.get("work_ids") or []]

    def authors(ws, field):
        return {a[field] for w in ws for a in w.get("authors") or [] if a.get(field)}

    def names(entities, key, ids):
        return [{key: e[key], "name": e.get("name") or e.get("title")} for e in entities if e[key] in ids]

    pages = [("publications", w["bib_id"], "work", {"work": w}) for w in works.values()]
    for p in people:
        in_projects = [x["id"] for x in projects if p["id"] in (x.get("people_ids") or [])]
        pages.append(("people", p["id"], "person", {
            "person": p, "works": works_of(p),
            "projects": names(projects, "id", in_projects),
            "coauthors": names(coauthors, "key", authors(works_of(p), "collaborator_key"))}))
    for x in projects:
        pages.append(("projects", x["id"], "project", {
            "project": x, "works": works_of(x),
            "people": names(people, "id", x.get("people_ids") or [])}))
    for c in coauthors:
        pages.append(("coauthors", c["key"], "coauthor", {
            "coauthor": c, "works": works_of(c),
            "people": names(people, "id", authors(works_of(c), "person_id"))}))

    out = Path(out_dir)
    shutil.rmtree(out, ignore_errors=True)
    for section, id_, kind, data in pages:
        path = out / section / f"{id_}.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        front = {"title": TITLES[kind], "permalink": f"/{section}/{id_}/", **data}
        path.write_text("---\n" + yaml.safe_dump(front, allow_unicode=True, sort_keys=False)
                        + f"---\n{{% include {kind}_page.html %}}\n", encoding="utf-8")


if __name__ == "__main__":
    main(*sys.argv[1:])

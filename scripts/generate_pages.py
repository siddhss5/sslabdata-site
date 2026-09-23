"""Write one Jekyll page per work, person, project and co-author, and the
co-author graph.

Reads the document sslabdata emits and writes a page for each entity into the
output directory, replacing what was there. A page's front matter holds the
entity and the entities it links to; every relationship is read from the
document, and this only joins them. The templates in site/_includes/*_page.html
lay the pages out.

Usage: generate_pages.py site/_data/lab.yml site/_entities
"""

import math
import shutil
import sys
from pathlib import Path

import yaml


def literal(s):
    """`s` as a page title: the theme reads a title as Markdown and does not
    escape it, so every character but letters, digits and spaces is written as
    an HTML character reference, which Markdown and HTML both show as text."""
    return "".join(c if c.isalnum() or c == " " else f"&#{ord(c)};" for c in s)


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

    pages = [("publications", w["bib_id"], "work", w["title"], {"work": w}) for w in works.values()]
    for p in people:
        in_projects = [x["id"] for x in projects if p["id"] in (x.get("people_ids") or [])]
        pages.append(("people", p["id"], "person", p["name"], {
            "person": p, "works": works_of(p),
            "projects": names(projects, "id", in_projects),
            "coauthors": names(coauthors, "key", authors(works_of(p), "collaborator_key"))}))
    for x in projects:
        pages.append(("projects", x["id"], "project", x["title"], {
            "project": x, "works": works_of(x),
            "people": names(people, "id", x.get("people_ids") or [])}))
    for c in coauthors:
        pages.append(("coauthors", c["key"], "coauthor", c["name"], {
            "coauthor": c, "works": works_of(c),
            "also_written_as": [v for v in c.get("name_variants") or [] if v != c["name"]],
            "people": names(people, "id", authors(works_of(c), "person_id"))}))

    # Co-author graph: an edge joins a lab member and a co-author who share a
    # work. Nodes sit on a circle in a fixed order, lab members by id and then
    # co-authors by key, so the layout is the same on every build.
    shared = {}
    for w in works.values():
        for a in w.get("authors") or []:
            for b in w.get("authors") or []:
                if a.get("person_id") and b.get("collaborator_key"):
                    shared.setdefault((a["person_id"], b["collaborator_key"]), set()).add(w["bib_id"])
    order = sorted({("person", p) for p, _ in shared} | {("coauthor", c) for _, c in shared})
    name = {**{("person", p["id"]): p["name"] for p in people},
            **{("coauthor", c["key"]): c["name"] for c in coauthors}}
    at = {n: (round(200 * math.sin(2 * math.pi * i / len(order)), 1),
              round(-200 * math.cos(2 * math.pi * i / len(order)), 1)) for i, n in enumerate(order)}
    graph = {"nodes": [{"kind": k, "id": i, "name": name[k, i], "x": at[k, i][0], "y": at[k, i][1],
                        "anchor": "start" if at[k, i][0] >= 0 else "end"} for k, i in order],
             "edges": [{"person": p, "person_name": name["person", p], "coauthor": c,
                        "coauthor_name": name["coauthor", c], "works": len(shared[p, c]),
                        "x1": at["person", p][0], "y1": at["person", p][1],
                        "x2": at["coauthor", c][0], "y2": at["coauthor", c][1]}
                       for p, c in sorted(shared)]}

    out = Path(out_dir)
    shutil.rmtree(out, ignore_errors=True)
    for section, id_, kind, title, data in pages:
        path = out / section / f"{id_}.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        front = {"title": literal(title), "permalink": f"/{section}/{id_}/", **data}
        path.write_text("---\n" + yaml.safe_dump(front, allow_unicode=True, sort_keys=False)
                        + f"---\n{{% include {kind}_page.html %}}\n", encoding="utf-8")
    front = {"title": "Co-author graph", "permalink": "/coauthor-graph/", **graph}
    (out / "coauthor-graph.html").write_text(
        "---\n" + yaml.safe_dump(front, allow_unicode=True, sort_keys=False)
        + "---\n{% include coauthor_graph.html %}\n", encoding="utf-8")


if __name__ == "__main__":
    main(*sys.argv[1:])

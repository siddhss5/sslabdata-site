---
title: "Co-authors"
permalink: /coauthors/
layout: single
classes: wide
---

{%- comment -%}
Unescaped outputs. Every output not listed here is escaped.
- `'/coauthor-graph/' | relative_url`: the site path is a literal in this template; relative_url only prefixes the baseurl from _config.yml.
- `'/coauthors/' | relative_url`: the site path is a literal in this template; relative_url only prefixes the baseurl from _config.yml.
{%- endcomment -%}

<p>Each entry groups author names by their spelling. It is not a verified person: two people who write their name the same way share one entry.</p>

<p><a href="{{ '/coauthor-graph/' | relative_url }}">Co-author graph</a>: which lab members each co-author shares works with.</p>

<ul>{% for c in site.data.lab.collaborators %}<li><a href="{{ '/coauthors/' | relative_url }}{{ c.key | escape }}/">{{ c.name | escape }}</a></li>{% endfor %}</ul>

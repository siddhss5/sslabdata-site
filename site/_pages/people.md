---
title: "People"
permalink: /people/
layout: single
classes: wide
---

{%- comment -%}
Unescaped outputs. Every output not listed here is escaped.
- `collaborators.size`: a count Liquid computes, not a string from the data file.
{%- endcomment -%}

{% assign people = site.data.lab.people %}
{% assign collaborators = site.data.lab.collaborators %}

{% assign pi = people | where: "role", "professor" | first %}
{% assign current_phd = people | where: "status", "current" | where: "role", "phd_student" %}
{% assign current_ms = people | where: "status", "current" | where: "role", "ms_student" %}

{% assign alumni_postdoc = people | where: "status", "alumni" | where: "role", "postdoc" %}
{% assign alumni_phd = people | where: "status", "alumni" | where: "role", "phd_student" %}
{% assign alumni_ms = people | where: "status", "alumni" | where: "role", "ms_student" %}

{% if people.size > 0 %}

{% if pi %}
## Principal Investigator

<p><span id="{{ pi.id | escape }}">{% if pi.website %}<a href="{{ pi.website | escape }}">{{ pi.name | escape }}</a>{% else %}{{ pi.name | escape }}{% endif %}</span></p>
{% endif %}

{% if current_phd.size > 0 %}
## PhD Students

<table>
<thead><tr><th>Name</th><th>Co-advisor</th><th>Thesis</th><th>Started</th></tr></thead>
<tbody>
{% for p in current_phd %}<tr><td><span id="{{ p.id | escape }}">{% if p.website %}<a href="{{ p.website | escape }}">{{ p.name | escape }}</a>{% else %}{{ p.name | escape }}{% endif %}</span></td><td>{{ p.co_advisor | escape }}</td><td>{{ p.thesis_title | escape }}</td><td>{{ p.start_year | escape }}</td></tr>
{% endfor %}</tbody>
</table>
{% endif %}

{% if current_ms.size > 0 %}
## MS Students

<table>
<thead><tr><th>Name</th><th>Co-advisor</th><th>Thesis</th><th>Started</th></tr></thead>
<tbody>
{% for p in current_ms %}<tr><td><span id="{{ p.id | escape }}">{% if p.website %}<a href="{{ p.website | escape }}">{{ p.name | escape }}</a>{% else %}{{ p.name | escape }}{% endif %}</span></td><td>{{ p.co_advisor | escape }}</td><td>{{ p.thesis_title | escape }}</td><td>{{ p.start_year | escape }}</td></tr>
{% endfor %}</tbody>
</table>
{% endif %}

{% if alumni_postdoc.size > 0 or alumni_phd.size > 0 or alumni_ms.size > 0 %}
## Alumni

{% if alumni_postdoc.size > 0 %}
### Postdocs

<table>
<thead><tr><th>Name</th><th>Period</th><th>Current Position</th></tr></thead>
<tbody>
{% for p in alumni_postdoc %}<tr><td><span id="{{ p.id | escape }}">{% if p.website %}<a href="{{ p.website | escape }}">{{ p.name | escape }}</a>{% else %}{{ p.name | escape }}{% endif %}</span></td><td>{{ p.start_year | escape }}–{{ p.end_year | escape }}</td><td>{{ p.current_position | escape }}</td></tr>
{% endfor %}</tbody>
</table>
{% endif %}

{% if alumni_phd.size > 0 %}
### PhD Students

<table>
<thead><tr><th>Name</th><th>Co-advisor</th><th>Thesis</th><th>Period</th><th>Current Position</th></tr></thead>
<tbody>
{% for p in alumni_phd %}<tr><td><span id="{{ p.id | escape }}">{% if p.website %}<a href="{{ p.website | escape }}">{{ p.name | escape }}</a>{% else %}{{ p.name | escape }}{% endif %}</span></td><td>{{ p.co_advisor | escape }}</td><td>{{ p.thesis_title | escape }}</td><td>{{ p.start_year | escape }}–{{ p.end_year | escape }}</td><td>{{ p.current_position | escape }}</td></tr>
{% endfor %}</tbody>
</table>
{% endif %}

{% if alumni_ms.size > 0 %}
### MS Students

<table>
<thead><tr><th>Name</th><th>Co-advisor</th><th>Thesis</th><th>Period</th><th>Current Position</th></tr></thead>
<tbody>
{% for p in alumni_ms %}<tr><td><span id="{{ p.id | escape }}">{% if p.website %}<a href="{{ p.website | escape }}">{{ p.name | escape }}</a>{% else %}{{ p.name | escape }}{% endif %}</span></td><td>{{ p.co_advisor | escape }}</td><td>{{ p.thesis_title | escape }}</td><td>{{ p.start_year | escape }}–{{ p.end_year | escape }}</td><td>{{ p.current_position | escape }}</td></tr>
{% endfor %}</tbody>
</table>
{% endif %}

{% endif %}

{% endif %}

{% if collaborators.size > 0 %}
## Collaborators

<details>
<summary style="cursor: pointer; font-size: 1.17em; font-weight: bold; margin-bottom: 0.5em;">{{ collaborators.size }} co-authors</summary>
<div style="margin-top: 0.8em; display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.3em 2em;">
{% for c in collaborators %}<div style="font-size: 0.9em;">{{ c.name | escape }}</div>
{% endfor %}
</div>
</details>
{% endif %}

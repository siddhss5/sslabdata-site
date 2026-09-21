---
title: "People"
permalink: /people/
layout: single
classes: wide
---

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

<span id="{{ pi.id }}">{% if pi.website %}[{{ pi.name }}]({{ pi.website }}){% else %}{{ pi.name }}{% endif %}</span>
{% endif %}

{% if current_phd.size > 0 %}
## PhD Students

| Name | Co-advisor | Thesis | Started |
|------|------------|--------|---------|
{% for p in current_phd %}| <span id="{{ p.id }}">{% if p.website %}[{{ p.name }}]({{ p.website }}){% else %}{{ p.name }}{% endif %}</span> | {{ p.co_advisor }} | {{ p.thesis_title }} | {{ p.start_year }} |
{% endfor %}
{% endif %}

{% if current_ms.size > 0 %}
## MS Students

| Name | Co-advisor | Thesis | Started |
|------|------------|--------|---------|
{% for p in current_ms %}| <span id="{{ p.id }}">{% if p.website %}[{{ p.name }}]({{ p.website }}){% else %}{{ p.name }}{% endif %}</span> | {{ p.co_advisor }} | {{ p.thesis_title }} | {{ p.start_year }} |
{% endfor %}
{% endif %}

{% if alumni_postdoc.size > 0 or alumni_phd.size > 0 or alumni_ms.size > 0 %}
## Alumni

{% if alumni_postdoc.size > 0 %}
### Postdocs

| Name | Period | Current Position |
|------|--------|------------------|
{% for p in alumni_postdoc %}| <span id="{{ p.id }}">{% if p.website %}[{{ p.name }}]({{ p.website }}){% else %}{{ p.name }}{% endif %}</span> | {{ p.start_year }}–{{ p.end_year }} | {{ p.current_position }} |
{% endfor %}
{% endif %}

{% if alumni_phd.size > 0 %}
### PhD Students

| Name | Co-advisor | Thesis | Period | Current Position |
|------|------------|--------|--------|------------------|
{% for p in alumni_phd %}| <span id="{{ p.id }}">{% if p.website %}[{{ p.name }}]({{ p.website }}){% else %}{{ p.name }}{% endif %}</span> | {{ p.co_advisor }} | {{ p.thesis_title }} | {{ p.start_year }}–{{ p.end_year }} | {{ p.current_position }} |
{% endfor %}
{% endif %}

{% if alumni_ms.size > 0 %}
### MS Students

| Name | Co-advisor | Thesis | Period | Current Position |
|------|------------|--------|--------|------------------|
{% for p in alumni_ms %}| <span id="{{ p.id }}">{% if p.website %}[{{ p.name }}]({{ p.website }}){% else %}{{ p.name }}{% endif %}</span> | {{ p.co_advisor }} | {{ p.thesis_title }} | {{ p.start_year }}–{{ p.end_year }} | {{ p.current_position }} |
{% endfor %}
{% endif %}

{% endif %}

{% endif %}

{% if collaborators.size > 0 %}
## Collaborators

<details>
<summary style="cursor: pointer; font-size: 1.17em; font-weight: bold; margin-bottom: 0.5em;">{{ collaborators.size }} co-authors</summary>
<div style="margin-top: 0.8em; display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.3em 2em;">
{% for c in collaborators %}<div style="font-size: 0.9em;">{{ c.name }}</div>
{% endfor %}
</div>
</details>
{% endif %}

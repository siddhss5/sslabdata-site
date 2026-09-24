---
title: "Projects"
permalink: /projects/
layout: single
classes: wide
---

{%- comment -%}
Unescaped outputs. Every output not listed here is escaped.
- `project.work_ids.size`: a count Liquid computes, not a string from the data file.
- `url`: a URL captured from safe_url.html, which escapes it.
- `'/projects/' | relative_url`: the site path is a literal in this template; relative_url only prefixes the baseurl from _config.yml.
{%- endcomment -%}

{% assign projects = site.data.lab.projects %}
{% assign works = site.data.lab.works %}

{% if projects.size == 0 %}
<p><em>No projects data configured yet. Add a <code>projects_file</code> to your sslabdata config to populate this page.</em></p>
{% else %}

{% for project in projects %}
<div id="{{ project.id | escape }}" style="margin-top: 2.5em;">

<h2 style="display: inline; margin-right: 0.5em;">{{ project.title | escape }}</h2>
{% if project.status == "active" %}
  {% capture url %}{% include safe_url.html url=project.website %}{% endcapture %}{% if url != "" %}
    <a href="{{ url }}" target="_blank" class="btn btn--success btn--small">Active</a>
  {% else %}
    <span class="btn btn--success btn--small">Active</span>
  {% endif %}
{% else %}
  <span class="btn btn--secondary btn--small">{{ project.status | capitalize | escape }}</span>
{% endif %}
<a href="{{ '/projects/' | relative_url }}{{ project.id | escape }}/" class="btn btn--info btn--small">{{ project.id | escape }}</a>

{% if project.description %}
<p style="margin-top: 0.8em;">{{ project.description | escape }}</p>
{% endif %}

{% if project.work_ids.size > 0 %}
<details>
<summary style="cursor: pointer; font-size: 1.17em; font-weight: bold; margin-top: 0.5em; margin-bottom: 0.5em;">Works ({{ project.work_ids.size }})</summary>
<div style="margin-top: 0.8em;">
{% for work_id in project.work_ids %}
  {% assign pub = works | where: "bib_id", work_id | first %}
  {% if pub %}
  {% include publication.html pub=pub %}
  {% endif %}
{% endfor %}
</div>
</details>
{% endif %}

</div>
{% endfor %}

{% endif %}

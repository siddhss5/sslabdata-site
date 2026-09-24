---
title: "Projects"
permalink: /projects/
layout: single
classes: wide
---

{%- comment -%}
Each project is listed compactly: its title links to the project's page, which
lists its contributors and works; here it has only its status, description,
website and work count.

Unescaped outputs. Every output not listed here is escaped.
- `project.work_ids.size`: a count Liquid computes, not a string from the data file.
- `url`: a URL captured from safe_url.html, which escapes it.
- `'/projects/' | relative_url`: the site path is a literal in this template; relative_url only prefixes the baseurl from _config.yml.
{%- endcomment -%}

{% assign projects = site.data.lab.projects %}

{% if projects.size == 0 %}
<p><em>No projects data configured yet. Add a <code>projects_file</code> to your sslabdata config to populate this page.</em></p>
{% else %}

{% for project in projects %}
<div id="{{ project.id | escape }}" style="margin-top: 2.5em;">

<h2 style="display: inline; margin-right: 0.5em;"><a href="{{ '/projects/' | relative_url }}{{ project.id | escape }}/">{{ project.title | escape }}</a></h2>
{% if project.status == "active" %}
  <span class="btn btn--success btn--small">Active</span>
{% else %}
  <span class="btn btn--secondary btn--small">{{ project.status | capitalize | escape }}</span>
{% endif %}

{% if project.description %}
<p style="margin-top: 0.8em;">{{ project.description | escape }}</p>
{% endif %}

{% capture url %}{% include safe_url.html url=project.website %}{% endcapture %}
{% if url != "" or project.work_ids.size > 0 %}
<p>{% if url != "" %}<a href="{{ url }}" class="btn btn--inverse btn--small" target="_blank">Website</a> {% endif %}{% if project.work_ids.size == 1 %}1 work{% elsif project.work_ids.size > 1 %}{{ project.work_ids.size }} works{% endif %}</p>
{% endif %}

</div>
{% endfor %}

{% endif %}

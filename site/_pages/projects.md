---
title: "Projects"
permalink: /projects/
layout: single
classes: wide
---

{%- comment -%}
Unescaped outputs. Every output not listed here is escaped.
- `project.work_ids.size`: a count Liquid computes, not a string from the data file.
- `title_link`: HTML captured from work_link.html, which escapes the link's URL and text.
- `web_link`: HTML captured from work_link.html, which escapes the link's URL and text.
- `video_link`: HTML captured from work_link.html, which escapes the link's URL and text.
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
<a href="{{ '/projects/' | relative_url }}#{{ project.id | escape }}" class="btn btn--info btn--small">{{ project.id | escape }}</a>

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
  {% capture title_link %}{% include work_link.html work=pub kind="pdf" text=pub.title %}{% endcapture %}
  {% capture web_link %}{% include work_link.html work=pub kind="url" text="Website" style="margin-right: 0.6em;" %}{% endcapture %}
  {% capture video_link %}{% include work_link.html work=pub kind="video" text="Video" style="margin-right: 0.6em;" %}{% endcapture %}
<div style="margin-bottom: 1.2em;">
  <div>
    {% if title_link != "" %}
      {{ title_link }}
    {% else %}
      {{ pub.title | escape }}
    {% endif %}
  </div>
  <div style="font-size: 0.9em; color: #494e52;">
    {% for author in pub.authors %}{{ author.name | escape }}{% if author.equal_contribution %}<sup>*</sup>{% endif %}{% unless forloop.last %}, {% endunless %}{% endfor %}
  </div>
  {% assign equal_authors = pub.authors | where: "equal_contribution", true %}
  {% if equal_authors.size > 0 %}
  <div style="font-size: 0.85em; color: #494e52;"><sup>*</sup> equal contribution</div>
  {% endif %}
  <div style="font-size: 0.9em; color: #494e52;">
    {% include venue.html work=pub %}
  </div>
  {% if pub.note or web_link != "" or video_link != "" %}
  <div style="font-size: 0.9em; margin-top: 0.2em;">
    {{ web_link }}
    {{ video_link }}
    {% if pub.note %}<strong>{{ pub.note | escape }}</strong>{% endif %}
  </div>
  {% endif %}
</div>
  {% endif %}
{% endfor %}
</div>
</details>
{% endif %}

</div>
{% endfor %}

{% endif %}

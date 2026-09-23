---
title: "Works"
permalink: /publications/
layout: single
classes: wide
---

{%- comment -%}
The full list is in the page, so it is complete without JavaScript.
works-filter.js reveals the hidden form and shows only the works matching the
URL's parameters, named as the form's fields.

Unescaped outputs. Every output not listed here is escaped.
- `'/assets/js/works-filter.js' | relative_url`: the site path is a literal in this template; relative_url only prefixes the baseurl from _config.yml.
{%- endcomment -%}
{% assign pubs = site.data.lab.works %}
{% assign years = pubs | map: "year" | uniq | sort | reverse %}
{% assign types = pubs | map: "category" | uniq | sort %}

<form id="works-filter" hidden style="margin-bottom: 1.5em;">
<select name="year" aria-label="Year"><option value="">All years</option>{% for year in years %}<option value="{{ year | escape }}">{{ year | escape }}</option>{% endfor %}</select>
<select name="type" aria-label="Type"><option value="">All types</option>{% for type in types %}<option value="{{ type | escape }}">{{ type | escape }}</option>{% endfor %}</select>
<select name="project" aria-label="Project"><option value="">All projects</option>{% for project in site.data.lab.projects %}<option value="{{ project.id | escape }}">{{ project.title | escape }}</option>{% endfor %}</select>
<select name="person" aria-label="Person"><option value="">All people</option>{% for person in site.data.lab.people %}{% if person.work_ids.size > 0 %}<option value="{{ person.id | escape }}">{{ person.name | escape }}</option>{% endif %}{% endfor %}</select>
<input type="search" name="q" placeholder="Title, author, venue or key" aria-label="Search">
<div id="works-filter-count" style="margin-top: 0.3em; font-size: 0.85em; color: #666;"></div>
</form>

{% for year in years %}
<div class="pub-year-section" data-year="{{ year | escape }}">
<h2>{{ year | escape }}</h2>

{% assign year_pubs = pubs | where: "year", year %}
{% assign categories = year_pubs | map: "category" | uniq %}

{% for category in categories %}
<div class="pub-category-section">
<h3>{{ category | escape }}</h3>

{% assign cat_pubs = year_pubs | where: "category", category %}
{% for pub in cat_pubs %}
{% include publication.html pub=pub %}
{% endfor %}

</div>
{% endfor %}
</div>
{% endfor %}

<script src="{{ '/assets/js/works-filter.js' | relative_url }}"></script>

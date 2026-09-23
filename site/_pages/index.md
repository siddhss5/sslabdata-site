---
title: ""
permalink: /
layout: single
classes: wide
---

{%- comment -%}
Unescaped outputs. Every output not listed here is escaped.
- `pubs.size`: a count Liquid computes, not a string from the data file.
- `current.size`: a count Liquid computes, not a string from the data file.
- `alumni.size`: a count Liquid computes, not a string from the data file.
- `projects.size`: a count Liquid computes, not a string from the data file.
- `website_url`: a URL captured from safe_url.html, which escapes it.
- `github_url`: a URL captured from safe_url.html, which escapes it.
- `youtube_url`: a URL captured from safe_url.html, which escapes it.
- `'/publications/' | relative_url`: the site path is a literal in this template; relative_url only prefixes the baseurl from _config.yml.
- `'/people/' | relative_url`: the site path is a literal in this template; relative_url only prefixes the baseurl from _config.yml.
- `'/projects/' | relative_url`: the site path is a literal in this template; relative_url only prefixes the baseurl from _config.yml.
{%- endcomment -%}

{% assign info = site.data.lab.lab %}
{% assign pubs = site.data.lab.works %}
{% assign people = site.data.lab.people %}
{% assign current = people | where: "status", "current" %}
{% assign alumni = people | where: "status", "alumni" %}
{% assign projects = site.data.lab.projects %}

{% if info %}
<div style="margin-bottom: 1.5em;">
  <h2 style="margin-bottom: 0.3em;">{{ info.name | escape }}</h2>
  <div style="color: #555; margin-bottom: 0.8em;">{{ info.department | escape }}, {{ info.university | escape }}</div>
  <p style="font-size: 1.05em;">{{ info.description | escape }}</p>
  <div>
    {% capture website_url %}{% include safe_url.html url=info.website %}{% endcapture %}{% if website_url != "" %}<a href="{{ website_url }}" class="btn btn--inverse btn--small" target="_blank">Website</a>{% endif %}
    {% capture github_url %}{% include safe_url.html url=info.github %}{% endcapture %}{% if github_url != "" %}<a href="{{ github_url }}" class="btn btn--inverse btn--small" target="_blank">GitHub</a>{% endif %}
    {% capture youtube_url %}{% include safe_url.html url=info.youtube %}{% endcapture %}{% if youtube_url != "" %}<a href="{{ youtube_url }}" class="btn btn--inverse btn--small" target="_blank">YouTube</a>{% endif %}
  </div>
</div>
<hr>
{% endif %}

<div style="margin-bottom: 2em; font-size: 1.05em;">
<strong>{{ pubs.size }}</strong> works, <strong>{{ current.size }}</strong> current members, <strong>{{ alumni.size }}</strong> alumni, and <strong>{{ projects.size }}</strong> research projects.
</div>

## Browse

- [**Works**]({{ '/publications/' | relative_url }}) — Full list of works with search, abstracts, and BibTeX
- [**People**]({{ '/people/' | relative_url }}) — Current members, alumni, and collaborators
- [**Projects**]({{ '/projects/' | relative_url }}) — Research projects with linked works

---

## Recent Works

{% assign recent = pubs | slice: 0, 10 %}
{% for pub in recent %}
{% include publication.html pub=pub %}
{% endfor %}

[View all {{ pubs.size }} works &rarr;]({{ '/publications/' | relative_url }})

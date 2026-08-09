---
permalink: /
title: "Fengyi Yuan"
description: >-
  Fengyi Yuan is an Assistant Professor at The Chinese University of Hong Kong,
  Shenzhen, with research interests in mean field games, generative models,
  stochastic control, financial mathematics, and time-inconsistent decision problems.
last_modified_at: "2026-08-09"
---
{% assign profile = site.data.profile %}
<article class="home-page">
  <header class="profile-hero">
    <div class="profile-identity">
      <h1>{{ profile.name | escape }}</h1>
      <p class="position">{{ profile.role | escape }}</p>
      <p class="affiliation"><a href="{{ profile.affiliation_url | escape }}">{{ profile.affiliation | escape }}</a></p>
      <nav class="profile-links" aria-label="Academic profiles and contact">
        {% for link in profile.profiles %}<a href="{{ link.url | escape }}">{{ link.label | escape }}</a>{% endfor %}
        <a href="mailto:{{ profile.email | escape }}">Email</a>
        <a href="{{ profile.cv_url | relative_url | escape }}">CV <span aria-hidden="true">(PDF)</span><span class="visually-hidden">, PDF document</span></a>
      </nav>
    </div>
    <div class="profile-photo-wrap">
      <img class="profile-photo" src="{{ profile.portrait.src | relative_url | escape }}" srcset="{{ profile.portrait.srcset | escape }}" sizes="(max-width: 720px) 160px, (max-width: 960px) 224px, 272px" width="{{ profile.portrait.width | escape }}" height="{{ profile.portrait.height | escape }}" alt="{{ profile.portrait.alt | escape }}">
    </div>
    <div class="biography">
      {% for paragraph in profile.bio %}{{ paragraph | markdownify }}{% endfor %}
    </div>
  </header>

  <section aria-labelledby="research-interests">
    <h2 id="research-interests">Research interests</h2>
    <ul class="compact-list interests-list">
      {% for interest in profile.research_interests %}<li>{{ interest | escape }}</li>{% endfor %}
    </ul>
  </section>

  <section aria-labelledby="recent-work">
    <div class="section-heading-row">
      <h2 id="recent-work">Recent work</h2>
      <a class="section-link" href="{{ '/publications/' | relative_url }}">All research</a>
    </div>
    {% assign preprints = site.data.publications | where: "section", "preprint" %}
    <ol class="publication-list recent-publications">
      {% for publication in preprints limit: 3 %}{% include publication-item.html item=publication %}{% endfor %}
    </ol>
  </section>

  <section id="honors" aria-labelledby="honors-heading">
    <h2 id="honors-heading">Awards &amp; honors</h2>
    <ul class="honors-list compact-list">
      {% for honor in site.data.honors %}
        <li><strong>{{ honor.title | escape }}</strong>{% if honor.detail %} ({{ honor.detail | escape }}){% endif %}.{% if honor.institution %} {{ honor.institution | escape }},{% endif %} {{ honor.year | escape }}.</li>
      {% endfor %}
    </ul>
  </section>

  <section aria-labelledby="contact-heading">
    <h2 id="contact-heading">Contact</h2>
    <address class="contact-details">
      <span>{{ profile.contact.address | escape }}</span>
      <span>Email: <a href="mailto:{{ profile.email | escape }}">{{ profile.email | escape }}</a></span>
      <span>Tel: {% for phone in profile.contact.phones %}{{ phone | escape }}{% unless forloop.last %}; {% endunless %}{% endfor %}</span>
    </address>
  </section>
</article>

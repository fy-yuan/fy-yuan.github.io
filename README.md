# Fengyi Yuan — academic website

This repository contains the Jekyll source for
[fy-yuan.github.io](https://fy-yuan.github.io). The site uses a small custom
layout, GitHub Pages, and structured YAML data; it has no JavaScript or Node
build step.

## Updating content

- Edit `_data/profile.yml` for the biography, research interests, contact
  details, and academic profile links.
- Edit `_data/publications.yml`, `_data/presentations.yml`,
  `_data/teaching.yml`, and `_data/honors.yml` for the corresponding lists.
  Entries appear in file order.
- Replace `assets/CV.pdf` when the CV is updated. The navigation and legacy CV
  URLs already point to this file.
- Put new papers or slides in `assets/` and reference them from the appropriate
  YAML record.

The homepage automatically displays the first three preprints from
`_data/publications.yml`, so those entries do not need to be duplicated.

## Local preview

The production environment is pinned to Ruby 3.3.4 and `github-pages` 232.

```sh
bundle install
bundle exec jekyll serve
```

Then open <http://127.0.0.1:4000>. To run the same repository checks used in
CI after a build:

```sh
bundle exec jekyll build
python3 scripts/validate_site.py _site
```

Pushes to `master` are built, validated, and deployed by
`.github/workflows/pages.yml`. GitHub Pages must use **GitHub Actions** as its
deployment source.

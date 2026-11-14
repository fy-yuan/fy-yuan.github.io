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
  Research and other full lists retain file order.
- Replace `assets/CV.pdf` when the CV is updated. The navigation and legacy CV
  URLs already point to this file.
- Put new papers or slides in `assets/` and reference them from the appropriate
  YAML record.

The homepage's **Recent work** combines preprints and newly accepted papers from
`_data/publications.yml`, sorts them by `recent_date` (newest first), and displays
the first three. Use a quoted ISO date (`"YYYY-MM-DD"`): the initial public release
date for a new preprint (arXiv v1 submission date for the current entries), then
replace it with the date its acceptance news is added to the website. Keep this
date when adding final journal publication details; it is separate from the
bibliographic `year`. Older journal entries without a recorded announcement date
are omitted from Recent work. No duplicate publication entry is needed.

## Local preview

The production environment is pinned to Ruby 3.3.4, `github-pages` 232, and
Jekyll 3.10.0. Bundler installs the exact dependency set in `Gemfile.lock`.

```sh
bundle install
bundle exec jekyll serve
```

Then open <http://127.0.0.1:4000>. To run the same repository checks used in
CI after a build:

```sh
JEKYLL_ENV=production bundle exec jekyll build --trace
python3 scripts/validate_site.py _site
```

Pushes to `master` are built, validated, and deployed by
`.github/workflows/pages.yml`. GitHub Pages must use **GitHub Actions** as its
deployment source.

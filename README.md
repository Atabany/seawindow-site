# SeaWindow public pages

Standalone support and privacy site for SeaWindow. Only this directory is published; no app source, keys or QA data belong here.

- Home: https://atabany.github.io/seawindow-site/
- Support: https://atabany.github.io/seawindow-site/support.html
- Privacy: https://atabany.github.io/seawindow-site/privacy.html

Review the privacy claims against the release build whenever data providers change (see SeaWindow docs/KB.md).

## Discovery and install links (18 October 2026)

After regenerating policy/support pages, run `python3 _ops/enrich.py`. It restores the verified metadata, App Store badges and campaign links from `_ops/discovery.json` without changing legal body text. Keep app-specific facts in sync with the current listing and app source. Privacy remains authored in the app repository. This project subpath does not control the host-root robots.txt. `llms.txt` is an optional reference, not an AI ranking mechanism.

## Guides (from 4 November 2026)

A guide is a hand-written root HTML page listed under `guides` in `_ops/discovery.json` (file, title, description, campaign tag, dates, llms summary). `python3 _ops/enrich.py` regenerates its managed parts and nothing else: metadata, Article, BreadcrumbList and FAQPage JSON-LD (the FAQ schema is read from the visible `#faq` section), the App Store CTA at each `<!-- discovery-cta-slot -->`, the Guides card on the home and support pages, the sitemap and both llms files. Everything outside `discovery-*` blocks survives a re-run, and the output is stable when run twice. To change a guide, edit the page, run enrich, then `python3 _ops/validate.py`, which also checks schema against visible text, byline, Updated date, a unique campaign tag of at most 30 characters, and 800–1,300 words.

- `how-to-read-a-tide-chart.html`, campaign `seawindow-guide-tide-chart`. The topic is editorial judgment, not measured search volume. Heights and times are NOAA CO-OPS predictions for station 9414290 and USNO moon phases, retrieved 4 November 2026; UI labels were checked in the SeaWindow Swift source. `_ops/tide_chart_example.py` reprints the inline SVG curve (paste between the `tide-svg` comments).
- IndexNow is not possible on this github.io subpath because its key file must sit at the host root. The host-root robots.txt is also outside this repo's control.

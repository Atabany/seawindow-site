# SeaWindow public pages

Standalone support and privacy site for SeaWindow. Only this directory is published; no app source, keys or QA data belong here.

- Home: https://atabany.github.io/seawindow-site/
- Support: https://atabany.github.io/seawindow-site/support.html
- Privacy: https://atabany.github.io/seawindow-site/privacy.html

Review the privacy claims against the release build whenever data providers change (see SeaWindow docs/KB.md).

## Discovery and install links (18 October 2026)

After regenerating policy/support pages, run `python3 _ops/enrich.py`. It restores the verified metadata, App Store badges and campaign links from `_ops/discovery.json` without changing legal body text. Keep app-specific facts in sync with the current listing and app source. Privacy remains authored in the app repository. This project subpath does not control the host-root robots.txt. `llms.txt` is an optional reference, not an AI ranking mechanism.

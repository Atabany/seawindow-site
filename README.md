# SeaWindow website

Static site for the SeaWindow iPhone app at https://seawindowtides.com/, published with GitHub Pages
from `main`. Everything in this
repository is public; no app source, keys or QA data belong here. The site's state and history are
written in the app repository's `docs/HANDOFF.md` and `docs/KB.md` ("Website").

## Build

```sh
python3 -I _ops/make_assets.py   # only when screenshots, art or the icon change
python3 -I _ops/build.py         # _src/pages/*.html -> *.html, sitemap.xml, robots.txt, llms*.txt
python3 -I _ops/validate.py      # must print OK before every push
```

- Sources: `_src/pages/*.html`. Each starts with a `<!--page {json} -->` header (title ≤ 60, description
  ≤ 160, kind `home|guide|tool|hub|page|404`, `campaign` tag, dates, `headline`, `blurb`, `summary`).
  Never edit the built root `.html` files by hand.
- Facts shared by every page: `_src/site.json` (`base`, App Store id, provider token, facts block,
  rating). `base` is `https://seawindowtides.com/`.
- Placeholders: `<!--cta-->`, `<!--cta:hero-->`, `<!--cta:band-->`, `<!--guides-->`, `<!--tools-->`,
  `<!--related-->`, `<!--rating-->`, `<!--facts-->`.
- App Store links are generated in Apple's campaign format
  (`https://apps.apple.com/app/apple-store/id6811683172?pt=127826363&ct=<tag>&mt=8`), one tag per page.
- Images come from real simulator captures in `~/indie/SeaWindow/Tools/Website/captures` (resized
  only) and the ChatGPT/Codex ocean art in `~/indie/SeaWindow/Tools/AppStore/art`.
- FAQ: `<section class="faq">` with `<details><summary>Q</summary><div class="a"><p>A</p></div></details>`;
  the FAQPage schema is generated from the visible text.
- Guides: 800–1,600 words, answer first, table of contents, worked example with retrieval date,
  Sources section, FAQ, `<!--cta-->` and `<!--related-->`. Facts about the app come from its source code.
- Never print prices, invented ratings or reviews. Show a rating only with its real count
  (`rating` in `site.json`).

## Domain and search engines

- `seawindowtides.com` is registered at Cloudflare (bought 2026-11-19, auto-renew). DNS is DNS-only
  (grey cloud): 4×A and 4×AAAA to GitHub Pages, `www` CNAME `atabany.github.io`, plus `v=spf1 -all`,
  a reject DMARC record (the domain sends no mail) and the Google Search Console TXT. `CNAME` in this repo
  holds the domain; HTTPS is enforced. Old `atabany.github.io/seawindow-site/...` URLs 301 to the same
  path here. `_ops/connect_domain.sh` is the script that made the move.
- Google Search Console: Domain property `seawindowtides.com` (verified by DNS TXT, never by authorising
  Google into Cloudflare), sitemap submitted.
- IndexNow (Bing, Yandex and others): after a push that adds or changes pages run
  `sh _ops/indexnow.sh` (every sitemap URL) or pass the changed URLs. The key file in the root
  (`<key>.txt`) must stay published.

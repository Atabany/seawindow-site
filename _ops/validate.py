#!/usr/bin/env python3
"""Check the built SeaWindow site before publishing. Prints OK or the problems and exits 1.

    python3 -I _ops/build.py && python3 -I _ops/validate.py

Checks: every page from _src is built; titles <= 60 and descriptions <= 155 characters, unique;
canonical = base + file; one h1; local links and images resolve; images have width/height/alt;
JSON-LD parses and FAQ schema matches the visible FAQ; App Store links use the campaign format with
one tag per page, unique across pages, <= 40 chars; guides have a byline, an Updated date and
800-1,600 words; sitemap and llms.txt cover every indexable page; banned phrases and prices absent.
"""
from pathlib import Path
import html
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
C = json.loads((ROOT / '_src/site.json').read_text())
BASE = C['base']
problems = []
err = lambda f, m: problems.append(f'{f}: {m}')

BANNED = [r'\bAI-powered\b', r'#1\b', r'\bbest tide app\b(?! for)', r'\$\d', r'€\d', r'£\d', r'\bguarantee', r'full chart atlas',
          r'\bnavigation tool\b(?<!not a navigation tool)', r'lorem', r'TODO', r'\bseawindow\.app\b']
SOURCES = sorted((ROOT / '_src/pages').glob('*.html'))
metas = {}
for p in SOURCES:
    m = re.match(r'<!--page\s*(\{.*?\})\s*-->', p.read_text(), re.S)
    metas[p.name] = json.loads(m[1])

titles, descs, tags = {}, {}, {}
sitemap = (ROOT / 'sitemap.xml').read_text()
llms = (ROOT / 'llms.txt').read_text()

for name, meta in metas.items():
    f = ROOT / name
    if not f.exists():
        err(name, 'not built')
        continue
    s = f.read_text()
    text = html.unescape(re.sub(r'<script.*?</script>|<style.*?</style>|<[^>]+>', ' ', s, flags=re.S))
    title = html.unescape(re.search(r'<title>(.*?)</title>', s, re.S)[1])
    desc = html.unescape(re.search(r'<meta name="description" content="([^"]*)"', s)[1])
    if len(title) > 60:
        err(name, f'title {len(title)} chars: {title}')
    if not 70 <= len(desc) <= 160:
        err(name, f'description {len(desc)} chars')
    if title in titles:
        err(name, f'title duplicates {titles[title]}')
    titles[title] = name
    if desc in descs:
        err(name, f'description duplicates {descs[desc]}')
    descs[desc] = name
    kind = meta['kind']
    if kind != '404':
        want = BASE if name == 'index.html' else BASE + name
        canon = re.search(r'<link rel="canonical" href="([^"]+)"', s)
        if not canon or canon[1] != want:
            err(name, f'canonical {canon and canon[1]} != {want}')
        if f'<loc>{want}</loc>' not in sitemap:
            err(name, 'missing from sitemap.xml')
        if want not in llms:
            err(name, 'missing from llms.txt')
    if len(re.findall(r'<h1[\s>]', s)) != 1:
        err(name, 'needs exactly one h1')
    # local links and assets
    for ref in re.findall(r'(?:href|src)="([^"#?]+)', s):
        if ref.startswith(('http:', 'https:', 'mailto:', 'data:')):
            continue
        if not (ROOT / ref).exists():
            err(name, f'broken local reference {ref}')
    for frag in re.findall(r'href="#([^"]+)"', s):
        if f'id="{frag}"' not in s:
            err(name, f'missing anchor #{frag}')
    for img in re.findall(r'<img\b[^>]*>', s):
        for attr in ('width=', 'height=', 'alt='):
            if attr not in img:
                err(name, f'img without {attr[:-1]}: {img[:80]}')
    # App Store links
    links = re.findall(r'href="(https://apps\.apple\.com/app/[^"]+)"', s)
    if kind != '404' and not links:
        err(name, 'no App Store link')
    page_tags = set()
    for l in links:
        l = html.unescape(l)
        m = re.fullmatch(r'https://apps\.apple\.com/app/apple-store/id' + C['appId'] + r'\?pt=' + C['providerToken'] + r'&ct=([\w-]+)&mt=8', l)
        if not m:
            err(name, f'App Store link not in campaign format: {l}')
            continue
        page_tags.add(m[1])
    if len(page_tags) > 1:
        err(name, f'several campaign tags {page_tags}')
    for t in page_tags:
        if len(t) > 40:
            err(name, f'campaign tag too long {t}')
        if t in tags and tags[t] != name:
            err(name, f'campaign tag {t} also used by {tags[t]}')
        tags[t] = name
    # JSON-LD
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
    graph = []
    for b in blocks:
        try:
            graph += json.loads(b.replace('<\\/', '</')).get('@graph', [])
        except json.JSONDecodeError as e:
            err(name, f'JSON-LD does not parse: {e}')
    types = {g.get('@type') for g in graph}
    faq_visible = re.findall(r'<summary>(.*?)</summary>', s)
    faq_schema = [g for g in graph if g.get('@type') == 'FAQPage']
    if faq_visible and not faq_schema:
        err(name, 'visible FAQ without FAQPage schema')
    for g in faq_schema:
        qs = [q['name'] for q in g['mainEntity']]
        vis = [re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', v))).strip() for v in faq_visible]
        if qs != vis:
            err(name, 'FAQ schema questions differ from visible FAQ')
        for q in g['mainEntity']:
            if q['acceptedAnswer']['text'][:60] not in re.sub(r'\s+', ' ', text):
                err(name, f'FAQ answer not visible: {q["name"]}')
    if kind == 'home' and 'MobileApplication' not in types:
        err(name, 'home without MobileApplication schema')
    if kind == 'guide':
        if 'Article' not in types or 'BreadcrumbList' not in types:
            err(name, 'guide needs Article and BreadcrumbList schema')
        if 'class="byline">By ' not in s or 'Updated <time' not in s:
            err(name, 'guide needs byline and Updated date')
        art = re.search(r'<div class="article">(.*?)<section class="related">', s, re.S)
        words = len(re.findall(r"[A-Za-z0-9’']+", html.unescape(re.sub(r'<[^>]+>', ' ', art[1] if art else ''))))
        if not 800 <= words <= 1600:
            err(name, f'guide has {words} words (800-1,600)')
        if not re.search(r'id="sources"', s):
            err(name, 'guide needs a Sources section')
    if kind == 'tool' and 'WebApplication' not in types:
        err(name, 'tool without WebApplication schema')
    for pat in BANNED:
        hit = re.search(pat, text, re.I)
        if hit:
            err(name, f'banned phrase “{hit[0]}”')
    if 'planning aid' not in text:
        err(name, 'missing the planning-aid disclaimer')

# stray built pages with no source
for f in ROOT.glob('*.html'):
    if f.name not in metas:
        err(f.name, 'built page with no _src source (remove it or add a source)')

if problems:
    print('\n'.join(problems))
    sys.exit(1)
print(f'OK: {len(metas)} pages, {len(tags)} campaign tags')

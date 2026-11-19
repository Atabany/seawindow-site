#!/usr/bin/env python3
"""Build the SeaWindow website: _src/pages/*.html -> repo root.

    python3 -I _ops/build.py && python3 -I _ops/validate.py

Each source page starts with a JSON header in an HTML comment:

    <!--page
    {"title": "...", "description": "...", "kind": "guide", "campaign": "seawindow-guide-x", ...}
    -->

kind: home | guide | tool | hub | page | 404. The build adds the shared head (metadata, canonical,
Open Graph, JSON-LD), header, footer, App Store CTAs with one campaign tag per page, the guide
hub, sitemap.xml, robots.txt, llms.txt and llms-full.txt. Facts live in _src/site.json.
Placeholders in page bodies: <!--cta-->, <!--cta:hero-->, <!--cta:band-->, <!--guides-->,
<!--tools-->, <!--related-->, <!--rating-->, <!--facts-->.
"""
from pathlib import Path
import hashlib
import html
import json
import re
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / '_src'
C = json.loads((SRC / 'site.json').read_text())
BASE = C['base']
APP = C['appId']
E = lambda s: html.escape(str(s), quote=True)
TODAY = date.today().isoformat()

CSS = ROOT / 'assets/site.css'
CSS_V = hashlib.sha1(CSS.read_bytes()).hexdigest()[:8]


def parse(path):
    s = path.read_text()
    m = re.match(r'<!--page\s*(\{.*?\})\s*-->\s*', s, re.S)
    if not m:
        raise SystemExit(f'{path.name}: missing <!--page {{...}} --> header')
    meta = json.loads(m[1])
    meta['file'] = path.name
    meta['body'] = s[m.end():]
    return meta


PAGES = [parse(p) for p in sorted((SRC / 'pages').glob('*.html'))]
BY_FILE = {p['file']: p for p in PAGES}
GUIDES = sorted([p for p in PAGES if p['kind'] == 'guide'], key=lambda p: p.get('order', 99))
TOOLS = sorted([p for p in PAGES if p['kind'] == 'tool'], key=lambda p: p.get('order', 99))


def url(p):
    return BASE if p['file'] == 'index.html' else BASE + p['file']


def store_url(tag):
    return f'https://apps.apple.com/app/apple-store/id{APP}?pt={C["providerToken"]}&ct={tag}&mt=8'


def rating_line():
    r = C.get('rating') or {}
    if not r.get('count'):
        return ''
    return (f'<p class="app-rating"><span aria-hidden="true">★★★★★</span> <strong>{r["value"]}</strong> on the App Store'
            f' · rated by {r["count"]} {"user" if r["count"] == 1 else "users"}</p>')


def cta(p, variant=''):
    tag = p['campaign']
    link = (f'<a class="cta-link" href="{E(store_url(tag))}" aria-label="Download SeaWindow on the App Store">'
            f'<img class="icon" src="assets/app-icon.png" width="60" height="60" alt="">'
            f'<img class="badge" src="assets/app-store-badge.svg" width="162" height="54" alt="Download on the App Store"></a>')
    note = f'<p class="cta-note">{C["ctaNote"]}</p>'
    if variant == 'inline':
        text = p.get('ctaText', C['ctaText'])
        return f'<aside class="cta-inline"><p><strong>{text}</strong></p><div class="cta">{link}{note}</div></aside>'
    return f'<div class="cta">{link}{note}</div>{rating_line()}'


def card(p):
    kicker = {'guide': 'Guide', 'tool': 'Free tool'}.get(p['kind'], '')
    return (f'<a class="card" href="{E(p["file"])}"><span class="kicker">{kicker}</span><h3>{E(p["headline"])}</h3>'
            f'<p>{E(p["blurb"])}</p><span class="more">{E(p.get("more", "Read the guide"))} →</span></a>')


def related(p):
    others = [q for q in TOOLS + GUIDES if q['file'] != p['file']]
    pick = [BY_FILE[f] for f in p.get('related', []) if f in BY_FILE] or others[:4]
    return '<section class="related"><h2>Keep reading</h2><div class="grid cols-2">' + ''.join(card(q) for q in pick[:4]) + '</div></section>'


NAV = [('Features', 'index.html#features'), ('Tide guides', 'guides.html'), ('Tide calculator', 'tide-calculator.html'), ('Support', 'support.html')]


def header(p):
    links = ''.join(
        f'<a href="{href}"' + (' aria-current="page"' if href == p['file'] else '') + f'>{name}</a>' for name, href in NAV)
    return (f'<a class="skip" href="#main">Skip to content</a><header class="site-header"><div class="wrap">'
            f'<a class="brand" href="index.html"><img src="assets/app-icon.png" width="34" height="34" alt="">SeaWindow</a>'
            f'<nav class="nav" aria-label="Main">{links}</nav>'
            f'<a class="nav-store" href="{E(store_url(p["campaign"]))}" aria-label="Download SeaWindow on the App Store">'
            f'<img src="assets/app-store-badge.svg" width="120" height="40" alt="Download on the App Store"></a></div></header>')


def footer():
    g = ''.join(f'<li><a href="{q["file"]}">{E(q["headline"])}</a></li>' for q in GUIDES[:6])
    t = ''.join(f'<li><a href="{q["file"]}">{E(q["headline"])}</a></li>' for q in TOOLS)
    return f'''<footer class="site-footer"><div class="wrap"><div class="foot-grid">
<div class="foot-brand"><a class="brand" href="index.html"><img src="assets/app-icon.png" width="34" height="34" alt="" loading="lazy">SeaWindow</a><p>{E(C["footerBlurb"])}</p></div>
<div><h2>Guides</h2><ul>{g}<li><a href="guides.html">All tide guides</a></li></ul></div>
<div><h2>Tools</h2><ul>{t}</ul></div>
<div><h2>SeaWindow</h2><ul><li><a href="index.html#features">Features</a></li><li><a href="index.html#pro">Free and Pro</a></li><li><a href="about.html">About</a></li><li><a href="support.html">Support</a></li><li><a href="privacy.html">Privacy policy</a></li></ul></div>
</div><div class="foot-legal"><span>© {date.today().year} Mohamed Elatabany. SeaWindow is a planning aid, not a navigation or safety tool.</span><span>Apple, the Apple logo and iPhone are trademarks of Apple Inc. App Store is a service mark of Apple Inc.</span></div></div></footer>'''


def faq_pairs(body):
    clean = lambda x: re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', x))).strip()
    sec = re.search(r'<section[^>]*class="faq"[^>]*>(.*?)</section>', body, re.S)
    if not sec:
        return []
    return [(clean(q), clean(a)) for q, a in re.findall(r'<summary>(.*?)</summary>\s*<div class="a">(.*?)</div>', sec[1], re.S)]


def jsonld(p, body):
    u = url(p)
    author = {'@id': BASE + '#author'}
    graph = [
        {'@type': 'WebSite', '@id': BASE + '#website', 'url': BASE, 'name': 'SeaWindow', 'inLanguage': 'en', 'publisher': author},
        {'@type': 'Person', '@id': BASE + '#author', 'name': C['author'], 'url': BASE + 'about.html', 'sameAs': C['authorLinks']},
    ]
    page_type = {'home': 'WebPage', 'guide': 'WebPage', 'tool': 'WebPage', 'hub': 'CollectionPage'}.get(p['kind'], 'WebPage')
    if p['file'] == 'about.html':
        page_type = 'AboutPage'
    if p['file'] == 'support.html':
        page_type = 'ContactPage'
    graph.append({'@type': page_type, '@id': u + '#page', 'url': u, 'name': p['title'], 'description': p['description'],
                  'isPartOf': {'@id': BASE + '#website'}, 'inLanguage': 'en',
                  'primaryImageOfPage': BASE + 'assets/og.jpg'})
    if p['kind'] == 'home':
        app = {'@type': 'MobileApplication', '@id': BASE + '#app', 'name': C['storeName'], 'alternateName': 'SeaWindow',
               'url': BASE, 'downloadUrl': f'https://apps.apple.com/app/id{APP}', 'sameAs': f'https://apps.apple.com/app/id{APP}',
               'operatingSystem': f'iOS {C["minimumOS"]} or later', 'applicationCategory': 'WeatherApplication',
               'softwareVersion': C['version'], 'description': C['facts'], 'image': BASE + 'assets/app-icon.png',
               'screenshot': [BASE + f'assets/screens/{n}.webp' for n in ('today', 'charts', 'places', 'sky')],
               'inLanguage': ['en', 'ar'], 'author': author,
               'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'USD', 'description': C['offerNote']}}
        r = C.get('rating') or {}
        if r.get('count'):
            app['aggregateRating'] = {'@type': 'AggregateRating', 'ratingValue': str(r['value']), 'ratingCount': r['count'], 'bestRating': '5', 'worstRating': '1'}
        graph.append(app)
    else:
        crumbs = [('SeaWindow', BASE)]
        if p['kind'] == 'guide':
            crumbs.append(('Tide guides', BASE + 'guides.html'))
        crumbs.append((p.get('crumb', p['title']), u))
        graph.append({'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': l} for i, (n, l) in enumerate(crumbs)]})
    if p['kind'] == 'guide':
        graph.append({'@type': 'Article', '@id': u + '#article', 'headline': p['headline'], 'description': p['description'],
                      'datePublished': p['published'], 'dateModified': p['modified'], 'author': author, 'publisher': author,
                      'image': BASE + 'assets/og.jpg', 'mainEntityOfPage': {'@id': u + '#page'}, 'inLanguage': 'en',
                      'about': p.get('about', [])})
    if p['kind'] == 'tool':
        graph.append({'@type': 'WebApplication', '@id': u + '#tool', 'name': p['headline'], 'url': u, 'description': p['description'],
                      'applicationCategory': 'UtilitiesApplication', 'operatingSystem': 'Any', 'browserRequirements': 'Requires JavaScript',
                      'isAccessibleForFree': True, 'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'USD'},
                      'author': author, 'datePublished': p['published'], 'dateModified': p['modified']})
    faq = faq_pairs(body)
    if faq:
        graph.append({'@type': 'FAQPage', '@id': u + '#faq', 'mainEntity': [
            {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faq]})
    data = json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False, separators=(',', ':'))
    return '<script type="application/ld+json">' + data.replace('</', '<\\/') + '</script>'


def head(p, body):
    u = url(p)
    og_type = 'article' if p['kind'] == 'guide' else 'website'
    robots = 'noindex' if p['kind'] == '404' else 'index,follow,max-image-preview:large'
    base_tag = f'<base href="{E(BASE)}">' if p['kind'] == '404' else ''
    canonical = '' if p['kind'] == '404' else f'<link rel="canonical" href="{E(u)}">'
    extra = ''.join(f'<link rel="stylesheet" href="{E(x)}">' for x in p.get('css', []))
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">{base_tag}'
            f'<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            f'<title>{E(p["title"])}</title><meta name="description" content="{E(p["description"])}">{canonical}'
            f'<meta name="robots" content="{robots}"><meta name="author" content="{E(C["author"])}">'
            f'<meta name="theme-color" content="#07101f"><meta name="apple-itunes-app" content="app-id={APP}">'
            f'<meta property="og:type" content="{og_type}"><meta property="og:site_name" content="SeaWindow">'
            f'<meta property="og:title" content="{E(p.get("ogTitle", p["title"]))}"><meta property="og:description" content="{E(p["description"])}">'
            f'<meta property="og:url" content="{E(u)}"><meta property="og:image" content="{E(BASE)}assets/og.jpg">'
            f'<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
            f'<meta property="og:image:alt" content="SeaWindow on iPhone: today\'s tide curve, next high and low">'
            f'<meta name="twitter:card" content="summary_large_image">'
            f'<link rel="icon" type="image/png" sizes="32x32" href="assets/favicon-32.png">'
            f'<link rel="apple-touch-icon" href="assets/apple-touch-icon.png">'
            f'<link rel="stylesheet" href="assets/site.css?v={CSS_V}">{extra}'
            f'{jsonld(p, body)}</head><body>')


def page_hero(p):
    crumbs = '<a href="index.html">SeaWindow</a>'
    if p['kind'] == 'guide':
        crumbs += ' › <a href="guides.html">Tide guides</a>'
    crumbs += f' › {E(p.get("crumb", p["title"]))}'
    byline = ''
    if p['kind'] in ('guide', 'tool'):
        d = date.fromisoformat(p['modified'])
        byline = (f'<p class="byline">By <a href="about.html">{E(C["author"])}</a>, developer of SeaWindow · '
                  f'Updated <time datetime="{p["modified"]}">{d.strftime("%B %Y")}</time></p>')
    elif p.get('lede'):
        byline = f'<p class="byline">{p["lede"]}</p>'
    return (f'<section class="page-hero"><div class="read"><nav aria-label="Breadcrumb"><p class="crumbs">{crumbs}</p></nav>'
            f'<p class="eyebrow">{E(p.get("eyebrow", ""))}</p><h1>{E(p["headline"])}</h1>{byline}</div></section>')


def render(p):
    body = p['body']
    body = body.replace('<!--cta:hero-->', cta(p)).replace('<!--cta:band-->', cta(p)).replace('<!--cta-->', cta(p, 'inline'))
    body = body.replace('<!--guides-->', ''.join(card(q) for q in GUIDES))
    body = body.replace('<!--tools-->', ''.join(card(q) for q in TOOLS))
    body = body.replace('<!--related-->', related(p)).replace('<!--rating-->', rating_line())
    body = body.replace('<!--facts-->', f'<p>{E(C["facts"])}</p>')
    if p['kind'] in ('guide', 'tool', 'page', 'hub', '404'):
        width = 'wrap' if p['kind'] == 'hub' else 'read'
        main = f'<main id="main">{page_hero(p)}<div class="article"><div class="{width}">{body}</div></div></main>'
    else:
        main = f'<main id="main">{body}</main>'
    script = ''.join(f'<script src="{E(s)}" defer></script>' for s in p.get('js', []))
    out = head(p, body) + header(p) + main + footer() + script + '</body></html>\n'
    leftovers = re.findall(r'<!--(?:cta|guides|tools|related|rating|facts)[^>]*-->', out)
    if leftovers:
        raise SystemExit(f'{p["file"]}: unknown placeholder {leftovers}')
    (ROOT / p['file']).write_text(out)


for p in PAGES:
    render(p)

# sitemap.xml
indexable = [p for p in PAGES if p['kind'] != '404']
rows = ''.join(f'  <url><loc>{E(url(p))}</loc><lastmod>{p.get("modified", TODAY)}</lastmod></url>\n' for p in indexable)
(ROOT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + rows + '</urlset>\n')

# robots.txt (effective only at a host root, i.e. once the custom domain is live)
bots = ['OAI-SearchBot', 'ChatGPT-User', 'GPTBot', 'ClaudeBot', 'Claude-SearchBot', 'Claude-User', 'PerplexityBot',
        'Perplexity-User', 'Google-Extended', 'Applebot', 'Applebot-Extended', 'Bingbot', 'Googlebot', 'DuckDuckBot']
robots = ''.join(f'User-agent: {b}\nAllow: /\n\n' for b in bots) + 'User-agent: *\nAllow: /\n\n' + f'Sitemap: {BASE}sitemap.xml\n'
(ROOT / 'robots.txt').write_text(robots)

# llms.txt and llms-full.txt
store = f'https://apps.apple.com/app/id{APP}'
lines = [f'# {C["storeName"]}', '', f'> {C["llmsLead"]}', '', C['facts'], '', f'App Store: {store}', '',
         '## Pages', ''] + [f'- [{p["title"]}]({url(p)}): {p["description"]}' for p in indexable if p['kind'] in ('home', 'page', 'hub')]
lines += ['', '## Tools', ''] + [f'- [{p["headline"]}]({url(p)}): {p["description"]}' for p in TOOLS]
lines += ['', '## Guides', ''] + [f'- [{p["headline"]}]({url(p)}): {p["description"]}' for p in GUIDES]
(ROOT / 'llms.txt').write_text('\n'.join(lines) + '\n')
full = lines[:9] + ['## About SeaWindow', '', C['llmsAbout'], '']
for p in [BY_FILE['index.html']] + TOOLS + GUIDES:
    full += [f'## {p.get("headline", p["title"])}', '', url(p), '']
    if p.get('summary'):
        full += [p['summary'], '']
    for q, a in faq_pairs(p['body']):
        full += [f'Q: {q}', f'A: {a}', '']
(ROOT / 'llms-full.txt').write_text('\n'.join(full))
print(f'built {len(PAGES)} pages, css v={CSS_V}')

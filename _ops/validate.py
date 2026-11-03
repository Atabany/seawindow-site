"""Validate a small app site's metadata, links, install paths and discovery coverage."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, parse_qs, unquote
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
C = json.loads((ROOT / '_ops/discovery.json').read_text())
errors = []

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ''
        self.in_title = False
        self.in_json = False
        self.buffer = ''
        self.schema = []
        self.links = []
        self.images = []
        self.ids = set()
        self.meta = {}
        self.canonical = []
        self.h1 = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            if a['id'] in self.ids:
                errors.append('Duplicate ID: ' + a['id'])
            self.ids.add(a['id'])
        if tag == 'title' and not self.title:
            # Only the document title; inline SVG <title> elements are accessible names.
            self.in_title = True
        if tag == 'h1':
            self.h1 += 1
        if tag == 'meta':
            key = a.get('name', a.get('property', ''))
            self.meta.setdefault(key, []).append(a.get('content', ''))
        if tag == 'link' and a.get('rel') == 'canonical':
            self.canonical.append(a.get('href', ''))
        if tag == 'script' and a.get('type') == 'application/ld+json':
            self.in_json = True
            self.buffer = ''
        if tag == 'img':
            self.images.append(a)
        for key in ['href', 'src', 'poster']:
            if a.get(key):
                self.links.append(a[key])

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
        if tag == 'script' and self.in_json:
            try:
                data = json.loads(self.buffer)
                self.schema.extend(data if isinstance(data, list) else [data])
            except ValueError:
                errors.append('Invalid JSON-LD')
            self.in_json = False

    def handle_data(self, value):
        if self.in_title:
            self.title += value
        if self.in_json:
            self.buffer += value

pages = {}
for path in ROOT.glob('*.html'):
    p = Page()
    p.feed(path.read_text())
    pages[path.name] = p

urls = {x.text for x in ET.parse(ROOT / 'sitemap.xml').getroot().iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')}
expected = {C['base'] + ('' if name == 'index.html' else name) for name in pages}
if urls != expected:
    errors.append('Sitemap differs from published pages')
if len({p.title for p in pages.values()}) != len(pages):
    errors.append('Duplicate titles')
campaigns = {}
for name, p in pages.items():
    def require(ok, message):
        if not ok:
            errors.append(name + ': ' + message)
    require(p.h1 == 1, 'needs one H1')
    require(0 < len(p.title) <= 60, 'title length')
    require(len(p.meta.get('description', [])) == 1 and 0 < len(p.meta['description'][0]) <= 155, 'description length/count')
    require(p.canonical == [C['base'] + ('' if name == 'index.html' else name)], 'canonical mismatch')
    require(p.meta.get('apple-itunes-app') == ['app-id=' + str(C['appId'])], 'wrong Smart App Banner')
    require(bool(p.schema), 'missing schema')
    installs = 0
    for raw in p.links:
        u = urlsplit(raw)
        if u.netloc or u.scheme:
            if u.hostname == 'apps.apple.com' and '/app/' in u.path:
                installs += 1
                q = parse_qs(u.query)
                require(str(C['appId']) in u.path, 'wrong App Store destination')
                require(q.get('pt') == ['127826363'] and q.get('mt') == ['8'] and 0 < len(q.get('ct', [''])[0]) <= 30, 'invalid campaign')
                campaigns.setdefault(q.get('ct', [''])[0], set()).add(name)
            continue
        target = unquote(u.path) or name
        if target.startswith('/'):
            target = target.removeprefix(urlsplit(C['base']).path)
        local = ROOT / target
        require(local.exists(), 'broken link/asset: ' + raw)
        if u.fragment and target in pages:
            require(unquote(u.fragment) in pages[target].ids, 'broken anchor: ' + raw)
    require(installs > 0, 'no install path')
    for img in p.images:
        require(all(x in img for x in ['width', 'height', 'alt']), 'image missing dimensions/alt')
    require(C['base'] + ('' if name == 'index.html' else name) in (ROOT / 'llms.txt').read_text(), 'missing reference coverage')
for tag, names in campaigns.items():
    if len(names) > 1:
        errors.append('Campaign tag reused across pages: ' + tag)

# Guides: hand-written pages listed in discovery.json.
import html as _html, re as _re
text_of = lambda x: _html.unescape(_re.sub(r'<[^>]+>', ' ', x))
for g in C.get('guides', []):
    name = g['file']
    def require(ok, message):
        if not ok:
            errors.append(name + ': ' + message)
    if name not in pages:
        errors.append('Guide missing: ' + name)
        continue
    raw = (ROOT / name).read_text()
    p = pages[name]
    types = {x.get('@type') for x in p.schema}
    require({'Article', 'BreadcrumbList'} <= types, 'needs Article and BreadcrumbList schema')
    visible = _re.findall(r'<h3>(.*?)</h3>', _re.search(r'<h2 id="faq">.*?(?=<aside|$)', raw, _re.S)[0], _re.S) if 'id="faq"' in raw else []
    faq = next((x for x in p.schema if x.get('@type') == 'FAQPage'), None)
    require((faq is None and not visible) or (faq and [q['name'] for q in faq['mainEntity']] == [text_of(v).strip() for v in visible]), 'FAQ schema must match visible questions')
    for q in (faq or {}).get('mainEntity', []):
        require(q['acceptedAnswer']['text'] in text_of(raw), 'FAQ answer not visible: ' + q['name'])
    require(p.title == g['title'], 'title not from discovery.json')
    require(_re.search(r'Updated \d{1,2} \w+ 20\d\d', raw) is not None, 'needs visible Updated date')
    require('href="support.html">Mohamed Elatabany</a>' in raw, 'needs author byline link')
    require('mailto:' in raw, 'needs correction contact')
    require(campaigns.get(g['campaign']) == {name}, 'campaign tag missing or reused: ' + g['campaign'])
    require(raw.count('<!-- discovery-cta-slot -->') >= 1 and 'app-store-badge.svg' in raw and 'discovery-icon.png' in raw, 'needs badge + icon CTA')
    main = _re.search(r'<main.*?</main>', raw, _re.S)[0]
    main = _re.sub(r'(?s)<svg.*?</svg>|<h2 id="sources">.*?</ul>', ' ', main)
    words = len(text_of(main).split())
    require(800 <= words <= 1300, f'useful word count {words} outside 800-1300')
    for other in ('index.html', 'support.html'):
        require(f'href="{name}"' in (ROOT / other).read_text(), 'not linked from ' + other)
    require(C['base'] + name in (ROOT / 'llms-full.txt').read_text(), 'missing from llms-full.txt')

home = pages['index.html']
app = next((s for s in home.schema if s.get('@type') == 'MobileApplication'), None)
if not app or app.get('downloadUrl') != 'https://apps.apple.com/app/id' + str(C['appId']):
    errors.append('Missing or incorrect application entity')
if 'listing is being prepared' in (ROOT / 'index.html').read_text():
    errors.append('Outdated launch status')
if errors:
    print('\n'.join(errors))
    raise SystemExit(1)
print('OK — ' + C['shortName'] + ': metadata, local assets, links, schema, sitemap and App Store campaigns')

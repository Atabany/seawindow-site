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
        if tag == 'title':
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
                require(q.get('pt') == ['127826363'] and q.get('mt') == ['8'] and 0 < len(q.get('ct', [''])[0]) <= 40, 'invalid campaign')
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

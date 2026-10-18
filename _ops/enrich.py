"""Add verified discovery metadata and install paths to a small static app site.

Re-run after the app's policy generator. No network requests; product facts live in
_ops/discovery.json. Privacy/support body text is preserved.
"""
from pathlib import Path
import html
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
C = json.loads((ROOT / '_ops/discovery.json').read_text())
BASE = C['base']
APP = str(C['appId'])
E = html.escape
PAGES = {
    'index.html': (C['title'], C['description']),
    'support.html': (C['shortName'] + ' Support and Contact', 'Get help with ' + C['shortName'] + ', contact the developer and find purchase and app support information.'),
    'privacy.html': (C['shortName'] + ' Privacy Policy', 'Read how ' + C['shortName'] + ' handles app data, device storage and purchase services, and contact the developer about privacy.')
}
STYLE = '''.discovery-download { display:flex; flex-wrap:wrap; align-items:center; gap:12px; margin:20px 0; text-decoration:none; width:fit-content; }
.discovery-download .discovery-icon { width:48px; height:48px; border-radius:11px; }
.discovery-download .discovery-badge { width:120px; height:40px; }
.discovery-facts { margin:24px 0; padding:20px; border:1px solid currentColor; border-radius:14px; }
.discovery-facts p:last-child { margin-bottom:0; }
.discovery-header { max-width:42rem; margin:0 auto; }
'''
(ROOT / 'assets').mkdir(exist_ok=True)
(ROOT / 'assets/discovery.css').write_text(STYLE)

def cta(tag, header=False):
    url = f'https://apps.apple.com/app/apple-store/id{APP}?pt=127826363&ct={tag}&mt=8'
    return ('<div class="discovery-header">' if header else '') + f'<a class="discovery-download" href="{E(url, quote=True)}" aria-label="Download {E(C["shortName"], quote=True)} on the App Store"><img class="discovery-icon" src="assets/discovery-icon.png" width="48" height="48" alt=""><img class="discovery-badge" src="assets/app-store-badge.svg" width="120" height="40" alt="Download on the App Store"></a>' + ('</div>' if header else '')

for name, (title, description) in PAGES.items():
    p = ROOT / name
    s = p.read_text()
    # Replace only our own blocks, and only the metadata fields managed here.
    s = re.sub(r'<!-- discovery-[\w-]+:start -->.*?<!-- discovery-[\w-]+:end -->', '', s, flags=re.S)
    s = re.sub(r'<title>.*?</title>', '<title>' + E(title) + '</title>', s, flags=re.S)
    s = re.sub(r'<link[^>]+rel="canonical"[^>]*>', '', s)
    managed = ['description', 'apple-itunes-app', 'twitter:card', 'twitter:title', 'twitter:description', 'twitter:image']
    for key in managed:
        s = re.sub(r'<meta[^>]+name="' + re.escape(key) + r'"[^>]*>', '', s)
    s = re.sub(r'<meta[^>]+property="og:[^"]*"[^>]*>', '', s)
    url = BASE + ('' if name == 'index.html' else name)
    schema = [{'@context': 'https://schema.org', '@type': 'WebPage', 'name': title, 'url': url, 'description': description, 'author': {'@type': 'Person', 'name': 'Mohamed Elatabany', 'url': 'https://github.com/Atabany'}}]
    if name == 'index.html':
        schema.append({'@context': 'https://schema.org', '@type': 'MobileApplication', '@id': BASE + '#app', 'name': C['storeName'], 'url': BASE, 'downloadUrl': f'https://apps.apple.com/app/id{APP}', 'operatingSystem': 'iOS ' + C['minimumOS'] + '+', 'applicationCategory': C['category'], 'softwareVersion': C['version'], 'image': BASE + 'assets/discovery-icon.png', 'description': C['facts'], 'author': {'@type': 'Person', 'name': 'Mohamed Elatabany', 'url': 'https://github.com/Atabany'}})
    meta = f'<meta name="description" content="{E(description, quote=True)}"><link rel="canonical" href="{url}"><meta name="apple-itunes-app" content="app-id={APP}">'
    for key, value in [('og:type', 'website'), ('og:title', title), ('og:description', description), ('og:url', url), ('og:image', BASE + 'assets/discovery-icon.png')]:
        meta += f'<meta property="{key}" content="{E(value, quote=True)}">'
    meta += '<meta name="twitter:card" content="summary"><link rel="stylesheet" href="assets/discovery.css?v=20261018"><script type="application/ld+json">' + json.dumps(schema, ensure_ascii=False).replace('</', '<\\/') + '</script>'
    s = s.replace('</head>', '<!-- discovery-meta:start -->' + meta + '<!-- discovery-meta:end --></head>')
    tag = C['campaignPrefix'] + '-' + ('home' if name == 'index.html' else Path(name).stem)
    assert len(tag) <= 30
    # Ballast already has campaign badges; preserve those, add missing install routes elsewhere.
    if 'apps.apple.com/app/' not in re.search(r'<header.*?</header>', s, re.S)[0]:
        header_cta = '<!-- discovery-header:start -->' + cta(tag, True) + '<!-- discovery-header:end -->'
        if re.search(r'<header.*?</header>', s, re.S)[0].endswith('</div></header>'):
            s = s.replace('</div></header>', header_cta + '</div></header>', 1)
        else:
            s = s.replace('</header>', header_cta + '</header>', 1)
    if name == 'index.html':
        s = re.sub(r'<p class="muted">DoseJot’s App Store listing is being prepared\..*?</p>', '', s)
        facts = '<aside class="discovery-facts"><h2>App facts</h2><p>' + E(C['facts']) + '</p><p>Made by <a href="https://github.com/Atabany">Mohamed Elatabany</a>. App Store listing checked 18 October 2026.</p></aside>'
        hero_cta = '' if 'class="store-link"' in s.split('</header>', 1)[-1] else cta(tag)
        s = s.replace('</h1>', '</h1><!-- discovery-hero:start -->' + hero_cta + '<!-- discovery-hero:end -->', 1)
        fact_block = '<!-- discovery-facts:start -->' + facts + '<!-- discovery-facts:end -->'
        if '</div></main>' in s:
            s = s.replace('</div></main>', fact_block + '</div></main>', 1)
        elif '</main>' in s:
            s = s.replace('</main>', fact_block + '</main>', 1)
        else:
            at = s.rfind('<nav>')
            s = s[:at] + fact_block + s[at:]
    s = s.replace('alt="Download on the App Store" height="44">', 'alt="Download on the App Store" width="132" height="44">')
    p.write_text(s)

ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
ET.register_namespace('', ns)
sitemap = ET.Element('{' + ns + '}urlset')
for name in PAGES:
    node = ET.SubElement(sitemap, '{' + ns + '}url')
    ET.SubElement(node, '{' + ns + '}loc').text = BASE + ('' if name == 'index.html' else name)
    if name == 'index.html':
        ET.SubElement(node, '{' + ns + '}lastmod').text = '2026-10-18'
ET.indent(sitemap, space='  ')
ET.ElementTree(sitemap).write(ROOT / 'sitemap.xml', encoding='utf-8', xml_declaration=True)
(ROOT / 'robots.txt').write_text('# Project sites use the host-root robots.txt policy. This file documents the intended policy.\nUser-agent: *\nAllow: /\nSitemap: ' + BASE + 'sitemap.xml\n')
summary = '# ' + C['storeName'] + '\n\n> Official app website by Mohamed Elatabany.\n\n' + C['facts'] + '\n\nCanonical App Store listing: https://apps.apple.com/app/id' + APP + '\n\n' + '\n'.join('- [' + title + '](' + BASE + ('' if name == 'index.html' else name) + ')' for name, (title, _) in PAGES.items()) + '\n\nThis reference file is supplementary navigation; it does not establish search ranking or AI recommendations.\n'
(ROOT / 'llms.txt').write_text(summary)
(ROOT / 'llms-full.txt').write_text(summary)
print('Added verified metadata, install links, product facts and discovery files for ' + C['shortName'])

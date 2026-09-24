from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import xml.etree.ElementTree as ET
import json

ROOT = Path(__file__).resolve().parents[1] / 'dist'
class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.h1=0; self.links=[]; self.ids=set(); self.canonical=[]; self.description=[]; self.images=[]; self.title=''; self.in_title=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get('id'): self.ids.add(a['id'])
        if tag=='h1': self.h1+=1
        if tag=='title': self.in_title=True
        if tag=='link' and a.get('rel')=='canonical': self.canonical.append(a.get('href',''))
        if tag=='meta' and a.get('name')=='description': self.description.append(a.get('content',''))
        if tag=='img': self.images.append(a)
        if tag in ('a','img','script','link'):
            u=a.get('href',a.get('src',''))
            if u.startswith(('/', '#')) and not u.startswith('//'): self.links.append(u)
    def handle_endtag(self,tag):
        if tag=='title':self.in_title=False
    def handle_data(self,data):
        if self.in_title:self.title+=data
pages={}
for path in ROOT.rglob('*.html'):
    page=Page();page.feed(path.read_text());pages[path]=page
errors=[];titles={}
for path,page in pages.items():
    name=str(path.relative_to(ROOT))
    if page.h1!=1:errors.append(f'{name}: expected one h1')
    if not page.title:errors.append(f'{name}: missing title')
    if page.title in titles:errors.append(f'{name}: duplicate title with {titles[page.title]}')
    titles[page.title]=name
    if len(page.description)!=1 or not page.description[0]:errors.append(f'{name}: invalid description')
    if len(page.canonical)!=1 or not page.canonical[0].startswith('https://www.lafabricadeclientes.es/'):errors.append(f'{name}: invalid canonical')
    for img in page.images:
        if 'alt' not in img or not img.get('width') or not img.get('height'):errors.append(f'{name}: image missing alt/dimensions')
    for link in page.links:
        u=urlsplit(link);target=ROOT/unquote(u.path.lstrip('/')) if u.path else path
        if target.is_dir():target=target/'index.html'
        if not target.exists():errors.append(f'{name}: missing {link}')
        elif u.fragment and target in pages and unquote(u.fragment) not in pages[target].ids:errors.append(f'{name}: missing anchor {link}')
for loc in ET.parse(ROOT/'sitemap.xml').iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
    target=ROOT/urlsplit(loc.text).path.lstrip('/')/'index.html'
    if not target.exists():errors.append(f'sitemap: missing {loc.text}')
print(json.dumps({'html_pages':len(pages),'errors':errors},ensure_ascii=False,indent=2))
raise SystemExit(bool(errors))

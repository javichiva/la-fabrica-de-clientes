"""Audit the generated static site. Run after npm run build. No network required."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
from collections import Counter
import xml.etree.ElementTree as ET
import json

ROOT = Path(__file__).resolve().parents[1] / 'dist'
ORIGIN = 'https://www.lafabricadeclientes.es'
class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.h1=0; self.links=[]; self.ids=[]; self.canonical=[]; self.meta={}; self.images=[]; self.title=''; self.in_title=False; self.lang=None; self.jsonld=[]; self.json_buffer=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='html': self.lang=a.get('lang')
        if a.get('id'): self.ids.append(a['id'])
        if tag=='h1': self.h1+=1
        if tag=='title': self.in_title=True
        if tag=='link' and a.get('rel')=='canonical': self.canonical.append(a.get('href',''))
        if tag=='meta': self.meta.setdefault(a.get('name',a.get('property','')),[]).append(a.get('content',''))
        if tag=='img': self.images.append(a)
        if tag=='script' and a.get('type')=='application/ld+json': self.json_buffer=''
        if tag in ('a','img','script','link'):
            u=a.get('href',a.get('src',''))
            if u.startswith(('/', '#')) and not u.startswith('//'): self.links.append(u)
    def handle_endtag(self,tag):
        if tag=='title': self.in_title=False
        if tag=='script' and self.json_buffer is not None:
            self.jsonld.append(self.json_buffer); self.json_buffer=None
    def handle_data(self,data):
        if self.in_title:self.title+=data
        if self.json_buffer is not None:self.json_buffer+=data
    @property
    def noindex(self):return any('noindex' in x for x in self.meta.get('robots',[]))

def route(path):
    relative=path.relative_to(ROOT).as_posix()
    return '/' if relative=='index.html' else '/'+relative.removesuffix('index.html')

def target_for(url,source):
    u=urlsplit(url)
    target=ROOT/unquote(u.path.lstrip('/')) if u.path else source
    if target.is_dir():target=target/'index.html'
    return target,u.fragment

files=list(ROOT.rglob('*.html')); errors=[];warnings=[];pages={};titles={};descriptions={}
if not files:errors.append('No generated HTML. Run the build first.')
for path in files:
    page=Page();page.feed(path.read_text());pages[path]=page
sitemap=ET.parse(ROOT/'sitemap.xml')
urls=[x.text for x in sitemap.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
if len(urls)!=len(set(urls)): errors.append('Duplicate sitemap URLs')
indexed=[];unindexed=[]
for path,page in pages.items():
    name=route(path); expected=ORIGIN+('/404/' if name=='/404.html' else name)
    if page.h1!=1:errors.append(f'{name}: expected one h1')
    if page.lang!='es':errors.append(f'{name}: invalid document language')
    if not page.title.strip():errors.append(f'{name}: missing title')
    if page.title in titles:errors.append(f'{name}: duplicate title with {titles[page.title]}')
    titles[page.title]=name
    description=page.meta.get('description',[])
    if len(description)!=1 or not description[0].strip():errors.append(f'{name}: invalid description')
    elif not page.noindex:
        if description[0] in descriptions:errors.append(f'{name}: duplicate description')
        descriptions[description[0]]=name
    if page.canonical!=[expected]:errors.append(f'{name}: canonical does not match route: {page.canonical}')
    if page.meta.get('og:url')!=[expected]:errors.append(f'{name}: inconsistent og:url')
    for field in ['viewport','og:title','og:description','og:type','og:image','og:locale','twitter:card']:
        if len(page.meta.get(field,[]))!=1 or not page.meta[field][0]:errors.append(f'{name}: invalid {field}')
    for key,count in Counter(page.ids).items():
        if count>1:errors.append(f'{name}: duplicate id {key}')
    for img in page.images:
        if 'alt' not in img or not img.get('width','').isdigit() or not img.get('height','').isdigit():errors.append(f'{name}: image missing alt/dimensions')
    for link in page.links:
        target,fragment=target_for(link,path)
        if not target.exists():errors.append(f'{name}: missing {link}')
        elif fragment and target in pages and unquote(fragment) not in pages[target].ids:errors.append(f'{name}: missing anchor {link}')
    for image in page.meta.get('og:image',[]):
        if not image.startswith(ORIGIN+'/'):errors.append(f'{name}: invalid social image origin')
        elif not (ROOT/urlsplit(image).path.lstrip('/')).is_file():errors.append(f'{name}: missing social image')
    objects=[]
    for raw in page.jsonld:
        try:objects.append(json.loads(raw))
        except json.JSONDecodeError:errors.append(f'{name}: invalid JSON-LD')
    if not any(o.get('@type')=='Organization' for o in objects):errors.append(f'{name}: missing Organization')
    if not page.noindex and name!='/':
        crumbs=[o for o in objects if o.get('@type')=='BreadcrumbList']
        if len(crumbs)!=1:errors.append(f'{name}: missing breadcrumbs schema')
        elif crumbs[0]['itemListElement'][-1]['item']!=expected:errors.append(f'{name}: breadcrumb URL mismatch')
    if name.startswith('/blog/') and name!='/blog/' and not page.noindex:
        posts=[o for o in objects if o.get('@type')=='BlogPosting']
        if len(posts)!=1:errors.append(f'{name}: missing BlogPosting')
        elif posts[0].get('mainEntityOfPage')!=expected:errors.append(f'{name}: article URL mismatch')
    if page.noindex:
        unindexed.append(name)
        if expected in urls:errors.append(f'{name}: noindex URL in sitemap')
    else:
        indexed.append(name)
        if expected not in urls:errors.append(f'{name}: indexable URL missing from sitemap')
for url in urls:
    if not url.startswith(ORIGIN+'/') or not url.endswith('/'):errors.append(f'sitemap: invalid URL {url}')
    target,_=target_for(url,ROOT/'index.html')
    if target not in pages:errors.append(f'sitemap: missing page {url}')
robots=(ROOT/'robots.txt').read_text()
if 'Sitemap: '+ORIGIN+'/sitemap.xml' not in robots:errors.append('Invalid robots sitemap')
if 'Disallow: /\n' in robots:errors.append('Production robots blocks entire site')
if ROOT/'404.html' not in pages or not pages[ROOT/'404.html'].noindex:errors.append('404 must be noindex')
report={'html_pages':len(pages),'indexable_pages':len(indexed),'sitemap_urls':len(urls),'noindex_pages':unindexed,'errors':errors,'warnings':warnings}
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(bool(errors))

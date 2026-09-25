"""Create a non-indexable subdirectory preview without changing production dist."""
from pathlib import Path
import re
import shutil

root = Path(__file__).resolve().parents[1]
target = root / 'preview-dist'
if target.exists():
    shutil.rmtree(target)
shutil.copytree(root / 'dist', target)
prefix = '/preview-astro'
for path in target.rglob('*'):
    if path.suffix not in ('.html', '.css', '.js'):
        continue
    text = path.read_text()
    if path.suffix == '.html':
        text = re.sub(r'((?:href|src|action|poster)=["\'])/(?!/)', lambda m: m[1] + prefix + '/', text)
        text = re.sub(r'<meta\s+name="robots"[^>]*>', '', text)
        text = text.replace('</head>', '<meta name="robots" content="noindex, nofollow"/></head>')
    text = re.sub(r'(url\(["\']?)/(?!/)', lambda m: m[1] + prefix + '/', text)
    path.write_text(text)
(target / '.htaccess').write_text('''Options -Indexes
DirectoryIndex index.html
ErrorDocument 404 /preview-astro/404.html
<IfModule mod_rewrite.c>
RewriteEngine Off
</IfModule>
<IfModule mod_headers.c>
Header always set X-Robots-Tag "noindex, nofollow"
</IfModule>
''')
(target / '.fabrica-preview').write_text('la-fabrica-de-clientes preview v1\n')
# Production sitemap must not be served as a preview sitemap.
(target / 'sitemap.xml').unlink(missing_ok=True)
(target / 'robots.txt').write_text('User-agent: *\nDisallow: /\n')
print('Preview prepared at /preview-astro/; production build unchanged.')

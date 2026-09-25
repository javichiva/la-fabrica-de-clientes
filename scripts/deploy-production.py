"""Stage the build, retain a web-blocked previous release, then switch root files.
Does not access/drop the WordPress database. No recursive FTP deletion.
"""
import ftplib
import io
import os
from pathlib import Path
import ssl
import time
import urllib.request
import urllib.error

HOST = 'host.cpseo16.eu'
SITE = 'https://www.lafabricadeclientes.es'
root = Path(__file__).resolve().parents[1] / 'dist'
run = os.environ.get('GITHUB_RUN_ID', str(int(time.time()))) + '-' + os.environ.get('GITHUB_RUN_ATTEMPT', '1')
stage = '/_fabrica-stage/' + run
backup = '/_fabrica-backups/' + run
protected = {'_fabrica-stage', '_fabrica-backups', 'preview-astro', '.well-known', 'cgi-bin', '.ftpquota'}
deny = b'Options -Indexes\n<IfModule mod_rewrite.c>\nRewriteEngine On\nRewriteRule ^ - [F,L]\n</IfModule>\nRequire all denied\n'
if os.environ.get('FTP_USERNAME') != 'info@lafabricadeclientes.es':
    raise SystemExit('Unexpected FTP account; stopping.')
if not os.environ.get('FTP_PASSWORD') or not (root/'index.html').is_file() or not (root/'.htaccess').is_file():
    raise SystemExit('Missing credentials or production build.')
if 'noindex' in (root/'index.html').read_text():
    raise SystemExit('Homepage has noindex; stopping.')

def ensure(ftp, path):
    ftp.cwd('/')
    for part in path.strip('/').split('/'):
        try:
            ftp.cwd(part)
        except ftplib.error_perm:
            ftp.mkd(part)
            ftp.cwd(part)

def blocked(path):
    try:
        with urllib.request.urlopen(SITE+path+'?check='+run, timeout=30) as response:
            raise RuntimeError('Backup protection check failed; stopping before cutover.')
    except urllib.error.HTTPError as error:
        if error.code != 403:
            raise RuntimeError('Backup must return HTTP 403 before cutover.') from None

with ftplib.FTP_TLS(context=ssl.create_default_context(), timeout=60) as ftp:
    ftp.connect(HOST,21)
    ftp.login(os.environ['FTP_USERNAME'],os.environ['FTP_PASSWORD'])
    ftp.prot_p()
    ftp.cwd('/')
    original = [name for name, facts in ftp.mlsd() if name not in ('.','..') and facts.get('type') not in ('cdir','pdir') and name not in protected]
    for parent in ('/_fabrica-backups','/_fabrica-stage'):
        ensure(ftp,parent)
        ftp.storbinary('STOR .htaccess',io.BytesIO(deny))
    ensure(ftp,backup+'/original')
    ftp.storbinary('STOR protection-check.txt',io.BytesIO(b'access must be denied'))
    blocked(backup+'/original/protection-check.txt')
    ensure(ftp,stage)
    files = sorted(p for p in root.rglob('*') if p.is_file())
    for i,path in enumerate(files,1):
        relative=path.relative_to(root)
        ensure(ftp,stage+'/'+str(relative.parent) if str(relative.parent)!='.' else stage)
        with path.open('rb') as source:
            ftp.storbinary('STOR '+relative.name,source)
        ftp.voidcmd('TYPE I')
        if ftp.size(relative.name)!=path.stat().st_size:
            raise RuntimeError('Uploaded file size mismatch; cutover not started.')
        if i%15==0: print(f'Staged {i}/{len(files)} files.',flush=True)
    ftp.cwd(stage)
    ftp.storbinary('STOR .fabrica-production',io.BytesIO((run+'\n').encode()))
    incoming = [p.name for p in root.iterdir()]+['.fabrica-production']
    # Keep the previous configuration and homepage until the end of the switch.
    original.sort(key=lambda name: name in ('.htaccess','index.php','index.html'))
    incoming.sort(key=lambda name: name in ('.htaccess','index.html'))
    moved=[]
    installed=[]
    try:
        for name in original:
            saved = 'original-htaccess' if name=='.htaccess' else name
            ftp.rename('/'+name,backup+'/original/'+saved)
            moved.append((name,saved))
        for name in incoming:
            ftp.rename(stage+'/'+name,'/'+name)
            installed.append(name)
        blocked(backup+'/original/protection-check.txt')
        with urllib.request.urlopen(SITE+'/?release='+run,timeout=30) as response:
            html=response.read().decode()
            if response.status!=200 or 'Buen negocio.' not in html or 'noindex' in response.headers.get('X-Robots-Tag',''):
                raise RuntimeError('Production homepage verification failed.')
    except Exception:
        print('Cutover failed; restoring previous root files.',flush=True)
        for name in reversed(installed): ftp.rename('/'+name,stage+'/'+name)
        for name,saved in reversed(moved): ftp.rename(backup+'/original/'+saved,'/'+name)
        raise
    print('Production verified. Previous root files retained in protected backup. Database untouched.',flush=True)
with open(os.environ.get('GITHUB_STEP_SUMMARY',os.devnull),'a') as summary:
    summary.write(f'## Production published\n{SITE}/\n\nPrevious files: `{backup}/original/` (HTTP access blocked). Database untouched.\n')

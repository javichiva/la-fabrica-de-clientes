"""Upload only the isolated preview directory over certificate-validated FTPS."""
import ftplib
import io
import os
from pathlib import Path
import ssl

HOST = 'host.cpseo16.eu'
DIRECTORY = 'preview-astro'
MARKER = b'la-fabrica-de-clientes preview v1\n'
root = Path(__file__).resolve().parents[1] / 'preview-dist'
if os.environ.get('FTP_USERNAME') != 'info@lafabricadeclientes.es':
    raise SystemExit('FTP_USERNAME must be the confirmed account info@lafabricadeclientes.es.')
if not os.environ.get('FTP_PASSWORD') or (root / '.fabrica-preview').read_bytes() != MARKER:
    raise SystemExit('Missing password or invalid preview build.')
with ftplib.FTP_TLS(context=ssl.create_default_context(), timeout=60) as ftp:
    ftp.connect(HOST, 21)
    ftp.login(os.environ['FTP_USERNAME'], os.environ['FTP_PASSWORD'])
    ftp.prot_p()
    ftp.cwd('/')
    entries = {name.rstrip('/').rsplit('/', 1)[-1] for name in ftp.nlst()}
    if DIRECTORY in entries:
        ftp.cwd(DIRECTORY)
        existing = io.BytesIO()
        try:
            ftp.retrbinary('RETR .fabrica-preview', existing.write)
        except ftplib.error_perm:
            raise SystemExit('Existing preview directory is not managed by this project; stopping.')
        if existing.getvalue() != MARKER:
            raise SystemExit('Preview ownership marker does not match; stopping.')
    else:
        ftp.mkd(DIRECTORY)
        ftp.cwd(DIRECTORY)
        ftp.storbinary('STOR .fabrica-preview', io.BytesIO(MARKER))
    remote_root = ftp.pwd()
    count = 0
    # Headers first; homepage last. Never remove server files or write outside preview.
    files = sorted((p for p in root.rglob('*') if p.is_file()), key=lambda p: (p == root / 'index.html', p.relative_to(root).as_posix()))
    for path in files:
        relative = path.relative_to(root)
        ftp.cwd(remote_root)
        for part in relative.parts[:-1]:
            try:
                ftp.cwd(part)
            except ftplib.error_perm:
                ftp.mkd(part)
                ftp.cwd(part)
        with path.open('rb') as source:
            ftp.storbinary('STOR ' + relative.name, source)
        count += 1
    print(f'Preview uploaded: {count} files. WordPress unchanged.')
with open(os.environ.get('GITHUB_STEP_SUMMARY', os.devnull), 'a') as summary:
    summary.write('## Preview published\nhttps://www.lafabricadeclientes.es/preview-astro/\n\nWordPress unchanged. Preview excluded from indexing.\n')

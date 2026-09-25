"""Integration checks against an isolated PHP server, never the live inbox."""
import hashlib
import http.cookiejar
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='fabrica-manager-test-') as directory:
    work = Path(directory)
    public = work / 'public'
    public.mkdir()
    shutil.copytree(root/'public/gestor', public/'gestor')
    (public/'_fabrica-private').mkdir()
    password = 'Test-only-private-password-2026'
    salt = 'unit-test-salt'
    settings = {'salt':salt, 'iterations':600000, 'hash':hashlib.pbkdf2_hmac('sha256',password.encode(),salt.encode(),600000).hex()}
    (public/'_fabrica-private/auth.json').write_text(json.dumps(settings))
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        port = sock.getsockname()[1]
    base = f'http://127.0.0.1:{port}'
    log = open(work/'php.log', 'w+')
    server = subprocess.Popen(['php','-S',f'127.0.0.1:{port}','-t',str(public)],stdout=log,stderr=log)
    jar = http.cookiejar.CookieJar()
    client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    def request(path='/gestor/', fields=None, headers=None, browser=client):
        req = urllib.request.Request(base+path, data=urllib.parse.urlencode(fields).encode() if fields is not None else None, headers=headers or {})
        try: response = browser.open(req,timeout=10)
        except urllib.error.HTTPError as e: response = e
        return response.status, response.read().decode(), response.headers
    def csrf(html): return re.search(r'name="csrf" value="([a-f0-9]+)"',html)[1]
    try:
        for _ in range(50):
            try:
                status, html, headers = request()
                break
            except urllib.error.URLError: time.sleep(.1)
        assert status == 200 and 'Hola, Javier.' in html
        assert headers['Cache-Control'] == 'no-store, private' and 'noindex' in headers['X-Robots-Tag']
        assert 'HttpOnly' in headers['Set-Cookie'] and 'SameSite=Strict' in headers['Set-Cookie']
        token=csrf(html)
        assert request('/gestor/contacto.php')[0] == 405
        payload={'nombre':'Test <script>alert(1)</script>', 'empresa':'Empresa <b>prueba</b>', 'email':'test@example.com','telefono':'+34600000000','web':'https://example.com','inversion':'Entre 10.000 y 20.000 €','objetivo':'Queremos mejorar la captación de clientes de nuestra empresa de prueba.'}
        assert request('/gestor/contacto.php',payload,{'Origin':'https://evil.example'})[0] == 403
        assert request('/gestor/contacto.php',{**payload,'email':'invalid'}, {'Accept':'application/json'})[0] == 422
        assert request('/gestor/contacto.php',{**payload,'direccion_fax':'spam'}, {'Accept':'application/json'})[0] == 400
        status, body, _=request('/gestor/contacto.php',payload, {'Accept':'application/json'})
        assert status == 201 and json.loads(body)['ok']
        # A browser retry must not create a second lead.
        assert request('/gestor/contacto.php',payload, {'Accept':'application/json'})[0] == 201
        store=work/'.fabrica-manager/store.json'
        data=json.loads(store.read_text()); assert len(data['leads'])==1
        lead=next(iter(data['leads'].values())); lead_id=lead['id']
        assert str(public) not in str(store)
        assert os.stat(store).st_mode & 0o777 == 0o600
        assert 'Empresa &lt;b&gt;' not in request('/gestor/?id='+lead_id)[1]
        assert request(fields={'action':'login','password':password,'csrf':'invalid'})[0] == 403
        assert request(fields={'action':'login','password':'wrong','csrf':token})[0] == 401
        status,html,_=request(fields={'action':'login','password':password,'csrf':token})
        assert status == 200 and 'Tus consultas.' in html and 'Empresa &lt;b&gt;prueba&lt;/b&gt;' in html
        assert any(c.name=='fabrica_manager' for c in jar)
        token=csrf(html)
        status,html,_=request('/gestor/?id='+lead_id)
        assert status==200 and '&lt;script&gt;alert(1)&lt;/script&gt;' in html and '<script>alert(1)</script>' not in html
        update={'action':'save','csrf':token,'id':lead_id,'status':'contactado','notes':'Notas privadas <script>bad()</script>','version':'1'}
        assert request(fields={**update,'csrf':'bad'})[0] == 403
        assert request(fields=update,headers={'Origin':'https://evil.example'})[0] == 403
        status,html,_=request(fields=update); assert status==200 and 'Cambios guardados.' in html
        assert json.loads(store.read_text())['leads'][lead_id]['status']=='contactado'
        assert request(fields=update)[0]==409
        assert 'No hay coincidencias.' in request('/gestor/?estado=nuevo')[1]
        assert request(fields={**update,'action':'delete','version':'2'})[0]==422
        assert request(fields={**update,'action':'delete','version':'2','confirm_delete':'yes'})[0]==200
        assert not json.loads(store.read_text())['leads']
        assert request(fields={'action':'logout','csrf':token})[0]==200
        assert 'Hola, Javier.' in request()[1]
        # Brute-force limits remain effective across anonymous sessions.
        _,html,_=request(); token=csrf(html)
        for _ in range(7): status,_,_=request(fields={'action':'login','password':'wrong','csrf':token})
        assert status==429
        # Public form limits fail visibly, rather than claiming a successful save.
        request('/gestor/contacto.php',payload, {'Accept':'application/json'})
        assert request('/gestor/contacto.php',payload, {'Accept':'application/json'})[0]==429
        # Preserve data on unexpected/corrupt input instead of silently resetting storage.
        store.write_text('{broken')
        assert request('/gestor/contacto.php',payload, {'Accept':'application/json'})[0]==503
        assert store.read_text()=='{broken'
        print('PASS: form persistence, validation, duplicate retry, private login, CSRF, XSS escaping, status/notes, stale edits, delete, logout, rate limits and corrupt-storage protection.')
    finally:
        server.terminate(); server.wait(timeout=5)
        log.close()

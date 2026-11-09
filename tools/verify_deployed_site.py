#!/usr/bin/env python3
"""Read back a deployed Studio bundle; reject stale or corrupted uploads."""
import hashlib
import json
from pathlib import Path
import sys
from urllib.request import Request,urlopen
from urllib.parse import urljoin
base=sys.argv[1].rstrip('/')+'/'
local=json.loads((Path(__file__).resolve().parents[1]/'Pinball/build/studio/build.json').read_text())
def get(name):
    request=Request(urljoin(base,name),headers={'Cache-Control':'no-cache'})
    with urlopen(request,timeout=60) as response:return response.read(),response.headers.get_content_type()
raw,_=get('build.json');live=json.loads(raw)
assert live['sourceHash']==local['sourceHash'],'Published source hash differs'
assert live['artifacts']==local['artifacts'],'Published artifact manifest differs'
for name,expected in local['artifacts'].items():
    if name=='.htaccess':continue # Apache configuration is deliberately not served.
    raw,mime=get(name)
    assert hashlib.sha256(raw).hexdigest()==expected,f'Wrong artifact: {name}'
    if name.endswith('.wasm'):assert mime=='application/wasm',f'Wrong WASM MIME: {mime}'
print(f'Verified {len(local["artifacts"])} published artifacts: {base}')

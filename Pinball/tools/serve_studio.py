#!/usr/bin/env python3
"""Serve the static editor locally; the server runs no game or USB bridge."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import subprocess
import sys
import webbrowser
from urllib.parse import parse_qs,urlsplit,urlencode
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
GAME=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--port',type=int,default=8765);p.add_argument('--open',action='store_true');p.add_argument('--no-build',action='store_true',help='Check and reuse the verified static bundle');a=p.parse_args()
    subprocess.run([sys.executable,str(GAME/'tools/build_studio.py'),*(['--check'] if a.no_build else [])],check=True)
    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            request=urlsplit(self.path)
            if request.path!='/api/pinball-release':
                return super().do_GET()
            # The deployed worker accepts the production site's origins.
            # Local development forwards only this project's public cart URL.
            value=parse_qs(request.query).get('url',[''])[0]
            asset=urlsplit(value)
            if (asset.scheme!='https' or asset.netloc!='github.com' or
                not asset.path.startswith('/juliendorra/chgame-pinball/releases/download/') or
                not asset.path.endswith('.chgame') or asset.query or asset.fragment):
                self.send_error(400,'Expected a Pinball GitHub release cart')
                return
            endpoint='https://chgame-release-relay.juliendorra.workers.dev/api/github-release?'+urlencode({'url':value})
            try:
                upstream=Request(endpoint,headers={'User-Agent':self.headers.get('User-Agent','Pinball-Studio')})
                with urlopen(upstream,timeout=30) as response:
                    body=response.read(64*1024*1024+1)
                    if len(body)>64*1024*1024:
                        self.send_error(502,'Package exceeds 64 MiB')
                        return
                    self.send_response(200)
                    self.send_header('Content-Type','application/octet-stream')
                    self.send_header('Content-Length',str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
            except HTTPError as error:
                self.send_error(error.code,'Release download failed')
            except URLError:
                self.send_error(502,'Release relay unavailable')
        def end_headers(self):
            self.send_header('Cache-Control','no-cache');super().end_headers()
    server=ThreadingHTTPServer(('127.0.0.1',a.port),partial(Handler,directory=str(GAME/'build/studio')))
    url=f'http://127.0.0.1:{a.port}/';print('Static Pinball Studio: '+url,flush=True)
    if a.open:webbrowser.open(url)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=='__main__':main()

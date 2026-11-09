#!/usr/bin/env python3
"""Serve the static editor locally; the server runs no game or USB bridge."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import subprocess
import sys
import webbrowser
GAME=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--port',type=int,default=8765);p.add_argument('--open',action='store_true');p.add_argument('--no-build',action='store_true',help='Check and reuse the verified static bundle');a=p.parse_args()
    subprocess.run([sys.executable,str(GAME/'tools/build_studio.py'),*(['--check'] if a.no_build else [])],check=True)
    class Handler(SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header('Cache-Control','no-cache');super().end_headers()
    server=ThreadingHTTPServer(('127.0.0.1',a.port),partial(Handler,directory=str(GAME/'build/studio')))
    url=f'http://127.0.0.1:{a.port}/';print('Static Pinball Studio: '+url,flush=True)
    if a.open:webbrowser.open(url)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=='__main__':main()

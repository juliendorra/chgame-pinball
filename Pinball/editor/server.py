#!/usr/bin/env python3
"""Native diagnostic harness and compatibility launcher for static Studio.

Run: .venv/bin/python Pinball/editor/server.py
Only loopback is bound. Browser mutation requests must come from this origin.
"""
import argparse
import base64
from collections import deque
import hashlib
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
import json
import os
from pathlib import Path
import queue
import socket
import struct
import sys
import threading
import time
from urllib.parse import urlsplit

HERE=Path(__file__).resolve().parent;GAME=HERE.parent;ROOT=GAME.parent
sys.path.insert(0,str(ROOT/'CHGame/tools/chsim'))
sys.path.insert(0,str(GAME/'tools'))
from chsim import build
from chdrivelib import Driver,SimTransport,SerialTransport
from boards import encode,image
from protocol import LiveClient,decode
from fat import BoardCard

class KeyQueue:
    """Keep short taps observable for one frame, without repeating held keys."""
    def __init__(self):
        self.pending=deque();self.latest=self.mask=0;self.at=0
    def push(self,mask,now):
        mask=int(mask)&255;self.at=now
        if mask!=self.latest:
            self.pending.append(mask);self.latest=mask
            # Bound a stalled client to at most half a second of input.
            if len(self.pending)>30:self.pending.clear();self.latest=self.mask=0
    def sample(self,now):
        if now-self.at>.5:self.pending.clear();self.latest=self.mask=0
        elif self.pending:self.mask=self.pending.popleft()
        return self.mask

class Device:
    def __init__(self):self.client=None;self.transport=None;self.port=None;self.lock=threading.RLock()
    def ports(self):
        from serial.tools import list_ports
        return [dict(path=p.device,name=p.description) for p in list_ports.comports() if p.vid==0x16c0 and p.pid==0x27dd]
    def connect(self,path=None):
        with self.lock:
            if self.client:return {'connected':True,'port':self.port}
            ports=self.ports()
            if path is None and len(ports)==1:path=ports[0]['path']
            if path not in [p['path'] for p in ports]:raise ValueError('Select a connected CHGame')
            t=SerialTransport(path);t.s.timeout=.2
            try:
                client=LiveClient(t);client.hello()
            except Exception:
                t.close();raise RuntimeError('CHGame did not answer. Install Pinball 1.4, then reconnect.')
            self.client=client;self.transport=t;self.port=path
            return {'connected':True,'port':path}
    def close(self):
        with self.lock:
            if self.transport:
                try:self.client.request('X')
                except Exception:pass
                self.transport.close()
            self.transport=self.client=self.port=None
    def action(self,op,args):
        with self.lock:
            if op=='connect':return self.connect(args.get('port'))
            if op=='disconnect':self.close();return {'connected':False}
            if not self.client:raise ValueError('Connect CHGame first')
            c=self.client
            if op=='boards':
                result=c.boards()
                for entry in result:entry['board']=decode(c.board(entry['index']),entry['file'])
                return result
            if op=='upload':
                data=encode(args['board']);c.upload(data)
                if c.board()!=data:raise IOError('CHGame RAM readback differs')
                return {'bytes':len(data),'verified':True}
            if op=='save':
                data=encode(args['board']);c.request('I');result=BoardCard(c).save(args['board']['file'],data)
                c.request('L');c.upload(data)
                return result
            if op=='state':return c.state()
            if op=='pause':c.request(f"Q {int(bool(args.get('paused')))}");return {'ok':True}
            if op=='keys':c.request(f"K {int(args.get('mask',0))&255}");return {'ok':True}
            if op=='restart':c.request('R');return {'ok':True}
            if op=='place':c.request(f"P {int(args['x'])},{int(args['y'])}");return {'ok':True}
            raise ValueError('Unknown device operation')

class Session:
    def __init__(self,exe,board):
        self.t=SimTransport(exe);self.d=Driver(self.t,'MPIN');self.live=LiveClient(self.t)
        self.d.handshake();self.d.frames(1);self.load(board)
    def load(self,board):self.live.upload(encode(board));self.board=board
    def state(self):
        line=self.d.query('V','PIN ')
        return {k:int(v) for k,v in (p.split('=') for p in line.split()[1:])}
    def overview(self):
        self.t.send('H');header=self.d.expect('OVERVIEW ');n=int(header.split()[1]);data=self.t.read(n);self.d.expect('OK');return data
    def frame(self,mask):
        self.d.buttons(mask);self.d.frames(1)
        state=self.state();shot=self.d.shot();overview=self.overview()
        metadata=json.dumps({'state':state,'height':self.board['height'],'headerHeight':24,'lcdBytes':len(shot)}).encode()
        return struct.pack('<I',len(metadata))+metadata+shot+overview
    def close(self):
        try:self.d.buttons(0)
        except Exception:pass
        rc=self.t.close();self.t.p.stdout.close();self.t.p.stderr.close()
        if rc or any('BUG:' in line for line in self.t.bugs):print('Simulator diagnostic:',self.t.bugs,file=sys.stderr)

class Server(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,address,exe,boards):
        self.exe=exe;self.boards=boards;self.device=Device();super().__init__(address,Handler)

class Handler(SimpleHTTPRequestHandler):
    protocol_version='HTTP/1.1'
    def __init__(self,*a,**k):super().__init__(*a,directory=str(HERE),**k)
    def log_message(self,fmt,*args):
        if args and ('/api/' in str(args[0]) or '404' in str(args)):super().log_message(fmt,*args)
    def end_headers(self):
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        super().end_headers()
    def valid_origin(self):
        host=self.headers.get('Host','');origin=self.headers.get('Origin')
        expected={f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
        return host in expected and (not origin or origin in {f'http://{h}' for h in expected})
    def json(self,result,status=200):
        data=json.dumps(result).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    def do_GET(self):
        if not self.valid_origin():return self.json({'error':'Local origin required'},403)
        path=urlsplit(self.path).path
        if path=='/api/boards':return self.json(self.server.boards)
        if path=='/api/device':return self.json({'connected':self.server.device.client is not None,'port':self.server.device.port,'ports':self.server.device.ports()})
        if path=='/api/health':return self.json({'engine':'CHGame native C++','version':'1.4','ready':True})
        if path=='/live':return self.websocket()
        if path=='/assets/elements.json':return self.json(json.loads((GAME/'sprites/element_sprites.json').read_text()))
        if path=='/assets/borders.json':return self.json(json.loads((GAME/'sprites/board_borders.json').read_text()))
        # Serve editor assets only; do not expose arbitrary repository files.
        if path.startswith('/api/'):return self.json({'error':'Not found'},404)
        return super().do_GET()
    def do_POST(self):
        if not self.valid_origin() or self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.json({'error':'Same-origin JSON required'},403)
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<65536:raise ValueError('Request too large')
            args=json.loads(self.rfile.read(length));path=urlsplit(self.path).path
            if path=='/api/validate':return self.json({'bytes':len(encode(args['board']))})
            if path=='/api/export':return self.json({'hex':encode(args['board']).hex()})
            if path=='/api/import':return self.json(decode(bytes.fromhex(args['hex']),args.get('file','IMPORT')))
            if path.startswith('/api/device/'):return self.json(self.server.device.action(path.rsplit('/',1)[-1],args))
            return self.json({'error':'Unknown operation'},404)
        except Exception as e:return self.json({'error':str(e)},400)
    def ws_send(self,payload,opcode=1):
        if isinstance(payload,str):payload=payload.encode()
        n=len(payload);head=bytes([128|opcode,n]) if n<126 else bytes([128|opcode,126])+struct.pack('!H',n) if n<65536 else bytes([128|opcode,127])+struct.pack('!Q',n)
        self.connection.sendall(head+payload)
    def ws_receive(self):
        def read(n):
            data=self.rfile.read(n)
            if len(data)!=n:raise EOFError()
            return data
        first,second=read(2);n=second&127
        if n==126:n=struct.unpack('!H',read(2))[0]
        elif n==127:n=struct.unpack('!Q',read(8))[0]
        if n>65536 or not second&128 or not first&128:raise ValueError('Unsupported WebSocket frame')
        mask=read(4);data=read(n);data=bytes(b^mask[i%4] for i,b in enumerate(data))
        return first&15,data
    def websocket(self):
        if self.headers.get('Upgrade','').lower()!='websocket':return self.json({'error':'WebSocket required'},400)
        key=self.headers.get('Sec-WebSocket-Key','')
        if len(key)>64:return self.json({'error':'Bad WebSocket key'},400)
        self.send_response(101);self.send_header('Upgrade','websocket');self.send_header('Connection','Upgrade');self.send_header('Sec-WebSocket-Accept',base64.b64encode(hashlib.sha1((key+'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest()).decode());self.end_headers()
        commands=queue.Queue(maxsize=128);alive=threading.Event();alive.set()
        def reader():
            try:
                while alive.is_set():
                    op,payload=self.ws_receive()
                    if op==8:break
                    if op==1:commands.put(json.loads(payload),timeout=1)
            except (OSError,EOFError,ValueError,queue.Full):pass
            finally:alive.clear()
        threading.Thread(target=reader,daemon=True).start();session=None
        try:
            session=Session(self.server.exe,self.server.boards[-1]);keys=KeyQueue();deadline=time.monotonic()
            self.ws_send(json.dumps({'type':'ready','engine':'Same C++ physics + renderer as CHGame'}))
            while alive.is_set():
                pending_board=None
                while not commands.empty():
                    message=commands.get();op=message.get('type')
                    try:
                        if op=='board':pending_board=message
                        elif op=='keys':keys.push(message['mask'],time.monotonic())
                        elif op=='restart':session.live.request('R')
                        elif op=='place':session.live.request(f"P {int(message['x'])},{int(message['y'])}")
                        elif op=='pause':session.d.buttons(64);session.d.frames(1);session.d.buttons(0)
                    except Exception as e:self.ws_send(json.dumps({'type':'error','error':str(e),'revision':message.get('revision')}))
                if pending_board:
                    try:
                        session.load(pending_board['board']);self.ws_send(json.dumps({'type':'applied','revision':pending_board['revision']}))
                    except Exception as e:self.ws_send(json.dumps({'type':'error','error':str(e),'revision':pending_board.get('revision')}))
                self.ws_send(session.frame(keys.sample(time.monotonic())),2)
                deadline+=1/60;delay=deadline-time.monotonic()
                if delay>0:time.sleep(delay)
                elif delay<-.1:deadline=time.monotonic()
        except (OSError,EOFError,TimeoutError,RuntimeError) as e:print('Editor session:',e,file=sys.stderr)
        finally:
            alive.clear()
            if session:session.close()
            self.close_connection=True

def main():
    # Compatibility entry point; Session/KeyQueue remain for native diagnostics.
    from serve_studio import main as static_main
    static_main()
if __name__=='__main__':main()

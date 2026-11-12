"""PBT data and the identical release/simulator live protocol."""
from pathlib import Path
import struct
import sys
import time
import threading

GAME=Path(__file__).resolve().parents[1]
ROOT=GAME.parent
sys.path.insert(0,str(GAME/'tools'))
from boards import encode,KINDS,checksum,HEADER_BYTES
NAMES=list(KINDS)

def decode(data,filename='CUSTOM'):
    if len(data)<HEADER_BYTES or data[:4]!=b'PBT2':raise ValueError('Not a PBT2 board')
    magic,version,theme,count,flags,height,gravity,ident,high,reserved,crc,title,mission,*pal=struct.unpack_from('<4sBBBBHHIHHI20s24s16H',data)
    if version!=2 or reserved or flags & ~1 or len(data)!=HEADER_BYTES+12*count or checksum(data)!=crc:raise ValueError('Invalid PBT size, version or checksum')
    ident|=high<<32
    board=dict(file=filename.removesuffix('.PBT'),id=ident,title=title.split(b'\0')[0].decode('ascii'),mission=mission.split(b'\0')[0].decode('ascii'),theme=theme,height=height,gravity=gravity,palette=[f'{v:03X}' for v in pal],objects=[])
    if flags: board["flags"]=flags
    for at in range(HEADER_BYTES,len(data),12):
        kind,group,x,y,u,v,value=struct.unpack_from('<BBhhhhH',data,at)
        if kind>=len(NAMES):raise ValueError('Unknown element')
        board['objects'].append(dict(kind=NAMES[kind],group=group,x=x,y=y,u=u,v=v,value=value))
    encode(board)
    return board

def fnv(data):
    h=2166136261
    for b in data:h=((h^b)*16777619)&0xffffffff
    return h

class LiveClient:
    def __init__(self,transport):self.t=transport;self.lock=threading.RLock();self.debug=hasattr(transport,"p")
    def request(self,text):
        with self.lock:
            self.t.send('@'+text)
            lines=[]
            for _ in range(130):
                line=self.t.readline()
                if line.startswith('LIVE ERR'):
                    if self.debug:self.t.readline()
                    raise RuntimeError('CHGame refused '+text.split()[0])
                if line.startswith('LIVE BOARD '):lines.append(line)
                elif line.startswith('LIVE '):
                    if self.debug:
                        ack=self.t.readline()
                        if not ack.startswith('OK'):raise RuntimeError('Simulator refused the live command')
                    return lines+[line]
            raise RuntimeError('CHGame did not answer the live protocol')
    def hello(self):
        reply=self.request('?')[-1]
        if not reply.startswith('LIVE HELLO 1.4'):raise RuntimeError('Install Pinball 1.4 or newer to connect')
        return reply
    def upload(self,data,raw_block=None):
        with self.lock:
            self.request(f'B {len(data)}' if raw_block is None else f'W {raw_block}')
            for offset in range(0,len(data),32):self.request(f'D {offset} {data[offset:offset+32].hex()}')
            self.request('C' if raw_block is None else f'F {fnv(data)}')
    def board(self,index=None):
        return bytes.fromhex(self.request('T' if index is None else f'G {index}')[-1].removeprefix('LIVE DATA '))
    def boards(self):
        lines=self.request('L');result=[]
        for line in lines:
            if line.startswith('LIVE BOARD '):
                _,_,index,name=line.split(maxsplit=3)
                result.append(dict(index=int(index),file=name.strip()))
        return result
    def read(self,lba):return bytes.fromhex(self.request(f'S {lba}')[-1].removeprefix('LIVE DATA '))
    def write(self,lba,data):
        if len(data)!=512:raise ValueError('A card sector must be 512 bytes')
        self.upload(data,raw_block=lba)

    def state(self):
        names=['id','score','lives','ticks','xq','yq','vx','vy','left','right','shooter','camera','zoom','paused','frames']
        values=list(map(int,self.request('V')[-1].split()[2:]))
        if len(values)!=len(names):raise ValueError('Unexpected CHGame state reply')
        return dict(zip(names,values))

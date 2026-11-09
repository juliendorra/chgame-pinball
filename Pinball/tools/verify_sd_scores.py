#!/usr/bin/env python3
"""Restart the actual game against namespaced SD scores; legacy files stay ignored."""
from pathlib import Path
import importlib.util,json,os,struct,sys,zlib
G=Path(__file__).resolve().parents[1];R=G.parent
sys.path[:0]=[str(Path(__file__).resolve().parents[2]/'tools'),str(R/'CHGame/tools/chsim'),str(R/'chgame-sd-saves/tools'),str(R/'CHGame/platform/board/arduino/CHGame/libraries/CHSd/tools')]
from sd_saves import overlay
import prepare
from fatimg import build_image,FatVolume
from chsim import build
from chdrivelib import Driver,SimTransport
O=G/'out/sd-scores';O.mkdir(parents=True,exist_ok=True)
os.environ['CHSIM_CHGAME']=str(overlay()/'CHGame/src')
os.environ['CHSIM_FLAGS']=f'-fsanitize=undefined,bounds -fsanitize-ignorelist={G}/tools/sanitizer.ignore -fno-sanitize-recover=all'
exe=build(G,out=O/'sim-scores');ID='com.juliendorra.pinball';NAME=prepare.filename(ID)
NEON,PIRATE=1297088769,1297088776

def payload(rows,muted=0):
 b=bytearray(196)
 for i,(ident,score) in enumerate(rows):struct.pack_into('<II',b,i*8,ident,score)
 b[192]=muted;return b

def journal(data,generation=1,version=1):
 b=bytearray(512);struct.pack_into('<IIHBBI',b,0,prepare.RECORD_TAG,generation,196,version,0,0)
 b[16:212]=data;struct.pack_into('<I',b,508,zlib.crc32(b[:508]));return prepare.descriptor(ID,1)+b+b'\xff'*512

OLD=b'legacy data must stay untouched'
def fresh(raw):
 p=O/'card.img';build_image(p,{NAME:raw,'MPIN.SAV':OLD,'OTHER.TXT':b'keep this exactly'},fs='fat16',spc=1,clusters=5000,mbr=True);return p

def boot(card,play=False):
 os.environ['CHGAME_SAVE_CARD']=str(card)
 t=SimTransport(exe);d=Driver(t,'MPIN')
 try:
  d.handshake();d.frames(1);d.cmd('F 0')
  if play:d.cmd('O 50000');d.cmd('F 0')
  return {k:int(v) for k,v in (p.split('=') for p in d.query('V','PIN ').split()[1:])}
 finally:assert t.close()==0 and not t.bugs,t.bugs

def raw_file(card):
 with FatVolume(card) as v:
  assert v.read_file('OTHER.TXT')==b'keep this exactly' and v.read_file('MPIN.SAV')==OLD
  return v.read_file(NAME)

def read(card):
 raw=raw_file(card);prepare.validate(raw,ID);valid=[]
 for i in range(2):
  p=raw[512+i*512:1024+i*512]
  if p[:4]==b'CSV3' and zlib.crc32(p[:508])==struct.unpack_from('<I',p,508)[0]:valid.append((struct.unpack_from('<I',p,4)[0],p[16:212]))
 data=max(valid)[1];rows=[struct.unpack_from('<II',data,i*8) for i in range(24)]
 assert len([ident for ident,score in rows if ident])==len({ident for ident,score in rows if ident})
 return {ident:score for ident,score in rows if ident},data,raw

initial=journal(payload([(0,0),(NEON,10680)],muted=1));card=fresh(initial);s=boot(card)
rows,data,raw=read(card);assert rows=={NEON:10680} and data[192]==1 and s['sound']==0
assert raw==initial  # Loading never rewrites a valid journal.
s=boot(card,play=True);assert read(card)[0][s['id']]==50000
assert boot(card)['best']==50000
blank=prepare.blank(ID);card=fresh(blank);boot(card);assert raw_file(card)==blank
raw=journal(payload([(NEON,77777)],muted=1),version=2);card=fresh(raw);boot(card);assert raw_file(card)==raw
report=dict(result='passed',id=ID,filename=NAME,checks=['preferences and scores retained','no write on boot','actual table-change save','restart persistence','legacy file ignored and unchanged','unknown schema preserved','unrelated file unchanged'])
(O/'report.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS:',', '.join(report['checks']))

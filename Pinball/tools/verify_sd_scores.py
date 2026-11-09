#!/usr/bin/env python3
"""Restart the actual game against real SD journals and legacy flash fixtures."""
from pathlib import Path
import json,os,struct,sys,zlib
G=Path(__file__).resolve().parents[1];R=G.parent
sys.path[:0]=[str(R/'tools'),str(R/'CHGame/tools/chsim'),str(R/'CHGame/platform/board/arduino/CHGame/libraries/CHSd/tools')]
from sd_saves import overlay,validate
from fatimg import build_image,FatVolume
from chsim import build
from chdrivelib import Driver,SimTransport
O=G/'out/sd-scores';O.mkdir(parents=True,exist_ok=True)
os.environ['CHSIM_CHGAME']=str(overlay()/'CHGame/src')
os.environ['CHSIM_FLAGS']=f'-fsanitize=undefined,bounds -fsanitize-ignorelist={G}/tools/sanitizer.ignore -fno-sanitize-recover=all'
exe=build(G,out=O/'sim-scores');magic=int.from_bytes(b'MPIN','little')
NEON,PIRATE=1297088769,1297088776

def payload(rows,muted=0,marker=0):
 b=bytearray(196)
 for i,(ident,score) in enumerate(rows):struct.pack_into('<II',b,i*8,ident,score)
 b[192]=muted;b[193]=marker;return b

def journal(data,generation=1,version=1):
 b=bytearray(512);struct.pack_into('<IIHBBI',b,0,magic,generation,196,version,0,0x31565343)
 b[16:212]=data;struct.pack_into('<I',b,508,zlib.crc32(b[:508]));return b+b'\xff'*512

def legacy(data):
 b=bytearray(b'\xff'*512);struct.pack_into('<IBBH',b,0,magic,1,0,9);b[8:204]=data
 struct.pack_into('<I',b,204,zlib.crc32(b[:204]));return b

def fresh(raw):
 p=O/'card.img';build_image(p,{'MPIN.SAV':raw,'OTHER.TXT':b'keep this exactly'},fs='fat16',spc=1,clusters=5000,mbr=True);return p

def boot(card,flash,play=False):
 os.environ['CHGAME_SAVE_CARD']=str(card);os.environ['CHGAME_LEGACY_FLASH']=str(flash)
 t=SimTransport(exe);d=Driver(t,'MPIN')
 try:
  d.handshake();d.frames(1);d.cmd('F 0')
  if play:d.cmd('O 50000');d.cmd('F 0') # real table transition calls remember()
  s={k:int(v) for k,v in (p.split('=') for p in d.query('V','PIN ').split()[1:])}
  return s
 finally:
  assert t.close()==0 and not t.bugs,t.bugs

def read(card):
 with FatVolume(card) as v:
  assert v.read_file('OTHER.TXT')==b'keep this exactly';raw=v.read_file('MPIN.SAV')
 validate(raw,magic);valid=[]
 for i in range(2):
  p=raw[i*512:(i+1)*512]
  if zlib.crc32(p[:508])==struct.unpack_from('<I',p,508)[0]:valid.append((struct.unpack_from('<I',p,4)[0],p[16:212]))
 data=max(valid)[1];rows=[struct.unpack_from('<II',data,i*8) for i in range(24)]
 assert len([ident for ident,score in rows if ident])==len({ident for ident,score in rows if ident})
 return {ident:score for ident,score in rows if ident},data,raw

flash=O/'legacy.bin';flash.write_bytes(legacy(payload([(NEON,15000),(PIRATE,2500)],muted=0)));original_flash=flash.read_bytes()
# Include a hole before an existing ID to catch accidental duplicate insertion.
card=fresh(journal(payload([(0,0),(NEON,10680)],muted=1)));s=boot(card,flash)
rows,data,raw=read(card);assert rows=={NEON:15000,PIRATE:2500},rows
assert data[192:194]==bytes([1,0x53]) and s['sound']==0
assert flash.read_bytes()==original_flash
# The completed migration must not resurrect a later/different flash record.
flash.write_bytes(legacy(payload([(NEON,999999),(PIRATE,999999)],muted=0)))
boot(card,flash);assert read(card)[2]==raw
# Actual gameplay saving uses SD and survives a new simulator process.
s=boot(card,flash,play=True);assert read(card)[0][s['id']]==50000
assert boot(card,flash)['best']==50000
# A blank journal imports the legacy payload and its original preference.
flash.write_bytes(original_flash);card=fresh(b'\xff'*1024);boot(card,flash)
rows,data,raw=read(card);assert rows=={NEON:15000,PIRATE:2500} and data[192:194]==bytes([0,0x53])
assert flash.read_bytes()==original_flash
# Unknown schema is not replaced at boot by defaults or old flash data.
raw=journal(payload([(NEON,77777)],muted=1),version=2);card=fresh(raw);boot(card,flash)
with FatVolume(card) as v:assert v.read_file('MPIN.SAV')==raw
report=dict(result='passed',checks=['merge per-table maxima','no duplicates across holes','preserve SD preferences','one-time migration','legacy flash unchanged','actual table-change save','restart persistence','blank SD import','unknown schema preserved','unrelated file unchanged'])
(O/'report.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS:',', '.join(report['checks']))

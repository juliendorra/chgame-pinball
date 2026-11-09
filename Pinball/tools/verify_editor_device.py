#!/usr/bin/env python3
"""Exercise the actual release live protocol and SD writer over CHGame USB."""
import argparse
import copy
import json
from pathlib import Path
import sys
import time

GAME=Path(__file__).resolve().parents[1];ROOT=GAME.parent
sys.path.insert(0,str(GAME/'editor'));sys.path.insert(0,str(ROOT/'CHGame/tools/chsim'))
from protocol import LiveClient,encode,decode,fnv
from fat import BoardCard
from chdrivelib import SerialTransport

def main():
 p=argparse.ArgumentParser();p.add_argument('--port',required=True);a=p.parse_args();out=GAME/'out/device/v1.4';out.mkdir(parents=True,exist_ok=True)
 report={'checks':[],'result':'running'}
 def check(value,label,details=None):
  if not value:raise AssertionError(label+': '+str(details))
  report['checks'].append({'check':label,'details':details});print('PASS:',label,details or '',flush=True)
 t=SerialTransport(a.port);c=LiveClient(t)
 try:
  report['hello']=c.hello();entries=c.boards();before={e['file']:c.board(e['index']) for e in entries if e['index'] and e['file']!='EDITLAB'}
  check(len(before)>=9,'retrieve every existing SD board',list(before))
  templates=json.loads((GAME/'boards/tables.json').read_text());b=copy.deepcopy(templates[-1]);b.update(file='EDITLAB',id=0x7f000001,title='Editor Device Lab')
  c.upload(encode(b));check(c.board()==encode(b),'release RAM upload and exact readback')
  c.request('Q 1');c.request('P 64,180');old=c.state();b['objects'][0]['x']+=2;c.upload(encode(b));new=c.state()
  check(all(old[k]==new[k] for k in ('xq','yq','vx','vy','score','lives','ticks','paused')),'live edit preserves paused ball, score, lives and clock')
  good=c.board();bad=bytearray(good);bad[-1]^=1
  try:c.upload(bad);raise AssertionError('corrupt upload accepted')
  except RuntimeError:pass
  check(c.board()==good,'corrupt PBT never replaces the running board')
  c.request('Q 0');c.request('K 18');time.sleep(.12);s=c.state();check(s['left']==255 and s['right']==255,'browser key packet drives both flipper sides',s)
  c.request('K 0');time.sleep(.12);s=c.state();check(s['left']==0 and s['right']==0,'key release returns both flippers')
  c.request('K 16');time.sleep(.7);check(c.state()['left']==0,'lost heartbeat releases a held flipper')
  c.request('R');c.request('K 1');time.sleep(.1);c.request('K 0');time.sleep(.12);check(not c.state()['shooter'],'browser launch key launches the physical ball')
  first=c.state();start=time.monotonic();time.sleep(1);last=c.state();fps=(last['frames']-first['frames'])/(time.monotonic()-start);check(57<=fps<=63,'release live build maintains 60 Hz',round(fps,2));report['release_fps']=round(fps,2)
  c.request('I');big=copy.deepcopy(b);big['objects']=(big['objects']*4)[:72]
  check(len(big['objects'])==72,'maximum board fixture has 72 elements')
  BoardCard(c).save('EDITLAB',encode(big))
  b['objects'].append(dict(kind='bumper',x=54,y=206,u=7,v=260,group=1,value=250));result=BoardCard(c).save('EDITLAB',encode(b));report['sd']=result
  entries=c.boards();index=next(e['index'] for e in entries if e['file']=='EDITLAB');check(c.board(index)==encode(b),'new board survives SD save, resize, rescan and native FAT reload',result)
  after={e['file']:c.board(e['index']) for e in entries if e['index'] and e['file'] in before}
  check(after==before,'all original SD board bytes are unchanged')
  c.upload(encode(b));c.request('Q 0');c.request('R');report['result']='passed';report['board']=b
 except Exception as e:report['result']='failed';report['error']=repr(e);raise
 finally:
  try:c.request('K 0')
  except Exception:pass
  t.close();(out/'editor-hardware.json').write_text(json.dumps(report,indent=2)+'\n')
 print('All release editor/USB/SD checks passed.',flush=True)
if __name__=='__main__':main()

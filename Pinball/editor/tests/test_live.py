import copy
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import time
import unittest

HERE=Path(__file__).resolve().parents[1];GAME=HERE.parent;ROOT=GAME.parent
sys.path.insert(0,str(HERE));sys.path.insert(0,str(GAME/'tools'));sys.path.insert(0,str(ROOT/'CHGame/platform/board/arduino/CHGame/libraries/CHSd/tools'))
from protocol import encode,decode,LiveClient
from server import Session
from fat import BoardCard
from fatimg import build_image,FatVolume as Reader
BOARDS=json.loads((GAME/'boards/tables.json').read_text())

class Blocks:
 def __init__(self,path):self.f=open(path,'r+b');self.fail_sector=None
 def read(self,lba):self.f.seek(lba*512);return self.f.read(512)
 def write(self,lba,data):
  if lba==self.fail_sector:raise IOError('Injected sector failure')
  self.f.seek(lba*512);self.f.write(data);self.f.flush()
 def close(self):self.f.close()

class CardTests(unittest.TestCase):
 def read_file(self,path,name):
  with Reader(path) as reader:return reader.read_file(name)
 def make(self,folder=True,fs='fat16',mbr=True):
  tmp=tempfile.TemporaryDirectory(dir=GAME/'out/editor');self.addCleanup(tmp.cleanup);path=Path(tmp.name)/'card.img'
  files={'KEEP.DAT':b'Existing unrelated file\x00'*93,'GAMES/KEEP.CHG':b'preserve this game'*150}
  if folder:files['PINBALL/ORIGINAL.PBT']=encode(BOARDS[0])
  build_image(path,files,fs=fs,mbr=mbr,spc=1)
  blocks=Blocks(path);self.addCleanup(blocks.close);return path,blocks
 def test_formats_clone_resize_directory_growth_and_preserve(self):
  for fs in ('fat16','fat32'):
   for mbr in (False,True):
    with self.subTest(fs=fs,mbr=mbr):
     path,blocks=self.make(fs=fs,mbr=mbr);card=BoardCard(blocks)
     big=copy.deepcopy(BOARDS[0]);big['objects']=(big['objects']*5)[:72];large=encode(big)
     self.assertEqual(len(large),964)
     card.save('ORIGINAL',large);card.save('ORIGINAL',encode(BOARDS[8]))
     for i in range(20):card.save(f'CLONE{i:02}',encode(BOARDS[i%9]))
     # Independent existing FAT reader verifies the writer and all chains.
     reader=Reader(path);self.addCleanup(reader.close)
     self.assertEqual(reader.read_file('PINBALL/ORIGINAL.PBT'),encode(BOARDS[8]))
     self.assertEqual(reader.read_file('PINBALL/CLONE19.PBT'),encode(BOARDS[1]))
     self.assertEqual(reader.read_file('KEEP.DAT'),b'Existing unrelated file\x00'*93)
     self.assertEqual(reader.read_file('GAMES/KEEP.CHG'),b'preserve this game'*150)
 def test_create_missing_folder(self):
  path,blocks=self.make(folder=False);BoardCard(blocks).save('NEWBOARD',encode(BOARDS[2]));self.assertEqual(self.read_file(path,'PINBALL/NEWBOARD.PBT'),encode(BOARDS[2]))
 def test_validation_precedes_any_mutation(self):
  path,blocks=self.make();before=path.read_bytes();card=BoardCard(blocks)
  with self.assertRaises(ValueError):card.save('../FAIL',encode(BOARDS[0]))
  bad=bytearray(encode(BOARDS[0]));bad[-1]^=1
  with self.assertRaises(ValueError):card.save('FAIL',bad)
  self.assertEqual(path.read_bytes(),before)
 def test_failed_data_write_keeps_old_board(self):
  path,blocks=self.make();card=BoardCard(blocks);folder=card.folder();old=card.find(folder,b'ORIGINALPBT');free=next(n for n in range(2,card.cluster_count+2) if not card.get(n));blocks.fail_sector=card.sector(free)
  with self.assertRaises(IOError):card.save('ORIGINAL',encode(BOARDS[8]))
  self.assertEqual(self.read_file(path,'PINBALL/ORIGINAL.PBT'),encode(BOARDS[0]))
 def test_failed_directory_commit_keeps_old_board(self):
  path,blocks=self.make();card=BoardCard(blocks);old=card.find(card.folder(),b'ORIGINALPBT');blocks.fail_sector=old[0]
  with self.assertRaises(IOError):card.save('ORIGINAL',encode(BOARDS[8]))
  self.assertEqual(self.read_file(path,'PINBALL/ORIGINAL.PBT'),encode(BOARDS[0]))

class NativeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.exe=GAME/'out/editor/pinball-studio'
  if not cls.exe.exists():raise unittest.SkipTest('Start the editor once to build the real native engine')
 def setUp(self):
  os.environ['CHSD_CARD']=str(GAME/'out/editor/boards.img');self.s=Session(self.exe,BOARDS[8]);self.addCleanup(self.s.close)
 def test_live_edit_preserves_ball_score_and_clock(self):
  s=self.s;s.d.frames(1);s.d.cmd('J 61,340,0,300');s.d.cmd('O 10000');before=s.state();b=copy.deepcopy(BOARDS[8]);b['objects'][0]['x']+=3;s.load(b);after=s.state()
  for key in ('xq','yq','vx','vy','score','lives','ticks'):self.assertEqual(after[key],before[key],key)
  s.d.frames(2);self.assertGreater(s.state()['ticks'],before['ticks']);self.assertEqual(s.live.board(),encode(b))
 def test_corrupt_partial_oversize_and_out_of_order_transfers_are_atomic(self):
  s=self.s;before=s.live.board();data=bytearray(before);data[-1]^=1
  with self.assertRaises(RuntimeError):s.live.upload(data)
  self.assertEqual(s.live.board(),before)
  s.live.request('B 336')
  with self.assertRaises(RuntimeError):s.live.request('D 32 0000')
  with self.assertRaises(RuntimeError):s.live.request('C')
  with self.assertRaises(RuntimeError):s.live.request('B 965')
  self.assertEqual(s.live.board(),before)
 def test_blank_board_and_theme_switch_use_real_renderer(self):
  s=self.s;b=copy.deepcopy(BOARDS[8]);b['objects']=[];s.load(b);s.d.frames(1);self.assertEqual(s.state()['objects'],0)
  for theme in range(9):
   b['theme']=theme;b['palette']=BOARDS[theme]['palette'];s.load(b);s.d.frames(1);data=s.overview();self.assertEqual(len(data),(b['height']+24)*64+32)
 def test_added_kickback_is_armed_and_theme_edits_preserve_capture(self):
  s=self.s;b=copy.deepcopy(BOARDS[8]);b['objects']=[];s.load(b);s.d.frames(1)
  b['objects']=[dict(kind='kickback',x=25,y=160,u=6,v=0,group=0,value=500)];s.load(b);s.d.cmd('J 25,160,0,100');s.d.frames(1);self.assertEqual(s.state()['kickbacks'],1)
  s.load(BOARDS[8]);s.d.frames(1);scoop=next(o for o in BOARDS[8]['objects'] if o['kind']=='scoop');s.d.cmd(f"J {scoop['x']},{scoop['y']},0,0");s.d.frames(1);held=s.state()['hold'];self.assertGreater(held,0)
  b=copy.deepcopy(BOARDS[8]);b['theme']=7;b['palette']=BOARDS[7]['palette'];s.load(b);self.assertEqual(s.state()['hold'],held)
 def test_full_board_render_does_not_advance_physics(self):
  s=self.s;s.d.frames(1);before=s.state()
  for _ in range(5):s.overview()
  self.assertEqual(s.state(),before)
 def test_three_simultaneous_controls_and_focus_release(self):
  s=self.s;s.d.buttons(16|2|1);s.d.frames(6);state=s.state();self.assertEqual((state['left'],state['right'],state['launch_held']),(255,255,1));s.d.buttons(0);s.d.frames(1);self.assertFalse(s.state()['shooter'])

if __name__=='__main__':unittest.main(verbosity=2)

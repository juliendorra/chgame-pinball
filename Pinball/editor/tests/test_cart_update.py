import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from update_cart_live import CartCard
import test_live as helpers
from test_live import Blocks,build_image
import chgpack
class CartUpdate(unittest.TestCase):
 make=helpers.CardTests.make
 read_file=helpers.CardTests.read_file
 def test_atomic_cart_replacement_and_data_failure(self):
  old=chgpack.pack(b'\x55'*32768,'MIDNIGHT PINBALL',version='old')
  payload=chgpack.pack(bytes(range(256))*160,'MIDNIGHT PINBALL',version='test')
  for fs in ('fat16','fat32'):
   path,blocks=self.make(fs=fs)
   blocks.close();build_image(path,{'GAMES/MIDNIGHT.CHG':old,'GAMES/KEEP.CHG':b'keep unchanged','PINBALL/KEEP.PBT':b'keep board'},fs=fs,mbr=True,spc=1)
   blocks=Blocks(path);self.addCleanup(blocks.close);card=CartCard(blocks)
   free=next(n for n in range(2,card.cluster_count+2) if card.get(n)==0);blocks.fail_sector=card.sector(free)
   with self.assertRaises(IOError):card.install(payload)
   self.assertEqual(self.read_file(path,'GAMES/MIDNIGHT.CHG'),old)
   self.assertEqual(card.get(free),0)
   blocks.fail_sector=None;report=CartCard(blocks).install(payload);self.assertTrue(report['uncached_readback'])
   self.assertEqual(self.read_file(path,'GAMES/MIDNIGHT.CHG'),payload)
   self.assertEqual(self.read_file(path,'GAMES/KEEP.CHG'),b'keep unchanged');self.assertEqual(self.read_file(path,'PINBALL/KEEP.PBT'),b'keep board')

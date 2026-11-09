import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server import KeyQueue

class InputEdges(unittest.TestCase):
    def test_short_shake_taps_survive_frame_coalescing(self):
        q=KeyQueue()
        for mask in [1,0,32,0]*3:q.push(mask,1)
        self.assertEqual([q.sample(1+i/60) for i in range(12)],[1,0,32,0]*3)
        self.assertEqual(q.sample(1.3),0)
    def test_heartbeat_and_timeout(self):
        q=KeyQueue();q.push(1,1)
        for _ in range(10):q.push(1,1.1)
        self.assertEqual(len(q.pending),1)
        self.assertEqual(q.sample(1.11),1)
        self.assertEqual(q.sample(1.2),1)
        self.assertEqual(q.sample(1.7),0)
        q.push(1,2);self.assertEqual(q.sample(2),1)
    def test_stalled_input_is_bounded_and_releases(self):
        q=KeyQueue()
        for i in range(1000):q.push(i%2,1)
        self.assertLessEqual(len(q.pending),30)
        self.assertEqual(q.sample(2),0)

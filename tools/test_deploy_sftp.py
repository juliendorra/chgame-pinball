"""Exercise confinement and publication failure behavior without a server."""
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from deploy_sftp import artifacts,confined,publish
class Fake:
    def __init__(self,escape=False,corrupt=False):
        self.escape=escape;self.corrupt=corrupt;self.files={'KEEP.txt':b'unrelated','index.html':b'old'};self.renames=[]
    def normalize(self,path):return '/parent' if self.escape and path=='..' else '/'
    def put(self,local,remote,confirm):self.files[remote]=Path(local).read_bytes()+(b'bad' if self.corrupt else b'')
    def open(self,path,mode):return io.BytesIO(self.files[path])
    def posix_rename(self,source,target):self.renames.append(target);self.files[target]=self.files.pop(source)
    def remove(self,path):
        if path not in self.files:raise FileNotFoundError(path)
        del self.files[path]
class Deploy(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.folder=Path(self.temp.name)
        files={'index.html':b'new','engine-version.wasm':b'wasm'}
        for name,data in files.items():(self.folder/name).write_bytes(data)
        (self.folder/'build.json').write_text(json.dumps({'artifacts':{n:hashlib.sha256(d).hexdigest() for n,d in files.items()}}))
    def tearDown(self):self.temp.cleanup()
    def test_confined_publication_preserves_other_files(self):
        server=Fake();publish(server,self.folder)
        self.assertEqual(server.files['KEEP.txt'],b'unrelated')
        self.assertEqual(server.files['index.html'],b'new')
        self.assertEqual(server.renames[-2:],['index.html','build.json'])
    def test_escape_stops_before_upload(self):
        server=Fake(escape=True)
        with self.assertRaisesRegex(RuntimeError,'leave'):publish(server,self.folder)
        self.assertEqual(server.files,{'KEEP.txt':b'unrelated','index.html':b'old'})
    def test_corrupt_upload_preserves_live_index(self):
        server=Fake(corrupt=True)
        with self.assertRaisesRegex(RuntimeError,'readback'):publish(server,self.folder)
        self.assertEqual(server.files,{'KEEP.txt':b'unrelated','index.html':b'old'})
        self.assertEqual(server.renames,[])
    def test_local_hash_mismatch_stops_before_upload(self):
        (self.folder/'index.html').write_bytes(b'changed');server=Fake()
        with self.assertRaises(ValueError):publish(server,self.folder)
        self.assertEqual(server.renames,[])
    def test_parent_path_is_rejected(self):
        (self.folder/'build.json').write_text(json.dumps({'artifacts':{'../escape':'0'*64}}))
        with self.assertRaises(ValueError):artifacts(self.folder)
if __name__=='__main__':unittest.main()

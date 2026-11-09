"""Test namespace boundaries and publication failures without network access."""
import errno
import hashlib
import io
import json
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from paramiko.sftp import CMD_OPENDIR,CMD_HANDLE,CMD_CLOSE
from deploy_sftp import TARGET,artifacts,publish
class Message:
    def get_binary(self):return b'handle'
class Fake:
    def __init__(self,escape=False,corrupt=False,parent_mode=0o755,extra_home=False):
        self.escape=escape;self.corrupt=corrupt;self.parent_mode=parent_mode;self.extra_home=extra_home
        self.files={'KEEP.txt':b'unrelated','index.html':b'old'};self.renames=[];self.cwd=None
    def normalize(self,path):return TARGET['sftpHome']
    def lstat(self,path):
        return SimpleNamespace(st_mode=stat.S_IFDIR|self.parent_mode,st_uid=0 if path=='/home' else 1001)
    def listdir(self,path):return [TARGET['username']]+(['other-account'] if self.extra_home else [])
    def chdir(self,path):self.cwd=path
    def _request(self,kind,*args):
        if kind==CMD_CLOSE:return 0,None
        if kind!=CMD_OPENDIR:raise AssertionError('Probe must never read directory contents')
        if not self.escape:raise PermissionError(errno.EACCES,'denied')
        return CMD_HANDLE,Message()
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
    def test_readonly_container_and_private_home_can_publish(self):
        server=Fake();publish(server,self.folder)
        self.assertEqual(server.files['KEEP.txt'],b'unrelated')
        self.assertEqual(server.files['index.html'],b'new')
        self.assertEqual(server.renames[-2:],['index.html','build.json'])
        self.assertEqual(server.cwd,TARGET['sftpHome'])
    def test_actual_outside_access_stops_before_upload(self):
        server=Fake(escape=True)
        with self.assertRaisesRegex(RuntimeError,'outside'):publish(server,self.folder)
        self.assertEqual(server.files,{'KEEP.txt':b'unrelated','index.html':b'old'})
    def test_writable_parent_is_rejected(self):
        server=Fake(parent_mode=0o777)
        with self.assertRaisesRegex(RuntimeError,'writable'):publish(server,self.folder)
        self.assertEqual(server.renames,[])
    def test_other_visible_home_is_rejected(self):
        server=Fake(extra_home=True)
        with self.assertRaisesRegex(RuntimeError,'other account'):publish(server,self.folder)
        self.assertEqual(server.renames,[])
    def test_wrong_login_home_is_rejected(self):
        server=Fake();server.normalize=lambda path:'/home/primary'
        with self.assertRaisesRegex(RuntimeError,'Unexpected'):publish(server,self.folder)
        self.assertEqual(server.renames,[])
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

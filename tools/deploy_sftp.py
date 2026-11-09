#!/usr/bin/env python3
"""Publish only a validated static bundle through pinned-host, confined SFTP."""
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import stat
import uuid
ROOT=Path(__file__).resolve().parents[1]
TARGET=json.loads((ROOT/'tools/deploy-target.json').read_text())

def directory_access(sftp,path):
    # Open/close a directory without READDIR: no sibling names or files read.
    from paramiko.sftp import CMD_OPENDIR,CMD_HANDLE,CMD_CLOSE
    try:
        kind,message=sftp._request(CMD_OPENDIR,path)
    except OSError as error:
        if error.errno in (2,13):return False
        raise
    if kind!=CMD_HANDLE:raise RuntimeError('Unexpected SFTP directory response')
    sftp._request(CMD_CLOSE,message.get_binary())
    return True

def confined(sftp):
    import posixpath
    home=posixpath.normpath(sftp.normalize('.'))
    if home!=TARGET['sftpHome']:raise RuntimeError('Unexpected SFTP login namespace; no files uploaded')
    parent=posixpath.dirname(home);info=sftp.lstat(parent);own=sftp.lstat(home)
    # OVH exposes a shared /home container above each isolated virtual home.
    # That container must be root-owned, non-writable by this account, and
    # expose exactly this account's home, rather than other site directories.
    if (not stat.S_ISDIR(info.st_mode) or not stat.S_ISDIR(own.st_mode) or info.st_uid!=0 or own.st_uid==0
            or info.st_mode & 0o022):
        raise RuntimeError('SFTP parent is writable or unexpected; no files uploaded')
    names=set(sftp.listdir(parent))-set(('.', '..'))
    if names!={posixpath.basename(home)}:
        raise RuntimeError('SFTP exposes other account namespaces; no files uploaded')
    for path in ('/','/../..','/home/juliendo','/home/juliendo-today','/home/juliendo/www','/www'):
        if directory_access(sftp,path):
            raise RuntimeError('SFTP can open an outside directory; no files uploaded')
    sftp.chdir(home)
    print('SFTP namespace verified: own home only; parent read-only; root and other accounts denied.')
    return home

def artifacts(folder):
    manifest=json.loads((folder/'build.json').read_text())
    files={**manifest['artifacts'],'build.json':hashlib.sha256((folder/'build.json').read_bytes()).hexdigest()}
    for name,digest in files.items():
        path=PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or str(path)!=name:
            raise ValueError('Unsafe artifact path')
        local=folder/name
        if not local.resolve().is_relative_to(folder.resolve()) or local.is_symlink() or not local.is_file() or hashlib.sha256(local.read_bytes()).hexdigest()!=digest:
            raise ValueError('Invalid local artifact: '+name)
    return files

def publish(sftp,folder):
    files=artifacts(folder);confined(sftp)
    # Immutable engine files first; entry document and manifest last.
    order=sorted(files,key=lambda name:(name in ('index.html','build.json'),name=='build.json',name))
    pending=[]
    try:
        for name in order:
            parent=PurePosixPath(name).parent
            for index in range(1,len(parent.parts)+1):
                part=str(PurePosixPath(*parent.parts[:index]))
                try:info=sftp.lstat(part)
                except FileNotFoundError:sftp.mkdir(part,mode=0o755);info=sftp.lstat(part)
                if not stat.S_ISDIR(info.st_mode):raise RuntimeError('Remote parent is not a real directory')
            temp=name+'.upload-'+uuid.uuid4().hex
            pending.append(temp)
            sftp.put(str(folder/name),temp,confirm=True)
            with sftp.open(temp,'rb') as remote:actual=hashlib.sha256(remote.read()).hexdigest()
            if actual!=files[name]:raise RuntimeError('SFTP readback differs: '+name)
        # Complete readback succeeds before replacing any live file.
        for name,temp in zip(order,pending):sftp.posix_rename(temp,name)
    finally:
        for temp in pending:
            try:sftp.remove(temp)
            except OSError:pass
    print(f'Published {len(files)} verified files through encrypted, confined SFTP.')

def main():
    import paramiko
    with paramiko.SSHClient() as client:
        client.load_host_keys(str(ROOT/'tools/deploy_known_hosts'))
        client.set_missing_host_key_policy(paramiko.RejectPolicy())
        if os.environ['FTP_SERVER']!=TARGET['host'] or os.environ['FTP_USERNAME']!=TARGET['username']:
            raise RuntimeError('Deployment must use the dedicated Pinball host and account')
        client.connect(os.environ['FTP_SERVER'],port=22,username=os.environ['FTP_USERNAME'],
                       password=os.environ['FTP_PASSWORD'],allow_agent=False,look_for_keys=False,
                       timeout=30,banner_timeout=30,auth_timeout=30)
        with client.open_sftp() as sftp:publish(sftp,ROOT/'Pinball/build/studio')
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Read-only SFTP boundary probe: open/close directories, never list or read files."""
import os
import posixpath
from pathlib import Path
import paramiko
from paramiko.sftp import CMD_OPENDIR,CMD_HANDLE,CMD_CLOSE
ROOT=Path(__file__).resolve().parents[1]
with paramiko.SSHClient() as client:
    client.load_host_keys(str(ROOT/'tools/deploy_known_hosts'))
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    client.connect(os.environ['FTP_SERVER'],port=22,username=os.environ['FTP_USERNAME'],
                   password=os.environ['FTP_PASSWORD'],allow_agent=False,look_for_keys=False,
                   timeout=30,banner_timeout=30,auth_timeout=30)
    with client.open_sftp() as sftp:
        home=posixpath.normpath(sftp.normalize('.'))
        print('Canonical login directory:',home)
        escaped=False
        for path in ('.','..','/','/../..'):
            try:
                canonical=posixpath.normpath(sftp.normalize(path))
                # Paramiko 5.1's listdir implementation uses these same requests;
                # stop before READDIR so no names or file contents are retrieved.
                kind,message=sftp._request(CMD_OPENDIR,path)
                if kind!=CMD_HANDLE:raise RuntimeError('Unexpected SFTP response')
                sftp._request(CMD_CLOSE,message.get_binary())
                allowed=True
            except OSError as error:
                print(f'{path}: denied ({type(error).__name__}, errno={error.errno})')
                continue
            outside=canonical!=home
            print(f'{path}: canonical={canonical}; directory open allowed={allowed}; outside login={outside}')
            escaped|=outside
        if escaped:raise SystemExit('Confirmed directory access outside configured home; no files read or uploaded.')
        print('Directory operations stayed inside the configured home; no files read or uploaded.')

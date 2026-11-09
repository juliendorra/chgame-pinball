#!/usr/bin/env python3
"""Check SFTP isolation without reading private files or uploading artifacts."""
import os
from pathlib import Path
import paramiko
from deploy_sftp import TARGET,confined
ROOT=Path(__file__).resolve().parents[1]
with paramiko.SSHClient() as client:
    client.load_host_keys(str(ROOT/'tools/deploy_known_hosts'))
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    if os.environ['FTP_SERVER']!=TARGET['host'] or os.environ['FTP_USERNAME']!=TARGET['username']:
        raise RuntimeError('Probe must use the dedicated Pinball host and account')
    client.connect(os.environ['FTP_SERVER'],port=22,username=os.environ['FTP_USERNAME'],
                   password=os.environ['FTP_PASSWORD'],allow_agent=False,look_for_keys=False,
                   timeout=30,banner_timeout=30,auth_timeout=30)
    with client.open_sftp() as sftp:confined(sftp)
print('Verified permission boundary; no private file contents read and no artifacts uploaded.')

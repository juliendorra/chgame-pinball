#!/usr/bin/env python3
"""Check the dedicated FTP login stays inside its configured home directory."""
from ftplib import FTP,error_perm
import os
with FTP(timeout=30) as ftp:
    ftp.connect(os.environ['FTP_SERVER'],21)
    ftp.login(os.environ['FTP_USERNAME'],os.environ['FTP_PASSWORD'])
    home=ftp.pwd()
    for path in ('..','/','/../..'):
        try:ftp.cwd(path)
        except error_perm:pass
        assert ftp.pwd()==home,'FTP user can leave its configured directory; deployment refused'
    print('FTP parent traversal stays confined to the login root.')

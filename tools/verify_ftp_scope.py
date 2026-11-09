#!/usr/bin/env python3
"""Check the dedicated FTPS login stays inside its configured home directory."""
from ftplib import FTP_TLS,error_perm
import os
import ssl
with FTP_TLS(context=ssl.create_default_context(),timeout=30) as ftp:
    ftp.connect(os.environ['FTP_SERVER'],21)
    ftp.login(os.environ['FTP_USERNAME'],os.environ['FTP_PASSWORD'])
    ftp.prot_p()
    home=ftp.pwd()
    for path in ('..','/','/../..'):
        try:ftp.cwd(path)
        except error_perm:pass
        assert ftp.pwd()==home,'FTP user can leave its configured directory; deployment refused'
    print('FTPS certificate verified; parent traversal stays confined to the login root.')

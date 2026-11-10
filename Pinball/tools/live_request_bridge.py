#!/usr/bin/env python3
"""JSON-lines transport for testing the production browser SD writer on CHGame.

No HTTP server or browser serial emulation. The Node diagnostic owns this
process and uses the same LiveClient as the other device verification tools.
"""
import argparse
import json
from pathlib import Path
import sys

GAME=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(GAME/'editor'),str(GAME.parent/'CHGame/tools/chsim')]
from protocol import LiveClient
from chdrivelib import SerialTransport

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--port');a=p.parse_args()
client=LiveClient(SerialTransport(a.port))
try:
    for line in sys.stdin:
        request=json.loads(line)
        try:response={'id':request['id'],'lines':client.request(request['command'])}
        except Exception as error:response={'id':request['id'],'error':str(error)}
        print(json.dumps(response),flush=True)
finally:client.t.close()

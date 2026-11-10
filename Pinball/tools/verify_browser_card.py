#!/usr/bin/env python3
"""Test browser FAT writes against the independent CHSd FAT image reader."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
GAME=Path(__file__).resolve().parents[1];ROOT=GAME.parent
sys.path.insert(0,str(ROOT/'CHGame/platform/board/arduino/CHGame/libraries/CHSd/tools'))
sys.path.insert(0,str(GAME/'tools'))
from fatimg import build_image,FatVolume
from boards import encode
from build_studio import node
boards=json.loads((GAME/'boards/tables.json').read_text())
with tempfile.TemporaryDirectory(dir=GAME/'out/wasm') as tmp:
    for fs in ('fat16','fat32'):
        for mbr in (False,True):
            path=Path(tmp)/'card.img'
            files={'KEEP.DAT':b'Keep this file\x00'*93,'GAMES/KEEP.CHG':b'Other cartridge'*150,'PINBALL/ORIGINAL.PBT':encode(boards[0])}
            build_image(path,files,fs=fs,mbr=mbr,spc=1)
            subprocess.run([node(),str(GAME/'tools/verify_browser_card.mjs'),str(path)],check=True)
            with FatVolume(path) as reader:
                assert reader.read_file('KEEP.DAT')==files['KEEP.DAT']
                assert reader.read_file('GAMES/KEEP.CHG')==files['GAMES/KEEP.CHG']
                assert reader.read_file('PINBALL/SAFE.PBT')==encode(boards[0])
                assert reader.read_file('PINBALL/SAFE.PBK')==encode(boards[0])
                assert reader.read_file('PINBALL/FAILSAFE.PBT')==encode(boards[0])
                assert reader.read_file('PINBALL/ORIGINAL.PBT')==encode(boards[8])
                assert reader.read_file('PINBALL/CLONE19.PBT')==encode(boards[1])
    # Creation of the PINBALL directory is also a browser-only operation.
    build_image(path,{'KEEP.DAT':b'preserve'},fs='fat16',mbr=True,spc=1)
    subprocess.run([node(),str(GAME/'tools/verify_browser_card.mjs'),str(path),'--new-folder'],check=True)
    with FatVolume(path) as reader:
        assert reader.read_file('PINBALL/NEWBOARD.PBT')==encode(boards[2])
        assert reader.read_file('KEEP.DAT')==b'preserve'
print('Browser SD writer: FAT16/FAT32, MBR/superfloppy, directory growth, protected auto-save/revert, conflict guards, failure recovery and independent readback passed.')

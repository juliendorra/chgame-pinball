#!/usr/bin/env python3
"""Verify the game creates and reopens both score files with full board IDs."""
from pathlib import Path
import importlib.util,json,os,struct,sys,zlib
G=Path(__file__).resolve().parents[1];R=G.parent
sys.path[:0]=[str(Path(__file__).resolve().parents[2]/'tools'),str(R/'CHGame/tools/chsim'),str(R/'chgame-sd-saves/tools'),str(R/'CHGame/platform/board/arduino/CHGame/libraries/CHSd/tools')]
from sd_saves import overlay
import prepare
from fatimg import build_image,FatVolume,short_name
from chsim import build
from chdrivelib import Driver,SimTransport
from boards import encode
O=G/'out/sd-scores';O.mkdir(parents=True,exist_ok=True)
os.environ['CHSIM_CHGAME']=str(overlay()/'CHGame/src')
os.environ['CHSIM_FLAGS']=f'-fsanitize=undefined,bounds -fsanitize-ignorelist={G}/tools/sanitizer.ignore -fno-sanitize-recover=all'
exe=build(G,out=O/'sim-scores');ID='com.juliendorra.pinball.v2.scores-a';NAME=prepare.save_path(ID)
SECOND_ID='com.juliendorra.pinball.v2.scores-b'
SECOND_NAME=prepare.save_path(SECOND_ID)
board = json.loads((G / "boards/tables.json").read_text())[0]
NEON = board["id"]

def payload(rows, muted=0):
    data = bytearray(484)
    for i, (ident, score) in enumerate(rows):
        struct.pack_into('<II', data, i * 8, ident & 0xffffffff, score)
        struct.pack_into('<H', data, 388 + 2 * i, ident >> 32)
    data[384] = muted
    return data

def journal(data, generation=1, version=1):
    record = bytearray(512)
    struct.pack_into('<IIHBBI', record, 0, prepare.RECORD_TAG, generation, len(data), version, 0, 0)
    record[16:16+len(data)] = data
    struct.pack_into('<I', record, 508, zlib.crc32(record[:508]))
    return prepare.descriptor(ID, 1) + record + b'\xff' * 512

def fresh(raw=None, root_journal=None):
    path = O/'card.img'
    files = {'OTHER.TXT': b'keep this exactly'}
    if raw is not None:
        files[NAME] = raw
    if root_journal is not None:
        files[prepare.filename(ID)] = root_journal
    build_image(path, files, fs='fat16', spc=1, clusters=5000, mbr=True)
    return path

def boot(card,play=False):
 os.environ['CHGAME_SAVE_CARD']=str(card)
 t=SimTransport(exe);d=Driver(t,'MPIN')
 try:
  d.handshake();d.frames(1);d.cmd('F 0')
  if play:d.cmd('O 50000');d.cmd('F 0')
  return {k:int(v) for k,v in (p.split('=') for p in d.query('V','PIN ').split()[1:])}
 finally:assert t.close()==0 and not t.bugs,t.bugs

def raw_file(card):
 with FatVolume(card) as v:
  assert v.read_file('OTHER.TXT')==b'keep this exactly'
  return v.read_file(NAME)

def read(card):
 raw=raw_file(card);prepare.validate(raw,ID);valid=[]
 for i in range(2):
  p=raw[512+i*512:1024+i*512]
  if p[:4]==b'CSV3' and zlib.crc32(p[:508])==struct.unpack_from('<I',p,508)[0]:
   generation,size=struct.unpack_from('<IH',p,4)
   valid.append((generation,p[16:16+size]))
 data=max(valid)[1]
 assert len(data) == 484
 rows = [struct.unpack_from('<II',data,i) for i in range(0,384,8)]
 rows = [(low | (high << 32),score) for (low,score),high in zip(rows,struct.unpack_from('<48H',data,388))]
 assert len([ident for ident,score in rows if ident])==len({ident for ident,score in rows if ident})
 return {ident:score for ident,score in rows if ident},data,raw

initial = journal(payload([(0,0),(NEON,10680)], muted=1))
card = fresh(initial)
s = boot(card)
rows,data,raw=read(card)
assert rows=={NEON:10680} and data[384]==1 and s['sound']==0 and s['best']==10680
assert raw==initial  # Loading never rewrites a valid journal.
s=boot(card,play=True);assert read(card)[0][s['id']]==50000
assert boot(card)['best']==50000
card=fresh();before=card.read_bytes();boot(card);assert card.read_bytes()==before
boot(card,play=True);assert boot(card)['best']==50000
with FatVolume(card) as volume:
    prepare.validate(volume.read_file(NAME),ID)
    assert all(entry[0] != short_name(prepare.filename(ID)) for entry in volume.listdir())
root_journal=journal(payload([(NEON,77777)],muted=1))
card=fresh(root_journal=root_journal)
assert boot(card)['best']==0
boot(card,play=True)
assert boot(card)['best']==50000
with FatVolume(card) as volume:
    assert volume.read_file(prepare.filename(ID))==root_journal
    prepare.validate(volume.read_file(NAME),ID)
raw=journal(payload([(NEON,77777)],muted=1),version=2);card=fresh(raw);boot(card);assert raw_file(card)==raw
report=dict(result='passed',id=ID,filename=NAME,checks=['preferences and scores retained','no write on boot','automatic first save in /SAVES on a blank card','actual table-change save','restart persistence','unknown schema preserved','unrelated file and old root journal unchanged'])

def board_id(index):
    # Force distinct IDs to share the same low word, including the bundled board.
    return index << 32 | (NEON if index != 95 else 0)


def run_library(card, populate):
    os.environ["CHSD_CARD"] = os.environ["CHGAME_SAVE_CARD"] = str(card)
    transport = SimTransport(exe)
    driver = Driver(transport, "MPIN")
    try:
        driver.handshake()
        driver.frames(1)
        for index in range(96):
            driver.cmd(f"F {index}")
            state = dict(part.split("=") for part in driver.query("V", "PIN ").split()[1:])
            ident = int(state["id_high"]) << 32 | (int(state["id"]) & 0xffffffff)
            assert ident == board_id(index), (index, state)
            if populate:
                driver.cmd(f"O {50000 + index}")
            else:
                assert int(state["best"]) == 50000 + index, (index, state["best"])
                assert state["sound"] == "0"
        if populate:
            driver.cmd("F 0")  # Commit score 96 before restarting.
    finally:
        assert transport.close() == 0 and not transport.bugs, transport.bugs


def update_second_bank(card):
    os.environ["CHSD_CARD"] = os.environ["CHGAME_SAVE_CARD"] = str(card)
    transport = SimTransport(exe)
    driver = Driver(transport, "MPIN")
    try:
        driver.handshake()
        driver.frames(1)
        driver.cmd("F 48")
        driver.cmd("O 60000")
        driver.cmd("F 0")
        driver.cmd("F 48")
        assert "best=60000" in driver.query("V", "PIN ").split()
    finally:
        assert transport.close() == 0 and not transport.bugs, transport.bugs


fixtures = {f"PINBALL/B{i:03}.PBT": encode({**board, "id": board_id(i)})
            for i in range(1, 96)}
for fs in ("fat16", "fat32"):
    card = O / f"scores-{fs}.img"
    build_image(card, {**fixtures, NAME: initial, "OTHER.TXT": b"keep this exactly"}, fs=fs, spc=1)
    run_library(card, populate=True)
    with FatVolume(card) as volume:
        first = volume.read_file(NAME)
        second = volume.read_file(SECOND_NAME)
        prepare.validate(first, ID)
        prepare.validate(second, SECOND_ID)
        assert volume.read_file("OTHER.TXT") == b"keep this exactly"
    run_library(card, populate=False)
    update_second_bank(card)
    with FatVolume(card) as volume:
        assert volume.read_file(NAME) == first
        assert volume.read_file(SECOND_NAME) != second
report["checks"].append("96 distinct 48-bit board IDs across two single-sector journals on FAT16 and FAT32")
report["checks"].append("saving in journal two leaves journal one byte-identical")
(O/'report.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS:',', '.join(report['checks']))

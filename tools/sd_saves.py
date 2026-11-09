#!/usr/bin/env python3
"""Provision isolated SD saves, generate the SDK overlay, and run CHGame tools."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import zlib

ROOT=Path(__file__).resolve().parents[1]
SDK=ROOT/'CHGame/platform/board/arduino/CHGame/libraries'
SOURCE=ROOT/'tools/sd_saves/src'
PUBLIC=ROOT/'chgame-sd-saves'
OVERLAY=ROOT/'.cache/sd-saves/libraries'

def catalog():
    return {'MPIN.SAV': {'game': 'Pinball', 'id': 'MPIN'}}

def validate(raw,magic):
    spec=importlib.util.spec_from_file_location('chsave_prepare',PUBLIC/'tools/prepare.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.validate(raw,magic.to_bytes(4,'little').decode('ascii'))

def prepare(card):
    card=Path(card)
    if not card.is_dir():raise ValueError(f'Card folder does not exist: {card}')
    for name,item in catalog().items():
        path=card/name
        if path.exists():
            try:validate(path.read_bytes(),int.from_bytes(name[:4].encode(),'little'))
            except ValueError as error:raise ValueError(f'{path}: {error}') from error
        else:
            with path.open('xb') as f:f.write(b'\xff'*1024);f.flush();os.fsync(f.fileno())
            if path.read_bytes()!=b'\xff'*1024:raise OSError(f'Provisioning readback failed: {path}')
    print(f'Prepared/preserved {len(catalog())} shared game journals on {card}')

def overlay():
    # Hash every input; rebuild after either the SDK or our implementation changes.
    sources=list((SDK/'CHGame/src').rglob('*'))+list(SOURCE.glob('*'))
    sources += [SDK/'CHGame/library.properties',Path(__file__)]
    sources += list((SDK/'CHSd/src').glob('Fat.*'))
    sources += list((ROOT/'vendor/sd-spi').glob('SdSpi.*'))
    sources += list((PUBLIC/'src').rglob('*'))+[PUBLIC/'library.properties']
    digest=hashlib.sha256()
    for path in sorted(p for p in sources if p.is_file()):digest.update(str(path.relative_to(ROOT)).encode());digest.update(path.read_bytes())
    fingerprint=digest.hexdigest();stamp=OVERLAY/'fingerprint'
    if stamp.exists() and stamp.read_text()==fingerprint:return OVERLAY
    OVERLAY.mkdir(parents=True,exist_ok=True)
    dest=OVERLAY/'CHGame'
    if dest.exists():shutil.rmtree(dest)
    shutil.copytree(SDK/'CHGame/src',dest/'src')
    shutil.copy2(SDK/'CHGame/library.properties',dest/'library.properties')
    for path in SOURCE.glob('*'):
        if path.name!='LegacyOnly.cpp':shutil.copy2(path,dest/'src/chgame'/path.name)
    # Bundle the standalone library unchanged, with a board transport bridge
    # to reuse the SDK asset driver's SPI state and host card fixtures.
    shutil.copytree(PUBLIC/'src',dest/'src/chsave')
    (dest/'src/CHSave.h').write_text('#pragma once\n#include "chsave/CHSave.h"\n')
    (dest/'src/chsave/detail/Host.cpp').unlink()
    (dest/'src/chsave/detail/Block.cpp').write_text('''#include "Block.h"
#if defined(CHSIM) && !defined(CHGAME_SAVE_SHARED_TEST)
namespace save_sd {bool init();bool read(uint32_t,uint8_t*);bool write(uint32_t,const uint8_t*);}
namespace transport=save_sd;
#else
#include <SdSpi.h>
namespace transport=sd;
#endif
namespace chsave {namespace block {
bool init(){return transport::init();}
bool read(uint32_t lba,uint8_t *p){return transport::read(lba,p);}
bool write(uint32_t lba,const uint8_t *p){return transport::write(lba,p);}
}}
''')
    private=dest/'src/chgame/card';private.mkdir()
    for origin,old,new in ((SDK/'CHSd/src','fat','save_fat'),(ROOT/'vendor/sd-spi','mybl_sd','save_sd')):
        pattern='Fat.*' if old=='fat' else 'SdSpi.*'
        for path in origin.glob(pattern):
            if path.name=='SdSpi.cpp':continue
            text=path.read_text()
            if path.name=='Fat.cpp':text+='\n'+(SOURCE/'FatSave.inc').read_text()
            text=text.replace('namespace '+old,'namespace '+new).replace(old+'::',new+'::')
            # FAT uses the private SPI driver, isolated from streamed game assets.
            if old=='fat':text=text.replace('sd::','save_sd::')
            if path.suffix=='.cpp':text='#ifdef CHSIM\n'+text+'\n#endif\n'
            (private/path.name).write_text(text)
    # Reuse the board's SD/FAT code for saves and game assets. The only
    # addition is Mystic Balloon's already-proven single-sector writer.
    link=OVERLAY/'CHGfx'
    if not link.exists():link.symlink_to(SDK/'CHGfx',target_is_directory=True)
    card=OVERLAY/'CHSd'
    if card.is_symlink():card.unlink()
    elif card.exists():shutil.rmtree(card)
    shutil.copytree(SDK/'CHSd',card,ignore=shutil.ignore_patterns('build','out','tools','test','tests'))
    for name in ('SdSpi.cpp','SdSpi.h'):
        text=(ROOT/'vendor/sd-spi'/name).read_text().replace('mybl_sd','sd')
        (card/'src'/name).write_text(text)
    fat_source=card/'src/Fat.cpp';fat_source.write_text(fat_source.read_text()+'\n'+(SOURCE/'FatSave.inc').read_text())
    props=dest/'library.properties';props.write_text(props.read_text().replace('depends=CHGfx','depends=CHGfx,CHSd'))
    # Header docs must describe the selected backend.
    header=dest/'src/CHGame.h';header.write_text(header.read_text().replace('a record in flash that survives power cycles','an isolated SD journal that survives power cycles'))
    legacy=OVERLAY/'legacy/CHGame'
    if legacy.exists():shutil.rmtree(legacy)
    shutil.copytree(dest,legacy)
    shutil.copy2(SOURCE/'LegacyOnly.cpp',legacy/'src/chgame/Save.cpp')
    for name in ('CHGfx','CHSd'):
        link=OVERLAY/'legacy'/name
        if link.is_symlink() and link.resolve()!=(OVERLAY/name).resolve():link.unlink()
        if not link.exists():link.symlink_to(OVERLAY/name,target_is_directory=True)
    stamp.write_text(fingerprint)
    return OVERLAY

def simulation_image(path):
    sys.path.insert(0,str(SDK/'CHSd/tools'))
    from fatimg import build_image
    build_image(path,{name:b'\xff'*1024 for name in catalog()},fs='fat16',spc=1,clusters=5000,mbr=True)

def run():
    for key,relative in {
        'ARDUINO_CONFIG_FILE':'arduino-cli.yaml','ARDUINO_DIRECTORIES_DATA':'.arduino15',
        'ARDUINO_DIRECTORIES_DOWNLOADS':'.arduino15/staging','ARDUINO_DIRECTORIES_USER':'sketchbook',
        'ARDUINO_BUILD_CACHE_PATH':'.arduino15/cache','TMPDIR':'.cache/tmp',
    }.items():os.environ.setdefault(key,str(ROOT/relative))
    libraries=overlay()
    # Mystic Balloon retains its larger established journal and only imports
    # from the SDK's old pages. It never uses the generic 244-byte SD format.
    if '--sketch' in sys.argv:
        sketch=sys.argv[sys.argv.index('--sketch')+1]
        if Path(sketch).name=='MysticBalloon':libraries=libraries/'legacy'
    sys.path[:0]=[str(ROOT/'CHGame/tools'),str(ROOT/'CHGame/tools/chsim')]
    os.environ['CHSIM_CHGAME']=str(libraries/'CHGame/src')
    if not os.environ.get('CHGAME_SAVE_CARD') and not os.environ.get('CHGAME_SAVE_TEMPLATE'):
        template=OVERLAY.parent/('sim-'+hashlib.sha256(json.dumps(catalog(),sort_keys=True).encode()).hexdigest()[:12]+'.img')
        if not template.exists():simulation_image(template)
        os.environ['CHGAME_SAVE_TEMPLATE']=str(template)
    # Deploy provisions journals as a separate, non-replacing operation.
    if 'deploy' in sys.argv:
        for i,arg in enumerate(sys.argv):
            card=sys.argv[i+1] if arg=='--card' and i+1<len(sys.argv) else arg[7:] if arg.startswith('--card=') else None
            if card:prepare(card)
    import device,gamecfg,hosttests
    device.LIBRARIES=libraries
    build=device.build
    def build_with_sd(sketch,debug=False,flags=''):
        if not debug and Path(sketch).name in {'CHBackgammon','CHBoardwalk','CHCraps','CHRoulette'}:
            header=ROOT/'tools/sd_saves/NoRuntimeUsb.h'
            flags+=' -include "'+str(header)+'"'
        return build(sketch,debug,flags)
    device.build=build_with_sd
    hosttests.LIB=libraries/'CHGame/src'
    hosttests.INCLUDES['lib']=hosttests.LIB
    # SD saves do not reserve flash pages. Mystic's legacy reader also checks
    # that former pages aren't occupied by the current image.
    load=gamecfg.load
    def config(sketch):
        value=load(sketch);value.SAVE_PAGES=0;return value
    gamecfg.load=config
    import chgame
    raise SystemExit(chgame.main())

def main():
    if len(sys.argv)>1 and sys.argv[1]=='run':
        sys.argv.pop(1);run();return
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('prepare');p.add_argument('--card',required=True,type=Path)
    sub.add_parser('overlay');sub.add_parser('list')
    p=sub.add_parser('sim-image');p.add_argument('path',type=Path)
    args=parser.parse_args()
    if args.command=='prepare':prepare(args.card)
    elif args.command=='overlay':print(overlay())
    elif args.command=='list':print(json.dumps(catalog(),indent=2))
    elif args.command=='sim-image':simulation_image(args.path)
if __name__=='__main__':main()

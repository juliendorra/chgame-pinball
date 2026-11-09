#!/usr/bin/env python3
"""Build a static Pinball Studio from the actual game sketch and libraries.

python3 Pinball/tools/build_studio.py             # WASM + parity checks + static files
python3 Pinball/tools/build_studio.py --check     # reject stale/missing output
EMXX can point at Emscripten 4.0.15; default: workspace .toolchains/pinball-emsdk.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

GAME=Path(__file__).resolve().parents[1];ROOT=GAME.parent
OUT=GAME/'build/studio';WORK=GAME/'out/wasm'
# Match the normal game launcher: firmware and browser/native targets use the
# same SD journal implementation, not the SDK's legacy shared-flash backend.
sys.path.insert(0,str(ROOT/'tools'))
from sd_saves import overlay as save_overlay
LIB=save_overlay()
HOST=ROOT/'CHGame/tools/chsim/host';SDK=ROOT/'.toolchains/pinball-emsdk'
VERSION='4.0.15'
EXPORTS=['init','input','apply','step','restart','pause','place','state','state_count','physics','render','render_size','lcd','lcd_size','table','table_size']
PHYSICS_KEYS=('spin_grip','spin_forget','scatter_passive','scatter_powered','scatter_eject')

def physics_config(defines):
    values=dict(d.split('=',1) for d in defines if d.startswith('PINBALL_') and '=' in d)
    try:return {key:int(values['PINBALL_'+key.upper()]) for key in PHYSICS_KEYS}
    except (KeyError,ValueError):raise SystemExit('tools/game.py must explicitly define all five Pinball physics settings.')

def run(args,**kw):
    subprocess.run([str(a) for a in args],check=True,cwd=ROOT,**kw)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inputs():
    files=set(GAME.glob('*.ino'))|set(GAME.glob('*.cpp'))|set(GAME.glob('*.h'))
    files.add(ROOT/'pinball.py')
    files.add(GAME/'editor/.htaccess')
    for name in ('build_studio.py','game.py','sprites.py','boards.py','sim_build.py',
                 'verify_wasm.mjs','verify_browser_card.py','verify_browser_card.mjs',
                 'verify_sim.py','verify_shake.py','verify_flippers.py','verify_regressions.py',
                 'sanitizer.ignore'):
        files.add(GAME/'tools'/name)
    files.add(ROOT/'tools/sd_saves.py')
    for folder in [GAME/'src',GAME/'sprites',GAME/'boards',GAME/'editor',GAME/'tools/wasm',HOST,ROOT/'CHGame/tools',
                   ROOT/'CHGame/platform/board/arduino/CHGame/libraries/CHSd/host',
                   LIB/'CHGame/src',LIB/'CHGfx/src',LIB/'CHSd/src',ROOT/'tools/sd_saves/src',
                   ROOT/'vendor/sd-spi']:
        files.update(p for p in folder.rglob('*') if p.is_file() and p.suffix in
                     ('.h','.cpp','.c','.ino','.json','.mjs','.css','.html','.py','.htaccess')
                     and not {'build','__pycache__'}&set(p.relative_to(folder).parts))
    return {p.relative_to(ROOT).as_posix():digest(p) for p in sorted(files)}
def source_hash(files):return hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()
def node():
    path=shutil.which('node')
    if not path:
        candidates=sorted((Path.home()/'.nvm/versions/node').glob('*/bin/node'))
        path=str(candidates[-1]) if candidates else None
    if not path:raise SystemExit('Node.js is required for native/WASM parity validation.')
    return path

def engine_inputs(work=WORK):
    # As Arduino/chsim do, discover every game translation unit, including future ones.
    unit=work/'sketch.cpp'
    unit.write_text('#include <Arduino.h>\n'+''.join(f'#include "{f.as_posix()}"\n' for f in sorted(GAME.glob('*.ino'))))
    game_sources=sorted(p for p in GAME.iterdir() if p.suffix in ('.cpp','.c'))
    game_sources+=sorted(p for p in (GAME/'src').rglob('*') if p.suffix in ('.cpp','.c'))
    sources=[unit,*game_sources,
             *sorted((LIB/'CHGfx/src').glob('*.cpp')),
             *sorted((LIB/'CHGame/src').rglob('*.cpp')),*sorted((LIB/'CHSd/src').glob('*.cpp')),
             GAME/'tools/wasm/platform.cpp',GAME/'tools/wasm/api.cpp']
    sources=[s for s in sources if s.name not in ('CHGfx.cpp',)]
    includes=[HOST,GAME,LIB/'CHGfx/src',LIB/'CHGame/src',LIB/'CHSd/src']
    sys.path.insert(0,str(ROOT/'CHGame/tools'))
    import gamecfg
    shared_defines=gamecfg.load(GAME).DEFINES
    flags=['-std=gnu++17','-O2','-w','-DCHSIM','-DCH32X035','-DARDUINO=10800','-DCHGAME_DEBUG=0',
           *['-D'+d for d in shared_defines],
           *[f'-I{d}' for d in includes]]
    return flags,sources,shared_defines

def firmware_snapshot(work):
    # Arduino scans every extra sketch file, including accumulated captures.
    # Compile only the actual source snapshot and its shared physics config.
    sketch=work/'firmware/Pinball';sketch.mkdir(parents=True,exist_ok=True)
    for source in GAME.iterdir():
        if source.is_file() and source.suffix in ('.ino','.cpp','.c','.h'):
            shutil.copy2(source,sketch/source.name)
    if (GAME/'src').exists():shutil.copytree(GAME/'src',sketch/'src')
    (sketch/'tools').mkdir();shutil.copy2(GAME/'tools/game.py',sketch/'tools/game.py')
    return sketch

def main():
    global OUT
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check',action='store_true');p.add_argument('--firmware',type=Path)
    p.add_argument('--build-firmware',action='store_true')
    p.add_argument('--debug',action='store_true');p.add_argument('-D',action='append',default=[])
    p.add_argument('--console-build',type=Path,help='Also require physics to match an installed-console build report')
    a=p.parse_args()
    if a.firmware and not a.check and not a.build_firmware:
        raise SystemExit('--firmware checks an existing pairing; create pairs with --build-firmware.')
    before=inputs();fingerprint=source_hash(before);manifest=OUT/'build.json'
    sys.path.insert(0,str(ROOT/'CHGame/tools'))
    import gamecfg
    physics=physics_config(gamecfg.load(GAME).DEFINES)
    if a.console_build:
        console=json.loads(a.console_build.read_text())
        if console.get('config')!=physics:raise SystemExit('Console and shared game physics differ; refusing a mismatched Studio build.')
    if a.check:
        if not manifest.exists():raise SystemExit('Build Pinball Studio first.')
        m=json.loads(manifest.read_text())
        if m.get('physics')!=physics:raise SystemExit('Studio physics configuration is stale: rebuild.')
        if m['sourceHash']!=fingerprint:raise SystemExit('Pinball Studio is stale: rebuild after game/editor changes.')
        for name,h in m['artifacts'].items():
            if not (OUT/name).exists() or digest(OUT/name)!=h:raise SystemExit(f'Stale/damaged Studio artifact: {name}')
        if a.firmware and (m.get('firmware',{}).get('sha256')!=digest(a.firmware)):
            raise SystemExit('Firmware differs from the verified Studio build.')
        print('Static Studio sources and artifacts are current.');return
    WORK.mkdir(parents=True,exist_ok=True)
    destination=OUT
    temporary=tempfile.TemporaryDirectory(prefix='studio-',dir=WORK)
    OUT=Path(temporary.name)
    # Both targets consume the checked-in generated assets. Reject stale art.
    run([sys.executable,GAME/'tools/sprites.py','--check'])
    run([sys.executable,GAME/'tools/boards.py','--check'])
    emxx=Path(os.environ.get('EMXX',str(SDK/'upstream/emscripten/em++')))
    if not emxx.exists():raise SystemExit(f'Install Emscripten {VERSION}; see Pinball/docs/static-studio.md (or set EMXX).')
    version=subprocess.check_output([str(emxx),'--version'],text=True)
    if not re.search(r'\b'+re.escape(VERSION)+r'\b',version):raise SystemExit(f'Use pinned Emscripten {VERSION}, got {version.splitlines()[0]}')
    if a.D:raise SystemExit('Custom game defines need matching WASM configuration; use the canonical build without -D.')
    if a.build_firmware:
        sketch=firmware_snapshot(OUT)
        run([sys.executable,ROOT/'tools/sd_saves.py','run','--sketch',sketch,'build',*(['--debug'] if a.debug else [])])
        a.firmware=sketch/'build'/('debug' if a.debug else 'release')/'Pinball.ino.bin'
    flags,sources,shared_defines=engine_inputs()
    wasmflags=['--no-entry','-sMODULARIZE=1','-sEXPORT_ES6=1','-sENVIRONMENT=web,node',
               '-sFILESYSTEM=0','-sALLOW_MEMORY_GROWTH=0','-sINITIAL_MEMORY=16777216',
               '-sEXPORTED_FUNCTIONS='+json.dumps(['_pb_'+n for n in EXPORTS]),
               '-sEXPORTED_RUNTIME_METHODS=["HEAPU8","HEAP32"]']
    engine='engine-'+fingerprint[:16]
    run([emxx,*flags,*sources,*wasmflags,'-o',OUT/(engine+'.mjs')])
    (OUT/'engine.mjs').write_text(f"export {{default}} from './{engine}.mjs';\n")
    # Isolate the host executable too: replacing a stale/in-use Mach-O file
    # can crash Apple's linker and concurrent builds must not share a target.
    native=OUT/'engine-replay'
    run([os.environ.get('CXX','clang++'),*flags,*sources,GAME/'tools/wasm/replay.cpp','-o',native])
    # Copy only deployable assets, with relative URLs (works under a subdirectory).
    for file in (GAME/'editor').iterdir():
        if file.suffix in ('.html','.css','.mjs') or file.name=='.htaccess':shutil.copy2(file,OUT/file.name)
    assets=OUT/'assets';assets.mkdir(exist_ok=True)
    (assets/'physics.json').write_text(json.dumps(physics,indent=2)+'\n')
    for src,dest in [('boards/tables.json','boards.json'),('sprites/element_sprites.json','elements.json'),('sprites/board_borders.json','borders.json')]:
        shutil.copy2(GAME/src,assets/dest)
    run([node(),GAME/'tools/verify_wasm.mjs',OUT,native])
    run([node(),'--test',*sorted((GAME/'editor/tests').glob('*.test.mjs'))])
    run([sys.executable,GAME/'tools/verify_browser_card.py'])
    run([sys.executable,GAME/'tools/verify_sim.py'])
    run([sys.executable,GAME/'tools/verify_shake.py'])
    run([sys.executable,GAME/'tools/verify_flippers.py'])
    run([sys.executable,GAME/'tools/verify_regressions.py','--out',OUT/'validation/regressions.json'])
    native.unlink() # validation tool, never part of the published static app
    after=inputs()
    if before!=after:raise SystemExit('Source changed during build; run again for a consistent bundle.')
    artifacts={f.relative_to(OUT).as_posix():digest(f) for f in sorted(OUT.rglob('*')) if f.is_file() and f!=manifest}
    result={'schema':1,'engine':'shared Pinball sketch + CHGame/CHGfx C++',
            'emscripten':VERSION,'sourceHash':fingerprint,'sources':before,'artifacts':artifacts,
            'nativeCompiler':subprocess.check_output([os.environ.get('CXX','clang++'),'--version'],text=True).splitlines()[0],
            'sharedDefines':shared_defines,'physics':physics,'saveBackend':'per-game SD journal (tools/sd_saves overlay)',
            'validation':'native/WASM deterministic replay: state + LCD/full-board pixels + live edits'}
    if a.firmware:
        result['firmware']={'sha256':digest(a.firmware),'bytes':a.firmware.stat().st_size}
        compiler=ROOT/'.toolchains/current/native/bin/riscv-none-elf-g++'
        if compiler.exists():result['firmware']['compiler']=subprocess.check_output([str(compiler),'--version'],text=True).splitlines()[0]
    if a.build_firmware:
        target=GAME/'build'/('debug' if a.debug else 'release');target.mkdir(parents=True,exist_ok=True)
        for artifact in a.firmware.parent.iterdir():
            if artifact.is_file() and artifact.suffix in ('.bin','.elf','.hex','.map'):
                shutil.copy2(artifact,target/artifact.name)
        # Firmware build files are local validation tools, never web assets.
        shutil.rmtree(OUT/'firmware')
        result['artifacts']={f.relative_to(OUT).as_posix():digest(f) for f in sorted(OUT.rglob('*')) if f.is_file()}
    (OUT/'build.json').write_text(json.dumps(result,indent=2)+'\n')
    # Only publish a complete validated bundle; never serve a half-built engine.
    backup=WORK/'studio-previous'
    if backup.exists():shutil.rmtree(backup)
    if destination.exists():destination.rename(backup)
    shutil.move(str(OUT),destination)
    temporary.cleanup()
    print(f'Static Studio: {destination}\nSource: {fingerprint}')
if __name__=='__main__':main()

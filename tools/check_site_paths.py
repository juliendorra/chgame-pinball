#!/usr/bin/env python3
"""Guard site deploy triggers against omissions and documentation-only runs."""
import fnmatch
from pathlib import Path
root=Path(__file__).resolve().parents[1]
workflow=(root/'.github/workflows/deploy-editor.yml').read_text()
paths=[line.split("'",2)[1] for line in workflow.splitlines() if line.startswith("      - '")]
def matches(path):return any(fnmatch.fnmatchcase(path,p) for p in paths)
for name in ('Pinball/Physics.cpp','Pinball/src/rumble/Rumble.cpp','Pinball/editor/.htaccess',
             'Pinball/editor/app.mjs','Pinball/boards/tables.json','Pinball/sprites/element_sprites.json',
             'Pinball/tools/verify_sim.py','tools/deploy_sftp.py','tools/deploy_known_hosts','CHGame/tools/gamecfg.py','tools/sd_saves.py','vendor/sd-spi/SdSpi.cpp','requirements.txt'):
    assert matches(name),f'Missing site trigger: {name}'
for name in ('README.md','Pinball/README.md','Pinball/docs/cart.png','Pinball/research/gator/verify_rom.py',
             'Pinball/chgame.json','Pinball/tools/install_built.py','tools/build_current_gcc.py','arduino-cli.yaml'):
    assert not matches(name),f'Unnecessary site trigger: {name}'
assert 'workflow_dispatch:' not in workflow and 'pull_request:' not in workflow
print('Site path filters: runtime inputs included; docs, research and firmware packaging excluded.')

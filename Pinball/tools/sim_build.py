"""Build Pinball diagnostics with the same save backend as Studio/firmware."""
import os
import sys
from build_studio import ROOT
from sd_saves import simulator_environment
sys.path.insert(0,str(ROOT/'CHGame/tools/chsim'))
from chsim import build as _build
sys.path.insert(0,str(ROOT/'CHGame/tools'))
import gamecfg

def build(sketch,defines=(),**kwargs):
    os.environ.update(simulator_environment())
    return _build(sketch,defines=[*gamecfg.load(sketch).DEFINES,*defines],**kwargs)

"""Build Pinball diagnostics with the same save backend as Studio/firmware."""
import os
import sys
from build_studio import LIB, ROOT
sys.path.insert(0,str(ROOT/'CHGame/tools/chsim'))
from chsim import build as _build
sys.path.insert(0,str(ROOT/'CHGame/tools'))
import gamecfg

def build(sketch,defines=(),**kwargs):
    os.environ['CHSIM_CHGAME']=str(LIB/'CHGame/src')
    return _build(sketch,defines=[*gamecfg.load(sketch).DEFINES,*defines],**kwargs)

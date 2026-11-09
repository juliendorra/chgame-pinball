"""pinball.py uses per-game SD saves and overrides SAVE_PAGES to zero.

The conservative reservation below protects unsupported direct SDK builds
from overwriting legacy records before migration.
"""
from pathlib import Path as _Path
import re as _re

SAVE_PAGES = 2
SIM_TESTS = ["tools/verify_sim.py"]
# Headers are the single source for standard physics, including direct C++
# builds. Export their defaults as explicit flags for SDK/Studio manifests.
_root = _Path(__file__).resolve().parents[1]
_headers = (_root / "Spin.h").read_text() + "\n" + (_root / "Scatter.h").read_text()
DEFINES = []
for _name in ("SPIN_GRIP", "SPIN_FORGET", "SCATTER_PASSIVE", "SCATTER_POWERED", "SCATTER_EJECT"):
    _match = _re.search(r"^#define PINBALL_" + _name + r" (\d+)\s*$", _headers, _re.MULTILINE)
    if not _match:
        raise ValueError("Missing numeric physics default: PINBALL_" + _name)
    DEFINES.append("PINBALL_" + _name + "=" + _match[1])

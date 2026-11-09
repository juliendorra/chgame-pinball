#!/bin/zsh
# Double-click in Finder to start the editor and open its local URL.
pinball_root=${0:A:h:h:h}
cd "$pinball_root" || exit 1
exec /usr/bin/env python3 "$pinball_root/pinball.py" editor --open

"""Where a game's art comes from: its own tools/art/ first, then the shared
tools/art/common/ (the files that were byte-identical in several games:
the dealer and his faces, the pointing glove, the display font, the card
art, the chips, the end-screen lettering).

    import artlib
    path = artlib.art(HERE, "dealer.png")      # HERE: the game's tools/ folder

`art()` returns the game's own file when it has one, else the common one,
else the game's (non-existent) path, so `.exists()` checks keep working.
A game that wants its own version of a shared file just puts it in its
tools/art/.
"""
from pathlib import Path

COMMON = Path(__file__).resolve().parent / "art" / "common"


def art(tools_dir, name):
    own = Path(tools_dir) / "art" / name
    if own.exists():
        return own
    shared = COMMON / name
    return shared if shared.exists() else own


def common_dir():
    return COMMON


def title_bits(tools_dir, name="title.txt"):
    """The cover's title lettering (tools/art/title.txt: '#' ink, '//' comment
    lines, as artkit.load_mask reads it) as rows of 0/1, trimmed to its ink:
    the games' title screens draw the same lettering as their cover."""
    rows = [r for r in art(tools_dir, name).read_text(encoding="utf-8").splitlines()
            if r.strip() and not r.startswith("//")]
    w = max(len(r) for r in rows)
    bits = [[1 if ch in "#X1" else 0 for ch in r.ljust(w)] for r in rows]
    while bits and not any(bits[0]):
        bits.pop(0)
    while bits and not any(bits[-1]):
        bits.pop()
    cols = [x for x in range(w) if any(r[x] for r in bits)]
    return [r[cols[0]:cols[-1] + 1] for r in bits]

"""The music composer the games' tools/make_music.py share: songs written as
"NOTE:len" tokens become Playtune bytes for the CHGame library's sequencer.

Each song is a tempo and up to four voices written as "NOTE:len" tokens,
lengths in eighth notes (default 1). NOTE is like C6, F#5, Bb6, or R for a
rest. Score bytes (Arduboy Playtune): 0x9c n = note on in channel c, 0x8c =
note off, two bytes big-endian = wait ms, 0xE0 = restart, 0xF0 = stop.

    from music.composer import write_music_cpp
    write_music_cpp(ROOT / "src/audio/Music.cpp", SONGS, LOOPS, HEADER, DEBUG_NOTE, ROOT)

A game's make_music.py holds only its songs and the two comment lines of
the generated file.
"""
from pathlib import Path

NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def midi(tok):
    name = tok[0]
    rest = tok[1:]
    acc = 0
    while rest and rest[0] in "#b":
        acc += 1 if rest[0] == "#" else -1
        rest = rest[1:]
    octave = int(rest)
    return 12 * (octave + 1) + NOTE[name] + acc


def voice_events(text, eighth):
    t = 0
    ev = []
    for tok in text.split():
        note, _, n = tok.partition(":")
        dur = int(n or 1) * eighth
        if note != "R":
            ev.append((t, "on", midi(note)))
            ev.append((t + dur - 12, "off", None))      # short gap keeps notes distinct
        t += dur
    return ev, t


def compile_song(song, loop):
    eighth = song["eighth_ms"]
    all_ev = []
    total = 0
    for ch, v in enumerate(song["voices"]):
        ev, t = voice_events(v, eighth)
        total = max(total, t)
        all_ev += [(tm, 0 if kind == "off" else 1, ch, n) for tm, kind, n in ev]
    all_ev.sort(key=lambda e: (e[0], e[1]))
    out, now = [], 0
    for tm, on, ch, n in all_ev:
        if tm > now:
            wait = tm - now
            while wait > 0x7FFF:
                out += [0x7F, 0xFF]
                wait -= 0x7FFF
            out += [wait >> 8, wait & 0xFF]
            now = tm
        out += [0x90 | ch, n] if on else [0x80 | ch]
    if total > now:
        w = total - now
        out += [w >> 8, w & 0xFF]
    out.append(0xE0 if loop else 0xF0)
    return out


def write_music_cpp(out, songs, loops, header, debug_note, root=None):
    """src/audio/Music.cpp: `header` is the first comment line, `debug_note`
    the first of the two lines explaining why debug builds have no scores."""
    out = Path(out)
    lines = [header,
             '#include "Music.h"', '#include "../../config.h"', "", "namespace music {", "",
             debug_note,
             "// out - the protocol needs the flash, and the tests never listen.",
             "#if !CHGAME_DEBUG"]
    names = []
    for name, song in songs.items():
        data = compile_song(song, loops[name])
        body = ",".join(f"0x{b:02X}" for b in data)
        chunks = [body[i:i + 100] for i in range(0, len(body), 100)]
        lines.append(f"static const uint8_t {name}[{len(data)}] = {{\n  " + "\n  ".join(chunks) + "\n};")
        names.append((name, len(data)))
    lines.append("#endif")
    lines.append("")
    lines.append("void get(uint8_t song, bool loop, const uint8_t *&data, size_t &n) {")
    lines.append("    (void)loop;")
    lines.append("#if !CHGAME_DEBUG")
    lines.append("    switch (song) {")
    for i, (name, n) in enumerate(names):
        lines.append(f"        case {i}: data = {name}; n = sizeof {name}; return;")
    lines.append("    }")
    lines.append("#else")
    lines.append("    (void)song;")
    lines.append("#endif")
    lines.append("    data = nullptr; n = 0;")
    lines.append("}")
    lines.append("")
    lines.append("}  // namespace music")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    shown = out.relative_to(root) if root else out
    print(f"wrote {shown}: " + ", ".join(f"{n} {b} B" for n, b in names))
    return names

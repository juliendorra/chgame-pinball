#!/usr/bin/env python3
"""Probe hinged gates against their actual rendered arm under the native game."""
import argparse
import copy
import json
import math
from pathlib import Path
import sys

GAME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GAME.parent / 'CHGame/tools/chsim'))
sys.path.insert(0, str(GAME / 'editor'))
from chdrivelib import Driver, SimTransport
from sim_build import build
from fbimage import to_image
from protocol import LiveClient, encode

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--exe', type=Path)
a = p.parse_args()
out = GAME / 'out/gates'; out.mkdir(parents=True, exist_ok=True)
exe = a.exe or build(GAME, out=out / 'sim-gates')
t = SimTransport(exe); d = Driver(t, 'MPIN'); live = LiveClient(t)
base = json.loads((GAME / 'boards/tables.json').read_text())[0]
checks = []; pictures = []

def check(ok, label):
    assert ok, label
    checks.append(label)

def query(command, prefix):
    return {k: int(v) for k, v in (word.split('=') for word in d.query(command, prefix).split()[1:])}

def arm(): return query('G 0', 'GATE ')
def state(): return query('V', 'PIN ')
def place(x, y, vx=0, vy=0): d.cmd(f'J {x},{y},{vx},{vy}')
def load(group=0, ends=(44, 100, 76, 112)):
    b = copy.deepcopy(base); b.update(title='Hinged Gate Lab', height=320)
    x, y, u, v = ends
    b['objects'] = [dict(kind='gate', x=x, y=y, u=u, v=v, group=group, value=0)]
    live.upload(encode(b)); live.request('R'); d.frames(1)
    return b

def pixel(frame, x, y): return (frame[y * 64 + x // 2] >> ((x & 1) * 4)) & 15

def visible(label, capture=False):
    g = arm(); d.cmd('M 40'); d.cmd('W 256'); frame = d.shot()
    length = math.hypot(g['u'] - g['x'], g['v'] - g['y'])
    check(abs(length - math.hypot(32, 12)) < 2, label + ': arm retains its length')
    hits = 0
    for j in range(3, 14):
        x = round(g['x'] + (g['u'] - g['x']) * j / 16)
        y = round(g['y'] + (g['v'] - g['y']) * j / 16) - 40 + 12
        hits += any(pixel(frame, x + dx, y + dy) == 10 for dx in (-1, 0, 1) for dy in (-1, 0, 1))
    check(hits >= 9, label + ': visible metal follows the collision arm')
    check(pixel(frame, 44, 100 - 40 + 12) == 1, label + ': hinge remains visible')
    check(pixel(frame, 76, 112 - 40 + 12) == 14, label + ': fixed stop remains visible')
    if capture: pictures.append(to_image(frame, 4))
    return g

try:
    d.handshake(); d.frames(1)
    load(); place(60, 116, 0, -1100); d.frames(4)
    check(arm()['angle'] > 0, 'allowed contact starts opening')
    place(90, 190)
    angles = []
    for tick in range(45):
        g = visible(f'swing frame {tick}', tick in (0, 2, 5, 10, 17, 23, 30, 39))
        angles.append(g['angle']); d.frames(1)
    check(max(angles) == 80 and angles[-1] == 0, 'arm opens, holds, and settles fully shut')
    check(len(set(angles)) >= 10, 'opening and return use multiple visible poses')
    check(all(-4 <= b-a <= 8 for a, b in zip(angles, angles[1:])), 'gate never teleports between shut and open')

    for ends in ((44, 100, 76, 112), (76, 112, 44, 100), (44, 100, 76, 100)):
        mid_y = (ends[1] + ends[3]) // 2
        for group in (0, 1):
            direction = -1 if group == 0 else 1
            load(group, ends); place(60, mid_y - direction*11, 0, direction*1100)
            d.frames(28); s = state()
            check((s['y'] - mid_y) * direction > 12, f'allowed side passes after swinging: {ends}, group {group}')
            check(s['vy'] * direction > 0, f'allowed shot keeps moving: {ends}, group {group}')
            load(group, ends); place(60, mid_y + direction*7, 0, -direction*900)
            d.frames(3); s = state()
            check(s['vy'] * direction > 0, f'blocked approach rebounds: {ends}, group {group}')
            check(arm()['angle'] == 0, f'blocked contact cannot open the arm: {ends}, group {group}')

    load(2); place(90, 190)
    for mask in (0, 1, 3):
        d.cmd(f'C {mask}'); d.frames(4)
        check(arm()['angle'] == 0, f'bank gate stays locked with target mask {mask}')
    d.cmd('C 7')
    for tick in range(10): d.frames(1); visible(f'bank opening {tick}')
    check(arm()['angle'] == 80, 'all three target banks visibly open the lock')
    g = arm(); dx, dy = g['u'] - g['x'], g['v'] - g['y']; length = math.hypot(dx, dy)
    nx, ny = -dy / length, dx / length
    place(round((g['x'] + g['u']) / 2 + nx*7), round((g['y'] + g['v']) / 2 + ny*7), round(-nx*900), round(-ny*900))
    d.frames(1); s = state()
    check(s['vx']*nx + s['vy']*ny > 0, 'even a fully open arm remains solid where it is drawn')
    place(90, 190); d.cmd('C 0'); d.frames(1)
    check(arm()['angle'] == 76, 'bank gate closes gradually when relocked')
    live.request('Q 1'); before = arm(); d.frames(10)
    check(arm() == before, 'pause freezes gate movement')
    live.request('Q 0'); d.frames(20)
    check(arm()['angle'] == 0, 'relocked gate returns to its stop')
    report = {'result': 'passed', 'checks': len(checks), 'cases': checks}
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    pictures[0].save(out / 'gate-swing.gif', save_all=True, append_images=pictures[1:], duration=130, loop=0)
    print(f'PASS: {len(checks)} hinged-gate checks, visual contact, both directions, reversed endpoints, bank locks and pause')
finally:
    assert t.close() == 0, t.bugs

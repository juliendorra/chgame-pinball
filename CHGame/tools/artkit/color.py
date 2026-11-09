"""Colours: hex, the panel's RGB565, OKLab, and hue-shifted ramps.

A picture's own colours are snapped to RGB565 as the panel shows them (the
card stores each palette entry truncated to 5-6-5 bits, spec/card.md), so the
PNG on the PC is what the screen shows. The menu's four fixed colours and the
rainbow colour are kept exact: the picture rule counts them by exact value.
"""
from __future__ import annotations

import numpy as np

# The menu's four (palette 11-14) and the rainbow colour (15): exact values.
CREAM = (255, 244, 214)
GREY = (128, 128, 128)
BLACK = (0, 0, 0)
RED = (214, 32, 32)
RAINBOW = (255, 0, 255)
FIXED = {"cream": CREAM, "grey": GREY, "black": BLACK, "red": RED, "rainbow": RAINBOW}
FIXED_INDEX = {"cream": 11, "grey": 12, "black": 13, "red": 14, "rainbow": 15}


def rgb(c):
    """'#RRGGBB', 'RRGGBB', 'RGB' or an (r, g, b) tuple -> (r, g, b) ints."""
    if isinstance(c, str):
        s = c.lstrip("#")
        if len(s) == 3:
            s = "".join(ch * 2 for ch in s)
        return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
    return tuple(int(v) for v in c[:3])


def hexs(c):
    r, g, b = rgb(c)
    return f"#{r:02X}{g:02X}{b:02X}"


def snap565(c):
    """The colour as the panel shows it: 5-6-5 bits, expanded back to 8."""
    r, g, b = rgb(c)
    r5, g6, b5 = r >> 3, g >> 2, b >> 3
    return (r5 << 3 | r5 >> 2, g6 << 2 | g6 >> 4, b5 << 3 | b5 >> 2)


# ---- OKLab (Bjorn Ottosson), for distances and ramps ---------------------------------

def _lin(u):
    u = np.asarray(u, dtype=np.float64)
    return np.where(u <= 0.04045, u / 12.92, ((u + 0.055) / 1.055) ** 2.4)


def _gam(u):
    u = np.clip(np.asarray(u, dtype=np.float64), 0, 1)
    return np.where(u <= 0.0031308, u * 12.92, 1.055 * u ** (1 / 2.4) - 0.055)


def srgb_to_oklab(c):
    """sRGB in 0..1, shape (..., 3) -> OKLab (..., 3)."""
    c = _lin(c)
    l = 0.4122214708 * c[..., 0] + 0.5363325363 * c[..., 1] + 0.0514459929 * c[..., 2]
    m = 0.2119034982 * c[..., 0] + 0.6806995451 * c[..., 1] + 0.1073969566 * c[..., 2]
    s = 0.0883024619 * c[..., 0] + 0.2817188376 * c[..., 1] + 0.6299787005 * c[..., 2]
    l, m, s = np.cbrt(l), np.cbrt(m), np.cbrt(s)
    return np.stack([0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
                     1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
                     0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s], axis=-1)


def oklab_to_srgb(L):
    L = np.asarray(L, dtype=np.float64)
    l = L[..., 0] + 0.3963377774 * L[..., 1] + 0.2158037573 * L[..., 2]
    m = L[..., 0] - 0.1055613458 * L[..., 1] - 0.0638541728 * L[..., 2]
    s = L[..., 0] - 0.0894841775 * L[..., 1] - 1.2914855480 * L[..., 2]
    l, m, s = l ** 3, m ** 3, s ** 3
    return _gam(np.stack([4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
                          -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
                          -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s], axis=-1))


def to_float(c):
    return np.array(rgb(c), dtype=np.float32) / 255.0


def lab(c):
    return srgb_to_oklab(to_float(c))


def mix(a, b, t):
    """a..b at t, in OKLab; returns '#RRGGBB'."""
    la, lb = lab(a), lab(b)
    c = oklab_to_srgb(la + (lb - la) * t)
    return hexs(tuple(int(round(v * 255)) for v in c))


def ramp(dark, light, n, hue_shift=0.0, sat_mid=1.0, snap=True):
    """n colours from `dark` to `light`, interpolated in OKLCh. hue_shift (in
    degrees) bends the hue along the way, as pixel artists do (shadows cooler,
    lights warmer); sat_mid > 1 boosts the chroma of the middle steps."""
    la, lb = lab(dark), lab(light)
    ca, cb = np.hypot(la[1], la[2]), np.hypot(lb[1], lb[2])
    ha, hb = np.arctan2(la[2], la[1]), np.arctan2(lb[2], lb[1])
    if ca < 1e-4:
        ha = hb
    if cb < 1e-4:
        hb = ha
    dh = (hb - ha + np.pi) % (2 * np.pi) - np.pi
    out = []
    for k in range(n):
        t = k / (n - 1) if n > 1 else 0.0
        L = la[0] + (lb[0] - la[0]) * t
        C = (ca + (cb - ca) * t) * (1 + (sat_mid - 1) * 4 * t * (1 - t))
        h = ha + dh * t + np.radians(hue_shift) * (t - 0.5) * 2 * t * (1 - t) * 2
        c = oklab_to_srgb(np.array([L, C * np.cos(h), C * np.sin(h)]))
        v = tuple(int(round(x * 255)) for x in c)
        out.append(hexs(snap565(v) if snap else v))
    return out


def luma(c):
    r, g, b = rgb(c)
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0

"""artkit: the visual menu's box art, painted (docs/cover-art.md).

A picture is painted in true colour on a supersampled canvas (canvas.py:
distance-field shapes, gradients, noise, 2D lighting; render3d.py: a small
ray marcher for props), turned into its 16 colours by a ramp-aware ordered
dither (quant.py), finished pixel by pixel (pixel.py), and crowned with its
title (title.py: a pixel font at its own size, from fontscout.py).
paint.py holds the hand-finishing tools: painting surfaces pixel by pixel
as levels on a ramp, clean lines, streaks, despeckling, glints, bevels.

    import artkit as ak
    P = ak.Palette({...11 named colours...}, ramps=[[...], ...])
    cv = ak.Canvas("#000000")
    ...paint...
    pic = cv.quantize(P, exclude=[the title's colours])
    ak.title(pic, ak.load_mask(HERE / "art" / "title.txt"), x, y, fill=[...], ...)
    return pic.image()                       # what boxart.png / bx.save take

    python -m artkit show RECIPE.py[:func] [--name N]    previews + lint in out/art/
    python -m artkit.fontscout ...                       titles
    python -m artkit.lint PNG ...                        the house checks
"""
from .color import ramp, mix, snap565, rgb, hexs, luma, CREAM, GREY, BLACK, RED, RAINBOW  # noqa: F401
from .canvas import (Canvas, circle, ellipse, box, rect, segment, polyline, polygon, star, ring, halfplane,  # noqa: F401
                     union, inter, sub, smin, cover, bezier, rotate, scale, homography, quad_uv, inside_uv,
                     sample, linear, radial, stops, lerp, noise, sphere_normal, dome, height_normal, light, rim,
                     shade, ramp_map, KEY)
from .quant import Palette, Picture, quantize, from_png, save_png  # noqa: F401
from .pixel import (shift, dilate, erode, edge, checker, outline, selout, drop_shadow, clean_orphans,  # noqa: F401
                    patch, sparkle, load_mask, mask_rows, place, Font)
from .title import title, centred_x, embolden, glow  # noqa: F401
from .paint import (by_level, levels, put_levels, terrace, cel, nbrs, thick, runs, outside_of,  # noqa: F401
                    distance_px, letters, raster, line_px, ink, streak, despeckle, lonely, glint, glint_in,
                    PIPS, pip_template, tube, path, hull, px_mean, at_px, up, ihash, bevel_contour, bevel_runs)
from . import render3d  # noqa: F401
from . import paint  # noqa: F401

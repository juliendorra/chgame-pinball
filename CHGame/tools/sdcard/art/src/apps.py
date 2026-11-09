r"""tools/sdcard/art/apps.png: the APPS folder's cover on the casino card (it
holds the STL Viewer and the SD Card Reader). `python tools/sdcard/covers.py`
redraws it; edit this, not the PNG. The folders' shared look is
folderkit.py, beside this file (cards.py is its worked example).

THE BRIEF (revision 2)
  Message: this way to the gadgets. Behind this door is the agent's kit:
  his gold watch throws a hologram of the world into the night, and a red SD
  card flies in to feed it. The folder's two apps in one picture: the STL
  Viewer's 3D made of light (its own cover is a watch projecting a model),
  the SD Card Reader's card.

  The owner chose to mix two looks here, on purpose: the folders' navy
  night and neon sign, with the apps' secret-agent look (green light on
  black, gold, red plastic). The night and the sign are the family's; the
  watch, its hologram and the card are the apps'.

  Composition (a folder: the sign over the door, then what is inside; read
  in this order):
  - The sign: APPS in the family's ice chrome on its navy panel and rainbow
    neon tube (folderkit.word), rows 1 to 48. Calm night beside it.
  - The hero: the hologram, an Earth of green light 49 px across, a little
    right of the middle (rows 53 to 102, its glow 3 px clear of the
    sign's), floating over the watch. Africa and Europe face us (real
    coastlines, coarse, projected on the sphere): the continents plates of
    light (grn1, burning grn2 where they face us and the lamp, through a 50%
    seam), the sea light you can see through (a checker of grn0 on navy2),
    a wireframe of meridians and parallels across the sea (clean 1-px grn1
    lines stopping at the coasts, short of the poles and of the limb), the
    glass glowing inside its limb (grn0), the limb a 2-px band (grn2 on the
    arc toward the lamp, grn1 round the rest) and a cream glint on it
    toward the lamp: the brightest, most saturated shape under the sign. Its light in the air: a ring of grn0 round it (solid,
    then a checker), and the night's sunburst centred on it.
  - The beam: from the watch's lens up to the globe: two 1-px grn1 edges
    from the lens to the globe's tangent points (grn2 where they cross the
    gold), the night between them lit by a 25% grn0 dither; four rows of
    night between the globe and the bezel, so it floats.
  - The watch: the agent's gold watch lying face up under the globe, 64 px
    across, its near half off the bottom frame. A gold bezel in crisp bands
    (its outer slope cream on a short arc toward the lamp, gold, wine where
    it turns away; its inner slope the other way round), twelve engraved
    notches (wine). A black dial: lume hour markers (grn1, grn2 at the
    quarters), gold hands (set across the dial, clear of the beam's edges)
    and a red seconds hand, the emitter's lens in the middle (a grn1 ring
    round a grn2 core), the hologram's light caught on the bezel's inner
    wall across the dial (grn0), a glint across the glass (cream to grey). A gold crown at 4 o'clock, gold lugs, and a wine
    leather strap curling away down both sides round an unseen wrist (a red
    line where its far edge catches the lamp).
  - The second: a red SD card flying in from the left toward the hologram,
    nearly upright (turned 18 degrees), its back to us: its cut corner at
    the top left, a cream bevel along it and the other lit edges, eight gold
    contacts (clean 1-px ribs) in a recessed wine row along its top, its
    edge showing on the shade side (wine), a green rim on the edge facing
    the hologram, a tapered cream gloss inside its left edge, a cream glint
    on its top corner. Three speed lines off its trailing edges, staggered
    (30, 22, 18 px), tapering from red to wine, curving back along the arc
    it fell on.
  - Behind: the family's night: a dome of glow and a sunburst of twelve
    navy rays centred on the globe (fading out below the sign), three
    twinkles in the open night, the vignette; the outer two rows and columns
    a step down.
  - Light: the house key from the top left (the bezel's cream arc, the
    card's bevel, gloss and glint, the globe's glint, the glass's glint);
    the hologram is the second light, green (the card's rim, the bezel's
    inner wall, the beam).
  Reading order: the sign; the glowing world; the red card; the gold watch.

  Thumbnail (128 x 128):
      +--------------------------------+
      |  .    [  A P P S  ]  neon    . |  rows 1-48: the sign
      |                                |
      | ~~  /''''|    ,-~~~~-,       . |  the card's trails, the card,
      | ~~ |  SD |   ( Africa )        |  the globe: an Earth of light
      |  ~ |_____|    `-____-'         |
      |                \    /          |  the beam
      |  \__,---===( ( o ) )===---,__/ |  the watch: gold bezel, strap
      +--------------------------------+

PALETTE (folderkit's 6 + 5 own + cream, grey, black, red; the rainbow is the neon)
  navy0 navy1 navy2   the night, its glow and rays; the hologram's sea (with grn0)
  ice0 ice1 ice2      the sign's face only: the title's reserved colours,
                      painted by nothing else
  grn0 grn1 grn2      the hologram's light: the globe, the beam, the lens, the
                      lume, the card's rim, the bezel's inner wall
  wine gold           the watch (gold lit, wine in shade and in the notches),
                      the strap, the card's contacts and edge, the trails' tails
  red cream grey black  the card, the strap's lit edge, the seconds hand;
                      glints, bevels, twinkles; outlines and the dial

LETTERING: BAZAR (bmf collection), "freeware; authors vary, few gave terms"
  (a `?` face: it wants the credits row in docs/cover-art.md), at its own
  size, from folderkit's word_apps.txt.

HOW IT IS PAINTED: on the pixels, from each thing's own geometry (no
render3d, no quantiser). The watch is a disc in perspective: each pixel's
(u, v) on its face (w_uv) chooses the band and its colour by the angle to
the lamp round the face; the strap is a surface drooping away from the
lugs; the case's side is the face swept down by its depth. The globe is a
sphere: each pixel's longitude and latitude decide land or sea (LAND below:
coastlines traced by hand, coarsely, for this picture), and the wireframe's
lines are projected and rasterised as clean 1-px polylines. The card is a
rectangle with a corner cut, turned in the picture's plane. The clean-up
(despeckle) runs before the hand-placed sparkle (glints, twinkles).
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import folderkit as fk  # noqa: E402  (puts the repository's tools/ on the path)
import numpy as np  # noqa: E402
import artkit as ak  # noqa: E402

YY, XX = fk.YY, fk.XX
X1, Y1 = XX + 0.5, YY + 0.5                                   # pixel centres
EDGE = np.minimum(np.minimum(XX, 127 - XX), np.minimum(YY, 127 - YY))

OWN = {"grn0": "#0B4C3E", "grn1": "#1FBF7E", "grn2": "#98FFC8", "wine": "#70102A", "gold": "#E8B03C"}
GREEN_R = ["black", "grn0", "grn1", "grn2", "cream"]
RED_R = ["black", "wine", "red", "cream"]
GOLD_R = ["black", "wine", "gold", "cream"]
STRAP_R = ["black", "wine", "red"]

LOOK = dict(centre=(80, 78), glow=(84, 66), rays=12, ray_reach=(20, 92), ray_k=1.2, spin=7.5,
            ray_width=0.4, ray_top=54)

# ---- the watch: its face is a disc; u runs along its strap (to the right), v
# across it (+ away from us), w up out of its face; lengths in its radius ----
WATCH = dict(c=(80.0, 120.0), R=32.0, k=0.42, tilt=-4.0, depth=0.20)
BEZEL = (0.74, 1.0)                     # the bezel ring: inner, outer radius
BEZEL_MID = 0.88                        # its crest: the outer slope beyond
CHAPTER = 0.64                          # the hour markers' radius
LENS = (0.16, 0.07)                     # the emitter's ring and hot core
CROWN = 60.0                            # where the crown sits (degrees round the face; 90 is away from us)
HANDS = [(196.0, 0.44, "gold"), (16.0, 0.64, "gold"), (-70.0, 0.58, "red")]   # hour, minute, seconds: angle, length, colour
                                        # (clear of the beam's edges, which rise steeply off the lens)
STRAP = dict(half=0.40, droop=0.55, start=0.86)
KEY = np.array([-0.55, 0.50, 0.67])     # the house key in the watch's frame (left, far, up)
KEY /= np.linalg.norm(KEY)
KEY_PHI = np.degrees(np.arctan2(KEY[1], KEY[0]))   # the lamp's direction round the face
CRYSTAL = ((-0.70, -0.12), (-0.50, 0.34))  # the glass's glint: from, to (u, v)

# ---- the hologram: an earth of light over the watch ----
GLOBE = dict(c=(80.0, 77.5), r=24.5, lon=12.0, lat=18.0, roll=-14.0)
MERIDIANS = 30                          # degrees apart
PARALLELS = (-60, -30, 0, 30, 60)
FRESNEL = 0.80                          # the glass glows on its own beyond this (of its radius)
TWINKLES = [(116, 28, 1), (12, 40, 1), (113, 62, 1)]   # stars in the open night: x, y, arm
HOT = (-0.18, -0.22, 0.62)              # the land's hot middle: offset (of its radius), reach
POLE_CLEAR = 3.5                        # the meridians stop this far (px) short of a pole
GLOBE_GLINT = 228.0                     # its glint on the limb (degrees; 270 is the top)

# ---- the card (its parameters) ----
CARD = dict(c=(27.0, 80.0), w=28.0, h=36.0, roll=18.0, cut=8.0, pads=8, edge=(1, 1),
            gloss=(2.0, -8.0), motion=(0.85, 0.53))
TRAILS = [(-1.0, 0.25, 30, 1.5, 0.3), (-1.0, -0.35, 22, 1.3, 0.3), (-0.75, 0.85, 18, 1.1, 0.3)]   # root (x, y in its halves), length, radii
TRAIL_BEND = 9.0
TRAIL_GAP = 3.0


# ---- the world, coarsely (lon, lat in degrees), for the hologram's continents --------------------
LAND = {
    "africa": [(-5.8, 35.8), (10, 37.2), (11, 33.5), (15, 32.3), (20, 30.8), (25, 31.8), (32.3, 31.2),
               (32.6, 29.9), (35.5, 24), (37.3, 21), (38.6, 18), (43.3, 12.6), (51.2, 11.8), (49, 6.5),
               (46, 2), (42, -1), (40.2, -6), (39.5, -10), (40.6, -15), (35.4, -21.5), (35.5, -24),
               (32.8, -27), (31, -29.8), (27, -33.8), (20, -34.8), (18.4, -33.9), (17, -29), (14.5, -24),
               (11.8, -17), (13.6, -12), (12.2, -6), (9.2, -1), (9.6, 3.8), (6.5, 4.3), (4, 6.4), (1.2, 6),
               (-4, 5.2), (-7.6, 4.4), (-11.2, 6.7), (-13.2, 8.5), (-15.3, 11), (-17.2, 14.6), (-16.2, 19),
               (-17, 21), (-15, 24.5), (-13, 27.7), (-9.8, 29.8), (-9.4, 32.6), (-6.8, 34.1)],
    "madagascar": [(43.3, -22), (44, -25), (47, -25), (50.3, -15.5), (49.3, -12), (46, -15.8), (44.2, -17.5)],
    "eurasia": [
        (-5.6, 36), (-9, 37), (-8.8, 42), (-9.3, 43.2), (-1.8, 43.4), (-1.2, 46.2), (-4.6, 48.4),
        (-1.4, 49.6), (1.7, 50.9), (4.4, 52.3), (8.5, 53.6), (8.2, 56.5), (10.5, 57.7), (10.4, 56),
        (10, 55), (11, 54.2), (14, 54), (19, 54.5), (21.2, 55.3), (21, 57), (24, 57.3), (23.6, 59.2),
        (30, 59.9), (25, 60.2), (22, 60.3), (21.5, 61.5), (21.5, 63.4), (25, 65), (22.5, 65.8),
        (21, 64.5), (17.5, 62.5), (18.8, 60), (16.5, 57.5), (16, 56.2), (14, 55.4), (12.8, 56),
        (11.8, 57.7), (10.6, 59.8), (8, 58), (5.6, 58.9), (5, 61.5), (7, 62.8), (10.5, 64), (12.5, 66),
        (15, 68), (18.9, 69.7), (25.8, 71.1), (30.8, 69.8), (33, 69.2), (36, 69), (41, 67), (44, 66.3),
        (44, 68.3), (53.5, 68.3), (59, 68.5), (66, 69.5), (69, 72.8), (72.8, 72.5), (80, 73.5),
        (87, 75), (100, 77.5), (105, 77.5), (113, 74), (128, 72.5), (140, 72.5), (150, 71.5),
        (160, 69.8), (170, 70), (180, 69), (180, 65), (178, 64), (178.5, 62.5), (173, 61), (164, 59.9),
        (163, 57), (160, 53), (156.5, 51), (156, 57), (160, 61), (152, 59.3), (143, 59.4), (138, 56.4),
        (137.5, 54), (141, 53.2), (140.5, 48.5), (138, 46.5), (135, 43.6), (132, 43.2), (130, 42.4),
        (129.7, 40.8), (129.4, 37), (129, 35.2), (126.5, 34.5), (126.4, 37.5), (124.8, 39.6),
        (121.5, 40.8), (118, 39.2), (119, 37.3), (122.6, 37.2), (120.5, 35.8), (119.5, 34.5),
        (121.8, 31.5), (121.9, 30), (120.5, 27.2), (119.5, 25.5), (116.8, 23.2), (113.8, 22.3),
        (110.3, 20.4), (109.6, 21.6), (107.5, 21.5), (106.5, 20), (105.7, 18.8), (107, 17),
        (108.9, 15.3), (109.3, 12), (107, 10.5), (105, 8.7), (104.8, 10.4), (103, 11.3), (102.3, 12.3),
        (100.9, 12.8), (100, 13.5), (99.2, 10.5), (100.3, 8), (101, 6.8), (103.4, 4.9), (104.3, 1.4),
        (103.4, 1.3), (101.3, 2.9), (98.3, 7.8), (98.6, 10), (97.7, 15.5), (95.3, 15.8), (94.3, 16.3),
        (94.6, 18.7), (92.5, 21), (91.5, 22.6), (88.6, 21.7), (86.9, 20.6), (85, 19.3), (82.3, 16.6),
        (80.3, 15.7), (80.2, 13), (79.8, 10.3), (77.5, 8.1), (76.2, 9.9), (74.8, 12.8), (73.4, 16),
        (72.8, 19), (72.6, 21.4), (70.3, 20.9), (68.9, 22.3), (68.5, 23.4), (67, 24.8), (66.6, 25.4),
        (61.6, 25.2), (58.8, 25.6), (57.3, 25.9), (56.6, 27.1), (54.5, 26.6), (51.6, 27.8), (50.2, 29.4),
        (48.6, 30), (48, 29.4), (49.6, 27), (50.2, 26.2), (51.5, 26.1), (51.6, 24.6), (54.4, 24.3),
        (56.1, 26.1), (56.4, 24.8), (58.5, 23.6), (59.8, 22.4), (58.6, 20.4), (57.8, 19), (55.4, 17.7),
        (52.2, 15.6), (49, 14.1), (45, 12.9), (43.4, 12.7), (42.8, 14.8), (42.6, 16.5), (41.2, 19),
        (39.1, 21.6), (38.4, 23.7), (36.9, 25.7), (35.1, 28.1), (34.9, 29.5), (34.2, 31.3), (35, 32.8),
        (35.9, 35), (36, 36.6), (34.6, 36.8), (32.5, 36.1), (30.6, 36.8), (29.6, 36.2), (28, 36.8),
        (27.2, 37.5), (26.4, 38.4), (26.8, 39.5), (26.2, 40.1), (26, 40.8), (24, 40.8), (22.6, 40.4),
        (22.9, 39.4), (23.2, 38.1), (24, 37.7), (22.5, 36.4), (21.7, 36.9), (21.1, 37.9), (20.7, 38.8),
        (20.1, 39.6), (19.4, 40.4), (19.5, 41.8), (18.5, 42.4), (17, 43.2), (15.8, 43.7), (14.9, 44.6),
        (13.8, 44.9), (13.6, 45.6), (12.4, 45.4), (12.3, 44.5), (13.6, 43.5), (14.7, 42.1), (16, 41.4),
        (17.4, 40.8), (18.5, 40.1), (17.1, 39.4), (16.5, 38.4), (15.7, 37.9), (16.1, 39.4), (15.6, 40.1),
        (14.3, 40.8), (12.6, 41.4), (11.2, 42.4), (10.5, 43), (10.3, 43.9), (8.8, 44.4), (7.5, 43.8),
        (6.6, 43.1), (4.8, 43.4), (3.2, 43.2), (3.2, 41.9), (2.2, 41.4), (0.8, 41), (-0.3, 39.5),
        (0.2, 38.8), (-0.7, 37.6), (-2.1, 36.7), (-4.4, 36.7)],
    "britain": [(-5.7, 50), (1.4, 51.2), (1.7, 52.7), (0.2, 53.5), (-1.6, 55.6), (-2, 57.6), (-3.3, 58.6),
                (-5, 58.6), (-6.2, 56.5), (-4.8, 54.8), (-3, 53.9), (-4.5, 53.3), (-4, 51.7), (-5.2, 51.7),
                (-3, 51.4)],
    "ireland": [(-6, 52.2), (-6.2, 54), (-7.3, 55.3), (-10, 54.2), (-10.3, 51.6), (-8, 51.6)],
    "iceland": [(-24, 65.5), (-22, 66.4), (-16, 66.5), (-13.5, 65.2), (-15, 64.2), (-20, 63.4), (-22.7, 63.9)],
    "greenland": [(-73, 78), (-60, 82), (-40, 83.5), (-22, 82.5), (-18, 78), (-20, 72), (-22, 70.5),
                  (-27, 68.2), (-32, 68.4), (-37, 65.8), (-40, 64.5), (-43, 60), (-48, 61), (-51, 64),
                  (-53.5, 66.5), (-54, 70), (-56, 72.5), (-58, 75.5), (-66, 76.5)],
    "samerica": [(-77, 8), (-72, 12), (-63, 10.7), (-60, 8.5), (-52, 5), (-50, 0), (-44, -2.5), (-35, -5.5),
                 (-35, -9), (-39, -13.5), (-39, -18), (-41, -22), (-45, -23.5), (-48.5, -26), (-49, -28.5),
                 (-53, -33.5), (-57, -36.5), (-57.5, -38), (-62, -39), (-65, -41), (-65, -45),
                 (-67.5, -46.5), (-69, -51), (-68.5, -53), (-71, -54), (-74.5, -51), (-73.5, -45),
                 (-73.5, -40), (-71.6, -33), (-70.5, -24), (-70.3, -18.5), (-75.5, -15), (-77, -12),
                 (-81, -6), (-80, -2), (-80.5, 1), (-78.5, 3), (-77.5, 7)],
    "namerica": [(-80.4, 25.2), (-80, 27), (-81.4, 30.5), (-81, 32), (-76.5, 35), (-76, 37), (-74, 40.5),
                 (-70, 41.6), (-70.5, 43), (-67, 44.8), (-65.7, 43.5), (-60, 46), (-64, 49), (-60, 50.2),
                 (-56, 51.5), (-56, 53.5), (-60, 55.3), (-62, 57.5), (-64.5, 60.3), (-70, 62), (-78, 62.5),
                 (-78.5, 58), (-76.5, 56), (-79, 54), (-80, 51.5), (-82.3, 52.9), (-87, 55.8), (-92.5, 57),
                 (-94.5, 59), (-94, 61.5), (-90, 63.5), (-86.5, 66.5), (-90, 69), (-96, 68), (-108, 68),
                 (-115, 68.8), (-124, 69.5), (-131, 69.7), (-141, 69.6), (-156, 71.3), (-162, 70),
                 (-166.5, 68.3), (-163, 66.5), (-168, 65.6), (-161, 64.5), (-165, 62.3), (-165, 60.5),
                 (-158, 58.7), (-162, 55.8), (-153, 57.5), (-150, 61), (-146, 60.5), (-140, 59.8),
                 (-136, 58), (-133, 55), (-130.5, 54), (-128, 51), (-124.7, 48.4), (-124, 46),
                 (-124.5, 42), (-123.8, 39.5), (-122.5, 37.5), (-120.6, 34.5), (-118.4, 34), (-117.1, 32.5),
                 (-116, 30), (-114.1, 28), (-112, 25.5), (-110, 23), (-112.5, 28.5), (-114.8, 31.7),
                 (-112.5, 29), (-109.5, 25.5), (-105.5, 21.5), (-105.5, 20), (-102, 18), (-98, 16),
                 (-94.5, 16.2), (-92, 14.5), (-87.5, 13), (-85.7, 11), (-83.5, 8.5), (-80, 7.3), (-77.5, 8.4),
                 (-79.5, 9.5), (-81.6, 9), (-83.6, 10.9), (-83.2, 15), (-87.5, 15.9), (-88.3, 18.5),
                 (-87.5, 21.5), (-90.4, 21.2), (-91, 19), (-94.5, 18.2), (-96.3, 19.5), (-97.5, 22),
                 (-97.2, 25.8), (-97.5, 27.5), (-94.5, 29.5), (-90, 29.2), (-89, 30.3), (-85.2, 29.7),
                 (-82.7, 27.8), (-81.2, 25.3)],
    "cuba": [(-85, 21.9), (-82, 23.1), (-77, 21.2), (-74.2, 20.2), (-77.5, 19.9), (-81, 21.7)],
    "australia": [(113.5, -22), (114, -26), (115, -34), (118, -35), (123.5, -34), (129, -31.5), (135, -34.5),
                  (138, -35.5), (140, -38), (146.5, -39), (150, -37.5), (153.5, -28), (153, -25), (150, -22),
                  (146, -19), (145.5, -15), (143.5, -14), (142.5, -10.7), (141.5, -13), (141.5, -17),
                  (139.5, -17.5), (137, -16), (135.5, -14.5), (136.5, -12), (132.5, -11.5), (130, -13),
                  (129.5, -15), (126, -14), (123, -17), (121, -19.5), (117, -20.7)],
    "sumatra": [(95.2, 5.6), (98, 4), (104, -2.5), (106, -5.9), (104.5, -5.9), (101, -2.5), (98.7, 1.7)],
    "borneo": [(109.2, 0), (110, -3), (114, -4), (116, -3.3), (118, 1), (119, 5), (117, 7), (115.5, 5),
               (113, 3), (111, 1.9)],
    "japan": [(130, 31), (131, 33.9), (135, 33.5), (136.8, 34.5), (139.8, 35), (140.8, 35.7), (141, 38.5),
              (142, 39.5), (141.5, 41.5), (140, 41.4), (140, 39), (138, 37.5), (136.8, 37.3), (136, 35.6),
              (133, 35.5), (131, 34.5), (129.7, 33.3)],
    "srilanka": [(79.8, 8), (80.2, 9.8), (81.9, 7.5), (81.2, 6.1), (80, 6.2)],
}
WATER = {
    "blacksea": [(28, 41.5), (29, 41.2), (31, 41.2), (35, 42), (38, 41), (41.5, 41.5), (41.6, 43), (38.5, 44.5),
                 (37, 45.2), (33.5, 44.5), (32.5, 45.4), (31, 46.6), (30, 45.2), (28.7, 44), (27.9, 42.5)],
    "caspian": [(47, 44.5), (49, 46.5), (52, 46.8), (53, 45), (51, 43), (53, 41.5), (54, 38), (51, 36.7),
                (49, 37.5), (49.5, 40), (47.5, 42)],
    "hudson": [(-78, 62.4), (-78.5, 58), (-76.5, 56), (-79, 54), (-80, 51.5), (-82.3, 52.9), (-87, 55.8),
               (-92.5, 57), (-94.5, 59), (-94, 61.5), (-90, 63.5), (-86, 64.5), (-82, 64)],
}


def inside(lon, lat, pts):
    """Which points (lon, lat) lie inside the polygon (degrees)."""
    return ak.polygon((lon, lat), pts) < 0


# ---- the watch's frame on the picture ----------------------------------------------------------

def w_axes():
    t = np.radians(WATCH["tilt"])
    A = np.array([np.cos(t), np.sin(t)])                 # u: along the strap, to the right
    B = np.array([np.sin(t), -np.cos(t)])                # v: away from us (up the picture)
    return A, B


def w_px(u, v, w=0.0):
    """A point of the watch (its frame) on the picture."""
    A, B = w_axes()
    R, k = WATCH["R"], WATCH["k"]
    c = np.asarray(WATCH["c"])
    return c + R * (np.multiply.outer(u, A) + np.multiply.outer(k * np.asarray(v) + np.sqrt(1 - k * k) * np.asarray(w), B))


def w_uv(X, Y, w=0.0):
    """The watch's (u, v) under the picture's points, on the plane at height w."""
    A, B = w_axes()
    R, k = WATCH["R"], WATCH["k"]
    dx, dy = X - WATCH["c"][0], Y - WATCH["c"][1]
    u = (dx * A[0] + dy * A[1]) / R
    vb = (dx * B[0] + dy * B[1]) / R                     # A and B are orthonormal
    v = (vb - np.sqrt(1 - k * k) * w) / k
    return u, v


def view_dir():
    k = WATCH["k"]
    return np.array([0.0, -np.sqrt(1 - k * k), k])


def lit(n, spec_k=40.0):
    """Diffuse and specular from the key for normals n (..., 3) in the watch's frame."""
    dif = np.clip(n @ KEY, 0, 1)
    h = KEY + view_dir()
    h /= np.linalg.norm(h)
    spec = np.clip(n @ h, 0, 1) ** spec_k
    return dif, spec


# ---- small helpers -----------------------------------------------------------------------------

def line_mask(pts, closed=False):
    """A clean 1-px line through the points (no L corners), as a mask."""
    m = np.zeros((128, 128), bool)
    pts = list(pts) + ([pts[0]] if closed else [])
    for x_, y_ in ak.line_px(pts):
        if 0 <= x_ < 128 and 0 <= y_ < 128:
            m[y_, x_] = True
    return m


def runs_of(pts, keep):
    """The continuous runs of points where keep is True."""
    out, cur = [], []
    for p_, k in zip(pts, keep):
        if k:
            cur.append(p_)
        elif cur:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return [r for r in out if len(r) > 1]


def facing(m, dx, dy, n=2):
    """How much each pixel's outward normal (from the smoothed mask) faces (dx, dy): -1..1."""
    b = fk._blur(m, n)
    gy, gx = np.gradient(b)
    nx, ny = -gx, -gy
    nn = np.hypot(nx, ny) + 1e-9
    return (nx * dx + ny * dy) / (nn * np.hypot(dx, dy))


DOWN = {"cream": "grey", "grey": "navy2", "gold": "wine", "red": "wine", "wine": "black", "grn2": "grn1",
        "grn1": "grn0", "grn0": "black", "navy2": "navy1", "navy1": "navy0", "navy0": "black"}


def step_down(pic, m):
    """Every colour under m a step darker (DOWN), all read from the pixels as they were."""
    cur = pic.idx.copy()
    for a_, b_ in DOWN.items():
        pic.put(m & (cur == pic.pal[a_]), b_)


# ---- the watch ---------------------------------------------------------------------------------

def strap():
    """The strap on both sides of the case, curling down out of sight round an unseen wrist:
    dark leather, its top lit where it turns to the lamp, a lit line along its far edge.
    Returns its mask, a level per pixel (STRAP_R) and its far edge."""
    s = STRAP
    u, _ = w_uv(X1, Y1)
    a = np.clip(np.abs(u) - s["start"], 0, None)
    w = -s["droop"] * a * a
    u, v = w_uv(X1, Y1, w)
    m = (np.abs(u) > s["start"]) & (np.abs(v) < s["half"])
    dw = -2 * s["droop"] * a * np.sign(u)                       # dw/du
    n = np.stack([-dw, np.zeros_like(dw), np.ones_like(dw)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    dif, _ = lit(n)
    lv = 0.6 + 1.0 * dif ** 2
    far = m & (v > s["half"] - 0.12)
    return m, lv, far


def paint_watch(pic):
    depth = WATCH["depth"]
    u, v = w_uv(X1, Y1)
    rho = np.hypot(u, v)
    phi = np.arctan2(v, u)
    vig = fk.edge_dark(X1, Y1)
    # the strap, under the case
    sm, slv, sfar = strap()
    ak.by_level(pic, fk.terrace_px(slv - vig * 1.5, 1.0), STRAP_R, sm, q=2)
    pic.put(sfar & (slv - vig * 1.5 > 1.0), "red")
    # the lugs: gold horns holding it
    lug = (np.abs(u) > 0.84) & (np.abs(u) < 1.12) & (np.abs(np.abs(v) - 0.31) < 0.085)
    pic.put(lug, "gold")
    pic.put(lug & (u > 0), "wine")
    pic.put(lug & (u < 0) & (v > 0), "cream")
    # the case's side: the face's disc swept down by its depth
    side = np.zeros((128, 128), bool)
    sphi = np.zeros((128, 128))
    for s in np.linspace(0, depth, 12):
        us, vs = w_uv(X1, Y1, -s)
        r_ = np.hypot(us, vs)
        hit = (r_ < 0.97) & ~side
        sphi = np.where(hit, np.arctan2(vs, us), sphi)
        side |= r_ < 0.97
    top = rho < BEZEL[1]
    side &= ~top
    c = np.cos(sphi - np.radians(KEY_PHI))
    ak.by_level(pic, fk.terrace_px(1.55 + 0.9 * c - vig, 1.0), GOLD_R, side, q=2)
    # the crown, at 4 o'clock (12 is at the left, where the strap leaves)
    ca = np.radians(CROWN)
    cu, cv = np.cos(ca), np.sin(ca)
    along = u * cu + v * cv
    perp = -u * cv + v * cu
    crown = (along > 0.95) & (along < 1.15) & (np.abs(perp) < 0.11) & ~top
    pic.put(crown, "gold")
    pic.put(crown & (perp > 0.04), "cream")
    pic.put(crown & (perp < -0.04), "wine")
    # the bezel: a rounded gold ring in crisp bands: its outer slope cream on a short arc toward
    # the lamp, gold, wine where it turns away; its inner slope the other way round
    bz = top & (rho >= BEZEL[0])
    c = np.cos(phi - np.radians(KEY_PHI))
    outer = bz & (rho > BEZEL_MID)
    inner = bz & ~outer
    pic.put(outer, "gold")
    pic.put(outer & (c < -0.45), "wine")
    pic.put(outer & (c > 0.80) & (rho > 0.955), "cream")
    pic.put(inner, "gold")
    pic.put(inner & (c > 0.72), "wine")
    # its engraved marks: a notch every five minutes, cut across the gold
    for h in range(12):
        a = np.radians(180 - 30 * h)
        pts = [w_px(r * np.cos(a), r * np.sin(a)) for r in (BEZEL[0] + 0.02, BEZEL[1] - 0.03)]
        notch = line_mask(pts) & bz & pic.where("gold")
        pic.put(notch, "wine")
    # the dial: black, its hour markers glowing green, the emitter's lens in the middle; the
    # hologram's light caught on the bezel's inner wall across the dial from us
    dial = top & (rho < BEZEL[0])
    pic.put(dial, "black")
    wall = dial & ~ak.erode(dial, 1) & (v > 0.25)
    pic.put(wall, "grn0")
    for h in range(12):
        a = np.radians(180 - 30 * h)
        big = h % 3 == 0
        r0, r1 = (CHAPTER - 0.08, CHAPTER + 0.06) if big else (CHAPTER - 0.03, CHAPTER + 0.03)
        pts = [w_px(r * np.cos(a), r * np.sin(a)) for r in (r0, r1)]
        pic.put(line_mask(pts) & dial, "grn2" if big else "grn1")
    # the hands
    for ang, ln, col in HANDS:
        a = np.radians(ang)
        pts = [w_px(0.0, 0.0), w_px(ln * np.cos(a), ln * np.sin(a))]
        pic.put(line_mask(pts) & dial, col)
    lens = dial & (rho < LENS[0])
    pic.put(lens, "grn1")
    pic.put(dial & (rho < LENS[1]), "grn2")
    return dict(top=top, side=side, strap=sm, bezel=bz, dial=dial, crown=crown, lug=lug,
                all=top | side | sm | crown | lug)


def crystal_glint(pic, W):
    """The watch glass catching the lamp: one tapered streak across the dial's upper left."""
    a, b = CRYSTAL
    ak.ink(pic, [w_px(*a), w_px(*b)], "cream", where=W["dial"], colours=[("cream", 0.45), ("grey", 1.0)])


# ---- the hologram ------------------------------------------------------------------------------

def g_rot():
    """Globe coordinates (x toward lon 90E, y north, z toward lon 0) to the view (x right, y up, z to us)."""
    g = GLOBE
    lo, la, ro = np.radians(g["lon"]), np.radians(g["lat"]), np.radians(g["roll"])
    Ry = np.array([[np.cos(lo), 0, -np.sin(lo)], [0, 1, 0], [np.sin(lo), 0, np.cos(lo)]])   # lon0 to the front
    Rx = np.array([[1, 0, 0], [0, np.cos(la), -np.sin(la)], [0, np.sin(la), np.cos(la)]])   # the north tipped to us
    Rz = np.array([[np.cos(ro), -np.sin(ro), 0], [np.sin(ro), np.cos(ro), 0], [0, 0, 1]])
    return Rz @ Rx @ Ry


def sph(lon, lat):
    lo, la = np.radians(lon), np.radians(lat)
    return np.stack([np.cos(la) * np.sin(lo), np.sin(la), np.cos(la) * np.cos(lo)], -1)


def g_px(p):
    """View coordinates on the unit sphere to the picture."""
    g = GLOBE
    return g["c"][0] + g["r"] * p[..., 0], g["c"][1] - g["r"] * p[..., 1]


def globe_lonlat():
    g = GLOBE
    dx, dy = (X1 - g["c"][0]) / g["r"], -(Y1 - g["c"][1]) / g["r"]
    rr = dx * dx + dy * dy
    dz = np.sqrt(np.clip(1 - rr, 0, 1))
    q = np.stack([dx, dy, dz], -1) @ g_rot()                      # view to globe (the inverse: transpose)
    lon = np.degrees(np.arctan2(q[..., 0], q[..., 2]))
    lat = np.degrees(np.arcsin(np.clip(q[..., 1], -1, 1)))
    return lon, lat, np.sqrt(rr)


def land_mask():
    lon, lat, rr = globe_lonlat()
    m = np.zeros((128, 128), bool)
    for pts in LAND.values():
        m |= inside(lon, lat, pts)
    for pts in WATER.values():
        m &= ~inside(lon, lat, pts)
    return m & (rr < 1)


def globe_lines():
    """The wireframe's front runs on the picture: [points]."""
    M = g_rot()
    out = []
    t = np.linspace(-90, 90, 91)
    for lo in np.arange(-180, 180, MERIDIANS):
        out.append(sph(np.full_like(t, lo), t))
    t = np.linspace(-180, 180, 181)
    for la in PARALLELS:
        out.append(sph(t, np.full_like(t, la)))
    runs = []
    for pts in out:
        v = pts @ M.T
        px = list(zip(*g_px(v)))
        for run in runs_of(px, list(v[:, 2] > 0.12)):
            runs.append(run)
    return runs


def paint_globe(pic):
    g = GLOBE
    gx, gy, r = g["c"][0], g["c"][1], g["r"]
    rr = np.hypot(X1 - gx, Y1 - gy) / r
    disc = rr < 1.0
    # its light in the air: a ring of green on the night round it
    bloom = (rr >= 1.0) & (rr < 1.0 + 3.2 / r)
    dark = pic.where("black", "navy0", "navy1", "navy2")
    pic.put(bloom & dark & ((rr < 1.0 + 1.2 / r) | ak.checker()), "grn0")
    # the sea: light you can see through (a checker of the glow and the night)
    pic.put(disc, "navy2")
    pic.put(disc & ak.checker(), "grn0")
    fres = disc & (rr > FRESNEL)
    pic.put(fres, "grn0")
    # the land: lit plates of light (islands smaller than 3 px left out)
    land = land_mask()
    lab = ak.letters(land)
    size = np.bincount(lab.reshape(-1))
    land &= size[lab] >= 3
    pic.put(land, "grn1")
    # it burns brightest where it faces us and the lamp (a 50% seam round that)
    hx, hy = gx + HOT[0] * r, gy + HOT[1] * r
    rh = np.hypot(X1 - hx, Y1 - hy) / r
    pic.put(land & (rh < HOT[2]), "grn2")
    pic.put(land & (rh >= HOT[2]) & (rh < HOT[2] + 0.08) & ak.checker(), "grn2")
    # turning away toward the limb, it thins into the glass's own glow (a pixel's seam)
    pic.put(land & (rr > FRESNEL + 0.05), "grn0")
    pic.put(land & (rr > FRESNEL) & (rr <= FRESNEL + 0.05) & ak.checker(), "grn0")
    # the wireframe: bright lines across the sea, stopping at the coasts
    L = np.zeros((128, 128), bool)
    for run in globe_lines():
        L |= line_mask(run)
    L &= disc & ~ak.dilate(~disc, 3)
    for pole in (sph(0.0, 90.0), sph(0.0, -90.0)):                 # no knots where the meridians meet
        q = pole @ g_rot().T
        if q[2] > 0:
            px_, py_ = g_px(q)
            L &= np.hypot(X1 - px_, Y1 - py_) > POLE_CLEAR
    pic.put(L & ~land, "grn1")
    # the limb: a 2-px band, grn2 toward the lamp
    limb = disc & (rr > 1.0 - 2.0 / r)
    ang = np.degrees(np.arctan2(Y1 - gy, X1 - gx))               # -90 is up
    hot = (ang > -175) & (ang < -40)
    pic.put(limb, "grn1")
    pic.put(limb & hot, "grn2")
    return disc


def globe_glint(pic):
    """The hologram's brightest point: a glint on its limb, toward the lamp."""
    g = GLOBE
    a0 = np.radians(GLOBE_GLINT)
    gx = int(np.floor(g["c"][0] + (g["r"] - 1.0) * np.cos(a0)))
    gy = int(np.floor(g["c"][1] + (g["r"] - 1.0) * np.sin(a0)))
    ak.glint(pic, gx, gy, arms=(3, 3, 3, 3), tip="grn2")


def beam_geom():
    """The beam from the emitter's lens up to the globe: its edges' ends."""
    g = GLOBE
    ex, ey = w_px(0.0, 0.0)
    gx, gy, r = g["c"][0], g["c"][1], g["r"]
    lx, ly = w_px(-LENS[0], 0.0)
    rx, ry = w_px(LENS[0], 0.0)
    out = []
    for (px, py), sgn in (((lx, ly), -1), ((rx, ry), 1)):
        dx, dy = px - gx, py - gy
        d = np.hypot(dx, dy)
        a = np.arctan2(dy, dx)
        b = np.arccos(r / d)
        t = a - sgn * b
        out.append(((px, py), (gx + r * np.cos(t), gy + r * np.sin(t))))
    return (ex, ey), out


def paint_beam(pic, W):
    (ex, ey), ((l0, l1), (r0, r1)) = beam_geom()
    cone = ak.polygon((X1, Y1), [l0, l1, (GLOBE["c"][0], GLOBE["c"][1]), r1, r0]) < 0
    dark = pic.where("black", "navy0", "navy1", "navy2")
    fill = cone & dark & ~W["bezel"] & ~W["dial"]
    pic.put(fill & ((XX + YY) % 2 == 0) & (YY % 2 == 0), "grn0")
    edges = line_mask([l0, l1]) | line_mask([r0, r1])
    pic.put(edges & ~W["bezel"], "grn1")
    pic.put(edges & W["bezel"], "grn2")
    return cone


# ---- the card ----------------------------------------------------------------------------------

def card_axes():
    t = np.radians(CARD["roll"])
    ax = np.array([np.cos(t), np.sin(t)])                # its x (across) on the picture
    ay = np.array([np.sin(t), -np.cos(t)])               # its y (toward the contacts' edge)
    return ax, ay


def card_xy(X, Y):
    ax, ay = card_axes()
    dx, dy = X - CARD["c"][0], Y - CARD["c"][1]
    return dx * ax[0] + dy * ax[1], dx * ay[0] + dy * ay[1]


def card_px(x, y):
    ax, ay = card_axes()
    return CARD["c"][0] + x * ax[0] + y * ay[0], CARD["c"][1] + x * ax[1] + y * ay[1]


def card_mask():
    x, y = card_xy(X1, Y1)
    hw, hh, cut = CARD["w"] / 2, CARD["h"] / 2, CARD["cut"]
    m = (np.abs(x) < hw) & (np.abs(y) < hh)
    m &= (x + hw) + (hh - y) > cut                     # the cut corner at (-x, +y): its back is to us
    return m


def paint_card(pic):
    """The SD card, its back to us: red plastic, the gold contacts in a row along its leading
    edge (the cut corner's), its edge showing on the shade side (wine), a cream bevel on the
    edges facing the lamp, a green rim where it faces the hologram, a tapered gloss."""
    m = card_mask()
    x, y = card_xy(X1, Y1)
    hw, hh, cut = CARD["w"] / 2, CARD["h"] / 2, CARD["cut"]
    # its thickness: the face pushed back along the shade side
    dx, dy = CARD["edge"]
    thick = ak.shift(m, dx, dy) & ~m
    pic.put(thick, "wine")
    # the face: red, falling to wine in a narrow band toward the corner away from the lamp
    lv = 2.0 - np.clip((x / hw * 0.5 - y / hh * 0.5) - 0.30, 0, 1) * 1.7
    ak.by_level(pic, fk.terrace_px(lv, 1.0), RED_R, m, q=2)
    ring = m & ~ak.erode(m, 1)
    lamp = facing(m, -1, -1.3)
    holo = facing(m, GLOBE["c"][0] - CARD["c"][0], GLOBE["c"][1] - CARD["c"][1])
    # the contacts: gold pads in a recessed (wine) row along the leading edge
    c0, c1, n_ = 1.6, 7.6, CARD["pads"]
    span0, span1 = -hw + cut - 0.4, hw - 1.6
    pitch = (span1 - span0) / n_
    pocket = m & (y > hh - c1) & (x > span0 - 0.5) & (x < span1)
    pic.put(pocket & ~ring, "wine")
    pads = np.zeros((128, 128), bool)
    for k_ in range(n_):
        xk = span0 + (k_ + 0.5) * pitch
        pads |= line_mask([card_px(xk, hh - c1 + 1.2), card_px(xk, hh - c0 - 0.6)])
    pic.put(pads & pocket & ~ring, "gold")
    # the bevel and the rims
    pic.put(ring & (lamp > 0.35), "cream")
    pic.put(ring & (holo > 0.6) & (lamp <= 0.35), "grn1")
    # the gloss: a tapered streak a pixel in from the lit long edge
    g0, g1 = CARD["gloss"]
    ak.ink(pic, [card_px(-hw + 2.0, g0), card_px(-hw + 2.0, g1)], "cream", where=ak.erode(m, 1),
           colours=[("cream", 0.55), ("red", 1.0)])
    return m | thick


def card_trails(pic):
    """Speed lines off its trailing edges, curving back up the arc it fell along."""
    mx, my = CARD["motion"]
    nm = np.hypot(mx, my)
    mx, my = mx / nm, my / nm
    px_, py_ = -my, mx                                     # the way its path bends, looking back
    hw, hh = CARD["w"] / 2, CARD["h"] / 2
    for rx, ry, L, r0, r1 in TRAILS:
        sx, sy = card_px(rx * hw, ry * hh)
        sx, sy = sx - mx * TRAIL_GAP, sy - my * TRAIL_GAP
        mid = (sx - mx * L * 0.55, sy - my * L * 0.55)
        end = (sx - mx * L + px_ * TRAIL_BEND * L / 30, sy - my * L + py_ * TRAIL_BEND * L / 30)
        ak.streak(pic, (sx, sy), mid, end, r0, r1, ok=(YY >= fk.OBJECT_TOP + 1) & (EDGE >= 3),
                  cols=(("red", 0.35), ("wine", 1.0)))


def card_glint(pic, m):
    ys, xs = np.nonzero(m)
    j = np.argmin(ys + 0.6 * xs)                                   # its corner nearest the lamp
    ak.glint(pic, int(xs[j]) + 1, int(ys[j]) + 1, arms=(3, 3, 3, 3), tip="grey")


# ---- the picture -------------------------------------------------------------------------------

def draw():
    P = fk.palette(OWN, ramps=[GREEN_R, RED_R, GOLD_R])
    pic = ak.Picture.blank(P, "navy0")
    below = YY >= fk.OBJECT_TOP
    fk.put_sky(pic, **LOOK)
    ak.despeckle(pic, 5, within=below)
    W = paint_watch(pic)
    fk.selout(pic, W["all"], "black")
    cone = paint_beam(pic, W)
    card_trails(pic)
    C = paint_card(pic)
    fk.selout(pic, C, "black")
    disc = paint_globe(pic)
    # the frame: the outer two rows and columns a step down; then the clean-up (lone pixels take
    # their neighbours' colour), and only then the hand-placed sparkle
    step_down(pic, (EDGE < 2) & below)
    ak.despeckle(pic, 4, within=below)
    ak.despeckle(pic, 3, within=disc | (cone & ~W["all"]))
    crystal_glint(pic, W)
    card_glint(pic, card_mask())
    globe_glint(pic)
    for x_, y_, size in TWINKLES:
        fk.twinkle(pic, x_, y_, "grey", size)
    fk.word(pic, "apps", glints=[(3, 4, 2)])
    return pic.image()


if __name__ == "__main__":
    sys.path.insert(0, str(HERE.parents[2]))                  # the repository's tools/
    import boxart
    print(boxart.save(draw(), HERE.parent / "apps.png"))

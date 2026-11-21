#!/usr/bin/env python3
"""AERIDOR - The Poster for a Place That Isn't There.

A vintage travel poster for AERIDOR, the isles above the cloud sea:
floating islands at sunset, one great lighthouse on the central isle,
a huge low sun, and a sea of clouds below. Pure stdlib (zlib/struct/math).
Writes /output/entry.png (1024x1024 PNG).
"""

import math
import os
import random
import struct
import time
import zlib

W = H = 1024
OUT = "/output/entry.png"

# ---------------------------------------------------------------- palette
CREAM = (247, 232, 200)
CREAM_SOFT = (255, 240, 214)
INK = (26, 18, 58)          # deep indigo silhouette / text shadow
SKY_TOP = (27, 27, 77)
SKY_MID1 = (91, 42, 110)
SKY_MID2 = (180, 74, 122)
SKY_MID3 = (240, 138, 60)
SKY_HORIZON = (255, 196, 107)
SUN_CORE = (255, 233, 168)
SUN_HALO = (255, 190, 110)
ROCK = (43, 28, 74)
ROCK_LIT = (74, 44, 96)
CLOUD1 = (255, 232, 201)    # warm cream clouds
CLOUD2 = (247, 184, 160)    # pink clouds
CLOUD3 = (201, 168, 216)    # lavender clouds
CLOUD4 = (255, 214, 170)
LIGHT_BEAM = (255, 226, 150)
WINDOW = (255, 205, 110)

# ------------------------------------------------------------------ buffer
buf = [bytearray(W * 3) for _ in range(H)]


def lerp(a, b, t):
    return a + (b - a) * t


def grad_color(stops, t):
    """stops: list of (pos, (r,g,b)); t in [0,1]."""
    for i in range(len(stops) - 1):
        p0, c0 = stops[i]
        p1, c1 = stops[i + 1]
        if t <= p1:
            f = 0.0 if p1 == p0 else (t - p0) / (p1 - p0)
            return (round(lerp(c0[0], c1[0], f)),
                    round(lerp(c0[1], c1[1], f)),
                    round(lerp(c0[2], c1[2], f)))
    return stops[-1][1]


def span(y, x0, x1, rgb):
    """Fill inclusive x-range on row y with a solid colour."""
    if y < 0 or y >= H:
        return
    if x0 < 0:
        x0 = 0
    if x1 >= W:
        x1 = W - 1
    if x1 < x0:
        return
    n = x1 - x0 + 1
    buf[y][x0 * 3:(x1 + 1) * 3] = bytes(rgb) * n


def blend_span(y, x0, x1, rgb, alpha):
    """Alpha-blend a span over existing pixels (alpha 0..1)."""
    if y < 0 or y >= H:
        return
    x0 = max(0, x0)
    x1 = min(W - 1, x1)
    if x1 < x0:
        return
    row = buf[y]
    ia = 1.0 - alpha
    r, g, b = rgb
    for x in range(x0, x1 + 1):
        i = x * 3
        row[i] = round(r * alpha + row[i] * ia)
        row[i + 1] = round(g * alpha + row[i + 1] * ia)
        row[i + 2] = round(b * alpha + row[i + 2] * ia)


def rect(x, y, w, h, rgb):
    for yy in range(y, y + h):
        span(yy, x, x + w - 1, rgb)


def disc(cx, cy, r, rgb):
    r2 = r * r
    for dy in range(-r, r + 1):
        dx = math.isqrt(r2 - dy * dy)
        span(cy + dy, cx - dx, cx + dx, rgb)


def disc_blend(cx, cy, r, rgb, alpha):
    r2 = r * r
    for dy in range(-r, r + 1):
        dx = math.isqrt(r2 - dy * dy)
        blend_span(cy + dy, cx - dx, cx + dx, rgb, alpha)


def ellipse(cx, cy, rx, ry, rgb):
    for dy in range(-ry, ry + 1):
        t = dy / ry
        dx = int(rx * math.sqrt(max(0.0, 1.0 - t * t)))
        span(cy + dy, cx - dx, cx + dx, rgb)


# ------------------------------------------------------------------- font
# 5x7 bitmap font, '1' = on. Rows top to bottom.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    '*': ("00000", "00100", "10101", "01110", "10101", "00100", "00000"),
}


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def draw_text(x, y, text, scale, color, shadow=None, shadow_dx=None):
    """Draw text; shadow (optional) is drawn offset first."""
    if shadow is not None:
        dx = shadow_dx if shadow_dx is not None else max(2, scale // 4)
        _draw_text_raw(x + dx, y + dx, text, scale, shadow)
    _draw_text_raw(x, y, text, scale, color)


def _draw_text_raw(x, y, text, scale, color):
    cx = x
    for ch in text:
        glyph = FONT.get(ch, FONT[' '])
        for row_i, row in enumerate(glyph):
            yy = y + row_i * scale
            for col_i, bit in enumerate(row):
                if bit == '1':
                    if scale > 1:
                        for sy in range(scale):
                            span(yy + sy, cx + col_i * scale,
                                 cx + (col_i + 1) * scale - 1, color)
                    else:
                        span(yy, cx, cx, color)
        cx += 6 * scale


# ------------------------------------------------------------------ scene
def paint_sky():
    stops = [
        (0.00, SKY_TOP),
        (0.28, SKY_MID1),
        (0.50, SKY_MID2),
        (0.72, SKY_MID3),
        (1.00, SKY_HORIZON),
    ]
    # Sky occupies y=14..640 (inside frame); below is cloud sea.
    for y in range(14, 641):
        t = (y - 14) / (641 - 14)
        c = grad_color(stops, t)
        buf[y][14 * 3:1010 * 3] = bytes(c) * (1010 - 14)


def paint_stars(rng):
    for _ in range(70):
        x = rng.randint(30, 994)
        y = rng.randint(26, 300)
        s = rng.choice((1, 1, 2))
        a = rng.choice((0.35, 0.55, 0.8))
        disc_blend(x, y, s, CREAM_SOFT, a)


def paint_sun():
    # Halo rings, then bright core.
    disc_blend(512, 452, 168, SUN_HALO, 0.18)
    disc_blend(512, 452, 138, SUN_HALO, 0.30)
    disc(512, 452, 108, (255, 206, 120))
    disc(512, 452, 96, SUN_CORE)


def paint_birds():
    # Small distant birds: two short diagonal strokes each.
    birds = [(300, 300, 10), (348, 268, 8), (700, 260, 9), (748, 300, 7),
             (660, 330, 8)]
    for bx, by, s in birds:
        for i in range(s):
            span(by + i // 2, bx - s + i, bx - s + i, INK)
            span(by + i // 2, bx + i, bx + i, INK)


def paint_island(cx, top_y, half_w, depth, color=ROCK):
    """Floating rock: flat top, tapering to a soft point below."""
    for yy in range(top_y, top_y + depth):
        t = (yy - top_y) / depth
        # taper with a slight bulge near the top, point at the bottom
        w = half_w * (1.0 - t) ** 0.75 * (1.0 + 0.10 * math.sin(t * 3.0))
        span(yy, int(cx - w), int(cx + w), color)
    # warm rim light along the top edge
    span(top_y, int(cx - half_w), int(cx + half_w), ROCK_LIT)
    span(top_y + 1, int(cx - half_w) + 4, int(cx + half_w) - 4, ROCK_LIT)


def paint_tree(x, base_y, h, color=INK):
    # Simple pine: stacked triangles + trunk.
    w = h // 3
    for i in range(3):
        ty = base_y - h + i * (h // 4)
        th = h // 2
        for yy in range(ty, ty + th):
            t = (yy - ty) / th
            ww = int(w * (0.3 + 0.7 * t))
            span(yy, x - ww, x + ww, color)
    rect(x - 2, base_y - 6, 5, 7, color)


def paint_house(x, base_y, w, h, color=INK):
    rect(x, base_y - h, w, h, color)
    # pitched roof: narrow at the top, widening down to the eaves
    roof_h = h // 2 + 2
    for j in range(roof_h):
        span(base_y - h - roof_h + j, x - j, x + w + j - 1, color)
    # warm window
    rect(x + w // 2 - 3, base_y - h + 6, 6, 8, WINDOW)


def paint_lighthouse(cx, base_y):
    """The landmark: a tall lighthouse on the central isle."""
    tower_w = 26
    tower_h = 118
    top_y = base_y - tower_h
    # tower, slightly tapering, with a dark outline so it reads against the sun
    for yy in range(top_y, base_y):
        t = (yy - top_y) / tower_h
        w = int(tower_w / 2 * (1.0 - 0.18 * t))
        span(yy, cx - w - 2, cx + w + 2, INK)
        span(yy, cx - w, cx + w, CREAM_SOFT)
    # dark bands on the tower
    for by in (top_y + 26, top_y + 62):
        span(by, cx - 12, cx + 12, INK)
        span(by + 1, cx - 12, cx + 12, INK)
    # gallery + lamp room
    rect(cx - 20, top_y - 10, 40, 8, INK)
    rect(cx - 13, top_y - 34, 26, 24, INK)
    rect(cx - 9, top_y - 30, 18, 16, WINDOW)
    # dome + tip
    disc(cx, top_y - 36, 10, INK)
    rect(cx - 1, top_y - 48, 3, 12, INK)
    lamp_y = top_y - 22
    # Lamp glow: a soft halo around the lamp room so the light reads
    # even against the bright sun behind the tower.
    disc_blend(cx, lamp_y, 30, LIGHT_BEAM, 0.35)
    disc_blend(cx, lamp_y, 16, SUN_CORE, 0.55)
    # Light beams left and right: a bright narrow core wedge over a
    # longer, softer sweep, so the beam visibly reaches across the sky.
    for i, yy in enumerate(range(lamp_y - 10, lamp_y + 11)):
        spread = 46 + i * 14
        blend_span(yy, cx - 20 - spread, cx - 20, LIGHT_BEAM, 0.22)
        blend_span(yy, cx + 20, cx + 20 + spread, LIGHT_BEAM, 0.22)
    for i, yy in enumerate(range(lamp_y - 5, lamp_y + 6)):
        spread = 34 + i * 7
        blend_span(yy, cx - 20 - spread, cx - 20, LIGHT_BEAM, 0.38)
        blend_span(yy, cx + 20, cx + 20 + spread, LIGHT_BEAM, 0.38)


def paint_cloud_sea():
    # Base gradient: warm gold near horizon -> soft cream below.
    stops = [
        (0.00, (255, 190, 130)),
        (0.25, CLOUD2),
        (0.55, CLOUD4),
        (1.00, (250, 226, 196)),
    ]
    for y in range(641, 1010):
        t = (y - 641) / (1010 - 641)
        c = grad_color(stops, t)
        buf[y][14 * 3:1010 * 3] = bytes(c) * (1010 - 14)
    # Layered cloud puffs: far (lavender), mid (pink), near (cream).
    rng = random.Random(20261121)
    for (cy, rx, ry, col, n) in (
            (700, 150, 34, CLOUD3, 9),
            (790, 190, 44, CLOUD2, 8),
            (900, 220, 52, CLOUD1, 8)):
        for _ in range(n):
            ex = rng.randint(40, 984)
            ey = cy + rng.randint(-18, 18)
            erx = rx + rng.randint(-50, 60)
            ery = ry + rng.randint(-10, 12)
            ellipse(ex, ey, erx, ery, col)
    # Soft golden glow column under the sun, fading down the cloud sea.
    for yy in range(641, 960):
        t = (yy - 641) / (960 - 641)
        half = int(150 * (1.0 - 0.55 * t))
        blend_span(yy, 512 - half, 512 + half, (255, 196, 110),
                   0.16 * (1.0 - t))
    # Warm light pool where the lighthouse beam strikes the cloud sea,
    # directly below the central isle, with horizontal shimmer strokes.
    disc_blend(512, 762, 96, (255, 200, 120), 0.22)
    disc_blend(512, 786, 58, (255, 214, 140), 0.28)
    for yy, half, a in ((736, 120, 0.14), (752, 150, 0.18),
                        (772, 128, 0.16), (796, 96, 0.14),
                        (818, 70, 0.10)):
        blend_span(yy, 512 - half, 512 + half, (255, 205, 130), a)


def paint_sailboat(x, y):
    """A tiny sailboat drifting on the cloud sea: scale and life."""
    # Wake: a soft pale ellipse under the hull.
    ellipse(x, y + 14, 34, 5, CLOUD4)
    # Hull: dark, tapering toward the bow.
    for j in range(9):
        span(y + j, x - 22 + j * 2, x + 22 - j * 2, INK)
    # Mast + tiny pennant.
    rect(x - 1, y - 44, 3, 44, INK)
    span(y - 48, x + 2, x + 12, (240, 138, 60))
    span(y - 47, x + 2, x + 9, (240, 138, 60))
    # Main sail (sunlit cream) to the right of the mast, jib (pink
    # shadow side) to the left: two triangles, wide at the boom.
    for j in range(38):
        w = int(22 * (1.0 - j / 38.0))
        span(y - 42 + j, x + 3, x + 3 + w, CREAM_SOFT)
    for j in range(30):
        w = int(13 * (1.0 - j / 30.0))
        span(y - 36 + j, x - 3 - w, x - 3, CLOUD2)


def paint_frame():
    rect(0, 0, W, 14, CREAM)
    rect(0, H - 14, W, 14, CREAM)
    rect(0, 0, 14, H, CREAM)
    rect(W - 14, 0, 14, H, CREAM)
    # thin inner keyline
    for x in range(22, W - 22):
        span(22, x, x, INK)
        span(H - 23, x, x, INK)
    for y in range(22, H - 22):
        span(y, 22, 22, INK)
        span(y, W - 23, W - 23, INK)


def paint_type():
    # Title, big and centred, cream with a dark shadow for legibility.
    title = "AERIDOR"
    scale = 16
    tw = text_width(title, scale)
    tx = (W - tw) // 2
    draw_text(tx, 66, title, scale, CREAM, shadow=INK, shadow_dx=6)
    # Tagline under the title.
    tag = "THE ISLES ABOVE THE CLOUD SEA"
    sc = 4
    tw2 = text_width(tag, sc)
    # Thin ornament rules above and below the tagline, slightly wider
    # than the text, with a dark offset so they read on the bright sky.
    for ry in (189, 190):
        span(ry + 1, (W - tw2) // 2 - 96, (W + tw2) // 2 + 96, INK)
        span(ry, (W - tw2) // 2 - 96, (W + tw2) // 2 + 96, CREAM_SOFT)
    for ry in (234, 235):
        span(ry + 1, (W - tw2) // 2 - 96, (W + tw2) // 2 + 96, INK)
        span(ry, (W - tw2) // 2 - 96, (W + tw2) // 2 + 96, CREAM_SOFT)
    draw_text((W - tw2) // 2, 200, tag, sc, CREAM_SOFT, shadow=INK,
              shadow_dx=2)
    # Small diamond ornaments flanking the tagline.
    mid_y = 200 + 14
    for ox in ((W - tw2) // 2 - 34, (W + tw2) // 2 + 22):
        disc(ox, mid_y, 4, CREAM_SOFT)
    # Bottom promise line, dark on the bright cloud sea.
    bottom = "WHERE THE SUNSET NEVER ENDS"
    sc2 = 4
    tw3 = text_width(bottom, sc2)
    draw_text((W - tw3) // 2, 948, bottom, sc2, INK, shadow=CREAM_SOFT,
              shadow_dx=2)


# -------------------------------------------------------------------- png
def write_png(path):
    raw = bytearray()
    for row in buf:
        raw.append(0)  # filter: None
        raw.extend(row)
    compressed = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        c += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return c

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", compressed)
    png += chunk(b"IEND", b"")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    t0 = time.time()
    rng = random.Random(7)
    paint_sky()
    paint_stars(rng)
    paint_sun()
    paint_birds()
    # Distant tiny isles near the horizon, at the edges so they read apart.
    paint_island(88, 612, 44, 40)
    paint_island(938, 606, 48, 44)
    # Side isles with trees and a cottage.
    paint_island(232, 606, 96, 96)
    paint_tree(196, 606, 34)
    paint_tree(262, 606, 26)
    paint_house(228, 606, 34, 26)
    paint_island(806, 596, 104, 110)
    paint_tree(766, 596, 30)
    paint_tree(842, 596, 38)
    paint_house(800, 596, 36, 28)
    # Central isle + lighthouse landmark (in front of the sun's lower half).
    paint_island(512, 556, 150, 168)
    paint_tree(420, 556, 30)
    paint_tree(600, 556, 34)
    paint_house(452, 556, 34, 26)
    paint_house(556, 556, 30, 22)
    paint_lighthouse(512, 556)
    paint_cloud_sea()
    # Re-draw the isles' lower tips over the cloud sea so they float above it.
    paint_island(512, 556, 150, 168)
    paint_tree(420, 556, 30)
    paint_tree(600, 556, 34)
    paint_house(452, 556, 34, 26)
    paint_house(556, 556, 30, 22)
    paint_lighthouse(512, 556)
    paint_island(232, 606, 96, 96)
    paint_tree(196, 606, 34)
    paint_tree(262, 606, 26)
    paint_house(228, 606, 34, 26)
    paint_island(806, 596, 104, 110)
    paint_tree(766, 596, 30)
    paint_tree(842, 596, 38)
    paint_house(800, 596, 36, 28)
    paint_island(88, 612, 44, 40)
    paint_island(938, 606, 48, 44)
    # A tiny sailboat drifting on the cloud sea, right of centre.
    paint_sailboat(712, 872)
    paint_frame()
    paint_type()
    size = write_png(OUT)
    dt = time.time() - t0
    print(f"wrote {OUT}: {size} bytes, {W}x{H}, in {dt:.2f}s")


if __name__ == "__main__":
    main()

"""The World in One Day - 22 November 2026.

Draws a one-page visual summary of the world's news of Sunday
22 November 2026 and writes it to entry.png in the output directory
(MAKEFUN_OUTPUT_DIR, default /output). Pure Python standard library:
the PNG is encoded by hand and every pixel is plotted by the small
rasteriser below, so two runs always produce the same bytes.
"""

import binascii
import math
import os
import struct
import zlib

# ---------------------------------------------------------------- font
# A 5x7 bitmap font, one tuple of seven rows per glyph. Only the
# characters the headlines use are included; anything else is a space.

FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", ".#.#.", "..#..", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "..##.", ".#...", "#....", "#####"),
    "3": (".###.", "#...#", "....#", "..##.", "....#", "#...#", ".###."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".....", ".##..", ".#..."),
    "'": ("..#..", "..#..", ".....", ".....", ".....", ".....", "....."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".#...", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "..##.", "..#..", ".....", "..#.."),
    "(": ("..##.", ".#...", "#....", "#....", "#....", ".#...", "..##."),
    ")": (".##..", "...#.", "....#", "....#", "....#", "...#.", ".##.."),
}

# ---------------------------------------------------------------- canvas

W = 1024
H = 1024

BG = (10, 20, 38)
PANEL = (17, 34, 58)
CARD = (20, 40, 66)
CARD_EDGE = (38, 66, 102)
INK = (245, 241, 232)
GOLD = (242, 177, 52)
RED = (216, 72, 66)
MUTED = (158, 178, 201)
NAVY = (10, 20, 38)
SEA = (18, 66, 102)
SEA_LIGHT = (52, 128, 168)
HULL = (8, 13, 22)
DECK = (44, 62, 84)
FLAME_OUT = (255, 122, 26)
FLAME_IN = (255, 198, 64)
SMOKE = (96, 108, 124)
GREEN = (52, 168, 96)
TEAL = (0, 156, 166)
ORANGE = (214, 128, 44)
BLUE = (92, 134, 204)


class Canvas:
    def __init__(self, w, h, color):
        self.w = w
        self.h = h
        self.px = bytearray(bytes(color) * (w * h))

    def set_px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def fill_circle(self, cx, cy, r, color):
        r2 = r * r
        for yy in range(cy - r, cy + r + 1):
            dy = yy - cy
            span = int(math.sqrt(max(0, r2 - dy * dy)))
            self.fill_rect(cx - span, yy, 2 * span + 1, 1, color)

    def ring(self, cx, cy, r, color, thick=3):
        for step in range(720):
            a = step * math.pi / 360.0
            x = int(round(cx + r * math.cos(a)))
            y = int(round(cy + r * math.sin(a)))
            self.fill_rect(x - thick // 2, y - thick // 2, thick, thick, color)

    def fill_poly(self, pts, color):
        ys = [p[1] for p in pts]
        for yy in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % n]
                if y1 == y2:
                    continue
                if min(y1, y2) <= yy < max(y1, y2):
                    xs.append(x1 + (yy - y1) * (x2 - x1) // (y2 - y1))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.fill_rect(xs[i], yy, xs[i + 1] - xs[i] + 1, 1, color)

    def line(self, x1, y1, x2, y2, color, thick=3):
        steps = max(abs(x2 - x1), abs(y2 - y1), 1)
        for i in range(steps + 1):
            x = x1 + (x2 - x1) * i // steps
            y = y1 + (y2 - y1) * i // steps
            self.fill_rect(x - thick // 2, y - thick // 2, thick, thick, color)


# ---------------------------------------------------------------- text

def text_width(s, scale):
    if not s:
        return 0
    return len(s) * 6 * scale - scale


def draw_text(cv, x, y, s, scale, color):
    cx = x
    for ch in s.upper():
        glyph = FONT.get(ch, FONT[" "])
        for ry, row in enumerate(glyph):
            for rx, cell in enumerate(row):
                if cell == "#":
                    cv.fill_rect(cx + rx * scale, y + ry * scale, scale, scale, color)
        cx += 6 * scale
    return cx - scale


def draw_text_centered(cv, y, s, scale, color):
    x = (cv.w - text_width(s, scale)) // 2
    draw_text(cv, x, y, s, scale, color)


def wrap_text(s, scale, max_width):
    max_chars = max(1, (max_width + scale) // (6 * scale))
    lines = []
    cur = ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if len(trial) <= max_chars:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- icons

def draw_tanker(cv, x, y, w, with_flame):
    """A simple tanker silhouette; y is the waterline."""
    cv.fill_rect(x, y - 14, w, 14, HULL)
    cv.fill_poly([(x + w, y - 14), (x + w + 16, y - 14), (x + w, y)], HULL)
    cv.fill_rect(x, y - 4, w, 4, RED)
    cv.fill_rect(x + 12, y - 24, w // 3, 10, DECK)
    cv.fill_rect(x + w - 40, y - 30, 22, 16, DECK)
    cv.fill_rect(x + w - 32, y - 38, 6, 8, DECK)
    if with_flame:
        fx = x + w // 3
        cv.fill_circle(fx + 16, y - 62, 9, SMOKE)
        cv.fill_circle(fx + 26, y - 74, 12, SMOKE)
        cv.fill_circle(fx, y - 40, 15, FLAME_OUT)
        cv.fill_circle(fx, y - 34, 10, FLAME_IN)
        cv.fill_circle(fx, y - 30, 5, (255, 236, 170))


def draw_flag_pl(cv, x, y):
    cv.fill_rect(x, y, 34, 10, (240, 240, 240))
    cv.fill_rect(x, y + 10, 34, 10, RED)
    cv.line(x, y, x + 34, y, CARD_EDGE, 1)
    cv.line(x, y + 20, x + 34, y + 20, CARD_EDGE, 1)


def draw_globe(cv, cx, cy, r):
    cv.ring(cx, cy, r, TEAL, 3)
    cv.line(cx - r, cy, cx + r, cy, TEAL, 2)
    for step in range(360):
        a = step * math.pi / 180.0
        x = int(round(cx + (r // 2) * math.cos(a)))
        y = int(round(cy + r * math.sin(a)))
        cv.fill_rect(x - 1, y - 1, 2, 2, TEAL)


def draw_star(cv, cx, cy, r, color):
    pts = []
    for i in range(10):
        rad = r if i % 2 == 0 else r * 2 // 5
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((int(round(cx + rad * math.cos(a))),
                    int(round(cy + rad * math.sin(a)))))
    cv.fill_poly(pts, color)


def draw_boat(cv, x, y):
    """A small sailboat in a 60x41 box; (x, y) is the box's top-left.

    Sized and placed to sit in a card's top-right corner, clear of the
    headline block, like the flag, globe and star icons.
    """
    cv.fill_rect(x + 28, y, 3, 22, INK)
    cv.fill_poly([(x + 33, y), (x + 33, y + 20), (x + 49, y + 20)], INK)
    cv.fill_poly([(x, y + 24), (x + 60, y + 24), (x + 52, y + 34),
                  (x + 8, y + 34)], ORANGE)
    for i in range(3):
        cv.fill_rect(x + 4 + i * 19, y + 38, 12, 3, SEA_LIGHT)


def draw_bolt(cv, cx, cy):
    pts = [(cx + 6, cy - 22), (cx - 10, cy + 4), (cx - 1, cy + 4),
           (cx - 6, cy + 22), (cx + 10, cy - 4), (cx + 1, cy - 4)]
    cv.fill_poly(pts, GOLD)


# ---------------------------------------------------------------- layout

def story_card(cv, x, y, w, h, tag, tag_color, headline, summary, icon):
    cv.fill_rect(x, y, w, h, CARD)
    cv.fill_rect(x, y, w, 3, tag_color)
    cv.fill_rect(x, y + 10, 4, 18, tag_color)
    draw_text(cv, x + 14, y + 12, tag, 2, tag_color)
    if icon == "flag":
        draw_flag_pl(cv, x + w - 48, y + 8)
    elif icon == "globe":
        draw_globe(cv, x + w - 30, y + 18, 13)
    elif icon == "star":
        draw_star(cv, x + w - 30, y + 18, 13, GOLD)
    elif icon == "boat":
        draw_boat(cv, x + w - 74, y + 3)
    elif icon == "bolt":
        draw_bolt(cv, x + w - 30, y + 23)
    hy = y + 44
    for ln in wrap_text(headline, 3, w - 28):
        draw_text(cv, x + 14, hy, ln, 3, INK)
        hy += 27
    sy = y + h - 52
    for ln in wrap_text(summary, 2, w - 28):
        draw_text(cv, x + 14, sy, ln, 2, MUTED)
        sy += 19


def build():
    cv = Canvas(W, H, BG)

    # masthead
    draw_text_centered(cv, 40, "WORLD NEWS IN ONE IMAGE", 3, GOLD)
    draw_text_centered(cv, 82, "THE WORLD IN ONE DAY", 7, INK)
    cv.fill_rect(40, 148, W - 80, 3, GOLD)
    cv.fill_rect(40, 162, W - 80, 50, GOLD)
    draw_text_centered(cv, 173, "SUNDAY 22 NOVEMBER 2026", 4, NAVY)

    # hero panel: the Hormuz story
    hy0 = 232
    cv.fill_rect(40, hy0, W - 80, 324, PANEL)
    cv.fill_rect(40, hy0, W - 80, 6, RED)
    cv.fill_circle(884, 282, 20, GOLD)
    cv.fill_rect(64, 330, W - 128, 44, SEA)
    for i in range(12):
        cv.fill_rect(84 + i * 76, 342 + (i % 3) * 10, 34, 3, SEA_LIGHT)
    draw_tanker(cv, 130, 336, 300, True)
    draw_tanker(cv, 560, 340, 230, False)
    draw_text(cv, 64, 392, "TOP STORY - MIDDLE EAST", 2, GOLD)
    draw_text(cv, 64, 414, "TANKERS HIT NEAR HORMUZ", 6, INK)
    draw_text(cv, 64, 466, "AS GULF CRISIS WIDENS", 6, GOLD)
    draw_text(cv, 64, 524, "BAHRAIN SAYS IRAN SET FIRE TO A CIVILIAN PLANT. IRAN SAYS IT HIT US BASES.", 2, MUTED)
    draw_text(cv, 64, 545, "SAUDI-LED COALITION DOWNED THREE HOOTHI MISSILES AIMED AT RIYADH.", 2, MUTED)

    # story cards, row A
    ay = 576
    story_card(cv, 40, ay, 301, 178, "EUROPE - SECURITY", RED,
               "RUSSIAN MISSILES DOWN IN POLAND",
               "NATO CALLS IT A GRAVE VIOLATION. NO DEATHS.", "flag")
    story_card(cv, 361, ay, 301, 178, "CLIMATE - COP31", GREEN,
               "COP31 TALKS RUN INTO OVERTIME",
               "SPLIT ON FOSSIL FUELS AND CLIMATE FINANCE.", "globe")
    story_card(cv, 682, ay, 301, 178, "AMERICAS - CRIME", TEAL,
               "MOST WANTED CARTEL CHIEF HELD",
               "'CHAPO ISIDRO' SEIZED WITH US HELP.", "star")

    # story cards, row B
    by = 774
    story_card(cv, 40, by, 461, 178, "AFRICA - DISASTER", ORANGE,
               "FUNERAL BOAT CAPSIZE KILLS 24",
               "BOAT OVERTURNED ON A FUNERAL TRIP. RESCUERS SEARCH FOR SURVIVORS.", "boat")
    story_card(cv, 522, by, 461, 178, "MIDDLE EAST - IRAQ", BLUE,
               "POWER PLANT FIRE KILLS FOUR",
               "BLAZE AT HARTHA STATION NEAR BASRA INJURES 35 PEOPLE.", "bolt")

    # footer
    cv.fill_rect(40, 968, W - 80, 2, CARD_EDGE)
    draw_text_centered(cv, 982, "SIX STORIES - ONE DAY - DRAWN ENTIRELY BY CODE", 2, MUTED)
    return cv


# ---------------------------------------------------------------- png out

def save_png(cv, path):
    raw = bytearray()
    stride = cv.w * 3
    for yy in range(cv.h):
        raw.append(0)
        raw += cv.px[yy * stride:(yy + 1) * stride]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    save_png(build(), os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()

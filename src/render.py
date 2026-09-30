#!/usr/bin/env python3
"""Render the Swarm Pepe motion study from the collection's on-chain SVGs.

Requires the vendored Pillow package in tools/python and the vendored ffmpeg
binary in tools/ffmpeg_pkg/usr/bin. Run from the repository root.
"""

import math
import os
import random
import subprocess
import sys
import wave
import xml.etree.ElementTree as ET
from array import array
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, "tools/python")
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, DURATION = 1280, 720, 30, 15
FRAMES = FPS * DURATION
BPM = 128
BAR = 60 / BPM * 4
INK = "#0a1715"
BLACK = "#07110f"
LIME = "#caff43"
CREAM = "#f4f0dc"
ORANGE = "#ff6947"
VIOLET = "#aa91f1"
CYAN = "#53ddcc"
MID = "#688974"
FFMPEG = "tools/ffmpeg_pkg/usr/bin/ffmpeg"
FONT_DISPLAY = "assets/fonts/Anton-Regular.ttf"
FONT_MONO = "assets/fonts/SpaceMono-Regular.ttf"
FONT_MONO_BOLD = "assets/fonts/SpaceMono-Bold.ttf"
OUT = "artifacts/video.mp4"
WORK = Path("test/scratch")
WORK.mkdir(parents=True, exist_ok=True)


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def ease(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def spring(x):
    x = clamp(x)
    return 1 - math.exp(-7 * x) * math.cos(12 * x)


def smooth(a, b, t):
    return ease((t - a) / (b - a))


@lru_cache(maxsize=32)
def font(size, bold=False, display=False):
    path = FONT_DISPLAY if display else (FONT_MONO_BOLD if bold else FONT_MONO)
    return ImageFont.truetype(path, size)


@lru_cache(maxsize=64)
def original_art(number):
    root = ET.parse(f"assets/pepe_{number}.svg").getroot()
    im = Image.new("RGB", (24, 24), BLACK)
    dr = ImageDraw.Draw(im)
    for el in root:
        x = int(el.get("x", "0"))
        y = int(el.get("y", "0"))
        w = int(el.get("width", "0"))
        h = int(el.get("height", "0"))
        dr.rectangle((x, y, x + w - 1, y + h - 1), fill=el.get("fill"))
    return im


@lru_cache(maxsize=128)
def art(number, size):
    return original_art(number).resize((size, size), Image.Resampling.NEAREST)


def txt(d, xy, message, size, fill=CREAM, display=False, bold=False, anchor=None, stroke=0, stroke_fill=None):
    d.text(xy, message, font=font(size, bold, display), fill=fill, anchor=anchor,
           stroke_width=stroke, stroke_fill=stroke_fill)


def rules(d, color=CREAM, opacity=False):
    d.line((48, 47, W - 48, 47), fill=color, width=2)
    d.line((48, H - 51, W - 48, H - 51), fill=color, width=2)


def chrome(d, time, mode="dark"):
    fg = CREAM if mode == "dark" else INK
    rules(d, fg)
    txt(d, (49, 19), "SP / 001     SWARM PEPE", 16, fg, bold=True)
    txt(d, (W - 48, 19), f"MOTION STUDY  /  {time:05.2f}", 16, fg, anchor="ra")
    txt(d, (49, H - 39), "ETHEREUM  •  ON-CHAIN PIXELS", 14, fg)
    txt(d, (W - 48, H - 39), "15 SEC / 128 BPM", 14, fg, anchor="ra")
    d.rectangle((48, H - 54, 48 + int((W - 96) * time / DURATION), H - 49), fill=ORANGE if mode == "dark" else INK)


def rect(d, box, fill, outline=None, width=1):
    d.rectangle(tuple(map(int, box)), fill=fill, outline=outline, width=width)


def ring(d, cx, cy, radius, color, width=2):
    d.ellipse((int(cx-radius), int(cy-radius), int(cx+radius), int(cy+radius)), outline=color, width=width)


def image_card(number, width=300, accent=LIME):
    height = int(width * 1.27)
    im = Image.new("RGBA", (width + 18, height + 18), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    rect(dr, (9, 9, width + 8, height + 8), INK)
    rect(dr, (9, 9, width + 8, height + 8), None, accent, 4)
    pad = 17
    sq = width - 2 * pad
    im.paste(art(number, sq), (9 + pad, 9 + pad))
    dr.line((9+pad, 9+pad+sq+12, 9+width-pad, 9+pad+sq+12), fill=accent, width=2)
    txt(dr, (9+pad, 9+pad+sq+21), f"SWARM PEPE  #{number:03d}", max(12, int(width * .043)), CREAM, bold=True)
    txt(dr, (9+pad, 9+height-25), "ON CHAIN  /  24×24", max(10, int(width * .035)), accent)
    return im


@lru_cache(maxsize=64)
def card_cached(number, width, accent):
    return image_card(number, width, accent)


def paste_card(im, number, cx, cy, width, angle=0, accent=LIME):
    card = card_cached(number, width, accent)
    if abs(angle) > .1:
        card = card.rotate(angle, Image.Resampling.BICUBIC, expand=True)
    im.alpha_composite(card, (int(cx - card.width / 2), int(cy - card.height / 2)))


def scanlines(im, alpha=20):
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for y in range(0, H, 5):
        d.line((0, y, W, y), fill=(0, 0, 0, alpha), width=1)
    im.alpha_composite(overlay)


def shot0(im, d, u, t):
    # Signal acquisition: concentric rings, then hard typographic reveal.
    for j in range(8):
        r = 70 + j * 85 + (u * 340) % 85
        ring(d, W/2, H/2, r, "#314a39", 2)
    for j in range(36):
        x = (j * 83 + int(u*150)) % W
        y = (j * 137) % H
        rect(d, (x, y, x+6, y+6), LIME if j%3 else ORANGE)
    p = spring(u / .28)
    block = int(980 * clamp(p))
    rect(d, (0, 278, block, 488), LIME)
    # Oversized split wordmark makes the first frame feel like a takeover.
    txt(d, (75 - 120*(1-ease(u/.3)), 245), "SWARM", 202, INK if u > .12 else LIME, display=True)
    txt(d, (902 + 210*(1-ease((u-.18)/.3)), 465), "PEPE", 104, CREAM, display=True, anchor="ra")
    txt(d, (75, 204), "A NEW SIGNAL FROM THE CHAIN", 18, CREAM, bold=True)
    if u > .62:
        txt(d, (76, 533), "001  /  THE SWARM IS LIVE", 18, LIME)
    # Persistent animated tally.
    for j in range(16):
        h = 18 + int(38 * abs(math.sin(t*8+j*.8)))
        rect(d, (1040+j*10, 192-h, 1045+j*10, 192), LIME)


def shot1(im, d, u, t):
    # Graphic portrait with orbital UI motifs and extremely large type.
    rect(d, (0, 0, W, H), LIME)
    for j in range(12):
        x = (j*108 + int(u*38)) % 1320
        d.line((x, 0, x-260, H), fill="#afd928", width=2)
    cx = 790 + 400*(1-spring(u/.30))
    cy = 355 + 10*math.sin(t*3)
    for r in (268, 319, 372):
        ring(d, cx, cy, r, INK, 2)
    paste_card(im, 757, cx, cy, 388, angle=-4+3*math.sin(u*3), accent=INK)
    rect(d, (56, 105, 501, 632), INK)
    txt(d, (75, 91), "01 / THE SIGNAL", 18, LIME, bold=True)
    txt(d, (76, 147), "SWARM", 101, CREAM, display=True)
    txt(d, (76, 245), "PEPE", 101, LIME, display=True)
    d.line((79, 365, 465, 365), fill=LIME, width=3)
    txt(d, (80, 391), "DRAWN ON CHAIN.", 23, CREAM, bold=True)
    txt(d, (80, 435), "PIXEL BY PIXEL.", 23, CREAM, bold=True)
    txt(d, (80, 550), "#757  /  24×24", 17, LIME)
    chrome(d, t, "light")


def shot2(im, d, u, t):
    # Macro pixel expansion: the artwork becomes the layout system.
    rect(d, (0, 0, W, H), INK)
    sz = int(760 + 360*ease(u/.9))
    crop = art(970, sz)
    x = int(550 - (sz-760)*.24)
    y = int(-120 - (sz-760)*.16)
    im.paste(crop, (x, y))
    rect(d, (0, 0, 570, H), INK)
    for i in range(19):
        px = 26 + i*32
        py = 120 + (i%4)*34 + int(16*math.sin(t*6+i))
        rect(d, (px, py, px+9, py+9), LIME if i%3 else ORANGE)
    txt(d, (58, 138), "24", 180, LIME, display=True)
    txt(d, (319, 208), "×", 72, ORANGE, display=True)
    txt(d, (55, 302), "24", 180, CREAM, display=True)
    txt(d, (57, 520), "DRAWN ON CHAIN", 26, CREAM, bold=True)
    txt(d, (57, 564), "PIXEL BY PIXEL", 19, LIME)
    d.line((570, 0, 570, H), fill=LIME, width=7)
    txt(d, (622, 83), "002  /  SOURCE CODE IS THE CANVAS", 18, CREAM, bold=True)
    chrome(d, t)


def shot3(im, d, u, t):
    rect(d, (0, 0, W, H), ORANGE)
    for i in range(13):
        d.line((i*117-170, 0, i*117+220, H), fill="#cf533a", width=3)
    txt(d, (W/2, 84), "MANY FACES. ONE SWARM.", 50, INK, display=True, anchor="ma")
    ids = (960, 475, 590)
    xs = (264, 642, 1020)
    colors = (LIME, CYAN, VIOLET)
    for i, (n, x, c) in enumerate(zip(ids, xs, colors)):
        delay = i*.12
        p = spring((u-delay)/.30)
        yy = 355 + (1-p)*660 + 8*math.sin(t*4+i)
        paste_card(im, n, x, yy, 326, angle=(-6, 0, 6)[i]+2*math.sin(t*2+i), accent=c)
    txt(d, (W/2, 610), "003 / INDIVIDUALS IN MOTION", 17, INK, bold=True, anchor="ma")
    chrome(d, t, "light")


GRID_IDS = [757, 960, 475, 590, 970, 589, 578, 310, 807, 495, 698, 287,
            517, 622, 507, 69, 366, 389, 808, 564, 448, 577, 424, 972]


def shot4(im, d, u, t):
    rect(d, (0, 0, W, H), CREAM)
    cell = 152
    for row in range(4):
        for col in range(8):
            j = (row*8+col) % len(GRID_IDS)
            x = col*cell + 28 - int((u*82)%cell)
            y = row*cell + 89
            appear = smooth(.02 + (row+col)*.025, .20 + (row+col)*.025, u)
            if appear:
                s = int(cell*appear)
                if s > 2:
                    tile = art(GRID_IDS[j], s)
                    im.paste(tile, (x+(cell-s)//2, y+(cell-s)//2))
    rect(d, (0, 260, W, 469), INK)
    txt(d, (W/2, 265), "ONE SWARM", 159, LIME, display=True, anchor="ma")
    txt(d, (W/2, 486), "UNIQUE SIGNALS / SHARED ENERGY", 20, INK, bold=True, anchor="ma")
    chrome(d, t, "light")


def shot5(im, d, u, t):
    rect(d, (0, 0, W, H), VIOLET)
    # Two enormous closeups crop through hard-edged viewports.
    left = art(578, 690)
    right = art(807, 690)
    lx = -200 + int(110*ease(u/.5))
    rx = 760 - int(130*ease(u/.5))
    im.paste(left, (lx, 36))
    im.paste(right, (rx, 36))
    rect(d, (0, 0, W, H), None, INK, 18)
    rect(d, (360, 89, 924, 623), INK)
    txt(d, (W/2, 99), "EVERY", 61, CREAM, display=True, anchor="ma")
    txt(d, (W/2, 171), "PIXEL", 123, LIME, display=True, anchor="ma")
    txt(d, (W/2, 308), "HAS A", 60, CREAM, display=True, anchor="ma")
    txt(d, (W/2, 375), "PULSE.", 101, ORANGE, display=True, anchor="ma")
    for i in range(12):
        r = 2+i*2
        xx = 396 + i*43
        yy = 559 + int(18*math.sin(t*8+i*.5))
        rect(d, (xx, yy, xx+r, yy+r), LIME)
    chrome(d, t)


def shot6(im, d, u, t):
    rect(d, (0, 0, W, H), BLACK)
    cx,cy = 640,365
    for i in range(12):
        r = 90 + i*56 + int((u*90)%56)
        ring(d, cx, cy, r, LIME if i%3 == 0 else "#26483a", 3 if i%3 == 0 else 1)
    for i in range(48):
        a = (i/48)*math.tau + t*.2
        r1, r2 = 258, 322 + 16*math.sin(t*4+i)
        d.line((cx+math.cos(a)*r1,cy+math.sin(a)*r1,cx+math.cos(a)*r2,cy+math.sin(a)*r2),fill=ORANGE if i%6==0 else LIME,width=3)
    sz = int(280 * min(1.0, spring(u/.3)))
    if sz > 2:
        im.paste(art(589, sz), (cx-sz//2, cy-sz//2))
    txt(d, (65, 133), "THE SWARM", 70, CREAM, display=True)
    txt(d, (65, 214), "IS CHOOSING", 70, LIME, display=True)
    txt(d, (65, 335), "MOST OF THESE PEPES", 17, CREAM, bold=True)
    txt(d, (65, 363), "DON'T HAVE OWNERS YET.", 17, CREAM, bold=True)
    txt(d, (937, 533), "THE NEXT SIGNAL", 18, CREAM, bold=True)
    txt(d, (937, 566), "COULD BE YOURS /", 17, LIME)
    chrome(d, t)


def shot7(im, d, u, t):
    rect(d, (0, 0, W, H), LIME)
    # Tight, confident end card with a recurring portrait constellation.
    for i, (n, x, y, s) in enumerate(((960, 72, 75, 140), (475, 1060, 104, 142),
                                      (757, 73, 475, 144), (590, 1066, 455, 145))):
        dy = int(7*math.sin(t*3+i))
        im.paste(art(n, s), (x, y+dy))
        rect(d, (x-5,y+dy-5,x+s+4,y+dy+s+4), None, INK, 4)
    q = ease(u/.35)
    rect(d, (258, 80, 1026, 640), INK)
    txt(d, (W/2, 112), "THE COLLECTION", 20, LIME, bold=True, anchor="ma")
    txt(d, (W/2, 189 + 46*(1-q)), "SWARM", 160, CREAM, display=True, anchor="ma")
    txt(d, (W/2, 352 + 46*(1-q)), "PEPE", 160, LIME, display=True, anchor="ma")
    d.line((332, 548, 954, 548), fill=ORANGE, width=5)
    txt(d, (W/2, 568), "DRAWN ON CHAIN  /  PIXEL BY PIXEL", 20, CREAM, bold=True, anchor="ma")
    txt(d, (W/2, 612), "OPENSEA.IO/COLLECTION/SWARM-PEPE", 17, LIME, anchor="ma")
    chrome(d, t, "light")


SHOTS = (shot0, shot1, shot2, shot3, shot4, shot5, shot6, shot7)
COLORS = (BLACK, LIME, INK, ORANGE, CREAM, VIOLET, BLACK, LIME)


def frame_at(k):
    t = k / FPS
    shot = min(7, int(t / BAR))
    u = t - shot*BAR
    im = Image.new("RGBA", (W, H), COLORS[shot])
    d = ImageDraw.Draw(im)
    SHOTS[shot](im, d, u, t)
    # Broadcast grit and tightly timed wipe flashes on every downbeat.
    if shot and u < .10:
        w = int(W * (1-u/.10))
        rect(d, (0, 0, w, H), CREAM if shot%2 else LIME)
    beat = (t * BPM / 60) % 1
    if beat < .055 and shot in (0, 2, 4, 6):
        flash = Image.new("RGBA", (W, H), (255,255,255, int(30*(1-beat/.055))))
        im.alpha_composite(flash)
    # Fine scan structure intentionally remains visible on modern screens.
    if k % 2 == 0:
        scanlines(im, 12)
    return im.convert("RGB")


def synth_audio(path):
    sr = 44100
    n = int(DURATION * sr)
    audio = array("f", [0.0]) * n
    rng = random.Random(70)

    def add(start, duration, fn):
        first = int(start*sr)
        count = min(int(duration*sr), n-first)
        if first < 0 or count <= 0: return
        for i in range(count):
            x=i/sr
            audio[first+i] += fn(x, i)

    # 128 BPM electro rhythm, composed for the eight visual phrases.
    for beat in range(32):
        start = beat * 60/BPM
        add(start, .34, lambda x,i: .70*math.sin(2*math.pi*(53*x + 65*(1-math.exp(-x*26))/26))*math.exp(-x*17))
        if beat % 2:
            add(start, .21, lambda x,i: .20*(rng.random()*2-1)*math.exp(-x*24) + .12*math.sin(2*math.pi*180*x)*math.exp(-x*22))
        if beat%4 == 0:
            add(start, .18, lambda x,i: .16*math.sin(2*math.pi*75*x)*math.exp(-x*16))
        for half in (0, .5):
            add(start+half*60/BPM, .085,
                lambda x,i: .08*(rng.random()*2-1)*math.exp(-x*65))
    # Syncopated analogue bass, with a small melodic turn each bar.
    notes = [55, 55, 65.41, 55, 73.42, 65.41, 55, 82.41]
    for bar in range(8):
        for sub in range(8):
            st = bar*BAR + sub*BAR/8
            note = notes[(bar+sub//2)%len(notes)]
            if sub in (0, 3, 4, 7):
                add(st, .20, lambda x,i,f=note: .15*(math.sin(2*math.pi*f*x)+.23*math.sin(2*math.pi*2*f*x))*math.exp(-x*10))
        # Short bright stab on the second half of each visual phrase.
        st = bar*BAR + BAR*.5
        for hz in (220, 261.63, 329.63):
            add(st, .22, lambda x,i,f=hz: .055*math.sin(2*math.pi*f*x)*math.exp(-x*10))
    # Entry sweep and the larger handoffs in the edit.
    for bar in (0, 2, 4, 6):
        st = bar*BAR
        add(st, .40, lambda x,i: .16*(rng.random()*2-1)*(x/.4)*math.exp(-x*3))
    for st in (0, BAR*2, BAR*4, BAR*6, BAR*7):
        add(st, .42, lambda x,i: .24*math.sin(2*math.pi*(125*x+180*x*x))*math.exp(-x*9))
    # Final tail resolves exactly at 15 seconds.
    peak=max(abs(v) for v in audio)
    gain=.91/max(peak, .91)
    with wave.open(str(path), "wb") as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(sr)
        samples=array("h")
        for i,v in enumerate(audio):
            env = min(1.0, (DURATION-i/sr)/.22)
            left=max(-1,min(1,v*gain*env))
            right=max(-1,min(1,v*gain*env*(.98+.02*math.sin(i/sr*6))))
            samples.extend((int(left*32767),int(right*32767)))
        f.writeframes(samples.tobytes())


def render():
    audio_path = WORK / "score.wav"
    video_path = WORK / "picture.mp4"
    synth_audio(audio_path)
    cmd=[FFMPEG,"-hide_banner","-loglevel","error","-y","-f","rawvideo","-pix_fmt","rgb24",
         "-s",f"{W}x{H}","-r",str(FPS),"-i","-","-c:v","libx264","-preset","veryfast",
         "-crf","18","-pix_fmt","yuv420p","-movflags","+faststart",str(video_path)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for k in range(FRAMES):
            proc.stdin.write(frame_at(k).tobytes())
            if k%30==0:
                print(f"render {k//30:02d}/{DURATION:02d}s", flush=True)
    finally:
        proc.stdin.close()
    if proc.wait(): raise RuntimeError("ffmpeg video encoding failed")
    os.makedirs("artifacts",exist_ok=True)
    subprocess.run([FFMPEG,"-hide_banner","-loglevel","error","-y","-i",str(video_path),
                    "-i",str(audio_path),"-c:v","copy","-c:a","aac","-b:a","192k",
                    "-ar","44100","-shortest","-movflags","+faststart",OUT],check=True)
    print(OUT)


if __name__ == "__main__":
    render()

#!/usr/bin/env python3
"""
Instagram carousel generator — husrav.ai style.
Format: 4:5 (1080×1350 px)
Usage: python3 generator.py content.json [output_dir] [--photo /path/to/photo.jpg]
"""

import json
import sys
import os
import base64
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

CHROMIUM_PATH = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
FONTS_DIR     = Path(__file__).parent / "fonts"
SLIDE_W       = 1080
SLIDE_H       = 1350   # 4:5

# ── embed fonts as base64 so rendering works offline ──────────────────────────
def _b64font(filename: str) -> str:
    path = FONTS_DIR / filename
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode()

def _font_face(family: str, weight: int, filename: str) -> str:
    b64 = _b64font(filename)
    if not b64:
        return ""
    return f"""@font-face {{
  font-family: '{family}';
  font-weight: {weight};
  font-style: normal;
  src: url('data:font/truetype;base64,{b64}') format('truetype');
}}"""

def build_font_css() -> str:
    return "\n".join([
        _font_face("BebasNeue",  400, "BebasNeue.ttf"),
        _font_face("Montserrat", 400, "Montserrat-Regular.ttf"),
        _font_face("Montserrat", 700, "Montserrat-Bold.ttf"),
        _font_face("Montserrat", 800, "Montserrat-ExtraBold.ttf"),
        _font_face("Montserrat", 900, "Montserrat-Black.ttf"),
    ])

# ── encode photo for inline embedding ─────────────────────────────────────────
def encode_photo(photo_path: str) -> str:
    if not photo_path or not Path(photo_path).exists():
        return ""
    data = Path(photo_path).read_bytes()
    b64  = base64.b64encode(data).decode()
    ext  = Path(photo_path).suffix.lower().lstrip(".")
    mime = "jpeg" if ext in ("jpg","jpeg") else ext
    return f"data:image/{mime};base64,{b64}"

# ── shared CSS ─────────────────────────────────────────────────────────────────
BASE_CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  background: #0C0E0A;
  color: #fff;
}

.slide {
  width: 1080px;
  height: 1350px;
  background: #0C0E0A;
  position: relative;
  overflow: hidden;
}

/* typography helpers */
.fn-bebas    { font-family: 'BebasNeue', 'Arial Black', Arial, sans-serif; }
.fn-mont     { font-family: 'Montserrat', 'Arial', sans-serif; }

.h-white { color: #ffffff; }
.h-green { color: #C5FF00; }

/* ── SHARED ELEMENTS ── */

.tag {
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: #888;
  display: flex;
  align-items: center;
  gap: 9px;
}
.tag::before {
  content: '+';
  color: #C5FF00;
  font-size: 17px;
  font-weight: 900;
  line-height: 1;
}

.brand {
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 17px;
  font-weight: 700;
  color: #444;
  letter-spacing: 0.05em;
}

.counter {
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 17px;
  font-weight: 700;
  color: #444;
  letter-spacing: 0.04em;
}

.bottom-bar {
  position: absolute;
  bottom: 50px;
  left: 60px;
  right: 60px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* large background deco number */
.deco-num {
  font-family: 'BebasNeue', 'Arial Black', Arial, sans-serif;
  font-size: 460px;
  line-height: 0.85;
  color: #141810;
  position: absolute;
  right: -10px;
  top: 30px;
  user-select: none;
  letter-spacing: -0.02em;
  z-index: 0;
}

/* pill badges */
.pills { display: flex; gap: 12px; flex-wrap: wrap; }
.pill {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #161a10;
  border: 1px solid #272e1c;
  border-radius: 40px;
  padding: 11px 22px;
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 14px;
  font-weight: 600;
  color: #ccc;
  letter-spacing: 0.03em;
}
.pill-dot { width: 7px; height: 7px; border-radius: 50%; background: #C5FF00; }

/* ── SLIDE 1 — COVER ── */

.cover .photo-wrap {
  position: absolute;
  inset: 0;
  z-index: 0;
}
.cover .photo-wrap img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: top center;
}
/* dark gradient overlay: bottom-heavy + left fade */
.cover .photo-wrap::after {
  content: '';
  position: absolute;
  inset: 0;
  background:
    linear-gradient(to right,  #0C0E0A 0%, #0C0E0Acc 35%, transparent 65%),
    linear-gradient(to top,    #0C0E0A 0%, #0C0E0Aaa 30%, transparent 60%);
  z-index: 1;
}
/* no-photo fallback */
.cover .photo-placeholder {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #1a1f14 0%, #0c0e0a 60%);
  z-index: 0;
}

.cover .content {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 0 60px 140px;
  z-index: 2;
}

.cover .cover-eyebrow {
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: #888;
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 24px;
}
.cover .cover-eyebrow .dot { width: 6px; height: 6px; border-radius: 50%; background: #C5FF00; }

.cover .headline {
  font-family: 'BebasNeue', 'Arial Black', Arial, sans-serif;
  font-size: 112px;
  line-height: 0.95;
  text-transform: uppercase;
  letter-spacing: 0.01em;
  margin-bottom: 26px;
}

.cover .subtext {
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 18px;
  font-weight: 400;
  color: #aaa;
  line-height: 1.55;
  max-width: 480px;
  margin-bottom: 48px;
}

.cover .cta-btn {
  display: inline-flex;
  align-items: center;
  gap: 14px;
  background: #C5FF00;
  color: #000;
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 17px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  padding: 17px 34px;
  border-radius: 7px;
}

/* ── SLIDE 2 — BRIEF (00) ── */

.brief .inner {
  padding: 72px 60px 0;
  height: 100%;
  position: relative;
}
.brief .headline {
  font-family: 'BebasNeue', 'Arial Black', Arial, sans-serif;
  font-size: 96px;
  line-height: 0.95;
  text-transform: uppercase;
  margin-top: 140px;
  margin-bottom: 36px;
  max-width: 780px;
  position: relative; z-index: 2;
  letter-spacing: 0.01em;
}
.brief .body-text {
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 21px;
  font-weight: 400;
  color: #aaa;
  line-height: 1.65;
  max-width: 680px;
  margin-bottom: 52px;
  position: relative; z-index: 2;
}

/* ── SLIDE 3 — FEATURE ── */

.feature .inner {
  padding: 72px 60px 0;
  height: 100%;
  position: relative;
}
.feature .headline {
  font-family: 'BebasNeue', 'Arial Black', Arial, sans-serif;
  font-size: 96px;
  line-height: 0.95;
  text-transform: uppercase;
  letter-spacing: 0.01em;
  margin-top: 140px;
  margin-bottom: 30px;
  max-width: 780px;
  position: relative; z-index: 2;
}
.feature .body-text {
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 21px;
  font-weight: 400;
  color: #aaa;
  line-height: 1.65;
  max-width: 680px;
  position: relative; z-index: 2;
  margin-bottom: 52px;
}
.feature .img-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  position: relative; z-index: 2;
}
.feature .img-placeholder {
  height: 220px;
  background: #161a10;
  border-radius: 10px;
  border: 1px solid #222;
}

/* ── SLIDE 4 — NUMBERED LIST ── */

.numlist .inner {
  padding: 72px 60px 0;
  height: 100%;
  position: relative;
}
.numlist .headline {
  font-family: 'BebasNeue', 'Arial Black', Arial, sans-serif;
  font-size: 88px;
  line-height: 0.95;
  text-transform: uppercase;
  letter-spacing: 0.01em;
  margin-bottom: 52px;
  max-width: 780px;
  position: relative; z-index: 2;
}
.numlist .items { display: flex; flex-direction: column; gap: 30px; position: relative; z-index: 2; }
.numlist .item  { display: flex; align-items: flex-start; gap: 22px; }
.numlist .item-num {
  min-width: 48px; width: 48px; height: 48px;
  background: #C5FF00;
  color: #000;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 20px; font-weight: 900;
  margin-top: 4px;
}
.numlist .item-title {
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 25px; font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  line-height: 1.1;
  margin-bottom: 7px;
}
.numlist .item-sub {
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 16px; font-weight: 400;
  color: #777;
}
.numlist .footer {
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 17px; color: #555;
  margin-top: 40px;
  position: relative; z-index: 2;
}

/* ── SLIDE 5 — STATS ── */

.stats .inner {
  padding: 72px 60px 0;
  height: 100%;
  position: relative;
}
.stats .headline {
  font-family: 'BebasNeue', 'Arial Black', Arial, sans-serif;
  font-size: 96px;
  line-height: 0.95;
  text-transform: uppercase;
  letter-spacing: 0.01em;
  margin-top: 140px;
  margin-bottom: 30px;
  max-width: 780px;
  position: relative; z-index: 2;
}
.stats .body-text {
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 20px; font-weight: 400;
  color: #aaa; line-height: 1.65;
  max-width: 680px;
  margin-bottom: 60px;
  position: relative; z-index: 2;
}
.stats .numbers-row {
  display: flex; gap: 70px;
  position: relative; z-index: 2;
}
.stats .stat-val {
  font-family: 'BebasNeue', 'Arial Black', Arial, sans-serif;
  font-size: 110px;
  line-height: 0.9;
  color: #C5FF00;
  letter-spacing: -0.01em;
}
.stats .stat-label {
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 13px; font-weight: 700;
  color: #555;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  margin-top: 8px;
}

/* ── SLIDE 6 — CTA ── */

.cta-slide .inner {
  padding: 72px 60px;
  height: 100%;
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding-bottom: 140px;
}
.cta-slide .headline {
  font-family: 'BebasNeue', 'Arial Black', Arial, sans-serif;
  font-size: 100px;
  line-height: 0.95;
  text-transform: uppercase;
  letter-spacing: 0.01em;
  margin-bottom: 36px;
  max-width: 780px;
  position: relative; z-index: 2;
}
.cta-slide .body-text {
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 20px; font-weight: 400;
  color: #aaa; line-height: 1.65;
  max-width: 620px;
  margin-bottom: 48px;
  position: relative; z-index: 2;
}
.cta-slide .cta-btn {
  display: inline-flex;
  align-items: center;
  gap: 16px;
  background: #C5FF00;
  color: #000;
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 19px; font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding: 20px 38px;
  border-radius: 7px;
  position: relative; z-index: 2;
  width: fit-content;
}
"""

# ── slide builders ─────────────────────────────────────────────────────────────

def _headline_html(lines: list) -> str:
    out = ""
    for line in lines:
        cls = "h-green" if line.get("green") else "h-white"
        out += f'<span class="{cls}">{line["text"]}</span><br>'
    return out

def slide_cover(data: dict, total: int, photo_src: str = "") -> str:
    tag      = data.get("tag", "")
    headline = _headline_html(data.get("headline", []))
    subtext  = data.get("subtext", "")
    cta      = data.get("cta", "ЛИСТАЙ")
    brand    = data.get("brand", "husrav.ai")

    photo_src = photo_src or data.get("photo", "")

    if photo_src:
        photo_html = f'<div class="photo-wrap"><img src="{photo_src}" /></div>'
    else:
        photo_html = '<div class="photo-placeholder"></div>'

    eyebrow_html = ""
    if tag:
        eyebrow_html = f'<div class="cover-eyebrow"><span class="dot"></span>{tag}</div>'

    return f"""
<div class="slide cover">
  {photo_html}
  <div class="content">
    {eyebrow_html}
    <div class="headline">{headline}</div>
    <div class="subtext">{subtext}</div>
    <div class="cta-btn"><span>{cta}</span><span>→</span></div>
  </div>
  <div class="bottom-bar" style="z-index:3">
    <div class="brand">{brand}</div>
  </div>
</div>"""


def slide_brief(data: dict, idx: int, total: int) -> str:
    tag     = data.get("tag", "КРАТКО")
    hl      = _headline_html(data.get("headline", []))
    body    = data.get("body", "")
    pills   = data.get("pills", [])
    brand   = data.get("brand", "husrav.ai")
    deco    = str(idx - 1).zfill(2)
    pills_h = "".join(f'<div class="pill"><span class="pill-dot"></span>{p}</div>' for p in pills)

    return f"""
<div class="slide brief">
  <div class="inner">
    <div class="tag">{tag}</div>
    <div class="deco-num">{deco}</div>
    <div class="headline">{hl}</div>
    <div class="body-text">{body}</div>
    <div class="pills" style="position:relative;z-index:2">{pills_h}</div>
    <div class="bottom-bar">
      <div class="brand">{brand}</div>
      <div class="counter">{str(idx).zfill(2)} / {str(total).zfill(2)}</div>
    </div>
  </div>
</div>"""


def slide_feature(data: dict, idx: int, total: int) -> str:
    tag   = data.get("tag", "КАК ЭТО РАБОТАЕТ")
    hl    = _headline_html(data.get("headline", []))
    body  = data.get("body", "")
    brand = data.get("brand", "husrav.ai")
    deco  = str(idx - 1).zfill(2)

    return f"""
<div class="slide feature">
  <div class="inner">
    <div class="tag">{tag}</div>
    <div class="deco-num">{deco}</div>
    <div class="headline">{hl}</div>
    <div class="body-text">{body}</div>
    <div class="bottom-bar">
      <div class="brand">{brand}</div>
      <div class="counter">{str(idx).zfill(2)} / {str(total).zfill(2)}</div>
    </div>
  </div>
</div>"""


def slide_numlist(data: dict, idx: int, total: int) -> str:
    tag   = data.get("tag", "ВОЗМОЖНОСТИ")
    hl    = _headline_html(data.get("headline", []))
    items = data.get("items", [])
    footer= data.get("footer", "")
    brand = data.get("brand", "husrav.ai")

    items_h = ""
    for i, item in enumerate(items, 1):
        items_h += f"""<div class="item">
          <div class="item-num">{i}</div>
          <div>
            <div class="item-title">{item.get('title','')}</div>
            <div class="item-sub">{item.get('sub','')}</div>
          </div>
        </div>"""

    footer_h = f'<div class="footer">{footer}</div>' if footer else ""

    return f"""
<div class="slide numlist">
  <div class="inner">
    <div class="tag">{tag}</div>
    <div class="headline">{hl}</div>
    <div class="items">{items_h}</div>
    {footer_h}
    <div class="bottom-bar">
      <div class="brand">{brand}</div>
      <div class="counter">{str(idx).zfill(2)} / {str(total).zfill(2)}</div>
    </div>
  </div>
</div>"""


def slide_stats(data: dict, idx: int, total: int) -> str:
    tag   = data.get("tag", "ЦИФРЫ")
    hl    = _headline_html(data.get("headline", []))
    body  = data.get("body", "")
    stats = data.get("stats", [])
    brand = data.get("brand", "husrav.ai")
    deco  = str(idx - 1).zfill(2)

    stats_h = "".join(f"""<div class="stat-item">
      <div class="stat-val">{s.get('value','')}</div>
      <div class="stat-label">{s.get('label','')}</div>
    </div>""" for s in stats)

    return f"""
<div class="slide stats">
  <div class="inner">
    <div class="tag">{tag}</div>
    <div class="deco-num">{deco}</div>
    <div class="headline">{hl}</div>
    <div class="body-text">{body}</div>
    <div class="numbers-row">{stats_h}</div>
    <div class="bottom-bar">
      <div class="brand">{brand}</div>
      <div class="counter">{str(idx).zfill(2)} / {str(total).zfill(2)}</div>
    </div>
  </div>
</div>"""


def slide_cta(data: dict, idx: int, total: int) -> str:
    tag   = data.get("tag", "ЗАБИРАЙ")
    hl    = _headline_html(data.get("headline", []))
    body  = data.get("body", "")
    cta   = data.get("cta", "НАПИСАТЬ В КОММЕНТАРИИ")
    brand = data.get("brand", "husrav.ai")
    deco  = str(idx - 1).zfill(2)

    return f"""
<div class="slide cta-slide">
  <div class="inner">
    <div class="tag">{tag}</div>
    <div class="deco-num">{deco}</div>
    <div class="headline">{hl}</div>
    <div class="body-text">{body}</div>
    <div class="cta-btn"><span>{cta}</span><span>→</span></div>
    <div class="bottom-bar">
      <div class="brand">{brand}</div>
      <div class="counter">{str(idx).zfill(2)} / {str(total).zfill(2)}</div>
    </div>
  </div>
</div>"""


BUILDERS = {
    "cover":   slide_cover,
    "brief":   slide_brief,
    "feature": slide_feature,
    "numlist": slide_numlist,
    "stats":   slide_stats,
    "cta":     slide_cta,
}


def build_html(slide_data: dict, idx: int, total: int, font_css: str, photo_src: str) -> str:
    kind    = slide_data.get("type", "feature")
    builder = BUILDERS.get(kind, slide_feature)

    if kind == "cover":
        body_html = builder(slide_data, total, photo_src)
    else:
        body_html = builder(slide_data, idx, total)

    return f"""<!DOCTYPE html>
<html lang="ru"><head>
<meta charset="UTF-8">
<style>
{font_css}
{BASE_CSS}
</style>
</head><body>{body_html}</body></html>"""


def render_slides(slides: list, output_dir: str, prefix: str, photo_path: str = "") -> list:
    font_css  = build_font_css()
    photo_src = encode_photo(photo_path) if photo_path else ""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    total  = len(slides)
    paths  = []

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROMIUM_PATH)
        ctx     = browser.new_context(viewport={"width": SLIDE_W, "height": SLIDE_H})
        page    = ctx.new_page()

        for i, slide in enumerate(slides, 1):
            html = build_html(slide, i, total, font_css, photo_src)
            page.set_content(html, wait_until="domcontentloaded")
            out  = output_dir / f"{prefix}_{str(i).zfill(2)}.png"
            page.screenshot(path=str(out),
                            clip={"x": 0, "y": 0, "width": SLIDE_W, "height": SLIDE_H})
            paths.append(str(out))
            print(f"  ✓ {out.name}")

        browser.close()

    return paths


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("content",    help="JSON file with slide data")
    ap.add_argument("output_dir", nargs="?", default="output", help="Output folder")
    ap.add_argument("--photo",    default="", help="Path to cover photo (JPG/PNG)")
    args = ap.parse_args()

    with open(args.content, "r", encoding="utf-8") as f:
        data = json.load(f)

    slides = data.get("slides", data) if isinstance(data, dict) else data
    prefix = data.get("prefix", "slide") if isinstance(data, dict) else "slide"

    print(f"Generating {len(slides)} slides  [{SLIDE_W}×{SLIDE_H}px, 4:5]")
    if args.photo:
        print(f"Photo: {args.photo}")

    paths = render_slides(slides, args.output_dir, prefix, args.photo)
    print(f"\nDone! {len(paths)} slides → '{args.output_dir}/'")

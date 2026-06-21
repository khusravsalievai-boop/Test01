#!/usr/bin/env python3
"""
Instagram carousel generator — husrav.ai style.
Format: 4:5 (1080×1350 px)
Usage: python3 generator.py content.json [output_dir] [--photo /path/to/photo.jpg]
"""

import json, sys, os, base64, argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

CHROMIUM_PATH = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
FONTS_DIR     = Path(__file__).parent / "fonts"
SLIDE_W, SLIDE_H = 1080, 1350

# ── fonts ──────────────────────────────────────────────────────────────────────
def _b64(filename):
    p = FONTS_DIR / filename
    return base64.b64encode(p.read_bytes()).decode() if p.exists() else ""

def font_css():
    bb = _b64("BebasNeue.ttf")
    mr = _b64("Montserrat-Regular.ttf")
    mb = _b64("Montserrat-Bold.ttf")
    me = _b64("Montserrat-ExtraBold.ttf")
    mx = _b64("Montserrat-Black.ttf")
    out = ""
    # "Display" = Bebas for Latin digits/latin, Montserrat Black for Cyrillic
    if bb:
        out += f"""@font-face{{font-family:'Display';font-weight:400;
  src:url('data:font/truetype;base64,{bb}')format('truetype');
  unicode-range:U+0020-007F,U+00A0-00FF;}}"""
    if mx:
        out += f"""@font-face{{font-family:'Display';font-weight:400;
  src:url('data:font/truetype;base64,{mx}')format('truetype');
  unicode-range:U+0400-04FF,U+0500-052F,U+1C80-1C8F;}}"""
    if mr:
        out += f"""@font-face{{font-family:'Montserrat';font-weight:400;
  src:url('data:font/truetype;base64,{mr}')format('truetype');}}"""
    if mb:
        out += f"""@font-face{{font-family:'Montserrat';font-weight:700;
  src:url('data:font/truetype;base64,{mb}')format('truetype');}}"""
    if me:
        out += f"""@font-face{{font-family:'Montserrat';font-weight:800;
  src:url('data:font/truetype;base64,{me}')format('truetype');}}"""
    if mx:
        out += f"""@font-face{{font-family:'Montserrat';font-weight:900;
  src:url('data:font/truetype;base64,{mx}')format('truetype');}}"""
    return out

def encode_photo(path):
    if not path or not Path(path).exists():
        return ""
    data = Path(path).read_bytes()
    ext  = Path(path).suffix.lower().lstrip(".")
    mime = "jpeg" if ext in ("jpg","jpeg") else ext
    return f"data:image/{mime};base64,{base64.b64encode(data).decode()}"

# ── CSS ────────────────────────────────────────────────────────────────────────
BASE_CSS = """
:root {
  --bg:      #0A0C08;
  --green:   #C8FF00;
  --white:   #F2F2EE;
  --gray:    #5A5A5A;
  --gray2:   #333;
  --surface: #111408;
  --border:  #1C2214;
  --deco:    #111408;
}

* { margin:0; padding:0; box-sizing:border-box; }
body { background:var(--bg); color:var(--white); }

.slide {
  width: 1080px;
  height: 1350px;
  background: var(--bg);
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* ── typography ── */
.t-display {
  font-family: 'Display', 'Arial Black', Arial, sans-serif;
  font-weight: 400;
  letter-spacing: 0.01em;
  text-transform: uppercase;
  line-height: 0.92;
}
.t-ui {
  font-family: 'Montserrat', Arial, sans-serif;
}

.c-white { color: var(--white); }
.c-green { color: var(--green); }
.c-gray  { color: var(--gray);  }

/* ── shared atoms ── */

/* eyebrow tag */
.eyebrow {
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.28em;
  text-transform: uppercase;
  color: var(--gray);
  display: flex;
  align-items: center;
  gap: 10px;
}
.eyebrow-dot {
  width: 6px; height: 6px;
  background: var(--green);
  border-radius: 50%;
  flex-shrink: 0;
}
/* thin rule below eyebrow */
.eyebrow-rule {
  width: 40px; height: 1px;
  background: var(--green);
  opacity: 0.5;
  margin-left: 4px;
}

/* bottom bar */
.btm {
  position: absolute;
  bottom: 52px;
  left: 64px;
  right: 64px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 10;
}
.brand {
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 16px;
  font-weight: 700;
  color: #363636;
  letter-spacing: 0.06em;
}
.counter {
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 16px;
  font-weight: 700;
  color: #363636;
  letter-spacing: 0.04em;
}

/* giant background deco number */
.deco {
  font-family: 'Display', 'Arial Black', Arial, sans-serif;
  font-weight: 400;
  font-size: 520px;
  line-height: 0.80;
  color: var(--deco);
  position: absolute;
  right: -24px;
  top: 10px;
  letter-spacing: -0.02em;
  z-index: 0;
  user-select: none;
  pointer-events: none;
}

/* pills */
.pills { display:flex; gap:12px; flex-wrap:wrap; }
.pill {
  display: flex;
  align-items: center;
  gap: 9px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 100px;
  padding: 12px 24px;
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 14px;
  font-weight: 600;
  color: #9a9a9a;
  letter-spacing: 0.04em;
}
.pill-dot { width:7px; height:7px; border-radius:50%; background:var(--green); }

/* CTA button */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 14px;
  background: var(--green);
  color: #000;
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 17px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  padding: 18px 36px;
  border-radius: 8px;
}
.btn-arrow { font-size: 20px; }

/* numbered circle */
.num-circle {
  min-width: 50px; width: 50px; height: 50px;
  background: var(--green);
  color: #000;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 20px; font-weight: 900;
}

/* ════════════════════════════════════════
   SLIDE 1 — COVER
════════════════════════════════════════ */
.s-cover .photo {
  position: absolute;
  inset: 0; z-index: 0;
}
.s-cover .photo img {
  width: 100%; height: 100%;
  object-fit: cover;
  object-position: top center;
  display: block;
}
/* full dark gradient overlay */
.s-cover .photo::after {
  content: '';
  position: absolute; inset: 0;
  background:
    linear-gradient(to top,   #0A0C08 0%,  #0A0C08ee 22%, #0A0C0888 48%, transparent 72%),
    linear-gradient(to right, #0A0C08 0%,  #0A0C08cc 30%, transparent 62%);
  z-index: 1;
}
/* no-photo dark fallback */
.s-cover .no-photo {
  position: absolute; inset: 0;
  background: radial-gradient(ellipse at 70% 30%, #1a2410 0%, var(--bg) 70%);
  z-index: 0;
}

.s-cover .content {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  padding: 0 64px 150px;
  z-index: 5;
}
.s-cover .cover-hl {
  font-family: 'Display', 'Arial Black', Arial, sans-serif;
  font-weight: 400;
  font-size: 118px;
  line-height: 0.90;
  text-transform: uppercase;
  letter-spacing: 0.01em;
  margin-bottom: 24px;
}
.s-cover .cover-sub {
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 19px; font-weight: 400;
  color: #888;
  line-height: 1.55;
  max-width: 500px;
  margin-bottom: 48px;
}

/* top eyebrow on cover */
.s-cover .cover-top {
  position: absolute;
  top: 60px; left: 64px; right: 64px;
  display: flex; justify-content: space-between; align-items: center;
  z-index: 5;
}

/* ════════════════════════════════════════
   SLIDE 2 — BRIEF / 00
════════════════════════════════════════ */
.s-brief .pad { padding: 72px 64px 0; height: 100%; position: relative; }

.s-brief .hl {
  font-family: 'Display', 'Arial Black', Arial, sans-serif;
  font-weight: 400;
  font-size: 105px;
  line-height: 0.90;
  text-transform: uppercase;
  letter-spacing: 0.01em;
  margin-top: 72px;
  margin-bottom: 36px;
  max-width: 820px;
  position: relative; z-index: 2;
}
.s-brief .body {
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 21px; font-weight: 400;
  color: #7a7a7a;
  line-height: 1.65;
  max-width: 700px;
  margin-bottom: 56px;
  position: relative; z-index: 2;
}

/* ════════════════════════════════════════
   SLIDE 3 — FEATURE
════════════════════════════════════════ */
.s-feat .pad { padding: 72px 64px 0; height: 100%; position: relative; }
.s-feat .hl {
  font-family: 'Display', 'Arial Black', Arial, sans-serif;
  font-weight: 400;
  font-size: 105px;
  line-height: 0.90;
  text-transform: uppercase;
  letter-spacing: 0.01em;
  margin-top: 72px;
  margin-bottom: 32px;
  max-width: 820px;
  position: relative; z-index: 2;
}
.s-feat .body {
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 21px; font-weight: 400;
  color: #7a7a7a;
  line-height: 1.65;
  max-width: 700px;
  margin-bottom: 52px;
  position: relative; z-index: 2;
}

/* accent arrow between words */
.arrow-accent {
  color: var(--green);
  font-family: 'Montserrat', Arial, sans-serif;
  font-weight: 900;
  font-size: 0.85em;
  margin: 0 6px;
}

/* ════════════════════════════════════════
   SLIDE 4 — NUMLIST
════════════════════════════════════════ */
.s-list .pad { padding: 72px 64px 0; height: 100%; position: relative; }
.s-list .hl {
  font-family: 'Display', 'Arial Black', Arial, sans-serif;
  font-weight: 400;
  font-size: 95px;
  line-height: 0.90;
  text-transform: uppercase;
  letter-spacing: 0.01em;
  margin-bottom: 56px;
  max-width: 820px;
  position: relative; z-index: 2;
}
.s-list .items { display:flex; flex-direction:column; gap:34px; position:relative; z-index:2; }
.s-list .item  { display:flex; align-items:flex-start; gap:24px; }
.s-list .item-text .ititle {
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 26px; font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  line-height: 1.1;
  margin-bottom: 8px;
  color: var(--white);
}
.s-list .item-text .isub {
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 16px; font-weight: 400;
  color: var(--gray);
}
.s-list .footer {
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 17px; color: #4a4a4a;
  margin-top: 44px;
  position: relative; z-index:2;
}

/* ════════════════════════════════════════
   SLIDE 5 — STATS
════════════════════════════════════════ */
.s-stats .pad { padding: 72px 64px 0; height: 100%; position: relative; }
.s-stats .hl {
  font-family: 'Display', 'Arial Black', Arial, sans-serif;
  font-weight: 400;
  font-size: 105px;
  line-height: 0.90;
  text-transform: uppercase;
  letter-spacing: 0.01em;
  margin-top: 72px;
  margin-bottom: 32px;
  max-width: 820px;
  position: relative; z-index: 2;
}
.s-stats .body {
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 21px; font-weight: 400;
  color: #7a7a7a;
  line-height: 1.65;
  max-width: 700px;
  margin-bottom: 68px;
  position: relative; z-index: 2;
}
.s-stats .nums { display:flex; gap:72px; position:relative; z-index:2; }
.s-stats .sval {
  font-family: 'Display', 'Arial Black', Arial, sans-serif;
  font-weight: 400;
  font-size: 130px;
  line-height: 0.85;
  color: var(--green);
  letter-spacing: -0.01em;
}
.s-stats .slbl {
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 13px; font-weight: 700;
  color: var(--gray2);
  text-transform: uppercase;
  letter-spacing: 0.14em;
  margin-top: 10px;
}

/* ════════════════════════════════════════
   SLIDE 6 — CTA
════════════════════════════════════════ */
.s-cta .pad {
  padding: 72px 64px;
  height: 100%;
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding-bottom: 150px;
}
.s-cta .hl {
  font-family: 'Display', 'Arial Black', Arial, sans-serif;
  font-weight: 400;
  font-size: 108px;
  line-height: 0.90;
  text-transform: uppercase;
  letter-spacing: 0.01em;
  margin-bottom: 36px;
  max-width: 820px;
  position: relative; z-index: 2;
}
.s-cta .body {
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 21px; font-weight: 400;
  color: #7a7a7a;
  line-height: 1.65;
  max-width: 700px;
  margin-bottom: 52px;
  position: relative; z-index: 2;
}
"""

# ── helpers ────────────────────────────────────────────────────────────────────

def hl_html(lines):
    """Build headline HTML from line list."""
    out = ""
    for ln in lines:
        cls = "c-green" if ln.get("green") else "c-white"
        out += f'<span class="{cls}">{ln["text"]}</span><br>'
    return out

def eyebrow(text):
    return f'<div class="eyebrow"><span class="eyebrow-dot"></span>{text}<span class="eyebrow-rule"></span></div>'

def btm_bar(brand, idx=None, total=None):
    counter = f'<div class="counter">{str(idx).zfill(2)} / {str(total).zfill(2)}</div>' if idx else ""
    return f'<div class="btm"><div class="brand">{brand}</div>{counter}</div>'

def pills_html(pills):
    return '<div class="pills">' + "".join(
        f'<div class="pill"><span class="pill-dot"></span>{p}</div>' for p in pills
    ) + "</div>"

def wrap(body_class, inner):
    return f'<div class="slide {body_class}">{inner}</div>'

# ── slide builders ─────────────────────────────────────────────────────────────

def build_cover(d, total, photo_src=""):
    src  = photo_src or d.get("photo", "")
    tag  = d.get("tag", "")
    brand= d.get("brand", "husrav.ai")
    cta  = d.get("cta", "ЛИСТАЙ")

    photo_el = (f'<div class="photo"><img src="{src}"/></div>' if src
                else '<div class="no-photo"></div>')

    tag_el = eyebrow(tag) if tag else ""
    brand_el = f'<div class="brand">{brand}</div>'

    inner = f"""
{photo_el}
<div class="cover-top">
  {tag_el}
  {brand_el}
</div>
<div class="content">
  <div class="cover-hl">{hl_html(d.get("headline",[]))}</div>
  <div class="cover-sub">{d.get("subtext","")}</div>
  <div class="btn"><span>{cta}</span><span class="btn-arrow">→</span></div>
</div>
{btm_bar(brand)}
"""
    return wrap("s-cover", inner)


def build_brief(d, idx, total):
    brand = d.get("brand", "husrav.ai")
    deco  = str(idx - 1).zfill(2)
    inner = f"""
<div class="pad">
  {eyebrow(d.get("tag","КРАТКО"))}
  <div class="deco">{deco}</div>
  <div class="hl">{hl_html(d.get("headline",[]))}</div>
  <div class="body">{d.get("body","")}</div>
  <div style="position:relative;z-index:2">{pills_html(d.get("pills",[]))}</div>
  {btm_bar(brand, idx, total)}
</div>"""
    return wrap("s-brief", inner)


def build_feature(d, idx, total):
    brand = d.get("brand", "husrav.ai")
    deco  = str(idx - 1).zfill(2)
    inner = f"""
<div class="pad">
  {eyebrow(d.get("tag","КАК ЭТО РАБОТАЕТ"))}
  <div class="deco">{deco}</div>
  <div class="hl">{hl_html(d.get("headline",[]))}</div>
  <div class="body">{d.get("body","")}</div>
  {btm_bar(brand, idx, total)}
</div>"""
    return wrap("s-feat", inner)


def build_numlist(d, idx, total):
    brand = d.get("brand", "husrav.ai")
    items_h = "".join(f"""<div class="item">
      <div class="num-circle">{i}</div>
      <div class="item-text">
        <div class="ititle">{it.get('title','')}</div>
        <div class="isub">{it.get('sub','')}</div>
      </div>
    </div>""" for i, it in enumerate(d.get("items",[]), 1))

    footer_h = f'<div class="footer">{d["footer"]}</div>' if d.get("footer") else ""

    inner = f"""
<div class="pad">
  {eyebrow(d.get("tag","ВОЗМОЖНОСТИ"))}
  <div class="hl">{hl_html(d.get("headline",[]))}</div>
  <div class="items">{items_h}</div>
  {footer_h}
  {btm_bar(brand, idx, total)}
</div>"""
    return wrap("s-list", inner)


def build_stats(d, idx, total):
    brand = d.get("brand", "husrav.ai")
    deco  = str(idx - 1).zfill(2)
    nums_h = "".join(f"""<div class="stat-item">
      <div class="sval">{s.get('value','')}</div>
      <div class="slbl">{s.get('label','')}</div>
    </div>""" for s in d.get("stats",[]))

    inner = f"""
<div class="pad">
  {eyebrow(d.get("tag","ЦИФРЫ"))}
  <div class="deco">{deco}</div>
  <div class="hl">{hl_html(d.get("headline",[]))}</div>
  <div class="body">{d.get("body","")}</div>
  <div class="nums">{nums_h}</div>
  {btm_bar(brand, idx, total)}
</div>"""
    return wrap("s-stats", inner)


def build_cta(d, idx, total):
    brand = d.get("brand", "husrav.ai")
    deco  = str(idx - 1).zfill(2)
    inner = f"""
<div class="pad">
  {eyebrow(d.get("tag","ЗАБИРАЙ"))}
  <div class="deco">{deco}</div>
  <div class="hl">{hl_html(d.get("headline",[]))}</div>
  <div class="body">{d.get("body","")}</div>
  <div class="btn" style="position:relative;z-index:2">
    <span>{d.get("cta","НАПИСАТЬ В КОММЕНТАРИИ")}</span>
    <span class="btn-arrow">→</span>
  </div>
  {btm_bar(brand, idx, total)}
</div>"""
    return wrap("s-cta", inner)


BUILDERS = {
    "cover":   build_cover,
    "brief":   build_brief,
    "feature": build_feature,
    "numlist": build_numlist,
    "stats":   build_stats,
    "cta":     build_cta,
}

# ── render ─────────────────────────────────────────────────────────────────────

def make_html(slide, idx, total, fcss, photo_src):
    kind = slide.get("type", "feature")
    fn   = BUILDERS.get(kind, build_feature)
    body = fn(slide, total, photo_src) if kind == "cover" else fn(slide, idx, total)
    return f"""<!DOCTYPE html><html lang="ru"><head>
<meta charset="UTF-8">
<style>{fcss}{BASE_CSS}</style>
</head><body>{body}</body></html>"""


def render(slides, output_dir, prefix, photo_path=""):
    fcss      = font_css()
    photo_src = encode_photo(photo_path)
    out       = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    total     = len(slides)
    paths     = []

    with sync_playwright() as p:
        br  = p.chromium.launch(executable_path=CHROMIUM_PATH)
        ctx = br.new_context(viewport={"width": SLIDE_W, "height": SLIDE_H})
        pg  = ctx.new_page()
        for i, slide in enumerate(slides, 1):
            html = make_html(slide, i, total, fcss, photo_src)
            pg.set_content(html, wait_until="domcontentloaded")
            fp = out / f"{prefix}_{str(i).zfill(2)}.png"
            pg.screenshot(path=str(fp),
                          clip={"x":0,"y":0,"width":SLIDE_W,"height":SLIDE_H})
            paths.append(str(fp))
            print(f"  ✓ {fp.name}")
        br.close()
    return paths


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("content")
    ap.add_argument("output_dir", nargs="?", default="output")
    ap.add_argument("--photo", default="")
    args = ap.parse_args()

    with open(args.content, encoding="utf-8") as f:
        data = json.load(f)

    slides = data.get("slides", data) if isinstance(data, dict) else data
    prefix = data.get("prefix", "slide") if isinstance(data, dict) else "slide"

    print(f"Generating {len(slides)} slides [{SLIDE_W}×{SLIDE_H}px]")
    paths = render(slides, args.output_dir, prefix, args.photo)
    print(f"\nDone → '{args.output_dir}/'")

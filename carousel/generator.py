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

# ── grain texture (film-grain SVG, embedded) ───────────────────────────────────
_GRAIN_SVG = """<svg xmlns='http://www.w3.org/2000/svg' width='256' height='256'>
<filter id='g'><feTurbulence type='fractalNoise' baseFrequency='0.80'
numOctaves='4' stitchTiles='stitch'/><feColorMatrix type='saturate' values='0'/>
</filter><rect width='256' height='256' filter='url(#g)'/></svg>"""
GRAIN_URL = "data:image/svg+xml;base64," + base64.b64encode(_GRAIN_SVG.encode()).decode()

# ── 4-pointed star SVG (inline, lime green) ───────────────────────────────────
STAR_SVG = """<svg viewBox='0 0 24 24' width='15' height='15'
  xmlns='http://www.w3.org/2000/svg' style='display:inline-block;flex-shrink:0'>
  <path d='M12 0 L13.8 10.2 L24 12 L13.8 13.8 L12 24 L10.2 13.8 L0 12 L10.2 10.2 Z'
    fill='#C8FF00'/>
</svg>"""

# ── dots grid pattern (corner accent) ─────────────────────────────────────────
def dots_grid(cols=5, rows=5, size=5, gap=14, color="rgba(200,255,0,0.18)"):
    items = ""
    for r in range(rows):
        for c in range(cols):
            x = c * (size + gap)
            y = r * (size + gap)
            items += f"<circle cx='{x+size/2}' cy='{y+size/2}' r='{size/2}' fill='{color}'/>"
    w = cols * (size + gap)
    h = rows * (size + gap)
    svg = f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}'>{items}</svg>"
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()

DOTS_URL = dots_grid()

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
    if bb:
        out += f"@font-face{{font-family:'Display';font-weight:400;src:url('data:font/truetype;base64,{bb}')format('truetype');unicode-range:U+0020-007F,U+00A0-00FF;}}\n"
    if mx:
        out += f"@font-face{{font-family:'Display';font-weight:400;src:url('data:font/truetype;base64,{mx}')format('truetype');unicode-range:U+0400-04FF,U+0500-052F;}}\n"
    for w, fn in [(400,mr),(700,mb),(800,me),(900,mx)]:
        if fn:
            out += f"@font-face{{font-family:'Montserrat';font-weight:{w};src:url('data:font/truetype;base64,{fn}')format('truetype');}}\n"
    return out

def encode_photo(path):
    if not path or not Path(path).exists():
        return ""
    data = Path(path).read_bytes()
    ext  = Path(path).suffix.lower().lstrip(".")
    mime = "jpeg" if ext in ("jpg","jpeg") else ext
    return f"data:image/{mime};base64,{base64.b64encode(data).decode()}"

# ── CSS ────────────────────────────────────────────────────────────────────────
def build_base_css():
    return f"""
:root {{
  --bg:      #09090A;
  --green:   #C8FF00;
  --white:   #F0F0EC;
  --gray:    #565656;
  --gray2:   #252525;
  --surface: #0F1008;
  --border:  #1C2010;
}}

* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:var(--bg); }}

/* ── SLIDE SHELL ── */
.slide {{
  width: {SLIDE_W}px;
  height: {SLIDE_H}px;
  background: var(--bg);
  position: relative;
  overflow: hidden;
}}

/* subtle ambient glow — top-right corner */
.slide::before {{
  content: '';
  position: absolute;
  top: -200px; right: -200px;
  width: 700px; height: 700px;
  background: radial-gradient(circle, rgba(100,180,0,0.07) 0%, transparent 65%);
  z-index: 0;
  pointer-events: none;
}}

/* film-grain overlay on every slide */
.slide::after {{
  content: '';
  position: absolute;
  inset: 0;
  background-image: url('{GRAIN_URL}');
  background-size: 256px 256px;
  background-repeat: repeat;
  opacity: 0.045;
  z-index: 300;
  pointer-events: none;
  mix-blend-mode: overlay;
}}

/* ── TYPOGRAPHY ── */
.t-display {{
  font-family: 'Display', 'Arial Black', Arial, sans-serif;
  font-weight: 400;
  text-transform: uppercase;
  line-height: 0.90;
  letter-spacing: 0.01em;
}}
.t-ui {{ font-family: 'Montserrat', Arial, sans-serif; }}

/* colours */
.c-white {{ color: var(--white); }}
.c-green {{
  color: var(--green);
  text-shadow: 0 0 50px rgba(200,255,0,0.20), 0 0 120px rgba(200,255,0,0.08);
}}
.c-gray  {{ color: var(--gray); }}

/* ── EYEBROW ── */
.eyebrow {{
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.30em;
  text-transform: uppercase;
  color: var(--gray);
}}

/* ── DECO NUMBER — outline stroke, no fill ── */
.deco {{
  font-family: 'Display', 'Arial Black', Arial, sans-serif;
  font-weight: 400;
  font-size: 560px;
  line-height: 0.78;
  position: absolute;
  right: -30px;
  top: -10px;
  letter-spacing: -0.02em;
  z-index: 1;
  user-select: none;
  pointer-events: none;
  /* outline-only — premium look */
  -webkit-text-stroke: 2px rgba(80,140,10,0.40);
  -webkit-text-fill-color: transparent;
  color: transparent;
}}

/* ── DIVIDER LINE above bottom bar ── */
.divider {{
  position: absolute;
  bottom: 104px;
  left: 64px;
  right: 64px;
  height: 1px;
  background: linear-gradient(to right, var(--border) 0%, var(--border) 70%, transparent 100%);
  z-index: 5;
}}

/* ── BOTTOM BAR ── */
.btm {{
  position: absolute;
  bottom: 52px;
  left: 64px;
  right: 64px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 10;
}}
.brand {{
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 16px; font-weight: 700;
  color: #383838;
  letter-spacing: 0.06em;
}}
.counter {{
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 16px; font-weight: 700;
  color: #383838;
  letter-spacing: 0.04em;
}}

/* ── PILLS ── */
.pills {{ display:flex; gap:12px; flex-wrap:wrap; }}
.pill {{
  display: flex; align-items: center; gap: 10px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 100px;
  padding: 13px 26px;
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 15px; font-weight: 600;
  color: #888;
  letter-spacing: 0.03em;
}}
.pill-dot {{ width:8px; height:8px; border-radius:50%; background:var(--green);
  box-shadow: 0 0 8px rgba(200,255,0,0.5); }}

/* ── CTA BUTTON ── */
.btn {{
  display: inline-flex; align-items: center; gap: 16px;
  background: var(--green);
  color: #000;
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 18px; font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  padding: 20px 38px;
  border-radius: 10px;
  box-shadow: 0 0 40px rgba(200,255,0,0.25), 0 0 80px rgba(200,255,0,0.10);
}}

/* ── NUMBERED CIRCLE ── */
.num-circle {{
  min-width: 52px; width: 52px; height: 52px;
  background: var(--green);
  color: #000;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-family: 'Montserrat', Arial, sans-serif;
  font-size: 21px; font-weight: 900;
  box-shadow: 0 0 20px rgba(200,255,0,0.30);
}}

/* ── CORNER DOTS ACCENT ── */
.dots-br {{
  position: absolute;
  bottom: 140px; right: 56px;
  width: 90px; height: 90px;
  background-image: url('{DOTS_URL}');
  background-repeat: no-repeat;
  background-size: contain;
  opacity: 0.6;
  z-index: 2;
  pointer-events: none;
}}

/* thin vertical green line accent */
.vline {{
  position: absolute;
  top: 64px; left: 0;
  width: 3px; height: 100px;
  background: linear-gradient(to bottom, transparent, var(--green), transparent);
  opacity: 0.5;
  z-index: 5;
}}

/* ════════════ COVER ════════════ */
.s-cover .photo {{
  position: absolute; inset:0; z-index:0;
}}
.s-cover .photo img {{
  width:100%; height:100%;
  object-fit:cover; object-position:top center;
}}
.s-cover .photo::after {{
  content:'';
  position:absolute; inset:0;
  background:
    linear-gradient(to top,   #09090A 0%, #09090Aee 20%, #09090Abb 42%, transparent 68%),
    linear-gradient(to right, #09090A 0%, #09090Add 28%, transparent 58%);
  z-index:1;
}}
.s-cover .no-photo {{
  position:absolute; inset:0;
  background: radial-gradient(ellipse at 70% 25%, #182210 0%, #09090A 55%);
  z-index:0;
}}
.s-cover .cover-top {{
  position:absolute; top:60px; left:64px; right:64px;
  display:flex; justify-content:space-between; align-items:center;
  z-index:5;
}}
.s-cover .content {{
  position:absolute; bottom:0; left:0; right:0;
  padding: 0 64px 148px;
  z-index:5;
}}
.s-cover .cover-hl {{
  font-family:'Display','Arial Black',Arial,sans-serif;
  font-weight:400;
  font-size:116px;
  line-height:0.88;
  text-transform:uppercase;
  letter-spacing:0.01em;
  margin-bottom:24px;
}}
.s-cover .cover-sub {{
  font-family:'Montserrat',Arial,sans-serif;
  font-size:19px; font-weight:400;
  color:#777;
  line-height:1.55;
  max-width:520px;
  margin-bottom:52px;
}}

/* ════════════ BRIEF ════════════ */
.s-brief .pad {{ padding:72px 64px 0; height:100%; position:relative; }}
.s-brief .hl {{
  font-family:'Display','Arial Black',Arial,sans-serif; font-weight:400;
  font-size:108px; line-height:0.88; text-transform:uppercase;
  letter-spacing:0.01em;
  margin-top:68px; margin-bottom:36px;
  max-width:860px; position:relative; z-index:2;
}}
.s-brief .body {{
  font-family:'Montserrat',Arial,sans-serif;
  font-size:22px; font-weight:400; color:#6a6a6a;
  line-height:1.65; max-width:720px;
  margin-bottom:60px; position:relative; z-index:2;
}}

/* ════════════ FEATURE ════════════ */
.s-feat .pad {{ padding:72px 64px 0; height:100%; position:relative; }}
.s-feat .hl {{
  font-family:'Display','Arial Black',Arial,sans-serif; font-weight:400;
  font-size:108px; line-height:0.88; text-transform:uppercase;
  letter-spacing:0.01em;
  margin-top:68px; margin-bottom:32px;
  max-width:860px; position:relative; z-index:2;
}}
.s-feat .body {{
  font-family:'Montserrat',Arial,sans-serif;
  font-size:22px; font-weight:400; color:#6a6a6a;
  line-height:1.65; max-width:720px;
  margin-bottom:52px; position:relative; z-index:2;
}}

/* ════════════ NUMLIST ════════════ */
.s-list .pad {{ padding:72px 64px 0; height:100%; position:relative; }}
.s-list .hl {{
  font-family:'Display','Arial Black',Arial,sans-serif; font-weight:400;
  font-size:96px; line-height:0.88; text-transform:uppercase;
  letter-spacing:0.01em;
  margin-bottom:56px; max-width:860px;
  position:relative; z-index:2;
}}
.s-list .items {{ display:flex; flex-direction:column; gap:36px; position:relative; z-index:2; }}
.s-list .item {{ display:flex; align-items:flex-start; gap:26px; }}
.s-list .ititle {{
  font-family:'Montserrat',Arial,sans-serif;
  font-size:27px; font-weight:800; text-transform:uppercase;
  letter-spacing:0.03em; line-height:1.1;
  margin-bottom:8px; color:var(--white);
}}
.s-list .isub {{
  font-family:'Montserrat',Arial,sans-serif;
  font-size:16px; font-weight:400; color:var(--gray);
}}
.s-list .footer {{
  font-family:'Montserrat',Arial,sans-serif;
  font-size:17px; color:#404040; margin-top:44px; position:relative; z-index:2;
}}

/* ════════════ STATS ════════════ */
.s-stats .pad {{ padding:72px 64px 0; height:100%; position:relative; }}
.s-stats .hl {{
  font-family:'Display','Arial Black',Arial,sans-serif; font-weight:400;
  font-size:108px; line-height:0.88; text-transform:uppercase;
  letter-spacing:0.01em;
  margin-top:68px; margin-bottom:32px;
  max-width:860px; position:relative; z-index:2;
}}
.s-stats .body {{
  font-family:'Montserrat',Arial,sans-serif;
  font-size:22px; font-weight:400; color:#6a6a6a;
  line-height:1.65; max-width:720px;
  margin-bottom:72px; position:relative; z-index:2;
}}
.s-stats .nums {{ display:flex; gap:80px; position:relative; z-index:2; }}
.s-stats .sval {{
  font-family:'Display','Arial Black',Arial,sans-serif; font-weight:400;
  font-size:140px; line-height:0.82;
  color:var(--green);
  text-shadow:0 0 60px rgba(200,255,0,0.25),0 0 120px rgba(200,255,0,0.10);
  letter-spacing:-0.01em;
}}
.s-stats .slbl {{
  font-family:'Montserrat',Arial,sans-serif;
  font-size:13px; font-weight:700; color:var(--gray2);
  text-transform:uppercase; letter-spacing:0.14em; margin-top:10px;
}}

/* ════════════ CTA ════════════ */
.s-cta .pad {{
  padding:72px 64px;
  height:100%; position:relative;
  display:flex; flex-direction:column;
  justify-content:flex-end; padding-bottom:152px;
}}
.s-cta .hl {{
  font-family:'Display','Arial Black',Arial,sans-serif; font-weight:400;
  font-size:110px; line-height:0.88; text-transform:uppercase;
  letter-spacing:0.01em;
  margin-bottom:36px; max-width:860px; position:relative; z-index:2;
}}
.s-cta .body {{
  font-family:'Montserrat',Arial,sans-serif;
  font-size:22px; font-weight:400; color:#6a6a6a;
  line-height:1.65; max-width:720px;
  margin-bottom:52px; position:relative; z-index:2;
}}
"""

# ── helpers ────────────────────────────────────────────────────────────────────

def hl_html(lines):
    out = ""
    for ln in lines:
        cls = "c-green" if ln.get("green") else "c-white"
        out += f'<span class="{cls}">{ln["text"]}</span><br>'
    return out

def eyebrow(text):
    return f'<div class="eyebrow">{STAR_SVG}<span>{text}</span></div>'

def btm(brand, idx=None, total=None):
    ctr = f'<div class="counter">{str(idx).zfill(2)} / {str(total).zfill(2)}</div>' if idx else ""
    return f'<div class="divider"></div><div class="btm"><div class="brand">{brand}</div>{ctr}</div>'

def pills_html(pills):
    return '<div class="pills">' + "".join(
        f'<div class="pill"><span class="pill-dot"></span>{p}</div>' for p in pills
    ) + "</div>"

def wrap(cls, inner):
    return f'<div class="slide {cls}">{inner}</div>'

# ── slide builders ─────────────────────────────────────────────────────────────

def build_cover(d, total, photo_src=""):
    src   = photo_src or d.get("photo", "")
    tag   = d.get("tag", "")
    brand = d.get("brand", "husrav.ai")
    cta   = d.get("cta", "ЛИСТАЙ")

    photo_el = (f'<div class="photo"><img src="{src}"/></div>' if src
                else '<div class="no-photo"></div>')
    tag_el   = eyebrow(tag) if tag else ""

    inner = f"""
{photo_el}
<div class="cover-top">{tag_el}<div class="brand">{brand}</div></div>
<div class="content">
  <div class="cover-hl">{hl_html(d.get("headline",[]))}</div>
  <div class="cover-sub">{d.get("subtext","")}</div>
  <div class="btn"><span>{cta}</span><span>→</span></div>
</div>
<div class="divider"></div>
<div class="btm"><div class="brand">{brand}</div></div>
"""
    return wrap("s-cover", inner)


def build_brief(d, idx, total):
    brand = d.get("brand", "husrav.ai")
    deco  = str(idx - 1).zfill(2)
    inner = f"""
<div class="pad">
  {eyebrow(d.get("tag","КРАТКО"))}
  <div class="deco">{deco}</div>
  <div class="vline"></div>
  <div class="hl">{hl_html(d.get("headline",[]))}</div>
  <div class="body">{d.get("body","")}</div>
  <div style="position:relative;z-index:2">{pills_html(d.get("pills",[]))}</div>
  <div class="dots-br"></div>
  {btm(brand, idx, total)}
</div>"""
    return wrap("s-brief", inner)


def build_feature(d, idx, total):
    brand = d.get("brand", "husrav.ai")
    deco  = str(idx - 1).zfill(2)
    inner = f"""
<div class="pad">
  {eyebrow(d.get("tag","КАК ЭТО РАБОТАЕТ"))}
  <div class="deco">{deco}</div>
  <div class="vline"></div>
  <div class="hl">{hl_html(d.get("headline",[]))}</div>
  <div class="body">{d.get("body","")}</div>
  <div class="dots-br"></div>
  {btm(brand, idx, total)}
</div>"""
    return wrap("s-feat", inner)


def build_numlist(d, idx, total):
    brand   = d.get("brand", "husrav.ai")
    items_h = "".join(f"""<div class="item">
      <div class="num-circle">{i}</div>
      <div><div class="ititle">{it.get('title','')}</div>
           <div class="isub">{it.get('sub','')}</div></div>
    </div>""" for i, it in enumerate(d.get("items",[]), 1))
    footer_h = f'<div class="footer">{d["footer"]}</div>' if d.get("footer") else ""
    inner = f"""
<div class="pad">
  {eyebrow(d.get("tag","ВОЗМОЖНОСТИ"))}
  <div class="hl">{hl_html(d.get("headline",[]))}</div>
  <div class="items">{items_h}</div>
  {footer_h}
  {btm(brand, idx, total)}
</div>"""
    return wrap("s-list", inner)


def build_stats(d, idx, total):
    brand  = d.get("brand", "husrav.ai")
    deco   = str(idx - 1).zfill(2)
    nums_h = "".join(f"""<div>
      <div class="sval">{s.get('value','')}</div>
      <div class="slbl">{s.get('label','')}</div>
    </div>""" for s in d.get("stats",[]))
    inner = f"""
<div class="pad">
  {eyebrow(d.get("tag","ЦИФРЫ"))}
  <div class="deco">{deco}</div>
  <div class="vline"></div>
  <div class="hl">{hl_html(d.get("headline",[]))}</div>
  <div class="body">{d.get("body","")}</div>
  <div class="nums">{nums_h}</div>
  {btm(brand, idx, total)}
</div>"""
    return wrap("s-stats", inner)


def build_cta(d, idx, total):
    brand = d.get("brand", "husrav.ai")
    deco  = str(idx - 1).zfill(2)
    inner = f"""
<div class="pad">
  {eyebrow(d.get("tag","ЗАБИРАЙ"))}
  <div class="deco">{deco}</div>
  <div class="vline"></div>
  <div class="hl">{hl_html(d.get("headline",[]))}</div>
  <div class="body">{d.get("body","")}</div>
  <div class="btn" style="position:relative;z-index:2;width:fit-content">
    <span>{d.get("cta","НАПИСАТЬ В КОММЕНТАРИИ")}</span><span>→</span>
  </div>
  {btm(brand, idx, total)}
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

def make_html(slide, idx, total, fcss, base_css, photo_src):
    kind = slide.get("type", "feature")
    fn   = BUILDERS.get(kind, build_feature)
    body = fn(slide, total, photo_src) if kind == "cover" else fn(slide, idx, total)
    return f"""<!DOCTYPE html><html lang="ru"><head>
<meta charset="UTF-8">
<style>{fcss}{base_css}</style>
</head><body>{body}</body></html>"""


def render(slides, output_dir, prefix, photo_path=""):
    fcss      = font_css()
    base_css  = build_base_css()
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
            html = make_html(slide, i, total, fcss, base_css, photo_src)
            pg.set_content(html, wait_until="domcontentloaded")
            fp   = out / f"{prefix}_{str(i).zfill(2)}.png"
            pg.screenshot(path=str(fp), clip={"x":0,"y":0,"width":SLIDE_W,"height":SLIDE_H})
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

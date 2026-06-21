#!/usr/bin/env python3
"""
Carousel generator for Instagram in husrav.ai style.
Usage: python3 generator.py content.json [output_dir]
"""

import json
import sys
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

CHROMIUM_PATH = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
SLIDE_W = 1080
SLIDE_H = 1080

STYLE = """
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&display=swap');

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: 'Montserrat', 'Arial Black', Arial, sans-serif;
  background: #0C0E0A;
  color: #ffffff;
}

.slide {
  width: 1080px;
  height: 1080px;
  background: #0C0E0A;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* ───── COMMON ELEMENTS ───── */

.tag {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #aaaaaa;
  display: flex;
  align-items: center;
  gap: 8px;
}
.tag::before { content: '+'; color: #C5FF00; font-size: 16px; font-weight: 900; }

.brand {
  font-size: 18px;
  font-weight: 700;
  color: #555;
  letter-spacing: 0.04em;
}

.counter {
  font-size: 17px;
  font-weight: 700;
  color: #444;
}

.bottom-bar {
  position: absolute;
  bottom: 44px;
  left: 56px;
  right: 56px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.deco-number {
  position: absolute;
  font-size: 420px;
  font-weight: 900;
  line-height: 0.85;
  color: #141810;
  right: -20px;
  top: -30px;
  user-select: none;
  letter-spacing: -0.04em;
}

.h-white { color: #ffffff; }
.h-green  { color: #C5FF00; }

/* ───── SLIDE 1: COVER ───── */

.cover {
  background: #0C0E0A;
}

.cover .photo-wrap {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 540px;
  height: 1080px;
  overflow: hidden;
}

.cover .photo-wrap img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: top center;
}

.cover .photo-wrap::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(to right, #0C0E0A 0%, #0C0E0A 10%, transparent 60%);
  z-index: 1;
}

.cover .photo-wrap::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 300px;
  background: linear-gradient(to top, #0C0E0A 0%, transparent 100%);
  z-index: 1;
}

.cover .content {
  position: absolute;
  left: 56px;
  top: 80px;
  width: 560px;
  z-index: 2;
}

.cover .cover-tag {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: #888;
  margin-bottom: 40px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.cover .cover-tag .dot {
  width: 5px; height: 5px;
  background: #C5FF00;
  border-radius: 50%;
}

.cover .headline {
  font-size: 72px;
  font-weight: 900;
  line-height: 1.0;
  text-transform: uppercase;
  margin-bottom: 24px;
  letter-spacing: -0.01em;
}

.cover .subtext {
  font-size: 18px;
  font-weight: 400;
  color: #aaaaaa;
  line-height: 1.5;
  max-width: 420px;
  margin-bottom: 56px;
}

.cover .cta-btn {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  background: #C5FF00;
  color: #000000;
  font-size: 18px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding: 16px 32px;
  border-radius: 6px;
}

.cover .cta-btn .arrow {
  font-size: 22px;
  font-weight: 900;
}

/* ───── SLIDE 2: BRIEF (00) ───── */

.brief .inner {
  padding: 64px 56px;
  position: relative;
  height: 100%;
}

.brief .deco-number { top: -20px; right: -10px; }

.brief .headline {
  font-size: 68px;
  font-weight: 900;
  line-height: 1.05;
  text-transform: uppercase;
  letter-spacing: -0.01em;
  margin-top: 120px;
  margin-bottom: 32px;
  max-width: 640px;
  position: relative;
  z-index: 2;
}

.brief .body-text {
  font-size: 20px;
  font-weight: 400;
  color: #aaaaaa;
  line-height: 1.6;
  max-width: 600px;
  position: relative;
  z-index: 2;
  margin-bottom: 48px;
}

.pills {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  position: relative;
  z-index: 2;
}

.pill {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #191d14;
  border: 1px solid #2a301f;
  border-radius: 40px;
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 600;
  color: #cccccc;
}

.pill .pill-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: #C5FF00;
}

/* ───── SLIDE 3: FEATURE (01, 02...) ───── */

.feature .inner {
  padding: 64px 56px;
  position: relative;
  height: 100%;
}

.feature .headline {
  font-size: 64px;
  font-weight: 900;
  line-height: 1.05;
  text-transform: uppercase;
  letter-spacing: -0.01em;
  margin-top: 120px;
  margin-bottom: 28px;
  max-width: 680px;
  position: relative;
  z-index: 2;
}

.feature .body-text {
  font-size: 20px;
  font-weight: 400;
  color: #aaaaaa;
  line-height: 1.6;
  max-width: 600px;
  position: relative;
  z-index: 2;
  margin-bottom: 44px;
}

.feature .img-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  position: relative;
  z-index: 2;
}

.feature .img-grid img {
  width: 100%;
  height: 200px;
  object-fit: cover;
  border-radius: 8px;
  background: #1a1f14;
}

.feature .img-placeholder {
  width: 100%;
  height: 200px;
  background: #1a1f14;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #333;
  font-size: 14px;
}

/* ───── SLIDE 4: NUMBERED LIST ───── */

.numlist .inner {
  padding: 64px 56px;
  position: relative;
  height: 100%;
}

.numlist .headline {
  font-size: 58px;
  font-weight: 900;
  line-height: 1.0;
  text-transform: uppercase;
  letter-spacing: -0.01em;
  margin-bottom: 48px;
  max-width: 700px;
  position: relative;
  z-index: 2;
}

.numlist .items {
  display: flex;
  flex-direction: column;
  gap: 24px;
  position: relative;
  z-index: 2;
}

.numlist .item {
  display: flex;
  align-items: flex-start;
  gap: 20px;
}

.numlist .item-num {
  width: 44px;
  height: 44px;
  min-width: 44px;
  background: #C5FF00;
  color: #000;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 900;
  margin-top: 2px;
}

.numlist .item-title {
  font-size: 24px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.02em;
  line-height: 1.1;
  margin-bottom: 6px;
}

.numlist .item-sub {
  font-size: 15px;
  font-weight: 400;
  color: #888;
}

/* ───── SLIDE 5: STATS ───── */

.stats .inner {
  padding: 64px 56px;
  position: relative;
  height: 100%;
}

.stats .headline {
  font-size: 62px;
  font-weight: 900;
  line-height: 1.0;
  text-transform: uppercase;
  letter-spacing: -0.01em;
  margin-top: 80px;
  margin-bottom: 28px;
  max-width: 700px;
  position: relative;
  z-index: 2;
}

.stats .body-text {
  font-size: 19px;
  color: #aaa;
  line-height: 1.6;
  max-width: 600px;
  margin-bottom: 56px;
  position: relative;
  z-index: 2;
}

.stats .numbers-row {
  display: flex;
  gap: 60px;
  position: relative;
  z-index: 2;
}

.stats .stat-item .stat-val {
  font-size: 72px;
  font-weight: 900;
  color: #C5FF00;
  line-height: 1.0;
  letter-spacing: -0.02em;
}

.stats .stat-item .stat-label {
  font-size: 14px;
  font-weight: 600;
  color: #555;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-top: 4px;
}

/* ───── SLIDE 6: CTA (last) ───── */

.cta-slide .inner {
  padding: 64px 56px;
  position: relative;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding-bottom: 140px;
}

.cta-slide .deco-number { top: -40px; right: -20px; font-size: 380px; }

.cta-slide .headline {
  font-size: 68px;
  font-weight: 900;
  line-height: 1.0;
  text-transform: uppercase;
  letter-spacing: -0.01em;
  margin-bottom: 40px;
  max-width: 680px;
  position: relative;
  z-index: 2;
}

.cta-slide .cta-btn {
  display: inline-flex;
  align-items: center;
  gap: 14px;
  background: #C5FF00;
  color: #000;
  font-size: 20px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding: 18px 36px;
  border-radius: 6px;
  position: relative;
  z-index: 2;
  width: fit-content;
}

.cta-slide .body-text {
  font-size: 19px;
  color: #aaa;
  line-height: 1.6;
  max-width: 600px;
  margin-bottom: 44px;
  position: relative;
  z-index: 2;
}
"""


def slide_cover(data: dict, total: int) -> str:
    headline_lines = data.get("headline", [])
    subtext = data.get("subtext", "")
    tag = data.get("tag", "")
    brand = data.get("brand", "husrav.ai")
    photo = data.get("photo", "")
    cta = data.get("cta", "ЛИСТАЙ")

    headline_html = ""
    for line in headline_lines:
        color = "h-green" if line.get("green") else "h-white"
        headline_html += f'<div class="{color}">{line["text"]}</div>'

    photo_html = f'<img src="{photo}" />' if photo else '<div style="width:100%;height:100%;background:linear-gradient(135deg,#1a1f14,#0c0e0a)"></div>'

    tag_html = f'<div class="cover-tag"><span class="dot"></span>{tag}</div>' if tag else ""

    return f"""
<div class="slide cover">
  <div class="photo-wrap">{photo_html}</div>
  <div class="content">
    {tag_html}
    <div class="headline">{headline_html}</div>
    <div class="subtext">{subtext}</div>
    <div class="cta-btn"><span>{cta}</span><span class="arrow">→</span></div>
  </div>
  <div class="bottom-bar">
    <div class="brand">{brand}</div>
  </div>
</div>"""


def slide_brief(data: dict, idx: int, total: int) -> str:
    tag = data.get("tag", "КРАТКО")
    headline_lines = data.get("headline", [])
    body = data.get("body", "")
    pills = data.get("pills", [])
    brand = data.get("brand", "husrav.ai")
    deco_num = str(idx - 1).zfill(2)

    headline_html = ""
    for line in headline_lines:
        color = "h-green" if line.get("green") else "h-white"
        headline_html += f'<span class="{color}">{line["text"]}</span><br>'

    pills_html = "".join(f'<div class="pill"><span class="pill-dot"></span>{p}</div>' for p in pills)

    return f"""
<div class="slide brief">
  <div class="inner">
    <div class="tag">{tag}</div>
    <div class="deco-number">{deco_num}</div>
    <div class="headline">{headline_html}</div>
    <div class="body-text">{body}</div>
    <div class="pills">{pills_html}</div>
    <div class="bottom-bar">
      <div class="brand">{brand}</div>
      <div class="counter">{str(idx).zfill(2)} / {str(total).zfill(2)}</div>
    </div>
  </div>
</div>"""


def slide_feature(data: dict, idx: int, total: int) -> str:
    tag = data.get("tag", "КАК ЭТО РАБОТАЕТ")
    headline_lines = data.get("headline", [])
    body = data.get("body", "")
    brand = data.get("brand", "husrav.ai")
    deco_num = str(idx - 1).zfill(2)

    headline_html = ""
    for line in headline_lines:
        color = "h-green" if line.get("green") else "h-white"
        headline_html += f'<span class="{color}">{line["text"]}</span><br>'

    return f"""
<div class="slide feature">
  <div class="inner">
    <div class="tag">{tag}</div>
    <div class="deco-number">{deco_num}</div>
    <div class="headline">{headline_html}</div>
    <div class="body-text">{body}</div>
    <div class="bottom-bar">
      <div class="brand">{brand}</div>
      <div class="counter">{str(idx).zfill(2)} / {str(total).zfill(2)}</div>
    </div>
  </div>
</div>"""


def slide_numlist(data: dict, idx: int, total: int) -> str:
    tag = data.get("tag", "ВОЗМОЖНОСТИ")
    headline_lines = data.get("headline", [])
    items = data.get("items", [])
    footer = data.get("footer", "")
    brand = data.get("brand", "husrav.ai")

    headline_html = ""
    for line in headline_lines:
        color = "h-green" if line.get("green") else "h-white"
        headline_html += f'<span class="{color}">{line["text"]}</span> '

    items_html = ""
    for i, item in enumerate(items, 1):
        items_html += f"""
        <div class="item">
          <div class="item-num">{i}</div>
          <div>
            <div class="item-title">{item.get('title','')}</div>
            <div class="item-sub">{item.get('sub','')}</div>
          </div>
        </div>"""

    footer_html = f'<div style="font-size:16px;color:#666;margin-top:32px;position:relative;z-index:2">{footer}</div>' if footer else ""

    return f"""
<div class="slide numlist">
  <div class="inner">
    <div class="tag">{tag}</div>
    <div class="headline">{headline_html}</div>
    <div class="items">{items_html}</div>
    {footer_html}
    <div class="bottom-bar">
      <div class="brand">{brand}</div>
      <div class="counter">{str(idx).zfill(2)} / {str(total).zfill(2)}</div>
    </div>
  </div>
</div>"""


def slide_stats(data: dict, idx: int, total: int) -> str:
    tag = data.get("tag", "ЦИФРЫ")
    headline_lines = data.get("headline", [])
    body = data.get("body", "")
    stats_list = data.get("stats", [])
    brand = data.get("brand", "husrav.ai")
    deco_num = str(idx - 1).zfill(2)

    headline_html = ""
    for line in headline_lines:
        color = "h-green" if line.get("green") else "h-white"
        headline_html += f'<span class="{color}">{line["text"]}</span><br>'

    stats_html = ""
    for s in stats_list:
        stats_html += f"""
        <div class="stat-item">
          <div class="stat-val">{s.get('value','')}</div>
          <div class="stat-label">{s.get('label','')}</div>
        </div>"""

    return f"""
<div class="slide stats">
  <div class="inner">
    <div class="tag">{tag}</div>
    <div class="deco-number">{deco_num}</div>
    <div class="headline">{headline_html}</div>
    <div class="body-text">{body}</div>
    <div class="numbers-row">{stats_html}</div>
    <div class="bottom-bar">
      <div class="brand">{brand}</div>
      <div class="counter">{str(idx).zfill(2)} / {str(total).zfill(2)}</div>
    </div>
  </div>
</div>"""


def slide_cta(data: dict, idx: int, total: int) -> str:
    tag = data.get("tag", "ЗАБИРАЙ")
    headline_lines = data.get("headline", [])
    body = data.get("body", "")
    cta = data.get("cta", "ХОЧЕШЬ ССЫЛКУ?")
    brand = data.get("brand", "husrav.ai")
    deco_num = str(idx - 1).zfill(2)

    headline_html = ""
    for line in headline_lines:
        color = "h-green" if line.get("green") else "h-white"
        headline_html += f'<span class="{color}">{line["text"]}</span><br>'

    return f"""
<div class="slide cta-slide">
  <div class="inner">
    <div class="tag">{tag}</div>
    <div class="deco-number">{deco_num}</div>
    <div class="headline">{headline_html}</div>
    <div class="body-text">{body}</div>
    <div class="cta-btn"><span>{cta}</span><span>→</span></div>
    <div class="bottom-bar">
      <div class="brand">{brand}</div>
      <div class="counter">{str(idx).zfill(2)} / {str(total).zfill(2)}</div>
    </div>
  </div>
</div>"""


SLIDE_BUILDERS = {
    "cover": slide_cover,
    "brief": slide_brief,
    "feature": slide_feature,
    "numlist": slide_numlist,
    "stats": slide_stats,
    "cta": slide_cta,
}


def build_html(slides_data: list) -> list:
    total = len(slides_data)
    htmls = []
    for i, slide in enumerate(slides_data):
        kind = slide.get("type", "feature")
        builder = SLIDE_BUILDERS.get(kind, slide_feature)
        if kind == "cover":
            html = builder(slide, total)
        else:
            html = builder(slide, i + 1, total)

        full = f"""<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<style>{STYLE}</style>
</head><body>{html}</body></html>"""
        htmls.append(full)
    return htmls


def render_slides(slides_data: list, output_dir: str, prefix: str = "slide") -> list:
    htmls = build_html(slides_data)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROMIUM_PATH)
        context = browser.new_context(viewport={"width": SLIDE_W, "height": SLIDE_H})
        page = context.new_page()

        for i, html in enumerate(htmls, 1):
            page.set_content(html, wait_until="networkidle")
            out_path = output_dir / f"{prefix}_{str(i).zfill(2)}.png"
            page.screenshot(path=str(out_path), clip={"x": 0, "y": 0, "width": SLIDE_W, "height": SLIDE_H})
            paths.append(str(out_path))
            print(f"  ✓ {out_path.name}")

        browser.close()

    return paths


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 generator.py content.json [output_dir]")
        sys.exit(1)

    content_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output"

    with open(content_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    slides = data.get("slides", data)
    prefix = data.get("prefix", "slide")

    print(f"Generating {len(slides)} slides...")
    paths = render_slides(slides, output_dir, prefix)
    print(f"\nDone! {len(paths)} slides saved to '{output_dir}/'")

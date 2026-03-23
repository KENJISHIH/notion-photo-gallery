"""
generate_html.py
讀取 albums.json，生成 index.html（家族旅行相簿網頁）
"""

import json
import re
from collections import defaultdict
from datetime import datetime

with open("albums.json", encoding="utf-8") as f:
    data = json.load(f)

albums = data["albums"]

# ── 依旅程分組 ──────────────────────────────────────────────────────────────
# 從標籤中找出旅程名稱（排除通用標籤）
GENERIC_TAGS = {"出國", "施家", "家族旅行"}

def trip_tag(album):
    for t in album["tags"]:
        if t not in GENERIC_TAGS:
            return t
    return "其他"

# 分組 + 排序（依日期最新在前）
groups = defaultdict(list)
for a in albums:
    groups[trip_tag(a)].append(a)

# 每組內按日期排序（舊→新）
for g in groups.values():
    g.sort(key=lambda x: x["date"] or "")

# 旅程順序：依最早日期排序（新→舊）
trip_order = sorted(groups.keys(), key=lambda t: groups[t][0]["date"] or "", reverse=True)

# ── 輔助函式 ────────────────────────────────────────────────────────────────
def fmt_date(d):
    if not d:
        return ""
    try:
        return datetime.fromisoformat(d).strftime("%Y.%m.%d")
    except:
        return d

def trip_date_range(group):
    dates = [a["date"] for a in group if a["date"]]
    if not dates:
        return ""
    start = fmt_date(min(dates))
    end = fmt_date(max(dates))
    return start if start == end else f"{start} — {end}"

def extract_year(trip_name):
    m = re.search(r"(\d{4})", trip_name)
    return m.group(1) if m else "—"

def card_html(album, idx):
    name = album["name"]
    url = album["url"]
    date_str = fmt_date(album["date"])

    # Day 幾：從名稱中解析
    day_match = re.search(r"Day\s*(\d+)", name, re.IGNORECASE)
    day_label = f"Day {day_match.group(1)}" if day_match else f"#{idx+1}"

    # 標題：去掉前綴日期和 Day 部分，保留景點描述
    short_name = re.sub(r"^\d{8}[^\s_]*[\s_]*", "", name)  # 去掉 YYYYMMDD 前綴
    short_name = re.sub(r"日本[^\s]*旅行Day\d+_?", "", short_name)  # 去掉旅程名 Day
    short_name = re.sub(r"\d{4}日本[^\s]*Day\d+_?", "", short_name)
    short_name = short_name.strip("_").strip() or name

    link_html = ""
    if url:
        link_html = f'''<a class="card-link link-google" href="{url}" target="_blank" rel="noopener">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
              <path d="M21 12a9 9 0 1 1-9-9 9 9 0 0 1 6.3 2.55"/><path d="M21 3v6h-6"/></svg>
            Google 相簿 →
          </a>'''
    else:
        link_html = '<span class="no-link">相簿待上傳</span>'

    delay = idx * 60
    return f'''    <div class="album-card" style="animation-delay:{delay}ms">
      <div class="card-strip">
        <span class="day-label">{day_label}</span>
        <span class="card-date">{date_str}</span>
      </div>
      <div class="card-body">
        <p class="card-title">{short_name}</p>
        <div class="card-links">{link_html}</div>
      </div>
    </div>'''

# ── 旅程 section HTML ────────────────────────────────────────────────────────
def section_html(trip_name, group):
    year = extract_year(trip_name)
    date_range = trip_date_range(group)
    count = len(group)
    cards = "\n".join(card_html(a, i) for i, a in enumerate(group))
    # data-trip 用 trip_name 的 slug
    slug = re.sub(r"\s+", "-", trip_name.strip())

    return f'''
  <section class="trip-section" data-trip="{slug}">
    <div class="trip-header">
      <span class="trip-year">{year}</span>
      <div class="trip-info">
        <h2 class="trip-name">{trip_name}</h2>
        <p class="trip-meta">{date_range}</p>
      </div>
      <span class="trip-badge">{count} 天</span>
    </div>
    <div class="albums-grid">
{cards}
    </div>
  </section>'''

# ── Filter buttons ───────────────────────────────────────────────────────────
filter_buttons = ['<button class="filter-btn active" data-filter="all">全部旅程</button>']
for t in trip_order:
    slug = re.sub(r"\s+", "-", t.strip())
    filter_buttons.append(f'<button class="filter-btn" data-filter="{slug}">{t}</button>')

# ── 所有 sections ─────────────────────────────────────────────────────────────
all_sections = "\n".join(section_html(t, groups[t]) for t in trip_order)

# ── Stats ─────────────────────────────────────────────────────────────────────
total_trips = len(trip_order)
total_days = len(albums)
has_link_count = sum(1 for a in albums if a["url"])
now = datetime.now().strftime("%Y.%m.%d")

# ── Full HTML ─────────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>家族旅行相簿</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@300;400;700&family=Cormorant+Garamond:ital,wght@0,300;0,600;1,300&display=swap" rel="stylesheet">
<style>
:root {{
  --ink: #1c1510;
  --paper: #f6f1e9;
  --light: #ede8dc;
  --sepia: #b89a6a;
  --rust: #a84e30;
  --muted: #8a7b68;
  --accent: #3d2b1f;
  --card-bg: #fdfaf5;
}}
*,*::before,*::after{{margin:0;padding:0;box-sizing:border-box}}
html{{scroll-behavior:smooth}}
body{{background:var(--paper);color:var(--ink);font-family:'Noto Serif TC',serif;min-height:100vh;position:relative}}
body::after{{content:'';position:fixed;inset:0;background:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='300' height='300' filter='url(%23n)' opacity='.035'/%3E%3C/svg%3E");pointer-events:none;z-index:999}}

/* ── Header ── */
header{{text-align:center;padding:72px 20px 52px;border-bottom:1px solid rgba(184,154,106,.35);background:radial-gradient(ellipse 80% 60% at 50% 0%,rgba(184,154,106,.1) 0%,transparent 70%)}}
.header-eyebrow{{font-family:'Cormorant Garamond',serif;font-style:italic;font-size:.85rem;letter-spacing:.4em;color:var(--sepia);text-transform:uppercase;margin-bottom:18px;display:block}}
header h1{{font-size:clamp(2.6rem,8vw,5rem);font-weight:300;letter-spacing:.18em;color:var(--accent);line-height:1.05}}
.header-sub{{margin-top:14px;font-size:.8rem;letter-spacing:.22em;color:var(--muted)}}
.ornament{{display:flex;align-items:center;justify-content:center;gap:12px;margin-top:28px;color:var(--sepia);font-size:.9rem}}
.ornament::before,.ornament::after{{content:'';flex:0 0 80px;height:1px;background:linear-gradient(90deg,transparent,var(--sepia))}}
.ornament::after{{background:linear-gradient(270deg,transparent,var(--sepia))}}

/* ── Stats ── */
.stats{{display:flex;justify-content:center;gap:48px;padding:28px 20px;background:var(--light);border-bottom:1px solid rgba(184,154,106,.25);flex-wrap:wrap}}
.stat{{text-align:center}}
.stat-n{{font-family:'Cormorant Garamond',serif;font-size:2.4rem;font-weight:300;color:var(--rust);display:block;line-height:1}}
.stat-l{{font-size:.82rem;letter-spacing:.18em;color:var(--muted);margin-top:4px;display:block}}

/* ── Filter bar ── */
.filter-bar{{display:flex;justify-content:center;padding:36px 16px 0;flex-wrap:wrap;gap:0}}
.filter-btn{{background:none;border:1px solid var(--sepia);border-right:none;padding:11px 20px;font-family:'Noto Serif TC',serif;font-size:.85rem;letter-spacing:.1em;color:var(--muted);cursor:pointer;transition:all .2s;white-space:nowrap}}
.filter-btn:first-child{{border-radius:3px 0 0 3px}}
.filter-btn:last-child{{border-right:1px solid var(--sepia);border-radius:0 3px 3px 0}}
.filter-btn:hover{{background:var(--light);color:var(--accent)}}
.filter-btn.active{{background:var(--accent);color:var(--paper);border-color:var(--accent)}}

/* ── Main ── */
main{{max-width:1080px;margin:0 auto;padding:56px 20px 100px}}
.trip-section{{margin-bottom:72px}}
.trip-section.hidden{{display:none}}

/* ── Trip header ── */
.trip-header{{display:flex;align-items:baseline;gap:18px;margin-bottom:28px;padding-bottom:14px;border-bottom:1px solid rgba(184,154,106,.35)}}
.trip-year{{font-family:'Cormorant Garamond',serif;font-size:3rem;font-weight:300;color:var(--sepia);line-height:1;flex-shrink:0}}
.trip-info{{flex:1}}
.trip-name{{font-size:1.25rem;font-weight:400;color:var(--accent);letter-spacing:.08em}}
.trip-meta{{font-size:.85rem;letter-spacing:.15em;color:var(--muted);margin-top:4px}}
.trip-badge{{font-family:'Cormorant Garamond',serif;font-style:italic;font-size:.82rem;color:var(--sepia);border:1px solid var(--sepia);padding:3px 12px;border-radius:20px;flex-shrink:0}}

/* ── Grid ── */
.albums-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:18px}}

/* ── Card ── */
@keyframes rise{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:translateY(0)}}}}
.album-card{{background:var(--card-bg);border:1px solid rgba(184,154,106,.28);border-radius:4px;overflow:hidden;transition:box-shadow .3s,transform .3s,border-color .3s;animation:rise .5s ease both}}
.album-card:hover{{box-shadow:0 10px 36px rgba(61,43,31,.1);transform:translateY(-3px);border-color:var(--sepia)}}
.card-strip{{background:var(--accent);color:var(--paper);padding:9px 16px;display:flex;justify-content:space-between;align-items:center}}
.day-label{{font-size:.85rem;letter-spacing:.18em}}
.card-date{{font-family:'Cormorant Garamond',serif;font-size:.9rem;opacity:.65}}
.card-body{{padding:18px}}
.card-title{{font-size:1rem;line-height:1.7;color:var(--ink);margin-bottom:16px;min-height:2.8em}}
.card-links{{display:flex;gap:8px;flex-wrap:wrap}}
.card-link{{display:inline-flex;align-items:center;gap:7px;font-size:.9rem;letter-spacing:.06em;padding:11px 18px;border-radius:6px;text-decoration:none;transition:all .2s;font-family:'Noto Serif TC',serif;width:100%;justify-content:center}}
.card-link svg{{width:16px;height:16px;flex-shrink:0}}
.link-google{{background:rgba(66,133,244,.1);color:#1a56b0;border:1px solid rgba(66,133,244,.3)}}
.link-google:hover{{background:rgba(66,133,244,.2);border-color:rgba(66,133,244,.55)}}
.no-link{{font-size:.88rem;color:var(--muted);font-style:italic;padding:5px 0;letter-spacing:.04em}}

/* ── Footer ── */
footer{{text-align:center;padding:36px 20px;font-size:.7rem;letter-spacing:.16em;color:var(--muted);border-top:1px solid rgba(184,154,106,.25)}}

@media(max-width:580px){{
  .filter-btn{{font-size:.82rem;padding:11px 14px}}
  .trip-year{{font-size:2rem}}
  .albums-grid{{grid-template-columns:1fr}}
  .stats{{gap:28px}}
  .ornament::before,.ornament::after{{flex:0 0 40px}}
  .card-title{{font-size:1.05rem}}
  .card-link{{font-size:.95rem;padding:14px 18px}}
}}
</style>
</head>
<body>

<header>
  <span class="header-eyebrow">Family Travel Archive</span>
  <h1>家族旅行相簿</h1>
  <p class="header-sub">施家出遊記錄　2020 — 2026</p>
  <div class="ornament">✦</div>
</header>

<div class="stats">
  <div class="stat"><span class="stat-n">{total_trips}</span><span class="stat-l">次旅程</span></div>
  <div class="stat"><span class="stat-n">{total_days}</span><span class="stat-l">天記錄</span></div>
  <div class="stat"><span class="stat-n">{has_link_count}</span><span class="stat-l">個相簿連結</span></div>
</div>

<div class="filter-bar">
  {''.join(filter_buttons)}
</div>

<main>
{all_sections}
</main>

<footer>
  資料來源：Notion 相簿資料庫　·　標籤：家族旅行　·　最後更新：{now}
</footer>

<script>
const btns = document.querySelectorAll('.filter-btn');
const sections = document.querySelectorAll('.trip-section');
btns.forEach(btn => {{
  btn.addEventListener('click', () => {{
    btns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const f = btn.dataset.filter;
    sections.forEach(s => {{
      s.classList.toggle('hidden', f !== 'all' && s.dataset.trip !== f);
    }});
  }});
}});
</script>
</body>
</html>"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ 生成 index.html（{total_trips} 旅程，{total_days} 筆）")

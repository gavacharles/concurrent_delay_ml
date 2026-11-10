"""Build the public site: one page joining the Concurrent Delay Explorer and the case-law timeline.

Sources (single source of truth):
  explorer/concurrent_delay_explorer.html     interactive rules explorer
  explorer/law_timeline_template.html         case-law timeline (+ docs/law_timeline.json)
Output:
  site/dist/index.html                        static page for GitHub Pages (no confidential material)

Run: python site/build_site.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "site" / "dist"
REPO_URL = "https://github.com/gavacharles/concurrent-delay-map"
SITE_URL = "https://gavacharles.github.io/concurrent-delay-map/"

# Credit shown on every view, in the citation and in the page metadata.
AUTHOR = "Charles Gava"
AUTHOR_LINKS = [("GitHub", "https://github.com/gavacharles")]   # add ("LinkedIn", url), ("Substack", url)
YEAR = 2026
CITATION = (f"Gava, C. ({YEAR}) Concurrent Delay Map: seven legal rules on one programme, and the case law "
            f"since 1999 [interactive]. Available at: {SITE_URL}")


def parts(html: str):
    style = re.search(r"<style>(.*?)</style>", html, re.S).group(1)
    script = re.search(r"<script>(.*?)</script>", html, re.S).group(1)
    body = html[html.index("</style>") + len("</style>"): html.index("<script>")]
    return style, body.strip(), script


def main():
    ex_style, ex_body, ex_js = parts((ROOT / "explorer" / "concurrent_delay_explorer.html").read_text())
    tl_html = (ROOT / "explorer" / "law_timeline_template.html").read_text()
    law = json.dumps(json.load(open(ROOT / "docs" / "law_timeline.json")), ensure_ascii=False)
    tl_style, tl_body, tl_js = parts(tl_html.replace("/*DATA*/[]", law))

    # avoid class/id clashes between the two pages
    for a, b in ((".legend", ".tl-legend"), (".dot", ".tl-dot")):
        tl_style = tl_style.replace(a, b)
    tl_body = tl_body.replace('class="legend" id="legend"', 'class="tl-legend" id="tlLegend"')
    tl_js = (tl_js.replace('$("legend")', '$("tlLegend")').replace('class="dot"', 'class="tl-dot"')
             .replace('querySelectorAll(".dot")', 'querySelectorAll(".tl-dot")')
             .replace('document.querySelectorAll(".chip")', 'document.querySelectorAll("#view-caselaw .chip")'))
    ex_js = ex_js.replace('document.querySelectorAll(".chip")', 'document.querySelectorAll("#view-explorer .chip")')
    tl_body = re.sub(r'<a href="https://claude\.ai/artifact/[^"]+"[^>]*>Concurrent Delay Explorer</a>',
                     '<a href="#explorer">Concurrent Delay Explorer</a>', tl_body)
    assert "claude.ai" not in tl_body + ex_body, "private links left in the public page"

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Concurrent Delay Map</title>
<meta name="description" content="Interactive map of concurrent delay in construction: how English, Scottish, SCL Protocol, FIDIC and NEC4 approaches allocate time and money, and how the case law evolved since 1999.">
<meta property="og:title" content="Concurrent Delay Map">
<meta property="og:description" content="Same delays, different law. Move the delays and watch seven legal rules respond, then trace 25 years of case law.">
<meta property="og:type" content="website">
<meta name="author" content="{AUTHOR}">
<meta property="og:url" content="{SITE_URL}">
<meta property="og:site_name" content="Concurrent Delay Map by {AUTHOR}">
<meta name="twitter:card" content="summary">
<link rel="author" href="{AUTHOR_LINKS[0][1]}">
<script type="application/ld+json">{json.dumps({"@context": "https://schema.org", "@type": "WebApplication",
  "name": "Concurrent Delay Map", "url": SITE_URL, "applicationCategory": "EducationalApplication",
  "author": {"@type": "Person", "name": AUTHOR, "url": AUTHOR_LINKS[0][1]},
  "copyrightHolder": {"@type": "Person", "name": AUTHOR}, "copyrightYear": YEAR,
  "description": "Interactive map of concurrent delay in construction law."})}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;800&family=Spline+Sans+Mono:wght@400;500&display=swap">
<style>
html {{ -webkit-text-size-adjust: 100%; }}
body {{ margin: 0; }}
[hidden] {{ display: none !important; }}
{ex_style}
/* ---- case-law view ---- */
{tl_style}
/* ---- site header ---- */
.site {{ position: sticky; top: 0; z-index: 20; background: var(--sheet); border-bottom: 1px solid var(--rule); }}
.site .in {{ max-width: 1120px; margin: 0 auto; display: flex; flex-wrap: wrap; align-items: center; gap: 10px 22px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  padding-block: 10px; }}
.brand {{ font-family: var(--f-display); font-weight: 800; font-size: 16px; letter-spacing: -0.01em; color: var(--ink);
  text-decoration: none; }}
.tabs {{ display: flex; gap: 4px; flex-wrap: wrap; }}
.tabs a {{ font: 600 14px var(--f-display); color: var(--muted); text-decoration: none; padding: 7px 12px; border-radius: 5px; }}
.tabs a[aria-current="page"] {{ background: var(--ink); color: var(--paper); }}
.tabs a:focus-visible {{ outline: 2px solid var(--focus); outline-offset: 2px; }}
.site .gh {{ margin-left: auto; font: 500 13px var(--f-data); color: var(--muted); }}
.byline {{ font: 500 13px var(--f-display); color: var(--muted); }}
.byline a {{ color: var(--ink); text-decoration: none; border-bottom: 1px solid var(--rule); }}
.credits {{ border-top: 1px solid var(--rule); background: var(--sheet); }}
.credits .in {{ max-width: 1120px; margin: 0 auto; display: grid; gap: 12px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  padding-block: 24px 32px; }}
.credits .who {{ font: 700 16px var(--f-display); }}
.credits .who a {{ color: var(--ink); }}
.credits .links {{ display: flex; flex-wrap: wrap; gap: 6px 16px; font: 500 13px var(--f-data); }}
.credits .links a {{ color: var(--focus); }}
.citebox {{ display: grid; gap: 6px; max-width: 80ch; }}
.citebox .lab {{ font: 500 11.5px var(--f-data); letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); }}
.citebox .row2 {{ display: flex; gap: 10px; align-items: flex-start; flex-wrap: wrap; }}
.citebox code {{ font: 400 13px var(--f-data); color: var(--ink); background: var(--paper); border: 1px solid var(--rule);
  border-radius: 4px; padding: 8px 10px; flex: 1 1 320px; min-width: 0; overflow-wrap: anywhere; user-select: all; }}
.citebox button {{ font: 600 13px var(--f-display); color: var(--paper); background: var(--ink); border: 0; border-radius: 4px;
  padding: 8px 14px; cursor: pointer; }}
.citebox button:focus-visible {{ outline: 2px solid var(--focus); outline-offset: 2px; }}
.credits small {{ color: var(--muted); font-size: 12.5px; }}
</style>
</head>
<body>
<header class="site">
  <div class="in">
    <a class="brand" href="#explorer">Concurrent Delay Map</a>
    <nav class="tabs" aria-label="Views">
      <a href="#explorer" data-view="explorer">Explorer</a>
      <a href="#case-law" data-view="caselaw">Case law, 1999–2024</a>
    </nav>
    <span class="byline">by <a href="{AUTHOR_LINKS[0][1]}" target="_blank" rel="noopener author">{AUTHOR}</a></span>
    <a class="gh" href="{REPO_URL}" target="_blank" rel="noopener">Source</a>
  </div>
</header>
<main>
<section id="view-explorer" aria-label="Concurrent delay explorer">
{ex_body}
</section>
<section id="view-caselaw" aria-label="Case-law timeline" hidden>
{tl_body}
</section>
</main>
<footer class="credits" aria-label="Credits">
  <div class="in">
    <div class="who">Created by <a href="{AUTHOR_LINKS[0][1]}" target="_blank" rel="noopener author">{AUTHOR}</a></div>
    <p>Research, legal analysis, causal model and design for <i>One Schedule, Many Laws: doctrine-conditioned causal attribution and explainable AI for concurrent delay</i>.</p>
    <div class="links">{"".join(f'<a href="{u}" target="_blank" rel="noopener">{n}</a>' for n, u in AUTHOR_LINKS)}<a href="{REPO_URL}" target="_blank" rel="noopener">Source code</a></div>
    <div class="citebox">
      <span class="lab">Cite this map</span>
      <div class="row2"><code id="citeText">{CITATION}</code><button type="button" id="citeBtn">Copy citation</button></div>
    </div>
    <small>© {YEAR} {AUTHOR}. Research material, not legal advice. Please credit {AUTHOR} when sharing or reusing.</small>
  </div>
</footer>
<script>
(function () {{
{ex_js}
window.__renderExplorer = () => render();
}})();
</script>
<script>
(function () {{
{tl_js}
}})();
</script>
<script>
(function () {{
  const views = {{ explorer: "view-explorer", caselaw: "view-caselaw" }};
  function show() {{
    const v = location.hash === "#case-law" ? "caselaw" : "explorer";
    for (const [k, id] of Object.entries(views)) document.getElementById(id).hidden = k !== v;
    document.querySelectorAll(".tabs a").forEach((a) => a.toggleAttribute("aria-current", a.dataset.view === v));
    document.querySelectorAll(".tabs a").forEach((a) => {{ if (a.dataset.view === v) a.setAttribute("aria-current", "page"); }});
    if (v === "explorer" && window.__renderExplorer) window.__renderExplorer();
    window.scrollTo(0, 0);
  }}
  window.addEventListener("hashchange", show);
  show();
  const btn = document.getElementById("citeBtn"), txt = document.getElementById("citeText");
  btn.addEventListener("click", () => {{
    const done = () => {{ btn.textContent = "Copied"; setTimeout(() => (btn.textContent = "Copy citation"), 1800); }};
    const select = () => {{ const r = document.createRange(); r.selectNodeContents(txt);
      const s = getSelection(); s.removeAllRanges(); s.addRange(r); btn.textContent = "Selected: press Ctrl/Cmd+C"; }};
    if (navigator.clipboard) navigator.clipboard.writeText(txt.textContent).then(done, select); else select();
  }});
}})();
</script>
</body>
</html>
"""
    DIST.mkdir(parents=True, exist_ok=True)
    (DIST / "index.html").write_text(page)
    (DIST / ".nojekyll").write_text("")
    print("wrote", DIST / "index.html", f"({len(page) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""/search/: site search page using Pagefind (open source, runs in the browser, no server).

The index is built at publish time by the Cloudflare build command:
  python3 scripts/build_public.py && npx -y pagefind --site dist
Pagefind writes /pagefind/ into dist/. This page is noindex and excluded from its own index.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_furnace_pages import shell  # noqa: E402

PATH = "/search/"

BODY = """<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li aria-current="page">Search</li></ol></nav>
<header class="hero"><div class="wrap"><h1>Search HomePowerRebate</h1>
<p>Find your city, a rebate, an installer or a guide. Try "heat pump Ottawa", "attic insulation" or "BC Hydro".</p></div></header>
<section class="body"><div class="wrap">
<link href="/pagefind/pagefind-ui.css" rel="stylesheet">
<div id="hpr-search"></div>
<noscript><p>Search needs JavaScript. You can browse <a href="/">all cities</a>, the <a href="/blog/">blog</a> or the <a href="/rebate-tracker/">rebate tracker</a>.</p></noscript>
<p class="small" style="margin-top:22px;">Popular: <a href="/insulation-rebates/">insulation rebates</a> · <a href="/rebate-tracker/">rebate tracker</a> · <a href="/installers/">top-rated installers</a> · <a href="/smart-thermostats/">smart thermostat rebates</a></p>
</div></section>
<style>
#hpr-search{--pagefind-ui-primary:#0d4f5c;--pagefind-ui-text:#0a2a2e;--pagefind-ui-background:#fff;--pagefind-ui-border:#d9d0c1;--pagefind-ui-border-width:1px;--pagefind-ui-border-radius:10px;--pagefind-ui-font:'Inter Tight',system-ui,sans-serif;--pagefind-ui-scale:1.05;margin-top:8px;}
#hpr-search .pagefind-ui__result-link{color:#0d4f5c;}
</style>
<script src="/pagefind/pagefind-ui.js"></script>
<script>
window.addEventListener('DOMContentLoaded',function(){
  if(!window.PagefindUI){document.getElementById('hpr-search').innerHTML='<p>Search is loading. If nothing appears, try again in a minute or browse the <a href="/">home page</a>.</p>';return;}
  var ui=new PagefindUI({element:'#hpr-search',showSubResults:false,showImages:false,autofocus:true,resetStyles:false,
    translations:{placeholder:'Search rebates, cities, installers',zero_results:'No results for [SEARCHTERM]. Try a city name or "heat pump".'}});
  var q=new URLSearchParams(location.search).get('q');
  if(q){ui.triggerSearch(q);}
});
</script>"""


def main():
    out = shell("Search | HomePowerRebate", "Search HomePowerRebate for rebates, cities, installers and guides.", PATH, "bc", BODY, [])
    out = out.replace('<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">',
                      '<meta name="robots" content="noindex, follow">', 1)
    out = out.replace("<body", '<body data-pagefind-ignore="all"', 1)
    f = ROOT / "search" / "index.html"
    f.parent.mkdir(exist_ok=True)
    f.write_text(out, encoding="utf-8")
    print("Wrote", PATH)


if __name__ == "__main__":
    main()

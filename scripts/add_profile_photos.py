#!/usr/bin/env python3
"""Installer profiles: a photo block that shows the company's Google photo at view time, over an initials tile.

Google's Places policies forbid storing Places photos (only place IDs may be stored), so pages never contain a photo
URL. Each profile gets, inside PROFILE-PHOTO markers where the old <img class="ip-photo"> sat:
  - an initials tile with an icon for what the company installs (always shown; it is what visitors see without a photo)
  - if data/installer-place-ids.json has the page's place ID and data/profile-photos/config.json has a worker_url:
    a small script that, when the block scrolls into view, asks photo-worker/ for the photo and shows it with the
    required credits (author with link, link to the photo on Google Maps, Google logo).
Also removes old Google or rehosted photo URLs from the page's <img> and JSON-LD "image". Re-run after
generate_installer_profiles.py, lookup_installer_place_ids.py or a config change. Usage: python3 scripts/add_profile_photos.py
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOCK_RE = re.compile(r"<!-- PROFILE-PHOTO-START -->.*?<!-- PROFILE-PHOTO-END -->\n*", re.S)
OLD_IMG_RE = re.compile(r'[ \t]*<img [^>]*class="ip-photo"[^>]*>\n?')
LD_IMAGE_RE = re.compile(r'("image":\s*)"(?:https://lh3\.googleusercontent\.com/[^"]*|https://homepowerrebate\.com/installers/photos/[^"]*|)"')
ANCHOR = '  <p class="ip-intro">'
STOP = {"the", "and", "of", "inc", "inc.", "ltd", "ltd.", "llc", "co", "co.", "corp", "&", "-", "|", "a"}

ICONS = {
    "solar": '<path d="M12 3v2M12 19v2M4.2 7.2l1.4 1.4M18.4 15.4l1.4 1.4M3 12h2M19 12h2M4.2 16.8l1.4-1.4M18.4 8.6l1.4-1.4"/><circle cx="12" cy="12" r="4"/>',
    "battery": '<rect x="3" y="7" width="16" height="10" rx="2"/><path d="M21 10v4M11 9l-2 4h4l-2 4"/>',
    "insulation": '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/><path d="M8 14c1.3-1.3 2.7 1.3 4 0s2.7 1.3 4 0"/>',
    "heat-pump": '<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="10" cy="12" r="3.5"/><path d="M10 8.5v7M6.5 12h7M16 9h2M16 12h2M16 15h2"/>',
}
LABEL = {"solar": "Solar", "battery": "Home batteries", "insulation": "Insulation", "heat-pump": "Heat pumps"}


def config():
    p = ROOT / "data" / "profile-photos" / "config.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def place_ids():
    p = ROOT / "data" / "installer-place-ids.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def initials(name):
    words = [w for w in re.split(r"[\s/]+", re.sub(r"[^\w\s&/-]", "", html.unescape(name))) if w and w.lower() not in STOP]
    return "".join(w[0] for w in words[:2]).upper() or "?"


def service(meta):
    m = meta.lower()
    for key, words in (("solar", ("solar",)), ("battery", ("batter",)), ("insulation", ("insulation", "spray foam", "attic"))):
        if any(w in m for w in words):
            return key
    return "heat-pump"


SCRIPT = """<script>(function(){var f=document.currentScript.previousElementSibling;if(!f||!('IntersectionObserver' in window))return;
var io=new IntersectionObserver(function(es){if(!es[0].isIntersecting)return;io.disconnect();
fetch(%(worker)s+'/photo?id='+encodeURIComponent(f.dataset.place)+'&w=900').then(function(r){return r.json()}).then(function(d){if(!d||!d.src)return;
var i=new Image();i.alt=f.dataset.name;i.className='ipf-img';i.decoding='async';i.referrerPolicy='no-referrer';
i.onload=function(){f.insertBefore(i,f.firstChild);f.classList.add('has-photo');var c=f.querySelector('.ipf-cap'),h='';
var e=function(t){var x=document.createElement('span');x.textContent=t;return x.innerHTML};
if(d.author)h+='Photo: '+(d.authorUri?'<a href="'+e(d.authorUri)+'" target="_blank" rel="noopener nofollow">'+e(d.author)+'</a>':e(d.author));
if(d.mapsUri)h+=(h?' &middot; ':'')+'<a href="'+e(d.mapsUri)+'" target="_blank" rel="noopener nofollow">View on Google Maps</a>';
h+=%(logo)s;c.innerHTML=h;c.hidden=false};i.src=d.src}).catch(function(){})},{rootMargin:'300px'});io.observe(f)})();</script>"""


def block(name, meta, place, cfg):
    svc = service(meta)
    worker = (cfg.get("worker_url") or "").rstrip("/")
    live = bool(worker and place)
    data = f' data-place="{html.escape(place)}" data-name="{html.escape(html.unescape(name))}"' if live else ""
    icon = f'<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{ICONS[svc]}</svg>'
    out = (f'<!-- PROFILE-PHOTO-START -->\n  <figure class="ipf"{data}><div class="ipf-tile" aria-hidden="true">'
           f'<span class="ipf-init">{html.escape(initials(name))}</span><span class="ipf-svc">{icon}{LABEL[svc]}</span></div>'
           f'<figcaption class="ipf-cap" hidden></figcaption></figure>')
    if live:
        logo = cfg.get("google_logo") or ""
        logo_js = (repr(f' <img class="ipf-g" src="{logo}" alt="Google Maps" width="98" height="18" translate="no">') if logo
                   else repr(' <span class="ipf-gt" translate="no">Google Maps</span>'))
        out += SCRIPT % {"worker": json.dumps(worker), "logo": logo_js}
    return out + "\n<!-- PROFILE-PHOTO-END -->\n"


def apply(s, rel, ids=None, cfg=None):
    ids = place_ids() if ids is None else ids
    cfg = config() if cfg is None else cfg
    s = BLOCK_RE.sub("", s)
    s = OLD_IMG_RE.sub("", s)
    s = LD_IMAGE_RE.sub(r'\1"https://homepowerrebate.com/og-image.jpg"', s)
    h1 = re.search(r"<h1>(.*?)</h1>", s, re.S)
    meta = re.search(r'<p class="ip-hero-meta">(.*?)</p>', s, re.S)
    if not h1 or ANCHOR not in s:
        return s
    name = re.sub(r"<[^>]+>", "", h1.group(1)).strip()
    return s.replace(ANCHOR, block(name, meta.group(1) if meta else "", ids.get(rel, ""), cfg) + "\n" + ANCHOR, 1)


def main():
    ids, cfg = place_ids(), config()
    changed = live = 0
    pages = sorted((ROOT / "installers" / "profiles").rglob("index.html"))
    for p in pages:
        rel = str(p.relative_to(ROOT))
        s = p.read_text(encoding="utf-8")
        out = apply(s, rel, ids, cfg)
        live += 'data-place="' in out
        if out != s:
            p.write_text(out, encoding="utf-8")
            changed += 1
    print(f"{len(pages)} profiles, {changed} changed, {live} load a Google photo"
          + ("" if cfg.get("worker_url") else " (no worker_url in data/profile-photos/config.json yet: tiles only)"))


if __name__ == "__main__":
    main()

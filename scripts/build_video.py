#!/usr/bin/env python3
"""Short explainer videos from verified facts, 2026-10-23: vertical 1080 x 1920, captions only (no voice), about 40 seconds, the answer in the first
seconds, the source and the checked date on the last scene. Every number comes from the fact the video names (data/verified-facts/*.json), never typed
into the script, so a video can't say something the page doesn't. Scenes are drawn with the site's fonts and colours (_partials/video-scene.html, headless
Chrome via scripts/video/render.js) and joined with ffmpeg (fades and a slow zoom).
Usage: python3 scripts/build_video.py ns-harp-status [--keep]    -> videos/ns-harp-status.mp4 (not published; upload to YouTube by hand, then embed on the page)
Add a video: write a function below that returns scenes from a fact, register it in VIDEOS. Never state an amount or date that is not in the fact."""
import json
import re
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import page_kit as kit  # noqa: E402

SCENE_SECONDS = 5.0   # default length of a scene; a scene can set "seconds"
FADE = 0.45


def nice(iso):
    d = date.fromisoformat(iso)
    return d.strftime("%B %-d, %Y")


def ns_harp_status():
    f = kit.FACTS["ns-16-heating-assistance-rebate-program-harp-province-of"]
    amount = re.search(r"\$[\d,]+", f["amount"]).group(0)
    end = nice(f["dates"].split(" to ")[-1].strip())
    start = nice(re.search(r"\d{4}-\d{2}-\d{2}", f["dates"]).group(0))
    claim = f["claim"]
    assert "online applicants only" in claim and "confirmation number" in claim and "postal code" in claim and "about 8 weeks" in claim, "fact changed: re-read it before rendering"
    host = urlparse(f["source_url"]).netloc.replace("www.", "")
    foot = f"Source: {host}. Checked {nice(f['verified_on'])}."
    return [
        dict(theme="dark", kicker="Nova Scotia heating rebate", headline=f"How to check your <em>status</em>", sub=f"The 2026-27 rebate is {amount} per household."),
        dict(theme="light", kicker="Step 1", headline="Open the province's <em>status page</em>", sub="It only works if you applied online."),
        dict(theme="light", kicker="Step 2", headline="Enter <em>two things</em>", sub="Your application confirmation number and your postal code."),
        dict(theme="light", kicker="Step 3", headline="Read what it says", sub="The page shows whether your application was received or approved."),
        dict(theme="dark", kicker="Mailed a paper form?", headline="The online tool <em>won't</em> work", sub="Contact the program through its official page instead."),
        dict(theme="light", kicker="How long does it take?", headline="About <em>8 weeks</em>", sub="Longer if the province needs more information."),
        dict(theme="light", kicker="Deadline", headline=f"Apply by <em>{end}</em>", sub=f"Applications opened {start}. Paper forms must be postmarked by that day."),
        dict(theme="dark", kicker="Full guide and payment dates", headline="homepowerrebate<em>.com</em>", size=86, sub="Search: Nova Scotia heating rebate status", foot=foot),
    ]


# ---- bento cards + sticker type + kinetic motion (frame by frame, 30 fps) -----------------------------------------------------------------------
VANITY = "homepowerrebate.com/harp"   # short URL: _redirects sends it to the HARP page with utm_source=video
CREAM, TEAL, AMBER, TAN = "#faf7f2", "#08363f", "#d4751c", "#ffe8c2"


def ns_harp_status_6():
    """6 seconds. Hook in the first 2 seconds, then the one thing to know, then where to look. Conversational, grade 6. The status tool is the PROVINCE's:
    we never say people can check on our site, only that we show where."""
    f = kit.FACTS["ns-16-heating-assistance-rebate-program-harp-province-of"]
    amount = re.search(r"\$[\d,]+", f["amount"]).group(0)
    claim = f["claim"]
    assert "online applicants only" in claim and "confirmation number" in claim and "postal code" in claim, "fact changed: re-read it before rendering"
    host = urlparse(f["source_url"]).netloc.replace("www.", "")
    return {"scenes": [
        {"at": 0.0, "end": 2.0, "theme": "dark", "items": [
            {"type": "tile", "x": 60, "y": 360, "w": 960, "h": 600, "bg": CREAM, "color": TEAL, "size": 150, "words": True, "html": f"Still waiting on your <em>{amount}</em>?", "rot": -1.5},
            {"type": "emoji", "x": 770, "y": 210, "size": 230, "html": "\U0001F440", "rot": 12, "delay": 0.45},
            {"type": "sticker", "x": 90, "y": 1030, "size": 50, "style": "cream", "html": "Nova Scotia heating rebate", "rot": -4, "delay": 0.7}]},
        {"at": 2.0, "end": 4.2, "theme": "light", "items": [
            {"type": "tile", "x": 60, "y": 270, "w": 960, "h": 470, "bg": TEAL, "color": CREAM, "size": 112, "words": True, "html": "The <em>province</em> has a status tool \U0001F50E", "rot": -1},
            {"type": "tile", "x": 60, "y": 780, "w": 468, "h": 400, "bg": AMBER, "color": "#fff", "font": "sans", "size": 62, "center": True, "html": "Your confirmation number", "rot": 1.5, "delay": 0.5},
            {"type": "tile", "x": 552, "y": 780, "w": 468, "h": 400, "bg": TAN, "color": "#7a4a00", "font": "sans", "size": 62, "center": True, "html": "Your postal code", "rot": -1.5, "delay": 0.7},
            {"type": "sticker", "x": 230, "y": 1240, "size": 42, "style": "teal", "html": "online applicants only", "rot": -3, "delay": 1.0}]},
        {"at": 4.2, "end": 6.0, "theme": "dark", "foot": f"Source: {host}. Checked {nice(f['verified_on'])}.", "items": [
            {"type": "tile", "x": 60, "y": 330, "w": 960, "h": 450, "bg": CREAM, "color": TEAL, "size": 128, "words": True, "html": "We'll show you <em>where</em> \U0001F447", "rot": 1},
            {"type": "tile", "x": 60, "y": 830, "w": 960, "h": 260, "bg": AMBER, "color": "#fff", "font": "sans", "size": 62, "center": True, "html": VANITY, "rot": -1, "delay": 0.45},
            {"type": "sticker", "x": 110, "y": 1150, "size": 40, "style": "cream", "html": "or search: NS heating rebate status", "rot": 3, "delay": 0.8}]},
    ]}


def _harp():
    """The HARP fact, checked, plus the bits every cut needs."""
    f = kit.FACTS["ns-16-heating-assistance-rebate-program-harp-province-of"]
    claim = f["claim"]
    for must in ("online applicants only", "confirmation number", "postal code", "about 8 weeks", "direct deposit", "postmarked"):
        assert must in claim, f"fact changed ({must}): re-read it before rendering"
    return {"amount": re.search(r"\$[\d,]+", f["amount"]).group(0), "end": nice(f["dates"].split(" to ")[-1].strip()),
            "start": nice(re.search(r"\d{4}-\d{2}-\d{2}", f["dates"]).group(0)),
            "foot": f"Source: {urlparse(f['source_url']).netloc.replace('www.', '')}. Checked {nice(f['verified_on'])}."}


def tile(x, y, w, h, bg, color, size, **kw):
    return {"type": "tile", "x": x, "y": y, "w": w, "h": h, "bg": bg, "color": color, "size": size, **kw}


def sticker(x, y, html, style="cream", size=44, rot=-3, delay=0.8):
    return {"type": "sticker", "x": x, "y": y, "html": html, "style": style, "size": size, "rot": rot, "delay": delay}


def emoji(x, y, ch, size=220, rot=10, delay=0.45):
    return {"type": "emoji", "x": x, "y": y, "html": ch, "size": size, "rot": rot, "delay": delay}


def ns_harp_status_15():
    """15 seconds: hook, the status tool, the two things, how long, where to look."""
    h = _harp(); a = h["amount"]
    return {"scenes": [
        {"at": 0.0, "end": 2.5, "theme": "dark", "items": [
            tile(60, 360, 960, 600, CREAM, TEAL, 150, words=True, html=f"Still waiting on your <em>{a}</em>?", rot=-1.5), emoji(770, 210, "\U0001F440", 230, 12),
            sticker(90, 1030, "Nova Scotia heating rebate", size=50, rot=-4)]},
        {"at": 2.5, "end": 5.5, "theme": "light", "items": [
            tile(60, 300, 960, 560, TEAL, CREAM, 120, words=True, html="Good news: the <em>province</em> has a status tool \U0001F50E", rot=-1),
            sticker(190, 930, "online applicants only", "teal", 46, -3, 0.9)]},
        {"at": 5.5, "end": 8.5, "theme": "light", "items": [
            tile(60, 250, 960, 300, "#ffffff", TEAL, 100, words=True, html="You just need <em>2 things</em>"),
            tile(60, 600, 468, 460, AMBER, "#fff", 66, font="sans", center=True, html="Your confirmation number", rot=1.5, delay=0.5),
            tile(552, 600, 468, 460, TAN, "#7a4a00", 66, font="sans", center=True, html="Your postal code", rot=-1.5, delay=0.7),
            sticker(300, 1120, "that's it!", "teal", 46, -4, 1.0)]},
        {"at": 8.5, "end": 11.5, "theme": "dark", "items": [
            tile(60, 280, 960, 420, CREAM, TEAL, 120, words=True, html="How long? About <em>8 weeks</em> \u23F3", rot=1),
            tile(60, 750, 960, 280, AMBER, "#fff", 62, font="sans", center=True, html="Longer if they need more info", rot=-1, delay=0.6)]},
        {"at": 11.5, "end": 15.0, "theme": "dark", "foot": h["foot"], "items": [
            tile(60, 330, 960, 450, CREAM, TEAL, 128, words=True, html="We'll show you <em>where</em> \U0001F447", rot=1),
            tile(60, 830, 960, 260, AMBER, "#fff", 62, font="sans", center=True, html=VANITY, rot=-1, delay=0.5),
            sticker(110, 1150, "or search: NS heating rebate status", "cream", 40, 3, 0.9)]},
    ]}


def ns_harp_status_30():
    """30 seconds: the same story with the money, the paper-form catch, how you get paid and the deadline."""
    h = _harp(); a = h["amount"]
    return {"scenes": [
        {"at": 0.0, "end": 2.5, "theme": "dark", "items": [
            tile(60, 360, 960, 600, CREAM, TEAL, 150, words=True, html=f"Still waiting on your <em>{a}</em>?", rot=-1.5), emoji(770, 210, "\U0001F440", 230, 12),
            sticker(90, 1030, "Nova Scotia heating rebate", size=50, rot=-4)]},
        {"at": 2.5, "end": 5.5, "theme": "light", "items": [
            tile(60, 280, 960, 520, TEAL, CREAM, 118, words=True, html=f"It's <em>{a}</em> per home to help with winter heat", rot=-1),
            sticker(150, 880, "2026-27 season", "cream", 48, 3, 0.9)]},
        {"at": 5.5, "end": 9.0, "theme": "light", "items": [
            tile(60, 300, 960, 560, AMBER, "#fff", 118, words=True, html="Applied online? The <em>province</em> has a status tool \U0001F50E", rot=1),
            sticker(190, 930, "online applicants only", "teal", 46, -3, 1.0)]},
        {"at": 9.0, "end": 12.5, "theme": "dark", "items": [
            tile(60, 250, 960, 300, CREAM, TEAL, 100, words=True, html="Have <em>2 things</em> ready"),
            tile(60, 600, 468, 460, AMBER, "#fff", 66, font="sans", center=True, html="Your confirmation number", rot=1.5, delay=0.5),
            tile(552, 600, 468, 460, TAN, "#7a4a00", 66, font="sans", center=True, html="Your postal code", rot=-1.5, delay=0.7)]},
        {"at": 12.5, "end": 16.0, "theme": "light", "items": [
            tile(60, 280, 960, 520, TEAL, CREAM, 118, words=True, html="Mailed a paper form? \U0001F4EC The online tool <em>won't work</em>", rot=-1),
            sticker(190, 880, "ask the program instead", "cream", 46, 3, 1.0)]},
        {"at": 16.0, "end": 19.5, "theme": "dark", "items": [
            tile(60, 280, 960, 440, CREAM, TEAL, 128, words=True, html="How long? About <em>8 weeks</em> \u23F3", rot=1),
            tile(60, 770, 960, 260, AMBER, "#fff", 62, font="sans", center=True, html="Longer if they need more info", rot=-1, delay=0.6)]},
        {"at": 19.5, "end": 23.0, "theme": "light", "items": [
            tile(60, 250, 960, 330, "#ffffff", TEAL, 104, words=True, html="How do you <em>get paid</em>? \U0001F4B8"),
            tile(60, 640, 468, 440, AMBER, "#fff", 50, font="sans", center=True, html="Direct deposit, if your tax refund comes that way", rot=1.5, delay=0.5),
            tile(552, 640, 468, 440, TAN, "#7a4a00", 50, font="sans", center=True, html="Otherwise it comes by mail \u2709\uFE0F", rot=-1.5, delay=0.7)]},
        {"at": 23.0, "end": 26.5, "theme": "dark", "items": [
            tile(60, 280, 960, 440, CREAM, TEAL, 130, words=True, html=f"Apply by <em>{h['end']}</em> \u23F0", rot=-1),
            tile(60, 770, 960, 260, AMBER, "#fff", 56, font="sans", center=True, html="Paper forms must be postmarked by then", rot=1, delay=0.6)]},
        {"at": 26.5, "end": 30.0, "theme": "dark", "foot": h["foot"], "items": [
            tile(60, 330, 960, 450, CREAM, TEAL, 128, words=True, html="We'll show you <em>where</em> \U0001F447", rot=1),
            tile(60, 830, 960, 260, AMBER, "#fff", 62, font="sans", center=True, html=VANITY, rot=-1, delay=0.5),
            sticker(110, 1150, "or search: NS heating rebate status", "cream", 40, 3, 0.9)]},
    ]}


# ---- heat pump series, 2026-10-23: teach one idea, then send people to the launch alert (/federal) ---------------------------------------------------
FED_VANITY = "homepowerrebate.com/federal"


def _fed():
    """The federal facts the heat pump videos use, checked. Nothing about who qualifies or a start date beyond what the facts say; the November 1, 2026 retroactivity start is in federal-1."""
    f0 = kit.FACTS["federal-0-national-heat-pump-rebate"]
    f1 = kit.FACTS["federal-1-launch-and-retroactivity"]
    f2 = kit.FACTS["federal-2-how-it-works"]
    assert "$10,000" in f0["amount"] and "$2,000" in f0["amount"], "federal amounts changed: re-read before rendering"
    assert "$1,400" in f0["eligibility"] and "not published" in f0["eligibility"], "federal eligibility changed: re-read before rendering"
    assert "early 2027" in f0["dates"] and "early 2027" in f1["dates"], "federal launch wording changed: re-read before rendering"
    assert "24 hours" in f2["claim"] and "five days" in f2["claim"] and "80 per cent" in f2["eligibility"], "federal process changed: re-read before rendering"
    assert "November 1, 2026" in f1["claim"], "federal retroactivity wording changed: re-read before rendering"
    assert f0["status"] == "upcoming", "the rebate is no longer 'upcoming': rewrite the videos"
    return {"foot": f"Source: canada.ca. Checked {nice(f0['verified_on'])}."}


def _fed_cta(at, end, foot, line="Want to hear <em>first</em>? \U0001F4EC"):
    return {"at": at, "end": end, "theme": "dark", "foot": foot, "items": [
        tile(60, 300, 960, 460, CREAM, TEAL, 128, words=True, html=line, rot=1),
        tile(60, 810, 960, 250, AMBER, "#fff", 62, font="sans", center=True, html=FED_VANITY, rot=-1, delay=0.5),
        sticker(110, 1120, "one email the day it opens", "cream", 42, 3, 0.9)]}


def hp_furnace_15():
    """15 seconds. Hook: the furnace will die. Teaches: most people replace heat only after it breaks, and Ottawa's rebate is built for that moment."""
    h = _fed()
    return {"scenes": [
        {"at": 0.0, "end": 2.5, "theme": "dark", "items": [
            tile(60, 330, 960, 640, CREAM, TEAL, 140, words=True, html="Your furnace <em>will die</em>. Probably in the cold.", rot=-1.5), emoji(760, 170, "\U0001F976", 240, 12),
            sticker(90, 1040, "Heat pump news from Ottawa", size=48, rot=-4)]},
        {"at": 2.5, "end": 6.0, "theme": "light", "items": [
            tile(60, 280, 960, 520, TEAL, CREAM, 118, words=True, html="Most people replace heat <em>after</em> it breaks \U0001F4A5", rot=-1),
            tile(60, 850, 960, 230, AMBER, "#fff", 58, font="sans", center=True, html="Ottawa's own numbers: 8 in 10", rot=1, delay=0.7)]},
        {"at": 6.0, "end": 10.5, "theme": "dark", "items": [
            tile(60, 260, 960, 330, CREAM, TEAL, 104, words=True, html="Ottawa will pay for a <em>heat pump</em>", rot=1),
            tile(60, 640, 468, 440, AMBER, "#fff", 56, font="sans", center=True, html="Up to <b>$10,000</b> if your home earns less than the middle", rot=1.5, delay=0.5),
            tile(552, 640, 468, 440, TAN, "#7a4a00", 56, font="sans", center=True, html="<b>$2,000</b> for other homes", rot=-1.5, delay=0.7)]},
        _fed_cta(10.5, 15.0, h["foot"], "Not open yet. Want to hear <em>first</em>? \U0001F4EC")]}


def hp_furnace_30():
    """30 seconds: the same hook, then how it is meant to work, what is still unknown, and the launch alert."""
    h = _fed()
    return {"scenes": [
        {"at": 0.0, "end": 2.5, "theme": "dark", "items": [
            tile(60, 330, 960, 640, CREAM, TEAL, 140, words=True, html="Your furnace <em>will die</em>. Probably in the cold.", rot=-1.5), emoji(760, 170, "\U0001F976", 240, 12),
            sticker(90, 1040, "Heat pump news from Ottawa", size=48, rot=-4)]},
        {"at": 2.5, "end": 5.5, "theme": "light", "items": [
            tile(60, 280, 960, 520, TEAL, CREAM, 118, words=True, html="Most people replace heat <em>after</em> it breaks \U0001F4A5", rot=-1),
            sticker(150, 870, "8 in 10, says Ottawa", "cream", 50, 3, 0.9)]},
        {"at": 5.5, "end": 9.5, "theme": "dark", "items": [
            tile(60, 260, 960, 330, CREAM, TEAL, 104, words=True, html="Ottawa just announced a <em>heat pump</em> rebate", rot=1),
            tile(60, 640, 468, 440, AMBER, "#fff", 56, font="sans", center=True, html="Up to <b>$10,000</b> if your home earns less than the middle", rot=1.5, delay=0.5),
            tile(552, 640, 468, 440, TAN, "#7a4a00", 56, font="sans", center=True, html="<b>$2,000</b> for other homes", rot=-1.5, delay=0.7)]},
        {"at": 9.5, "end": 13.5, "theme": "light", "items": [
            tile(60, 260, 960, 330, "#ffffff", TEAL, 100, words=True, html="Here's the plan, <em>step by step</em> \U0001FA9C"),
            tile(60, 640, 960, 200, TEAL, CREAM, 56, font="sans", center=True, html="1. Apply online when your heat breaks or gets old", rot=-1, delay=0.5),
            tile(60, 880, 960, 200, AMBER, "#fff", 56, font="sans", center=True, html="2. Hear back within a day", rot=1, delay=0.8)]},
        {"at": 13.5, "end": 17.5, "theme": "light", "items": [
            tile(60, 260, 960, 200, TAN, "#7a4a00", 56, font="sans", center=True, html="3. Buy and install your heat pump", rot=1),
            tile(60, 500, 960, 200, TEAL, CREAM, 56, font="sans", center=True, html="4. Upload your receipts", rot=-1, delay=0.4),
            tile(60, 740, 960, 340, AMBER, "#fff", 96, words=True, html="Paid within <em>5 days</em> \U0001F4B8", rot=1, delay=0.8)]},
        {"at": 17.5, "end": 21.5, "theme": "dark", "items": [
            tile(60, 280, 960, 440, CREAM, TEAL, 128, words=True, html="No home energy check <em>first</em> \u2705", rot=-1),
            sticker(150, 800, "says Ottawa's plan", "cream", 48, 3, 0.8)]},
        {"at": 21.5, "end": 25.5, "theme": "light", "items": [
            tile(60, 260, 960, 440, AMBER, "#fff", 118, words=True, html="But it's <em>not open yet</em> \u23F3", rot=1),
            tile(60, 750, 960, 300, TEAL, CREAM, 62, font="sans", center=True, html="Expected early 2027. Installs from Nov 1, 2026 can apply. Who qualifies isn't published yet.", rot=-1, delay=0.6)]},
        _fed_cta(25.5, 30.0, h["foot"])]}


def hp_cold_air_15():
    """15 seconds. Hook: a machine that heats your home with cold air. Teaches: it moves heat, like a fridge in reverse."""
    h = _fed()
    return {"scenes": [
        {"at": 0.0, "end": 2.5, "theme": "dark", "items": [
            tile(60, 330, 960, 640, CREAM, TEAL, 140, words=True, html="This machine heats your home with <em>cold air</em>", rot=-1.5), emoji(760, 170, "\u2744\uFE0F", 240, 12),
            sticker(90, 1040, "How a heat pump works", size=48, rot=-4)]},
        {"at": 2.5, "end": 6.0, "theme": "light", "items": [
            tile(60, 280, 960, 520, TEAL, CREAM, 118, words=True, html="It doesn't make heat. It <em>moves</em> it \U0001F69A", rot=-1),
            sticker(160, 870, "like a fridge, but backwards \U0001F9CA", "cream", 46, 3, 0.9)]},
        {"at": 6.0, "end": 10.5, "theme": "dark", "items": [
            tile(60, 270, 960, 420, AMBER, "#fff", 112, words=True, html="Homes on oil, propane or plain electric heat save over <em>$1,400</em> a year", rot=1),
            sticker(150, 760, "average, says Ottawa", "cream", 48, -3, 0.9)]},
        _fed_cta(10.5, 15.0, h["foot"], "Ottawa will help pay. Hear <em>first</em>? \U0001F4EC")]}


def hp_cold_air_30():
    """30 seconds: the hook, the fridge idea in plain steps, the savings Ottawa cites, the rebate, and the alert."""
    h = _fed()
    return {"scenes": [
        {"at": 0.0, "end": 2.5, "theme": "dark", "items": [
            tile(60, 330, 960, 640, CREAM, TEAL, 140, words=True, html="This machine heats your home with <em>cold air</em>", rot=-1.5), emoji(760, 170, "\u2744\uFE0F", 240, 12),
            sticker(90, 1040, "How a heat pump works", size=48, rot=-4)]},
        {"at": 2.5, "end": 6.0, "theme": "light", "items": [
            tile(60, 280, 960, 520, TEAL, CREAM, 118, words=True, html="It doesn't make heat. It <em>moves</em> it \U0001F69A", rot=-1),
            sticker(190, 870, "that's the trick", "cream", 50, 3, 0.9)]},
        {"at": 6.0, "end": 10.0, "theme": "dark", "items": [
            tile(60, 260, 960, 380, CREAM, TEAL, 108, words=True, html="Think of a <em>fridge</em> \U0001F9CA", rot=1),
            tile(60, 690, 960, 380, AMBER, "#fff", 62, font="sans", center=True, html="A fridge pulls heat out of the box and dumps it in your kitchen", rot=-1, delay=0.6)]},
        {"at": 10.0, "end": 14.0, "theme": "light", "items": [
            tile(60, 260, 960, 380, TEAL, CREAM, 108, words=True, html="A heat pump <em>flips it</em> \U0001F501", rot=-1),
            tile(60, 690, 960, 380, TAN, "#7a4a00", 62, font="sans", center=True, html="It pulls heat out of the outside air and pushes it into your home", rot=1, delay=0.6)]},
        {"at": 14.0, "end": 18.0, "theme": "dark", "items": [
            tile(60, 280, 960, 440, CREAM, TEAL, 118, words=True, html="Even when it's <em>freezing</em> outside \U0001F976", rot=1),
            sticker(110, 800, "pick a model made for cold winters", "cream", 44, -3, 0.8)]},
        {"at": 18.0, "end": 22.0, "theme": "dark", "items": [
            tile(60, 260, 960, 440, AMBER, "#fff", 108, words=True, html="Oil, propane or plain electric heat? Save over <em>$1,400</em> a year", rot=1),
            sticker(150, 780, "on average, says Ottawa", "cream", 48, -3, 0.9)]},
        {"at": 22.0, "end": 26.0, "theme": "light", "items": [
            tile(60, 260, 960, 330, "#ffffff", TEAL, 100, words=True, html="And Ottawa will <em>help pay</em> \U0001F4B5"),
            tile(60, 640, 468, 440, AMBER, "#fff", 56, font="sans", center=True, html="Up to <b>$10,000</b> if your home earns less than the middle", rot=1.5, delay=0.5),
            tile(552, 640, 468, 440, TAN, "#7a4a00", 56, font="sans", center=True, html="<b>$2,000</b> for other homes", rot=-1.5, delay=0.7)]},
        _fed_cta(26.0, 30.0, h["foot"], "Not open yet. Hear <em>first</em>? \U0001F4EC")]}


def hp_explainer_60():
    """60 seconds: hook, how a heat pump works, why people switch, the national rebate (two levels, scale, how Ottawa says it will work, can be
    combined with provincial programs), what is still unknown, and the launch alert. Facts only: federal-0/1/2/3. Never says who qualifies, which provinces,
    gas homes, retroactivity or an exact start date."""
    h = _fed()
    f0 = kit.FACTS["federal-0-national-heat-pump-rebate"]
    f3 = kit.FACTS["federal-3-stacking"]
    assert "820,000" in f0["claim"] and "$2 billion" in f0["claim"] and "100,000" in f0["eligibility"], "federal scale changed: re-read before rendering"
    assert "combined" in f3["claim"] and "provincial" in f3["claim"], "federal stacking wording changed: re-read before rendering"
    return {"scenes": [
        {"at": 0.0, "end": 2.5, "theme": "dark", "items": [
            tile(60, 330, 960, 640, CREAM, TEAL, 140, words=True, html="Ottawa will pay up to <em>$10,000</em> for a heat pump \U0001F633", rot=-1.5),
            sticker(90, 1040, "Here's the catch...", size=50, rot=-4)]},
        {"at": 2.5, "end": 6.0, "theme": "light", "items": [
            tile(60, 280, 960, 520, TEAL, CREAM, 118, words=True, html="First: what <em>is</em> a heat pump? \U0001F914", rot=-1),
            sticker(150, 870, "it's not a pump for water", "cream", 46, 3, 0.9)]},
        {"at": 6.0, "end": 10.0, "theme": "dark", "items": [
            tile(60, 260, 960, 380, CREAM, TEAL, 108, words=True, html="It doesn't make heat. It <em>moves</em> it \U0001F69A", rot=1),
            tile(60, 690, 960, 380, AMBER, "#fff", 62, font="sans", center=True, html="Like a fridge, but flipped: it pulls heat out of the outside air and pushes it into your home", rot=-1, delay=0.6)]},
        {"at": 10.0, "end": 14.0, "theme": "light", "items": [
            tile(60, 280, 960, 440, "#ffffff", TEAL, 118, words=True, html="Even when it's <em>freezing</em> out \U0001F976"),
            sticker(110, 800, "pick a model made for cold winters", "teal", 46, -3, 0.8)]},
        {"at": 14.0, "end": 18.5, "theme": "dark", "items": [
            tile(60, 260, 960, 470, AMBER, "#fff", 108, words=True, html="Oil, propane or plain electric heat? Save over <em>$1,400</em> a year", rot=1),
            sticker(150, 800, "on average, says Ottawa", "cream", 50, -3, 0.9)]},
        {"at": 18.5, "end": 23.0, "theme": "light", "items": [
            tile(60, 260, 960, 330, "#ffffff", TEAL, 100, words=True, html="That's why Ottawa made a <em>national</em> rebate \U0001F341"),
            tile(60, 640, 468, 440, AMBER, "#fff", 56, font="sans", center=True, html="Up to <b>$10,000</b> if your home earns less than the middle", rot=1.5, delay=0.5),
            tile(552, 640, 468, 440, TAN, "#7a4a00", 56, font="sans", center=True, html="<b>$2,000</b> for other eligible homes", rot=-1.5, delay=0.7)]},
        {"at": 23.0, "end": 27.5, "theme": "dark", "items": [
            tile(60, 260, 960, 440, CREAM, TEAL, 118, words=True, html="Built for <em>a lot</em> of Canadian homes", rot=-1),
            tile(60, 750, 960, 300, TEAL, CREAM, 62, font="sans", center=True, html="$2 billion over 8 years, aimed at up to 820,000 households", rot=1, delay=0.6)]},
        {"at": 27.5, "end": 32.0, "theme": "light", "items": [
            tile(60, 260, 960, 300, "#ffffff", TEAL, 100, words=True, html="Here's the plan, <em>step by step</em> \U0001FA9C"),
            tile(60, 610, 960, 200, TEAL, CREAM, 54, font="sans", center=True, html="1. Apply online when your heat breaks or gets old", rot=-1, delay=0.5),
            tile(60, 850, 960, 200, AMBER, "#fff", 54, font="sans", center=True, html="2. Hear back within a day", rot=1, delay=0.8)]},
        {"at": 32.0, "end": 36.5, "theme": "light", "items": [
            tile(60, 250, 960, 190, TAN, "#7a4a00", 52, font="sans", center=True, html="3. Buy and install a heat pump from the approved list", rot=1),
            tile(60, 480, 960, 190, TEAL, CREAM, 52, font="sans", center=True, html="4. Upload your receipts", rot=-1, delay=0.4),
            tile(60, 710, 960, 340, AMBER, "#fff", 96, words=True, html="Paid within <em>5 days</em> \U0001F4B8", rot=1, delay=0.8)]},
        {"at": 36.5, "end": 41.0, "theme": "dark", "items": [
            tile(60, 260, 960, 440, CREAM, TEAL, 118, words=True, html="No home energy check <em>first</em> \u2705", rot=-1),
            sticker(150, 780, "says Ottawa's plan", "cream", 48, 3, 0.8)]},
        {"at": 41.0, "end": 46.0, "theme": "light", "items": [
            tile(60, 260, 960, 400, TEAL, CREAM, 108, words=True, html="Your province may add <em>more</em> \U0001F4B0", rot=1),
            tile(60, 710, 960, 340, AMBER, "#fff", 62, font="sans", center=True, html="Ottawa says it can be combined with provincial programs. Check your province's rules.", rot=-1, delay=0.6)]},
        {"at": 46.0, "end": 51.0, "theme": "dark", "items": [
            tile(60, 260, 960, 400, CREAM, TEAL, 112, words=True, html="What we <em>don't</em> know yet \U0001F937", rot=-1),
            tile(60, 710, 960, 340, TEAL, CREAM, 60, font="sans", center=True, html="Where the income line is. Which homes and which heating types qualify.", rot=1, delay=0.6)]},
        {"at": 51.0, "end": 55.0, "theme": "light", "items": [
            tile(60, 260, 960, 440, AMBER, "#fff", 118, words=True, html="And it's <em>not open yet</em> \u23F3", rot=1),
            tile(60, 750, 960, 280, TEAL, CREAM, 66, font="sans", center=True, html="Expected early 2027. Installs from Nov 1, 2026 can apply.", rot=-1, delay=0.6)]},
        _fed_cta(55.0, 60.0, h["foot"], "Be the first to <em>know</em> \U0001F4EC")]}


NL_VANITY = "homepowerrebate.com/nl-oil"   # _redirects sends it to the NL heating assistance page with utm_source=video


def _nl():
    """The Newfoundland oil supplement fact, checked."""
    f = kit.FACTS["nl-4-home-heating-supplement"]
    claim, elig = f["claim"], f["eligibility"]
    for must in ("from $500 to $1,000", "from $200 to $400", "do not need to apply again", "second payment"):
        assert must in claim, f"fact changed ({must}): re-read it before rendering"
    for must in ("$100,000 or less", "$150,000", "250 litres"):
        assert must in elig, f"fact changed ({must}): re-read it before rendering"
    assert f["amount"] == "$400 to $1,000" and f["status"] == "active" and "January 15, 2027" in f["dates"]
    return {"foot": f"Source: {urlparse(f['source_url']).netloc.replace('www.', '')}. Checked {nice(f['verified_on'])}."}


def _nl_hook():
    return {"at": 0.0, "end": 2.5, "theme": "dark", "items": [
        tile(60, 340, 960, 640, CREAM, TEAL, 150, words=True, html="Your oil rebate just <em>doubled</em>!", rot=-1.5), emoji(770, 190, "\U0001F4B0", 240, 12),
        sticker(90, 1040, "Newfoundland and Labrador", size=50, rot=-4)]}


def _nl_cta(at, end, foot):
    return {"at": at, "end": end, "theme": "dark", "foot": foot, "items": [
        tile(60, 330, 960, 450, CREAM, TEAL, 120, words=True, html="Here's <em>how to apply</em> \U0001F447", rot=1),
        tile(60, 830, 960, 260, AMBER, "#fff", 62, font="sans", center=True, html=NL_VANITY, rot=-1, delay=0.5),
        sticker(110, 1150, "or search: NL oil rebate 2026", "cream", 40, 3, 0.9)]}


def nl_oil_15():
    """15 seconds: doubled, the new amounts, who gets the full amount, already applied, link."""
    h = _nl()
    return {"scenes": [
        _nl_hook(),
        {"at": 2.5, "end": 5.5, "theme": "light", "items": [
            tile(60, 280, 960, 300, "#ffffff", TEAL, 100, words=True, html="It was $200 to $500. Now it's <em>$400 to $1,000</em>"),
            tile(60, 640, 960, 360, AMBER, "#fff", 70, font="sans", center=True, html="For homes heated with <b>furnace or stove oil</b>", rot=-1, delay=0.6)]},
        {"at": 5.5, "end": 9.0, "theme": "dark", "items": [
            tile(60, 260, 960, 330, CREAM, TEAL, 104, words=True, html="The full <em>$1,000</em> if your family earned $100,000 or less", rot=1),
            tile(60, 640, 960, 340, TAN, "#7a4a00", 62, font="sans", center=True, html="Earned up to $150,000? You get at least $400", rot=-1, delay=0.6)]},
        {"at": 9.0, "end": 11.5, "theme": "light", "items": [
            tile(60, 300, 960, 520, TEAL, CREAM, 124, words=True, html="Already applied? <em>Relax.</em> \u2705", rot=-1),
            sticker(150, 890, "you don't need to apply again", "cream", 46, 3, 0.8)]},
        _nl_cta(11.5, 15.0, h["foot"])]}


def nl_oil_30():
    """30 seconds: the same hook, the two amounts, what counts, already applied, how to apply, the deadline."""
    h = _nl()
    return {"scenes": [
        _nl_hook(),
        {"at": 2.5, "end": 6.0, "theme": "light", "items": [
            tile(60, 260, 960, 300, "#ffffff", TEAL, 100, words=True, html="Before: <em>$200 to $500</em>"),
            tile(60, 610, 960, 440, AMBER, "#fff", 128, words=True, html="Now: <em>$400 to $1,000</em> \U0001F389", rot=1, delay=0.6)]},
        {"at": 6.0, "end": 10.5, "theme": "dark", "items": [
            tile(60, 240, 960, 260, CREAM, TEAL, 90, words=True, html="Who gets the <em>full $1,000</em>?", rot=-1),
            tile(60, 540, 960, 280, AMBER, "#fff", 62, font="sans", center=True, html="Your family earned <b>$100,000 or less</b> in 2025", rot=1, delay=0.5),
            tile(60, 860, 960, 230, TAN, "#7a4a00", 56, font="sans", center=True, html="Earned up to $150,000? You get at least $400", rot=-1, delay=0.9)]},
        {"at": 10.5, "end": 15.0, "theme": "light", "items": [
            tile(60, 250, 960, 300, "#ffffff", TEAL, 100, words=True, html="What you <em>need</em> \U0001F9FE"),
            tile(60, 600, 960, 220, TEAL, CREAM, 56, font="sans", center=True, html="You pay for the oil yourself", rot=-1, delay=0.5),
            tile(60, 860, 960, 230, AMBER, "#fff", 56, font="sans", center=True, html="Bills for 250+ litres bought in 2026. <b>Keep them!</b>", rot=1, delay=0.9)]},
        {"at": 15.0, "end": 19.0, "theme": "dark", "items": [
            tile(60, 280, 960, 440, CREAM, TEAL, 118, words=True, html="Already applied? Don't apply <em>again</em>", rot=-1),
            tile(60, 770, 960, 300, AMBER, "#fff", 60, font="sans", center=True, html="Already paid? A second payment is coming later this year \U0001F4B8", rot=1, delay=0.6)]},
        {"at": 19.0, "end": 23.5, "theme": "light", "items": [
            tile(60, 250, 960, 300, "#ffffff", TEAL, 100, words=True, html="Two ways to <em>apply</em> \U0001F4DD"),
            tile(60, 600, 468, 460, TEAL, CREAM, 66, font="sans", center=True, html="Online", rot=1.5, delay=0.5),
            tile(552, 600, 468, 460, TAN, "#7a4a00", 66, font="sans", center=True, html="A paper form, by mail", rot=-1.5, delay=0.7)]},
        {"at": 23.5, "end": 27.0, "theme": "dark", "items": [
            tile(60, 280, 960, 440, AMBER, "#fff", 118, words=True, html="Last day: <em>January 15, 2027</em> \u23F0", rot=1),
            tile(60, 770, 960, 280, CREAM, TEAL, 62, font="sans", center=True, html="Late forms are not accepted", rot=-1, delay=0.6)]},
        _nl_cta(27.0, 30.0, h["foot"])]}


BENTO = {"ns-harp-status-6": ns_harp_status_6, "ns-harp-status-15": ns_harp_status_15, "ns-harp-status-30": ns_harp_status_30,
         "hp-furnace-15": hp_furnace_15, "hp-furnace-30": hp_furnace_30, "hp-cold-air-15": hp_cold_air_15, "hp-cold-air-30": hp_cold_air_30, "hp-explainer-60": hp_explainer_60,
         "nl-oil-15": nl_oil_15, "nl-oil-30": nl_oil_30}


def build_bento(name):
    spec = BENTO[name]()
    out_dir = ROOT / "videos"
    out_dir.mkdir(exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="hpr-bento-"))
    (tmp / "spec.json").write_text(json.dumps(spec))
    subprocess.run(["node", str(ROOT / "scripts/video/render_frames.js"), str(tmp / "spec.json"), str(tmp / "frames"), "30", str(ROOT)], check=True)
    final = out_dir / f"{name}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "30", "-i", str(tmp / "frames" / "frame_%05d.jpg"), "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(final)], check=True)
    print("wrote", final, f"{spec['scenes'][-1]['end']:.0f}s")
    subprocess.run(["rm", "-rf", str(tmp)])
    return final


VIDEOS = {"ns-harp-status": ns_harp_status}


def build(name, keep=False):
    scenes = VIDEOS[name]()
    out_dir = ROOT / "videos"
    out_dir.mkdir(exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="hpr-video-"))
    for i, s in enumerate(scenes):
        s.update(out=str(tmp / f"s{i}.png"), index=i, total=len(scenes))
        s.setdefault("foot", "")
    job = tmp / "job.json"
    job.write_text(json.dumps({"scenes": scenes}))
    subprocess.run(["node", str(ROOT / "scripts/video/render.js"), str(job), str(ROOT)], check=True)
    clips = []
    total = 0.0
    for i, sc in enumerate(scenes):
        secs = float(sc.get("seconds", SCENE_SECONDS))
        fade = min(FADE, secs / 5)
        total += secs
        clip = tmp / f"c{i}.mp4"
        # a slow drift across a slightly larger frame (cheap: no per-frame resampling)
        vf = (f"scale=1188:2112,crop=1080:1920:x='54-20*t':y='96-34*t',"
              f"fade=t=in:st=0:d={fade:.2f},fade=t=out:st={secs - fade:.2f}:d={fade:.2f},format=yuv420p")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", "30", "-t", f"{secs}", "-i", str(tmp / f"s{i}.png"), "-vf", vf,
                        "-r", "30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(clip)], check=True)
        clips.append(clip)
    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{c}'\n" for c in clips))
    final = out_dir / f"{name}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(final)], check=True)
    print("wrote", final, f"{total:.0f}s", "scenes in", tmp if keep else "(temp removed)")
    if not keep:
        subprocess.run(["rm", "-rf", str(tmp)])
    return final


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args and args[0] in BENTO:
        build_bento(args[0])
    elif args and args[0] in VIDEOS:
        build(args[0], keep="--keep" in sys.argv)
    else:
        sys.exit(__doc__)

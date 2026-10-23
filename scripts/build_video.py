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
            {"type": "tile", "x": 60, "y": 830, "w": 960, "h": 260, "bg": AMBER, "color": "#fff", "font": "sans", "size": 86, "center": True, "html": "homepowerrebate.com", "rot": -1, "delay": 0.45},
            {"type": "sticker", "x": 650, "y": 1150, "size": 46, "style": "cream", "html": "free guide", "rot": 5, "delay": 0.8}]},
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
            tile(60, 830, 960, 260, AMBER, "#fff", 86, font="sans", center=True, html="homepowerrebate.com", rot=-1, delay=0.5),
            sticker(650, 1150, "free guide", "cream", 46, 5, 0.9)]},
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
            tile(60, 830, 960, 260, AMBER, "#fff", 86, font="sans", center=True, html="homepowerrebate.com", rot=-1, delay=0.5),
            sticker(650, 1150, "free guide", "cream", 46, 5, 0.9)]},
    ]}


BENTO = {"ns-harp-status-6": ns_harp_status_6, "ns-harp-status-15": ns_harp_status_15, "ns-harp-status-30": ns_harp_status_30}


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

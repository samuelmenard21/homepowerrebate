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

SCENE_SECONDS = 5.0
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
    frames = int(SCENE_SECONDS * 30)
    for i in range(len(scenes)):
        clip = tmp / f"c{i}.mp4"
        vf = (f"scale=1188:2112,zoompan=z='min(zoom+0.0004,1.06)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps=30,"
              f"fade=t=in:st=0:d={FADE},fade=t=out:st={SCENE_SECONDS - FADE}:d={FADE},format=yuv420p")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(tmp / f"s{i}.png"), "-vf", vf, "-frames:v", str(frames), "-c:v", "libx264", "-crf", "18", str(clip)], check=True)
        clips.append(clip)
    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{c}'\n" for c in clips))
    final = out_dir / f"{name}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest",
                    "-c:v", "libx264", "-crf", "20", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(final)], check=True)
    print("wrote", final, f"{len(scenes) * SCENE_SECONDS:.0f}s", "scenes in", tmp if keep else "(temp removed)")
    if not keep:
        subprocess.run(["rm", "-rf", str(tmp)])
    return final


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args or args[0] not in VIDEOS:
        sys.exit(__doc__)
    build(args[0], keep="--keep" in sys.argv)

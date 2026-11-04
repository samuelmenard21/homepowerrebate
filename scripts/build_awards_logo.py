#!/usr/bin/env python3
"""Top-Rated Installer Awards logo (2026-11-04): a laurel seal in the site's own colours, as SVG.

assets/awards/top-rated-awards-emblem.svg   the seal alone (dark disc, so it works on any background)
assets/awards/top-rated-awards-lockup.svg   seal plus the words, for headers and press
Winner seals for each city and service are drawn by the same function (city_seal) in December. Text uses Fraunces with Georgia as the
fallback, so the logo looks right where the site font loads and close to it elsewhere; export PNGs from a browser for social sites.
Usage: python3 scripts/build_awards_logo.py [--year 2026]"""
import argparse
from math import atan2, cos, degrees, pi, radians, sin
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INK, TEAL, DEEP, AMBER, BRIGHT, PAPER, WARM = "#0a2a2e", "#0d4f5c", "#08363f", "#d4751c", "#e88a2e", "#faf7f2", "#f5efe5"
SERIF = "Fraunces, 'Iowan Old Style', Georgia, serif"
SANS = "'Inter Tight', 'Helvetica Neue', Arial, sans-serif"
CX, CY = 300, 290


def f(x):
    return f"{x:.1f}"


def laurel(mirror):
    """One laurel branch: a stem along an arc and paired leaves that taper toward the tip."""
    R = 176
    parts = []
    pts = []
    n = 12
    for k in range(n):
        th = radians(98 + k * 12.6)
        x, y = CX + R * cos(th), CY + R * sin(th)
        pts.append((x, y, th))
    d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y, _ in pts)
    parts.append(f'<path d="{d}" fill="none" stroke="url(#gold)" stroke-width="3" stroke-linecap="round"/>')
    for k, (x, y, th) in enumerate(pts):
        size = 1 - k * 0.032
        rx, ry = 25 * size, 9.5 * size
        tang = degrees(th) + 90          # direction of travel along the arc (clockwise in screen space)
        for side in (-1, 1):
            ang = radians(tang + side * 30)
            cx_, cy_ = x + cos(ang) * rx * 0.95, y + sin(ang) * rx * 0.95
            parts.append(f'<ellipse cx="{f(cx_)}" cy="{f(cy_)}" rx="{f(rx)}" ry="{f(ry)}" transform="rotate({f(degrees(ang))} {f(cx_)} {f(cy_)})" fill="url(#gold)" opacity="{0.96 if side == 1 else 0.82}"/>')
    # tip leaf
    x, y, th = pts[-1]
    ang = radians(degrees(th) + 90)
    cx_, cy_ = x + cos(ang) * 20, y + sin(ang) * 20
    parts.append(f'<ellipse cx="{f(cx_)}" cy="{f(cy_)}" rx="17" ry="7" transform="rotate({f(degrees(ang))} {f(cx_)} {f(cy_)})" fill="url(#gold)"/>')
    g = "".join(parts)
    return f'<g transform="translate({CX * 2} 0) scale(-1 1)">{g}</g>' if mirror else f"<g>{g}</g>"


def star(cx, cy, r):
    pts = []
    for i in range(10):
        a = -pi / 2 + i * pi / 5
        rr = r if i % 2 == 0 else r * 0.42
        pts.append(f"{f(cx + rr * cos(a))},{f(cy + rr * sin(a))}")
    return f'<polygon points="{" ".join(pts)}" fill="url(#gold)"/>'


def seal(year, top="TOP-RATED INSTALLER AWARDS", bottom="HOMEPOWERREBATE", band=None):
    """The seal as an SVG group (600 x 600 box). band: optional ribbon text (a city winner seal)."""
    stars = "".join(star(CX + 86 * cos(radians(a)), CY - 6 + 86 * sin(radians(a)), 9.5) for a in (-132, -111, -90, -69, -48))
    ribbon = ""
    if band:
        ribbon = (f'<g><path d="M 96 452 L 504 452 L 520 478 L 504 504 L 96 504 L 80 478 Z" fill="{AMBER}"/><path d="M 96 452 L 504 452 L 504 458 L 96 458 Z" fill="{BRIGHT}" opacity=".6"/>'
                  f'<text x="{CX}" y="489" text-anchor="middle" font-family="{SANS}" font-weight="700" font-size="22" letter-spacing="3" fill="{PAPER}">{band}</text></g>')
    return f"""<g id="seal">
<circle cx="{CX}" cy="{CY}" r="272" fill="url(#disc)"/>
<circle cx="{CX}" cy="{CY}" r="262" fill="none" stroke="url(#gold)" stroke-width="3"/>
<circle cx="{CX}" cy="{CY}" r="252" fill="none" stroke="url(#gold)" stroke-width="1" opacity=".55"/>
<circle cx="{CX}" cy="{CY}" r="196" fill="none" stroke="url(#gold)" stroke-width="1" opacity=".35"/>
<path id="arcT" d="M {CX - 224} {CY} A 224 224 0 0 1 {CX + 224} {CY}" fill="none"/>
<path id="arcB" d="M {CX - 236} {CY} A 236 236 0 0 0 {CX + 236} {CY}" fill="none"/>
<text font-family="{SANS}" font-weight="700" font-size="25" letter-spacing="6" fill="{BRIGHT}"><textPath href="#arcT" startOffset="50%" text-anchor="middle">{top}</textPath></text>
<text font-family="{SANS}" font-weight="600" font-size="19" letter-spacing="7" fill="{WARM}" opacity=".9"><textPath href="#arcB" startOffset="50%" text-anchor="middle">{bottom}</textPath></text>
<circle cx="{CX - 252}" cy="{CY}" r="4.5" fill="url(#gold)"/><circle cx="{CX + 252}" cy="{CY}" r="4.5" fill="url(#gold)"/>
{laurel(False)}{laurel(True)}
{stars}
<path d="M {CX - 64} {CY - 22} L {CX} {CY - 80} L {CX + 64} {CY - 22} L {CX + 50} {CY - 22} L {CX + 50} {CY + 40} L {CX - 50} {CY + 40} L {CX - 50} {CY - 22} Z" fill="{PAPER}"/>
<path d="M {CX - 64} {CY - 22} L {CX} {CY - 80} L {CX + 64} {CY - 22}" fill="none" stroke="url(#gold)" stroke-width="5" stroke-linejoin="round" stroke-linecap="round"/>
<polygon points="{CX + 8},{CY - 14} {CX - 16},{CY + 14} {CX - 2},{CY + 14} {CX - 8},{CY + 36} {CX + 18},{CY + 6} {CX + 4},{CY + 6}" fill="{AMBER}"/>
<line x1="{CX - 108}" y1="{CY + 82}" x2="{CX - 58}" y2="{CY + 82}" stroke="url(#gold)" stroke-width="2"/><line x1="{CX + 58}" y1="{CY + 82}" x2="{CX + 108}" y2="{CY + 82}" stroke="url(#gold)" stroke-width="2"/>
<text x="{CX}" y="{CY + 100}" text-anchor="middle" font-family="{SERIF}" font-weight="700" font-size="62" letter-spacing="2" fill="url(#gold)">{year}</text>
{ribbon}
</g>"""


DEFS = f"""<defs>
<radialGradient id="disc" cx="50%" cy="38%" r="75%"><stop offset="0" stop-color="{TEAL}"/><stop offset="0.55" stop-color="{DEEP}"/><stop offset="1" stop-color="{INK}"/></radialGradient>
<linearGradient id="gold" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f6c98a"/><stop offset="0.45" stop-color="{BRIGHT}"/><stop offset="1" stop-color="{AMBER}"/></linearGradient>
</defs>"""


def emblem(year, **kw):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" role="img" aria-label="HomePowerRebate Top-Rated Installer Awards {year}">'
            f'<title>HomePowerRebate Top-Rated Installer Awards {year}</title>{DEFS}{seal(year, **kw)}</svg>')


def lockup(year):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1260 640" role="img" aria-label="HomePowerRebate Top-Rated Installer Awards {year}">'
            f'<title>HomePowerRebate Top-Rated Installer Awards {year}</title>{DEFS}<rect width="1260" height="640" fill="{PAPER}"/>'
            f'<g transform="translate(20 20)">{seal(year)}</g>'
            f'<text x="660" y="250" font-family="{SANS}" font-weight="700" font-size="24" letter-spacing="6" fill="{AMBER}">HOMEPOWERREBATE</text>'
            f'<text x="660" y="330" font-family="{SERIF}" font-weight="700" font-size="72" fill="{INK}">Top-Rated</text>'
            f'<text x="660" y="410" font-family="{SERIF}" font-weight="700" font-size="72" fill="{INK}">Installer Awards</text>'
            f'<line x1="662" y1="440" x2="900" y2="440" stroke="{AMBER}" stroke-width="4"/>'
            f'<text x="660" y="490" font-family="{SANS}" font-weight="500" font-size="26" fill="{TEAL}">Ranked by Google reviews. Never paid for.</text></svg>')


def city_seal(year, band):
    return emblem(year, band=band, bottom="")   # the ribbon sits over the bottom arc, so that text is dropped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", default="2026")
    a = ap.parse_args()
    out = ROOT / "assets" / "awards"
    out.mkdir(parents=True, exist_ok=True)
    (out / "top-rated-awards-emblem.svg").write_text(emblem(a.year), encoding="utf-8")
    (out / "top-rated-awards-lockup.svg").write_text(lockup(a.year), encoding="utf-8")
    (out / "top-rated-awards-city-sample.svg").write_text(city_seal(a.year, "HAMILTON · HEAT PUMPS"), encoding="utf-8")
    print("wrote", ", ".join(p.name for p in sorted(out.glob("*.svg"))))


if __name__ == "__main__":
    main()

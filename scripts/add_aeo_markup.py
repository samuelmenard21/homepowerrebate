#!/usr/bin/env python3
"""Add speakable and FAQPage JSON-LD to built pages. Idempotent: blocks sit between AEO-*-START/END markers.

- Speakable: only on indexable pages whose hero holds an h1 immediately followed by a lead paragraph. The selectors
  point at those two elements (`.hero h1`, `.hero h1 + p`), so the markup always matches visible text.
- FAQPage: only on pages that already SHOW visible question and answer pairs (.faq-item blocks) and have no FAQPage yet.
  Questions and answers are copied from the visible text; nothing is written for the schema alone.
Usage: python3 scripts/add_aeo_markup.py [--dry-run]
"""
import html
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = ("scripts/", "_partials/", "data/", "drafts/")
SP_S, SP_E = "<!-- AEO-SPEAKABLE-START -->", "<!-- AEO-SPEAKABLE-END -->"
FQ_S, FQ_E = "<!-- AEO-FAQ-START -->", "<!-- AEO-FAQ-END -->"
BLOCK = lambda s, e: re.compile(re.escape(s) + r".*?" + re.escape(e) + r"\n?", re.S)
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


class Node:
    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.parent, self.kids = tag, dict(attrs), parent, []

    def cls(self):
        return (self.attrs.get("class") or "").split()

    def text(self):
        out = []
        for k in self.kids:
            out.append(k if isinstance(k, str) else ("" if k.tag in ("script", "style") else k.text()))
        return " ".join("".join(out).split())

    def walk(self):
        yield self
        for k in self.kids:
            if not isinstance(k, str):
                yield from k.walk()


class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("root", [], None)
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.cur)
        self.cur.kids.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_endtag(self, tag):
        c = self.cur
        while c is not self.root and c.tag != tag:
            c = c.parent
        if c is not self.root:
            self.cur = c.parent

    def handle_data(self, data):
        self.cur.kids.append(data)


def parse(s):
    t = Tree()
    t.feed(re.sub(r"<!--.*?-->", "", s, flags=re.S))
    return t.root


def first_text(node, selectors):
    for n in node.walk():
        if n is node:
            continue
        for tag, cls in selectors:
            if n.tag == tag and (cls is None or cls in n.cls()):
                return n
    return None


def faq_pairs(root):
    pairs = []
    for item in root.walk():
        if "faq-item" not in item.cls():
            continue
        q = first_text(item, [("h3", None), ("h4", None), ("button", "faq-question"), ("div", "faq-q")])
        a = first_text(item, [("div", "faq-a"), ("div", "faq-answer")])
        if q is None:
            continue
        if a is None:
            ps = [k for k in item.kids if not isinstance(k, str) and k.tag == "p"]
            answer = " ".join(p.text() for p in ps)
        else:
            answer = a.text()
        qt = q.text().rstrip("+ ").strip()
        # drop a trailing toggle glyph that sits inside the question element
        qt = re.sub(r"\s*[+−–-]$", "", qt).strip()
        if qt and answer:
            pairs.append((qt, answer))
    return pairs


def hero_ok(root):
    for n in root.walk():
        if n.tag in ("section", "header", "div") and "hero" in n.cls():
            kids = [k for k in n.walk() if k is not n]
            for i, k in enumerate(kids):
                if k.tag == "h1":
                    sib = [x for x in k.parent.kids if not isinstance(x, str) or x.strip()]
                    j = sib.index(k)
                    return j + 1 < len(sib) and not isinstance(sib[j + 1], str) and sib[j + 1].tag == "p" and len(sib[j + 1].text()) >= 30
    return False


def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, separators=(", ", ": ")) + "</script>"


def process(rel, dry):
    p = ROOT / rel
    s = p.read_text(encoding="utf-8", errors="ignore")
    if re.search(r"<meta[^>]*noindex", s):
        return None
    canon = re.search(r'rel="canonical" href="([^"]+)"', s)
    title = re.search(r"<title>(.*?)</title>", s, re.S)
    if not canon or not title or "</head>" not in s:
        return None
    original = s
    s = BLOCK(SP_S, SP_E).sub("", s)
    s = BLOCK(FQ_S, FQ_E).sub("", s)
    root = parse(re.sub(r"<(script|style)\b.*?</\1>", "", s, flags=re.S | re.I))
    add = []
    if hero_ok(root):
        add.append(SP_S + "\n" + ld({"@context": "https://schema.org", "@type": "WebPage", "name": html.unescape(title.group(1).strip()),
                                    "url": canon.group(1),
                                    "speakable": {"@type": "SpeakableSpecification", "cssSelector": [".hero h1", ".hero h1 + p"]}}) + "\n" + SP_E)
    if "FAQPage" not in s:
        pairs = faq_pairs(root)
        if len(pairs) >= 2:
            add.append(FQ_S + "\n" + ld({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in pairs]}) + "\n" + FQ_E)
    if add:
        s = s.replace("</head>", "\n".join(add) + "\n</head>", 1)
    if s != original and not dry:
        p.write_text(s, encoding="utf-8")
    return ("speakable" in "".join(add), "FAQPage" in "".join(add), s != original)


def main():
    dry = "--dry-run" in sys.argv
    files = subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "*.html"], text=True).split()
    sp = fq = n = 0
    for f in files:
        if f.startswith(SKIP) or f in ("privacy.html", "terms.html") or re.match(r"^[A-Z_]+.*\.html$", f) or "template" in f.lower():
            continue
        r = process(f, dry)
        if r:
            sp += r[0]; fq += r[1]; n += r[2]
    print(f"{'would change' if dry else 'changed'} {n} pages: speakable on {sp}, FAQPage on {fq}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Turn a page family's shared inline <style> block into _partials/templates/<name>.base.css.

Every selector is scoped to body.tpl-<name> through :where(), so specificity does not change, and the file is placed
before the shared CSS in site.css, so the cascade does not change either. Then add the block's hash to TEMPLATE_LEGACY
in apply_canonical_nav_footer.py and run the restamp: pages lose the inline block and gain the body class.
Usage: python3 scripts/extract_template_css.py <page.html> <name> <text that identifies the block>
Prints the normalised sha1 to add to TEMPLATE_LEGACY."""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def scope_selector(sel, body):
    out = []
    for x in sel.split(","):
        x = x.strip()
        if not x:
            continue
        if x in (":root", "html"):
            out.append(x if x == ":root" else f"html:has(> body.{body})")
        elif x == "*":
            out += [f":where(body.{body})", f":where(body.{body}) *"]
        elif re.match(r"body\b", x):
            out.append(f"body:where(.{body})" + x[4:])
        else:
            out.append(f":where(body.{body}) {x}")
    return ", ".join(out)


def scope(css, body):
    out, i = [], 0
    while i < len(css):
        j = css.find("{", i)
        if j < 0:
            break
        head = css[i:j].strip()
        if head.startswith(("@media", "@supports", "@keyframes", "@-webkit-keyframes")):
            depth, k = 1, j + 1
            while depth:
                depth += {"{": 1, "}": -1}.get(css[k], 0)
                k += 1
            inner = css[j + 1:k - 1]
            out.append(head + " {\n" + (inner.strip() if "keyframes" in head else scope(inner, body)) + "\n}")
            i = k
            continue
        k = css.find("}", j)
        decl = css[j + 1:k].strip()
        if head.startswith("@"):
            out.append(f"{head} {{ {decl} }}")
        else:
            out.append(scope_selector(head, body) + " { " + decl + " }")
        i = k + 1
    return "\n".join(out)


def main():
    page, name, ident = sys.argv[1], sys.argv[2], sys.argv[3]
    s = (ROOT / page).read_text(encoding="utf-8")
    block = next(b for b in re.findall(r"<style>([\s\S]*?)</style>", s) if ident in b)
    css = re.sub(r"/\*.*?\*/", "", block, flags=re.S)
    out = ROOT / "_partials" / "templates" / f"{name}.base.css"
    out.write_text(f"/* {name} template base: the rules each page used to carry inline (from {page}), scoped to body.tplb-{name} with no added specificity */\n"
                   + scope(css, f"tplb-{name}") + "\n", encoding="utf-8")
    print(hashlib.sha1(" ".join(block.split()).encode()).hexdigest())


if __name__ == "__main__":
    main()

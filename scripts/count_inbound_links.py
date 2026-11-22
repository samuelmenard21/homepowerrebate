import re,subprocess,json,collections,sys
from urllib.parse import urlparse
root='.'
files=[f for f in subprocess.run(['git','ls-files','*.html'],capture_output=True,text=True).stdout.split()]
SKIP=('_partials/','scripts/','embed/','calculator/embed/','data/','node_modules','.claude/','ONTARIO_','CITY_','city-page','pinterest','installer-carousel','og-image','unified','solar-carousel','preview','nav-footer','outreach/')
def url(f):
    if f=='index.html': return '/'
    if f.endswith('/index.html'): return '/'+f[:-10]
    return '/'+f[:-5]
pages={}
for f in files:
    if f.startswith(SKIP) or 'embed/' in f: continue
    s=open(f,errors='ignore').read()
    pages[url(f)]=s
def indexable(s): return not re.search(r'name="robots"[^>]*noindex',s[:8000])
def body(s):
    s=re.sub(r'<!-- CANONICAL-NAV-START -->.*?<!-- CANONICAL-NAV-END -->','',s,flags=re.S)
    s=re.sub(r'<!-- CANONICAL-FOOTER-START -->.*?<!-- CANONICAL-FOOTER-END -->','',s,flags=re.S)
    s=re.sub(r'<head>.*?</head>','',s,flags=re.S)
    return s
inb=collections.defaultdict(set); n=0
for u,s in pages.items():
    for m in re.finditer(r'<a\s[^>]*href="([^"#?]*)',body(s)):
        h=m.group(1)
        if h.startswith('https://homepowerrebate.com'): h=h[len('https://homepowerrebate.com'):] or '/'
        if not h.startswith('/'): continue
        h=h.rstrip('/') or '/'
        h2=h if h=='/' else h+'/'
        for t in (h2,h):
            if t in pages and t!=u: inb[t].add(u); break
idx=[u for u,s in pages.items() if indexable(s)]
rows=sorted(((len(inb[u]),u) for u in idx))
weak=[(c,u) for c,u in rows if c<3]
print('indexable',len(idx),'weak(<3)',len(weak),'zero',sum(1 for c,u in rows if c==0))
fam=collections.Counter()
for c,u in weak: fam['/'.join(u.strip('/').split('/')[:2]) or '/']+=1
print(fam.most_common(15))
for c,u in weak[:60]: print(c,u)
json.dump({u:len(inb[u]) for u in idx},open('seo/internal-link-graph.json','w'),indent=0,sort_keys=True)
mp=['/get-quotes/','/programs/national-heat-pump-rebate/','/installers/heat-pump/','/calculator/widget/','/powerscore/','/ca/bc/','/ca/on/','/us/ma/','/programs/national-heat-pump-rebate/do-i-qualify/','/blog/']
print('money pages inbound:',{m:len(inb[m]) for m in mp if m in pages})

import re, pathlib, unicodedata
from collections import OrderedDict

path = pathlib.Path(r'c:\Users\HP\chatbot_ntu\data\nlu.yml')
text = path.read_text(encoding='utf-8')
lines = text.splitlines()

header=[]
idx=0
while idx < len(lines) and not re.match(r'^nlu:\s*$', lines[idx]):
    header.append(lines[idx]); idx+=1
if idx < len(lines):
    header.append(lines[idx]); idx+=1

intents=OrderedDict(); order=[]
while idx < len(lines):
    m=re.match(r'^\s*- intent:\s+([A-Za-z0-9_]+)\s*$', lines[idx])
    if not m:
        idx+=1; continue
    intent=m.group(1); order.append(intent); idx+=1
    while idx < len(lines) and not re.match(r'^\s*examples:\s*\|\s*$', lines[idx]):
        idx+=1
    if idx < len(lines): idx+=1
    ex=[]
    while idx < len(lines) and not re.match(r'^\s*- intent:\s+', lines[idx]):
        s=lines[idx].strip()
        if s.startswith('- '): ex.append(re.sub(r'\s+',' ',s[2:].strip()))
        idx+=1
    intents[intent]=ex

def no_diac(s:str)->str:
    s=s.replace('đ','d').replace('Đ','D')
    return ''.join(ch for ch in unicodedata.normalize('NFD', s) if unicodedata.category(ch)!='Mn')

abbr_map=[('không','ko'),('khong','ko'),('được','dc'),('duoc','dc'),('với','vs'),('voi','vs'),('như thế nào','ntn'),('nhu the nao','ntn'),('hệ thống','ht'),('he thong','ht'),('đăng nhập','login'),('dang nhap','login'),('mật khẩu','mk'),('mat khau','mk'),('tài khoản','tk'),('tai khoan','tk'),('giảng viên','gv'),('giang vien','gv')]

def abbr(s:str)->str:
    low=s.lower()
    for a,b in abbr_map:
        low=low.replace(a,b)
    return re.sub(r'\s+',' ',low).strip()

suffixes=[' nha',' nhe',' a',' ah',' z']

def make_candidates(ex:str):
    base=re.sub(r'\s+',' ',ex.strip())
    c=[base, base.lower(), no_diac(base), abbr(base), abbr(no_diac(base))]
    q=('?' in base) or any(w in base.lower() for w in ['khong','không','sao','gi','nao','nào','o dau','ở đâu','bao nhieu','bao lâu','khi nao'])
    stem=base.rstrip(' ?.!')
    if q:
        for suf in suffixes:
            c.extend([(stem+suf).strip(), no_diac((stem+suf).strip()), abbr((stem+suf).strip())])
    else:
        c.extend([stem+' nha', no_diac(stem)+' nha', abbr(stem+' nha')])
    out=[]; seen=set()
    for x in c:
        x=re.sub(r'\s+',' ',x).strip(' -')
        if len(x)<4: continue
        k=x.lower()
        if k in seen: continue
        seen.add(k); out.append(x)
    return out

TARGET=55; MAX_KEEP=60
for k,v in intents.items():
    seen=set(); clean=[]
    for e in v:
        e=re.sub(r'\s+',' ',e).strip()
        if not e: continue
        kl=e.lower()
        if kl in seen: continue
        seen.add(kl); clean.append(e)
    intents[k]=clean

global_used=set(); reb=OrderedDict()
for intent in order:
    src=intents[intent]
    chosen=[]
    for e in src:
        k=e.lower()
        if k in global_used: continue
        if len(chosen)>=MAX_KEEP: break
        chosen.append(e); global_used.add(k)
    if len(chosen)<TARGET:
        pool=[]
        for e in src: pool.extend(make_candidates(e))
        for cand in pool:
            k=cand.lower()
            if k in global_used: continue
            chosen.append(cand); global_used.add(k)
            if len(chosen)>=TARGET: break
    i=0
    while len(chosen)<TARGET and src and i<600:
        e=src[i%len(src)].strip(' ?.!')
        for z in [f"{e} duoc khong", no_diac(f"{e} duoc khong"), abbr(f"{e} duoc khong"), f"{e} nha", no_diac(f"{e} nha")]:
            kz=z.lower()
            if kz not in global_used and len(z)>=4:
                chosen.append(z); global_used.add(kz)
                if len(chosen)>=TARGET: break
        i+=1
    if len(chosen)>MAX_KEEP:
        for x in chosen[MAX_KEEP:]: global_used.discard(x.lower())
        chosen=chosen[:MAX_KEEP]
    reb[intent]=chosen

out=[]; out.extend(header)
for intent, exs in reb.items():
    out.append(f"  - intent: {intent}")
    out.append("    examples: |")
    for e in exs: out.append(f"      - {e}")
    out.append("")

path.write_text('\n'.join(out).rstrip()+'\n', encoding='utf-8')
print('updated', len(reb), 'intents')
print('min', min(len(v) for v in reb.values()), 'max', max(len(v) for v in reb.values()))

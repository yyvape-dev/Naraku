"""素材フォルダを、配布版に埋め込む用の軽い版に作り直す（元の素材は触らない）。
   使い方: python3 slim.py <素材フォルダ=assets> <出力フォルダ=assets_min> [townw=480 town=50 atlask=76 atlas=64 cut=60 face=68 art=70 bg=58 bgw=440 map=52 mapw=440 part=70 partk=62]
   配布版が2MBを超えると、スマホのClaudeアプリのプレビューで起動しなくなった（スクリプトが途中で切れた時と同じ症状）。
   そのため配布版は必ず assets_min から作り、2MB未満に収める。"""
import sys, os, shutil, glob, json
from PIL import Image
a=[x for x in sys.argv[1:] if '=' not in x]; src=a[0] if a else 'assets'; out=a[1] if len(a)>1 else 'assets_min'
o=dict(x.split('=') for x in sys.argv[1:] if '=' in x); Q=lambda k,d:int(o.get(k,d))
os.makedirs(out,exist_ok=True); tot0=tot1=0
for f in glob.glob(out+'/*'): os.remove(f)
for p in sorted(glob.glob(src+'/*')):
    n=os.path.basename(p); d=f'{out}/{n}'
    if not n.endswith('.webp'): shutil.copy(p,d); continue
    k=n[:-5]; im=Image.open(p)
    if os.path.exists(f'{src}/{k}.json'):      # スプライトのアトラス（透過あり）。atlask=縮小率(%)。コマの大きさと基準点（json）も同じ率で直す
        m=json.load(open(f'{src}/{k}.json')); r=Q('atlask',76)/100; cw,ch=max(1,round(m['cw']*r)),max(1,round(m['ch']*r))
        im.convert('RGBA').resize((cw*m['cols'],ch),Image.LANCZOS).save(d,quality=Q('atlas',64),alpha_quality=80,method=6)
        m.update(ax=round(m['ax']*cw/m['cw'],2),ay=round(m['ay']*ch/m['ch'],2),refH=round(m['refH']*ch/m['ch'],1),cw=cw,ch=ch); json.dump(m,open(f'{out}/{k}.json','w'))
        tot0+=os.path.getsize(p); tot1+=os.path.getsize(d); continue
    elif n.startswith('cut_'):  im.convert('RGB').save(d,quality=Q('cut',60),method=6)
    elif n.startswith('face_'): im.convert('RGB').save(d,quality=Q('face',68),method=6)
    elif n in ('ui_medals.webp','ui_pieces.webp'):  # 盤上のメダルと駒（透過あり。小さく表示するので縮める）
        k=Q('partk',62)/100; im=im.convert('RGBA').resize((round(im.width*k),round(im.height*k)),Image.LANCZOS); im.save(d,quality=Q('part',70),alpha_quality=82,method=6)
    elif n=='ui_town.webp':  # 街の一枚絵（明るく細部が多い。幅を落として軽くする）
        w=Q('townw',480); im=im.convert('RGB'); im=im.resize((w,round(w*im.height/im.width)),Image.LANCZOS) if im.width>w else im; im.save(d,quality=Q('town',50),method=6)
    elif n.startswith('ui_fac_'):  # 施設の背景（街の絵と同じ扱い）
        w=Q('townw',480); im=im.convert('RGB'); im=im.resize((w,round(w*im.height/im.width)),Image.LANCZOS) if im.width>w else im; im.save(d,quality=Q('town',50),method=6)
    elif n.startswith('ui_npc_'):  # 施設の店主（透過あり。画面では高さ約520pxまで）
        w=Q('npcw',340); im=im.convert('RGBA'); im=im.resize((w,round(w*im.height/im.width)),Image.LANCZOS) if im.width>w else im; im.save(d,quality=Q('npc',66),alpha_quality=80,method=6)
    elif n=='ui_map.webp':  # 探索の盤面（暗い石の質感。細部が多く重いので、幅を落とす）
        w=Q('mapw',440); im=im.convert('RGB'); im=im.resize((w,round(w*im.height/im.width)),Image.LANCZOS) if im.width>w else im; im.save(d,quality=Q('map',52),method=6)
    elif n.startswith('bg_'):
        w=Q('bgw',440); im=im.convert('RGB'); im=im.resize((w,round(w*im.height/im.width)),Image.LANCZOS) if im.width>w else im; im.save(d,quality=Q('bg',58),method=6)
    else: im.convert('RGB').save(d,quality=Q('art',70),method=6)
    if os.path.getsize(d)>os.path.getsize(p): shutil.copy(p,d)   # 軽くならなかったものは元のまま
    tot0+=os.path.getsize(p); tot1+=os.path.getsize(d)
print(f'slim {src} → {out}: {tot0//1024} KB → {tot1//1024} KB')

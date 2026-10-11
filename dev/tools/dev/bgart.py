"""戦場の背景（床の絵）を整える。使い方: python3 bgart.py <出力フォルダ> <キー>=<画像> …  [w=540 q=66 keep=0.8 src=<元絵の保存先>]
   ゲームは絵を縦横比を保ったまま戦場いっぱいに敷く（はみ出す分は中央基準で切る）ので、比率は問わない。
   keep＝左右を残す割合。戦場は縦長の画面で幅/高さ≒0.43、短い画面で≒0.55。
     2:3（0.67）の絵は中央の約7割しか映らない → keep=0.8（既定）
     9:16（0.56）の絵は短い画面でほぼ全幅が映る → keep=1（切らない）
   src=cardart を付けると、元絵を cardart/src_bg_<キー>.webp（q95）として残す。"""
import sys, os
from PIL import Image
OPT=('w','q','keep','src')
out=sys.argv[1]; opt=dict(a.split('=') for a in sys.argv[2:] if a.split('=')[0] in OPT); items=[a for a in sys.argv[2:] if a.split('=')[0] not in OPT]
w=int(opt.get('w',540)); q=int(opt.get('q',66)); keep=float(opt.get('keep',0.8)); src=opt.get('src')
for a in items:
    k,path=a.split('=',1); im=Image.open(path).convert('RGB'); W,H=im.size
    if src and os.path.abspath(path)!=os.path.abspath(f'{src}/src_bg_{k}.webp'): im.save(f'{src}/src_bg_{k}.webp',quality=95,method=6)
    cw=round(W*keep); x=(W-cw)//2
    im=im.crop((x,0,x+cw,H)); ww=min(w,cw)
    if ww!=cw: im=im.resize((ww,round(ww*H/cw)),Image.LANCZOS)
    p=f'{out}/bg_{k}.webp'; im.save(p,quality=q,method=6); print(k,(W,H),'→',im.size,os.path.getsize(p)//1024,'KB')

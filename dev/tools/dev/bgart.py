"""戦場の背景（真上から見た床）を整える。使い方: python3 bgart.py <出力フォルダ> <キー>=<画像> …  [w=540 q=66 keep=0.8]
   画面には中央の約7割しか映らないので、左右を keep の割合まで切り落としてから縮小する。"""
import sys, os
from PIL import Image
out=sys.argv[1]; opt=dict(a.split('=') for a in sys.argv[2:] if a.split('=')[0] in('w','q','keep')); items=[a for a in sys.argv[2:] if a.split('=')[0] not in('w','q','keep')]
w=int(opt.get('w',540)); q=int(opt.get('q',66)); keep=float(opt.get('keep',0.8))
for a in items:
    k,path=a.split('=',1); im=Image.open(path).convert('RGB'); W,H=im.size; cw=round(W*keep); x=(W-cw)//2
    im=im.crop((x,0,x+cw,H)); im=im.resize((w,round(w*H/cw)),Image.LANCZOS)
    p=f'{out}/bg_{k}.webp'; im.save(p,quality=q,method=6); print(k,(W,H),'→',im.size,os.path.getsize(p)//1024,'KB')

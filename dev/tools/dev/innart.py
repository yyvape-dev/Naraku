"""宿屋の素材を焼く：cardart/src_inn_*.webp → assets/ui_inn_*.webp
   使い方: python3 -I tools/dev/innart.py cardart assets
   ledger（台帳・透過）/ win（就寝後の窓・透過）/ morn（朝の光・透過。宿屋の背景と同じ比率941:1672を720幅に）/ room（寝室）/ stable（馬小屋）"""
import sys
from PIL import Image
import numpy as np
src,dst=sys.argv[1],sys.argv[2]
def clean(im,lo=10,hi=245):
    a=np.array(im.convert('RGBA'));al=a[...,3]
    al[al>=hi]=255;a[al<lo]=0          # 本体のわずかな透け（250〜254）を不透明に、ほぼ透明の縁（赤・黄の残りかす）を完全な透明に
    return Image.fromarray(a)
def fit(im,w):return im if im.width<=w else im.resize((w,round(im.height*w/im.width)),Image.LANCZOS)
J={'ledger':(780,88,True),'win':(760,88,True),'morn':(720,76,True),'room':(1448,74,False),'stable':(1448,74,False)}
for k,(w,q,al) in J.items():
    im=Image.open(f'{src}/src_inn_{k}.webp')
    im=fit(clean(im) if al else im.convert('RGB'),w)
    if k=='morn':
        a=np.array(im);a[a[...,3]<14]=0;im=Image.fromarray(a)
    im.save(f'{dst}/ui_inn_{k}.webp',quality=q,method=6)
    print(k,im.size)

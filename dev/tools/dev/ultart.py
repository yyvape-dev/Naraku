"""超必殺のカットイン絵（マゼンタ/濃いピンク背景の縦長）→ 背景を抜いた assets/ult_<id>.webp
   使い方: python3 -I tools/dev/ultart.py <id> <元画像> [unmix]
   unmix＝背景色が混ざった中間色（赤い光に乗ったピンクなど）も、混ざった分だけ透かす。紫の多い絵（シェリ）には使わない（紫が消える）
   背景色は右上の隅から測る（絵ごとに #FF00FF〜#FB039C とばらつくため）。縁は背景色を差し引いて色にじみを消す。"""
import sys,numpy as np
from PIL import Image
k,src=sys.argv[1],sys.argv[2]
im=Image.open(src).convert('RGB')
im.save(f'cardart/src_ult_{k}.webp',quality=92)
a=np.asarray(im).astype(np.float32)
bg=a[2:12,-12:-2].reshape(-1,3).mean(0)
d=np.sqrt(((a-bg)**2).sum(2))
al=np.clip((d-40)/80,0,1)
if 'unmix' in sys.argv[3:]:
    # 背景色をどこまで差し引けるか（色が0〜255に収まる最大の割合 t）を画素ごとに求め、その9割を透かす
    t=np.ones(a.shape[:2],np.float32)
    for c in range(3):
        b=bg[c]
        if b>1:t=np.minimum(t,a[...,c]/b)
        t=np.minimum(t,np.where(b<255,(255-a[...,c])/np.maximum(255-b,1),1))
    al=np.minimum(al,1-0.9*np.clip(t,0,1))
m=(al>0)&(al<1)
rgb=a.copy()
rgb[m]=np.clip((a[m]-bg*(1-al[m,None]))/np.maximum(al[m,None],0.05),0,255)
rgb[al==0]=0
out=Image.fromarray(np.dstack([rgb,al*255]).astype(np.uint8),'RGBA')
out.save(f'assets/ult_{k}.webp',quality=88,method=6)
import os;print(k,out.size,'bg',bg.round().tolist(),round(os.path.getsize(f'assets/ult_{k}.webp')/1024),'KB')

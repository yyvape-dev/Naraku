"""マリアンヌの通常攻撃のVFX（白金の光と風）を焼く。使い方: python3 -I tools/dev/sisart.py cardart assets
   元画像 cardart/src_vfx_sister_{thread,wind,sheet}.webp（ChatGPT作・透過）→ assets/vfx_sister_*.webp
   thread/wind は下敷き（guide 1024×1536、キャラは ox=237, oy=691, 3倍）の線の両端へ回転・拡大で寄せ、
   ベージュのにじみ（光の外側）を弱めて細く見せる（白い芯は残す）。出力は下敷きの座標のまま 0.5 倍（512×768）。
   sheet（3列×2段）は区画ごとに切り出す：orb / feather_a / feather_b / bolt / pillar / rays"""
import sys
from PIL import Image
import numpy as np
from scipy import ndimage as ndi
src,dst=sys.argv[1],sys.argv[2];OX,OY,S=237,691,3
G=lambda p:np.array([OX+p[0]*S,OY+p[1]*S],float)
L=lambda k:Image.open(f'{src}/src_vfx_sister_{k}.webp').convert('RGBA')
THREAD=[(60,160),(161,65)];WIND=[(92,262),(168,56)]
def ends(im,d):
    a=np.array(im)[...,3];ys,xs=np.nonzero(a>60);P=np.stack([xs,ys],1).astype(float);pr=P@d
    lo=P[pr<=np.percentile(pr,0.4)].mean(0);hi=P[pr>=np.percentile(pr,99.6)].mean(0);return lo,hi
def fit(im,g0,g1,sx=1.0):
    d=(g1-g0)/np.linalg.norm(g1-g0);a,b=ends(im,d);v=b-a;w=g1-g0
    s=np.linalg.norm(w)/np.linalg.norm(v);ang=np.arctan2(w[1],w[0])-np.arctan2(v[1],v[0])
    R=np.array([[np.cos(ang),-np.sin(ang)],[np.sin(ang),np.cos(ang)]])*s
    # 線に直交する向きだけ sx 倍（太さを詰める）
    u=w/np.linalg.norm(w);n=np.array([-u[1],u[0]]);Q=np.outer(u,u)+sx*np.outer(n,n);M=Q@R
    Mi=np.linalg.inv(M);off=a-Mi@g0
    out=im.transform((1024,1536),Image.AFFINE,(Mi[0,0],Mi[0,1],off[0],Mi[1,0],Mi[1,1],off[1]),Image.BICUBIC)
    print('scale',round(s,3),'rot',round(np.degrees(ang),1),'sx',sx);return out
def thin(im,keep,t0=205):
    a=np.array(im).astype(float);lum=a[...,:3].mean(-1);w=np.clip((lum-t0)/40,0,1)
    a[...,3]*=keep+(1-keep)*w;return Image.fromarray(a.clip(0,255).astype(np.uint8))
def save(im,n):im.save(f'{dst}/vfx_sister_{n}.webp','WEBP',quality=88,method=6);print(n,im.size)
save(fit(thin(L('thread'),0.12),G(THREAD[0]),G(THREAD[1])).resize((512,768),Image.LANCZOS),'thread')
save(fit(thin(L('wind'),0.18,200),G(WIND[0]),G(WIND[1]),sx=0.8).resize((512,768),Image.LANCZOS),'wind')
sh=L('sheet');A=np.array(sh)[...,3];names=[['orb','feather_a','feather_b'],['bolt','pillar','rays']]
for r,(y0,y1) in enumerate([(0,440),(440,A.shape[0])]):
    m=np.zeros_like(A,bool);m[y0:y1]=A[y0:y1]>40;lab,k=ndi.label(m);sz=ndi.sum(m,lab,range(1,k+1))
    big=sorted(np.argsort(sz)[-3:]+1,key=lambda i:np.nonzero(lab==i)[1].mean())
    for i,n in zip(big,names[r]):
        ys,xs=np.nonzero(lab==i);x0,x1,yy0,yy1=xs.min()-8,xs.max()+9,ys.min()-8,ys.max()+9
        c=np.array(sh.crop((x0,yy0,x1,yy1)));mk=ndi.binary_dilation(lab[yy0:yy1,x0:x1]==i,iterations=8) if x0>=0 and yy0>=0 else None
        if mk is not None and mk.shape==c.shape[:2]:c[...,3]=np.where(mk,c[...,3],0)
        im=Image.fromarray(c);sc=min(1,256/max(im.size));im=im.resize((max(1,round(im.width*sc)),max(1,round(im.height*sc))),Image.LANCZOS)
        save(im,n)

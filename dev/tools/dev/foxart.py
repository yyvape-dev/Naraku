"""ユズナミキの通常攻撃のVFX（狐火）を焼く。使い方: python3 -I tools/dev/foxart.py cardart assets
   元画像 cardart/src_vfx_fox_{back,arc,head,tail,flash,burst}.webp（ChatGPT作・透過）→ assets/vfx_fox_*.webp
   back/arc は下敷き（guide 1024×1536、キャラは ox=135, oy=709, 3倍）の線に合わせて、炎の両端を測った端点へ回転・拡大で寄せ直す。
   出力は下敷きの座標のまま 0.5 倍（512×768）。ゲーム側は FOXV の ox/oy/S で背面スプライトのマスの座標へ直す"""
import sys,json
from PIL import Image
import numpy as np
src,dst=sys.argv[1],sys.argv[2]
tr=json.load(open(f'{src}/fox_track.json'));OX,OY,S=135,709,3
G=lambda p:np.array([OX+p[0]*S,OY+p[1]*S],float)
L=lambda k:Image.open(f'{src}/src_vfx_fox_{k}.webp').convert('RGBA')
def ends(im,d):
    a=np.array(im)[...,3];ys,xs=np.nonzero(a>60);P=np.stack([xs,ys],1).astype(float);pr=P@d
    lo=P[pr<=np.percentile(pr,0.4)].mean(0);hi=P[pr>=np.percentile(pr,99.6)].mean(0);return lo,hi
def fit(im,g0,g1,over0=0.0,over1=0.0):
    d=(g1-g0)/np.linalg.norm(g1-g0);a,b=ends(im,d)          # a=始まり側、b=終わり側（炎の頭）
    t0=g0-(g1-g0)*over0;t1=g1+(g1-g0)*over1                  # 尾は線より少し外へはみ出させてよい
    v=b-a;w=t1-t0;s=np.linalg.norm(w)/np.linalg.norm(v);ang=np.arctan2(w[1],w[0])-np.arctan2(v[1],v[0])
    c,sn=np.cos(ang)*s,np.sin(ang)*s
    # 出力の点 q を入力の点へ戻す逆変換（PIL の AFFINE は出力→入力）
    M=np.array([[c,-sn],[sn,c]]);Mi=np.linalg.inv(M);off=a-Mi@t0
    out=im.transform((1024,1536),Image.AFFINE,(Mi[0,0],Mi[0,1],off[0],Mi[1,0],Mi[1,1],off[1]),Image.BICUBIC)
    print('scale',round(s,3),'rot',round(np.degrees(ang),1));return out
def save(im,n):im.save(f'{dst}/vfx_fox_{n}.webp','WEBP',quality=88,method=6);print(n,im.size)
bk=tr['back'];save(fit(L('back'),G(bk[0]),G(bk[-1]),0.35,0.0).resize((512,768),Image.LANCZOS),'back')
wd=tr['windup'];save(fit(L('arc'),G(wd[0]),G(wd[-1]),0.05,0.08).resize((512,768),Image.LANCZOS),'arc')
def sq(im,n,size):
    a=np.array(im)[...,3];ys,xs=np.nonzero(a>6);cx,cy=(xs.min()+xs.max())/2,(ys.min()+ys.max())/2;r=max(xs.max()-xs.min(),ys.max()-ys.min())/2+6
    save(im.crop((int(cx-r),int(cy-r),int(cx+r),int(cy+r))).resize((size,size),Image.LANCZOS),n)
sq(L('head'),'head',192);sq(L('flash'),'flash',192);sq(L('burst'),'burst',256)
t=L('tail');a=np.array(t)[...,3];ys,xs=np.nonzero(a>6);t=t.crop((0,max(0,ys.min()-6),t.width,min(t.height,ys.max()+6)))
save(t.resize((640,round(t.height*640/t.width)),Image.LANCZOS),'tail')

"""アベニウスの通常攻撃のVFX（蒼い月光と稲妻）を焼く。使い方: python3 -I tools/dev/bluart.py cardart assets
   元画像 cardart/src_vfx_blue_{charge,slash,sheet}.webp（ChatGPT作・透過）→ assets/vfx_blue_*.webp
   charge：剣身にまとう稲妻とオーラ。描かれた帯の軸を測って縦にまっすぐ直す（上＝切っ先、下＝柄）。ゲーム側でコマごとに柄→切っ先へ回して貼る
   slash ：三日月の残像。下敷き（1024×1536、キャラは ox=5, oy=536 の2.2倍）の線の両端（右上の始まり・左下の終わり）へ回転・拡大で寄せ、0.5倍で保存
   sheet ：4×2のシート。1行目＝溜めの放電(orb)・命中の閃き(hit)・飛ぶ三日月(moon)・稲妻の一筋(bolt)、2行目＝散る火花の4コマ(spark)"""
import sys,json
from PIL import Image
import numpy as np
src,dst=sys.argv[1],sys.argv[2]
tr=json.load(open(f'{src}/blue_track.json'));gd=tr['guide'];OX,OY,S=gd['ox'],gd['oy'],gd['scale']
G=lambda p:np.array([OX+p[0]*S,OY+p[1]*S],float)
L=lambda k:Image.open(f'{src}/src_vfx_blue_{k}.webp').convert('RGBA')
def save(im,n,q=88):im.save(f'{dst}/vfx_blue_{n}.webp','WEBP',quality=q,method=6);print(n,im.size)
def pts(im,t=60):a=np.array(im)[...,3];ys,xs=np.nonzero(a>t);return np.stack([xs,ys],1).astype(float)
def affine(im,a,b,t0,t1,size):
    v=b-a;w=t1-t0;s=np.linalg.norm(w)/np.linalg.norm(v);ang=np.arctan2(w[1],w[0])-np.arctan2(v[1],v[0])
    c,sn=np.cos(ang)*s,np.sin(ang)*s;M=np.array([[c,-sn],[sn,c]]);Mi=np.linalg.inv(M);off=a-Mi@t0
    print(' scale',round(s,3),'rot',round(np.degrees(ang),1))
    return im.transform(size,Image.AFFINE,(Mi[0,0],Mi[0,1],off[0],Mi[1,0],Mi[1,1],off[1]),Image.BICUBIC)
# --- charge：主軸（PCA）の両端。明るい端＝切っ先
ch=L('charge');P=pts(ch);m=P.mean(0);u,sv,vt=np.linalg.svd(P-m,full_matrices=False);d=vt[0];pr=(P-m)@d
e0=P[pr<=np.percentile(pr,0.3)].mean(0);e1=P[pr>=np.percentile(pr,99.7)].mean(0)
A=np.array(ch).astype(float);lum=lambda p:A[max(0,int(p[1])-40):int(p[1])+40,max(0,int(p[0])-40):int(p[0])+40,:3].mean()
tip,hilt=(e0,e1) if lum(e0)>lum(e1) else (e1,e0);print('charge tip',tip.round(),'hilt',hilt.round())
Lb=np.linalg.norm(tip-hilt);H=1024;Wd=320  # 縦の帯：切っ先を上端から 12%、柄を下端から 4% に置く
band=affine(ch,hilt,tip,np.array([Wd/2,H*0.96]),np.array([Wd/2,H*0.12]),(Wd,H))
save(band.resize((Wd//2,H//2),Image.LANCZOS),'aura')
# --- slash：右端（始まり）と下端（終わり）
sl=L('slash');P=pts(sl);s0=P[P[:,0]>=np.percentile(P[:,0],99.7)].mean(0);s1=P[P[:,1]>=np.percentile(P[:,1],99.7)].mean(0)
print('slash start',s0.round(),'end',s1.round())
g=tr['slash'];out=affine(sl,s0,s1,G(g[0]),G(g[-1]),(1024,1536))
save(out.resize((512,768),Image.LANCZOS),'slash')
# --- sheet：区画ごとに切り出し（隣のにじみは捨てる）
sh=L('sheet')
def cut(box):
    c=sh.crop(box);a=np.array(c)[...,3];ys,xs=np.nonzero(a>8);return c.crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1))
def sq(im,n,size):
    w,h=im.size;r=max(w,h);o=Image.new('RGBA',(r+12,r+12));o.alpha_composite(im,((r+12-w)//2,(r+12-h)//2));save(o.resize((size,size),Image.LANCZOS),n)
sq(cut((30,20,440,470)),'orb',192);sq(cut((445,15,910,480)),'hit',224)
mo=cut((912,60,1395,460));save(mo.resize((256,round(mo.height*256/mo.width)),Image.LANCZOS),'moon')
bo=cut((1440,0,1750,530));save(bo.resize((round(bo.width*384/bo.height),384),Image.LANCZOS),'bolt')
fr=[cut(b) for b in [(30,470,450,887),(470,470,895,887),(905,470,1360,887),(1370,470,1774,887)]]
C=192;strip=Image.new('RGBA',(C*4,C))
for i,f in enumerate(fr):
    k=C/max(fr[0].size)*0.98;f=f.resize((max(1,round(f.width*k)),max(1,round(f.height*k))),Image.LANCZOS);strip.alpha_composite(f,(i*C+(C-f.width)//2,(C-f.height)//2))
save(strip,'spark')

"""VFXの下敷き（ChatGPTに渡す「この線に沿って描いて」の画像）を作る。
   使い方: python3 -I tools/dev/vfxguide.py <キャラ> <コマ番号(1始まり)> <出力png> "x,y x,y x,y …" [size=1024x1536] [scale=3]
   点は背面スプライトの元のマス（assets/<キャラ>.json の cw×ch）の座標。先頭→末尾が動きの向き（末尾に矢じり）。
   灰色の地にキャラを scale 倍で下寄せ（縦長）または中央（横長）に置き、水色の太線を引く。置いた位置 ox,oy を表示する（焼き直しで使う）"""
import sys,json,math
from PIL import Image,ImageDraw
import numpy as np
ch_id,fi,out,pts=sys.argv[1],int(sys.argv[2])-1,sys.argv[3],[tuple(map(float,p.split(','))) for p in sys.argv[4].split()]
opt=dict(a.split('=') for a in sys.argv[5:]);W,H=map(int,opt.get('size','1024x1536').split('x'));S=float(opt.get('scale',3))
m=json.load(open(f'assets/{ch_id}.json'));cw,ch=m['cw'],m['ch'];sh=Image.open(f'assets/{ch_id}.webp').convert('RGBA')
ox=int((W-cw*S)/2);oy=int(H-ch*S-20) if H>W else int((H-ch*S)/2+40)
def cr(p,n=24):
    P=[p[0]]+p+[p[-1]];o=[]
    for i in range(1,len(P)-2):
        p0,p1,p2,p3=[np.array(P[j],float) for j in (i-1,i,i+1,i+2)]
        for t in np.linspace(0,1,n,endpoint=False):o.append(0.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t**3))
    o.append(np.array(P[-2],float));return o
im=Image.new('RGB',(W,H),(128,128,128));f=sh.crop((fi*cw,0,fi*cw+cw,ch)).resize((int(cw*S),int(ch*S)),Image.LANCZOS);im.paste(f,(ox,oy),f)
d=ImageDraw.Draw(im);C=tuple(int(opt.get('col','00C8FF')[i:i+2],16) for i in (0,2,4));q=[(ox+x*S,oy+y*S) for x,y in (cr(pts) if len(pts)>2 else pts)]
d.line(q,fill=C,width=10,joint='curve');(x1,y1),(x2,y2)=q[max(0,len(q)-5)],q[-1];a=math.atan2(y2-y1,x2-x1)
for s in (2.6,-2.6):d.line([(x2,y2),(x2+40*math.cos(a+s),y2+40*math.sin(a+s))],fill=C,width=10)
im.save(out);print(out,'ox',ox,'oy',oy,'scale',S)

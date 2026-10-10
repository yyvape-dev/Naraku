"""ラナの通常攻撃のVFX（赤黒い斬撃・軌跡・命中・散る靄）を焼く。
   使い方: python3 -I tools/dev/lanaart.py cardart assets
   元画像 cardart/src_vfx_lana_{slash,trail,hit,smoke}.webp（ChatGPT作・透過）→ assets/vfx_lana_*.webp
   slash：下敷き（guide 1536×1024）の座標のまま使うので切り抜かず縮小だけ（0.5倍）。lana_track.json の guide と対応
   trail：帯の上下の余白だけ切る（左右は端まで使う）／hit：正方形に切って256／smoke：横4コマを等幅のマスに並べ直す"""
import sys,os,json
from PIL import Image
import numpy as np
src,dst=sys.argv[1],sys.argv[2]
L=lambda k:Image.open(f'{src}/src_vfx_lana_{k}.webp').convert('RGBA')
def bbox(im,th=6):
    a=np.array(im)[...,3];ys,xs=np.nonzero(a>th);return xs.min(),ys.min(),xs.max()+1,ys.max()+1
def save(im,name):im.save(f'{dst}/vfx_{name}.webp','WEBP',quality=88,method=6,exact=False);print(name,im.size,os.path.getsize(f'{dst}/vfx_{name}.webp')//1024,'KB')
# 斬撃：下敷きと同じ座標系のまま0.5倍（768×512）
s=L('slash');save(s.resize((768,512),Image.LANCZOS),'lana_slash')
# 軌跡：上下の余白を切る（左右はそのまま）→ 幅768
t=L('trail');x0,y0,x1,y1=bbox(t);pad=8;t=t.crop((0,max(0,y0-pad),t.width,min(t.height,y1+pad)))
save(t.resize((768,round(t.height*768/t.width)),Image.LANCZOS),'lana_trail')
# 命中：中心を保って正方形に切る
h=L('hit');x0,y0,x1,y1=bbox(h);cx,cy=(x0+x1)/2,(y0+y1)/2;r=max(x1-x0,y1-y0)/2+6
h=h.crop((int(cx-r),int(cy-r),int(cx+r),int(cy+r)));save(h.resize((256,256),Image.LANCZOS),'lana_hit')
# 靄：4コマ。列ごとに不透明の範囲を探して切り出し、中心をそろえて等幅のマスへ
m=L('smoke');a=np.array(m)[...,3];col=(a>8).any(0);W=m.width;q=W//4;cells=[]
for i in range(4):
    seg=m.crop((i*q,0,(i+1)*q,m.height));cells.append(seg)
bx=[bbox(c) for c in cells];hh=max(b[3] for b in bx)-min(b[1] for b in bx);ytop=min(b[1] for b in bx)
cw=max(b[2]-b[0] for b in bx)+16;chh=hh+16
sheet=Image.new('RGBA',(cw*4,chh),(0,0,0,0))
for i,(c,b) in enumerate(zip(cells,bx)):
    piece=c.crop((b[0],ytop-8,b[2],ytop+hh+8));sheet.paste(piece,(i*cw+(cw-piece.width)//2,0),piece)
k=360/cw;sheet=sheet.resize((round(sheet.width*k),round(sheet.height*k)),Image.LANCZOS);save(sheet,'lana_smoke')
json.dump({'smoke_cols':4},open(f'{dst}/../cardart/lana_vfx.json','w'))

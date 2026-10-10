"""街TOPのUI（ユーザーが外部AIで作った「文字を消したモック」と板・挿絵）を焼く。
   使い方: python3 -I tools/dev/townart.py cardart assets
   元: cardart/src_th_mock.webp（文字を消したモック 971×1619。下のUIだけを切り出す）
       cardart/src_th_plates.webp（マゼンタ背景：名札の板／日数の板（羅針盤）／資材の板）
       cardart/src_th_vig.webp（マゼンタ背景：施設の挿絵 3×2 ＝ 教会・酒場・廃屋／商店・鍛冶屋・宿屋）
       cardart/src_th_facicons.webp（施設アイコン 3×2）
   出力: assets/ui_th_{panel,tag,day,coin,cry,vig,ic}.webp。座標はソースの TH_DEF / THP と対応させること。"""
import sys
from PIL import Image, ImageFilter
import numpy as np, scipy.ndimage as nd
src,out=sys.argv[1],sys.argv[2]
L=lambda n:Image.open(f'{src}/src_th_{n}.webp')
def save(im,name,w=None):
    if w and w!=im.width: im=im.resize((w,round(im.height*w/im.width)),Image.LANCZOS)
    im.save(f'{out}/ui_th_{name}.webp',quality=90,alpha_quality=90,method=6); print(name,im.size)
def key(im):   # マゼンタ背景を透過に（npc_key.py と同じ方式）
    a0=np.asarray(im.convert('RGB')).astype(np.float32); R,G,B=a0[...,0],a0[...,1],a0[...,2]
    a=np.clip(((255-R)+G+(255-B)-70)/130,0,1)
    a=np.asarray(Image.fromarray((a*255).astype(np.uint8)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.6))).astype(np.float32)/255
    edge=np.asarray(Image.fromarray(((a<0.98)*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7))).astype(bool)
    ex=np.clip(np.minimum(R,B)-G,0,None)*edge
    return Image.fromarray(np.dstack([R-ex,G,B-ex,a*255]).clip(0,255).astype(np.uint8))
def bbox(im,th=8):
    a=np.asarray(im.getchannel('A'))>th; ys=np.where(a.any(1))[0]; xs=np.where(a.any(0))[0]; return im.crop((xs[0],ys[0],xs[-1]+1,ys[-1]+1))
# ---- 下のUI：モックの y1172〜下端。焼き込みの宿屋の挿絵は消し（x12〜162 を x260 の列で埋める）、上へはみ出す中央の飾りだけ残す
m=np.array(L('mock').convert('RGB')).astype(int); Y0,TOP=1172,1220
for x in range(12,163): m[TOP:1411,x]=m[TOP:1411,630]   # 外枠の内側の平らな列（カードの外）で埋める
reg=m[Y0:TOP]; R,G,B=reg[...,0],reg[...,1],reg[...,2]; lum=reg.mean(2); mx=reg.max(2); mn=reg.min(2); sat=(mx-mn)/np.maximum(mx,1)
cand=((R>95)&(sat>0.42)&(R-G>22)&(G>B))|(lum<34)
xs=np.arange(reg.shape[1])[None,:].repeat(reg.shape[0],0); ys=np.arange(reg.shape[0])[:,None].repeat(reg.shape[1],1)+Y0
cand&=(xs>=432)&(xs<=552)&((ys>=1197)|((xs>=462)&(xs<=522)))
lab,_=nd.label(cand); mask=np.isin(lab,[v for v in set(lab[-1].tolist()) if v])
mask=nd.binary_fill_holes(nd.binary_closing(mask,iterations=1))
for x in range(mask.shape[1]):
    c=np.where(mask[:,x])[0]
    if len(c): mask[c.min():,x]=True
al=np.zeros(m.shape[:2],np.uint8); al[TOP:]=255; al[Y0:TOP][mask]=255
al=np.array(Image.fromarray(al).filter(ImageFilter.GaussianBlur(0.7))); al[TOP:]=255
p=Image.fromarray(np.clip(m,0,255).astype(np.uint8)).convert('RGBA'); p.putalpha(Image.fromarray(al)); save(p.crop((0,Y0,p.width,p.height)),'panel')
# ---- 板（名札・日数・資材）
pl=key(L('plates')); a=np.asarray(pl.getchannel('A'))>8; rows=[(0,500),(500,950),(950,pl.height)]
parts=[bbox(pl.crop((0,y0,pl.width,y1))) for y0,y1 in rows]
save(parts[0],'tag',w=600); save(parts[1],'day',w=600)
r=parts[2]   # 資材の板は名札の板で作るので、金貨と結晶だけを抜き出す（「＋」は使わない：ユーザー決定）
def pick(x0,x1):
    q=r.crop((int(r.width*x0),0,int(r.width*x1),r.height)); qa=np.asarray(q.convert('RGB')).astype(int)
    mk=(qa.mean(2)>62)|((qa.max(2)-qa.min(2))>70); mk=nd.binary_opening(mk,iterations=1); mk=nd.binary_fill_holes(nd.binary_closing(mk,iterations=2))
    lab,n=nd.label(mk); sz=nd.sum(mk,lab,range(1,n+1)); mk=lab==(1+int(np.argmax(sz)))
    al=np.minimum(np.asarray(q.getchannel('A')),np.asarray(Image.fromarray((mk*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))))
    q.putalpha(Image.fromarray(al)); return bbox(q,20)
save(pick(0.06,0.22),'coin',w=90); save(pick(0.52,0.66),'cry',w=70)
# ---- 施設の挿絵（3×2）→ 1枚の帯（各 300×290、下端そろえ）
v=key(L('vig')); C=(300,290); strip=Image.new('RGBA',(C[0]*6,C[1]))
for i in range(6):
    cx,cy=i%3,i//3; c=bbox(v.crop((cx*512,cy*512,(cx+1)*512,(cy+1)*512)),40)
    k=min((C[0]-6)/c.width,(C[1]-4)/c.height); c=c.resize((round(c.width*k),round(c.height*k)),Image.LANCZOS)
    strip.alpha_composite(c,(i*C[0]+(C[0]-c.width)//2,C[1]-c.height-2))
save(strip,'vig')
# ---- 施設アイコン（名札用）
f=Image.open(f'{src}/src_th_facicons.webp').convert('RGBA'); ICB=[(112,78,443,476),(613,110,942,448),(1085,133,1448,440),(114,566,422,917),(575,572,959,914),(1078,615,1459,870)]
Cc=96; st=Image.new('RGBA',(Cc*6,Cc))
for i,(x0,y0,x1,y1) in enumerate(ICB):
    q=f.crop((x0,y0,x1+1,y1+1)); k=(Cc-6)/max(q.size); q=q.resize((round(q.width*k),round(q.height*k)),Image.LANCZOS); st.alpha_composite(q,(i*Cc+(Cc-q.width)//2,(Cc-q.height)//2))
save(st,'ic')

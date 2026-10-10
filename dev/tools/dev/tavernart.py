"""酒場の素材を焼く：cardart/src_tv_*.webp → assets/ui_tv_*.webp
   使い方: python3 -I tools/dev/tavernart.py cardart assets
   board（仲間表の板 1122:1402）/ detail（詳細画面の板 1040:1512）/ btn（コマンドの枠）/ chip（小さなボタンの枠）
   icons（icons1 の8個＋icons2 の7個を 4×4 に並べ直す。0交差剣 1吹き出し 2扉 3兜 4剣 5胸当て 6弓 7笏 8クナイ 9大剣 10聖印 11魔導書 12三日月の剣 13拳の盾 14宝珠）
   arna（頬杖のアルナ。肘の高さ＝元画像の上から790pxで水平に切る）"""
import sys, numpy as np
from PIL import Image, ImageFilter
src,dst=sys.argv[1],sys.argv[2]
def opaque(im):
    a=np.array(im.convert('RGBA'));al=a[...,3];al[al>=245]=255;a[al<10]=0;return Image.fromarray(a)
def bbox(im,th=20):
    al=np.array(im)[...,3];ys,xs=np.where(al>th);return im.crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1))
def fit(im,w):return im.resize((w,round(im.height*w/im.width)),Image.LANCZOS)
def key(im):  # マゼンタ(255,0,255)からの距離で抜く（npc_key.py と同じ方式。ピンクの髪を守る）
    a3=np.asarray(im.convert('RGB')).astype(np.float32);R,G,B=a3[...,0],a3[...,1],a3[...,2]
    a=np.clip(((255-R)+G+(255-B)-70)/130,0,1)
    A=Image.fromarray((a*255).astype(np.uint8)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.6));a=np.asarray(A).astype(np.float32)/255
    edge=np.asarray(Image.fromarray(((a<0.98)*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7))).astype(bool)
    ex=np.clip(np.minimum(R,B)-G,0,None)*edge
    return Image.fromarray(np.dstack([R-ex,G,B-ex,a*255]).clip(0,255).astype(np.uint8))
def save(im,k,q=86):im.save(f'{dst}/ui_tv_{k}.webp',quality=q,alpha_quality=90,method=6);print(k,im.size)
save(fit(opaque(Image.open(f'{src}/src_tv_board.webp')),780),'board')
save(fit(opaque(Image.open(f'{src}/src_tv_detail.webp')),780),'detail')
save(fit(bbox(opaque(Image.open(f'{src}/src_tv_btn.webp'))),600),'btn')
save(fit(bbox(opaque(Image.open(f'{src}/src_tv_chip.webp'))),480),'chip')
C=192;sheet=Image.new('RGBA',(C*4,C*4),(0,0,0,0));n=0
for f,cnt in [('icons1',8),('icons2',7)]:
    k=key(Image.open(f'{src}/src_tv_{f}.webp'));cw,ch=k.width/4,k.height/2
    for i in range(cnt):
        c=bbox(k.crop((round(i%4*cw),round(i//4*ch),round((i%4+1)*cw),round((i//4+1)*ch))),40)
        s=(C-16)/max(c.width,c.height);c=c.resize((max(1,round(c.width*s)),max(1,round(c.height*s))),Image.LANCZOS)
        sheet.alpha_composite(c,(n%4*C+(C-c.width)//2,n//4*C+(C-c.height)//2));n+=1
save(sheet,'icons',88)
ar=key(Image.open(f'{src}/src_tv_arna.webp')).crop((0,0,1340,790))
save(fit(ar,720),'arna',88)

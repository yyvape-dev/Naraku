"""シェリの通常攻撃のVFX（紫の魔力の光線と魔法陣）を焼く。使い方: python3 -I tools/dev/mageart.py cardart assets
   元画像 cardart/src_vfx_mage_{circle,beam,sheet}.webp（ChatGPT作・透過）→ assets/vfx_mage_*.webp
   すべて「黒地の加算用」に焼く：色×不透明度に、暗い紫の地（にじみの板）を落とす重みを掛ける。青に寄った色相は紫へ戻す（透過の縁の青い残り）
   circle：魔法陣（正方形 384）／beam：光線の帯（横長。右端＝先端）／sheet 3×2：orb（溜めの球）・flash（発射の閃光）・hit（命中の弾け）・glow（終点の残光）・shard（結晶の欠片）・mist（靄）"""
import sys
from PIL import Image
import numpy as np
src,dst=sys.argv[1],sys.argv[2]
L=lambda k:Image.open(f'{src}/src_vfx_mage_{k}.webp').convert('RGBA')
def light(im,lo=38,span=170,gam=1.25):
    a=np.array(im).astype(float);al=a[...,3:4]/255
    hsv=np.array(Image.fromarray(a[...,:3].astype(np.uint8)).convert('HSV')).astype(float)
    h=hsv[...,0];h=np.where((h>120)&(h<182),182,h);hsv[...,0]=h   # 青（〜256°）を紫（約257°以上）へ
    rgb=np.array(Image.fromarray(hsv.astype(np.uint8),'HSV').convert('RGB')).astype(float)
    lum=rgb.max(-1,keepdims=True);w=np.clip((lum-lo)/span,0,1)**gam
    out=np.clip(rgb*al*w,0,255).astype(np.uint8);return Image.fromarray(out,'RGB')
def bbox(im,t=6):
    a=np.array(im).max(-1);ys,xs=np.nonzero(a>t);return im.crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1))
def save(im,n,q=88):im.save(f'{dst}/vfx_mage_{n}.webp','WEBP',quality=q,method=6);print(n,im.size)
def sq(im,n,size,pad=0.04):
    w,h=im.size;r=int(max(w,h)*(1+pad));o=Image.new('RGB',(r,r));o.paste(im,((r-w)//2,(r-h)//2));save(o.resize((size,size),Image.LANCZOS),n)
sq(bbox(light(L('circle'),lo=30)),'circle',384)
bm=bbox(light(L('beam'),lo=34));save(bm.resize((768,round(bm.height*768/bm.width)),Image.LANCZOS),'beam')
sh=light(L('sheet'));W,H=sh.size;cw,ch=W//3,H//2
for i,(n,s) in enumerate([('orb',160),('flash',224),('hit',224),('glow',224),('shard',160),('mist',192)]):
    c,r=i%3,i//3;cell=bbox(sh.crop((c*cw,r*ch,c*cw+cw,r*ch+ch)))
    if n!='shard':sq(cell,n,s);continue
    # 結晶の欠片：1つずつに分ける（大きい順に4つ。残滓として1枚ずつ飛ばす）→ shard0〜3
    from scipy import ndimage as ndi
    a=np.array(cell).max(-1);lab,k=ndi.label(ndi.binary_closing(a>40,iterations=2));sz=ndi.sum(a>40,lab,range(1,k+1))
    for j,ix in enumerate(np.argsort(sz)[::-1][:4]):
        ys,xs=np.nonzero(ndi.binary_dilation(lab==ix+1,iterations=6));sq(cell.crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1)),f'shard{j}',64,0.1)

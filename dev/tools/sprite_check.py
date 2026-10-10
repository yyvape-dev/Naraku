"""焼いた味方の絵（assets/<名前>.webp）を確認する。
   使い方: python3 tools/sprite_check.py <名前> <出力.png> [clean]
     出力: 12コマを横6×2段に並べ、足元（緑）と左右の基準（青）の線を引いた確認画像。コマごとの 頭/腰/足 の左右位置と彩度・明るさも表示
     clean: 本体から離れた小さな欠片（光エフェクトの残りかす）を消して上書きする"""
import sys, json, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
if len(sys.argv)<3: raise SystemExit(__doc__)
name,out=sys.argv[1],sys.argv[2];A='assets'
J=json.load(open(f'{A}/{name}.json'));cw,ch,n=J['cw'],J['ch'],J['cols']
a=np.array(Image.open(f'{A}/{name}.webp').convert('RGBA'))
if 'clean' in sys.argv[3:]:
    for k in range(n):
        sub=a[:,k*cw:(k+1)*cw];al=sub[...,3]>20;lab,m=ndi.label(al,structure=np.ones((3,3)))
        if m>1:
            s=ndi.sum(al,lab,range(1,m+1));main=1+int(np.argmax(s));sub[(lab!=main)&al]=0
            print(f'{k+1}コマ目: 欠片を消した',[int(v) for i,v in enumerate(s) if i+1!=main])
    Image.fromarray(a).save(f'{A}/{name}.webp',quality=90,method=6)
for k in range(n):
    f=a[:,k*cw:(k+1)*cw];al=f[...,3]>128;top=np.where(al)[0].min()
    med=lambda r:float(np.median(np.where(al[r])[1])) if al[r].any() else -1
    H=np.array(Image.fromarray(f[...,:3]).convert('HSV')).astype(float)[ndi.binary_erosion(al,iterations=2)]
    print(f'{k+1:2d}コマ 頭{med(slice(top+15,top+55)):6.1f} 腰{med(slice(top+90,top+150)):6.1f} 足{med(slice(J["ay"]-25,J["ay"])):6.1f}  彩度{H[:,1].mean():5.1f} 明るさ{H[:,2].mean():5.1f}')
cols=6;rows=(n+cols-1)//cols;im=Image.fromarray(a)
o=Image.new('RGBA',(cw*cols,ch*rows),(40,40,48,255));d=ImageDraw.Draw(o)
for k in range(n):
    r,c=divmod(k,cols);o.alpha_composite(im.crop((k*cw,0,(k+1)*cw,ch)),(c*cw,r*ch))
for k in range(n):
    r,c=divmod(k,cols);d.line([(c*cw+J['ax'],r*ch),(c*cw+J['ax'],r*ch+ch)],fill=(0,200,255,110));d.text((c*cw+4,r*ch+4),str(k+1),fill=(255,255,0,255))
for r in range(rows): d.line([(0,r*ch+J['ay']),(cw*cols,r*ch+J['ay'])],fill=(0,255,0,255))
o.save(out);print('確認画像',out)

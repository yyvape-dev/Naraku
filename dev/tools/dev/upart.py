"""強化の札の絵を 4:5 に整えて assets/upart_<キー>.webp にする。使い方: python3 upart.py <出力フォルダ> <キー>=<画像>[:拡大率] …"""
import sys, os
from PIL import Image
out=sys.argv[1]
for a in sys.argv[2:]:
    k,v=a.split('=',1); path,_,z=v.partition(':'); z=float(z or 1)
    im=Image.open(path).convert('RGB'); w,h=im.size
    cw=min(w,h*4/5)/z; ch=cw*5/4; x=(w-cw)/2; y=(h-ch)/2          # 中央を 4:5 で切り出す（拡大率ぶん内側へ）
    im=im.crop((round(x),round(y),round(x+cw),round(y+ch))).resize((288,360),Image.LANCZOS)
    p=f'{out}/upart_{k}.webp'; im.save(p,quality=80,method=6); print(k,(w,h),os.path.getsize(p)//1024,'KB')

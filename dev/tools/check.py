"""焼き上がったアトラスを暗い背景に並べ、足元の基準線(緑)を重ねた確認画像を作る。
   使い方: python3 check.py <出力png> <アトラス名…> [dir=assets] [w=1400]
   できた画像は必ず目で見る：欠け・隣のコマの写り込み・ピンクの縁・足元が線に乗っているか。"""
import sys, json
from PIL import Image, ImageDraw
opt=dict(a.split('=') for a in sys.argv[2:] if '=' in a); names=[a for a in sys.argv[2:] if '=' not in a]
d=opt.get('dir','assets'); Wt=int(opt.get('w',1400)); rows=[]
for n in names:
    im=Image.open(f'{d}/{n}.webp').convert('RGBA'); m=json.load(open(f'{d}/{n}.json'))
    bg=Image.new('RGBA',im.size,(24,20,16,255)); bg.alpha_composite(im); g=ImageDraw.Draw(bg)
    g.line([(0,m['ay']),(im.width,m['ay'])],fill=(60,255,110,255))
    for f in range(m['cols']):
        x=f*m['cw']; g.line([(x,0),(x,im.height)],fill=(80,80,80,255)); g.line([(x+m['ax'],m['ay']-10),(x+m['ax'],m['ay']+6)],fill=(60,255,110,255))
    rows.append(bg.resize((Wt,max(1,round(im.height*Wt/im.width))),Image.LANCZOS).convert('RGB'))
out=Image.new('RGB',(Wt,sum(r.height for r in rows))); y=0
for r in rows: out.paste(r,(0,y)); y+=r.height
out.save(sys.argv[1]); print('saved',sys.argv[1],out.size)

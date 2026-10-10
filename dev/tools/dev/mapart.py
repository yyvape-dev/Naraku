"""探索の盤上の素材（メダルと駒）を、外部AIで作ったマゼンタ背景のシートから切り出して assets に置く。
   使い方: python3 tools/dev/mapart.py <メダルのシート.png> <駒のシート.png> [素材フォルダ=assets] [確認用png]
   メダル: 3×3（左上から 戦闘・強敵・宝箱／異変・焚き火・キャンプ／ボス・入口・不明）→ ui_medals.webp（1マス192px、円で抜く。少し暗く落とす）
   駒:     横5体（狐耳・女騎士・シスター・魔術師・蒼剣士）→ ui_pieces.webp（5コマ等幅。台座の底の中央を、各コマの下端中央にそろえる）"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance
from scipy import ndimage
med_p,pc_p=sys.argv[1],sys.argv[2]; out=sys.argv[3] if len(sys.argv)>3 else 'assets'; chk=sys.argv[4] if len(sys.argv)>4 else None
def key(im):  # マゼンタを透過にして、輪郭に残るにじみを抜く
    a=np.asarray(im.convert('RGB')).astype(np.int32); r,g,b=a[...,0],a[...,1],a[...,2]
    m=np.minimum(r,b)-g; sc=np.clip((m-40)/90.0,0,1)*(np.abs(r-b)<90)
    ex=np.clip(m,0,255)*(sc>0.02)
    return Image.fromarray(np.dstack([np.clip(r-ex*0.9,0,255),g,np.clip(b-ex*0.9,0,255),255*(1-sc)]).astype(np.uint8),'RGBA')
# ---- メダル ----
med=Image.open(med_p).convert('RGB'); W,H=med.size; mk=np.asarray(key(med))[...,3]>128; C=192
sheet=Image.new('RGBA',(C*3,C*3),(0,0,0,0)); info=[]
for r in range(3):
    for c in range(3):
        x0,y0=c*W//3,r*H//3; sub=mk[y0:(r+1)*H//3,x0:(c+1)*W//3]; ys,xs=np.nonzero(sub)
        cx,cy,rad=xs.mean()+x0,ys.mean()+y0,np.sqrt(sub.sum()/np.pi)*0.975   # 面積から半径を出す（外に落ちた影に引きずられない）
        R=int(round(rad)); im=med.crop((int(round(cx))-R,int(round(cy))-R,int(round(cx))+R,int(round(cy))+R)).convert('RGBA')
        m2=Image.new('L',(im.width*3,im.height*3),0); ImageDraw.Draw(m2).ellipse((2,2,im.width*3-3,im.height*3-3),fill=255); im.putalpha(m2.resize(im.size,Image.LANCZOS))
        rgb=ImageEnhance.Color(ImageEnhance.Brightness(im.convert('RGB')).enhance(0.86)).enhance(0.9)   # UIのくすんだ金に合わせて少し落とす
        im=Image.merge('RGBA',(*rgb.split(),im.split()[3])).resize((C,C),Image.LANCZOS); sheet.alpha_composite(im,(c*C,r*C)); info.append(R)
sheet.save(f'{out}/ui_medals.webp',quality=86,alpha_quality=90,method=6); print('medals radius(px)',info)
# ---- 駒 ----
pk=key(Image.open(pc_p)); a=np.asarray(pk); solid=a[...,3]>128
lab,n=ndimage.label(solid); sizes=ndimage.sum(solid,lab,range(1,n+1)); big=[i+1 for i in np.argsort(sizes)[::-1][:5]]
objs=sorted(big,key=lambda i:ndimage.center_of_mass(lab==i)[1]); print('components',n,'top5',[int(sizes[i-1]) for i in objs])
cut=[]
for i in objs:
    m=lab==i; m=ndimage.binary_dilation(m,iterations=3)&(a[...,3]>0)   # 輪郭の半透明も拾う（隣の駒は拾わない）
    for j in objs:
        if j!=i: m&=~ndimage.binary_dilation(lab==j,iterations=2)
    ys,xs=np.nonzero(m); y0,y1,x0,x1=ys.min(),ys.max()+1,xs.min(),xs.max()+1
    im=np.array(a[y0:y1,x0:x1]); im[...,3]=np.where(m[y0:y1,x0:x1],im[...,3],0)
    base=np.nonzero(m[y1-int((y1-y0)*0.06):y1].any(axis=0))[0]; ax=(base.min()+base.max())/2-x0   # 台座の底の中央
    cut.append((Image.fromarray(im,'RGBA'),ax,y1-y0))
hmax=max(c[2] for c in cut); half=max(max(c[1],c[0].width-c[1]) for c in cut); cw=int(np.ceil(half))*2+4; SC=300/hmax; CW,CH=int(round(cw*SC)),300
strip=Image.new('RGBA',(CW*5,CH),(0,0,0,0))
for k,(im,ax,h) in enumerate(cut):
    cell=Image.new('RGBA',(cw,hmax),(0,0,0,0)); cell.alpha_composite(im,(int(round(cw/2-ax)),hmax-h)); strip.alpha_composite(cell.resize((CW,CH),Image.LANCZOS),(k*CW,0))
strip.save(f'{out}/ui_pieces.webp',quality=88,alpha_quality=92,method=6); print('pieces cell',CW,'x',CH,'heights',[c[2] for c in cut])
if chk:
    bg=Image.new('RGBA',(max(C*3,CW*5),C*3+CH+10),(34,28,24,255)); bg.alpha_composite(sheet,(0,0)); bg.alpha_composite(strip,(0,C*3+10)); bg.convert('RGB').save(chk)

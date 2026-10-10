"""鍛冶屋の画面の素材（ユーザー提供の枠6枚＋装備アイコン4×4）を assets/ui_sm_*.webp に焼く。
   使い方: python3 -I tools/dev/smithart.py <cardart> <assets>
   sheet=下の板の木箱の枠（左右の柱の帯 y368〜380 だけを縦に伸ばす 9-slice）/ stone=板の内側の石の地 / card=右上の札（比率固定）/
   row=一覧の1行（中央の飾りを保ったまま、左右の無地の梁を横に伸ばして 5.6:1 に）/ tab=タブ・ボタン・ログ欄（9-slice）/
   socket=宝珠をはめる円枠 / slot=素材の四角枠 / icons=装備アイコン（マゼンタ抜き。160px角×4×4）"""
import sys, numpy as np
from PIL import Image, ImageFilter
S,D=sys.argv[1],sys.argv[2]
def ld(n): return Image.open(f'{S}/src_sm_{n}.webp').convert('RGBA')
def bb(im,t=40): return im.getchannel('A').point(lambda a:255 if a>t else 0).getbbox()
def sv(im,n,q=86): im.save(f'{D}/ui_sm_{n}.webp',quality=q,alpha_quality=90,method=6); print(n,im.size)
# 下の板
im=ld('sheet');b=bb(im);c=im.crop(b);k=1100/c.width;sv(c.resize((1100,round(c.height*k)),Image.LANCZOS),'sheet')
print(' sheet slice top',round((368-b[1])*k),'bottom',round((b[3]-380)*k),'left',round((165-b[0])*k),'right',round((b[2]-1370)*k),'k(元→素材)',round(k,4),'元bbox',b)
st=im.crop((200,280,1330,750)).convert('RGB');st=st.resize((640,round(640*st.height/st.width)),Image.LANCZOS);st.save(f'{D}/ui_sm_stone.webp',quality=70,method=6);print('stone',st.size)
# 右上の札
im=ld('card');b=bb(im);c=im.crop(b);sv(c.resize((720,round(c.height*720/c.width)),Image.LANCZOS),'card');print(' card bbox',b)
# 一覧の1行
im=ld('row');b=bb(im);c=im.crop(b);W,H=c.size;tw=round(H*5.6);ex=tw-W
s1=(456-b[0],652-b[0]);s2=(1520-b[0],1737-b[0]);add=ex//2
parts=[c.crop((0,0,s1[0],H)),c.crop((s1[0],0,s1[1],H)).resize((s1[1]-s1[0]+add,H),Image.LANCZOS),c.crop((s1[1],0,s2[0],H)),
       c.crop((s2[0],0,s2[1],H)).resize((s2[1]-s2[0]+ex-add,H),Image.LANCZOS),c.crop((s2[1],0,W,H))]
o=Image.new('RGBA',(tw,H));x=0
for p in parts:o.alpha_composite(p,(x,0));x+=p.width
sv(o.resize((round(tw*150/H),150),Image.LANCZOS),'row');print(' row bbox',b)
# タブ
im=ld('tab');b=bb(im);c=im.crop(b);k=120/c.height;sv(c.resize((round(c.width*k),120),Image.LANCZOS),'tab')
print(' tab slice top',round((295-b[1])*k),'bottom',round((b[3]-515)*k),'left',round((245-b[0])*k),'right',round((b[2]-1680)*k))
for n,w in (('socket',200),('slot',140)):
    im=ld(n);b=bb(im);c=im.crop(b);sv(c.resize((w,round(c.height*w/c.width)),Image.LANCZOS),n);print(' ',n,'bbox',b)
# アイコン（マゼンタからの距離で透明度。npc_key.py と同じ式）
im=np.asarray(Image.open(f'{S}/src_sm_icons.webp').convert('RGB')).astype(np.float32)
R,G,B=im[...,0],im[...,1],im[...,2];d=(255-R)+G+(255-B);a=np.clip((d-70)/(200-70),0,1)
A=Image.fromarray((a*255).astype(np.uint8)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.6));a=np.asarray(A).astype(np.float32)/255
edge=np.asarray(Image.fromarray(((a<0.98)*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7))).astype(bool)
ex=np.clip(np.minimum(R,B)-G,0,None)*edge
I=Image.fromarray(np.dstack([R-ex,G,B-ex,a*255]).clip(0,255).astype(np.uint8))
# 連結成分ごとに重心の入るマスへ振り分ける（隣のマスへはみ出た鎖などを正しいマスに戻す）
from scipy import ndimage
lab,n=ndimage.label(a>0.25);cw=I.width/4;ch=I.height/4;C=160;sheet=Image.new('RGBA',(C*4,C*4));arr=np.asarray(I)
cells={}
for i,sl in enumerate(ndimage.find_objects(lab),1):
    m=lab[sl]==i;area=int(m.sum())
    if area<40:continue
    cy,cx=ndimage.center_of_mass(lab==i)
    cells.setdefault((int(cx//cw),int(cy//ch)),[]).append(i)
mask_all=ndimage.binary_dilation(lab>0,iterations=3)
for (ci,cj),ids in cells.items():
    m=ndimage.binary_dilation(np.isin(lab,ids),iterations=3)
    ys,xs=np.where(m);x0,x1,y0,y1=xs.min(),xs.max()+1,ys.min(),ys.max()+1
    sub=arr[y0:y1,x0:x1].copy();sub[...,3]=(sub[...,3]*m[y0:y1,x0:x1]).astype(np.uint8)
    cell=Image.fromarray(sub);s_=148/max(cell.size);cell=cell.resize((max(1,round(cell.width*s_)),max(1,round(cell.height*s_))),Image.LANCZOS)
    sheet.alpha_composite(cell,(ci*C+(C-cell.width)//2,cj*C+(C-cell.height)//2))
sv(sheet,'icons',88)

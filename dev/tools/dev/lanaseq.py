"""ラナの超必殺（天地開闢）の連番エフェクト（ユーザーが動画AIから選んだ48コマ・黒背景・416×752）→ assets
   使い方: python3 -I tools/dev/lanaseq.py <48コマのPNGまたはwebpのフォルダ> [cardart/lana_ult_seq] [assets]
   1コマにつき2枚を焼く（ゲーム側は「抜き」を普通に重ねて戦場を暗くし、その上に「光」を加算で足す＝黒地に置いた元の絵と同じ見え方になる）:
     seq_lanaU_NN.webp  ＝光（黒背景のまま・不透明・416×752。加算で重ねる）
     seq_lanaUm_NN.webp ＝抜き（黒一色＋不透明度だけ・半分の大きさ）。加算だけだと黒い岩が「穴」になって戦場が透けるので、岩と光の芯の所だけ戦場を隠す
       ・光（赤〜白）＝明るさがそのまま不透明度 ・灰色の岩＝色味の無い画素は不透明に寄せる
       ・光に囲まれた黒い岩＝まわりの明るさ（ぼかし）から不透明度をもらう → 黒いまま残る
   端は少しだけぼかす（下端のぼかしはゲーム側で防衛線に合わせて掛ける）。元絵は cardart/lana_ult_seq/NN.webp（q92）に残す"""
import sys,os,glob
import numpy as np
from PIL import Image,ImageFilter
src=sys.argv[1];keep=sys.argv[2] if len(sys.argv)>2 else 'cardart/lana_ult_seq';out=sys.argv[3] if len(sys.argv)>3 else 'assets'
fs=sorted(glob.glob(f'{src}/*.png'))or sorted(glob.glob(f'{src}/*.webp'))
assert len(fs)==48,len(fs)
os.makedirs(keep,exist_ok=True)
def ss(x,a,b):
    u=np.clip((x-a)/(b-a),0,1);return u*u*(3-2*u)
tot=0
for i,f in enumerate(fs):
    im=Image.open(f).convert('RGB')
    if os.path.abspath(os.path.dirname(f))!=os.path.abspath(keep):im.save(f'{keep}/{i+1:02d}.webp',quality=92,method=4)
    a=np.asarray(im).astype(np.float32)/255
    mx=a.max(axis=2);mn=a.min(axis=2);sat=np.where(mx>0.02,(mx-mn)/np.maximum(mx,1e-3),0)
    nb=np.asarray(Image.fromarray((mx*255).astype('uint8')).filter(ImageFilter.GaussianBlur(7))).astype(np.float32)/255
    rock=ss(nb,0.30,0.62)*0.92
    al=np.maximum(mx,np.maximum(rock,(1-sat)**1.5*ss(mx,0.10,0.30)*0.9))
    al=np.where(mx<0.035,np.minimum(al,rock),al) # 黒背景のざらつきは消す
    h,w=mx.shape;ey=np.ones(h);ex=np.ones(w);m=int(h*0.05);n=int(w*0.05)
    ey[:m]=np.linspace(0,1,m);ey[h-m:]=np.linspace(1,0,m);ex[:n]=np.linspace(0,1,n);ex[w-n:]=np.linspace(1,0,n)
    e=ey[:,None]*ex[None,:]
    rgb=np.where(mx[...,None]<0.035,0,a)*e[...,None]
    p=f'{out}/seq_lanaU_{i+1:02d}.webp';Image.fromarray((rgb*255+0.5).astype('uint8'),'RGB').save(p,quality=78,method=4);tot+=os.path.getsize(p)
    mt=np.zeros((h,w,4),'uint8');mt[...,3]=(al*e*255+0.5).astype('uint8')
    p=f'{out}/seq_lanaUm_{i+1:02d}.webp';Image.fromarray(mt,'RGBA').resize((w//2,h//2),Image.BILINEAR).save(p,quality=50,alpha_quality=45,method=4);tot+=os.path.getsize(p)
print('frames',len(fs),'size',im.size,'total',round(tot/1024),'KB')

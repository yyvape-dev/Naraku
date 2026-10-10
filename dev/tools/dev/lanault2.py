"""ラナの超必殺（天地開闢）の全画面エフェクト（ユーザーがChatGPTで描いた透過PNG・1024×1536）→ assets
   使い方: python3 -I tools/dev/lanault2.py cardart/lana_ult2
   01〜08＝4段階×（床の層, 上の層）。04 は 03 と同じ絵が届いたので使わない（2段階目の上の層は1段階目の絵を流用）。09〜12＝ラナの体にまとうオーラ（4コマ）
   出力：vfx_lanaU_f1..f4（床）/ vfx_lanaU_t1,t3,t4（上）は 768×1152、vfx_lanaU_a1..a4（オーラ）は 512×768。webp q82"""
import sys,os
from PIL import Image
d=sys.argv[1]
def put(src,name,size):
    im=Image.open(f'{d}/{src}.webp').convert('RGBA').resize(size,Image.LANCZOS)
    if name[0] in 'ft': # 下端と上端をぼかす（絵の端が戦場の中で横一直線の切れ目に見えないように）
        import numpy as np
        a=np.asarray(im).copy();h=a.shape[0];g=np.ones(h);b=int(h*0.14);tp=int(h*0.06)
        g[h-b:]=np.linspace(1,0,b)**1.6;g[:tp]=np.linspace(0,1,tp);a[...,3]=(a[...,3]*g[:,None]).astype('uint8');im=Image.fromarray(a,'RGBA')
    im.save(f'assets/vfx_lanaU_{name}.webp',quality=82,method=6);print(name,round(os.path.getsize(f'assets/vfx_lanaU_{name}.webp')/1024),'KB')
for k,src in {'f1':'01','t1':'02','f2':'03','f3':'05','t3':'06','f4':'07','t4':'08'}.items():put(src,k,(768,1152))
for i,src in enumerate(['09','10','11','12']):put(src,f'a{i+1}',(512,768))

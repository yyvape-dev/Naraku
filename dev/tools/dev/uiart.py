"""UI素材を整える。使い方: python3 uiart.py <出力フォルダ> <革の質感.png> <逆転の右手.png>
   ui_leather.webp : 端をなじませて、並べても継ぎ目が出ないタイルにする
   ui_rewind.webp  : 黒背景の演出絵（画面では加算ぎみに重ねるので黒は透ける）"""
import sys, os, numpy as np
from PIL import Image
out,lea,rew=sys.argv[1:4]
a=np.asarray(Image.open(lea).convert('RGB').resize((448,448),Image.LANCZOS)).astype(np.float32)
m=64                                                    # 端64pxを反対側と重ねてなじませる
def blend(a,axis):
    a=np.moveaxis(a,axis,0); n=a.shape[0]; w=np.linspace(0,1,m,dtype=np.float32).reshape(-1,*([1]*(a.ndim-1)))
    body=a[:n-m].copy(); body[:m]=a[n-m:]*(1-w)+a[:m]*w
    return np.moveaxis(body,0,axis)
t=blend(blend(a,0),1); im=Image.fromarray(np.clip(t,0,255).astype(np.uint8))
im.save(f'{out}/ui_leather.webp',quality=72,method=6)
Image.fromarray(np.tile(np.asarray(im),(2,2,1))).save(f'{out}/../_leather_check.png')   # 2×2に並べた確認用
r=Image.open(rew).convert('RGB'); r=r.resize((520,round(520*r.height/r.width)),Image.LANCZOS)
ar=np.asarray(r).astype(np.float32); lum=ar.max(-1,keepdims=True); ar=ar*np.clip((lum-10)/22,0,1)   # ほぼ黒の部分は完全な黒にして、重ねたときに枠が見えないようにする
Image.fromarray(ar.astype(np.uint8)).save(f'{out}/ui_rewind.webp',quality=74,method=6)
for n in ('ui_leather','ui_rewind'): print(n,Image.open(f'{out}/{n}.webp').size,os.path.getsize(f'{out}/{n}.webp')//1024,'KB')

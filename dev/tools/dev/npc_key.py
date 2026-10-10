"""店主の絵（マゼンタ背景）を透過にする（髪や服のピンク・紫を守る方式）。
   使い方: python3 -I key3.py <入力.png> <出力.webp>
   マゼンタ(255,0,255)からの距離で透明度を決めるので、ピンクの髪などは消えない。色かぶり除去は縁の帯だけにかける。"""
import sys, numpy as np
from PIL import Image, ImageFilter
im=np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(np.float32)
R,G,B=im[...,0],im[...,1],im[...,2]
d=(255-R)+G+(255-B)                       # マゼンタからの距離（0〜765）
a=np.clip((d-70)/(200-70),0,1)            # 近い＝透明、遠い＝不透明
A=Image.fromarray((a*255).astype(np.uint8)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.6))
a=np.asarray(A).astype(np.float32)/255
# 縁の帯（透明に近い画素から3画素以内）だけ、マゼンタの色かぶりを差し引く
edge=np.asarray(Image.fromarray(((a<0.98)*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7))).astype(bool)
ex=np.clip(np.minimum(R,B)-G,0,None)*edge
R2=R-ex; B2=B-ex
out=np.dstack([R2,G,B2,a*255]).clip(0,255).astype(np.uint8)
ys,xs=np.where(a>0.03); img=Image.fromarray(out).crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1))
img.save(sys.argv[2],quality=90,alpha_quality=90,method=6)
print(sys.argv[2].split('/')[-1],img.size,'元',im.shape[1],'x',im.shape[0],'上余白',ys.min(),'下端',im.shape[0]-ys.max()-1)

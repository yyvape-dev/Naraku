"""RIFE 4.6 interpolation of Lana's normal-attack sprite, original frames preserved.
RIFE_BIN / RIFE_MODEL select the installed public tool. VK_DRIVER_FILES may select lavapipe.
"""
from pathlib import Path
from PIL import Image
import numpy as np,json,os,subprocess,time
root=Path(__file__).resolve().parent;assets=root.parents[1]/'assets';work=root/'work';work.mkdir(exist_ok=True)
meta=json.loads((assets/'sword.json').read_text());source=Image.open(assets/'sword.webp').convert('RGBA');w,h=meta['cw'],meta['ch']
original=[]
for i in range(12):
 im=source.crop((i*w,0,(i+1)*w,h));original.append(im)
 a=np.array(im,dtype=np.float32);rgb=np.rint(a[:,:,:3]*(a[:,:,3:4]/255)).astype('uint8')
 Image.fromarray(rgb).save(work/f'color-{i:02}.png');im.getchannel('A').convert('RGB').save(work/f'alpha-{i:02}.png')
binary=os.environ.get('RIFE_BIN','/tmp/naraku-rife/rife-ncnn-vulkan');model=os.environ.get('RIFE_MODEL','/tmp/naraku-rife/rife-v4.6')
result=[];frames=[];start=time.perf_counter()
for i in range(12):
 j=(i+1)%12;frames.append(original[i]);timing={}
 for kind in ['color','alpha']:
  out=work/f'{kind}-mid-{i:02}.png';t=time.perf_counter()
  args=[binary,'-m',model,'-g','0','-j','1:1:1','-0',str(work/f'{kind}-{i:02}.png'),'-1',str(work/f'{kind}-{j:02}.png'),'-o',str(out)]
  p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=180)
  if p.returncode:raise RuntimeError(p.stderr.decode(errors='replace'))
  timing[kind]=round(time.perf_counter()-t,3)
 rgb=np.asarray(Image.open(work/f'color-mid-{i:02}.png').convert('RGB'),dtype=np.float32)
 alpha=np.asarray(Image.open(work/f'alpha-mid-{i:02}.png').convert('L'),dtype=np.float32)
 straight=np.clip(rgb*255/np.maximum(alpha[:,:,None],1),0,255)
 rgba=np.concatenate([straight,alpha[:,:,None]],axis=2);rgba[alpha<2]=0
 mid=Image.fromarray(np.rint(rgba).astype('uint8'));mid.save(work/f'mid-{i:02}.png');frames.append(mid)
 result.append({'pair':[i+1,j+1],'seconds':timing});print('pair',i+1,'OK',flush=True)
# Last original pose returns to the idle pose through one closing midpoint, no longer attack duration.
atlas=Image.new('RGBA',(w*6,h*4))
for i,im in enumerate(frames):atlas.paste(im,(i%6*w,i//6*h))
atlas.save(root/'sword_rife.webp',lossless=True,exact=True,method=4)
(root/'sword_rife.json').write_text(json.dumps({**meta,'cols':6,'rows':4,'frames':24,'originalFrames':12,'midpoints':12,'loopClosingMidpoint':True,'target':'ally'},indent=2)+'\n')
(root/'benchmark.json').write_text(json.dumps({'seconds':round(time.perf_counter()-start,3),'pairs':result,'source':str(assets/'sword.webp')},indent=2)+'\n')
print('DONE',round(time.perf_counter()-start,2),'seconds',flush=True)

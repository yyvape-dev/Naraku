import numpy as np
from PIL import Image, ImageFilter
up='/root/.claude/uploads/ef9f1d5c-212a-5dba-91c8-24da764c4d66/';d='/home/claude/w1009/naraku_handoff/'
A=np.asarray(Image.open(up+'3cfda761-image.png').convert('RGB')).astype(float);R,G,B=A[...,0],A[...,1],A[...,2]
al=np.clip(1-((R+B)/2-G)/255.0,0,1)
print('bg alpha pct', np.percentile(al[:20,:].ravel(),[50,95,99.5]))
lo=np.percentile(al[:20,:].ravel(),99.5)+0.02
al=np.clip((al-lo)/(1-lo),0,1)
v=np.clip(G/np.maximum(al*(1-lo)+lo,1e-3),0,255)
# cleaner: recompute gray from G given original alpha
a0=np.clip(1-((R+B)/2-G)/255.0,1e-3,1); v=np.clip(np.maximum(G/a0,175),0,255)
colsum=al.sum(0);print('colsum max',colsum.max())
on=colsum>colsum.max()*0.01
xs=np.where(on)[0];groups=[];s=p=xs[0]
for c in xs[1:]:
  if c-p>25:groups.append((s,p));s=c
  p=c
groups.append((s,p));print(groups)
rgba=np.dstack([v,v,v,al*255]).astype(np.uint8)
cells=[]
for x0,x1 in groups:
  rs=al[:,x0:x1+1].sum(1);ys=np.where(rs>rs.max()*0.01)[0]
  x0=max(0,x0-10);x1=min(A.shape[1]-1,x1+10);y0=max(0,ys[0]-10);y1=min(A.shape[0]-1,ys[-1]+10)
  cells.append(Image.fromarray(rgba[y0:y1+1,x0:x1+1],'RGBA'))
cw=max(c.width for c in cells);ch=max(c.height for c in cells)
sh=Image.new('RGBA',(cw*3,ch),(0,0,0,0))
for i,c in enumerate(cells):sh.paste(c,(i*cw+(cw-c.width)//2,(ch-c.height)//2))
k=380/cw;sh=sh.resize((round(cw*3*k),round(ch*k)),Image.LANCZOS)
sh.save(d+'assets/ui_smoke.webp',quality=88,method=6,exact=True);print(sh.size)
bg=Image.new('RGBA',sh.size,(40,30,25,255));bg.alpha_composite(sh);bg.save('/tmp/claude-0/-home-claude-naraku/ef9f1d5c-212a-5dba-91c8-24da764c4d66/scratchpad/smoke_check.png')

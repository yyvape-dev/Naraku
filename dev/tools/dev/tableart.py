import sys,numpy as np
from PIL import Image
up='/root/.claude/uploads/ef9f1d5c-212a-5dba-91c8-24da764c4d66/'
d='/home/claude/w1009/naraku_handoff/'
# table
im=Image.open(up+'14dcc552-image.png').convert('RGB')
im.save(d+'cardart/src_table.png')
a=np.asarray(im).astype(float).mean(2)
# frame inner edge: frame is bright gold; find columns/rows profile in middle band
col=a[600:900].mean(0); row=a[:,450:600].mean(1)
print('col', [(x,int(col[x])) for x in range(60,160,4)])
print('colR', [(x,int(col[x])) for x in range(860,960,4)])
print('row', [(y,int(row[y])) for y in range(170,260,4)])
print('rowB', [(y,int(row[y])) for y in range(1160,1260,4)])
im.resize((720,1080),Image.LANCZOS).save(d+'assets/ui_table.webp',quality=86,method=6)
# smoke unmix
s=Image.open(up+'3cfda761-image.png').convert('RGB');s.save(d+'cardart/src_smoke.png')
A=np.asarray(s).astype(float);R,G,B=A[...,0],A[...,1],A[...,2]
al=1-((R+B)/2-G)/255.0; al=np.clip(al,0,1)
al=np.clip((al-0.06)/0.94,0,1)
v=np.clip(G/np.maximum(al,1e-3),0,255); v=np.where(al>0.02,v,0)
rgba=np.dstack([v,v,v,al*255]).astype(np.uint8)
mask=al>0.04
cols=np.where(mask.any(0))[0]
# split into 3 groups by gaps
groups=[];start=cols[0];prev=cols[0]
for c in cols[1:]:
  if c-prev>30: groups.append((start,prev));start=c
  prev=c
groups.append((start,prev));print('groups',groups)
cells=[]
for x0,x1 in groups:
  sub=mask[:,x0:x1+1];rows=np.where(sub.any(1))[0]
  cells.append(Image.fromarray(rgba[rows[0]:rows[-1]+1,x0:x1+1],'RGBA'))
cw=max(c.width for c in cells);ch=max(c.height for c in cells)
sheet=Image.new('RGBA',(cw*3,ch),(0,0,0,0))
for i,c in enumerate(cells): sheet.paste(c,(i*cw+(cw-c.width)//2,(ch-c.height)//2))
k=360/cw; sheet=sheet.resize((int(cw*3*k),int(ch*k)),Image.LANCZOS)
sheet.save(d+'assets/ui_smoke.webp',quality=88,method=6,exact=True)
print('smoke',sheet.size)

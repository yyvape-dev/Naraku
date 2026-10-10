"""超必殺の着弾エフェクトを、明けた瞬間からの時刻で撮る（描画の時計を手動で進める）。
   使い方: python3 tools/dev/ultfx.py <full.html> <出力.png> <キャラ> [時刻(秒,カンマ区切り)]"""
import sys,os
from playwright.sync_api import sync_playwright
from PIL import Image
INIT="""(()=>{let now=1000;const q=[];performance.now=()=>now;window.requestAnimationFrame=cb=>{q.push(cb);return q.length};
window.__tick=(n,ms)=>{for(let i=0;i<n;i++){now+=ms;const c=q.splice(0);c.forEach(f=>f(now))}}})()"""
src,out,cid=sys.argv[1],sys.argv[2],sys.argv[3]
TS=[float(v) for v in (sys.argv[4] if len(sys.argv)>4 else '0.03,0.1,0.18,0.28,0.4,0.55,0.8,1.5,3.5').split(',')]
with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page(viewport={'width':390,'height':844},device_scale_factor=1);errs=[]
  pg.on('pageerror',lambda e:errs.append(str(e)[:160]))
  pg.add_init_script(INIT);pg.goto('file://'+os.path.abspath(src))
  for _ in range(30):pg.evaluate("__tick(5,16.67)");pg.wait_for_timeout(40)
  others=[i for i in ['fox','sword','mage','sister','blue'] if i!=cid][:2]
  pg.evaluate(f"NARAKU.start({[cid]+others},321)")
  pg.evaluate("setInterval(()=>{if(NARAKU.mode==='levelup')NARAKU.pick(0)||NARAKU.pick(1)||NARAKU.pick(-1)},5)")
  for _ in range(40):pg.evaluate("__tick(30,16.67)");pg.wait_for_timeout(20)
  pg.evaluate(f"NARAKU.startUlt(NARAKU.B.allies.find(o=>o.d.id==='{cid}'))")
  for _ in range(200):
    if not pg.evaluate("!!NARAKU.ULT"):break
    pg.evaluate("__tick(1,16.67)")
  r=pg.evaluate("(()=>{const r=document.querySelector('#arena').getBoundingClientRect();return [r.left,r.top,r.width,r.height]})()")
  cl=dict(x=r[0],y=r[1],width=r[2],height=r[3]);ims=[];t=0
  for T in TS:
    n=max(0,round((T-t)/(1/60)));pg.evaluate(f"__tick({n},16.67)");t+=n/60
    f=f'{out}.{T}.png';pg.wait_for_timeout(30);pg.screenshot(path=f,clip=cl);ims.append(Image.open(f).convert('RGB'));os.remove(f)
  print(cid,'errs',errs[:3],'enemies',pg.evaluate("NARAKU.B.enemies.filter(e=>!e.dead).length"))
  b.close()
w,h=ims[0].size;s=Image.new('RGB',(w*len(ims),h))
for i,im in enumerate(ims):s.paste(im,(i*w,0))
s.resize((int(w*len(ims)*0.6),int(h*0.6))).save(out);print('saved',out,'times',TS)

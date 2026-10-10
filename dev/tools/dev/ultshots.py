"""超必殺のカットインを決まった時刻で止めて撮る（CSSアニメを getAnimations で止めて時刻を指定）。
   使い方: python3 tools/dev/ultshots.py <full.html> <出力.png> [幅=390] [高さ=844] [キャラ=sword,blue,mage,sister,fox]
   キャラごとに1行、時刻（ミリ秒）ごとに1列の一覧を作る"""
import sys,os
from playwright.sync_api import sync_playwright
from PIL import Image
INIT="""(()=>{let now=1000;const q=[];performance.now=()=>now;window.requestAnimationFrame=cb=>{q.push(cb);return q.length};
window.__tick=(n,ms)=>{for(let i=0;i<n;i++){now+=ms;const c=q.splice(0);c.forEach(f=>f(now))}}})()"""
src,out=sys.argv[1],sys.argv[2];VW=int(sys.argv[3]) if len(sys.argv)>3 else 390;VH=int(sys.argv[4]) if len(sys.argv)>4 else 844
ids=(sys.argv[5] if len(sys.argv)>5 else 'sword,blue,mage,sister,fox').split(',')
TS=[60,150,250,350,700,920,1000,1080,1200]
rows=[]
with sync_playwright() as p:
  b=p.chromium.launch()
  for cid in ids:
    pg=b.new_page(viewport={'width':VW,'height':VH},device_scale_factor=1);errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:120]))
    pg.add_init_script(INIT);pg.goto('file://'+os.path.abspath(src))
    for _ in range(30):pg.evaluate("__tick(5,16.67)");pg.wait_for_timeout(40)
    others=[i for i in ['fox','sword','mage','sister','blue'] if i!=cid][:2]
    pg.evaluate(f"NARAKU.start({[cid]+others},321)")
    pg.evaluate("__tick(180,16.67)");pg.wait_for_timeout(300)
    pg.evaluate(f"NARAKU.startUlt(NARAKU.B.allies.find(o=>o.d.id==='{cid}'))")
    pg.wait_for_timeout(300)
    r=pg.evaluate("(()=>{const r=document.querySelector('#arena').getBoundingClientRect();return [r.left,r.top,r.width,r.height]})()")
    cl=dict(x=r[0],y=r[1],width=r[2],height=r[3]);row=[]
    for t in TS:
      pg.evaluate(f"document.querySelectorAll('#ult, #ult *').forEach(e=>e.getAnimations().forEach(a=>{{a.pause();a.currentTime={t}}}))")
      pg.wait_for_timeout(60);f=f'{out}.{cid}.{t}.png';pg.screenshot(path=f,clip=cl);row.append(Image.open(f));os.remove(f)
    print(cid,'arena',[round(v) for v in r],'errs',errs[:2]);rows.append(row);pg.close()
  b.close()
w,h=rows[0][0].size;s=0.5;tw,th=int(w*s),int(h*s)
sheet=Image.new('RGB',(tw*len(TS),th*len(rows)),(0,0,0))
for j,row in enumerate(rows):
  for i,im in enumerate(row):sheet.paste(im.convert('RGB').resize((tw,th)),(i*tw,j*th))
sheet.save(out);print('saved',out,sheet.size,'times(ms)',TS)

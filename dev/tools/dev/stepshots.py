"""戦闘をコマ送りで撮る（描画の時計を手動で進める）。エフェクトの見た目の確認用。
   使い方: python3 tools/dev/stepshots.py <full.html> <出力フォルダ> <キャラ> [枚数=28] [何回目の攻撃から=3] [clip=x,y,w,h]
   <キャラ>の攻撃が始まった瞬間から 1/60 秒ずつ進めて s_00.png… を撮る。強化の選択は自動で選ぶ"""
import sys,asyncio,os
from playwright.async_api import async_playwright
INIT="""(()=>{let now=1000;const q=[];performance.now=()=>now;window.requestAnimationFrame=cb=>{q.push(cb);return q.length};
window.__tick=(n,ms)=>{for(let i=0;i<n;i++){now+=ms;const c=q.splice(0);c.forEach(f=>f(now))}}})()"""
src,out,cid=sys.argv[1],sys.argv[2],sys.argv[3];N=int(sys.argv[4]) if len(sys.argv)>4 else 28;nth=int(sys.argv[5]) if len(sys.argv)>5 else 3
clip=dict(zip('x y width height'.split(),map(float,(sys.argv[6] if len(sys.argv)>6 else '0,40,290,450').split(','))))
async def main():
  os.makedirs(out,exist_ok=True)
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page(viewport={'width':390,'height':664},device_scale_factor=2)
    await pg.add_init_script(INIT);await pg.goto('file://'+os.path.abspath(src))
    for _ in range(40):await pg.evaluate("__tick(5,16.67)");await pg.wait_for_timeout(50)
    ids=['fox','sword','mage','sister','blue'];team=[cid]+[i for i in ids if i!=cid][:2]
    await pg.evaluate(f"NARAKU.start({team},321)")
    await pg.evaluate("setInterval(()=>{if(NARAKU.mode==='levelup')NARAKU.pick(0)||NARAKU.pick(1)||NARAKU.pick(-1)},5)")
    seen=0
    for i in range(4000):
      await pg.evaluate("__tick(1,16.67)")
      t=await pg.evaluate(f"NARAKU.B.allies.find(o=>o.d.id==='{cid}').animT")
      if 0<=t<0.02:
        seen+=1
        if seen>=nth:break
    for k in range(N):
      await pg.screenshot(path=f'{out}/s_{k:02d}.png',clip=clip);await pg.evaluate("__tick(1,16.67)")
    await b.close()
asyncio.run(main())

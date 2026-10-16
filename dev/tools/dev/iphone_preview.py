"""Review the actual short iPhone viewport before selecting its layout."""
import sys,json
from pathlib import Path
from playwright.sync_api import sync_playwright
html=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
 b=p.chromium.launch()
 result={}
 for w,h in [(375,667),(390,664),(393,659),(393,852)]:
  pg=b.new_page(viewport={'width':w,'height':h},is_mobile=True,has_touch=True,device_scale_factor=1)
  pg.goto(html.as_uri());pg.wait_for_function('window.NARAKU_READY')
  pg.evaluate("NARAKU.start(['sword','fox','mage'],4242);document.querySelector('#btnPause').click();NARAKU.sim(12)")
  pg.wait_for_timeout(500)
  pg.wait_for_function("()=>[...document.querySelectorAll('#hand img,.orb-frame,#battleTrayArt')].every(e=>!e.getAttribute('src')||(e.complete&&e.naturalWidth>0))")
  result[f'{w}x{h}']=pg.evaluate("""()=>{const rect=e=>{const r=e.getBoundingClientRect();return{x:r.x,y:r.y,width:r.width,height:r.height}};return{viewport:{width:innerWidth,height:innerHeight},canvas:rect(document.querySelector('#cv')),lower:rect(document.querySelector('#cmd'))}}""")
  pg.screenshot(path=str(out/f'current-{w}x{h}.png'))
  pg.evaluate("NARAKU.start(['sword','fox','mage'],4242);document.querySelector('#btnPause').click()")
  pg.wait_for_timeout(100)
  for i in range(5):
   pg.evaluate("NARAKU.B.slots.forEach(s=>s.card=NARAKU.CARDS.find(c=>c.id==='fox_bind'));NARAKU.B.sel=null;document.querySelector('#btnPause').click()")
   pg.wait_for_timeout(70)
   r=pg.locator(f'#hand [data-i="{i}"]').bounding_box()
   pg.touchscreen.tap(r['x']+30,r['y']+30);pg.wait_for_timeout(140)
   assert pg.evaluate('NARAKU.B.sel')==i,('touch blocked',w,h,i)
   selected=pg.locator(f'#hand [data-i="{i}"]').bounding_box()
   assert selected['x']>=0 and selected['x']+selected['width']<=w,('clipped card',w,h,i)
   assert pg.evaluate("document.querySelector('#cv').getBoundingClientRect().x")==0
   pg.click('#btnPause')
  result[f'{w}x{h}']['touchChecks']=5
  pg.close()
 b.close()
(out/'current.json').write_text(json.dumps(result,indent=2));print(result)

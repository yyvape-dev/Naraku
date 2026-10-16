"""Measure the actual battle DOM and fixed simulation geometry at two viewports."""
import json, os, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

html, out, label = map(str, sys.argv[1:4])
Path(out).mkdir(parents=True, exist_ok=True)
MEASURE = """() => {
 const rect = e => {if(!e)return null;const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}};
 const q=s=>rect(document.querySelector(s));
 const cv=document.querySelector('#cv').getBoundingClientRect(),B=NARAKU.B;
 const cards=[...document.querySelectorAll('#hand .card')].map(e=>{
  const s=getComputedStyle(e),m=new DOMMatrix(s.transform),r=e.getBoundingClientRect();
  return {rect:rect(e),width:parseFloat(s.width),height:parseFloat(s.height),rotation:Math.atan2(m.b,m.a)*180/Math.PI,center:{x:r.x+r.width/2,y:r.y+r.height/2},selected:e.classList.contains('sel')};
 });
 const units=[...document.querySelectorAll('#rail .unit')].map(rect);
 const overlap=cards.slice(1).map((c,i)=>Math.max(0,cards[i].rect.x+cards[i].rect.width-c.rect.x));
 return {canvas:q('#cv'),arena:q('#arena'),main:q('#main'),hud:q('#hud'),lower:q('#cmd'),hand:q('#hand'),tray:q('#battleTray'),units,cards,overlap,buttons:{pause:q('#btnPause'),speed:q('#btnSpeed'),tune:q('#btnTune')},logical:{lineY:B.lineY,allies:B.allies.map(a=>({x:a.x,y:a.y})),enemies:B.enemies.map(e=>({idx:e.idx,x:e.x,y:e.y,hp:e.hp}))},footHP:!!document.querySelector('.foot-hp')};
}"""
all_results = {}
with sync_playwright() as p:
    b=p.chromium.launch(channel="chromium")
    for w,h in [(390,844),(375,667)]:
        pg=b.new_page(viewport={"width":w,"height":h},device_scale_factor=1)
        errors=[]
        pg.on('pageerror',lambda e: errors.append(str(e)))
        pg.goto('file://'+os.path.abspath(html))
        pg.wait_for_function('window.NARAKU_READY')
        pg.evaluate("NARAKU.start(['sword','fox','mage'],4242); document.querySelector('#btnPause').click(); NARAKU.sim(12)")
        pg.wait_for_timeout(300)
        pg.wait_for_function("""()=>[...document.querySelectorAll('#hand .card')].every(e=>{const s=getComputedStyle(e),target=parseFloat(e.style.getPropertyValue('--angle'));if(!Number.isFinite(target))return true;const m=new DOMMatrix(s.transform);return Math.abs(Math.atan2(m.b,m.a)*180/Math.PI-target)<.01})""")
        all_results[f'{w}x{h}']=pg.evaluate(MEASURE)
        all_results[f'{w}x{h}']['errors']=errors
        pg.screenshot(path=f'{out}/{label}-{w}x{h}.png')
        pg.close()
    b.close()
Path(f'{out}/{label}.json').write_text(json.dumps(all_results,ensure_ascii=False,indent=2))
print(json.dumps({k:{n:v[n] for n in ['canvas','hud','lower','logical','errors']} for k,v in all_results.items()},ensure_ascii=False))

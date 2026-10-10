import sys,os
from playwright.sync_api import sync_playwright
html=os.path.abspath(sys.argv[1]);out=sys.argv[2]
with sync_playwright() as p:
  b=p.chromium.launch()
  for (w,h) in [(390,664),(390,844),(375,667)]:
    pg=b.new_page(viewport={'width':w,'height':h},device_scale_factor=2);errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto('file://'+html);pg.wait_for_timeout(1500)
    for tag,js in [('clear',"let sd=1;for(;sd<200;sd++){NARAKU.startRun(['fox','sword','mage'],sd);if(NARAKU.R.map.nodes[0].next.length===3)break};NARAKU.R.light=100;NARAKU.R.sel=NARAKU.R.map.nodes[0].next[NARAKU.R.map.nodes[0].next.length-1]"),
                   ('dark',"NARAKU.startRun(['fox','sword','mage'],11);NARAKU.R.light=20;NARAKU.R.sel=null")]:
      pg.evaluate("()=>{"+js+"}");pg.wait_for_timeout(900);pg.screenshot(path=f'{out}/map_{w}x{h}_{tag}.png')
    print(w,h,'errs',errs)
  b.close()

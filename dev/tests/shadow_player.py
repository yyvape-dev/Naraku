"""Verify the lightweight comparison actually paints, plus explicit failure UI.
Usage: python3 dev/tests/shadow_player.py BASE_URL OUT [chromium|webkit]
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json,sys,time
url=sys.argv[1].rstrip('/');out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
engine=sys.argv[3] if len(sys.argv)>3 else 'chromium'
with sync_playwright() as p:
 b=getattr(p,engine).launch();pg=b.new_page(viewport={'width':393,'height':852},is_mobile=True,has_touch=True);errors=[];fails=[]
 pg.on('pageerror',lambda e:errors.append(str(e)));pg.on('requestfailed',lambda r:fails.append([r.url,r.failure]))
 started=time.time();pg.goto(url+'/dev/mock/shadow_bind_demo.html?v=player-fix');pg.wait_for_function("document.querySelector('#status').textContent==='再生できます'",timeout=90000)
 ready_time=time.time()-started;pg.click('#pause');pg.locator('#scrub').evaluate('(e)=>{e.value=.39;e.dispatchEvent(new Event("input"))}');pg.wait_for_timeout(100)
 assert pg.locator('iframe').count()==1;assert not pg.locator('#loading').is_visible()
 f=pg.frames[1];assert f.evaluate('NARAKU.SHADOW_VFX.enabled&&NARAKU.FX.sh.some(s=>s.k==="shadow")')
 canvas=f.locator('#cv');assert canvas.screenshot()!=bytes(), 'no canvas'
 # Count non-black pixels of the actual rendered arena, not only readiness flags.
 pixels=f.evaluate('''()=>{const c=document.querySelector('#cv'),a=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let n=0;for(let i=0;i<a.length;i+=16)if(a[i]+a[i+1]+a[i+2]>45)n++;return n}''')
 assert pixels>1000,pixels
 pg.screenshot(path=str(out/(engine+'-mobile.png')),full_page=True)
 pg.select_option('#variant','legacy');assert f.evaluate('!NARAKU.SHADOW_VFX.enabled');pg.select_option('#variant','godot')
 pg.select_option('#range','2.44140625');pg.locator('#scrub').evaluate('(e)=>{e.value=.39;e.dispatchEvent(new Event("input"))}');pg.wait_for_timeout(100)
 pg.screenshot(path=str(out/(engine+'-maximum.png')),full_page=True)
 sizes=f.evaluate('performance.getEntriesByType("resource").map(r=>({url:r.name,size:r.encodedBodySize,decoded:r.decodedBodySize}))')
 assert not any('/index.html' in r['url'] for r in sizes)
 assert not f.evaluate('SAVE_ON'), 'preview writes saves'
 bad=b.new_page();bad.route('**/vfx_shadow_air.webp*',lambda r:r.abort());bad.goto(url+'/dev/mock/shadow_bind_demo.html?v=failure-check');bad.wait_for_function("document.querySelector('#status').textContent==='読み込みに失敗しました'",timeout=30000)
 assert bad.locator('#loading').is_visible();assert bad.locator('#replay').inner_text()=='再読み込み'
 assert not errors,errors
 result={'engine':engine,'secondsToReady':round(ready_time,2),'onePlayer':True,'arenaNonBlackSamples':pixels,'assetFailureVisible':True,'resources':sizes,'errors':errors,'requestFailures':fails}
 (out/(engine+'-checks.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print('RESULT OK',engine,round(ready_time,2),pixels,sum(r['size'] for r in sizes));b.close()

"""Review split mock layers, actual controls and movable/reloading cards."""
from pathlib import Path
import json,sys
from PIL import Image
from playwright.sync_api import sync_playwright

html=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
root=Path(__file__).resolve().parents[2]
im=Image.open(root/'dev/assets/ui_battle_extracted_base.webp').convert('RGBA')
alpha=im.getchannel('A').tobytes()
# This region occupied the five upper card holders in the supplied full mock.
vals=[alpha[y*im.width+x] for y in range(180) for x in range(200,1080)]
clear=sum(v<20 for v in vals)/len(vals)
assert clear>.99,('fixed card outlines left in base',clear)
results={'fixedUpperCardAreaTransparent':clear,'viewports':{}}
with sync_playwright() as p:
 b=p.chromium.launch()
 for w,h in [(375,667),(390,664),(393,659),(393,852)]:
  pg=b.new_page(viewport={'width':w,'height':h},has_touch=True,is_mobile=True)
  errors=[];pg.on('pageerror',lambda e:errors.append(str(e)))
  pg.goto(html.as_uri());pg.wait_for_function('window.NARAKU_READY')
  pg.evaluate("NARAKU.start(['sword','fox','mage'],4242);document.querySelector('#btnPause').click()")
  pg.wait_for_timeout(200)
  t=pg.evaluate('NARAKU.B.t')
  pg.locator('#btnPause').tap();pg.wait_for_timeout(200)
  assert pg.evaluate('NARAKU.B.t')>t
  pg.locator('#btnPause').tap()
  assert pg.locator('#btnPause .btn-label').inner_text()=='▶'
  pg.locator('#btnSpeed').tap()
  assert pg.locator('#btnSpeed .btn-label').inner_text()=='×2'
  pg.locator('#btnSpeed').tap()
  assert pg.locator('#btnSpeed .btn-label').inner_text()=='×1'
  pg.locator('#btnTune').tap();pg.wait_for_timeout(100)
  assert 'tuning' in pg.locator('#cmd').get_attribute('class')
  assert not pg.locator('#handRow').is_visible()
  assert not pg.locator('#ops').is_visible()
  pg.locator('#tuneClose').tap();pg.wait_for_timeout(100)
  assert pg.locator('#handRow').is_visible()
  # Stable before/selected/reloading captures of the same real battle.
  pg.evaluate("NARAKU.start(['sword','fox','mage'],4242);document.querySelector('#btnPause').click();NARAKU.sim(12)")
  pg.wait_for_timeout(250)
  pg.wait_for_function("()=>[...document.querySelectorAll('#hand img,.orb-frame,#battleTrayArt')].every(e=>e.complete&&e.naturalWidth>0)")
  centers=pg.locator('#hand .card').evaluate_all('es=>es.map(e=>{const r=e.getBoundingClientRect();return r.x+r.width/2})')
  assert len(centers)==5 and all(centers[i+1]-centers[i]>40 for i in range(4)),centers
  assert all(20<x<w-20 for x in centers),centers
  pg.screenshot(path=str(out/f'normal-{w}x{h}.png'))
  pg.evaluate('NARAKU.B.sel=2');pg.wait_for_timeout(250)
  assert pg.locator('#hand .card.sel').count()==1
  assert pg.locator('#battleTray .card').count()==0
  pg.screenshot(path=str(out/f'selected-{w}x{h}.png'))
  assert pg.evaluate('NARAKU.useCard(2,180,240)')
  pg.wait_for_timeout(250)
  assert pg.locator('#hand [data-i="2"]').evaluate("e=>e.classList.contains('back')")
  assert pg.locator('#hand [data-i="2"] .ki').inner_text()=='装填中'
  pg.screenshot(path=str(out/f'reload-{w}x{h}.png'))
  assert not errors,errors
  results['viewports'][f'{w}x{h}']={'pause':True,'speed':True,'tuning':True,'selection':True,'reload':True,'errors':errors}
  pg.close()
 b.close()
(out/'split-checks.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print('RESULT OK',json.dumps(results,ensure_ascii=False))

"""Verify the Godot atlas integration changes visuals without changing battle state."""
from pathlib import Path
import json,sys,time
from playwright.sync_api import sync_playwright
html=Path(sys.argv[1]).resolve();old=Path(sys.argv[2]).resolve();out=Path(sys.argv[3]);out.mkdir(parents=True,exist_ok=True)
script=r"""()=>{
 const N=NARAKU,result=[];
 for(const seed of [1,77,4242]){
  N.start(['sword','fox','mage'],seed);
  N.sim(8);N.B.slots[0].card=N.CARDS.find(c=>c.id==='sw_quake');N.useCard(0,180,200);N.sim(.1);
  const pending=N.B.impacts.some(q=>q.c.id==='sw_quake');N.sim(.1);
  const visual=N.FX.sh.filter(q=>q.k==='quake').length;
  N.sim(20);const B=N.B;
  result.push({seed,pending,visual,state:{t:B.t,life:B.life,kills:B.kills,gold:B.gold,stat:B.stat,hp:B.allies.map(a=>a.hp),enemies:B.enemies.map(e=>[e.idx,e.hp,e.x,e.y]),slots:B.slots.map(s=>[s.card?.id,s.refill]),queue:B.queue.map(c=>c.id)}});
 }
 return result;
}"""
with sync_playwright() as p:
 b=p.chromium.launch();snapshots=[];errors=[]
 for path in [old,html]:
  pg=b.new_page(viewport={'width':393,'height':659});pg.on('pageerror',lambda e:errors.append(str(e)))
  pg.goto(path.as_uri()+('?quakefx=godot' if path==html else ''));pg.wait_for_function('window.NARAKU_READY');pg.wait_for_timeout(300)
  snapshots.append(pg.evaluate(script));pg.close()
 assert [r['state'] for r in snapshots[0]]==[r['state'] for r in snapshots[1]],'combat state changed'
 assert all(r['pending'] and r['visual']==2 for r in snapshots[1]),snapshots[1]
 result={'sameCombatState':True,'seeds':3,'impactDelayPreserved':True,'quakeLayersPerHit':2,'screens':{}}
 for w,h in [(375,667),(393,852)]:
  pg=b.new_page(viewport={'width':w,'height':h});pg.on('pageerror',lambda e:errors.append(str(e)))
  pg.goto(html.as_uri()+"?quakefx=godot");pg.wait_for_function('window.NARAKU_READY');pg.wait_for_timeout(200)
  pg.evaluate("NARAKU.start(['sword','fox','mage'],4242);document.querySelector('#btnPause').click();NARAKU.QUAKE_VFX.preview=true;NARAKU.sim(12);NARAKU.FX.sh.length=0;NARAKU.FX.parts.length=0;NARAKU.FX.dust.length=0;NARAKU.FX.floats.length=0;NARAKU.B.slots[0].card=NARAKU.CARDS.find(c=>c.id==='sw_quake');NARAKU.useCard(0,180,235);NARAKU.FX.cut=null;NARAKU.sim(.2)")
  for t in [0,.075,.25,.4,.8,1.27,1.8,2.25]:
   pg.evaluate("t=>NARAKU.FX.sh.forEach(s=>{if(s.k==='quake')s.t=t;else s.t=s.life*.98})",t)
   pg.wait_for_timeout(50);pg.screenshot(path=str(out/f'quake-{w}x{h}-{t}.png'))
  # A real-time warm browser frame sample under repeated VFX, not a physical-phone benchmark.
  sample=pg.evaluate("""async()=>{
   const N=NARAKU,ts=[];N.FX.sh=N.FX.sh;
   N.FX.sh.filter(s=>s.k==='quake').forEach(s=>s.t=.1);
   let prev=performance.now();for(let i=0;i<90;i++){await new Promise(requestAnimationFrame);const now=performance.now();ts.push(now-prev);prev=now}
   return ts.sort((a,b)=>a-b);
  }""".replace('N.FX.sh=N.FX.sh;',''))
  result['screens'][f'{w}x{h}']={'medianMs':sample[len(sample)//2],'p95Ms':sample[int(len(sample)*.95)]}
  pg.close()
 assert not errors,errors
 result['errors']=errors;b.close()
(out/'checks.json').write_text(json.dumps(result,indent=2));print('RESULT OK',json.dumps(result))

"""Candidate vs legacy: identical combat, hit/slow timing, echo, fallback and cleanup."""
from playwright.sync_api import sync_playwright
from pathlib import Path
import json,sys
url=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8765/index.html'
out=Path(sys.argv[2] if len(sys.argv)>2 else 'dev/reports/shadow-bind');out.mkdir(parents=True,exist_ok=True)
script=r'''()=>{
 const N=NARAKU,result=[];
 for(const seed of [1,77,4242])for(const levels of [0,4]){
  N.start(['sword','fox','mage'],seed);N.sim(8);for(let j=0;j<levels;j++)N.grant('s_r');
  N.B.slots[0].card=N.CARDS.find(c=>c.id==='fox_bind');N.useCard(0,180,240);
  const charge=N.FX.sh.filter(s=>s.k==='shadow').map(s=>({layer:s.layer,w:s.w,t:s.t}));
  N.sim(.15);const pending=N.B.impacts.some(s=>s.c.id==='fox_bind');N.sim(1/60);
  const justHit=N.B.impacts.every(s=>s.c.id!=='fox_bind');
  N.sim(18);const B=N.B;
  result.push({seed,levels,charge,pending,justHit,state:{mode:N.mode,t:B.t,life:B.life,kills:B.kills,gold:B.gold,stat:B.stat,hp:B.allies.map(a=>a.hp),enemies:B.enemies.map(e=>[e.idx,e.hp,e.x,e.y,e.slowT]),slots:B.slots.map(s=>[s.card?.id,s.refill]),queue:B.queue.map(c=>c.id)}});
 }
 return result;
}'''
with sync_playwright() as p:
 b=p.chromium.launch();states=[];errors=[]
 for variant in ['legacy','godot']:
  pg=b.new_page(viewport={'width':393,'height':659});pg.on('pageerror',lambda e:errors.append(str(e)))
  pg.goto(url+'?shadowfx='+variant);pg.wait_for_function('window.NARAKU_READY&&NARAKU.vfx.shadowReady()');states.append(pg.evaluate(script));pg.close()
 assert [r['state'] for r in states[0]]==[r['state'] for r in states[1]],'battle changed'
 assert all(r['pending'] and r['justHit'] and len(r['charge'])==2 and all(s['t']==0 for s in r['charge']) for r in states[1])
 assert all(abs(r['charge'][0]['w']-95*1.25**r['levels']*3.4)<1e-7 for r in states[1])
 pg=b.new_page();pg.on('pageerror',lambda e:errors.append(str(e)));pg.goto(url+'?shadowfx=godot');pg.wait_for_function('window.NARAKU_READY&&NARAKU.vfx.shadowReady()')
 details=pg.evaluate(r'''()=>{
  const N=NARAKU;N.start(['sword','fox','mage'],42);N.sim(8);
  N.B.allies.forEach(a=>a.cdT=999);N.B.shots=[];N.B.impacts=[];
  const e=N.B.enemies.find(e=>!e.dead);e.hp=e.max=10000;e.x=180;e.y=256;e.spd=0;e.st='walk';e.pend=0;e.atkT=999;e.slowT=0;N.B.enemies=[e];
  N.B.slots[0].card=N.CARDS.find(c=>c.id==='fox_bind');N.useCard(0,180,240);
  const hp=e.hp;N.sim(.15);if(e.hp!==hp||e.slowT!==0)throw Error('early hit');
  N.sim(1/60);if(e.hp>=hp||Math.abs(e.slowT-4.5)>.001)throw Error('hit/slow timing');
  if(N.SHADOW_VFX.fps!==60||N.SHADOW_VFX.life!==.9)throw Error('2x playback config');
  N.vfx.tick(.89);if(!N.FX.sh.some(s=>s.k==='shadow'))throw Error('visual ended early');
  N.vfx.tick(.02);if(N.FX.sh.some(s=>s.k==='shadow'))throw Error('visual leaked');
  if(e.slowT<4.4)throw Error('visual cleanup altered slow');
  N.start(['sword','fox','mage'],42);N.B.M.echo=2;N.B.slots[0].card=N.CARDS.find(c=>c.id==='fox_bind');N.useCard(0,180,240);N.sim(1);
  if(N.FX.sh.filter(s=>s.k==='shadow').length!==6)throw Error('echo missing');
  N.start(['sword','fox','mage'],42);const img=VT.shadow_air;delete VT.shadow_air;N.B.slots[0].card=N.CARDS.find(c=>c.id==='fox_bind');N.useCard(0,180,240);N.sim(.2);VT.shadow_air=img;
  if(N.FX.sh.some(s=>s.k==='shadow')||!N.FX.sh.some(s=>s.k==='ring'||s.k==='tex'))throw Error('fallback');
  return {slow:4.5,reload:8,visualLife:.9,playbackFps:60,echoLayers:6,fallback:true,cleanup:true};
 }''')
 assert not errors,errors
 result={'sameCombatState':True,'seeds':3,'rangeLevels':[0,4],'preHitCharge':True,'impactDelay':.16,'details':details,'errors':errors}
 (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print('RESULT OK',json.dumps(result));b.close()

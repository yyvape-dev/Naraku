"""Dedicated skill/strategy slots, all six effects, probabilities and touch input."""
import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
html=Path(sys.argv[1]).resolve()
out=Path(sys.argv[2] if len(sys.argv)>2 else 'dev/reports/strategy-slots');out.mkdir(parents=True,exist_ok=True)
script=r"""()=>{
 const N=NARAKU,checks={},assert=(k,v)=>{if(!v)throw Error(k);checks[k]=true},
 start=(ids=['sword','fox','mage'],seed=4242)=>N.start(ids,seed),
 use=e=>{N.B.slots[4].card=N.STRATEGIES.find(c=>c.effect===e);return N.useCard(4,0,0)},
 skills=()=>N.B.slots.slice(0,4).map(s=>s.card?.id).concat(N.B.queue.map(c=>c.id)).filter(Boolean).sort().join();
 start();const counts=Object.fromEntries(N.STRATEGIES.map(c=>[c.effect,0]));
 for(let seed=1;seed<=200;seed++){
  start(undefined,seed);const B=N.B;counts[B.slots[4].card.effect]++;
  assert('fixed slots',B.slots.length===5&&B.slots.slice(0,4).every(s=>s.card.owner)&&B.slots[4].card.category==='strategy'&&B.queue.every(c=>c.owner));
 }
 start();N.B.allies.forEach(a=>{a.cdT=100000;a.hp=a.max=1e9});N.B.life=100000;N.B.dur=100000;for(let i=0;i<5000;i++){N.B.slots[4].card=null;N.B.slots[4].refill=0;N.sim(1/60);counts[N.B.slots[4].card.effect]++}assert('rare probabilities',counts.revive>140&&counts.revive<280&&counts.ult>140&&counts.ult<280);
 start();let B=N.B;B.allies.forEach(a=>a.hp=a.max*.2);B.allies[2].alive=false;B.allies[2].hp=0;
 use('heal');assert('25% heal without revive',B.allies.slice(0,2).every(a=>Math.abs(a.hp-(a.max*.2+Math.round(a.max*.25)))<.001)&&B.allies[2].hp===0);
 assert('20 second strategy cooldown',B.slots[4].refill===20&&!B.slots[4].card&&B.queue.every(c=>c.category!=='strategy'));
 start();B=N.B;N.useCard(0,180,100);const before=skills(),wait=B.slots[0].refill;
 use('redraw');assert('redraw conserves skills and empty wait',skills()===before&&!B.slots[0].card&&B.slots[0].refill===wait&&B.slots.slice(1,4).every(s=>s.card));
 start();B=N.B;N.useCard(0,180,100);N.useCard(1,180,100);const cd=B.allies.map(a=>a.cdT).join();use('reset');
 assert('prepare fills all skill slots only',B.slots.slice(0,4).every(s=>s.card&&s.refill===0)&&B.slots[4].refill===20&&B.allies.map(a=>a.cdT).join()===cd);
 start();B=N.B;use('chase');assert('chase lasts ten seconds',B.chaseUntil===B.t+10);
 // Compare actual normal-attack damage for all five characters, including ranged fallback.
 const attack=(id,chase,far=false,multi=0)=>{
  start([id,...['sword','fox','mage','blue','sister'].filter(x=>x!==id).slice(0,2)]);B=N.B;
  B.allies.forEach(a=>a.cdT=100);const a=B.allies[0];a.cdT=0;a.d={...a.d,cd:100};a.M.multi=multi;
  const d=N.ENEMIES[far?'shaman':'skel'],e={idx:999,type:far?'shaman':'skel',d,x:a.x,y:B.lineY-(far?200:20),hp:100000,max:100000,spd:0,st:far?'cast':'walk',atkT:100,animT:-1,pend:0,slowT:0,frzT:0,burnT:0,burnDps:0,burnTick:0,knT:0,flash:0,elite:false,sc:1,dead:false,tg:null,ph:0,stopOff:far?-200:-4};
  B.enemies=[e];if(chase)use('chase');if(chase==='expired')B.chaseUntil=B.t;N.sim(.95);return 100000-e.hp;
 };
 const attacks={};for(const id of ['sword','fox','mage','blue','sister']){
  const normal=attack(id,false),triple=attack(id,true);attacks[id]={normal,triple};assert('triple normal attack '+id,normal>0&&Math.abs(triple/normal-3)<.001);
 }
 for(const id of ['sword','blue']){const normal=attack(id,false,true),triple=attack(id,true,true);assert('triple ranged fallback '+id+' '+normal+'/'+triple,normal>0&&Math.abs(triple/normal-3)<.001)}
 assert('multi remains additive',Math.abs(attack('fox',true,false,1)/attack('fox',false,false,0)-4)<.001);
 assert('chase expiry',attack('mage','expired')===attack('mage',false));
 // Real taboo collapse removes cards; revival must reconstruct the deck exactly once.
 start();B=N.B;B.allies[0].m.madness=99;N.grant('t_pact');const dead=B.allies[0];
 assert('test collapsed ally',!dead.alive&&dead.m.collapsed&&!B.queue.some(c=>c.owner===dead.d.id)&&!B.slots.some(s=>s.card?.owner===dead.d.id));
 B.allies[1].alive=false;B.allies[1].hp=0;B.allies[1].deadBy='hp';B.allies[1].m.madness=70;
 use('revive');assert('revive HP and madness',B.allies.slice(0,2).every(a=>a.alive&&!a.m.collapsed&&a.m.madness===0&&a.hp===a.max*.5&&a.deadBy===null));
 assert('restore collapsed skills',N.CARDS.filter(c=>c.owner===dead.d.id).every(c=>B.queue.concat(B.slots.map(s=>s.card).filter(Boolean)).filter(o=>o.id===c.id).length===1));
 const deck=skills();use('revive');assert('no duplicate revival skills',skills()===deck);N.sim(.5);assert('revived ally resumes',dead.cdT<.3);
 for(const used of [false,true]){
  start();B=N.B;B.allies[2].alive=false;for(const a of B.allies)if(used)B.ultUsed[a.d.id]=true;
  const old=JSON.stringify(B.ultUsed);use('ult');assert('ult uses living ally',!!N.ULT&&N.ULT.a.alive);assert('ult preserves normal rights '+used,JSON.stringify(B.ultUsed)===old);
  N.sim(.01);assert('ult completes '+used,!N.ULT&&B.impacts.length>0);
 }
 start();B=N.B;B.allies.forEach(a=>a.cdT=10000);B.life=10000;B.dur=10000;use('heal');
 N.sim(19.9);assert('strategy not early',!B.slots[4].card&&B.slots[4].refill>0);N.sim(.2);assert('strategy replenishes at 20',B.slots[4].card?.category==='strategy');
 return {checks,counts,attacks};
}"""
with sync_playwright() as p:
 b=p.chromium.launch();pg=b.new_page(viewport={'width':390,'height':844},has_touch=True,is_mobile=True);errors=[]
 pg.on('pageerror',lambda e:errors.append(str(e)))
 pg.goto(html.as_uri());pg.wait_for_function('window.NARAKU_READY')
 result=pg.evaluate(script);result['touch']={}
 for w,h in [(375,667),(390,664),(393,659),(393,852)]:
  pg.set_viewport_size({'width':w,'height':h})
  pg.evaluate("NARAKU.start(['sword','fox','mage'],4242);document.querySelector('#btnPause').click()")
  pg.wait_for_timeout(80)
  for i in range(4):
   pg.evaluate("i=>{NARAKU.B.slots[i].card=NARAKU.CARDS.find(c=>c.id==='fox_bind')}",i);pg.wait_for_timeout(40)
   pg.click('#btnPause');pg.locator(f'#hand [data-i="{i}"]').tap(position={'x':32,'y':32});pg.click('#btnPause')
   assert pg.evaluate('NARAKU.B.sel')==i
  for effect in ['heal','redraw','reset','chase','revive','ult']:
   pg.evaluate("effect=>{NARAKU.start(['sword','fox','mage'],4242);document.querySelector('#btnPause').click();NARAKU.B.slots[4].card=NARAKU.STRATEGIES.find(c=>c.effect===effect)}",effect)
   pg.wait_for_timeout(60);pg.screenshot(path=str(out/f'{effect}-{w}x{h}.png'))
   pg.click('#btnPause');pg.locator('#hand [data-i="4"]').tap(position={'x':32,'y':32});pg.wait_for_timeout(50)
   assert pg.evaluate('NARAKU.B.sel===4&&NARAKU.B.slots[4].card!==null'),(w,effect,'first tap selects')
   pg.evaluate("window.revealSeen=false;const observer=new MutationObserver(()=>{const el=document.querySelector('#strategyReveal');if(el){window.revealSeen=!!el.querySelector('.back img')&&!!el.querySelector('.front img');observer.disconnect()}});observer.observe(document.body,{childList:true})")
   pg.locator('#hand [data-i="4"]').tap(position={'x':32,'y':32});pg.wait_for_timeout(50)
   assert pg.evaluate('window.revealSeen'),(w,effect,'reveal mounted')
   assert pg.evaluate('NARAKU.B.slots[4].card===null&&NARAKU.B.slots[4].max===20'),(w,effect)
   pg.click('#btnPause')
  result['touch'][f'{w}x{h}']={'skillSlots':4,'strategyEffects':6}
 assert not errors,errors
 result['errors']=errors;b.close()
(out/'checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print('RESULT OK',json.dumps(result,ensure_ascii=False))

"""通常攻撃の中身を測る：1回の攻撃で何体に当たるか、攻撃していた時間の割合、削った体力の割合。
   使い方: python3 atk_probe.py <配布版.html> ['<CHARS上書きJSON>']"""
import sys, os, json
from playwright.sync_api import sync_playwright
html=os.path.abspath(sys.argv[1]); ov=json.loads(sys.argv[2]) if len(sys.argv)>2 else {}
JS=r"""([ids,seed,ov])=>{
  for(const k in ov)Object.assign(NARAKU.CHARS[k],ov[k]);
  if(!window._w){window._w=1;window.PS={};const h0=window.hitFrom,a0=window.allyHit;
    window.allyHit=function(a,tg,rep){const s=PS[a.d.id]||(PS[a.d.id]={n:0,hits:0,raw:0});s.n++;return a0(a,tg,rep)};
    window.hitFrom=function(a,e,k){const s=PS[a.d.id]||(PS[a.d.id]={n:0,hits:0,raw:0});s.hits++;s.raw+=a.d.dmg*NARAKU.B.M[a.tag].dmg*k;return h0(a,e,k)}}
  window.PS={};
  const BOT=(B)=>{const al=B.allies.filter(a=>a.alive);
    B.slots.forEach((s,i)=>{const c=s.card;if(!c)return;
      if(c.kind==='instant'){if(c.band){if(B.enemies.filter(e=>e.y>B.lineY-c.band).length>=4)NARAKU.useCard(i,0,0)}
        else if(al.some(a=>a.hp<a.max*0.55))NARAKU.useCard(i,0,0);return}
      if(c.shape==='col'){let bx=0,bn=0;for(let x=30;x<=330;x+=20){let n=0;for(const e of B.enemies){if(e.y<B.lineY&&Math.abs(e.x-x)<c.hw)n++}if(n>bn){bn=n;bx=x}}if(bn>=3)NARAKU.useCard(i,bx,B.lineY*0.5);return}
      if(c.shape==='row'){let bb=null,bn=0;for(const e of B.enemies){let n=0;for(const o of B.enemies){if(Math.abs(o.y-e.y)<c.hh)n++}if(n>bn){bn=n;bb=e}}if(bb&&bn>=4)NARAKU.useCard(i,180,bb.y-16);return}
      let best=null,bc=0;for(const e of B.enemies){if(e.y<20)continue;let n=0;for(const o of B.enemies){const dx=o.x-e.x,dy=o.y-e.y;if(dx*dx+dy*dy<c.r*c.r)n++}if(n>bc){bc=n;best=e}}
      if(best&&bc>=4)NARAKU.useCard(i,best.x,best.y-16)})};
  let rs=seed*7919+13;const rnd=()=>{rs=(rs*1103515245+12345)&0x7fffffff;return rs/0x7fffffff};
  const pick=(o,B)=>{const c=o.map((u,i)=>i).filter(i=>o[i].fam!=='taboo');return c[Math.floor(rnd()*c.length)]};
  NARAKU.start(ids,seed);const dead={};let m='battle';
  for(let t=0;t<NARAKU.CFG.dur+1&&(m==='battle'||m==='levelup');t++){m=NARAKU.sim(1,BOT,pick);NARAKU.B.allies.forEach(a=>{if(!a.alive&&dead[a.d.id]==null)dead[a.d.id]=NARAKU.B.t})}
  const B=NARAKU.B,t=B.t;
  return {win:m==='victory',rows:B.allies.map(a=>{const s=B.stat[a.d.id],q=PS[a.d.id]||{n:0,hits:0,raw:0};return [a.d.id,s.atk/t,s.skill/t,q.n,q.hits,q.raw,s.atk,dead[a.d.id]==null?t:dead[a.d.id],s.taken]})}}"""
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':390,'height':844})
    errs=[]; pg.on('pageerror',lambda e: errs.append(str(e)))
    pg.goto('file://'+html); pg.wait_for_timeout(1200)
    agg={}; wins=0; n=0
    for party in (['fox','sword','mage'],['blue','sword','sister'],['blue','fox','sword'],['blue','sister','mage'],['sword','sister','mage']):
        for seed in (1,2):
            r=pg.evaluate(JS,[party,seed,ov]); n+=1; wins+=r['win']
            for x in r['rows']:
                a=agg.setdefault(x[0],[0]*9); a[0]+=1
                for i in range(1,9): a[i]+=x[i]
    print(f'勝率 {wins}/{n}')
    print('キャラ   通常DPS スキルDPS  攻撃回数/分  1回の命中数  無駄撃ち%  生存秒 被ダメ')
    for k,a in sorted(agg.items(),key=lambda kv:-(kv[1][1]+kv[1][2])/kv[1][0]):
        c=a[0]; print(f'{k:7} {a[1]/c:7.0f} {a[2]/c:8.0f} {a[3]/a[7]*60:10.0f} {a[4]/max(1,a[3]):10.2f} {(1-a[6]/max(1,a[5]))*100:9.0f} {a[7]/c:7.0f} {a[8]/c:6.0f}')
    b.close(); print('errs',errs)

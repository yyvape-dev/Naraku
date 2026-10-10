"""難易度調整用。CFG / UPCFG を上書きして、強化の選び方ごとの戦績を並べる。
   使い方: python3 tune_sim.py <配布版.html> '<CFG上書きJSON>' '<UPCFG上書きJSON>' [seeds=1,2,3]"""
import sys, os, json
from playwright.sync_api import sync_playwright
html=os.path.abspath(sys.argv[1]); cfg=json.loads(sys.argv[2]) if len(sys.argv)>2 else {}; ucfg=json.loads(sys.argv[3]) if len(sys.argv)>3 else {}
seeds=[int(x) for x in (sys.argv[4].split('=')[1] if len(sys.argv)>4 else '1,2,3').split(',')]
JS=r"""([ids,seed,useBot,pol,cfg,ucfg])=>{
  Object.assign(NARAKU.CFG,cfg);Object.assign(NARAKU.UPCFG,ucfg);
  const BOT=(B)=>{const al=B.allies.filter(a=>a.alive);
    B.slots.forEach((s,i)=>{const c=s.card;if(!c)return;
      if(c.kind==='instant'){if(c.band){if(B.enemies.filter(e=>e.y>B.lineY-c.band).length>=4)NARAKU.useCard(i,0,0)}
        else if(al.some(a=>a.hp<a.max*0.55))NARAKU.useCard(i,0,0);return}
      if(c.shape==='col'){let bx=0,bn=0;for(let x=30;x<=330;x+=20){let n=0;for(const e of B.enemies){if(e.y<B.lineY&&Math.abs(e.x-x)<c.hw)n++}if(n>bn){bn=n;bx=x}}if(bn>=3)NARAKU.useCard(i,bx,B.lineY*0.5);return}
      if(c.shape==='row'){let bb=null,bn=0;for(const e of B.enemies){let n=0;for(const o of B.enemies){if(Math.abs(o.y-e.y)<c.hh)n++}if(n>bn){bn=n;bb=e}}if(bb&&bn>=4)NARAKU.useCard(i,180,bb.y-16);return}
      let best=null,bc=0;for(const e of B.enemies){if(e.y<20)continue;let n=0;for(const o of B.enemies){const dx=o.x-e.x,dy=o.y-e.y;if(dx*dx+dy*dy<c.r*c.r)n++}if(n>bc){bc=n;best=e}}
      if(best&&bc>=4)NARAKU.useCard(i,best.x,best.y-16)})};
  const PR=['p_multi','t_aura','t_pact','p_dmg','m_dmg','a_dmg','p_spd','m_spd','a_spd','p_crit','m_burn','m_pierce','s_dmg','s_echo','t_judge','s_r','s_reload','a_hp','s_range','p_knock','m_chill','s_soul','s_life','x_heal'];
  let rs=seed*7919+13;const rnd=()=>{rs=(rs*1103515245+12345)&0x7fffffff;return rs/0x7fffffff};
  const POL={none:null,
    rot:(o,B)=>{const c=o.map((u,i)=>i).filter(i=>o[i].fam!=='taboo');return c[B.lv%c.length]},
    rnd:(o,B)=>{const c=o.map((u,i)=>i).filter(i=>o[i].fam!=='taboo');return c[Math.floor(rnd()*c.length)]},
    dps:(o,B)=>{let b=0,bv=99;o.forEach((u,i)=>{const v=PR.indexOf(u.id);if(v<bv){bv=v;b=i}});return b}};
  NARAKU.start(ids,seed);let peak=0,m='battle';
  for(let t=0;t<NARAKU.CFG.dur+1&&(m==='battle'||m==='levelup');t++){m=NARAKU.sim(1,useBot?BOT:null,POL[pol]);peak=Math.max(peak,NARAKU.B.enemies.length)}
  const B=NARAKU.B;return [m==='victory'?'勝':'負',Math.round(B.t),B.lv,B.kills,peak,B.idx,Math.round(B.life)]}"""
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':390,'height':844})
    pg.goto('file://'+html); pg.wait_for_timeout(1200)
    print('形式: 勝敗/秒 Lv強化回数 k撃破 p同時最大 n出現総数 L拠点')
    tot={}
    for party in (['fox','sword','mage'],['blue','sword','sister'],['fox','sister','mage'],['blue','fox','sword']):
        print(' '.join(party))
        for bot,pol in ((0,'none'),(0,'rnd'),(1,'none'),(1,'rnd'),(1,'rot'),(1,'dps')):
            row=[]
            for sd in seeds:
                r=pg.evaluate(JS,[party,sd,bot,pol,cfg,ucfg]); row.append(f"{r[0]}{r[1]} Lv{r[2]} k{r[3]} p{r[4]} n{r[5]} L{r[6]}")
                key=('操縦' if bot else '放置')+'+'+pol; tot.setdefault(key,[0,0]); tot[key][1]+=1; tot[key][0]+=r[0]=='勝'
            print(f"  {'操縦' if bot else '放置'}+{pol:4}",' | '.join(row))
    print('勝率',{k:f'{v[0]}/{v[1]}' for k,v in tot.items()})
    b.close()

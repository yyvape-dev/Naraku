"""探索の難易度調整用（Step 4で装備と層に対応）。自動操縦で、マスごとの戦闘と、探索1回の通しを回して戦績を並べる。
   使い方: python3 run_sim.py <配布版.html> battle [seeds=1,2,3] ['<XCFG上書きJSON>' '<BKINDS上書きJSON>' '<CFG上書きJSON>']
           python3 run_sim.py <配布版.html> run    [seeds=1,2,3,4,5] [同上]
   battle … 戦闘の種類と深さごとの勝率・強化回数・勝ったときの残り体力・金
   run    … 探索の通し（道はシードで決めた適当な分岐。途中で帰還はしない）。踏破率と、どこで終わったか
   装備と層: gear=15（全員に ATK+15 の武器と DFN+15 の防具。無銘・固有と同じ属性）/ cross=1（武器を固有と逆の属性にする＝両方の札が効く）/ floor=2（第2層）"""
import sys, os, json
from playwright.sync_api import sync_playwright
html=os.path.abspath(sys.argv[1]); what=sys.argv[2] if len(sys.argv)>2 else 'battle'
rest=sys.argv[3:]; seeds=[1,2,3] if what=='battle' else [1,2,3,4,5]
G={k:int(v) for k,v in (x.split('=') for x in rest if x.split('=')[0] in ('gear','cross','floor'))}; rest=[x for x in rest if x.split('=')[0] not in ('gear','cross','floor')]
GEAR=[G.get('gear',0),G.get('cross',0),G.get('floor',1)]
if rest and rest[0].startswith('seeds='): seeds=[int(x) for x in rest[0].split('=')[1].split(',')]; rest=rest[1:]
ov=[json.loads(x) for x in rest]+[{},{},{}]
LIB=r"""window.T={
  BOT:(B)=>{const al=B.allies.filter(a=>a.alive);
    B.slots.forEach((s,i)=>{const c=s.card;if(!c)return;
      if(c.kind==='instant'){if(c.band){if(B.enemies.filter(e=>e.y>B.lineY-c.band).length>=4)NARAKU.useCard(i,0,0)}
        else if(al.some(a=>a.hp<a.max*0.55))NARAKU.useCard(i,0,0);return}
      if(c.shape==='col'){let bx=0,bn=0;for(let x=30;x<=330;x+=20){let n=0;for(const e of B.enemies){if(e.y<B.lineY&&Math.abs(e.x-x)<c.hw)n++}if(n>bn){bn=n;bx=x}}if(bn>=3)NARAKU.useCard(i,bx,B.lineY*0.5);return}
      if(c.shape==='row'){let bb=null,bn=0;for(const e of B.enemies){let n=0;for(const o of B.enemies){if(Math.abs(o.y-e.y)<c.hh)n++}if(n>bn){bn=n;bb=e}}if(bb&&bn>=4)NARAKU.useCard(i,180,bb.y-16);return}
      let best=null,bc=0;for(const e of B.enemies){if(e.y<20)continue;let n=0;for(const o of B.enemies){const dx=o.x-e.x,dy=o.y-e.y;if(dx*dx+dy*dy<c.r*c.r)n++}if(n>bc){bc=n;best=e}}
      if(best&&bc>=4)NARAKU.useCard(i,best.x,best.y-16)})},
  PR:['p_multi','t_aura','t_pact','p_dmg','m_dmg','a_dmg','p_spd','m_spd','a_spd','p_crit','m_burn','m_pierce','s_dmg','s_echo','t_judge','s_r','s_reload','a_hp','s_range','p_knock','m_chill','s_soul','s_life','x_heal'],
  rng(seed){let rs=seed*7919+13;return()=>{rs=(rs*1103515245+12345)&0x7fffffff;return rs/0x7fffffff}},
  pol(name,seed){const rnd=T.rng(seed);
    if(name==='rnd')return(o,B)=>{const c=o.map((u,i)=>i).filter(i=>o[i].fam!=='taboo');return c[Math.floor(rnd()*c.length)]};
    // 探索では狂気が持ち越されるので、火力優先でも禁忌は取らない
    if(name==='dps')return(o,B)=>{let b=0,bv=99;o.forEach((u,i)=>{if(u.fam==='taboo'&&NARAKU.R)return;const v=T.PR.indexOf(u.id);if(v<bv){bv=v;b=i}});return b};
    return null},
  set(x,k,c){Object.assign(NARAKU.XCFG,x);for(const n in k)Object.assign(NARAKU.BKINDS[n],k[n]);Object.assign(NARAKU.CFG,c)},
  // 戦闘1回。hp0=開始時の体力の割合
  // 装備を持たせる（pw=ATK・DFNの値。cross=武器を固有と逆の属性にする）
  arm(pw,cross){if(!pw)return;const mag={sister:1,mage:1};NARAKU.P.members.forEach(m=>{const mg=!!mag[m.id]!==!!cross;m.w={id:0,s:'w',b:mg?4:0,r:0,p:'',n:0,pw};m.a={id:0,s:'a',b:0,r:0,p:'',n:0,pw}})},
  fight(ids,seed,kind,depth,pol,hp0,G){
    NARAKU.start(ids,seed,{kind,depth,floor:G[2],gear:G[0]?{w:{id:0,s:'w',b:0,r:0,p:'',n:0,pw:G[0]},a:{id:0,s:'a',b:0,r:0,p:'',n:0,pw:G[0]}}:null});
    if(hp0<1){NARAKU.P.members.forEach(m=>{m.hpR=hp0});NARAKU.B.allies.forEach(a=>{a.hp=a.max*hp0})}
    const B0=NARAKU.B,m=NARAKU.sim(B0.dur+1,T.BOT,T.pol(pol,seed)),B=NARAKU.B;
    const hp=B.allies.reduce((v,a)=>v+(a.alive?a.hp/a.max:0),0)/B.allies.length;
    return{win:m==='victory',t:Math.round(B.t),lv:B.lv,hp:+hp.toFixed(2),down:B.allies.filter(a=>!a.alive).length,gold:B.gold,gear:B.loot.length,kills:B.kills,n:B.idx,life:B.life}},
  // 探索1回の通し
  run(ids,seed,pol,G){
    const rnd=T.rng(seed+101),pick=T.pol(pol,seed),log=[];
    NARAKU.startRun(ids,seed,G[2]);T.arm(G[0],G[1]);
    const hpAvg=()=>{const al=NARAKU.P.members.filter(m=>!m.collapsed);return al.length?al.reduce((v,m)=>v+m.hpR,0)/al.length:0};
    const madMax=()=>Math.max(...NARAKU.P.members.filter(m=>!m.collapsed).map(m=>m.madness),0);
    for(let g=0;g<400;g++){
      const m=NARAKU.mode,R=NARAKU.R;
      if(m==='settle')break;
      if(m==='map'){ // 道の選び方：見えているマスだけで判断する。体力が減っていれば休める場所へ、余裕がなければ強敵を避ける
        const nx=R.map.nodes[R.at].next,h=hpAvg(),sc=nx.map(id=>{const f=NARAKU.info(id),ty=R.map.nodes[id].type;
          if(f.lv!=='full')return 1+rnd();
          const w=h<0.6?{rest:9,camp:9,chest:5,event:4,battle:2,elite:0,boss:1}:h<0.85?{rest:4,camp:5,chest:5,event:4,battle:4,elite:1,boss:1}:{rest:1,camp:5,chest:5,event:4,battle:5,elite:4,boss:1};
          return w[ty]+rnd()});
        NARAKU.go(nx[sc.indexOf(Math.max(...sc))]);continue}
      if(m==='node'){const N=R.node,ty=N.n.type;
        if(N.phase==='pick'){
          let i=0;
          if(ty==='rest')i=(hpAvg()<0.75||madMax()<20)?0:1;
          else{const id=NARAKU.EVENTS[N.n.ev].id;
            if(id==='altar')i=0;else if(id==='wounded')i=R.light>40?0:2;else if(id==='spring')i=hpAvg()<0.5?0:1;
            else if(id==='ghost')i=R.light<=60?(R.gold>=60?0:(hpAvg()>0.7?1:2)):2;else if(id==='collapse')i=R.light>40?1:0;else i=0}
          if(!NARAKU.choose(i))NARAKU.choose(N.opts.length-1);
        }else if(N.phase==='shop'){
          for(let k=0;k<4&&hpAvg()<0.8&&NARAKU.buy('salve');k++);
          for(let k=0;k<4&&R.light<=50&&NARAKU.buy('oil');k++);
          if(madMax()>=35)NARAKU.buy('incense');
          NARAKU.leave();
        }else NARAKU.leave();
        continue}
      if(m==='battle'||m==='levelup'){const h0=hpAvg(),B0=NARAKU.B,r=NARAKU.sim(B0.dur+1,T.BOT,pick);
        log.push(B0.kind[0]+(r==='victory'?'○':'×')+Math.round(NARAKU.B.t)+'/Lv'+NARAKU.B.lv+'/体'+Math.round(h0*100));continue}
      if(m==='victory'){NARAKU.next();continue}
      if(m==='defeat'){ // 狂気に余裕があれば1度だけ逆転の右手を使う
        if(madMax()<=20&&NARAKU.startRewind()){NARAKU.updRewind(1.0);NARAKU.updRewind(0.8)}else NARAKU.giveUp();continue}
      break;
    }
    const R=NARAKU.R,P=NARAKU.P;
    return{end:R.end?R.end.kind:'?'+NARAKU.mode,L:R.map.nodes[R.at].L,steps:R.map.steps,wins:R.wins,gold:R.end?R.end.gold:0,gear:R.end?R.end.loot.length:0,light:R.light,rew:P.rewinds,mad:P.members.map(m=>m.madness),log:log.join(' ')}}
};"""
PARTIES=(['fox','sword','mage'],['blue','sword','sister'],['fox','sister','mage'],['blue','fox','sword'])
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':390,'height':844})
    errs=[]; pg.on('pageerror',lambda e: errs.append(str(e)[:200]))
    pg.goto('file://'+html); pg.wait_for_timeout(1200); pg.evaluate(LIB); pg.evaluate("([x,k,c])=>T.set(x,k,c)",ov[:3])
    if what=='battle':
        print('形式: 勝率 / 平均の強化回数 / 勝ったときの残り体力(%) / 勝ったときの戦闘不能の人数 / 金 / 装備   （4編成×シード',seeds,'）')
        for kind,depth,hp0 in (('battle',0,1),('battle',0.5,1),('battle',1,1),('battle',0.5,0.6),('elite',0.5,1),('elite',1,1),('ambush',0.5,1),('boss',1,1),('boss',1,0.6),('trial',0,1)):
            for pol in ('rnd','dps'):
                rs=[pg.evaluate("([ids,seed,kind,depth,pol,hp0,G])=>T.fight(ids,seed,kind,depth,pol,hp0,G)",[pa,sd,kind,depth,pol,hp0,GEAR]) for pa in PARTIES for sd in seeds]
                w=[r for r in rs if r['win']]; avg=lambda k,L:(sum(r[k] for r in L)/len(L)) if L else 0
                print(f"  {kind:6} 深さ{depth:<3} 開始体力{int(hp0*100):3}% {'適当' if pol=='rnd' else '火力'}: 勝 {len(w):2}/{len(rs)}  Lv{avg('lv',rs):4.1f}  残体力{avg('hp',w)*100:3.0f}%  不能{avg('down',w):.1f}人  金{avg('gold',rs):4.0f}  装備{avg('gear',rs):.1f}  出現{avg('n',rs):.0f}")
    else:
        print('探索の通し（途中で帰還しない。敗北時は狂気20%以下なら1度だけ逆転の右手）  装備',GEAR[0],'/ 逆属性の武器',GEAR[1],'/ 第',GEAR[2],'層')
        for pol in ('rnd','dps'):
            tot={}
            print(' 強化の選び方:', '適当' if pol=='rnd' else '火力優先')
            for pa in PARTIES:
                for sd in seeds:
                    r=pg.evaluate("([ids,seed,pol,G])=>T.run(ids,seed,pol,G)",[pa,sd,pol,GEAR]); tot[r['end']]=tot.get(r['end'],0)+1
                    print(f"   {' '.join(pa):18} seed{sd}: {r['end']:6} 歩{r['L']}/{r['steps']} 勝{r['wins']} 灯{r['light']:3}% 逆転{r['rew']} 狂気{r['mad']} 金{r['gold']} 装{r['gear']} | {r['log']}")
            print('   結果',tot)
    b.close(); print('errs',errs or 'なし')

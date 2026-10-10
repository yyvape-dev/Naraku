"""配布版HTMLの動作確認（ヘッドレスChromium）。使い方: python3 tests/smoke.py naraku_step4.html [shot.png] [shot_lvup.png] [shot_map.png] [shot_town.png]
   確認内容: 起動エラーなし / 全スプライトが本番素材 / 逆転の右手（敵の出現とドロップは同じ・強化は引き直し）/
             狂気の加算 / ソウル強化の決定性・確率誘導・禁忌の代償 /
             探索（マップの形・灯りの3段階・暗闇の狂気・体力の持ち越し・帰還と全滅）/
             装備（中身の決定性・ATK/DFN・属性タグ）/ 街（宿屋・教会・鍛冶屋・商店・編成）/ セーブ（写し・自動保存・探索の再開）/ 難易度の目安（自動操縦）
   NARAKU.start(ids,seed) は、Step 2までと同じ条件の単発180秒戦（探索とは別の検証用の入口）"""
import sys, os, json
from playwright.sync_api import sync_playwright
html=os.path.abspath(sys.argv[1]); shot=sys.argv[2] if len(sys.argv)>2 else None; shot2=sys.argv[3] if len(sys.argv)>3 else None; shot3=sys.argv[4] if len(sys.argv)>4 else None; shot4=sys.argv[5] if len(sys.argv)>5 else None
# スキルを撃つ自動操縦と、強化の選び方3種（rnd=適当 / dps=火力優先 / none=何も取らない）
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
  pol(name,seed){let rs=seed*7919+13;const rnd=()=>{rs=(rs*1103515245+12345)&0x7fffffff;return rs/0x7fffffff};
    if(name==='rnd')return(o,B)=>{const c=o.map((u,i)=>i).filter(i=>o[i].fam!=='taboo');return c[Math.floor(rnd()*c.length)]};
    if(name==='dps')return(o,B)=>{let b=0,bv=99;o.forEach((u,i)=>{const v=T.PR.indexOf(u.id);if(v<bv){bv=v;b=i}});return b};
    if(name==='first')return()=>0;
    return null},
  snap(){const B=NARAKU.B;return JSON.stringify([B.idx,B.kills,B.gold,B.loot.length,B.life,B.lv,+B.soul.toFixed(2),B.up,B.allies.map(a=>+a.hp.toFixed(3)),B.enemies.map(e=>[e.idx,e.type,+e.x.toFixed(2),+e.y.toFixed(2),+e.hp.toFixed(2)])])},
  // 最初のn回ぶんの提示（何も取らずに進めた場合）
  offers(n){const out=[];let g=0;while(out.length<n&&g++<4000){NARAKU.sim(1/60);if(NARAKU.mode==='levelup'){out.push(NARAKU.B.offer.map(u=>u.id).join('+'));NARAKU.pick(-1)}else if(NARAKU.mode!=='battle')break}return out}
};"""
errs=[]; ok=True
def check(name,cond,detail=''):
    global ok
    print(('  OK ' if cond else '  NG ')+name+((' … '+str(detail)) if detail!='' else '')); ok&=bool(cond)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':390,'height':844},device_scale_factor=2)
    pg.on('console',lambda m: errs.append(m.text) if m.type=='error' else None)
    pg.on('pageerror',lambda e: errs.append('PAGEERR '+str(e)))
    pg.goto('file://'+html); pg.wait_for_timeout(1500); pg.evaluate(LIB)
    fake=pg.evaluate("[...Object.keys(NARAKU.SPR.ally).filter(k=>!NARAKU.SPR.ally[k].real),...Object.keys(NARAKU.SPR.enemy).filter(k=>!NARAKU.SPR.enemy[k].real)]")
    print('仮絵のまま:',fake or 'なし')

    print('逆転の右手')
    # 注意: start と sim は同じ evaluate の中で呼ぶ（間に実時間が挟まると比較がずれる）
    r=pg.evaluate("""()=>{
      NARAKU.start(['fox','sword','mage'],4242);const sig=NARAKU.dropSig(4242);NARAKU.sim(70);const a=T.snap();
      NARAKU.startRewind();NARAKU.updRewind(1.0);const m1=NARAKU.P.members.map(m=>m.madness);NARAKU.updRewind(0.8);NARAKU.sim(70);const same=a===T.snap();
      NARAKU.startRewind();NARAKU.updRewind(1.0);NARAKU.updRewind(0.8);const m2=NARAKU.P.members.map(m=>m.madness);
      return {same,m1,m2,third:NARAKU.startRewind(),sig:sig===NARAKU.dropSig(4242)}}""")
    check('強化を取らなければ、巻き戻し後も敵の出現と展開が同じ',r['same'])
    check('狂気 +35% ずつ、3回目は不可',r['m1']==[35,35,35] and r['m2']==[70,70,70] and r['third'] is False,(r['m1'],r['m2']))
    check('ドロップ署名は不変',r['sig'])

    print('ソウル強化')
    r=pg.evaluate("""()=>{
      const run=()=>{NARAKU.start(['fox','sword','mage'],777);NARAKU.sim(80,null,T.pol('first'));return T.snap()};
      const a=run(),b=run();
      NARAKU.start(['fox','sword','mage'],777);const o1=T.offers(4);
      NARAKU.start(['fox','sword','mage'],777);const o1b=T.offers(4);
      NARAKU.startRewind();NARAKU.updRewind(1.0);NARAKU.updRewind(0.8);const o2=T.offers(4);
      return {det:a===b,lv:JSON.parse(a)[5],o1,same:o1.join()===o1b.join(),redraw:o1.join()!==o2.join(),o2}}""")
    check('同じシード・同じ選択なら同じ展開',r['det'],f"80秒で強化{r['lv']}回")
    check('同じシードなら提示も同じ',r['same'],r['o1'][:2])
    check('逆転の右手のあとは提示が引き直しになる',r['redraw'],r['o2'][:2])
    r=pg.evaluate("""()=>{
      const count=(ids)=>{const c={phys:0,mag:0,all:0,common:0,taboo:0};for(let s=1;s<=40;s++){NARAKU.start(ids,s);T.offers(6).forEach(o=>o.split('+').forEach(id=>{const u=NARAKU.UPS.find(x=>x.id===id);if(u)c[u.fam]++}))}return c};
      return {p3:count(['fox','sword','blue']),m2:count(['sister','mage','fox'])}}""")
    check('確率誘導：物理3人なら魔法の札は出ない',r['p3']['mag']==0 and r['p3']['phys']>r['p3']['common'],r['p3'])
    check('確率誘導：魔法2人・物理1人なら魔法の札が物理より多い',r['m2']['mag']>r['m2']['phys']>0,r['m2'])
    r=pg.evaluate("""()=>{
      NARAKU.start(['fox','sword','mage'],5);NARAKU.sim(3);const cd0=NARAKU.B.M.phys.spd;
      NARAKU.grant('t_aura');const m1=NARAKU.P.members.map(m=>m.madness),spd=NARAKU.B.M.phys.spd/cd0;
      NARAKU.grant('p_dmg');NARAKU.grant('p_dmg');NARAKU.grant('a_dmg');const dmg=NARAKU.B.M.phys.dmg,mdmg=NARAKU.B.M.mag.dmg;
      NARAKU.startRewind();NARAKU.updRewind(1.0);NARAKU.updRewind(0.8);
      return {m1,spd,dmg:+dmg.toFixed(3),mdmg:+mdmg.toFixed(3),after:Object.keys(NARAKU.B.up).length,mad:NARAKU.P.members.map(m=>m.madness)}}""")
    check('禁忌：狂気 +10%、攻撃速度2倍',r['m1']==[10,10,10] and r['spd']==2,r['m1'])
    check('掛け算：剛力×2と戦意高揚で物理 2.028倍、魔法は 1.2倍',r['dmg']==2.028 and r['mdmg']==1.2,(r['dmg'],r['mdmg']))
    check('逆転の右手で強化は消え、禁忌の狂気は残る',r['after']==0 and r['mad']==[45,45,45],r['mad'])

    print('探索（モジュールB）')
    r=pg.evaluate("""()=>{
      const bad=[],seen={};
      for(let s=1;s<=300;s++){
        const m=NARAKU.genMap(s),nd=m.nodes;seen[m.steps]=1;
        if(m.steps<7||m.steps>10)bad.push('steps@'+s);
        if(m.layers[0].length!==1||m.layers[m.steps].length!==1||nd[m.layers[m.steps][0]].type!=='boss')bad.push('ends@'+s);
        m.camps.forEach(L=>{if(m.layers[L].length!==1||nd[m.layers[L][0]].type!=='camp')bad.push('camp@'+s)});
        nd.forEach(n=>{
          if(n.L<m.steps){const want=m.layers[n.L+1].length===1?1:2;if(n.next.length<want||n.next.length>(n.n===1?4:3))bad.push('branch@'+s+':'+n.id);if(n.next.some(k=>nd[k].L!==n.L+1))bad.push('skip@'+s)}
          if(n.L>0&&!n.prev.length)bad.push('orphan@'+s);
          if(n.type==='event'&&!NARAKU.EVENTS[n.ev])bad.push('event@'+s);
        });
        m.layers.forEach(row=>{if(row.length>1&&!row.some(id=>nd[id].type==='battle'||nd[id].type==='elite'))bad.push('nofight@'+s)});
      }
      return {bad:bad.slice(0,5),steps:Object.keys(seen).join(','),same:JSON.stringify(NARAKU.genMap(77))===JSON.stringify(NARAKU.genMap(77)),diff:JSON.stringify(NARAKU.genMap(77))!==JSON.stringify(NARAKU.genMap(78))}}""")
    check('マップ300個：全7〜10歩／キャンプとボスへ収束／1歩ごとに2〜3分岐（1マスの段からは最大4）／行けないマスなし／どの段にも戦闘あり',not r['bad'] and r['steps']=='7,8,9,10',r['bad'] or r['steps'])
    check('同じシードなら同じマップ、違うシードなら違うマップ',r['same'] and r['diff'])
    r=pg.evaluate("""()=>{
      NARAKU.startRun(['fox','sword','mage'],3);const R=NARAKU.R,nd=R.map.nodes,a=nd[0].next[0],b=nd[a].next[0],far=R.map.layers[3][0];
      const lv=()=>[NARAKU.info(a).lv,NARAKU.info(b).lv,NARAKU.info(far).lv].join();
      const out={};[100,70,69,30,29,0].forEach(v=>{R.light=v;out[v]=NARAKU.light()+':'+lv()});
      R.light=69;out.hint=NARAKU.info(a).text===nd[a].hint&&NARAKU.info(a).name!==NARAKU.NODES[nd[a].type].name;
      return out}""")
    check('灯りの3段階：100〜70%は正体が見える／69〜30%は予兆だけ／29%以下は何も見えない（2歩より先は常に見えない）',
          r['100']==r['70']=='clear:full,full,far' and r['69']==r['30']=='dim:hint,hint,far' and r['29']==r['0']=='dark:none,none,far' and r['hint'],[r['70'],r['69'],r['29']])
    r=pg.evaluate("""()=>{
      const one=(light)=>{NARAKU.startRun(['fox','sword','mage'],3);const R=NARAKU.R;R.light=light;NARAKU.go(R.map.nodes[0].next[0]);return [R.light,NARAKU.P.members.map(m=>m.madness).join()]};
      const a=one(100),b=one(40),c=one(39);
      NARAKU.startRun(['fox','sword','mage'],3);NARAKU.P.members.forEach((m,i)=>{m.madness=[90,80,0][i]});NARAKU.R.light=20;NARAKU.go(NARAKU.R.map.nodes[0].next[0]);
      const fell=NARAKU.P.members.map(m=>m.collapsed).join();
      NARAKU.startRun(['fox','sword','mage'],3);NARAKU.P.members.forEach(m=>{m.madness=90});NARAKU.R.light=20;NARAKU.R.gold=50;const g0=NARAKU.S.gold;NARAKU.go(NARAKU.R.map.nodes[0].next[0]);
      return {a,b,c,fell,mad:[NARAKU.mode,NARAKU.R.end&&NARAKU.R.end.kind,NARAKU.S.gold-g0].join()}}""")
    check('1歩で灯り −10%。暗闇に入った1歩ごとに全員の狂気 +15%、100%で崩壊',r['a']==[90,'0,0,0'] and r['b']==[30,'0,0,0'] and r['c']==[29,'15,15,15'] and r['fell']=='true,false,false',(r['a'],r['b'],r['c'],r['fell']))
    check('暗闇で全員が精神崩壊すると探索は終わり、戦利品を失う',r['mad']=='settle,mad,0',r['mad'])
    r=pg.evaluate("""()=>{
      NARAKU.startRun(['fox','sword','mage'],3);const R=NARAKU.R,nd=R.map.nodes,P=NARAKU.P;
      const mapSig=JSON.stringify(R.map),bt=nd[0].next.find(id=>nd[id].type==='battle');
      NARAKU.go(bt);const B=NARAKU.B,o={kind:B.kind,dur:B.dur,boss:B.hasBoss,mode0:NARAKU.mode};
      // 逆転の右手：戦闘だけが巻き戻り、マップと持ち越しは変わらない
      NARAKU.sim(20);NARAKU.startRewind();NARAKU.updRewind(1.0);NARAKU.updRewind(0.8);
      o.rewind=NARAKU.B.t<0.5&&JSON.stringify(R.map)===mapSig&&R.at===bt&&P.members.every(m=>m.hpR===1&&m.madness===35);
      // 勝利：体力を持ち越す。戦闘不能の味方は30%で戻る
      const al=NARAKU.B.allies;al[0].alive=false;al[0].hp=0;al[0].deadBy='hp';al[1].hp=al[1].max*0.5;NARAKU.B.enemies.length=0;NARAKU.B.gold=77;NARAKU.B.loot=[NARAKU.mkItem(NARAKU.rng(5),0,0)];NARAKU.B.t=NARAKU.B.dur;
      o.end=NARAKU.sim(0.05);o.hpR=P.members.map(m=>+m.hpR.toFixed(2)).join();o.loot=[R.gold,R.loot.length,R.wins].join();
      NARAKU.next();o.mode1=NARAKU.mode;o.B=NARAKU.B===null;
      return o}""")
    check('マスの戦闘：通常は90秒・蠍の女王なし。逆転の右手はマップと持ち越しを変えない',r['kind']=='battle' and r['dur']==90 and r['boss'] is False and r['mode0']=='battle' and r['rewind'],(r['kind'],r['dur'],r['rewind']))
    check('勝利で体力と戦利品を持ち越し、戦闘不能の味方は体力30%で戻る',r['end']=='victory' and r['hpR']=='0.3,0.6,1' and r['loot']=='77,1,1' and r['mode1']=='map' and r['B'],(r['hpR'],r['loot'],r['mode1']))
    r=pg.evaluate("""()=>{
      const g0=NARAKU.TCFG.startGold,o={};
      NARAKU.startRun(['fox','sword','mage'],3);NARAKU.R.gold=123;NARAKU.R.loot=[NARAKU.mkItem(NARAKU.rng(1),0,0),NARAKU.mkItem(NARAKU.rng(2),0,0)];NARAKU.retreat();
      o.ret=[NARAKU.mode,NARAKU.R.end.kind,NARAKU.S.gold-g0,NARAKU.S.inv.length].join();
      NARAKU.startRun(['fox','sword','mage'],3);const R=NARAKU.R,nd=R.map.nodes;R.gold=500;
      NARAKU.go(nd[0].next.find(id=>nd[id].type==='battle'));NARAKU.B.allies.forEach(a=>{a.hp=0.01});
      o.def=NARAKU.sim(95);NARAKU.giveUp();o.wipe=[NARAKU.mode,NARAKU.R.end.kind,NARAKU.R.end.keep,NARAKU.S.gold-g0,NARAKU.S.inv.length,NARAKU.P.members.map(m=>m.hpR).join('/')].join();
      NARAKU.start(['fox','sword','mage'],9,{kind:'battle',depth:1});const B=NARAKU.B;o.deep=[B.dur,+B.hpK.toFixed(3),+B.dmgK.toFixed(3)].join();
      NARAKU.start(['fox','sword','mage'],9);o.trial=[NARAKU.B.dur,NARAKU.B.hpK,NARAKU.B.dmgK,NARAKU.B.ts,NARAKU.B.hasBoss].join();
      return o}""")
    check('帰還は金と装備を街へ持ち帰り、戦闘での全滅は未精算の戦利品をすべて失って全員が瀕死（体力10%）で戻る',r['ret']=='settle,return,123,2' and r['def']=='defeat' and r['wipe']=='settle,wipe,false,0,0,0.1/0.1/0.1',(r['ret'],r['wipe']))
    check('敵の強さ：最深部の通常戦は体力1.35倍・攻撃力1.2倍。単発の検証戦はStep 2と同じ条件',r['deep']=='90,1.35,1.2' and r['trial']=='180,1,1,1,true',(r['deep'],r['trial']))
    r=pg.evaluate("""()=>{
      const walk=()=>{NARAKU.startRun(['blue','sword','sister'],11);const log=[];
        for(let g=0;g<200&&NARAKU.mode!=='settle';g++){const R=NARAKU.R,m=NARAKU.mode;
          if(m==='map'){const nx=R.map.nodes[R.at].next,id=nx.find(k=>['battle','elite','boss'].indexOf(R.map.nodes[k].type)<0)??nx[0];NARAKU.go(id);log.push(R.map.nodes[id].type)}
          else if(m==='node'){const N=R.node;if(N.phase==='pick'){if(!NARAKU.choose(0))NARAKU.choose(N.opts.length-1)}else if(N.phase==='shop'){R.gold+=400;log.push(NARAKU.buy('oil'),NARAKU.buy('incense'),NARAKU.buy('incense'));NARAKU.leave()}else{log.push(N.res.join('/'));NARAKU.leave()}}
          else if(m==='battle'){NARAKU.B.enemies.length=0;NARAKU.B.t=NARAKU.B.dur;NARAKU.sim(0.05)}else if(m==='victory')NARAKU.next();else break}
        return JSON.stringify([log,NARAKU.R.gold,NARAKU.R.light,NARAKU.P.members.map(m=>[m.hpR,m.madness])])};
      const a=walk(),b=walk();return {same:a===b,end:NARAKU.R.end&&NARAKU.R.end.kind,log:JSON.parse(a)[0].filter(x=>typeof x==='string'&&x.length<7).join('→')}}""")
    check('入口からボス撃破まで通せて、宝箱・焚き火・異変・商人の結果は同じシードなら同じ',r['same'] and r['end']=='clear',r['log'])

    print('絵の差し替え（候補を置いて見比べる仕組み）')
    r=pg.evaluate("""()=>{
      const L=NARAKU.look,A=NARAKU.SPR.ally,MG=A.mage;A.mage=Object.assign({},MG,{frames:MG.frames.slice(0,6)}); // 全員12コマになったので、シェリを仮に6コマの絵にして確かめる
      const o={fox:A.fox.frames.length,none:[L.list('mage').join(),L.set('mage','new'),L.frames('fox'),L.frames('mage')].join('/')};
      // シェリに12コマの候補（中身はユズナミキの絵を借りる）を置いたことにして、切り替えを確かめる
      A.mage2=A.fox;o.list=L.list('mage').join();o.first=L.get('mage')+':'+L.frames('mage');
      const run=k=>{L.set('mage',k);NARAKU.start(['fox','sister','mage'],4242);NARAKU.sim(40);return T.snap()};
      const a=run('old'),b=run('new'),c=run('new6');
      o.same=a===b&&b===c;o.frames=['old','new','new6'].map(k=>{L.set('mage',k);return L.get('mage')+':'+L.frames('mage')}).join();o.bad=L.set('mage','constructor');
      delete A.mage2;o.back=L.get('mage')+':'+L.frames('mage');A.mage=MG;try{localStorage.removeItem('naraku_look_v1')}catch(e){}
      return o}""")
    check('ユズナミキの攻撃は12コマ（既定は今の絵）。候補が無いキャラは「今の絵」だけ',r['fox']==12 and r['none']=='old/false/12/6',r['none'])
    check('候補（<名前>2）を置くと 今の絵／新／新6コマ を切り替えられる。初めは新。戦闘の結果は変わらない',r['list']=='old,new,new6' and r['first']=='new:12' and r['same'] and r['frames']=='old:6,new:12,new6:6' and r['bad'] is False and r['back']=='old:6',(r['frames'],r['back']))

    print('モーションの緩急（コマを等間隔で再生しない）')
    r=pg.evaluate("""()=>{
      const M=NARAKU.MOTION,S=NARAKU.SPR,bad=[],o={};
      for(const k in M){const m=M[k],n=m.ms.length,set=S.ally[k]||S.enemy[k];
        if(!set||set.frames.length!==n)bad.push(k+':コマ数');
        if(Math.min(...m.ms)!==m.ms[m.hit])bad.push(k+':ヒットが最短でない');
        if(!(m.ms[0]>m.ms[m.hit]*2&&m.ms[n-1]>m.ms[m.hit]*2))bad.push(k+':待機と回収が短い');
        for(let i=m.hit+1;i<n-1;i++)if(m.ms[i+1]<m.ms[i])bad.push(k+':回収が徐々に長くなっていない');
        for(const h of [0.55,0.32,0.5,null]){let prev=0;const seen={};
          for(let j=0;j<4000;j++){const f=NARAKU.frameAt(m,n,j/4000,h);if(f<prev)bad.push(k+':逆戻り');prev=f;seen[f]=1}
          if(Object.keys(seen).length!==n)bad.push(k+':映らないコマがある@'+h);
          if(h!=null&&(NARAKU.frameAt(m,n,h,h)!==m.hit||NARAKU.frameAt(m,n,h-1e-6,h)!==m.hit-1))bad.push(k+':ヒットのコマが命中の瞬間に出ない@'+h)}}
      // 実際の長さでの配分：ユズナミキの通常攻撃（0.42秒）で、各コマが何ミリ秒映るか
      const m=M.fox,cnt=new Array(12).fill(0),N=42000;for(let j=0;j<N;j++)cnt[NARAKU.frameAt(m,12,j/N,NARAKU.HIT_AT)]++;
      o.fox=cnt.map(c=>Math.round(c/N*420));o.bad=bad;o.keys=Object.keys(M).filter(k=>!/2$/.test(k)).length; // 差し替え候補（<名前>2）の表は数えない
      
      o.uni=[0,0.2,0.5,0.99].map(u=>NARAKU.frameAt(null,6,u,0.55)).join();o.def=[!!NARAKU.motionOf('zzz',6),!!NARAKU.motionOf('zzz',12),NARAKU.motionOf('zzz',7)===null,NARAKU.motionOf('fox',6)===NARAKU.MOTION_DEF[6]].join();
      return o}""")
    check('全11体に緩急の表があり、ヒットが最短・待機と回収が長め・回収は徐々に長い。どの速さでもヒットのコマが命中の瞬間に出る',not r['bad'] and r['keys']==11,r['bad'] or 'ユズナミキ0.42秒の配分(ms) '+str(r['fox']))
    check('表の無い絵は、コマ数に合う仮の配分か等間隔で再生する',r['uni']=='0,1,3,5' and r['def']=='true,true,true,true',(r['uni'],r['def']))

    print('装備（モジュールD・軸1）')
    r=pg.evaluate("""()=>{
      const mk=(s,lv,b)=>NARAKU.mkItem(NARAKU.rng(s),lv,b),o={};
      o.same=JSON.stringify(mk(7,0.5,0))===JSON.stringify(mk(7,0.5,0));
      const rar=[0,0,0,0];let bad=0,up=0;for(let i=1;i<=3000;i++){const it=mk(i,0,0);rar[it.r]++;if((it.r>0)!==!!it.p||(it.p&&NARAKU.AFFIX[it.p].s!==it.s))bad++;if(mk(i,1,0).pw>it.pw)up++}
      o.rar=rar;o.bad=bad;o.up=up;o.boss=[...Array(200)].every((x,i)=>mk(i+1,0,2).r>=2);
      const d1=JSON.stringify(NARAKU.dropFor(99,5,true,0.5,false)),d2=JSON.stringify(NARAKU.dropFor(99,5,true,0.5,false));o.drop=d1===d2;
      // 物理のユズナミキに魔法の武器（迅雷の・強化+2）と防具（不屈の）を持たせる
      const g={w:{s:'w',b:4,r:1,p:'swift',n:2,pw:10},a:{s:'a',b:0,r:2,p:'vital',n:0,pw:20}};
      NARAKU.start(['fox','sword','mage'],5,{gear:g});const B=NARAKU.B,f=B.allies[0],m=B.allies[2];
      o.name=NARAKU.itemName(g.w)+'/'+NARAKU.itemName(g.a);o.pow=NARAKU.itemPow(g.w);
      o.tags=[f.tags.phys,f.tags.mag,m.tags.phys,m.tags.mag].join();o.max=+f.max.toFixed(2);o.base=[+f.M.dmg.toFixed(4),+f.M.spd.toFixed(4),f.g.dfn].join();
      const tc0=NARAKU.B.allies.filter(a=>a.tags.phys).length+'/'+NARAKU.B.allies.filter(a=>a.tags.mag).length;
      NARAKU.grant('p_dmg');NARAKU.grant('m_dmg');NARAKU.grant('a_dmg');
      o.tc=tc0;o.both=+f.M.dmg.toFixed(4);o.magOnly=+m.M.dmg.toFixed(4);
      // DFN 100 なら、受けるダメージはちょうど半分
      const taken=(pw)=>{NARAKU.start(['fox','sword','mage'],8,pw?{gear:{a:{s:'a',b:0,r:0,p:'',n:0,pw}}}:{});NARAKU.sim(32);const st=NARAKU.B.stat;return [st.fox.taken+st.sword.taken+st.mage.taken,NARAKU.B.allies.every(a=>a.alive)]};
      const t0=taken(0),t1=taken(100);o.dfn=[t0[0]>0&&t0[1]&&t1[1],+(t1[0]/t0[0]).toFixed(6)];
      return o}""")
    check('装備の中身は乱数だけで決まる。4つの格がすべて出て、無銘に二つ名は付かず、深いほど基礎値が高い',r['same'] and r['drop'] and all(v>0 for v in r['rar']) and r['bad']==0 and r['up']==3000,r['rar'])
    check('奈落の主の装備は英雄以上',r['boss'])
    check('名前は［二つ名］＋装備名＋［強化値］。強化+2で基礎値 10→12',r['name']=='迅雷の杖 +2/不屈の兜' and r['pow']==12,r['name'])
    check('属性タグは固有＋武器の両方（物理のユズナミキが魔法の武器で両方持ち）',r['tags']=='true,true,false,true' and r['tc']=='2/3',(r['tags'],r['tc']))
    check('ATK +12 で威力1.12倍、迅雷の（希少）で攻撃速度1.06倍、不屈の（英雄）で最大体力 +13%',r['base']=='1.12,1.06,20' and r['max']==round(95*1.13,2),(r['base'],r['max']))
    check('両方の属性を持つ味方には、物理と魔法の札が両方効く（全員の札は二重に数えない）',r['both']==round(1.3*1.3*1.2*1.12,4) and r['magOnly']==round(1.3*1.2*1.12,4),(r['both'],r['magOnly']))
    check('DFN 100 で受けるダメージが半分',r['dfn'][0] and r['dfn'][1]==0.5,r['dfn'])

    print('街（モジュールA）')
    r=pg.evaluate("""()=>{
      const o={},T=NARAKU.town;let S=NARAKU.fresh();
      o.start=[NARAKU.mode,S.gold,S.day,S.picks.join()].join();
      S.roster.fox.hpR=0.4;S.roster.fox.madness=35;
      o.bed=[T.inn(true),S.roster.fox.hpR,S.roster.fox.madness,S.gold,S.day,T.inn(true)].join();
      S.roster.sword.hpR=0.2;o.stable=[T.inn(false),S.roster.sword.hpR,S.roster.fox.madness,S.gold,T.inn(false)].join();
      // 教会
      const fall=id=>{const m=S.roster[id];m.collapsed=true;m.madness=100;m.hpR=0};
      fall('blue');o.poor=T.revive('blue');S.gold=300;o.rev=[T.revive('blue'),S.roster.blue.collapsed,S.roster.blue.hpR,S.roster.blue.madness,S.gold].join();
      fall('blue');fall('fox');fall('sword');o.alms=[T.revive('fox'),S.roster.fox.hpR,S.roster.fox.madness,S.gold,T.revive('blue')].join();
      // 編成：崩壊した仲間がいると出撃できない
      o.dive0=NARAKU.sortie(3);T.pick('sword');T.pick('blue');T.pick('sister');o.picks=S.picks.join();S.roster.blue.collapsed=false;S.roster.blue.madness=0;S.roster.blue.hpR=1;T.pick('blue');o.picks2=S.picks.join();
      // 鍛冶屋と装備
      S=NARAKU.fresh();S.gold=1000;S.mats=3;
      T.bank([{s:'w',b:0,r:0,p:'',n:0,pw:10},{s:'w',b:4,r:2,p:'skill',n:0,pw:15},{s:'a',b:1,r:1,p:'sturdy',n:0,pw:12},{s:'a',b:2,r:0,p:'',n:0,pw:8}]);
      const id=S.inv.map(i=>i.id);
      o.eq=[T.equip('fox',id[1]),T.equip('fox',id[0]),S.inv.length,S.roster.fox.w.id===id[0],T.equip('mage',id[0]),T.unequip('fox','w'),S.inv.length].join();
      T.equip('sword',id[2]);const g=NARAKU.gearStats(S.roster.sword);o.sturdy=g.dfn;
      o.enh=[T.enhance(id[2]),S.roster.sword.a.n,S.gold,S.mats,T.enhance(id[2]),S.gold,S.mats,T.enhance(id[2])].join();
      o.brk=[T.breakItem(id[2]),T.breakItem(id[1]),S.mats,JSON.stringify(T.breakAll(0)),S.inv.length,S.mats].join();
      o.shop=[T.buy('salve'),T.buy('oil'),T.buy('oil'),T.buy('oil'),S.bag.oil,S.bag.salve,S.gold].join();
      // 持ち越し：体力・狂気・装備を持って出撃し、荷物を使い、帰還すると街に残る
      S.roster.fox.hpR=0.5;S.roster.fox.madness=20;T.bank([{s:'w',b:0,r:0,p:'',n:0,pw:10}]);T.equip('fox',S.inv[0].id);
      o.sortie=NARAKU.sortie(3);const R=NARAKU.R,nd=R.map.nodes;R.light=50;NARAKU.bag();o.use=[NARAKU.use('oil'),R.light,S.bag.oil,NARAKU.use('incense'),NARAKU.leave(),NARAKU.mode].join();
      NARAKU.go(nd[0].next.find(k=>nd[k].type==='battle'));const a=NARAKU.B.allies[0];o.carry=[+(a.hp/a.max).toFixed(2),a.m.madness,a.g.atk>0,NARAKU.P.members[0]===S.roster.fox].join();
      NARAKU.startRewind();NARAKU.updRewind(1.0);NARAKU.updRewind(0.8);NARAKU.B.enemies.length=0;NARAKU.B.t=NARAKU.B.dur;NARAKU.sim(0.05);NARAKU.next();
      const d0=S.day;NARAKU.retreat();o.back=[NARAKU.mode,S.roster.fox.madness,S.roster.sword.madness,+S.roster.fox.hpR.toFixed(2),S.runs,S.day-d0,S.run].join();
      return o}""")
    check('はじめは街から。金150・出撃はユズナミキ／ラナ／シェリ',r['start']=='town,150,1,fox,sword,mage',r['start'])
    check('宿屋の寝台：金100で全員の体力が全快し狂気 −15%。金が足りなければ泊まれない',r['bed']=='true,1,20,50,2,false',r['bed'])
    check('宿屋の馬小屋：無料で体力が50%まで戻るだけ（狂気は下がらない）',r['stable']=='true,0.5,20,50,false',r['stable'])
    check('教会：金300で蘇生（体力50%・狂気50%）。金が足りなければ不可',r['poor'] is False and r['rev']=='true,false,0.5,50,0',(r['poor'],r['rev']))
    check('教会：戦える仲間が3人に満たず金も無いときは、施しの蘇生（無料・体力30%・狂気70%）。3人そろえば施しは終わる',r['alms']=='true,0.3,70,0,false',r['alms'])
    check('編成：崩壊した仲間がいると出撃できない。外して入れ替えられる',r['dive0'] is False and r['picks']=='fox,mage,sister' and r['picks2']=='fox,mage,sister',(r['dive0'],r['picks'],r['picks2']))
    check('装備の付け替え：替えた装備は倉庫に戻る。他人の装備は奪えない',r['eq']=='true,true,3,true,false,true,4' and r['sturdy']==12+6,(r['eq'],r['sturdy']))
    check('強化：金と資材を払って +1（希少は金60・資材1 → 金120・資材2）。足りなければ不可',r['enh']=='true,1,940,2,true,820,0,false',r['enh'])
    check('分解：身に着けている装備は分解できない。一括分解は無銘の鍛えていない装備だけ',r['brk']=='0,4,4,{"n":2,"y":2},0,6',r['brk'])
    check('商店：物資は持てる数まで（灯り油3）',r['shop']=='true,true,true,false,3,1,'+str(820-130-180),r['shop'])
    check('荷物：探索中に使うと、その場で効いて減る',r['sortie'] and r['use']=='true,80,2,false,true,map',r['use'])
    check('持ち越し：街の体力・狂気・装備のまま戦闘に入る（パーティは街の記録そのもの）',r['carry']=='0.5,20,true,true',r['carry'])
    check('帰還すると、狂気（逆転の右手 +35%）と体力が街に残り、1日が過ぎる',r['back']=='settle,55,35,0.6,1,1,',r['back'])
    r=pg.evaluate("""()=>{
      const o={};NARAKU.startRun(['blue','sword','sister'],11);const S=NARAKU.S,g0=S.gold;
      for(let g=0;g<200&&NARAKU.mode!=='settle';g++){const R=NARAKU.R,m=NARAKU.mode;
        if(m==='map'){const nx=R.map.nodes[R.at].next;NARAKU.go(nx.find(k=>['battle','elite','boss'].indexOf(R.map.nodes[k].type)<0)??nx[0])}
        else if(m==='node'){const N=R.node;if(N.phase==='pick'){if(!NARAKU.choose(0))NARAKU.choose(N.opts.length-1)}else NARAKU.leave()}
        else if(m==='battle'){NARAKU.B.enemies.length=0;NARAKU.B.t=NARAKU.B.dur;NARAKU.sim(0.05)}else if(m==='victory')NARAKU.next();else break}
      const e=NARAKU.R.end;o.clear=[e.kind,e.deeper,S.floorMax,S.floor,S.clears,S.gold-g0===e.gold,S.inv.length===e.loot.length,e.loot.some(i=>i.r>=2),S.inv.every(i=>i.id>0)].join();
      NARAKU.startRun(['fox','sword','mage'],3,2);const R=NARAKU.R,nd=R.map.nodes,bt=nd[0].next.find(id=>nd[id].type==='battle');NARAKU.go(bt);
      o.f2=[+NARAKU.B.hpK.toFixed(3),+NARAKU.B.dmgK.toFixed(3),NARAKU.B.goldK,NARAKU.B.ilv].join();
      return o}""")
    check('踏破すると次の層が開き、報酬（英雄以上の装備と金）が街の蓄えに入る',r['clear']=='clear,true,2,2,1,true,true,true,true',r['clear'])
    check('第2層：敵の体力1.2倍・攻撃力1.14倍・金1.3倍、装備の基礎値も上がる',r['f2']=='1.2,1.14,1.3,1',r['f2'])

    print('街のハブ画面（背景の絵・建物のタップ・駒・演出）')
    r=pg.evaluate("""async()=>{
      const o={},H=NARAKU.hub.HUB,S=NARAKU.fresh();S.roster.blue.collapsed=true;S.roster.blue.madness=100;S.roster.fox.hpR=0.5;NARAKU.town.show();
      await new Promise(r=>setTimeout(r,700));
      const inPoly=(p,x,y)=>{let c=false;for(let i=0,j=p.length-1;i<p.length;j=i++){const a=p[i],b=p[j];if((a[1]>y)!==(b[1]>y)&&x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0])c=!c}return c};
      const bad=[];
      H.fac.forEach(f=>{if(f.poly.some(q=>q[0]<0||q[0]>100||q[1]<0||q[1]>100))bad.push(f.k+':範囲外');if(!inPoly(f.poly,f.lb[0],f.lb[1]))bad.push(f.k+':名札が建物の外');
        H.fac.forEach(g=>{if(g!==f&&inPoly(g.poly,f.lb[0],f.lb[1]))bad.push(f.k+':'+g.k+'と重なる')})});
      // プレイヤーの駒の置き場（3体ぶん＋まわり）は、どの建物のタップ判定とも重ならない
      const A=H.party;for(let i=-1;i<=1;i++)for(const dy of [-A.ph,-A.ph/2,0,2])for(const dx of [-3,0,3])H.fac.forEach(f=>{if(inPoly(f.poly,A.x+i*A.dx+dx,A.y+dy))bad.push('駒が'+f.k+'に重なる')});
      o.bad=[...new Set(bad)];
      o.layers=['hubBg','hubFx','hubLights','hubLit','hubGlow','hubParty','hubHot'].map(id=>!!document.getElementById(id)).join();o.n=[document.querySelectorAll('.hub-hs').length,document.querySelectorAll('.hub-lb').length,document.querySelectorAll('#hubGlow polygon').length].join();
      // 実際の画面で、名札の位置を押すとその建物が反応する
      o.hit=H.fac.map(f=>{const r=document.querySelector('[data-lb="'+f.k+'"]').getBoundingClientRect(),e=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);return e&&e.dataset.fac===f.k}).join();
      const sc=document.querySelector('#hubScene').getBoundingClientRect(),pe=document.elementFromPoint(sc.left+sc.width*A.x/100,sc.top+sc.height*(A.y-A.ph/2)/100);o.plaza=!(pe&&pe.dataset&&pe.dataset.fac);
      o.none=[document.querySelector('#hubName').textContent,document.querySelector('#hubEnter').disabled,NARAKU.hub.sel].join();
      const tap=k=>{const r=document.querySelector('[data-lb="'+k+'"]').getBoundingClientRect();document.elementFromPoint(r.left+r.width/2,r.top+r.height/2).click()};
      tap('inn');o.sel=[NARAKU.hub.sel,document.querySelector('#hubName').textContent,document.querySelector('#hubEnter').disabled,document.querySelector('[data-g=inn]').classList.contains('sel'),document.querySelector('#hubLit').classList.contains('on'),document.querySelector('[data-lb=church]').textContent,document.querySelector('[data-lb=inn]').textContent].join();
      tap('smith');o.sel2=[NARAKU.hub.sel,document.querySelector('[data-g=inn]').classList.contains('sel'),document.querySelector('[data-g=smith]').classList.contains('sel'),NARAKU.mode].join();
      document.querySelector('#hubEnter').click();o.enter=document.querySelector('#screen h2').textContent+','+!!document.querySelector('#hub');
      document.querySelector('#screen .tw-back').click();o.back=[!!document.querySelector('#hub'),NARAKU.hub.sel].join();
      tap('church');tap('church');o.twice=document.querySelector('#screen h2').textContent;NARAKU.town.show();
      await new Promise(r=>setTimeout(r,900));
      const fx=document.querySelector('#hubFx'),pc=document.querySelector('#hubParty'),px=c=>{const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let n=0;for(let i=3;i<d.length;i+=4)if(d[i])n++;return n};
      o.anim=[fx.width>300,px(fx)>200,px(document.querySelector('#hubLights'))>200,px(pc)>200].join();
      o.dive=[document.querySelector('#hubDive').disabled,NARAKU.town.pick('fox'),(NARAKU.hub.tick(1e9),NARAKU.town.show(),document.querySelector('#hubDive').disabled),document.querySelector('#hubDiveSub').textContent].join();
      return o}""")
    check('6つの建物：輪郭は絵の中に収まり、名札は自分の建物の上。駒の置き場はどの建物とも重ならない',not r['bad'] and r['plaza'],r['bad'])
    check('層が分かれている（背景／演出／灯り／選択の光／駒／タップ判定と名札）',r['layers']=='true,true,true,true,true,true,true' and r['n']=='6,6,6',(r['layers'],r['n']))
    check('名札の位置を押すと、その建物が反応する',r['hit']=='true,true,true,true,true,true',r['hit'])
    check('初めは未選択で「入る」は押せない。建物を押すと光り、施設名と説明が出る（状況の印つき）',r['none']=='建物を選んでください,true,' and r['sel']=='inn,宿屋,false,true,true,教会崩壊 1,宿屋要休息 1',(r['none'],r['sel']))
    check('別の建物を押すと選択が移る。「入る」で施設へ、戻ると選択は残る。同じ建物をもう一度押しても入れる',r['sel2']=='smith,false,true,town' and r['enter']=='鍛冶屋,false' and r['back']=='true,smith' and r['twice']=='教会',(r['sel2'],r['enter'],r['back'],r['twice']))
    check('演出が動いている（布・煙・人の息づき／灯り／駒）',r['anim']=='true,true,true,true',r['anim'])
    check('3人そろわないと出撃できず、理由が出る',r['dive']=='false,true,true,酒場で、出撃する3人を選んでください',r['dive'])

    print('セーブ（廃屋）')
    r=pg.evaluate("""()=>{
      const o={},T=NARAKU.town;let S=NARAKU.fresh();S.gold=4321;S.mats=17;S.floorMax=3;S.floor=2;S.roster.mage.madness=45;S.roster.blue.collapsed=true;S.roster.blue.madness=100;S.roster.blue.hpR=0;
      const r=NARAKU.rng(4);T.bank([...Array(30)].map((x,i)=>NARAKU.mkItem(r,i/10,i%3)));T.equip('fox',S.inv.find(i=>i.s==='w').id);T.enhance(S.roster.fox.w.id);
      const before=NARAKU.saveText(),code=NARAKU.exportCode();o.len=code.length;o.line=!/\\s/.test(code)&&code.indexOf('NRK4.')===0;o.hidden=code.indexOf('gold')<0&&atob(code.split('.')[2].replace(/-/g,'+').replace(/_/g,'/')).indexOf('roster')<0;
      const back=NARAKU.importCode(code);o.round=!!back&&NARAKU.saveText(back)===before&&back.roster.fox.w.n===1&&back.gold===S.gold&&back.mats===S.mats&&back.floor===2&&back.roster.mage.madness===45&&back.inv.length===S.inv.length&&back.roster.blue.collapsed;o.dbg=[!!back,back&&NARAKU.saveText(back)===before,o.line,o.hidden];
      const i=code.length-9,bad=code.slice(0,i)+(code[i]==='A'?'B':'A')+code.slice(i+1);
      o.reject=[NARAKU.importCode(bad),NARAKU.importCode(code.slice(0,-20)),NARAKU.importCode('NRK4.zzz'),NARAKU.importCode('')].every(x=>x===null);
      o.spaces=!!NARAKU.importCode('  '+code.slice(0,40)+'\\n'+code.slice(40)+' ');
      const f=NARAKU.fixSave({v:1,gold:'x',mats:-5,floor:99,picks:['fox','fox','zzz'],inv:[{s:'w',b:99,r:9,p:'<img>',pw:1e9,n:99},{s:'q'},null,['a',1,2,'sword',5,1]],roster:{fox:{hpR:'a',madness:500,w:{s:'a',b:0,r:0,p:'',pw:5,n:0}}},bag:{oil:99}});
      o.fix=[f.gold,f.mats,f.floor,f.picks.join(),f.inv.length,f.inv[0].b,f.inv[0].r,f.inv[0].p,f.inv[0].pw,f.inv[0].n,f.inv[1].p,f.roster.fox.hpR,f.roster.fox.madness,f.roster.fox.w,f.bag.oil].join();
      return o}""")
    check('記録の写し：1行の英数字で、中身は読めない。貼り直すと街の状態がそのまま戻る',r['line'] and r['hidden'] and r['round'] and r['spaces'],f"装備30個で{r['len']}文字 {r['dbg'] if not r['round'] else ''}")
    check('書き換えた写し・途中で切れた写しは弾く',r['reject'])
    check('壊れた記録は正しい形に直して読む（範囲外の数・知らない二つ名・枠の違う装備）',r['fix']=='0,0,1,fox,2,7,3,,999,10,,1,99,,3',r['fix'])
    # 自動保存：本物の localStorage で、閉じて開き直しても続きから（ここだけ自動保存を入れたまま動かす）
    pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(1500); pg.evaluate(LIB)
    r1=pg.evaluate("()=>{const S=NARAKU.S,T=NARAKU.town;S.gold=777;T.buy('oil');S.roster.fox.madness=40;T.bank([NARAKU.mkItem(NARAKU.rng(1),0,2)]);T.equip('sword',S.inv[0].id);return [NARAKU.saveOk,S.gold,NARAKU.itemName(S.roster.sword.w||S.roster.sword.a)]}")
    pg.reload(); pg.wait_for_timeout(1500); pg.evaluate(LIB)
    r2=pg.evaluate("()=>{const S=NARAKU.S;return [NARAKU.mode,S.gold,S.bag.oil,S.roster.fox.madness,NARAKU.itemName(S.roster.sword.w||S.roster.sword.a),S.inv.length]}")
    check('自動保存：開き直しても、金・荷物・狂気・装備が残る',r1[0] is True and r2==['town',687,2,40,r1[2],0],r2)
    r3=pg.evaluate("""()=>{NARAKU.sortie(3);const R=NARAKU.R,nd=R.map.nodes,ch=nd[0].next.find(k=>nd[k].type!=='battle')??nd[0].next[0];
      NARAKU.go(nd[0].next.find(k=>nd[k].type==='battle'));NARAKU.sim(10);NARAKU.startRewind();NARAKU.updRewind(1.0);NARAKU.updRewind(0.8);NARAKU.B.enemies.length=0;NARAKU.B.gold=55;NARAKU.B.t=NARAKU.B.dur;NARAKU.sim(0.05);NARAKU.next();
      const b2=nd[R.at].next.find(k=>nd[k].type==='battle'||nd[k].type==='elite');NARAKU.go(b2);NARAKU.sim(5);
      return [R.seed,R.at,R.light,R.gold,NARAKU.mode,NARAKU.P.members.map(m=>m.madness).join()]}""")
    pg.reload(); pg.wait_for_timeout(1500); pg.evaluate(LIB)
    r4=pg.evaluate("()=>{const h=document.querySelector('#screen h1');const o=[NARAKU.mode,h&&h.textContent,NARAKU.R===null,!!NARAKU.S.run];document.querySelector('#screen [data-act=resume]').click();const R=NARAKU.R;return o.concat([R.seed,R.at,R.light,R.gold,NARAKU.mode,NARAKU.B&&NARAKU.B.t<0.5,NARAKU.P.members.map(m=>m.madness).join(),NARAKU.P.rewinds,R.wins])}")
    check('探索の途中で閉じても、たどり着いたマスの最初から再開する（勝った戦闘の戦利品と、逆転の右手の狂気は残る）',
          r4[:4]==['town','探索の途中',True,True] and r4[4:8]==r3[:4] and r3[3]==55 and r4[8]=='battle' and r4[9] is True and r4[10]==r3[5]=='75,35,35' and r4[11]==1 and r4[12]==1,(r3,r4[4:]))
    r5=pg.evaluate("()=>{NARAKU.B.allies.forEach(a=>{a.hp=0.01});NARAKU.sim(95);NARAKU.giveUp();const S=NARAKU.S;return [NARAKU.mode,S.run,S.runs,S.roster.fox.hpR]}")
    pg.reload(); pg.wait_for_timeout(1500); pg.evaluate(LIB)
    r6=pg.evaluate("()=>{const S=NARAKU.S,o=[NARAKU.mode,S.runs,S.roster.fox.hpR,S.roster.fox.madness,!!S.run];localStorage.clear();return o}")
    check('探索が終われば途中経過は消え、結果（全滅で瀕死）だけが街に残る',r5[:3]==['settle',None,1] and r6==['town',1,0.1,75,False],(r5,r6))
    pg.reload(); pg.wait_for_timeout(1500); pg.evaluate(LIB)

    print('難易度の目安（単発の180秒戦。各3シード。勝敗と到達秒、Lv=強化回数）')
    tot={}
    for party in (['fox','sword','mage'],['blue','sword','sister'],['fox','sister','mage'],['blue','fox','sword']):
        line=[]
        for bot,pol,label in ((0,'rnd','放置・適当'),(1,'none','操縦・強化なし'),(1,'rnd','操縦・適当'),(1,'dps','操縦・火力優先')):
            row=[]
            for seed in (1,2,3):
                m,t,lv=pg.evaluate("([ids,seed,bot,pol])=>{NARAKU.start(ids,seed);const m=NARAKU.sim(NARAKU.CFG.dur+1,bot?T.BOT:null,T.pol(pol,seed));return [m,Math.round(NARAKU.B.t),NARAKU.B.lv]}",[party,seed,bot,pol])
                row.append(f"{'勝' if m=='victory' else '負'}{t}/Lv{lv}")
                tot.setdefault(label,[0,0]); tot[label][1]+=1; tot[label][0]+=m=='victory'
            line.append(label+' '+' '.join(row))
        print(' ',' '.join(party)); [print('    '+x) for x in line]
    print('  勝率',{k:f'{v[0]}/{v[1]}' for k,v in tot.items()})
    if shot:
        pg.evaluate("()=>{NARAKU.start(['blue','sword','sister'],31);NARAKU.sim(150,T.BOT,T.pol('dps',31))}"); pg.wait_for_timeout(400); pg.screenshot(path=shot)
    if shot2:
        pg.evaluate("()=>{NARAKU.start(['fox','sword','mage'],31);for(let i=0;i<4000&&!(NARAKU.mode==='levelup'&&NARAKU.B.offer.some(u=>u.fam==='taboo'));i++){if(NARAKU.mode==='levelup')NARAKU.pick(0);else NARAKU.sim(1/60,T.BOT)}}"); pg.wait_for_timeout(700); pg.screenshot(path=shot2)
    if shot3:
        pg.evaluate("()=>{NARAKU.startRun(['fox','sword','mage'],3);NARAKU.R.light=60;NARAKU.R.sel=NARAKU.R.map.nodes[0].next[1]}"); pg.wait_for_timeout(500); pg.screenshot(path=shot3)
    if shot4:
        pg.evaluate("()=>{const S=NARAKU.fresh();S.gold=640;S.mats=9;NARAKU.town.bank([...Array(6)].map((x,i)=>NARAKU.mkItem(NARAKU.rng(i+3),0.5,i%3)));NARAKU.town.equip('fox',S.inv[0].id);S.roster.fox.hpR=0.6;S.roster.mage.madness=35;NARAKU.town.show()}"); pg.wait_for_timeout(400); pg.screenshot(path=shot4)
    b.close()
print('エラー:',errs or 'なし'); print('RESULT','OK' if ok and not errs and not fake else 'NG')

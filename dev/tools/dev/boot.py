"""実際の操作（タップ）で、起動→街→出撃→マップ→各マス→戦闘→勝利→マップ→帰還→街の各施設→開き直し（自動保存）→探索の再開までを通す。
   使い方: python3 boot.py <配布版.html> <出力png> [切り詰めバイト数]"""
import sys, os, re
from playwright.sync_api import sync_playwright
html=os.path.abspath(sys.argv[1]); out=sys.argv[2]; cut=int(sys.argv[3]) if len(sys.argv)>3 else 0
if cut:
    d=open(html,'rb').read()[:cut]; html=out+'.cut.html'; open(html,'wb').write(d)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':390,'height':844},device_scale_factor=1)
    errs=[]; pg.on('pageerror',lambda e: errs.append(str(e)[:120])); pg.on('console',lambda m: errs.append(m.text[:120]) if m.type=='error' else None)
    pg.goto('file://'+html); pg.wait_for_timeout(600)
    if not cut: pg.evaluate('try{localStorage.clear()}catch(e){}'); pg.reload()   # 前回の記録を消して、最初の起動から始める
    pg.wait_for_timeout(2500 if not cut else 7500)
    title=pg.evaluate("()=>{const s=document.querySelector('#screen');return !s.classList.contains('on')?null:s.querySelector('#hub')?'街（ハブ画面）':s.querySelector('h1,h2').textContent}")
    print('起動直後の画面:',title or '（タイトルが出ていない）','/ 見張りの表示:',pg.evaluate("()=>{const d=document.getElementById('bootErr');return d?d.textContent.split('\\n')[0]:'なし'}"))
    if cut: pg.screenshot(path=out,clip={'x':0,'y':0,'width':390,'height':420}); b.close(); print('errs',errs[:2]); sys.exit()
    mode=lambda: pg.evaluate("NARAKU.mode")
    head=lambda: pg.evaluate("document.querySelector('#screen #hub')?'街（ハブ画面）':document.querySelector('#screen h1,#screen h2').textContent")
    def fac(k,w=250):   # 街のハブ画面：建物（名札の位置）をタップして選び、「入る」で入る
        xy=pg.evaluate("k=>{const r=document.querySelector('[data-lb=\"'+k+'\"]').getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2]}",k)
        pg.mouse.click(xy[0],xy[1]); pg.wait_for_timeout(200); sel=pg.evaluate('NARAKU.hub.sel')
        if pg.query_selector('#hubEnter'): pg.click('#hubEnter')   # すでに選んでいた建物は、押した時点で入っている
        pg.wait_for_timeout(w)
        if pg.query_selector('#screen [data-fopen]'): pg.click('#screen [data-fopen]'); pg.wait_for_timeout(450)   # 施設の画面：入口のコマンドで中身の板を開く
        return sel
    def home():   # 施設から街のハブ画面へ戻る（施設の画面では、1回目の「戻る」で板を閉じる）
        for _ in range(4):
            if pg.query_selector('#screen #hub'): return
            pg.click('#screen .tw-back'); pg.wait_for_timeout(300)
    pg.screenshot(path=out.replace('.png','_town.png'))
    pg.click('[data-act=dive]'); pg.wait_for_timeout(500)
    print('出撃: mode',mode(),'/ 全',pg.evaluate("NARAKU.R.map.steps"),'歩 / 行き先の札',pg.evaluate("document.querySelectorAll('#hand [data-node]').length"),'枚 / 灯り',pg.evaluate("NARAKU.R.light"),'%')
    pg.screenshot(path=out.replace('.png','_map.png'))
    # マップ上のマスをタップして情報を見る（進まない）
    xy=pg.evaluate("()=>{const r=document.querySelector('#cv').getBoundingClientRect(),R=NARAKU.R,q=NARAKU.nodeXY(R.map.nodes[R.map.nodes[0].next[0]].next[0]);return [r.left+r.width*q.x,r.top+r.height*q.y]}")
    pg.mouse.click(xy[0],xy[1]); pg.wait_for_timeout(150); print('マップをタップ: 選択',pg.evaluate("NARAKU.R.sel"),'/ 案内「'+pg.evaluate("document.querySelector('#hint').textContent")[:24]+'」')
    # 戦闘に入るまで、札を選んで進む。戦闘以外のマスは画面の選択肢を押して抜ける
    for i in range(8):
        if mode()!='map': break
        want=pg.evaluate("()=>{const R=NARAKU.R,nx=R.map.nodes[R.at].next;return nx.find(k=>R.map.nodes[k].type==='battle')??nx[0]}")
        pg.click(f'#hand [data-node="{want}"]'); pg.wait_for_timeout(120)
        go_dis=pg.evaluate("document.querySelector('#btnGo').disabled"); pg.click('#btnGo'); pg.wait_for_timeout(900)
        ty=pg.evaluate("NARAKU.R.map.nodes[NARAKU.R.at].type"); print(f'  {i+1}歩目: 札を選ぶ→「進む」(押せる={not go_dis}) → {ty} / mode',mode(),'/ 灯り',pg.evaluate("NARAKU.R.light"),'%')
        for j in range(4):
            if mode()!='node': break
            pg.wait_for_timeout(320)
            if pg.query_selector('#screen [data-opt]'): pg.click('#screen [data-opt]:last-of-type')
            else: pg.click('#screen [data-act=leave]')
            pg.wait_for_timeout(200)
    t1=pg.evaluate("NARAKU.B.t"); print('戦闘開始: mode',mode(),'種類',pg.evaluate("NARAKU.B.kind"),'長さ',pg.evaluate("NARAKU.B.dur"),'秒 / 戦場',pg.evaluate("NARAKU.B.bg"))
    pg.wait_for_timeout(2500); print('2.5秒後: 経過',round(pg.evaluate("NARAKU.B.t"),1),'秒 / 敵',pg.evaluate("NARAKU.B.enemies.length"),'体')
    pg.click('#btnSpeed')
    for i in range(60):
        pg.wait_for_timeout(500)
        if mode()=='levelup': break
    print('強化の選択が出た: mode',mode(),'経過',round(pg.evaluate("NARAKU.B.t"),1),'秒')
    pg.wait_for_timeout(600); pg.click('#lvCards .up:nth-child(1)'); pg.wait_for_timeout(1200)
    print('札を選んだ後: mode',mode(),'強化',pg.evaluate("JSON.stringify(NARAKU.B.up)"))
    c=pg.evaluate("()=>{const el=[...document.querySelectorAll('#hand .card')].find(e=>!e.classList.contains('empty')&&!e.classList.contains('back')&&e.querySelector('.kd,.ki').textContent!=='即時');el.click();return el.querySelector('.nm,.sn').textContent}")
    k0=pg.evaluate("NARAKU.B.kills"); bx=pg.evaluate("()=>{const r=document.querySelector('#cv').getBoundingClientRect();return [r.left+r.width/2,r.top+r.height*0.45]}")
    pg.mouse.move(bx[0],bx[1]); pg.mouse.down(); pg.wait_for_timeout(120); pg.mouse.up(); pg.wait_for_timeout(900)
    print('スキル',c,'を戦場タップで発動: 撃破',k0,'→',pg.evaluate("NARAKU.B.kills"))
    if mode()=='levelup': pg.wait_for_timeout(600); pg.click('#lvCards .up:nth-child(1)'); pg.wait_for_timeout(300)
    pg.click('#btnRewind'); pg.wait_for_timeout(2300)
    print('逆転の右手の後: mode',mode(),'経過',round(pg.evaluate("NARAKU.B.t"),1),'秒 / 狂気',pg.evaluate("NARAKU.P.members.map(m=>m.madness)"))
    pg.screenshot(path=out)
    # 残り時間を飛ばして勝利させ、結果画面のボタンでマップへ戻る
    pg.evaluate("()=>{const B=NARAKU.B;B.enemies.length=0;B.allies[2].hp=B.allies[2].max*0.4;B.t=B.dur-0.2}"); pg.wait_for_timeout(900)
    print('時間切れ: mode',mode(),'/ 画面「'+pg.evaluate("document.querySelector('#screen h1').textContent")+'」/ ボタン',pg.evaluate("[...document.querySelectorAll('#screen [data-act]')].map(b=>b.textContent)"))
    pg.click('#screen [data-act=next]'); pg.wait_for_timeout(600)
    print('マップへ戻る: mode',mode(),'/ 未精算 金',pg.evaluate("NARAKU.R.gold"),'装備',pg.evaluate("NARAKU.R.loot.length"),'/ 帯の体力',pg.evaluate("[...document.querySelectorAll('#party .hp em')].map(e=>e.textContent)"),'/ サイドエリア',pg.evaluate("getComputedStyle(document.querySelector('#rail')).display"))
    pg.screenshot(path=out.replace('.png','_map2.png'))
    pg.click('#btnBack'); pg.wait_for_timeout(450); print('街へ帰還: 画面「'+pg.evaluate("document.querySelector('#screen h1').textContent")+'」')
    pg.evaluate("()=>{NARAKU.R.gold+=400;NARAKU.R.loot.push(NARAKU.mkItem(NARAKU.rng(3),0.3,1),NARAKU.mkItem(NARAKU.rng(9),0.3,0),NARAKU.mkItem(NARAKU.rng(12),0.3,0))}")   # 街で試すぶんの戦利品を足しておく
    pg.click('#screen [data-act=retreat]'); pg.wait_for_timeout(300)
    print('精算: mode',mode(),'/ 画面「'+head()+'」/ 持ち帰った装備',pg.evaluate("document.querySelectorAll('#screen .loot .it').length"),'個 / 街の蓄え 金',pg.evaluate("NARAKU.S.gold"))
    pg.screenshot(path=out.replace('.png','_settle.png'))
    pg.click('#screen [data-act=town]'); pg.wait_for_timeout(300); print('街へ戻る: mode',mode(),'/ 画面「'+head()+'」/ 狂気',pg.evaluate("NARAKU.S.picks.map(id=>NARAKU.S.roster[id].madness)"),'/ 体力',pg.evaluate("NARAKU.S.picks.map(id=>+NARAKU.S.roster[id].hpR.toFixed(2))"))
    # 街の各施設を、タップだけで回る
    tap=lambda sel,w=250:(pg.click(sel),pg.wait_for_timeout(w))
    hub=pg.evaluate("()=>{const xy=k=>{const r=document.querySelector('[data-lb=\"'+k+'\"]').getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2]};return ['church','hut','party','shop','smith','inn'].map(k=>{const p=xy(k),e=document.elementFromPoint(p[0],p[1]);return e&&e.dataset.fac===k})}")
    print('ハブ画面: 6つの建物それぞれ、名札の位置で正しい建物が反応する',hub)
    S=lambda e: pg.evaluate('NARAKU.S.'+e)
    fac('inn'); g0=S('gold')
    if pg.query_selector('#screen [data-innstay]'): tap('#screen [data-innsel=bed]'); tap('#screen [data-innstay]',700); pg.screenshot(path=out.replace('.png','_inn_night.png')); tap('#screen .inn-night',300); tap('#screen .inn-night',700)   # 台帳の画面：寝台を選んで休む → 演出をタップで飛ばす
    else: tap('#screen [data-inn=bed]')
    print('宿屋の寝台: 画面「'+head()+'」/ 金',g0,'→',S('gold'),'/ 狂気',pg.evaluate("NARAKU.S.picks.map(id=>NARAKU.S.roster[id].madness)"),'/ 体力',pg.evaluate("NARAKU.S.picks.map(id=>NARAKU.S.roster[id].hpR)"),'/',S('day'),'日目')
    home(); fac('shop'); tap('#screen [data-shop=salve]'); print('商店: 傷薬',S('bag.salve'),'個 / 金',S('gold'))
    home(); fac('party'); tap('#screen [data-tvch=fox] .nb' if pg.query_selector('#screen .tv-row') else '#screen [data-go=char][data-arg=fox]')   # 酒場の板（仲間表）なら行をタップして詳細へ
    pg.screenshot(path=out.replace('.png','_tvchar.png')); tap('#screen [data-go=pick][data-arg="fox:w"]')
    n_w=pg.evaluate("document.querySelectorAll('#screen [data-eq]').length")
    if n_w: tap('#screen [data-eq]')
    else: tap('#screen .tw-back'); tap('#screen [data-go=pick][data-arg="fox:a"]'); tap('#screen [data-eq]')
    print('酒場→装備: 画面「'+head()+'」/ ユズナミキの装備',pg.evaluate("(()=>{const m=NARAKU.S.roster.fox;return [m.w,m.a].filter(Boolean).map(NARAKU.itemName).join('・')})()"),'/ 属性',pg.evaluate("JSON.stringify(NARAKU.gearStats(NARAKU.S.roster.fox).tags)"))
    pg.screenshot(path=out.replace('.png','_char.png'))
    home(); fac('smith'); tap('#screen [data-smode=enh]',500); tap('#screen [data-sel]'); m0=S('mats')
    can=pg.evaluate("!!document.querySelector('#screen [data-brk]:not([disabled])')")
    if can: tap('#screen [data-brk]')
    else: tap('#screen [data-sel]:nth-of-type(3)'); tap('#screen [data-brk]')
    tap('#screen [data-sel]'); e0=pg.evaluate("document.querySelector('#screen [data-enh]').disabled"); tap('#screen [data-enh]') if not e0 else None
    print('鍛冶屋: 分解で資材',m0,'→',S('mats'),'/ 強化',('済み' if not e0 else '不可（資材か金が足りない）'),'/ 倉庫',S('inv.length'),'個 / 知らせ「'+(pg.evaluate("(document.querySelector('#screen .tw-msg')||{}).textContent||''"))+'」')
    pg.screenshot(path=out.replace('.png','_smith.png'))
    home(); fac('church'); print('教会: 画面「'+head()+'」/ 蘇生の対象',pg.evaluate("document.querySelectorAll('#screen [data-rev]').length"),'人')
    home(); fac('hut'); code=pg.evaluate("document.querySelector('#svCode').value"); print('廃屋: 写し',len(code),'文字 / 自動保存',pg.evaluate("NARAKU.saveOk"))
    norm=lambda: re.sub(r'"nid":\d+','',pg.evaluate("NARAKU.saveText()"))   # 倉庫の通し番号は復元で振り直すので、比べない
    snap=norm()
    # 記録を消して、写しから復元する（押し直しで確定）
    tap('#screen [data-act=reset]'); tap('#screen [data-act=reset]'); g1=S('gold'); fac('hut')
    pg.fill('#svIn',code); tap('#screen [data-act=import]'); print('記録を消す→写しから復元: 金',g1,'→',S('gold'),'/ 元どおり',norm()==snap,'/ 画面「'+head()+'」')
    # 開き直しても街の状態が残る（自動保存）
    pg.reload(); pg.wait_for_timeout(2000); print('開き直し: mode',mode(),'/ 画面「'+head()+'」/ 記録が残っている',norm()==snap)
    # もう一度出撃して1歩進み、探索の途中で開き直す
    pg.click('[data-act=dive]'); pg.wait_for_timeout(500)
    want=pg.evaluate("()=>{const R=NARAKU.R,nx=R.map.nodes[R.at].next;return nx[0]}"); pg.click(f'#hand [data-node="{want}"]'); pg.wait_for_timeout(120); pg.click('#btnGo'); pg.wait_for_timeout(1100)
    at=pg.evaluate("[NARAKU.R.at,NARAKU.R.light,NARAKU.mode]")
    pg.reload(); pg.wait_for_timeout(2000); print('探索の途中で開き直し: 画面「'+head()+'」'); pg.screenshot(path=out.replace('.png','_resume.png'))
    pg.click('#screen [data-act=resume]'); pg.wait_for_timeout(600); print('再開: 進んだマス',at,'→',pg.evaluate("[NARAKU.R.at,NARAKU.R.light,NARAKU.mode]"))
    pg.evaluate('try{localStorage.clear()}catch(e){}')
    b.close(); print('errs',errs or 'なし')

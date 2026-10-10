"""街の各画面を撮る（見た目の確認用）。使い方: python3 town_shots.py <配布版.html> <出力フォルダ>
   倉庫に装備を入れ、仲間を負傷・崩壊させた状態を作ってから、街・酒場・装備・鍛冶屋・商店・宿屋・教会・廃屋を順に撮る"""
import sys, os
from playwright.sync_api import sync_playwright
html=os.path.abspath(sys.argv[1]); out=sys.argv[2]; os.makedirs(out,exist_ok=True)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':390,'height':844},device_scale_factor=2)
    errs=[]; pg.on('pageerror',lambda e: errs.append(str(e)[:200])); pg.on('console',lambda m: errs.append(m.text[:200]) if m.type=='error' else None)
    pg.goto('file://'+html); pg.wait_for_timeout(1800)
    pg.evaluate("""()=>{const S=NARAKU.fresh();S.gold=1840;S.mats=23;S.day=6;S.runs=5;S.clears=1;S.floorMax=2;S.floor=2;S.bag.salve=2;
      const r=NARAKU.rng(11),L=[];for(let i=0;i<14;i++)L.push(NARAKU.mkItem(r,i/14*1.6,i%5===0?2:i%3===0?1:0));NARAKU.town.bank(L);
      const w=S.inv.filter(i=>i.s==='w'),a=S.inv.filter(i=>i.s==='a');
      NARAKU.town.equip('fox',w[0].id);NARAKU.town.equip('mage',w[1].id);NARAKU.town.equip('sword',a[0].id);NARAKU.town.enhance(w[0].id);NARAKU.town.enhance(w[0].id);
      S.roster.fox.hpR=0.45;S.roster.fox.madness=35;S.roster.sword.hpR=0.8;S.roster.mage.madness=70;S.roster.blue.collapsed=true;S.roster.blue.madness=100;S.roster.blue.hpR=0;
      NARAKU.town.show()}""")
    def shot(name,view=None,arg=None,pre=None):
        if view: pg.evaluate("([v,a])=>NARAKU.town.view(v,a)",[view,arg])
        if pre: pg.evaluate(pre)
        pg.wait_for_timeout(250); pg.screenshot(path=f'{out}/{name}.png')
    def both(name,v):   # 施設の画面：入口と、中身の板を開いたところ
        pg.evaluate("()=>NARAKU.town.show()"); shot(name,v); pg.wait_for_timeout(500); pg.screenshot(path=f'{out}/{name}.png')
        if pg.query_selector('#screen [data-fopen]'): pg.click('#screen [data-fopen]'); pg.wait_for_timeout(550); pg.screenshot(path=f'{out}/{name}_open.png')
    shot('1_town'); both('2_party','party'); shot('3_char','char','fox'); pg.wait_for_timeout(400); pg.screenshot(path=f'{out}/3_char.png'); shot('4_pick','pick','fox:w')
    shot('5_smith','smith'); pg.wait_for_timeout(600); pg.screenshot(path=f'{out}/5_smith.png')
    shot('5b_smith_list',None,None,"()=>{document.querySelector('#screen [data-smode=enh]').click()}"); pg.wait_for_timeout(500); pg.screenshot(path=f'{out}/5b_smith_list.png')
    shot('5c_smith_brk',None,None,"()=>{document.querySelector('#screen [data-fclose]').click();document.querySelector('#screen [data-smode=brk]').click()}"); pg.wait_for_timeout(500); pg.screenshot(path=f'{out}/5c_smith_brk.png')
    both('6_shop','shop'); both('7_inn','inn'); both('8_church','church'); both('9_hut','hut')
    b.close(); print('errs',errs or 'なし')

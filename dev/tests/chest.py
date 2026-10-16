"""宝箱の実操作・表示・連打・保存再開を確認し、2サイズの画面を撮る。
使い方: python3 dev/tests/chest.py index.html <出力dir> [変更前のHTML]
変更前HTMLがあれば、40シードの取得結果と保存内容が一致することも確認する。
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

html = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
out.mkdir(parents=True, exist_ok=True)
baseline = Path(sys.argv[3]).resolve() if len(sys.argv) > 3 else None
checks = []


def check(name, condition, detail=None):
    checks.append({"name": name, "ok": bool(condition), "detail": detail})
    print(("OK " if condition else "NG ") + name, detail or "", flush=True)
    assert condition, name


def ready(pg, path):
    pg.goto(path.as_uri())
    pg.wait_for_function("window.NARAKU_READY === true", timeout=30000)


with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 390, "height": 844})
    pg = ctx.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    ready(pg, html)
    seeds = pg.evaluate("""() => {
      const out=[];
      for(let seed=1;out.length<40;seed++){
        const map=NARAKU.genMap(seed),id=map.nodes[0].next.find(id=>map.nodes[id].type==='chest');
        if(id!==undefined)out.push({seed,id});
      }
      return out;
    }""")
    collect = """cases => cases.map(({seed,id}) => {
      NARAKU.startRun(['fox','sword','mage'],seed);NARAKU.go(id);
      return {seed,res:NARAKU.R.node.res,save:NARAKU.saveText()};
    })"""
    actual = pg.evaluate(collect, seeds)
    if baseline:
        old = ctx.new_page()
        ready(old, baseline)
        expected = old.evaluate(collect, seeds)
        check("変更前と40シードの宝箱報酬・保存内容が完全一致", actual == expected)
        old.close()
    chosen = next(c for c, result in zip(seeds, actual) if len(result["res"]) == 3)
    ctx.close()

    for width, height in [(390, 844), (375, 667)]:
        ctx = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=1, is_mobile=True, has_touch=True)
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        ready(pg, html)
        pg.evaluate("seed=>{NARAKU.S.picks=['fox','sword','mage'];NARAKU.sortie(seed)}", chosen["seed"])
        # マップの札と「進む」を実際にタップして到着する。
        pg.locator(f'#hand [data-node="{chosen["id"]}"]').tap()
        pg.locator('#btnGo').tap()
        pg.wait_for_selector('#screen.chest', timeout=10000)
        pg.wait_for_function("[...document.querySelectorAll('.chest-art img')].every(i => i.complete && i.naturalWidth > 0)")
        pg.wait_for_timeout(400)
        size = pg.evaluate("(()=>{const i=document.querySelector('.chest-art img');return [i.naturalWidth,i.naturalHeight]})()")
        check(f"{width}×{height}: 4:3の宝箱画像を表示", size == [1280, 960], size)
        check(f"{width}×{height}: 開く前は閉じた宝箱の画像", pg.evaluate("document.querySelector('.chest-illustration').getAttribute('src') === EVENT_ART.chest"))
        image_layout = pg.evaluate("(()=>{const i=document.querySelector('.chest-art img'),r=i.getBoundingClientRect();return {w:r.width,h:r.height,fit:getComputedStyle(i).objectFit}})()")
        check(f"{width}×{height}: 4:3の全体を全幅で表示（トリミングなし）", abs(image_layout['w'] / image_layout['h'] - 4 / 3) < .001 and image_layout['fit'] == 'contain' and abs(image_layout['w'] - width) < .5 and image_layout['h'] <= height * .46, image_layout)
        check(f"{width}×{height}: 開く前は結果を隠し、進行を無効化", pg.locator('.chest-results').count() == 0 and pg.locator('.chest-next').is_disabled())
        snapshot = pg.evaluate('NARAKU.saveText()')
        rewards = pg.evaluate('NARAKU.R.node.res')
        layout = pg.evaluate("""() => {
          const selectors=['.chest-head','.pstrip','.chest-art','.chest-body','.chest-controls','.chest-foot'];
          return selectors.map(s=>{const r=document.querySelector('#screen '+s).getBoundingClientRect();return {s,x:r.x,y:r.y,w:r.width,h:r.height,bottom:r.bottom}});
        }""")
        check(f"{width}×{height}: 全要素が画面内・縦スクロールなし", all(r['x'] >= 0 and r['y'] >= 0 and r['bottom'] <= height + .5 and r['w'] <= width + .5 for r in layout) and pg.evaluate('document.querySelector("#screen").scrollHeight <= document.querySelector("#screen").clientHeight'), layout)
        stem = f"chest-{width}x{height}"
        pg.screenshot(path=str(out / f'{stem}-before.png'))
        pg.locator('.chest-open').tap()
        pg.wait_for_selector('.chest-results')
        check(f"{width}×{height}: タップ後は開いた宝箱の画像に切り替わる", pg.evaluate("document.querySelector('.chest-illustration').getAttribute('src') === EVENT_ART.chest_open && EVENT_ART.chest !== EVENT_ART.chest_open"))
        check(f"{width}×{height}: タップで金色の開錠演出・効果音を開始", pg.locator('#screen.unlocking').count() == 1 and pg.evaluate("chestAudio && chestAudio.state === 'running'"))
        pg.wait_for_timeout(120)
        pg.screenshot(path=str(out / f'{stem}-opening.png'))
        # DOMを連打しても、最初の開錠後は同じ報酬の表示だけになる。
        duplicate = pg.evaluate("""() => {
          for(let i=0;i<20;i++)revealChest();
          const res=NARAKU.R.node.res.slice();showNode();
          return {res,save:NARAKU.saveText()};
        }""")
        check(f"{width}×{height}: 20回連打・画面再表示で再抽選・二重取得なし", duplicate['save'] == snapshot and duplicate['res'] == rewards)
        rendered = pg.locator('.chest-results li').all_text_contents()
        check(f"{width}×{height}: 装備・金・灯りの既存結果を表示", rendered == rewards, rendered)
        narrative = pg.locator('.chest-description').inner_text()
        check(f"{width}×{height}: 元のイベント本文と油の発見を省略せず表示", narrative == pg.evaluate('NARAKU.R.node.text') and '底には油の小瓶も転がっていた。' in narrative, narrative)
        result_image = pg.evaluate("(()=>{const r=document.querySelector('.chest-art img').getBoundingClientRect();return {w:r.width,h:r.height}})()")
        check(f"{width}×{height}: 取得結果でも画像のサイズが変わらない", abs(result_image['w'] - image_layout['w']) < .5 and abs(result_image['h'] - image_layout['h']) < .5, result_image)
        pg.wait_for_timeout(300)
        pg.screenshot(path=str(out / f'{stem}-result.png'))
        check(f"{width}×{height}: 結果も画面内に収まる", pg.evaluate('document.querySelector("#screen").scrollHeight <= document.querySelector("#screen").clientHeight') and pg.locator('.chest-next').is_enabled())
        pg.locator('.chest-next').tap()
        check(f"{width}×{height}: 先へ進む→探索へ正常復帰", pg.evaluate('NARAKU.mode === "map" && !NARAKU.R.node && !document.querySelector("#screen").classList.contains("on")'))
        pg.wait_for_timeout(300)
        pg.screenshot(path=str(out / f'{stem}-map.png'))
        saved = pg.evaluate("JSON.parse(localStorage.getItem('naraku_save_v1')).run")
        check(f"{width}×{height}: 取得済みフラグと報酬が実際に自動保存される", bool(saved['done'].get(str(chosen['id']))) and saved['gold'] > 0 and len(saved['loot']) == 1)
        # 取得後に閉じて再開しても、完了済み宝箱を開き直さない。
        for repeat in range(2):
            pg.reload()
            pg.wait_for_function('window.NARAKU_READY === true')
            pg.locator('[data-act=resume]').tap()
            restored = pg.evaluate('({mode:NARAKU.mode,gold:NARAKU.R.gold,light:NARAKU.R.light,loot:NARAKU.R.loot.length,at:NARAKU.R.at})')
            check(f"{width}×{height}: 保存再開{repeat+1}回目も取得済みで探索に復帰", restored == {'mode':'map','gold':saved['gold'],'light':saved['light'],'loot':len(saved['loot']),'at':chosen['id']}, restored)
        # 開く前に閉じた場合も、元の到着時保存を維持し、報酬を再付与しない。
        pg.evaluate("seed=>{NARAKU.town.show();NARAKU.sortie(seed)}", chosen['seed'])
        pg.locator(f'#hand [data-node="{chosen["id"]}"]').tap()
        pg.locator('#btnGo').tap()
        pg.wait_for_selector('#screen.chest')
        before = pg.evaluate('({gold:NARAKU.R.gold,light:NARAKU.R.light,loot:NARAKU.R.loot.length})')
        pg.reload()
        pg.wait_for_function('window.NARAKU_READY === true')
        pg.locator('[data-act=resume]').tap()
        check(f"{width}×{height}: 開く前の中断でも報酬・保存仕様は変更なし", before == pg.evaluate('({gold:NARAKU.R.gold,light:NARAKU.R.light,loot:NARAKU.R.loot.length})') and pg.evaluate('NARAKU.mode') == 'map')
        ctx.close()
    # 画像未配置・破損で、代替画像や完了画面に進まない。
    ctx = browser.new_context(viewport={"width":390,"height":844})
    pg = ctx.new_page()
    ready(pg, html)
    assets = pg.evaluate('({chest:EVENT_ART.chest,chest_open:EVENT_ART.chest_open})')
    for which in ['chest', 'chest_open']:
        for invalid in ['', 'data:image/webp;base64,broken']:
            pg.evaluate("({seed,id,which,invalid,assets})=>{Object.assign(EVENT_ART,assets);EVENT_ART[which]=invalid;NARAKU.startRun(['fox','sword','mage'],seed);NARAKU.go(id)}", {**chosen, 'which':which, 'invalid':invalid, 'assets':assets})
            pg.wait_for_timeout(350)
            check(which + ': 画像未配置・破損はエラー表示、開錠と進行を停止', pg.locator('.chest-error').is_visible() and pg.locator('.chest-open').is_disabled() and pg.locator('.chest-next').is_disabled())
    ctx.close()
    check('通常操作でJavaScript・コンソールエラーなし', not errors, errors)
    browser.close()

(out / 'chest-tests.json').write_text(json.dumps({'seed':chosen,'checks':checks}, ensure_ascii=False, indent=2), encoding='utf-8')
print('RESULT OK', flush=True)

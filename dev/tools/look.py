"""味方の絵（背面スプライト）の差し替え。候補を置く → ゲームの中で見比べる → 確定か取り消し、の3つをコマンド1つずつで行う。
   使い方: python3 tools/look.py add <キャラ名> <新しいシート画像> [bake.py のオプション…]   候補として焼き込む（assets/<キャラ名>2.webp）
           python3 tools/look.py promote <キャラ名>                                          候補を本採用にする（今の絵は消える）
           python3 tools/look.py drop <キャラ名>                                             候補を取り消す
   キャラ名: fox（ユズナミキ）/ sword（ラナ）/ sister（マリアンヌ）/ mage（シェリ）/ blue（アベニウス）
   add のあとビルドして公開すると、戦闘中の「調整」→ そのキャラ →「絵」の段で 今の絵／新／新6コマ を切り替えられる。
   横6コマ×2段で1つの動きになっているシートは seq=2 を付ける（例: look.py add fox sheet.png seq=2）。
   注意: 候補が入っているあいだは絵が2つぶん入るので、軽量版（2MB未満）には収まらないことがある。公開ページは問題ない。"""
import sys, os, json, subprocess
here=os.path.dirname(os.path.abspath(__file__)); A=os.path.join(os.path.dirname(here),'assets')
if len(sys.argv)<3 or sys.argv[1] not in ('add','promote','drop'): raise SystemExit(__doc__)
cmd,name=sys.argv[1],sys.argv[2]; alt=name+'2'
if not os.path.exists(f'{A}/{name}.json'): raise SystemExit(f'{name} という味方の素材がありません')
xp=f'{A}/extra.json'; extra=json.load(open(xp)) if os.path.exists(xp) else {}
def put(): json.dump(extra,open(xp,'w'))
if cmd=='add':
    if len(sys.argv)<4: raise SystemExit('画像を指定してください')
    subprocess.check_call([sys.executable,f'{here}/bake.py',sys.argv[3],alt,f'out={A}']+sys.argv[4:])
    if os.path.exists(f'{A}/{alt}.png'): os.remove(f'{A}/{alt}.png')     # 確認用のPNGは配布に要らない
    extra[alt]={'target':'ally'}; put()
    m=json.load(open(f'{A}/{alt}.json')); print(f'候補 {alt} を置きました（{m["cols"]}コマ）。ビルドして、調整パネルで見比べてください')
else:
    if not os.path.exists(f'{A}/{alt}.webp'): raise SystemExit(f'{name} の候補（{alt}）がありません')
    for ext in ('webp','json'):
        if cmd=='promote': os.replace(f'{A}/{alt}.{ext}',f'{A}/{name}.{ext}')
        else: os.remove(f'{A}/{alt}.{ext}')
    extra.pop(alt,None); put()
    print(f'{name} を新しい絵に入れ替えました' if cmd=='promote' else f'{name} の候補を取り消しました')

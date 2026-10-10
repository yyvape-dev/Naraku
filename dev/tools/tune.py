"""ユーザーが調整パネルからコピーした調整コードを tune.json に固定値として書き込む。
   使い方: python3 tune.py "NRK1 fox:100,0,0 sword:94,0,-2 …" [素材フォルダ=assets]
   形式: <目印> <名前>:<大きさ%>,<左右px>,<上下px> …。既定値(100,0,0)は保存しない。
   既存の tune.json に上書き合成するので、コードに載っていない名前の値は残る。
   複数のコードを受け取ったときは、古い順に1つずつ実行する（ページを開き直すと未保存の値が100に戻るため、
   後のコードで100に戻っている項目は「リセット」か「意図した変更」かをユーザーに確認する）。"""
import sys, json, os
code=sys.argv[1].split(); d=sys.argv[2] if len(sys.argv)>2 else 'assets'
p=f'{d}/tune.json'; cur=json.load(open(p)) if os.path.exists(p) else {}
for part in code[1:]:
    k,v=part.split(':'); s,x,y=[int(float(n)) for n in v.split(',')]
    if (s,x,y)==(100,0,0): cur.pop(k,None)
    else: cur[k]={'s':s,'x':x,'y':y}
json.dump(cur,open(p,'w')); print('tune.json',cur)

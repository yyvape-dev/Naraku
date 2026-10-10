"""配布版HTMLを、Claudeの公開ページ（アーティファクト）用の形に直す。使い方: python3 to_artifact.py <配布版.html> <出力.html> [確認用.html]
   公開時に <!doctype>〜<body> の外枠が自動で付くので、外枠のタグを外して中身だけにする。
   外枠が上下にスマホの安全域ぶんの余白を取るので、画面の高さは 100vh ではなく 100% にし、自前の安全域の余白は外す。"""
import sys, re
src,out=sys.argv[1],sys.argv[2]; s=open(src,encoding='utf-8').read()
def rep(o,n):
    global s
    assert s.count(o)==1,o[:50]; s=s.replace(o,n)
s=re.sub(r'<!DOCTYPE html>\s*<html[^>]*>\s*<head>\s*','',s,1); s=re.sub(r'<meta[^>]*>\s*','',s)
rep('</head>\n<body>\n',''); s=re.sub(r'</body>\s*</html>\s*$','',s)
s=re.sub(r'<title>.*?</title>','<title>奈落の防衛前線</title>',s,1)
rep(':root{\n  --soot:',':root{\n  color-scheme:dark;\n  --soot:')
rep('#app{position:relative;height:100vh;height:100dvh;','#app{position:relative;height:100%;')
rep('padding:8px 8px calc(8px + env(safe-area-inset-bottom))}','padding:8px}')
assert s.lstrip().startswith('<title>') and '<html' not in s and '<body' not in s
open(out,'w',encoding='utf-8').write(s); print('artifact',out,len(s.encode())//1024,'KB')
if len(sys.argv)>3:  # 公開時の外枠をまねた確認用（手元のテストだけに使う）
    open(sys.argv[3],'w',encoding='utf-8').write('<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><style>:root{color-scheme:light;padding:env(safe-area-inset-top,0px) 0 env(safe-area-inset-bottom,0px)}body{margin:0;font:14px system-ui;background:#faf9f5}img{max-width:100%}[hidden]{display:none!important}</style></head><body>'+s+'</body></html>')

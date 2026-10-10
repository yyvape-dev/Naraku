"""軽量ソースHTML + 素材フォルダ → 画像入りの配布用HTML（ワンファイル）を作る。
   使い方: python3 embed.py <ソース.html> <出力.html> [素材フォルダ=assets]
   ソース側に置く目印（中身はビルドのたびに差し替わる。目印が無いものは無視される）:
     const EMBED=/*__EMBED_START__*/{}/*__EMBED_END__*/;   ← <名前>.webp と <名前>.json の組すべて（アトラス）
     const TUNE =/*__TUNE_START__*/{}/*__TUNE_END__*/;     ← tune.json（表示の微調整値）
     const FACES=/*__FACES_START__*/{}/*__FACES_END__*/;   ← face_<名前>.webp（目印名を小文字にして末尾のsを取ったものが接頭辞）
   extra.json があれば、{"名前":{…}} をアトラスのメタ情報に合成する（例: {"fox":{"target":"ally"}}）。"""
import sys, re, os, json, base64, glob
src,out=sys.argv[1],sys.argv[2]; d=sys.argv[3] if len(sys.argv)>3 else 'assets'
s=open(src,encoding='utf-8').read()
uri=lambda p:'data:image/webp;base64,'+base64.b64encode(open(p,'rb').read()).decode()
tags=sorted(set(re.findall(r'/\*__([A-Z0-9]+)_START__\*/',s)))
extra=json.load(open(f'{d}/extra.json')) if os.path.exists(f'{d}/extra.json') else {}
report=[]
for tag in tags:
    if tag=='EMBED':
        obj={}
        for j in sorted(glob.glob(f'{d}/*.json')):
            k=os.path.basename(j)[:-5]
            if not os.path.exists(f'{d}/{k}.webp'): continue
            m=json.load(open(j)); m.update(extra.get(k,{})); m['src']=uri(f'{d}/{k}.webp'); obj[k]=m
    elif tag=='TUNE':
        obj=json.load(open(f'{d}/tune.json')) if os.path.exists(f'{d}/tune.json') else {}
    else:
        pre=tag.lower().rstrip('s')+'_'
        obj={os.path.basename(p)[len(pre):-5]:uri(p) for p in sorted(glob.glob(f'{d}/{pre}*.webp'))}
    pat=re.compile(r'/\*__%s_START__\*/.*?/\*__%s_END__\*/'%(tag,tag),re.S)
    s=pat.sub(lambda _:'/*__%s_START__*/%s/*__%s_END__*/'%(tag,json.dumps(obj,separators=(',',':'),ensure_ascii=False),tag),s,1)
    report.append(f'{tag}:{len(obj)}')
open(out,'w',encoding='utf-8').write(s)
print('built',out,round(len(s.encode())/1024),'KB |',' '.join(report))

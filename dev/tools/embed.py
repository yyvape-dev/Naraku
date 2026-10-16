"""軽量ソースHTML + 素材フォルダ → 画像入りの配布用HTML（ワンファイル）を作る。
   使い方: python3 embed.py <ソース.html> <出力.html> [素材フォルダ=assets] [--link <公開時の素材の場所>]
   --link（リンク方式。2026-10-16〜公開の既定）：画像を埋め込まず「場所?v=中身のハッシュ」を書く。例：--link dev/assets/
     （リポジトリ直下の index.html から dev/assets の画像を読む。中身が変わると ?v が変わるので、古い画像が残らない）
     リンク方式の出力は file:// では canvas の getImageData が使えないので、確認は http で開く（リポジトリ直下で python3 -m http.server 8765 → smoke.py／boot.py に http://127.0.0.1:8765/<出力> を渡す）。
   ソース側に置く目印（中身はビルドのたびに差し替わる。目印が無いものは無視される）:
     const EMBED=/*__EMBED_START__*/{}/*__EMBED_END__*/;   ← <名前>.webp と <名前>.json の組すべて（アトラス）
     const TUNE =/*__TUNE_START__*/{}/*__TUNE_END__*/;     ← tune.json（表示の微調整値）
     const FACES=/*__FACES_START__*/{}/*__FACES_END__*/;   ← face_<名前>.webp（目印名を小文字にして末尾のsを取ったものが接頭辞）
   extra.json があれば、{"名前":{…}} をアトラスのメタ情報に合成する（例: {"fox":{"target":"ally"}}）。"""
import sys, re, os, json, base64, glob, hashlib
args=sys.argv[1:]; link=None
if '--link' in args: i=args.index('--link'); link=args[i+1]; del args[i:i+2]
src,out=args[0],args[1]; d=args[2] if len(args)>2 else 'assets'
s=open(src,encoding='utf-8').read()
def uri(p):
    b=open(p,'rb').read()
    if link is not None: return link+os.path.basename(p)+'?v='+hashlib.md5(b).hexdigest()[:8]
    return 'data:image/webp;base64,'+base64.b64encode(b).decode()
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
print('built'+(' (link '+link+')' if link is not None else ''),out,round(len(s.encode())/1024),'KB |',' '.join(report))

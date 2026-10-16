"""Build a comparison-only player with external, selected assets. Never alters index.html."""
from pathlib import Path
import json,re,hashlib
root=Path(__file__).resolve().parents[3]
assets=root/'dev/assets';source=(root/'dev/naraku_src.html').read_text()
url=lambda name:'../assets/'+name+'?v='+hashlib.sha256((assets/name).read_bytes()).hexdigest()[:12]
extra=json.loads((assets/'extra.json').read_text())
embed={}
for name in ['fox','sword','mage','skel','knight']:
 meta=json.loads((assets/f'{name}.json').read_text());meta.update(extra[name]);meta['src']=url(name+'.webp');embed[name]=meta
keys=['battle_back_skill','battle_back_strategy','battle_extracted_base','battle_extracted_card_frame','battle_button_frame','battle_status_frame','battle_face_fox','battle_face_sword','battle_face_mage','card_fox','card_sword','card_mage']+['battle_strategy_'+n for n in ['heal','redraw','reset','chase','revive','ult']]
ui={k:url('ui_'+k+'.webp') for k in keys}
# This presence flag enables the current UI; the actual extracted tray is shared.
ui['battle_tray_full']=ui['battle_extracted_base']
data={'EMBED':embed,'TUNE':json.loads((assets/'tune.json').read_text()),'UI':ui,'BGS':{'camp':url('bg_camp.webp')},'FACES':{k:url('face_'+k+'.webp') for k in ['fox','sword','mage']},'VFX':{k:url('vfx_'+k+'.webp') for k in ['circle','shadow_floor','shadow_air']}}
for tag in set(re.findall(r'/\*__([A-Z0-9]+)_START__\*/',source)):
 source=re.sub(r'/\*__'+tag+r'_START__\*/.*?/\*__'+tag+r'_END__\*/','/*__'+tag+'_START__*/'+json.dumps(data.get(tag,{}),ensure_ascii=False,separators=(',',':'))+'/*__'+tag+'_END__*/',source,count=1,flags=re.S)
start=source.index('loadEmbedded().then(()=>{',source.index('buildPlaceholders();'))
end=source.index('\n</script>',start)
source=source[:start]+'''// Preview assets are shared HTTP resources; one player, no save load/write.
window.PREVIEW_LOAD={done:0,total:0,error:null};
const previewSources=[...new Set([...Object.values(UI),...Object.values(BGS),...Object.values(FACES),...Object.values(VFX),...Object.values(EMBED).map(e=>e.src)])];
PREVIEW_LOAD.total=previewSources.length;
const previewImages=previewSources.map(src=>new Promise((resolve,reject)=>{
 const im=new Image();im.onload=()=>{PREVIEW_LOAD.done++;resolve()};im.onerror=()=>reject(Error('素材を読み込めません: '+src));im.src=src;
}));
Promise.all([loadEmbedded(),...previewImages]).then(async()=>{
 await Promise.all(Object.values(VT).map(im=>im.decode?im.decode():Promise.resolve()));
 S=newSave();SAVE_ON=false;
 window.NARAKU_READY=true;requestAnimationFrame(frame);
}).catch(error=>{PREVIEW_LOAD.error=error.message;console.error(error)});
'''+source[end:]
source='\n'.join(line for line in source.split('\n') if "window.addEventListener('load',function(){setTimeout" not in line)
source=source.replace('<title>奈落の防衛前線</title>','<title>影縫い・軽量比較プレイヤー</title>')
output=root/'dev/mock/shadow_bind_player.html';output.write_text(source)
demo=root/'dev/mock/shadow_bind_demo.html'
version=hashlib.sha256(output.read_bytes()).hexdigest()[:12]
demo.write_text(re.sub(r'shadow_bind_player\.html\?shadowfx=godot&v=[^\"]+', 'shadow_bind_player.html?shadowfx=godot&v='+version,demo.read_text()))
print('player HTML bytes',output.stat().st_size,'shared assets',len(set([*ui.values(),*data['BGS'].values(),*data['FACES'].values(),*data['VFX'].values(),*(m['src'] for m in embed.values())])))

"""Bake image_gen transparency-cleaned PNGs into distributable UI WebP assets.
Usage: python3 dev/tools/dev/battle_materials.py [repository root]
Original supplied JPEGs and transparency-cleaned PNGs remain in cardart.
"""
from pathlib import Path
from PIL import Image
import sys
root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[3]
for name,width in [('tray_full',1280),('card_frame',720),('button_frame',320),('status_frame',768)]:
    src=root/'dev/cardart/battle_ui_materials'/f'transparent_{name}.png'
    im=Image.open(src).convert('RGBA')
    assert im.getchannel('A').getextrema()[0]==0, f'{src}: transparency missing'
    height=round(im.height*width/im.width)
    out=root/'dev/assets'/f'ui_battle_{name}.webp'
    im.resize((width,height),Image.Resampling.LANCZOS).save(out,quality=94,method=4)
    print(name,f'{width}x{height}',out.stat().st_size,'bytes')

# Optional UI layers extracted from the supplied mock.
for name,width in [('base',1280),('card_frame',720)]:
    src=root/'dev/cardart/battle_ui_extracted'/f'transparent_{name}.png'
    if not src.exists():continue
    im=Image.open(src).convert('RGBA');height=round(im.height*width/im.width)
    out=root/'dev/assets'/f'ui_battle_extracted_{name}.webp'
    im.resize((width,height),Image.Resampling.LANCZOS).save(out,quality=94,method=4)
    print('extracted_'+name,f'{width}x{height}',out.stat().st_size,'bytes')

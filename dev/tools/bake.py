"""スプライトシート(単色背景) → 透過・人物ごとに分離・足元そろえ済みの等間隔アトラスへ焼き直す。
   使い方: python3 bake.py <入力画像> <名前[,2段目,3段目…]> [オプション…]
   オプション: n=6            1段あたりのコマ数
               seq=2          段をつなげて1つの動きにする（例：横6コマ×2段＝12コマの攻撃）。名前は1つだけ渡す
               out=assets     出力フォルダ（<名前>.webp / .png / .json を書き出す）
               anchor=feet    左右の基準。feet=足まわり（人型の味方向け）/ core=胴体の中心（敵・武器が地面に付く絵）/
                              corexy=上下も胴体基準（多脚など足先が上下する絵）
               glow=all|N     光エフェクトに混ざった背景色を分離。all=全体 / N=輪郭からNpx以内だけ（体内にピンク・紫がある絵）
               refh=px        身長の基準（元画像px）。1コマ目で武器を掲げている絵は頭頂〜足元を手動指定
               th=260         アトラス上の身長px（これより大きい絵は縮小）
               key=70         背景とみなす色距離。体の色が背景に近くて欠けるなら下げる
               q=90           WebP品質"""
import sys, os, json, numpy as np
from PIL import Image
from scipy import ndimage as ndi
S8=np.ones((3,3))

def unmix(a,glow=False,key=70):
    rgb=a[...,:3].astype(np.float32)
    border=np.concatenate([rgb[:4].reshape(-1,3),rgb[-4:].reshape(-1,3),rgb[:,:4].reshape(-1,3),rgb[:,-4:].reshape(-1,3)])
    bg=np.median(border,axis=0)
    d=np.sqrt(((rgb-bg)**2).sum(-1))
    sure_bg=d<key
    near=ndi.binary_dilation(sure_bg,iterations=2)&~sure_bg          # 輪郭の2pxだけを半透明候補にする
    alpha=np.ones(d.shape,np.float32); alpha[sure_bg]=0
    alpha[near]=np.clip((d[near]-key)/(170-key),0,1)
    out=rgb.copy(); m=near&(alpha>0.02)                               # 背景色の混ざりを取り除く
    al=alpha[m][:,None]; out[m]=np.clip((rgb[m]-bg*(1-al))/al,0,255)
    if glow:
        # 光エフェクト用：マゼンタ寄りの画素を「光＋背景」の混色とみなして分離する
        r,g,b=out[...,0],out[...,1],out[...,2]
        m2=(alpha>0)&(r>g+12)&(b>g+12)
        if glow is not True: m2&=ndi.distance_transform_edt(~sure_bg)<=glow   # 体の内側のピンク等は守る
        t=np.clip((r[m2]-g[m2])/(bg[0]-bg[1]),0,0.97); a2=1-t
        for c in range(3): out[...,c][m2]=np.clip((out[...,c][m2]-bg[c]*t)/a2,0,255)
        alpha[m2]=alpha[m2]*a2
    return out,alpha

def segment(alpha,total,per_row):
    H,W=alpha.shape
    solid=alpha>0.35
    lab,cnt=ndi.label(ndi.binary_dilation(solid,iterations=2),structure=S8)
    idx=np.arange(1,cnt+1); area=ndi.sum(solid,lab,idx); sl=ndi.find_objects(lab)
    dropped=0
    for L in idx:                                                     # 画像の上下端に張り付いた小さなゴミは捨てる
        ys,xs=sl[L-1]
        if area[L-1]<area.max()*0.03 and (ys.start<=1 or ys.stop>=H-1): solid[lab==L]=False; dropped+=1
    big=[L for L in idx if area[L-1]>=area.max()*0.15]
    if len(big)>total: raise SystemExit(f'{len(big)}体を検出しましたが、指定は{total}体です。名前の数（段数）と n=（1段のコマ数）を確認してください')
    split=len(big)!=total
    own=np.zeros((H,W),np.int32)
    if not split:
        for i,L in enumerate(big): own[(lab==L)&solid]=i+1
    else:
        # 隣と接触している場合：芯だけ残るまで削って種を作り、人物の内側を伝って塗り広げる
        seeds=None
        for it in range(1,30):
            e=ndi.binary_erosion(solid,iterations=it); l2,c2=ndi.label(e,structure=S8)
            if c2<total: continue
            ar=ndi.sum(e,l2,np.arange(1,c2+1)); top=np.argsort(-ar)[:total]
            if ar[top[-1]]>=ar[top[0]]*0.12: seeds=[l2==(t+1) for t in top]; break
        if seeds is None: raise SystemExit(f'{total}体に分離できません。n= と段数（名前の数）が合っているか確認し、合っていればキャラの間隔を広げた版が必要です')
        for i,m in enumerate(seeds): own[m]=i+1
        for _ in range(3000):
            grow=ndi.maximum_filter(own,size=3); todo=solid&(own==0)&(grow>0)
            if not todo.any(): break
            own[todo]=grow[todo]
    bodies=[own==i+1 for i in range(total)]
    nr=ndi.distance_transform_edt(own==0,return_indices=True)[1]       # 離れた光や火の粉は最寄りの本体へ
    rest=solid&(own==0); own[rest]=own[nr[0][rest],nr[1][rest]]
    edge=ndi.binary_dilation(solid,iterations=3)&~solid                # 輪郭の半透明画素も同じ持ち主に
    nr=ndi.distance_transform_edt(own==0,return_indices=True)[1]
    soft=own.copy(); soft[edge]=own[nr[0][edge],nr[1][edge]]
    # 段→左から右の順に並べ替える
    cen=[(np.where(b)[0].mean(),np.where(b)[1].mean()) for b in bodies]
    order=sorted(range(total),key=lambda i:cen[i][0])
    rows=[sorted(order[r:r+per_row],key=lambda i:cen[i][1]) for r in range(0,total,per_row)]
    return soft,bodies,rows,dropped,split

def pack(name,rgb,alpha,soft,bodies,ids,W,target_h,refh,anchor,q,out):
    frames=[]
    for i in ids:
        mask=soft==i+1; body=bodies[i]
        rc=body.sum(1); ok=np.where(rc>=3)[0]; top,bottom=ok.min(),ok.max()
        if anchor.startswith('core'):                                  # 敵向け：胴体の一番太い所の中心を左右の基準にする
            dt=ndi.distance_transform_edt(body); cy_,cx_=np.where(dt>=dt.max()*0.75); fx=cx_.mean()
            if anchor=='corexy':                                       # 多脚など足先が上下する絵：上下も胴体基準でそろえる
                if not frames: base=bottom-cy_.mean()
                bottom=int(round(cy_.mean()+base))
        else:                                                          # 味方向け：足まわりの重心
            band=max(3,int((bottom-top)*0.14)); fx=np.where(body[bottom-band:bottom+1])[1].mean()
        ya,xa=np.where(mask&(alpha>0.02))
        frames.append(dict(mask=mask,top=top,bottom=bottom,fx=fx,x0=xa.min(),x1=xa.max(),y0=ya.min(),y1=ya.max()))
    n=len(frames)
    ref_h=refh or (frames[0]['bottom']-frames[0]['top']+1)             # 武器を掲げた絵は頭頂〜足元を手動指定
    k=min(1.0,target_h/ref_h)
    half=max(max(f['fx']-f['x0'],f['x1']-f['fx']) for f in frames)
    up=max(f['bottom']-f['y0'] for f in frames); down=max(f['y1']-f['bottom'] for f in frames)
    pad=4
    cw=int(np.ceil(half*2*k))+pad*2; ch=int(np.ceil((up+down+1)*k))+pad*2
    ax=cw/2; ay=ch-pad-int(np.ceil(down*k))
    atlas=Image.new('RGBA',(cw*n,ch),(0,0,0,0))
    rgba=np.dstack([rgb,alpha*255]).astype(np.uint8)
    for i,f in enumerate(frames):
        x0,x1,y0,y1=f['x0'],f['x1']+1,f['y0'],f['y1']+1
        cut=rgba[y0:y1,x0:x1].copy(); cut[...,3]=np.where(f['mask'][y0:y1,x0:x1],cut[...,3],0)
        im=Image.fromarray(cut,'RGBA')
        if k<1: im=im.resize((max(1,round(im.width*k)),max(1,round(im.height*k))),Image.LANCZOS)
        atlas.alpha_composite(im,(round(i*cw+ax-(f['fx']-x0+0.5)*k),round(ay-(f['bottom']+1-y0)*k)))
    os.makedirs(out,exist_ok=True)
    atlas.save(f'{out}/{name}.webp',quality=q,method=6)
    atlas.save(f'{out}/{name}.png')
    json.dump(dict(cols=n,cw=cw,ch=ch,ax=ax,ay=ay,refH=round(ref_h*k,1)),open(f'{out}/{name}.json','w'))
    jit=[(round(float(f['fx']-(W/n*(i+0.5))),1),int(f['bottom']-frames[0]['bottom'])) for i,f in enumerate(frames)]
    print(f'  {name}: 身長{int(ref_h)}px 縮尺{k:.2f} アトラス{atlas.size} / 元のズレ(左右,上下) {jit}')

def bake(path,names,n=6,glow=False,refh=None,th=260,anchor='feet',key=70,q=90,out='assets',seq=1):
    a=np.array(Image.open(path).convert('RGB')); H,W=a.shape[:2]
    rgb,alpha=unmix(a,glow,key)
    if seq>1 and len(names)!=1: raise SystemExit('seq= を使うときは、名前を1つだけ渡してください')
    soft,bodies,rows,dropped,split=segment(alpha,n*len(names)*seq,n)
    if seq>1: rows=[sum(rows,[])]   # 上の段→下の段の順につなげて、1本のアトラスにする
    print(path.split('/')[-1][:12],(W,H),'ゴミ除去',dropped,'接触を切り分け' if split else '分離OK')
    for name,ids in zip(names,rows): pack(name,rgb,alpha,soft,bodies,ids,W,th,refh,anchor,q,out)

if __name__=='__main__':
    opt=dict(x.split('=') for x in sys.argv[3:] if '=' in x)
    g=opt.get('glow'); g=True if g=='all' else (int(g) if g else False)
    bake(sys.argv[1],sys.argv[2].split(','),int(opt.get('n',6)),glow=g,refh=int(opt['refh']) if 'refh' in opt else None,th=int(opt.get('th',260)),anchor=opt.get('anchor','feet'),key=int(opt.get('key',70)),q=int(opt.get('q',90)),out=opt.get('out','assets'),seq=int(opt.get('seq',1)))

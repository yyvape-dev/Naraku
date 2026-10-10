"""動画AIのコマ一覧（単色背景・不揃いな並び）→ bake.py に渡せる「横6×2段・隙間50px」のシートを作る。
   使い方: python3 tools/vsheet.py <コマ一覧の画像> <出力.png> grid=4x3 [stand=<立ち絵.png>] [at=1,12] [tone=stand|video]
     grid=列x段      元画像のコマの並び（左上→右下が再生順。合計12コマ）
     stand=画像      立ち絵（単色背景）。at= のコマをこの絵に差し替える（既定 1,12）
     tone=stand      色の基準を立ち絵にする（既定。待機で一番長く映るのは1コマ目なので）。動画のコマ全部に同じ対応表を当てる
     tone=video      立ち絵のほうを動画のコマに合わせる
   立ち絵の大きさは、差し替える最後のコマ（既定12）の元の身長に合わせる。色は彩度と明るさを分布ごと合わせ、色相は変えない。
   このあと: python3 tools/look.py add <キャラ> <出力.png> seq=2 glow=3"""
import sys, numpy as np
from PIL import Image
from scipy import ndimage as ndi

def bgcolor(a):
    b=np.concatenate([a[:4].reshape(-1,3),a[-4:].reshape(-1,3),a[:,:4].reshape(-1,3),a[:,-4:].reshape(-1,3)]);return np.median(b,0)
def mask_of(a,bg,key=70):
    d=np.sqrt(((a.astype(np.float32)-bg)**2).sum(-1));return ndi.binary_opening(d>key,iterations=1)
def crop_fig(a,m):
    lab,n=ndi.label(m);s=ndi.sum(m,lab,range(1,n+1));keep=np.isin(lab,[i+1 for i in range(n) if s[i]>=40])
    keep=ndi.binary_dilation(keep,iterations=3)
    yy,xx=np.where(keep);y0,y1,x0,x1=yy.min(),yy.max()+1,xx.min(),xx.max()+1
    return a[y0:y1,x0:x1],keep[y0:y1,x0:x1]
def cut(proj,n):
    """投影（列ごと/段ごとの前景の量）から、等分の境目の近くで一番空いている位置を n-1 個選ぶ"""
    L=len(proj);out=[0]
    for i in range(1,n):
        c=L*i//n;w=L//n//4;seg=proj[c-w:c+w];out.append(c-w+int(np.argmin(seg)))
    return out+[L]
def hsv(a):return np.array(Image.fromarray(a).convert('HSV')).astype(float)

def main():
    if len(sys.argv)<3: raise SystemExit(__doc__)
    opt=dict(x.split('=',1) for x in sys.argv[3:] if '=' in x)
    gc,gr=map(int,opt.get('grid','4x3').split('x'))
    src=np.array(Image.open(sys.argv[1]).convert('RGB'));bg=bgcolor(src);fg=mask_of(src,bg)
    ys=cut(fg.sum(1),gr);crops=[]
    for r in range(gr):
        band=fg[ys[r]:ys[r+1]];xs=cut(band.sum(0),gc)
        for c in range(gc):
            m=np.zeros_like(fg);m[ys[r]:ys[r+1],xs[c]:xs[c+1]]=band[:,xs[c]:xs[c+1]]
            crops.append(crop_fig(src,m))
    print('コマ',len(crops),'段の境',ys)
    if len(crops)!=12: print('注意: 12コマではありません（',len(crops),'）')
    if 'stand' in opt:
        at=[int(x)-1 for x in opt.get('at','1,12').split(',')]
        st=np.array(Image.open(opt['stand']).convert('RGB'));sbg=bgcolor(st);p,_=crop_fig(st,mask_of(st,sbg))
        ref=crops[at[-1]][0];H=ref.shape[0];w=round(p.shape[1]*H/p.shape[0])
        big=p.copy();big[~mask_of(p,sbg)]=bg.astype(np.uint8)
        small=np.array(Image.fromarray(big).resize((w,H),Image.LANCZOS));fm=mask_of(small,bg)
        qs=np.linspace(0,100,101);rm=ndi.binary_erosion(mask_of(ref,bg),iterations=2)
        R=hsv(ref)[rm];T=hsv(small)[ndi.binary_erosion(fm,iterations=2)]
        def tone(a,m,src_,dst_):
            Hh=hsv(a)
            for ch in (1,2): Hh[...,ch][m]=np.interp(Hh[...,ch][m],np.percentile(src_[:,ch],qs),np.percentile(dst_[:,ch],qs))
            o=a.copy();o[m]=np.array(Image.fromarray(Hh.clip(0,255).astype(np.uint8),'HSV').convert('RGB'))[m];return o
        if opt.get('tone','stand')=='stand':
            for k in range(len(crops)):
                if k in at: continue
                p0,m0=crops[k];crops[k]=(tone(p0,mask_of(p0,bg),R,T),m0)
        else:
            small=tone(small,fm,T,R)
        sm=ndi.binary_dilation(fm,iterations=2)
        for k in at: crops[k]=(small,sm)
        print('立ち絵 縮尺',round(H/p.shape[0],3),'彩度 動画',R[:,1].mean().round(1),'立ち絵',T[:,1].mean().round(1),' 明るさ 動画',R[:,2].mean().round(1),'立ち絵',T[:,2].mean().round(1),' 基準=',opt.get('tone','stand'))
    CW=max(p.shape[1] for p,_ in crops)+20;CH=max(p.shape[0] for p,_ in crops)+20;G=50
    sheet=np.zeros((2*CH+3*G,6*CW+7*G,3),np.uint8);sheet[:]=bg.astype(np.uint8)
    for k,(p,mk) in enumerate(crops[:12]):
        r,c=divmod(k,6);ox=G+c*(CW+G)+(CW-p.shape[1])//2;oy=G+r*(CH+G)+CH-10-p.shape[0]
        reg=sheet[oy:oy+p.shape[0],ox:ox+p.shape[1]];reg[mk]=p[mk]
    Image.fromarray(sheet).save(sys.argv[2]);print('出力',sys.argv[2],sheet.shape[1],'x',sheet.shape[0])
main()

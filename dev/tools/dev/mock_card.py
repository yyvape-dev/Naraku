import sys,os,base64,json
from playwright.sync_api import sync_playwright
H=os.path.abspath(sys.argv[1]);A=sys.argv[2];out=sys.argv[3]
def du(n): return 'data:image/webp;base64,'+base64.b64encode(open(f'{A}/cut_{n}.webp','rb').read()).decode()
art={k:du(k) for k in ['fox','sword','sister','mage','blue']}
art['mg_void']='data:image/webp;base64,'+base64.b64encode(open('cardart/mg_void.webp','rb').read()).decode()
CSS='''
.lx.fa .ar{bottom:3px;border-radius:3px}
.lx.fa .ar::after{background:linear-gradient(transparent 52%,rgba(6,4,3,.6) 70%,rgba(6,4,3,.95) 90%),radial-gradient(ellipse at 50% 35%,transparent 55%,rgba(0,0,0,.4))}
.lx.fa .pl{background:none;border-top:0;height:34px;bottom:2px;justify-content:flex-end;padding-bottom:3px}
.lx.fa .pl::before{top:auto;bottom:30px;width:30px;height:1px;transform:translateX(-50%);background:linear-gradient(90deg,transparent,#f1d892,transparent);box-shadow:none}
.lx.fa .nm{font-size:12.5px;font-weight:600;color:#ffeab4;letter-spacing:.04em;
  text-shadow:0 0 1px #000,0 1px 1px #000,0 0 4px rgba(0,0,0,.95),0 0 8px rgba(0,0,0,.8)}
.lx.fa .kd2{color:#e6d3a3;text-shadow:0 1px 2px #000,0 0 4px #000}

#hand.lx{gap:7px;min-height:var(--ch)}
.lx .card{height:var(--ch);padding:0;border:0;border-radius:7px;background:none;overflow:visible;box-shadow:0 6px 12px -4px #000}
.lx .card::after{display:none}
.lx .cf{position:absolute;inset:0;border-radius:7px;padding:3px;
  background:linear-gradient(145deg,#fff1c0 0%,#d9b260 18%,#7a5520 42%,#e9cd84 60%,#8a6326 80%,#f6dea0 100%)}
.lx .ci{position:absolute;inset:3px;border-radius:5px;overflow:hidden;background:#0b0907;box-shadow:inset 0 0 0 1px #2a1c0c}
.lx .ar{position:absolute;left:3px;right:3px;top:3px;bottom:var(--pl);border-radius:3px 3px 0 0;overflow:hidden;box-shadow:inset 0 0 0 1px rgba(255,230,168,.5)}
.lx .ar img{width:100%;height:100%;object-fit:cover;object-position:var(--op,50% 30%);filter:saturate(1.08) contrast(1.05)}
.lx .ar::after{content:"";position:absolute;inset:0;background:linear-gradient(transparent 55%,rgba(8,6,4,.85)),radial-gradient(ellipse at 50% 40%,transparent 50%,rgba(0,0,0,.45))}
.lx .sh{position:absolute;inset:0;background:linear-gradient(115deg,transparent 35%,rgba(255,240,200,.28) 47%,transparent 58%);mix-blend-mode:screen;animation:sh 4.5s ease-in-out infinite}
@keyframes sh{0%,60%{transform:translateX(-120%)}100%{transform:translateX(120%)}}
.lx .pl{position:absolute;left:0;right:0;bottom:0;height:var(--pl);display:flex;flex-direction:column;align-items:center;justify-content:center;
  background:linear-gradient(#1c140c,#0b0806);border-top:1px solid #c9a85a}
.lx .pl::before{content:"";position:absolute;left:50%;top:-5px;width:8px;height:8px;transform:translateX(-50%) rotate(45deg);background:var(--oc);box-shadow:0 0 0 1px #f1d892,0 0 8px var(--oc)}
.lx .nm{font-size:12px;letter-spacing:.06em;color:#ffe9b0;margin:2px 0 0;text-shadow:0 1px 0 #000;white-space:nowrap}
.lx .kd2{font-size:8.5px;letter-spacing:.2em;color:#b8a070}
.lx .gm{position:absolute;left:-3px;top:-3px;width:20px;height:20px;border-radius:50%;z-index:2;font-style:normal;font-size:10px;font-weight:700;display:flex;align-items:center;justify-content:center;color:#fff8e0;
  background:radial-gradient(circle at 35% 30%,#fff 0,var(--oc) 35%,#1a0f05 100%);box-shadow:0 0 0 1.5px #f1d892,0 0 0 3px #4a3410,0 2px 4px #000}
.lx .cn{position:absolute;width:9px;height:9px;border:1.5px solid #f1d892;transform:rotate(45deg);background:#2a1c0c;z-index:2}
.lx .cn.a{right:-3px;top:-3px}.lx .cn.b{right:-3px;bottom:-3px}.lx .cn.c{left:-3px;bottom:-3px}
.lx .card.sel{transform:translateY(-12px)}
.lx .card.sel .cf{box-shadow:0 0 0 1px #fff3c8,0 0 18px 4px rgba(255,200,110,.7)}
.lx .back .ci{background:repeating-linear-gradient(45deg,#1a120a 0 6px,#140e08 6px 12px)}
.lx .back .em2{position:absolute;left:50%;top:44%;width:44%;aspect-ratio:1;transform:translate(-50%,-50%) rotate(45deg);border:1.5px solid #c9a85a;box-shadow:inset 0 0 0 4px #140e08,inset 0 0 0 5px #8a6a2e}
.lx .back .fl{position:absolute;left:0;right:0;bottom:0;height:42%;background:linear-gradient(rgba(241,216,146,.05),rgba(241,216,146,.32));border-top:1px solid #f1d892}
.lx .back .ld{position:absolute;left:0;right:0;bottom:8px;text-align:center;font-size:9px;letter-spacing:.3em;color:#d8c08a}
'''
cards=[('mg_void','凍てつく虚無','範囲','#a57be0','シ','48% 30%',True),('sword','大地割り','範囲','#b9c2cc','ラ','50% 20%',False),('fox','狐火乱舞','範囲','#e0913a','ユ','50% 25%',False),None]
def html():
  s=''
  for c in cards:
    if c is None:
      s+='<div class="card back"><span class="cf"></span><span class="ci"><span class="em2"></span><span class="fl"></span><span class="ld">装填中</span></span></div>';continue
    k,n,kd,col,g,op,sel=c
    s+=f'<button class="card{" sel" if sel else ""}" style="--oc:{col};--op:{op}"><span class="cf"></span><span class="ci"><span class="ar"><img src="{art[k]}"><span class="sh"></span></span><span class="pl"><span class="nm">{n}</span><span class="kd2">― {kd} ―</span></span></span><i class="gm">{g}</i><i class="cn a"></i><i class="cn b"></i><i class="cn c"></i></button>'
  return s
with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page(viewport={'width':390,'height':844},device_scale_factor=2)
  pg.goto('file://'+H);pg.wait_for_timeout(1500)
  pg.evaluate("()=>{NARAKU.start(['fox','sword','mage'],7);NARAKU.sim&&0}")
  pg.wait_for_timeout(9000)
  pg.click('#btnPause');pg.wait_for_timeout(300)
  pg.screenshot(path=f'{out}/c0.png')
  pg.add_style_tag(content=CSS)
  for name,ch,pl,fa in [('c4',132,32,False),('c5',132,32,True)]:
    pg.evaluate('f=>window.__fa=f',fa)
    pg.evaluate("([h,ch,pl])=>{const e=document.querySelector('#hand');e.className='lx'+(window.__fa?' fa':'');e.style.setProperty('--ch',ch+'px');e.style.setProperty('--pl',pl+'px');e.innerHTML=h;window.dispatchEvent(new Event('resize'))}",[html(),ch,pl])
    pg.evaluate("()=>{const h=document.querySelector('#hint');h.textContent='範囲の敵を凍結させる　―　戦場をタップして放つ';h.classList.add('on')}");pg.wait_for_timeout(500);pg.screenshot(path=f'{out}/{name}.png')
  b.close()

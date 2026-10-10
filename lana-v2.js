/* Lana V2 prototype. Visual-only replacement, no damage or battle logic changes. */
(function(){
const frame=document.getElementById('game'),err=document.getElementById('err');
function install(){try{
const w=frame.contentWindow;
if(!w||!w.document.getElementById('app'))return;
err.style.display='none';err.textContent='';
const replacement=function drawLanaUlt(g,layer){
 const U=FX.lanaU;if(!U||!B)return;const t=U.t,y=B.lineY*.50;
 const smooth=u=>{u=Math.max(0,Math.min(1,u));return u*u*(3-2*u)};
 const rnd=n=>{const a=Math.sin(n*127.1+32.31)*43758.5453;return a-Math.floor(a)};
 g.save();
 if(layer==='floor'){
  for(let i=0;i<6;i++){
   const onset=.04+i*.06,dt=t-onset;if(dt<0||dt>4.25)continue;
   const x=30+i*60,grow=smooth(dt/.25),fade=Math.min(1,(4.25-dt)/.95),span=15+21*grow,fy=6+12*grow;
   g.save();g.translate(x,y);g.globalAlpha=fade;
   g.fillStyle='rgba(14,3,4,.53)';g.beginPath();g.ellipse(0,0,span*1.38,fy*1.55,0,0,Math.PI*2);g.fill();
   for(let k=0;k<7;k++){
    const seed=i*31+k*17,off=(rnd(seed)-.5)*span*.95,side=k%2?1:-1,sx=off,sy=(rnd(seed+4)-.5)*fy*.9,len=(7+rnd(seed+3)*21)*grow;
    g.lineCap='round';g.lineJoin='bevel';g.beginPath();g.moveTo(sx,sy);g.lineTo(sx+side*len*.43,sy+(rnd(seed+1)-.5)*9);g.lineTo(sx+side*len*.8,sy+(rnd(seed+2)-.5)*fy);g.lineTo(sx+side*len,sy+(rnd(seed+9)-.5)*fy);
    g.strokeStyle='#110508';g.lineWidth=1.8+1.3*rnd(seed+10);g.stroke();
    g.globalCompositeOperation='screen';g.strokeStyle='rgba(255,29,24,'+(.33+.38*Math.max(0,1-dt/1.15))+')';g.lineWidth=.65+grow*.7;g.stroke();g.globalCompositeOperation='source-over';
   }
   const floorTex=vtex('lanaU_f4');
   if(floorTex && dt>.12){
     const sw=floorTex.width/6,srcX=Math.min(floorTex.width-sw,i*sw);
     g.globalAlpha=.34*fade;g.drawImage(floorTex,srcX,0,sw,floorTex.height,-span*1.3,-fy*2.3,span*2.6,fy*4.6);g.globalAlpha=fade;
   }
   const glow=Math.max(0,1-dt/1.75)*grow;if(glow>0){const grad=g.createRadialGradient(0,0,0,0,0,span*1.5);grad.addColorStop(0,'rgba(255,36,23,'+(.28*glow)+')');grad.addColorStop(1,'rgba(70,0,0,0)');g.fillStyle=grad;g.beginPath();g.ellipse(0,0,span*1.5,fy*1.8,0,0,Math.PI*2);g.fill();}
   g.restore();
  }
 }else if(layer==='top'){
  for(let i=0;i<6;i++){
   const onset=.08+i*.06,dt=t-onset;if(dt<0||dt>1.55)continue;
   const x=30+i*60,rise=smooth(dt/.20),decay=Math.min(1,Math.max(0,(1.55-dt)/.65));
   const height=(38+112*rise)*decay,width=(5+5*rise)*decay,base=y+4;
   g.save();g.globalCompositeOperation='screen';g.globalAlpha=.68*decay;
   // Paint-textured plume: crop one-sixth of original high-quality eruption art per impact.
   const tex=vtex(dt<.48?'lanaU_t1':dt<.9?'lanaU_t3':'lanaU_t4');
   if(tex){
     g.globalCompositeOperation='source-over';g.globalAlpha=.78*decay;
     const sw=tex.width/6, sx=Math.min(tex.width-sw,i*sw);
     g.drawImage(tex,sx,0,sw,tex.height,x-25,base-height-20,50,height+36);
     g.globalCompositeOperation='screen';g.globalAlpha=.26*decay;
     g.drawImage(tex,sx,0,sw,tex.height,x-25,base-height-20,50,height+36);
   }
   // Irregular wisps break the silhouette, never use a triangle/polygon cone.
   g.globalCompositeOperation='screen';
   for(let j=0;j<5;j++){
     const seed=i*53+j*19,dx=(rnd(seed)-.5)*11,wiggle=(rnd(seed+4)-.5)*19;
     g.globalAlpha=(.13+.13*rnd(seed+9))*decay;
     const plume=g.createLinearGradient(x+dx,base,x+dx+wiggle,base-height);
     plume.addColorStop(0,'rgba(255,66,41,.85)');plume.addColorStop(.6,'rgba(179,17,24,.48)');plume.addColorStop(1,'rgba(51,0,0,0)');
     g.strokeStyle=plume;g.lineWidth=2+5*rnd(seed+17);
     g.beginPath();g.moveTo(x+dx,base);g.bezierCurveTo(x+dx+wiggle*.5,base-height*.29,x+dx-wiggle,base-height*.67,x+dx+wiggle,base-height);g.stroke();
   }
   if(dt<.63){g.globalAlpha=.5*decay;g.strokeStyle='#ffb9a4';g.lineWidth=1.2;g.beginPath();g.moveTo(x,base);g.lineTo(x+Math.sin(i*7+dt*13)*3,base-height*.78);g.stroke();}
   g.restore();
   for(let j=0;j<8;j++){const seed=i*97+j*13,delay=rnd(seed)*.27,d=dt-delay;if(d<0||d>1.1)continue;const angle=-Math.PI*.85+rnd(seed+3)*Math.PI*.7,vel=55+85*rnd(seed+7),px=x+Math.cos(angle)*vel*d,py=base+Math.sin(angle)*vel*d+125*d*d,size=(1.6+2.9*rnd(seed+11))*(1-d/1.1);g.save();g.translate(px,py);g.rotate(d*9*(rnd(seed+19)-.5));g.globalAlpha=Math.max(0,1-d/1.1)*.88;g.fillStyle=j%3===0?'#9c291b':'#240b0b';g.fillRect(-size,-size,size*2,size*1.5);g.restore();}
  }
  const peak=Math.max(0,1-Math.abs(t-.56)/.11);if(peak){g.save();g.globalCompositeOperation='screen';g.globalAlpha=.20*peak;g.fillStyle='#fa4833';g.fillRect(0,y-60,W,95);g.restore();}
  if(t<2.4)for(let j=0;j<35;j++){const seed=700+j*37,u=(t*.55+rnd(seed))%1,xx=rnd(seed+4)*W,yy=y-25-rnd(seed+6)*110*u;g.globalAlpha=(1-u)*.5;g.fillStyle=j%4?'#a7241e':'#ff5943';g.fillRect(xx+Math.sin(u*7+j)*6,yy,1.2,2.6);}
 }else if(layer==='aura'){
  const o=B.allies.find(z=>z.d.id==='sword'&&z.alive),a=lanaUA(t,0,1.6,2.1);
  if(o&&a>.01){const fr=t*14,i=Math.floor(fr)%4,f=fr-Math.floor(fr),h=ALLY_H*1.75,w=h/1.5,x=o.x-w/2,yy=o.y-h*.86;for(const [j,al] of [[i,1-f],[(i+1)%4,f]]){const im=vtex('lanaU_a'+(j+1));if(!im)continue;g.globalCompositeOperation='source-over';g.globalAlpha=a*al*.78;g.drawImage(im,x,yy,w,h);}}
 }
 g.restore();
};
w.eval('drawLanaUlt = ('+replacement.toString()+')');
w.eval('ultLanaCol = ('+function ultLanaCol(x,hw,pal){const y=B.lineY*.5;dustBurst('shard',x,y,7,{ang:-Math.PI/2,spread:2.2,v0:90,v1:210,jit:hw*.7,l0:.3,l1:.35,spin:9,p:{drag:2,grav:430,w:2.2,c0:'#531413',c1:'#160708'}});FX.shake=Math.min(16,FX.shake+5);}.toString()+')');
window.LANA_V2_READY=true;err.style.display='none';err.textContent='';
}catch(e){err.style.display='block';err.textContent='改善版の適用に失敗: '+e.message;console.error(e)}}
frame.addEventListener('load',install);if(frame.contentDocument?.getElementById('app'))install();
})();

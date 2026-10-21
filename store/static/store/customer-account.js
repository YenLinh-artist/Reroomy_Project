(()=>{
const node=document.getElementById('account-products-json'),products=node?JSON.parse(node.textContent):[];
const grid=document.getElementById('favoriteGrid'),empty=document.getElementById('favoriteEmpty');
const safe=v=>String(v==null?'':v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const read=(k,d)=>{try{return JSON.parse(localStorage.getItem(k))??d}catch{return d}};
document.querySelectorAll('[data-order-demo-image]').forEach(img=>{
 const slot=img.closest('.order-image-placeholder');
 const show=()=>slot?.classList.add('has-image');
 const hide=()=>img.remove();
 if(img.complete){if(img.naturalWidth)show();else hide()}
 else{img.addEventListener('load',show,{once:true});img.addEventListener('error',hide,{once:true})}
});
function favorites(){
 if(!grid||!empty)return;
 const raw=read('reroom-demo-faves',[]),ids=Array.isArray(raw)?raw.map(String):[];
 const rows=products.filter(p=>ids.includes(String(p.id)));
 grid.innerHTML=rows.map(p=>'<article class="mini-product"><a class="mini-product-image" href="/san-pham/'+encodeURIComponent(p.detail_url)+'/">'+(p.has_photo?'<img src="'+safe(p.image_url)+'" alt="'+safe(p.name)+'">':'<img class="category-placeholder-icon" src="'+safe(p.icon_url)+'" alt=""><span>\u1ea2nh s\u1ea3n ph\u1ea9m</span>')+'</a><div><h3>'+safe(p.name)+'</h3><p>'+safe(p.price_text)+'</p><button class="secondary-link" data-unfavorite="'+safe(p.id)+'" type="button">B\u1ecf y\u00eau th\u00edch</button></div></article>').join('');
 empty.hidden=rows.length>0;
}
grid?.addEventListener('click',e=>{const b=e.target.closest('[data-unfavorite]');if(!b)return;const raw=read('reroom-demo-faves',[]);localStorage.setItem('reroom-demo-faves',JSON.stringify((Array.isArray(raw)?raw:[]).map(String).filter(x=>x!==b.dataset.unfavorite)));favorites()});
window.addEventListener('storage',favorites);favorites();

const standard={width:3,depth:4,loft:false,objects:[
 {type:'bed',label:'Gi\u01b0\u1eddng 1m4',x:.04,y:.05,w:.39,h:.3},
 {type:'desk',label:'B\u00e0n h\u1ecdc',x:.55,y:.05,w:.38,h:.2},
 {type:'wardrobe',label:'T\u1ee7 qu\u1ea7n \u00e1o',x:.57,y:.31,w:.34,h:.16},
 {type:'rug',label:'Th\u1ea3m',x:.17,y:.58,w:.52,h:.21},
 {type:'plant',label:'C\u00e2y xanh',x:.81,y:.82,w:.12,h:.12}]};
const stored=read('reroom-room-plan',standard),room=stored&&typeof stored==='object'?stored:{...standard};
room.width=Number(room.width)||3;room.depth=Number(room.depth)||4;room.loft=Boolean(room.loft);
if(!Array.isArray(room.objects)||!room.objects.length)room.objects=standard.objects.map(x=>({...x}));
room.objects=room.objects.slice(0,8).map((x,i)=>({...standard.objects[i%standard.objects.length],...x}));
const canvas=document.getElementById('roomPlan'),form=document.getElementById('roomForm'),state=document.getElementById('roomSaveState'),combo=document.getElementById('roomComboLink');
if(canvas&&form){
 const ctx=canvas.getContext('2d'),wi=form.elements.width,di=form.elements.depth,loft=form.elements.loft,preset=document.getElementById('roomPreset');
 let roomRect=null,drawn=[];
 const rounded=(x,y,w,h,r)=>{ctx.beginPath();if(ctx.roundRect)ctx.roundRect(x,y,w,h,r);else ctx.rect(x,y,w,h)};
 function draw(){
  ctx.clearRect(0,0,900,540);ctx.fillStyle='#fffaf6';ctx.fillRect(0,0,900,540);
  ctx.textAlign='left';ctx.fillStyle='#d87592';ctx.font='bold 13px Arial';ctx.fillText('G\u1ee2I \u00dd B\u1ed0 TR\u00cd PH\u00d2NG TR\u1ecc',30,32);
  ctx.fillStyle='#99847d';ctx.font='12px Arial';ctx.fillText('M\u1eb7t b\u1eb1ng 2D minh h\u1ecda \u00b7 k\u00e9o th\u1ea3 n\u1ed9i th\u1ea5t',30,52);
  ctx.fillStyle='#fff';rounded(28,78,220,400,14);ctx.fill();ctx.strokeStyle='#f0ded8';ctx.stroke();
  ctx.fillStyle='#b08c7f';ctx.font='bold 11px Arial';ctx.fillText('K\u00cdCH TH\u01af\u1edaC PH\u00d2NG',46,112);
  ctx.fillStyle='#392f2c';ctx.font='bold 26px Arial';ctx.fillText(room.width+' \u00d7 '+room.depth+' m',46,150);
  ctx.fillStyle='#df7890';ctx.font='bold 17px Arial';ctx.fillText((room.width*room.depth).toFixed(1).replace('.0','')+' m\u00b2',46,180);
  [['Gi\u01b0\u1eddng ng\u1ee7','#f0b5c3'],['G\u00f3c h\u1ecdc t\u1eadp','#d8ad82'],['T\u1ee7 qu\u1ea7n \u00e1o','#d6bd9e'],['Th\u1ea3m & c\u00e2y xanh','#96b984']].forEach((v,i)=>{ctx.fillStyle=v[1];ctx.fillRect(46,244+i*38,18,18);ctx.fillStyle='#66544e';ctx.font='11px Arial';ctx.fillText(v[0],75,258+i*38)});
  if(room.loft){ctx.fillStyle='#cf6389';ctx.fillText('C\u00f3 g\u00e1c l\u1eedng \u00b7 ti\u1ebft ki\u1ec7m di\u1ec7n t\u00edch',46,424)}
  const scale=Math.min(590/room.width,380/room.depth),rw=room.width*scale,rh=room.depth*scale,rx=288+(585-rw)/2,ry=88+(378-rh)/2;
  roomRect={x:rx,y:ry,w:rw,h:rh};drawn=[];ctx.textAlign='center';ctx.fillStyle='#95847d';ctx.font='12px Arial';ctx.fillText(room.width+' m',rx+rw/2,ry-18);
  ctx.save();ctx.translate(rx-17,ry+rh/2);ctx.rotate(-Math.PI/2);ctx.fillText(room.depth+' m',0,0);ctx.restore();
  ctx.fillStyle='#eee1d5';ctx.fillRect(rx-6,ry-6,rw+12,rh+12);ctx.fillStyle='#f5e8dc';ctx.fillRect(rx,ry,rw,rh);
  ctx.save();ctx.beginPath();ctx.rect(rx,ry,rw,rh);ctx.clip();ctx.strokeStyle='#ead9ca';for(let y=ry+16;y<ry+rh;y+=20){ctx.beginPath();ctx.moveTo(rx,y);ctx.lineTo(rx+rw,y);ctx.stroke()}ctx.restore();
  ctx.lineWidth=5;ctx.strokeStyle='#9c7667';ctx.strokeRect(rx,ry,rw,rh);ctx.fillStyle='#dff0eb';ctx.fillRect(rx+rw*.27,ry-3,rw*.35,6);
  room.objects.forEach(o=>{const x=rx+o.x*rw,y=ry+o.y*rh,w=o.w*rw,h=o.h*rh;drawn.push({o,x,y,w,h});ctx.fillStyle=({bed:'#f0b5c3',desk:'#d8ad82',wardrobe:'#d6bd9e',plant:'#96b984',rug:'#f4d8d5'})[o.type]||'#f4d8d5';ctx.strokeStyle='#aa8278';ctx.lineWidth=1.5;rounded(x,y,w,h,7);ctx.fill();ctx.stroke();ctx.fillStyle='#51423f';ctx.font='bold 11px Arial';if(w>54&&h>27)ctx.fillText(o.label,x+w/2,y+h*.58,w-8)});
  ctx.textAlign='left';ctx.fillStyle='#a18b83';ctx.font='11px Arial';ctx.fillText('S\u01a1 \u0111\u1ed3 tham kh\u1ea3o \u00b7 k\u00e9o c\u00e1c m\u00f3n \u0111\u1ed3 \u0111\u1ec3 s\u1eafp x\u1ebfp.',288,510);
 }
 const update=()=>{if(combo)combo.href='/goi-y-combo/?width='+encodeURIComponent(wi.value||'3')+'&depth='+encodeURIComponent(di.value||'4')};
 const sync=()=>{const v=Number(wi.value)+'x'+Number(di.value);preset.value=['3x4','3x5','4x5'].includes(v)?v:'custom'};
 preset?.addEventListener('change',()=>{const map={'3x4':[3,4],'3x5':[3,5],'4x5':[4,5]},v=map[preset.value];if(v){wi.value=v[0];di.value=v[1];room.width=v[0];room.depth=v[1];draw();update()}});
 wi.addEventListener('input',()=>{room.width=Math.max(1,Math.min(10,Number(wi.value)||3));sync();draw();update()});
 di.addEventListener('input',()=>{room.depth=Math.max(1,Math.min(15,Number(di.value)||4));sync();draw();update()});
 loft.addEventListener('change',()=>{room.loft=loft.checked;draw()});
 form.addEventListener('submit',e=>{e.preventDefault();room.width=Number(wi.value)||3;room.depth=Number(di.value)||4;room.loft=loft.checked;localStorage.setItem('reroom-room-plan',JSON.stringify(room));draw();update();if(state)state.textContent='\u0110\u00e3 l\u01b0u s\u01a1 \u0111\u1ed3 tr\u00ean tr\u00ecnh duy\u1ec7t n\u00e0y.'});
 canvas.addEventListener('pointerdown',e=>{const r=canvas.getBoundingClientRect(),x=(e.clientX-r.left)*900/r.width,y=(e.clientY-r.top)*540/r.height,h=drawn.slice().reverse().find(v=>x>=v.x&&x<=v.x+v.w&&y>=v.y&&y<=v.y+v.h);if(h){canvas.setPointerCapture(e.pointerId);canvas._moving=h.o;e.preventDefault()}});
 canvas.addEventListener('pointermove',e=>{if(!canvas._moving||!roomRect)return;const r=canvas.getBoundingClientRect(),x=(e.clientX-r.left)*900/r.width,y=(e.clientY-r.top)*540/r.height,o=canvas._moving;o.x=Math.max(0,Math.min(1-o.w,(x-roomRect.x)/roomRect.w-o.w/2));o.y=Math.max(0,Math.min(1-o.h,(y-roomRect.y)/roomRect.h-o.h/2));draw()});
 const stop=()=>canvas._moving=null;canvas.addEventListener('pointerup',stop);canvas.addEventListener('pointercancel',stop);
 document.getElementById('expandPlan')?.addEventListener('click',()=>canvas.requestFullscreen?.());
 document.getElementById('exportPlan')?.addEventListener('click',()=>{const a=document.createElement('a');a.download='reroom-ban-ve-phong-2d.png';a.href=canvas.toDataURL('image/png');a.click()});
 document.addEventListener('fullscreenchange',draw);wi.value=room.width;di.value=room.depth;loft.checked=room.loft;sync();draw();update();
}
document.querySelectorAll('[data-copy-voucher]').forEach(b=>b.addEventListener('click',async()=>{const code=b.dataset.copyVoucher;try{await navigator.clipboard.writeText(code);b.innerHTML=safe(code)+'<span>\u0110\u00e3 sao ch\u00e9p \u2713</span>'}catch{b.innerHTML=safe(code)+'<span>Nh\u1eadp m\u00e3 \u1edf gi\u1ecf h\u00e0ng</span>'}}));
document.querySelectorAll('[data-account-preference]').forEach(i=>{const k='reroom-account-pref-'+i.dataset.accountPreference,v=localStorage.getItem(k);if(v!==null)i.checked=v==='true';i.addEventListener('change',()=>localStorage.setItem(k,String(i.checked)))});
const links=[...document.querySelectorAll('[data-account-nav]')];links.forEach(a=>a.addEventListener('click',()=>links.forEach(x=>x.classList.toggle('is-active',x===a))));
if('IntersectionObserver'in window){const io=new IntersectionObserver(entries=>{const e=entries.filter(x=>x.isIntersecting).sort((a,b)=>b.intersectionRatio-a.intersectionRatio)[0];if(e)links.forEach(a=>a.classList.toggle('is-active',a.hash==='#'+e.target.id))},{rootMargin:'-14% 0px -72% 0px',threshold:[0,.1,.35]});links.forEach(a=>{const s=document.querySelector(a.hash);if(s)io.observe(s)})}
})();

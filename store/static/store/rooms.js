(()=>{
  const svg=document.getElementById('sampleRoomPlan');
  if(!svg)return;
  const form=document.getElementById('sampleRoomForm');
  const floorLayer=document.getElementById('roomPlanFloor');
  const architectureLayer=document.getElementById('roomPlanArchitecture');
  const objectLayer=document.getElementById('roomPlanObjects');
  const selectionLabel=document.getElementById('roomPlanSelection');
  const rotateButton=document.getElementById('rotateRoomProduct');
  const removeButton=document.getElementById('removeRoomProduct');
  const plannerLayout=document.getElementById('roomPlannerLayout');
  const plannerHome=plannerLayout.parentElement;
  const fullscreenControls=document.getElementById('roomFullscreenControls');
  const fullscreenToggle=document.getElementById('roomFullscreenToggle');
  const fullscreenClose=document.getElementById('roomFullscreenClose');
  const zoomLevel=document.getElementById('roomZoomLevel');
  const budgetToggle=document.getElementById('roomBudgetToggle');
  const budgetPanel=document.getElementById('roomBudgetPanel');
  const budgetTotal=document.getElementById('roomBudgetTotal');
  const budgetBreakdown=document.getElementById('roomBudgetBreakdown');
  const roomWidthInput=form.elements.width,roomDepthInput=form.elements.depth;
  const paletteInput=form.elements.palette;
  const loftInput=form.elements.loft,doorSideInput=form.elements.doorSide;
  const doorSwingInput=form.elements.doorSwing,doorPositionInput=form.elements.doorPosition;
  const bathroomInput=form.elements.bathroom,kitchenInput=form.elements.kitchen;
  const loftSideInput=form.elements.loftSide,loftDirectionField=document.getElementById('roomLoftDirectionField');
  const ns='http://www.w3.org/2000/svg';
  let roomWidth=Number(roomWidthInput.value)||3,roomDepth=Number(roomDepthInput.value)||4;
  let objects=[],selectedId=null,frame=null,drag=null,zoom=1,plannerPlaceholder=null,budgetExpanded=false;
  const zones={bathroom:null,kitchen:null};
  const normalize=value=>String(value||'').normalize('NFD').replace(/\p{Diacritic}/gu,'').toLowerCase();
  const swatches=[[/xanh\s*duong|xanh\s*bien/,'#9ab7d2'],[/xanh\s*reu/,'#a7b28d'],[/xanh\s*la/,'#a8bd9e'],[/(^|\s)trang($|\s)/,'#f4eee8'],[/kem/,'#edcfaa'],[/(^|\s)be($|\s)/,'#d9bd9e'],[/vang/,'#e8cf84'],[/hong/,'#e8a9b8'],[/mau\s*do|do\s*tuoi/,'#d9847b'],[/nau/,'#9d7964'],[/(^|\s)den($|\s)/,'#777274'],[/caro/,'#caa899'],[/xanh/,'#9ab7bd']];
  function productColor(hint,name){const value=normalize(hint+' '+name);for(const [pattern,color] of swatches){if(pattern.test(value))return color}let hash=0;for(const char of value)hash=(hash*31+char.charCodeAt(0))|0;return ['#e8b5bb','#b9c8b2','#d9c2a4','#b9c4d7','#dfb6d0','#b8d0cd'][Math.abs(hash)%6]}
  function node(tag,attrs={}){const result=document.createElementNS(ns,tag);Object.entries(attrs).forEach(([key,value])=>result.setAttribute(key,String(value)));return result}
  function formatMoney(value){return new Intl.NumberFormat('vi-VN',{maximumFractionDigits:0}).format(Number(value)||0)+' ₫'}
  function updateBudgetPanel(){
    if(!budgetExpanded)return;
    const groups=new Map();
    objects.forEach(item=>{const key=item.name+'|'+item.price;const group=groups.get(key)||{name:item.name,price:item.price,quantity:0};group.quantity+=1;groups.set(key,group)});
    const total=objects.reduce((sum,item)=>sum+(Number(item.price)||0),0);
    budgetTotal.textContent='Tạm tính '+formatMoney(total)+' · '+objects.length+' món';
    budgetBreakdown.replaceChildren();
    if(!groups.size){const empty=document.createElement('li');empty.textContent='Thêm sản phẩm vào sơ đồ để xem bảng kê.';budgetBreakdown.append(empty);return}
    groups.forEach(group=>{const row=document.createElement('li'),name=document.createElement('span'),price=document.createElement('strong');name.textContent=group.name+' × '+group.quantity;price.textContent=formatMoney(group.price*group.quantity);row.append(name,price);budgetBreakdown.append(row)});
  }
  function updateZoom(){const width=760/zoom,height=700/zoom;svg.setAttribute('viewBox',`${(760-width)/2} ${(700-height)/2} ${width} ${height}`);zoomLevel.textContent=`${Math.round(zoom*100)}%`}
  function setFullscreen(enabled){
    plannerLayout.classList.toggle('is-fullscreen',enabled);document.body.classList.toggle('room-plan-layout-open',enabled);
    zoom=1;updateZoom();
    if(enabled){plannerPlaceholder=document.createComment('room planner position');plannerHome.insertBefore(plannerPlaceholder,plannerLayout);document.body.append(plannerLayout);fullscreenControls.append(form);fullscreenToggle.hidden=true;fullscreenClose.hidden=false;fullscreenToggle.setAttribute('aria-pressed','true')}
    else{plannerHome.insertBefore(plannerLayout,plannerPlaceholder);plannerPlaceholder.remove();plannerPlaceholder=null;plannerHome.insertBefore(form,plannerLayout);fullscreenToggle.hidden=false;fullscreenClose.hidden=true;fullscreenToggle.setAttribute('aria-pressed','false')}
    requestAnimationFrame(drawPlan);
  }
  fullscreenToggle.addEventListener('click',()=>setFullscreen(true));
  fullscreenClose.addEventListener('click',()=>setFullscreen(false));
  document.addEventListener('keydown',event=>{if(event.key==='Escape'&&plannerLayout.classList.contains('is-fullscreen'))setFullscreen(false)});
  document.getElementById('roomZoomIn').addEventListener('click',()=>{zoom=Math.min(2.8,Math.round((zoom+0.2)*10)/10);updateZoom()});
  document.getElementById('roomZoomOut').addEventListener('click',()=>{zoom=Math.max(1,Math.round((zoom-0.2)*10)/10);updateZoom()});
  document.getElementById('roomZoomReset').addEventListener('click',()=>{zoom=1;updateZoom()});
  function clampObjects(){const pad=.06;objects.forEach(item=>{item.width=Math.min(item.width,Math.max(.2,roomWidth-pad*2));item.depth=Math.min(item.depth,Math.max(.2,roomDepth-pad*2));item.x=Math.max(pad,Math.min(roomWidth-pad-item.width,item.x));item.y=Math.max(pad,Math.min(roomDepth-pad-item.depth,item.y))})}
  function getFrame(){const scale=Math.min(620/roomWidth,430/roomDepth,150);const width=roomWidth*scale,depth=roomDepth*scale;return{x:(760-width)/2,y:(700-depth)/2,width,depth,scale}}
  function drawRoomArchitecture(){
    architectureLayer.replaceChildren();
    const wallWidth=Math.max(4,frame.scale*.055),side=doorSideInput.value;
    if(loftInput.checked){
      const loftSide=loftSideInput.value,horizontal=loftSide==='top'||loftSide==='bottom';
      const loftWidth=horizontal?frame.width-wallWidth*2:Math.min(frame.width*.4,1.7*frame.scale);
      const loftDepth=horizontal?Math.min(frame.depth*.4,1.7*frame.scale):frame.depth-wallWidth*2;
      const loftX=loftSide==='right'?frame.x+frame.width-wallWidth-loftWidth:frame.x+wallWidth;
      const loftY=loftSide==='bottom'?frame.y+frame.depth-wallWidth-loftDepth:frame.y+wallWidth;
      architectureLayer.append(node('rect',{x:loftX,y:loftY,width:loftWidth,height:loftDepth,rx:3,class:'room-loft-area'}));
      const boundary=horizontal
        ?node('line',{x1:frame.x+wallWidth,y1:loftSide==='top'?loftY+loftDepth:loftY,x2:frame.x+frame.width-wallWidth,y2:loftSide==='top'?loftY+loftDepth:loftY,stroke:'#ac9278','stroke-width':2,'stroke-dasharray':'7 5'})
        :node('line',{x1:loftSide==='left'?loftX+loftWidth:loftX,y1:frame.y+wallWidth,x2:loftSide==='left'?loftX+loftWidth:loftX,y2:frame.y+frame.depth-wallWidth,stroke:'#ac9278','stroke-width':2,'stroke-dasharray':'7 5'});
      architectureLayer.append(boundary);
      const loftLabel=node('text',{x:loftX+loftWidth/2,y:loftY+loftDepth/2+4,class:'room-structure-label'});
      loftLabel.textContent='KHU GÁC LỬNG';architectureLayer.append(loftLabel);
      const ladderLength=frame.scale*.42,ladderCenter=horizontal?frame.x+frame.width*.76:frame.y+frame.depth*.76;
      const ladderBoundary=horizontal?(loftSide==='top'?loftY+loftDepth:loftY):(loftSide==='left'?loftX+loftWidth:loftX);
      const ladderStart=horizontal?(loftSide==='top'?ladderBoundary:ladderBoundary-ladderLength):ladderBoundary;
      const ladderEnd=horizontal?(loftSide==='top'?ladderBoundary+ladderLength:ladderBoundary):ladderBoundary+(loftSide==='left'?ladderLength:-ladderLength);
      if(horizontal){
        architectureLayer.append(node('path',{d:'M '+(ladderCenter-10)+' '+ladderStart+' V '+ladderEnd+' M '+(ladderCenter+10)+' '+ladderStart+' V '+ladderEnd,stroke:'#a88d70','stroke-width':2}));
        for(let rung=1;rung<5;rung++)architectureLayer.append(node('line',{x1:ladderCenter-9,y1:ladderStart+(ladderEnd-ladderStart)*rung/5,x2:ladderCenter+9,y2:ladderStart+(ladderEnd-ladderStart)*rung/5,stroke:'#a88d70','stroke-width':1.4}));
      }else{
        architectureLayer.append(node('path',{d:'M '+ladderStart+' '+(ladderCenter-10)+' H '+ladderEnd+' M '+ladderStart+' '+(ladderCenter+10)+' H '+ladderEnd,stroke:'#a88d70','stroke-width':2}));
        for(let rung=1;rung<5;rung++)architectureLayer.append(node('line',{x1:ladderStart+(ladderEnd-ladderStart)*rung/5,y1:ladderCenter-9,x2:ladderStart+(ladderEnd-ladderStart)*rung/5,y2:ladderCenter+9,stroke:'#a88d70','stroke-width':1.4}));
      }
    }
    const zoneWidth=roomWidth*.27,zoneDepth=roomDepth*.2;
    const addZone=(id,label,defaultX,defaultY,fill)=>{
      const position=zones[id]||(zones[id]={x:defaultX,y:defaultY});
      position.x=Math.max(.04,Math.min(roomWidth-zoneWidth-.04,position.x));
      position.y=Math.max(.04,Math.min(roomDepth-zoneDepth-.04,position.y));
      const x=frame.x+position.x*frame.scale,y=frame.y+position.y*frame.scale,w=zoneWidth*frame.scale,h=zoneDepth*frame.scale;
      const group=node('g',{class:'room-zone-group','data-room-zone':id,transform:'translate('+x+' '+y+')',tabindex:0,role:'button','aria-label':'Kéo để di chuyển '+label.toLowerCase()});
      group.append(node('rect',{x:0,y:0,width:w,height:h,rx:5,class:'room-zone',fill}));
      const text=node('text',{x:w/2,y:h/2+4,class:'room-zone-label'});text.textContent=label;group.append(text);architectureLayer.append(group);
    };
    if(bathroomInput.checked)addZone('bathroom','NHÀ VỆ SINH',roomWidth-zoneWidth-.12,roomDepth-zoneDepth-.12,'#dce8e3');
    if(kitchenInput.checked&&!loftInput.checked)addZone('kitchen','KHU BẾP',roomWidth-zoneWidth-.12,.12,'#f0e5d7');
    const horizontal=side==='top'||side==='bottom';
    const sideLength=horizontal?frame.width:frame.depth;
    const doorWidth=Math.min(frame.scale*.82,sideLength*.34);
    const center=Math.max(doorWidth*.65,Math.min(sideLength-doorWidth*.65,sideLength*Number(doorPositionInput.value||.5)));
    const start=center-doorWidth/2,end=center+doorWidth/2;
    const walls={
      top:{x:frame.x,y:frame.y,tx:1,ty:0,nx:0,ny:1,length:frame.width},
      bottom:{x:frame.x,y:frame.y+frame.depth,tx:1,ty:0,nx:0,ny:-1,length:frame.width},
      left:{x:frame.x,y:frame.y,tx:0,ty:1,nx:1,ny:0,length:frame.depth},
      right:{x:frame.x+frame.width,y:frame.y,tx:0,ty:1,nx:-1,ny:0,length:frame.depth}
    };
    const wallLine=(a,b)=>architectureLayer.append(node('line',{x1:a.x,y1:a.y,x2:b.x,y2:b.y,class:'room-wall'}));
    Object.entries(walls).forEach(([wallSide,wall])=>{
      if(wallSide===side)return;
      wallLine({x:wall.x,y:wall.y},{x:wall.x+wall.tx*wall.length,y:wall.y+wall.ty*wall.length});
    });
    const {x:wallX,y:wallY,tx,ty,nx:wallNx,ny:wallNy}=walls[side];
    let nx=wallNx,ny=wallNy;
    if(doorSwingInput.value==='outside'){nx=-nx;ny=-ny}
    const pointAt=distance=>({x:wallX+tx*distance,y:wallY+ty*distance});
    const line=(a,b,attrs={})=>architectureLayer.append(node('line',{x1:a.x,y1:a.y,x2:b.x,y2:b.y,class:'room-wall',...attrs}));
    line(pointAt(0),pointAt(start));line(pointAt(end),pointAt(sideLength));
    const hinge=pointAt(start),closed={x:hinge.x+tx*doorWidth,y:hinge.y+ty*doorWidth},open={x:hinge.x+nx*doorWidth,y:hinge.y+ny*doorWidth};
    architectureLayer.append(node('line',{x1:hinge.x,y1:hinge.y,x2:open.x,y2:open.y,class:'room-door-leaf'}));
    const sweep=tx*ny-ty*nx>0?1:0;
    architectureLayer.append(node('path',{d:'M '+closed.x+' '+closed.y+' A '+doorWidth+' '+doorWidth+' 0 0 '+sweep+' '+open.x+' '+open.y,class:'room-door-arc'}));
    const doorLabel=node('text',{x:hinge.x+tx*doorWidth/2+nx*9,y:hinge.y+ty*doorWidth/2+ny*9,class:'room-door-label'});
    doorLabel.textContent='CỬA · '+({top:'BẮC',right:'ĐÔNG',bottom:'NAM',left:'TÂY'}[side]);architectureLayer.append(doorLabel);
  }
  function wrappedName(value,maxChars){
    const words=String(value||'').trim().split(/\s+/);let lines=[''];
    for(const original of words){
      let word=original;
      while(Array.from(word).length>maxChars){const chars=Array.from(word);const piece=chars.splice(0,maxChars-1).join('')+'…';word=chars.join('');if(lines[lines.length-1])lines.push('');lines[lines.length-1]=piece;if(lines.length>=2)return lines}
      const current=lines[lines.length-1];
      if(current&&Array.from(current+' '+word).length>maxChars){if(lines.length===2){lines[1]=lines[1].slice(0,Math.max(1,maxChars-1))+'…';return lines}lines.push(word)}
      else lines[lines.length-1]=current?current+' '+word:word;
    }
    if(lines.length>2)lines.length=2;
    return lines.filter(Boolean);
  }
  function drawPlan(){
    loftDirectionField.hidden=!loftInput.checked;
    kitchenInput.disabled=loftInput.checked;
    document.getElementById('roomKitchenToggle').classList.toggle('is-disabled',kitchenInput.disabled);
    frame=getFrame();floorLayer.replaceChildren();architectureLayer.replaceChildren();objectLayer.replaceChildren();
    const floor=node('rect',{x:frame.x,y:frame.y,width:frame.width,height:frame.depth,rx:3,fill:paletteInput.value,class:'room-floor'});
    const grid=node('rect',{x:frame.x,y:frame.y,width:frame.width,height:frame.depth,rx:8,fill:'url(#roomGrid)',opacity:.7,'pointer-events':'none'});
    floorLayer.append(floor,grid);
    const label=node('text',{x:frame.x,y:frame.y-14,fill:'#836c64','font-size':13,'font-family':'sans-serif','font-weight':700});
    label.textContent=roomWidth+' × '+roomDepth+' m';floorLayer.append(label);
    document.getElementById('roomPlanDimensions').textContent='Phòng '+roomWidth+' × '+roomDepth+' m';
    const pattern=svg.querySelector('#roomGrid');pattern.setAttribute('width',Math.max(12,frame.scale/2));pattern.setAttribute('height',Math.max(12,frame.scale/2));
    drawRoomArchitecture();
    if(!objects.length){const empty=node('text',{x:frame.x+frame.width/2,y:frame.y+frame.depth/2,fill:'#b29d96','font-size':13,'font-family':'sans-serif','text-anchor':'middle'});empty.textContent='Chọn sản phẩm bên trái để bắt đầu bố trí';objectLayer.append(empty)}
    objects.forEach(item=>drawObject(item));
    const selected=objects.find(item=>item.id===selectedId);
    selectionLabel.textContent=selected?selected.name+(selected.estimated?' · kích thước tạm tính':'')+' · '+Math.round(selected.width*100)+' × '+Math.round(selected.depth*100)+' cm · '+formatMoney(selected.price):'Chọn món đồ trong danh sách';
    rotateButton.disabled=!selected;removeButton.disabled=!selected;
    updateBudgetPanel();
  }
  function drawObject(item){
    const x=frame.x+item.x*frame.scale,y=frame.y+item.y*frame.scale,w=item.width*frame.scale,h=item.depth*frame.scale;
    const group=node('g',{class:'room-object'+(item.id===selectedId?' is-selected':''),'data-room-object':item.id,transform:'translate('+x+' '+y+')',tabindex:0,role:'button','aria-label':item.name+'; '+Math.round(item.width*100)+' × '+Math.round(item.depth*100)+' cm'});
    const title=node('title');title.textContent=item.name+' · '+Math.round(item.width*100)+' × '+Math.round(item.depth*100)+' cm'+(item.estimated?' · kích thước tạm tính':'');group.append(title);
    const base=node('rect',{class:'object-footprint',x:1,y:1,width:Math.max(1,w-2),height:Math.max(1,h-2),rx:Math.min(12,w/8,h/8),fill:item.color,stroke:item.id===selectedId?'#e64e87':'#907e70','stroke-width':item.id===selectedId?3:1.5});group.append(base);
    const shape=normalize(item.category+' '+item.name);
    if(!item.topView){
    if(/giuong|nem|chan|goi|bed/.test(shape)){
      group.append(node('rect',{x:2,y:2,width:Math.max(1,w-4),height:Math.max(8,h*.18),rx:5,fill:'#8e776b',opacity:.75}));
      for(let i=0;i<2;i++)group.append(node('rect',{x:w*.12+i*w*.4,y:h*.23,width:w*.32,height:h*.16,rx:5,fill:'#fffaf4',stroke:'#d7c4b7','stroke-width':1}));
      group.append(node('path',{d:'M '+(w*.08)+' '+(h*.46)+' H '+(w*.92),stroke:'#ffffffad','stroke-width':2,'pointer-events':'none'}));
    }else if(/sofa|ghe|armchair/.test(shape)){
      group.append(node('rect',{x:w*.12,y:h*.2,width:w*.76,height:h*.62,rx:9,fill:'#fffaf2a8',stroke:'#ffffffd9','stroke-width':1.5}));
      group.append(node('path',{d:'M '+(w*.5)+' '+(h*.22)+' V '+(h*.8),stroke:'#ffffffd9','stroke-width':1.5}));
      group.append(node('rect',{x:w*.04,y:h*.23,width:w*.1,height:h*.55,rx:5,fill:item.color,stroke:'#907e70','stroke-width':1}));
      group.append(node('rect',{x:w*.86,y:h*.23,width:w*.1,height:h*.55,rx:5,fill:item.color,stroke:'#907e70','stroke-width':1}));
    }else if(/ban|desk|table/.test(shape)){
      group.append(node('circle',{cx:w/2,cy:h/2,r:Math.min(w,h)*.12,fill:'#fffaf4a8'}));
      for(const [lx,ly] of [[.12,.12],[.82,.12],[.12,.82],[.82,.82]])group.append(node('circle',{cx:w*lx,cy:h*ly,r:Math.min(w,h)*.035,fill:'#806c60'}));
    }else if(/tu|ke|cabinet|wardrobe/.test(shape)){
      group.append(node('path',{d:'M '+(w*.5)+' 4 V '+(h-4),stroke:'#ffffffb8','stroke-width':1.5}));
      group.append(node('circle',{cx:w*.44,cy:h*.52,r:2.3,fill:'#826a61'}));group.append(node('circle',{cx:w*.56,cy:h*.52,r:2.3,fill:'#826a61'}));
    }
    }
    if(item.topView){
      const clipId='room-top-view-'+String(item.id).replace(/[^a-z0-9_-]/gi,'');
      const clip=node('clipPath',{id:clipId,clipPathUnits:'userSpaceOnUse'});
      clip.append(node('rect',{x:2,y:2,width:Math.max(1,w-4),height:Math.max(1,h-4),rx:Math.min(10,w/8,h/8)}));
      const defs=node('defs');defs.append(clip);group.append(defs);
      const imageAttrs={x:2,y:2,width:Math.max(1,w-4),height:Math.max(1,h-4),preserveAspectRatio:'xMidYMid meet','clip-path':'url(#'+clipId+')',href:item.topView};
      if(item.rotation===90){imageAttrs.x=(w-h+4)/2;imageAttrs.y=(h-w+4)/2;imageAttrs.width=Math.max(1,h-4);imageAttrs.height=Math.max(1,w-4);imageAttrs.transform='rotate(90 '+(w/2)+' '+(h/2)+')'}
      group.append(node('image',imageAttrs));
      if(item.id===selectedId)group.append(node('rect',{x:1,y:1,width:Math.max(1,w-2),height:Math.max(1,h-2),rx:Math.min(12,w/8,h/8),fill:'none',stroke:'#e64e87','stroke-width':3,'pointer-events':'none'}));
    }
    if(!item.topView&&w>=38&&h>=30){
      const fontSize=Math.max(6,Math.min(9,w/9)),maxChars=Math.max(4,Math.floor((w-10)/(fontSize*.58))),lines=wrappedName(item.name,maxChars).slice(0,2),lineHeight=fontSize+2,labelHeight=lines.length*lineHeight+3,labelY=Math.max(4,h*.52-labelHeight/2),labelWidth=Math.min(w-6,Math.max(fontSize*3,Math.max(...lines.map(text=>Array.from(text).length))*fontSize*.62+8));
      group.append(node('rect',{x:(w-labelWidth)/2,y:labelY,width:labelWidth,height:labelHeight,rx:3,fill:'#fffaf2e8','pointer-events':'none'}));
      const name=node('text',{x:w/2,y:labelY+fontSize,fill:'#493c39','font-size':fontSize,'font-family':'sans-serif','font-weight':700,'text-anchor':'middle','pointer-events':'none'});
      lines.forEach((line,index)=>{const span=node('tspan',{x:w/2,dy:index?lineHeight:0});span.textContent=line;name.append(span)});group.append(name);
    }
    if(item.id===selectedId){const size=node('text',{x:w/2,y:h-5,fill:'#6c5550','font-size':8,'font-family':'sans-serif','text-anchor':'middle','pointer-events':'none'});size.textContent=Math.round(item.width*100)+'×'+Math.round(item.depth*100);group.append(size)}
    objectLayer.append(group);
  }
  function overlaps(x,y,w,h,ignore=null){return objects.some(item=>item.id!==ignore&&x<item.x+item.width+.04&&x+w+.04>item.x&&y<item.y+item.depth+.04&&y+h+.04>item.y)}
  function findPosition(w,h){const pad=.08;for(let y=pad;y+h<=roomDepth-pad+.001;y+=.2){for(let x=pad;x+w<=roomWidth-pad+.001;x+=.2){if(!overlaps(x,y,w,h))return{x,y}}}return{x:Math.max(pad,(roomWidth-w)/2),y:Math.max(pad,(roomDepth-h)/2)}}
  document.querySelectorAll('[data-add-room-product]').forEach(button=>button.addEventListener('click',()=>{
    const rawWidth=(Number(button.dataset.width)||70)/100,rawDepth=(Number(button.dataset.depth)||55)/100;
    const width=Math.min(rawWidth,Math.max(.2,roomWidth-.16)),depth=Math.min(rawDepth,Math.max(.2,roomDepth-.16)),position=findPosition(width,depth);
    const item={id:Date.now().toString(36)+Math.random().toString(36).slice(2,7),name:button.dataset.name||'Sản phẩm',category:button.dataset.category||'',colorHint:button.dataset.color||'',color:productColor(button.dataset.color,button.dataset.name),topView:button.dataset.topView||'',price:Math.max(0,Number(button.dataset.price)||0),rotation:0,width,depth,x:position.x,y:position.y,estimated:button.dataset.estimated==='true'};
    objects.push(item);selectedId=item.id;drawPlan();
  }));
  document.getElementById('roomProductSearch')?.addEventListener('input',event=>{const query=normalize(event.target.value);document.querySelectorAll('[data-room-product]').forEach(item=>item.hidden=!normalize(item.dataset.search).includes(query))});
  form.addEventListener('submit',event=>{event.preventDefault();roomWidth=Math.min(10,Math.max(1,Number(roomWidthInput.value)||3));roomDepth=Math.min(15,Math.max(1,Number(roomDepthInput.value)||4));roomWidthInput.value=roomWidth;roomDepthInput.value=roomDepth;clampObjects();drawPlan()});
  [doorSideInput,doorSwingInput,doorPositionInput,paletteInput,bathroomInput,kitchenInput,loftSideInput,loftInput].forEach(input=>['input','change'].forEach(eventName=>input.addEventListener(eventName,drawPlan)));
  svg.addEventListener('pointerdown',event=>{const zoneGroup=event.target.closest('[data-room-zone]'),group=event.target.closest('[data-room-object]');if(!zoneGroup&&!group)return;const point=svg.createSVGPoint();point.x=event.clientX;point.y=event.clientY;const local=point.matrixTransform(svg.getScreenCTM().inverse());if(zoneGroup){const id=zoneGroup.dataset.roomZone,position=zones[id];if(!position)return;selectedId=null;drag={type:'zone',id,offsetX:(local.x-frame.x)/frame.scale-position.x,offsetY:(local.y-frame.y)/frame.scale-position.y}}else{const item=objects.find(value=>value.id===group.dataset.roomObject);if(!item)return;selectedId=item.id;drag={type:'object',id:item.id,offsetX:(local.x-frame.x)/frame.scale-item.x,offsetY:(local.y-frame.y)/frame.scale-item.y}}svg.setPointerCapture(event.pointerId);drawPlan();event.preventDefault()});
  svg.addEventListener('pointermove',event=>{if(!drag)return;const point=svg.createSVGPoint();point.x=event.clientX;point.y=event.clientY;const local=point.matrixTransform(svg.getScreenCTM().inverse());if(drag.type==='zone'){const position=zones[drag.id],width=roomWidth*.27,depth=roomDepth*.2;if(!position)return;position.x=Math.max(.04,Math.min(roomWidth-width-.04,(local.x-frame.x)/frame.scale-drag.offsetX));position.y=Math.max(.04,Math.min(roomDepth-depth-.04,(local.y-frame.y)/frame.scale-drag.offsetY));drawPlan();return}const item=objects.find(value=>value.id===drag.id);if(!item)return;const pad=.06;item.x=Math.max(pad,Math.min(roomWidth-pad-item.width,(local.x-frame.x)/frame.scale-drag.offsetX));item.y=Math.max(pad,Math.min(roomDepth-pad-item.depth,(local.y-frame.y)/frame.scale-drag.offsetY));drawPlan()});
  svg.addEventListener('keydown',event=>{const group=event.target.closest('[data-room-zone]');if(!group)return;const position=zones[group.dataset.roomZone];if(!position)return;const step=event.shiftKey ? 0.25 : 0.1,width=roomWidth*.27,depth=roomDepth*.2;const moves={ArrowLeft:[-step,0],ArrowRight:[step,0],ArrowUp:[0,-step],ArrowDown:[0,step]};if(!moves[event.key])return;const [dx,dy]=moves[event.key];position.x=Math.max(.04,Math.min(roomWidth-width-.04,position.x+dx));position.y=Math.max(.04,Math.min(roomDepth-depth-.04,position.y+dy));const id=group.dataset.roomZone;drawPlan();svg.querySelector('[data-room-zone="'+id+'"]')?.focus();event.preventDefault()});
  const endDrag=()=>{drag=null};svg.addEventListener('pointerup',endDrag);svg.addEventListener('pointercancel',endDrag);
  rotateButton.addEventListener('click',()=>{const item=objects.find(value=>value.id===selectedId);if(!item)return;[item.width,item.depth]=[item.depth,item.width];item.rotation=item.rotation===90?0:90;const pad=.06;item.x=Math.max(pad,Math.min(item.x,roomWidth-pad-item.width));item.y=Math.max(pad,Math.min(item.y,roomDepth-pad-item.depth));drawPlan()});
  removeButton.addEventListener('click',()=>{objects=objects.filter(item=>item.id!==selectedId);selectedId=null;drawPlan()});
  document.getElementById('clearRoomPlan').addEventListener('click',()=>{objects=[];selectedId=null;drawPlan()});
  budgetToggle.addEventListener('click',()=>{budgetExpanded=!budgetExpanded;budgetPanel.hidden=!budgetExpanded;budgetToggle.setAttribute('aria-expanded',String(budgetExpanded));updateBudgetPanel()});
  document.getElementById('roomPlanExport').addEventListener('click',()=>{const copy=svg.cloneNode(true);copy.setAttribute('xmlns',ns);copy.setAttribute('width','1520');copy.setAttribute('height','1400');copy.setAttribute('viewBox','0 0 760 700');const styles=node('style');styles.textContent='.room-wall{stroke:#879681;stroke-width:7;stroke-linecap:square;fill:none}.room-door-leaf{stroke:#ae8f76;stroke-width:2.2;fill:none}.room-door-arc{stroke:#bc9b80;stroke-width:1.5;stroke-dasharray:4 3;fill:none}.room-loft-area{fill:#c8aa8b;fill-opacity:.23;stroke:#ac9278;stroke-width:1.5;stroke-dasharray:7 5}.room-zone{stroke:#b7c7bb;stroke-width:1.5}.room-zone-label{fill:#817460;font:700 7px sans-serif;text-anchor:middle}.room-structure-label{fill:#817460;font:700 11px sans-serif;letter-spacing:.06em;text-anchor:middle}.room-door-label{fill:#967b68;font:600 8px sans-serif;text-anchor:middle}.room-compass text{fill:#817460;font:700 10px sans-serif;text-anchor:middle}.room-compass path{fill:none;stroke:#879681;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}';copy.insertBefore(styles,copy.firstChild);const xml=new XMLSerializer().serializeToString(copy);const url=URL.createObjectURL(new Blob([xml],{type:'image/svg+xml;charset=utf-8'}));const link=document.createElement('a');link.href=url;link.download='reroom-so-do-phong.svg';link.click();URL.revokeObjectURL(url)});
  document.querySelectorAll('.room-filters button').forEach(button=>button.addEventListener('click',()=>{document.querySelectorAll('.room-filters button').forEach(other=>other.classList.toggle('active',other===button));const filter=normalize(button.dataset.filter),terms={ngu:['ngu','chan','goi','giuong'],hoc:['hoc','ban','den'],'thu gian':['thu gian','sofa','ghe']}[filter]||[filter];document.querySelectorAll('#roomProducts .product-card').forEach(card=>card.hidden=filter!=='all'&&!terms.some(term=>normalize(card.dataset.category).includes(term)))}));
  updateZoom();drawPlan();
})();

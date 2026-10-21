(()=>{
 const photo=document.getElementById('roomGalleryPhoto');
 const fallback=document.getElementById('roomGalleryFallback');
 const buttons=[...document.querySelectorAll('.room-gallery-picks button[data-image]')];
 if(!photo||!fallback||!buttons.length)return;
 function showFallback(){photo.hidden=true;fallback.hidden=false}
 function showPhoto(){photo.hidden=false;fallback.hidden=true}
 function select(button){
  buttons.forEach(item=>item.classList.toggle('active',item===button));
  photo.onerror=showFallback;photo.onload=showPhoto;
  photo.alt=button.dataset.title||'Room sample';
  photo.src=button.dataset.image;
  if(photo.complete){if(photo.naturalWidth)showPhoto();else showFallback()}
 }
 buttons.forEach(button=>button.addEventListener('click',()=>select(button)));
 select(buttons.find(button=>button.classList.contains('active'))||buttons[0]);
})();

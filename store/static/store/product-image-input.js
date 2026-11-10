(()=>{
  document.querySelectorAll('.js-product-images').forEach(input=>{
    const preview=input.closest('.field,.staff-proposals-field')?.querySelector('[data-image-preview]');
    if(!preview)return;
    input.addEventListener('change',()=>{
      preview.replaceChildren();
      const files=Array.from(input.files||[]);
      if(!files.length)return;
      files.forEach((file,index)=>{
        if(!file.type.startsWith('image/'))return;
        const figure=document.createElement('figure');
        const image=document.createElement('img');
        const caption=document.createElement('figcaption');
        image.src=URL.createObjectURL(file);
        image.alt=file.name;
        image.onload=()=>URL.revokeObjectURL(image.src);
        caption.textContent=index===0?'Ảnh '+(index+1)+' · '+file.name:file.name;
        figure.append(image,caption);
        preview.append(figure);
      });
      const note=document.createElement('span');
      note.className='preview-pending';
      note.textContent=files.length+' ảnh đã chọn';
      preview.append(note);
    });
  });
})();

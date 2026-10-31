/* KL EventRadar: zugängliche Helligkeitssteuerung, unabhängig vom Event-Kalender. */
(function(root, factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  if(root&&root.document){root.KLBrightness=api;api.init(root.document, root.localStorage);}
})(typeof window!=='undefined'?window:undefined,function(){
  'use strict';
  const KEY='kl-eventradar-brightness';
  const DEFAULT=100;
  const LEVELS=[70,85,100,115,130];
  function normalize(raw){
    const number=Number(raw);
    return LEVELS.includes(number)?number:DEFAULT;
  }
  function description(value){
    const v=normalize(value);
    return v===DEFAULT?'100 % · Standard':v<DEFAULT?v+' % · Dunkler':v+' % · Heller';
  }
  function init(doc,store){
    const button=doc.getElementById('btn-brightness');
    const panel=doc.getElementById('brightness-panel');
    const slider=doc.getElementById('brightness-range');
    const output=doc.getElementById('brightness-value');
    const reset=doc.getElementById('brightness-reset');
    if(!button||!panel||!slider||!output||!reset)return;
    let level=DEFAULT;
    try{level=normalize(store.getItem(KEY));}catch{}
    function apply(raw,persist=true){
      level=normalize(raw);
      // Standard entfernt bewusst jede Überschreibung: die alte Optik bleibt exakt erhalten.
      if(level===DEFAULT)doc.documentElement.removeAttribute('data-kl-brightness');
      else doc.documentElement.setAttribute('data-kl-brightness',String(level));
      slider.value=String(level);
      const detail=description(level);
      output.textContent=detail;
      slider.setAttribute('aria-valuetext',detail);
      button.textContent='◐ Helligkeit: '+(level===DEFAULT?'Standard':level+' %');
      if(persist){
        try{if(level===DEFAULT)store.removeItem(KEY);else store.setItem(KEY,String(level));}catch{}
      }
    }
    function close(){
      panel.classList.add('hidden');
      button.setAttribute('aria-expanded','false');
    }
    button.addEventListener('click',()=>{
      if(panel.classList.contains('hidden')){
        panel.classList.remove('hidden');
        button.setAttribute('aria-expanded','true');
        slider.focus();
      }else close();
    });
    slider.addEventListener('input',()=>apply(slider.value));
    slider.addEventListener('change',()=>apply(slider.value));
    reset.addEventListener('click',()=>apply(DEFAULT));
    doc.addEventListener('pointerdown',event=>{
      if(!panel.classList.contains('hidden')&&!doc.getElementById('brightness-control').contains(event.target))close();
    });
    doc.addEventListener('keydown',event=>{
      if(event.key==='Escape'&&!panel.classList.contains('hidden')){close();button.focus();}
    });
    apply(level,false);
  }
  return {KEY,DEFAULT,LEVELS,normalize,description,init};
});

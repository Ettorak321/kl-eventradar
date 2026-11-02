/* KL EventRadar V12: Symbole und umschaltbare kompakte Smartphone-Ansicht. */
(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  if(root){root.KLMobile=api;}
})(typeof window!=='undefined'?window:globalThis,function(){
 'use strict';
 const KEY='kl-mobile-compact';
 const ICONS=Object.freeze({
  fussball:'🏟️',fck_auswaerts:'⚽↗',kerwe:'🎡',stadtfest:'🎉',
  konzert:'🎵',sport:'🏅',markt:'🛍️',feiertag:'⭐',anlass:'✨',
  ausstellung:'🖼️',museum:'🏛️',kultur:'🎭',sonstiges:'📌'
 });
 const SHORT=Object.freeze({
  fussball:'FCK Heim',fck_auswaerts:'FCK Ausw.',kerwe:'Kerwe',
  stadtfest:'Fest',konzert:'Musik',sport:'Sport',markt:'Markt',
  feiertag:'Feiertag',anlass:'Anlass',ausstellung:'Ausstellung',
  museum:'Museum',kultur:'Kultur',sonstiges:'Termin'
 });
 function categoryOf(ev){return String(ev?.displayCategory||ev?.category||'sonstiges');}
 function iconFor(ev){
  const name=String(ev?.title||'');
  if(/weihnachtsmarkt|weihnachtsdorf|christkindlmarkt/i.test(name))return '🎄';
  return ICONS[categoryOf(ev)]||ICONS.sonstiges;
 }
 function shortLabel(ev){
  const name=String(ev?.title||'').trim();
  if(ev?.isSeries){
   if(/weihnachtsmarkt/i.test(name))return 'Weihnachtsmarkt';
   if(/kulturmarkt/i.test(name))return 'Kulturmarkt';
   return name.length>24?name.slice(0,21).trimEnd()+'…':name;
  }
  if(ev?.forecast)return 'Prognose';
  return SHORT[categoryOf(ev)]||SHORT.sonstiges;
 }
 function initToggle(doc,storage){
  const btn=doc?.getElementById('btn-mobile-density');
  if(!btn)return;
  let compact=true;
  try{compact=storage?.getItem(KEY)!=='off';}catch{}
  function apply(){
   doc.documentElement.classList.toggle('kl-mobile-standard',!compact);
   btn.setAttribute('aria-pressed',compact?'true':'false');
   btn.textContent=compact?'◧ Symbole':'▤ Textansicht';
   btn.title=compact?'Kompakte Symbolansicht aktiv; antippen für Textansicht':'Textansicht aktiv; antippen für Symbole';
  }
  btn.addEventListener('click',()=>{
   compact=!compact;
   try{storage?.setItem(KEY,compact?'on':'off');}catch{}
   apply();
  });
  apply();
 }
 return {KEY,ICONS,SHORT,iconFor,shortLabel,initToggle};
});

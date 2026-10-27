(() => {
 'use strict';
 const TAX=window.KLTypes;
 if (!TAX) throw new Error('Die Veranstaltungstypen-Bibliothek wurde nicht geladen');
 const DEFAULT_SELECTED = TAX.defaultSelected();
 let selectedKinds = new Set(DEFAULT_SELECTED);
 const NAMES={fck:'FCK-Profis',city:'Stadt Kaiserslautern',sommerswing:'Sommerswing',rlp:'OpenData Rheinland-Pfalz',ramstein:'VG Ramstein-Miesenbach',pfalz:'Pfalz Touristik (Landkreis)',weilerbach:'VG Weilerbach / Amtsblatt'};
 const REGIONS={
   'stadt-kl':['Stadt Kaiserslautern','#8b6ee0'],
   'vg-bruchmuehlbach':['Bruchmühlbach-Miesau','#b48730'],
   'vg-enkenbach':['Enkenbach-Alsenborn','#168d92'],
   'vg-landstuhl':['Landstuhl','#347ed1'],
   'vg-otterbach':['Otterbach-Otterberg','#9a5cc0'],
   'vg-ramstein':['Ramstein-Miesenbach','#27925a'],
   'vg-weilerbach':['Weilerbach','#de743d']
 };
 const eventType=ev=>TAX.decorate(ev).displayLabel;
 const typeColor=ev=>TAX.decorate(ev).displayColor;
 const regionColor=ev=>REGIONS[ev.region]?.[1]||'#607d8b';
 const areaName=ev=>REGIONS[ev.region]?.[0]||'Region nicht ermittelt';
 let remoteEvents=[],customEvents=[],filteredEvents=[],calendar=null,lastData=null;
 const $=id=>document.getElementById(id);
 const E={calendar:$('calendar'),upcoming:$('upcoming-list'),sync:$('sync-info'),alert:$('alert-banner'),source:$('source-status'),search:$('search-input'),categoryChoices:$('category-choices'),categorySummary:$('category-summary'),count:$('filter-count'),typeLegend:$('type-legend'),sourceFilter:$('filter-source'),location:$('filter-location'),region:$('filter-region'),kerwe:$('filter-kerwe'),legend:$('region-legend'),customRegion:$('custom-region'),stadium:$('filter-stadium'),major:$('filter-major'),modal:$('event-modal'),modalTitle:$('modal-title'),modalBody:$('modal-body'),modalActions:$('modal-actions'),form:$('custom-form'),customModal:$('custom-modal'),customId:$('custom-id'),customTitle:$('custom-title'),customDate:$('custom-date'),customTime:$('custom-time'),customLocation:$('custom-location'),customCategory:$('custom-category'),customDesc:$('custom-desc'),customDelete:$('custom-delete')};
 const node=(tag,props={},children=[])=>{const e=document.createElement(tag);for(const [k,v] of Object.entries(props)){if(k==='text')e.textContent=v??'';else if(k==='class')e.className=v;else if(k==='value')e.value=v;else if(k==='type')e.type=v;else if(k.startsWith('data-'))e.setAttribute(k,v);}for(const c of children)e.append(c);return e;};
 const safeUrl=url=>{try{const u=new URL(url);return ['http:','https:'].includes(u.protocol)?u.href:null;}catch{return null;}};
 const dateOnly=iso=>iso?.slice(0,10)||'';
 function format(iso,withTime=true){
   if(!iso)return 'Nicht bekannt';
   if(/^\d{4}-\d\d-\d\d$/.test(iso)){const [y,m,d]=iso.split('-');return `${d}.${m}.${y} (ganztägig)`;}
   const date=new Date(iso);if(Number.isNaN(date.getTime()))return 'Unbekannt';
   return new Intl.DateTimeFormat('de-DE',{timeZone:'Europe/Berlin',day:'2-digit',month:'2-digit',year:'numeric',...(withTime?{hour:'2-digit',minute:'2-digit'}:{})}).format(date);
 }
 function todayBerlin(){return new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Berlin',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());}
 function localEvents(){return [...remoteEvents,...customEvents];}
 function loadCustom(){try{const data=JSON.parse(localStorage.getItem('kl-custom-events')||'[]');customEvents=Array.isArray(data)?data.filter(x=>x.isCustom):[];}catch{customEvents=[];}}
 function storeCustom(){try{localStorage.setItem('kl-custom-events',JSON.stringify(customEvents));}catch{E.alert.textContent='Eigene Termine konnten nicht gespeichert werden (Browserspeicher nicht verfügbar).';E.alert.classList.remove('hidden');}}
 function loadSelection() {
  try {
   const stored=JSON.parse(localStorage.getItem('kl-selected-event-types')||'null');
   if(Array.isArray(stored)) selectedKinds=new Set(stored.filter(id=>TAX.TYPES.some(t=>t.id===id)));
  }catch{}
 }
 function storeSelection(){try{localStorage.setItem('kl-selected-event-types',JSON.stringify([...selectedKinds]));}catch{}}
 function updateChoices(){
  for(const box of E.categoryChoices.querySelectorAll('input[type=checkbox]'))box.checked=selectedKinds.has(box.value);
  E.categorySummary.textContent=`Veranstaltungsarten: ${selectedKinds.size} von ${TAX.TYPES.length} ✓`;
 }
 function changeSelection(values){selectedKinds=new Set(values);storeSelection();updateChoices();applyFilters();}
 function fillLocations(){
  const current=E.location.value;
  const locations=[...new Set(localEvents().map(e=>e.location).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'de'));
  E.location.replaceChildren(node('option',{text:'Alle Orte',value:'all'}),...locations.map(l=>node('option',{text:l,value:l})));
  E.location.value=locations.includes(current)?current:'all';
  const sourceCurrent=E.sourceFilter.value;
  const sources=[...new Set(localEvents().map(e=>e.sourceKey).filter(Boolean))].sort();
  E.sourceFilter.replaceChildren(node('option',{text:'Alle Datenquellen',value:'all'}),
    ...sources.map(k=>node('option',{text:NAMES[k]||k,value:k})));
  E.sourceFilter.value=sources.includes(sourceCurrent)?sourceCurrent:'all';
 }
 function toFCEvent(ev){return {
   id:ev.id,title:ev.title,start:ev.start,end:ev.end||undefined,allDay:ev.allDay,
   backgroundColor:ev.displayColor,borderColor:ev.displayColor,textColor:'#fff',
   classNames:['kl-event-card'],extendedProps:{payload:ev}
 };}
 function applyFilters(){
  const q=E.search.value.trim().toLocaleLowerCase('de');
  filteredEvents=TAX.filter(localEvents(),selectedKinds,ev=>
   (E.location.value==='all'||ev.location===E.location.value)&&
   (E.region.value==='all'||ev.region===E.region.value)&&
   (E.sourceFilter.value==='all'||ev.sourceKey===E.sourceFilter.value)&&
   (!E.kerwe.checked||ev.displayCategory==='kerwe')&&
   (!E.stadium.checked||(ev.displayCategory==='fussball'&&ev.isStadium===true))&&
   (!E.major.checked||ev.isMajor===true)&&
   (!q||[ev.title,ev.description,ev.location,ev.locality,areaName(ev),ev.displayLabel].join(' ').toLocaleLowerCase('de').includes(q))
  );
  if(calendar){calendar.removeAllEvents();calendar.addEventSource(filteredEvents.map(toFCEvent));}
  E.count.textContent=`${filteredEvents.length} von ${localEvents().length} Terminen angezeigt`;
  renderUpcoming();
 }
 function renderUpcoming(){
  const cutoff=todayBerlin();
  const next=filteredEvents.filter(ev=>dateOnly(ev.end||ev.start)>=cutoff&&!['cancelled'].includes(ev.status))
    .sort((a,b)=>a.start.localeCompare(b.start)).slice(0,9);
  E.upcoming.replaceChildren();
  if(!next.length){E.upcoming.append(node('li',{text:'Keine bevorstehenden Termine mit dieser Filterauswahl'}));return;}
  for(const ev of next){
   const regionDot=node('span',{class:'region-dot','data-region':ev.region});regionDot.style.background=regionColor(ev);
   const kindTag=node('span',{class:'upcoming-type',text:`${ev.displayLabel} · ${areaName(ev)} `});kindTag.append(regionDot);
   const li=node('li',{},[
    node('span',{class:'date',text:format(ev.start)}),kindTag,
    node('strong',{text:ev.title}),node('span',{class:'loc',text:ev.location||'Ort nicht angegeben'})
   ]);
   li.style.borderLeft=`4px solid ${ev.displayColor}`;li.style.paddingLeft='9px';li.tabIndex=0;
   li.setAttribute('role','button');li.addEventListener('click',()=>showEvent(ev));
   li.addEventListener('keydown',e=>{if(e.key==='Enter')showEvent(ev);});E.upcoming.append(li);
  }
 }
 function showEvent(ev){E.modalTitle.textContent=ev.title||'Veranstaltung';E.modalBody.replaceChildren();E.modalActions.replaceChildren();const dl=node('dl');const add=(term,value)=>{dl.append(node('dt',{text:term}),node('dd',{text:value??'Nicht bekannt'}));};add('Region / tatsächlicher Ort',areaName(ev));add('Datenquelle',NAMES[ev.sourceKey]||ev.sourceKey||'Eigener Termin');add('Ortsteil',ev.locality||'Nicht angegeben');add('Veranstaltungsart',eventType(ev));add('Beginn',format(ev.start));if(ev.end)add('Ende',ev.allDay?`${dateOnly(window.KLICS.addDays(ev.end,-1))} (einschließlich)` : format(ev.end));add('Ort',ev.location);add('Adresse',ev.address);add('Kalenderfarbe / Art',TAX.decorate(ev).displayLabel);add('Quelle ≠ Veranstaltungsort','Der Datenanbieter bestimmt nicht die Farbe oder Region.');add('Status',({confirmed:'Bestätigt',tentative:'Vorläufig',cancelled:'Abgesagt',postponed:'Verschoben'})[ev.status]||'Nicht bekannt');add('Beschreibung',ev.description);if(ev.stale)add('Datenstand','Quelle beim letzten Abruf nicht erreichbar – möglicherweise veraltet');if(ev.sourceKey==='rlp'||ev.sourceKey==='pfalz'||ev.sourceKey==='ramstein'||ev.sourceKey==='weilerbach')add('Ortszuordnung','Automatisch aus der veröffentlichten Ortsangabe; für Lieferplanung bitte Originalquelle prüfen');if(ev.isStadium)add('Stadionprüfung','Fritz-Walter-Stadion ausdrücklich als Veranstaltungsort ausgewiesen');if(ev.lastChecked)add('Zuletzt geprüft',format(ev.lastChecked));const link=safeUrl(ev.source);if(link){dl.append(node('dt',{text:'Quelle'}));const dd=node('dd');const a=node('a',{text:'Originalveranstaltung öffnen'});a.href=link;a.target='_blank';a.rel='noopener noreferrer';dd.append(a);dl.append(dd);}E.modalBody.append(dl);
  if(ev.isCustom){const edit=node('button',{class:'btn',text:'Bearbeiten'});edit.type='button';edit.addEventListener('click',()=>{closeModal(E.modal);openCustom(ev);});E.modalActions.append(edit);}openModal(E.modal);}
 function openModal(m){m.classList.remove('hidden');m.querySelector('.modal-close')?.focus();}
 function closeModal(m){m.classList.add('hidden');}
 function openCustom(ev=null){E.form.reset();$('custom-modal-title').textContent=ev?'Eigenen Termin bearbeiten':'Eigenen Termin hinzufügen';E.customId.value=ev?.id||'';E.customTitle.value=ev?.title||'';E.customDate.value=dateOnly(ev?.start);E.customTime.value=ev&&!ev.allDay?ev.start.slice(11,16):'';E.customLocation.value=ev?.location||'';E.customRegion.value=ev?.region||'stadt-kl';E.customCategory.value=ev?.category||'kultur';E.customDesc.value=ev?.description||'';E.customDelete.classList.toggle('hidden',!ev);openModal(E.customModal);}
 function saveEvent(e){e.preventDefault();const title=E.customTitle.value.trim(),d=E.customDate.value,t=E.customTime.value;if(!title||!/^\d{4}-\d\d-\d\d$/.test(d))return;const id=E.customId.value||`custom-${crypto.randomUUID?crypto.randomUUID():Date.now()}`;const entry={id,isCustom:true,sourceKey:'custom',title,start:t?`${d}T${t}:00`:d,end:null,allDay:!t,location:E.customLocation.value.trim()||'Eigener Termin',locality:E.customLocation.value.trim(),region:E.customRegion.value,category:E.customCategory.value,description:E.customDesc.value.trim(),eventType: TAX.decorate({title,isCustom:true,category:E.customCategory.value}).displayLabel,status:'confirmed',isStadium:false,isMajor:false};customEvents=customEvents.filter(x=>x.id!==id).concat(entry);storeCustom();closeModal(E.customModal);fillLocations();applyFilters();}
 function renderStatus(data){const sources=data.sourceStatus||{};E.source.replaceChildren();const failures=[];for(const key of ['fck','city','sommerswing','rlp','ramstein','pfalz','weilerbach']){const s=sources[key]||{};const error=s.status!=='ok';if(error)failures.push(NAMES[key]);E.source.append(node('div',{class:`source-row ${error?'error':''}`},[node('span',{class:'source-name',text:NAMES[key]}),node('span',{class:'source-info',text:error?`⚠ ${s.lastSuccess?'Veralteter Stand':'Noch keine bestätigten Daten'}`:`✓ ${s.eventCount??0} Termine`})]));}E.sync.textContent=data.lastSuccessfulSync?`Letzter erfolgreicher Quellabruf: ${format(data.lastSuccessfulSync)}`:'Noch kein erfolgreicher Quellenabruf';E.alert.textContent=failures.length?`Datenwarnung: ${failures.join(', ')} nicht aktuell bestätigt. Ältere Einträge können sichtbar sein.`:'';E.alert.classList.toggle('hidden',!failures.length);}
 async function loadData(){const btn=$('btn-refresh');btn.disabled=true;try{const res=await fetch(`data/events.json?v=${Date.now()}`,{cache:'no-store'});if(!res.ok)throw new Error('HTTP '+res.status);const data=await res.json();if(!Array.isArray(data.events))throw new Error('Ungültiges Datenformat');remoteEvents=data.events.filter(e=>e&&e.id&&e.start);lastData=data;try{localStorage.setItem('kl-last-remote',JSON.stringify(data));}catch{}renderStatus(data);fillLocations();updateLegendCounts();applyFilters();}catch(err){console.error(err);let data=lastData;try{data=data||JSON.parse(localStorage.getItem('kl-last-remote')||'null');}catch{}if(data?.events){remoteEvents=data.events;renderStatus(data);updateLegendCounts();E.alert.textContent='Netzwerkfehler: Zuletzt gespeicherte Kalenderdaten werden angezeigt.';E.alert.classList.remove('hidden');}else{E.sync.textContent='Noch keine Daten vorhanden';E.alert.textContent='Kalenderdaten konnten nicht geladen werden. Prüfe die URL oder die GitHub Action.';E.alert.classList.remove('hidden');}fillLocations();applyFilters();}finally{btn.disabled=false;}}
 function initCalendar(){
  if(!window.FullCalendar){E.calendar.textContent='Kalenderbibliothek konnte nicht geladen werden. Für FullCalendar ist eine Internetverbindung erforderlich.';return;}
  calendar=new FullCalendar.Calendar(E.calendar,{
   initialView:'dayGridMonth',locale:'de',firstDay:1,timeZone:'Europe/Berlin',
   eventContent:info=>{
    const ev=info.event.extendedProps.payload||{};
    const type=node('span',{class:'kl-type-chip',text:ev.displayLabel||eventType(ev)});
    const title=node('span',{class:'kl-event-name',text:info.event.title});
    const region=node('span',{class:'region-dot','data-region':ev.region});
    region.style.background=regionColor(ev);
    return {domNodes:[node('span',{class:'kl-calendar-event'},[type,title,region])]};
   },
   eventDidMount:info=>{
    const ev=info.event.extendedProps.payload||{};
    const color=ev.displayColor||typeColor(ev);
    // Explizite CSS-Variable: FullCalendar-Ansichten überschreiben sonst teils die Eventfarbe.
    info.el.style.setProperty('--kl-event-color',color);
    info.el.style.setProperty('--kl-region-color',regionColor(ev));
    info.el.style.setProperty('border-color',color,'important');
    if(!info.view.type.startsWith('list')){
      info.el.style.setProperty('background-color',color,'important');
      info.el.style.setProperty('color','#fff','important');
    }
    info.el.title=`${ev.displayLabel||eventType(ev)} · ${areaName(ev)} · Quelle: ${NAMES[ev.sourceKey]||ev.sourceKey||'privat'} · ${info.event.title}`;
   },
   headerToolbar:{left:'prev,next today',center:'title',right:''},buttonText:{today:'Heute'},
   height:'auto',dayMaxEvents:5,initialDate:new Date(),
   // FCK und Kerwen sollen bei vollen Tagen vor Kultur und sonstigen Events erscheinen.
   eventOrder:(a,b)=>{
    const rank={fussball:0,kerwe:1,stadtfest:2,konzert:3,sport:4,markt:5,ausstellung:6,museum:7,kultur:8,sonstiges:9};
    const ca=a.extendedProps?.payload?.displayCategory,cb=b.extendedProps?.payload?.displayCategory;
    return (rank[ca]??99)-(rank[cb]??99);
   },eventOrderStrict:true,
   eventClick:info=>{info.jsEvent.preventDefault();showEvent(info.event.extendedProps.payload);}
  });calendar.render();applyFilters();
 }
 function saveICS(){if(!window.KLICS)return;try{const content=window.KLICS.exportEvents(filteredEvents);const url=URL.createObjectURL(new Blob([content],{type:'text/calendar;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='kl-eventradar.ics';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(err){E.alert.textContent=`ICS-Export fehlgeschlagen: ${err.message}`;E.alert.classList.remove('hidden');}}
 E.form.addEventListener('submit',saveEvent);E.customDelete.addEventListener('click',()=>{const id=E.customId.value;if(!id||!confirm('Eigenen Termin wirklich löschen?'))return;customEvents=customEvents.filter(e=>e.id!==id);storeCustom();closeModal(E.customModal);fillLocations();applyFilters();});$('btn-add-custom').addEventListener('click',()=>openCustom());$('btn-export-ics').addEventListener('click',saveICS);$('btn-refresh').addEventListener('click',loadData);
 for(const id of ['search-input','filter-source','filter-region','filter-location','filter-major'])
  $(id).addEventListener(id==='search-input'?'input':'change',applyFilters);
 E.kerwe.addEventListener('change',()=>{
  if(E.kerwe.checked && !selectedKinds.has('kerwe')){
   selectedKinds.add('kerwe');storeSelection();updateChoices();
  }
  applyFilters();
 });
 E.stadium.addEventListener('change',()=>{
  if(E.stadium.checked && !selectedKinds.has('fussball')){
   selectedKinds.add('fussball');storeSelection();updateChoices();
  }
  applyFilters();
 });
 document.querySelectorAll('.view-switch button').forEach(btn=>btn.addEventListener('click',()=>{if(!calendar)return;calendar.changeView(btn.dataset.view);document.querySelectorAll('.view-switch button').forEach(b=>{b.classList.toggle('active',b===btn);b.classList.toggle('btn-outline',b!==btn);});}));
 document.querySelectorAll('.modal-close').forEach(btn=>btn.addEventListener('click',()=>closeModal(btn.closest('.modal'))));document.querySelectorAll('.modal').forEach(m=>m.addEventListener('click',e=>{if(e.target===m)closeModal(m);}));document.addEventListener('keydown',e=>{if(e.key==='Escape')document.querySelectorAll('.modal:not(.hidden)').forEach(closeModal);});
 function updateLegendCounts(){const total=localEvents();for(const line of E.legend.children){const id=line.dataset.region;const number=total.filter(ev=>ev.region===id).length;const count=line.querySelector('.legend-count');if(count)count.textContent=`${number} erfasst`;}}
 for(const type of TAX.TYPES){
  const line=node('div',{class:'type-legend-item'},[node('span',{class:'legend-swatch'}),node('span',{text:type.name})]);
  line.querySelector('.legend-swatch').style.background=type.color;E.typeLegend.append(line);
 }
 for(const type of TAX.TYPES){
  const label=node('label',{class:'category-check'});
  const check=node('input',{type:'checkbox',value:type.id});check.value=type.id;check.checked=selectedKinds.has(type.id);
  const dot=node('span',{class:'legend-swatch'});dot.style.background=type.color;
  label.append(check,dot,node('span',{text:type.name}));E.categoryChoices.append(label);
  check.addEventListener('change',()=>{if(check.checked)selectedKinds.add(type.id);else selectedKinds.delete(type.id);storeSelection();updateChoices();applyFilters();});
 }
 $('categories-all').addEventListener('click',()=>changeSelection(TAX.TYPES.map(t=>t.id)));
 $('categories-none').addEventListener('click',()=>changeSelection([]));
 $('categories-relevant').addEventListener('click',()=>changeSelection(DEFAULT_SELECTED));
 loadSelection();updateChoices();
 for(const [id,[name,color]] of Object.entries(REGIONS)){
   const line=node('div',{class:'region-legend-item'},[node('span',{class:'legend-swatch'}),node('span',{text:name}),node('span',{class:'legend-count',text:'–'})]);line.dataset.region=id;
   line.querySelector('.legend-swatch').style.background=color;E.legend.append(line);
 }
 loadCustom();initCalendar();loadData();
})();

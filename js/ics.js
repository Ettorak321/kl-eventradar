/* ICS-Export als testbares, browser- und Node-kompatibles Modul. */
(function(root,factory){ const api=factory(); if(typeof module==='object'&&module.exports) module.exports=api; if(root) root.KLICS=api; })(typeof window!=='undefined'?window:undefined, function(){
 'use strict';
 const zone='Europe/Berlin';
 const pad=n=>String(n).padStart(2,'0');
 const esc=s=>String(s||'').replace(/\\/g,'\\\\').replace(/\r?\n/g,'\\n').replace(/,/g,'\\,').replace(/;/g,'\\;');
 const ymd=s=>String(s).slice(0,10).replace(/-/g,'');
 function addDays(iso,days){const d=new Date(`${iso.slice(0,10)}T12:00:00Z`);d.setUTCDate(d.getUTCDate()+days);return d.toISOString().slice(0,10);}
 // Naive lokale Zeiten sind nur bei selbst angelegten Ereignissen zulässig.
 // Iteration löst den Berlin-Offset unabhängig von der Browser-Zeitzone auf.
 function berlinLocalToUTC(iso){
   const [y,m,d,h='00',min='00',s='00']=iso.match(/\d+/g).map(Number);
   const wanted=Date.UTC(y,m-1,d,h,min,s);
   let epoch=wanted;
   const dtf=new Intl.DateTimeFormat('en-GB',{timeZone:zone,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'});
   for(let i=0;i<4;i++){
     const obj=Object.fromEntries(dtf.formatToParts(new Date(epoch)).filter(x=>x.type!=='literal').map(x=>[x.type,+x.value]));
     const local=Date.UTC(obj.year,obj.month-1,obj.day,obj.hour,obj.minute,obj.second);
     const next=epoch+wanted-local;
     if(next===epoch)break;
     epoch=next;
   }
   return new Date(epoch);
 }
 function asUTC(iso){
   if(/(?:Z|[+-]\d\d:\d\d)$/i.test(iso)) return new Date(iso);
   return berlinLocalToUTC(iso);
 }
 function utcICS(iso){const d=asUTC(iso);if(Number.isNaN(d.getTime()))throw new Error('Ungültiges Datum: '+iso);return `${d.getUTCFullYear()}${pad(d.getUTCMonth()+1)}${pad(d.getUTCDate())}T${pad(d.getUTCHours())}${pad(d.getUTCMinutes())}${pad(d.getUTCSeconds())}Z`;}
 function fold(line){
   const encoder=typeof TextEncoder!=='undefined'?new TextEncoder():null;
   let out='',width=0;
   for(const cp of line){const count=encoder?encoder.encode(cp).length:Buffer.byteLength(cp,'utf8');if(width+count>75){out+='\r\n ';width=1;}out+=cp;width+=count;}
   return out;
 }
 function exportEvents(events, generated=new Date()){
   const lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//KL EventRadar//DE','CALSCALE:GREGORIAN','METHOD:PUBLISH'];
   for(const ev of events){
     if(!ev.start)continue;
     const allDay=ev.allDay===true||/^\d{4}-\d\d-\d\d$/.test(ev.start);
     lines.push('BEGIN:VEVENT',`UID:${String(ev.id||'unknown').replace(/[^A-Za-z0-9_-]/g,'_')}@kl-eventradar`,`DTSTAMP:${utcICS(generated.toISOString())}`,`SUMMARY:${esc(ev.title)}`,`DESCRIPTION:${esc(ev.description)}`,`LOCATION:${esc(ev.location)}`);
     if(allDay){
       lines.push(`DTSTART;VALUE=DATE:${ymd(ev.start)}`);
       // end ist bereits exklusiv; fehlt es, handelt es sich um einen einzelnen Tag.
       const exclusive=(ev.end&&/^\d{4}-\d\d-\d\d$/.test(ev.end))?ev.end:addDays(ev.start,1);
       lines.push(`DTEND;VALUE=DATE:${ymd(exclusive)}`);
     }else{
       lines.push(`DTSTART:${utcICS(ev.start)}`);
       if(ev.end)lines.push(`DTEND:${utcICS(ev.end)}`);
     }
     if(ev.status==='cancelled')lines.push('STATUS:CANCELLED');
     else if(ev.status==='tentative')lines.push('STATUS:TENTATIVE');
     if(ev.source&&/^https?:\/\//i.test(ev.source)) lines.push(`URL:${esc(ev.source)}`);
     lines.push('END:VEVENT');
   }
   lines.push('END:VCALENDAR');return lines.map(fold).join('\r\n')+'\r\n';
 }
 return {exportEvents,utcICS,berlinLocalToUTC,addDays,esc};
});

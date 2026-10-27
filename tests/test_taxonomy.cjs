const test = require('node:test');
const assert = require('node:assert/strict');
const T=require('../js/taxonomy.js');
function ev(title, props={}) {return {title,sourceKey:'city',region:'stadt-kl',isStadium:false,...props};}
test('verified FCK home game is red category, venue not source city',()=>{
 const result=T.decorate(ev('1. FC Kaiserslautern – Hertha BSC',{sourceKey:'fck',isStadium:true,venueVerified:true}));
 assert.equal(result.displayCategory,'fussball');assert.equal(result.displayColor,'#c62828');
 assert.equal(T.classify(ev('FCK – Hertha',{sourceKey:'fck',isStadium:true,venueVerified:false})),'sonstiges');
});
test('Kerwe classified from event title independently of region',()=>{
 const result=T.decorate(ev('Kerwe in Rodenbach',{region:'vg-weilerbach',category:'stadtfest',eventType:'Fest'}));
 assert.equal(result.displayCategory,'kerwe');assert.equal(result.displayColor,'#e97827');
});
test('museum culture exhibition excluded by default but can be included',()=>{
 const items=[ev('Kerwe in Weilerbach'),ev('Ausstellung Moderne Kunst'),ev('Museumsführung'),ev('Theateraufführung')];
 assert.deepEqual(T.filter(items,T.defaultSelected()).map(e=>e.title),['Kerwe in Weilerbach']);
 assert.equal(T.filter(items,['museum','ausstellung','kultur']).length,3);
});
test('simultaneous multiselection shows different event types',()=>{
 const items=[ev('Kerwe'),ev('Konzert'),ev('Ausstellung im Museum'),ev('Weinfest')];
 assert.equal(T.filter(items,['kerwe','konzert','stadtfest']).length,3);
 assert.equal(T.filter(items,[]).length,0);
});
test('all event types are distinct and presets omit low-priority culture',()=>{
 assert.equal(new Set(T.TYPES.map(t=>t.id)).size,T.TYPES.length);
 for (const id of ['ausstellung','museum','kultur','sonstiges']) assert.ok(!T.defaultSelected().includes(id));
});

test('manual category survives generic title and cannot impersonate FCK stadium',()=>{
 assert.equal(T.classify(ev('Interner Termin',{isCustom:true,category:'kerwe'})),'kerwe');
 assert.equal(T.classify(ev('Privates Fußballspiel',{isCustom:true,category:'fussball'})),'sport');
});

const test=require('node:test'),assert=require('node:assert/strict');
const T=require('../js/taxonomy.js');
test('Museumsreihen vom geprüften Datenabgleich werden als Ausstellungen sichtbar',()=>{
 const ev=T.decorate({title:'Hans Purrmann als Sammler',sourceKey:'city',category:'ausstellung',
  location:'mpk - Museum Pfalzgalerie Kaiserslautern',exhibitionSeries:true});
 assert.equal(ev.displayCategory,'ausstellung');
 assert.equal(ev.displayColor,'#956db9');
 assert.ok(!T.defaultSelected().includes('ausstellung'));
 assert.equal(T.filter([ev],['ausstellung']).length,1);
});
test('Einzelausstellung ohne Nachweis und andere Quellen behalten bisherige Klassifikation',()=>{
 assert.equal(T.classify({title:'Hans Purrmann als Sammler',sourceKey:'city',
  category:'sonstiges'}),'sonstiges');
 assert.equal(T.classify({title:'Familienführung',sourceKey:'city',
  category:'ausstellung',exhibitionSeries:false}),'sonstiges');
 assert.equal(T.classify({title:'Hans Purrmann als Sammler',sourceKey:'rlp',
  category:'ausstellung',exhibitionSeries:true}),'sonstiges');
});

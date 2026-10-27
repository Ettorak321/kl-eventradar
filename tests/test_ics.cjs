const test=require('node:test');const assert=require('node:assert/strict');
const {exportEvents,utcICS,addDays}=require('../js/ics.js');
test('Berlin summer and winter offsets become correct UTC values',()=>{
 assert.equal(utcICS('2026-07-08T19:00:00+02:00'),'20260708T170000Z');
 assert.equal(utcICS('2026-11-08T13:30:00+01:00'),'20261108T123000Z');
});
test('floating Berlin time stays correct when executed in different browser timezone',()=>{
 assert.equal(utcICS('2026-07-08T19:00:00'),'20260708T170000Z');
});
test('single and multiple full days use exclusive end',()=>{
 const ics=exportEvents([{id:'one',title:'Eintag',start:'2026-10-22',allDay:true},{id:'range',title:'Mehrtag',start:'2026-10-22',end:'2026-10-26',allDay:true}]);
 assert.match(ics,/DTSTART;VALUE=DATE:20261022\r\nDTEND;VALUE=DATE:20261023/);
 assert.match(ics,/DTSTART;VALUE=DATE:20261022\r\nDTEND;VALUE=DATE:20261026/);
});
test('ICS escaping, line endings and cancellation',()=>{
 const ics=exportEvents([{id:'evt1',title:'A,B;C\\D',description:'erste\nzweite',start:'2026-11-08T13:30:00+01:00',status:'cancelled'}]);
 assert.match(ics,/SUMMARY:A\\,B\\;C\\\\D/);
 assert.match(ics,/DESCRIPTION:erste\\nzweite/);
 assert.match(ics,/DTSTART:20261108T123000Z/);
 assert.match(ics,/STATUS:CANCELLED/);
 assert.ok(ics.endsWith('\r\n'));
});
test('long Unicode content folded by octets',()=>{
 const ics=exportEvents([{id:'x',title:'Ä'.repeat(120),start:'2026-11-08',allDay:true}]);
 for(const line of ics.trim().split('\r\n'))assert.ok(Buffer.byteLength(line,'utf8')<=75);
});

// Bei GitHub Actions läuft diese Datei als Einstiegspunkt: V5-Regressionen mit ausführen.
require('./test_taxonomy.cjs');

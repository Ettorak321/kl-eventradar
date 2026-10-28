const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const read=p=>fs.readFileSync(path.join(__dirname,'..',p),'utf8');
test('Feiertage bleiben auch bei Regionseinschränkungen sichtbar',()=>{
 const app=read('js/app.js');const tax=read('js/taxonomy.js');
 assert.match(app,/ev\.isAnnualDay===true/);
 assert.match(app,/ev\.isPublicHoliday\?'Gesetzlicher Feiertag/);
 assert.match(tax,/s === 'calendar_days'/);
});
test('öffentliche Oberfläche ohne gewerbliche Zwecke',()=>{
 const html=read('index.html');
 assert.match(html,/Feiertage/);
 assert.doesNotMatch(html,/getränkeabsatz|disposition|umsatzstark|umsatzprognose/i);
});

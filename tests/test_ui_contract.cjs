const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const read=x=>fs.readFileSync(path.join(__dirname,'..',x),'utf8');
test('öffentliche Oberfläche neutral',()=>{for(const f of ['index.html','README.md','TESTBERICHT.md','AENDERUNGEN_V6.md'])assert.doesNotMatch(read(f),/getränke?(?:großhandel|absatz|disposition)|absatzprognose|lieferplanung|dispositionsentscheidung/i,f)});
test('Vorläufigkeitskennzeichnung und Filter vorhanden',()=>{assert.match(read('index.html'),/id="filter-forecast"/);assert.match(read('index.html'),/Nur Kerwe-Prognosen/);assert.match(read('js/app.js'),/forecastEvidence/);assert.match(read('css/style.css'),/kl-forecast/)});

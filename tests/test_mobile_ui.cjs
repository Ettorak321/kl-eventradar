const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const UI=require('../js/mobile_ui.js');
const read=p=>fs.readFileSync(path.join(__dirname,'..',p),'utf8');
test('jedes Veranstaltungsthema bekommt ein eigenes erkennbares Symbol',()=>{
  const keys=['fussball','fck_auswaerts','kerwe','stadtfest','konzert','sport','markt','feiertag','anlass','ausstellung','museum','kultur','sonstiges'];
  keys.forEach(k=>assert.ok(UI.iconFor({displayCategory:k}).length>0,k));
  assert.notEqual(UI.iconFor({displayCategory:'fussball'}),UI.iconFor({displayCategory:'fck_auswaerts'}));
  assert.equal(UI.iconFor({displayCategory:'markt',title:'Lautrer Weihnachtsmarkt'}),'🎄');
});
test('Serien behalten kurzen Namen statt eines unverständlichen Icons',()=>{
  assert.equal(UI.shortLabel({isSeries:true,title:'Lautrer Weihnachtsmarkt',category:'markt'}),'Weihnachtsmarkt');
  assert.equal(UI.shortLabel({isSeries:true,title:'Kulturmarkt',category:'markt'}),'Kulturmarkt');
  assert.ok(UI.shortLabel({isSeries:true,title:'Hans Purrmann als Sammler und weitere Sonderausstellungen'}).length<=24);
  assert.equal(UI.shortLabel({category:'fck_auswaerts'}),'FCK Ausw.');
});
test('mobil ist die kompakte Ansicht standardmäßig an, aber abschaltbar',()=>{
  class FakeNode{
    constructor(){this.attrs={};this.handlers={};this.textContent='';this.states=new Set();
      this.classList={toggle:(key,on)=>{if(on)this.states.add(key);else this.states.delete(key);}};}
    setAttribute(k,v){this.attrs[k]=v;}
    addEventListener(k,fn){this.handlers[k]=fn;}
    click(){this.handlers.click();}
  }
  const btn=new FakeNode(),root=new FakeNode();
  const doc={documentElement:root,getElementById:id=>id==='btn-mobile-density'?btn:null};
  const values=new Map(),store={getItem:k=>values.get(k)||null,setItem:(k,v)=>values.set(k,v)};
  UI.initToggle(doc,store);
  assert.equal(btn.attrs['aria-pressed'],'true');
  assert.equal(root.states.has('kl-mobile-standard'),false);
  btn.click();
  assert.equal(btn.attrs['aria-pressed'],'false');
  assert.equal(root.states.has('kl-mobile-standard'),true);
  assert.equal(values.get(UI.KEY),'off');
  UI.initToggle(doc,store);
  assert.equal(btn.attrs['aria-pressed'],'false');
});
test('Tab-Icon, iPhone-Icon, Android-Manifest und mobile Darstellung sind eingebunden',()=>{
  const html=read('index.html'),app=read('js/app.js'),css=read('css/style.css');
  for(const file of ['favicon.svg','favicon-32.png','apple-touch-icon.png',,'site.webmanifest'])
    assert.ok(fs.existsSync(path.join(__dirname,'..',file)),file);
  assert.match(html,/rel="icon"/);assert.match(html,/rel="apple-touch-icon"/);
  assert.match(html,/rel="manifest"/);assert.match(html,/src="js\/mobile_ui\.js"/);
  assert.match(html,/id="btn-mobile-density"/);
  assert.match(app,/MOBILE\.iconFor\(ev\)/);assert.match(app,/MOBILE\.shortLabel\(ev\)/);
  assert.match(app,/eventClick:info=>/);
  assert.match(css,/@media\(max-width:460px\)/);
  const manifest=JSON.parse(read('site.webmanifest'));
  assert.equal(manifest.name,'KL EventRadar');
  assert.equal(manifest.start_url,'./');
});

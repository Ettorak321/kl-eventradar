const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const B=require('../js/brightness.js');
const read=name=>fs.readFileSync(path.join(__dirname,'..',name),'utf8');

test('die bisherige Standard-Helligkeit ist 100 Prozent',()=>{
  assert.equal(B.DEFAULT,100);
  assert.deepEqual(B.LEVELS,[70,85,100,115,130]);
  assert.equal(B.normalize(null),100);
  assert.equal(B.normalize('kaputt'),100);
  assert.equal(B.normalize('999'),100);
  assert.equal(B.description(100),'100 % · Standard');
});

test('hellere und dunklere Einstellungen werden korrekt bezeichnet',()=>{
  assert.match(B.description(70),/Dunkler/);
  assert.match(B.description(130),/Heller/);
});

test('Button, Regler, Reset und persistente Einstellung sind vorhanden',()=>{
  const html=read('index.html'),css=read('css/style.css'),js=read('js/brightness.js');
  for(const id of ['btn-brightness','brightness-panel','brightness-range','brightness-value','brightness-reset'])
    assert.match(html,new RegExp('id="'+id+'"'));
  assert.match(html,/src="js\/brightness\.js"/);
  assert.match(css,/data-kl-brightness="70"/);
  assert.match(css,/data-kl-brightness="130"/);
  assert.match(js,/store\.setItem\(KEY/);
  assert.match(js,/store\.removeItem\(KEY/);
});

test('Interaktion, Wiederherstellen, Speicherung und Escape funktionieren',()=>{
  class Element{
    constructor(){this.value='100';this.textContent='';this.attributes={};this.handlers={};this.focused=false;
      this.classList={set:new Set(['hidden']),contains:x=>this.classList.set.has(x),add:x=>this.classList.set.add(x),remove:x=>this.classList.set.delete(x)};
    }
    addEventListener(k,fn){this.handlers[k]=fn;}
    setAttribute(k,v){this.attributes[k]=v;}
    removeAttribute(k){delete this.attributes[k];}
    contains(target){return target===this;}
    focus(){this.focused=true;}
    dispatch(event,details={}){if(this.handlers[event])this.handlers[event](details);}
  }
  const els=Object.fromEntries(['btn-brightness','brightness-panel','brightness-range','brightness-value','brightness-reset','brightness-control'].map(id=>[id,new Element()]));
  const doc={handlers:{},documentElement:new Element(),getElementById:id=>els[id],addEventListener(k,fn){this.handlers[k]=fn;}};
  const values=new Map([['kl-eventradar-brightness','115']]);
  const store={getItem:k=>values.get(k)||null,setItem:(k,v)=>values.set(k,v),removeItem:k=>values.delete(k)};
  B.init(doc,store);
  assert.equal(doc.documentElement.attributes['data-kl-brightness'],'115');
  assert.equal(els['brightness-range'].value,'115');
  els['btn-brightness'].dispatch('click');
  assert.equal(els['btn-brightness'].attributes['aria-expanded'],'true');
  els['brightness-range'].value='70';
  els['brightness-range'].dispatch('input');
  assert.equal(doc.documentElement.attributes['data-kl-brightness'],'70');
  assert.equal(values.get(B.KEY),'70');
  els['brightness-reset'].dispatch('click');
  assert.equal(doc.documentElement.attributes['data-kl-brightness'],undefined);
  assert.equal(els['brightness-range'].value,'100');
  assert.equal(values.has(B.KEY),false);
  doc.handlers.keydown({key:'Escape'});
  assert.equal(els['btn-brightness'].attributes['aria-expanded'],'false');
  assert.equal(els['btn-brightness'].focused,true);
});

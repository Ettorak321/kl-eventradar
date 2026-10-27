/* KL EventRadar V5: Quelle, Region und Veranstaltungstyp bewusst getrennt. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.KLTypes = api;
})(typeof window !== 'undefined' ? window : globalThis, function () {
  'use strict';
  const TYPES = [
    {id:'fussball',name:'FCK-Heimspiele',color:'#c62828',defaultOn:true},
    {id:'fck_auswaerts',name:'FCK-Auswärtsspiele',color:'#d68846',defaultOn:true},
    {id:'kerwe',name:'Kerwen / Kirmes',color:'#e97827',defaultOn:true},
    {id:'stadtfest',name:'Stadt- / Vereinsfeste',color:'#e0a21f',defaultOn:true},
    {id:'konzert',name:'Konzerte / Musik',color:'#287bd1',defaultOn:true},
    {id:'sport',name:'Sonstige Sportevents',color:'#12a4aa',defaultOn:true},
    {id:'markt',name:'Märkte / Messen',color:'#26845f',defaultOn:true},
    {id:'ausstellung',name:'Ausstellungen',color:'#956db9',defaultOn:false},
    {id:'museum',name:'Museen / Führungen',color:'#8174a0',defaultOn:false},
    {id:'kultur',name:'Kultur / Theater',color:'#7662a9',defaultOn:false},
    {id:'sonstiges',name:'Sonstiges',color:'#697586',defaultOn:false},
  ];
  const find = (key) => TYPES.find(x => x.id === key);
  const defaultSelected = () => TYPES.filter(x => x.defaultOn).map(x=>x.id);
  function classify(ev) {
    const t = String(ev?.title || '').toLocaleLowerCase('de');
    const s = String(ev?.sourceKey || '');
    if (s === 'fck' && ev?.isAway === true && ev?.isStadium !== true) return 'fck_auswaerts';
    if (s === 'fck' && ev?.isStadium === true && ev?.venueVerified === true) return 'fussball';
    if (/kerwe|kerb\b|kirchweih|kirmes/i.test(t)) return 'kerwe';
    // Eigene manuell eingetragene Termine respektieren die bewusste Typauswahl.
    if (ev?.isCustom === true) {
      if (ev.category === 'fussball') return 'sport'; // kein verifiziertes FCK-Spiel
      if (find(ev.category)) return ev.category;
    }
    if (/ausstellung|vernissage|kunstausstellung|fotoausstellung|exposition/i.test(t)) return 'ausstellung';
    if (/museum|museumsnacht|museumsführung/i.test(t)) return 'museum';
    if (/sportfest|fußball|fussball|turnier|laufveranstaltung|marathon|radrennen|handball|volleyball|basketball|leichtathletik/i.test(t)) return 'sport';
    if (/konzert|musik|sommerswing|jazz|blues|livemusik|live-musik|bandabend|rocknacht|open.air/i.test(t)) return 'konzert';
    if (/\b(?:weihnachtsmarkt|flohmarkt|wochenmarkt|jahrmarkt|bauernmarkt|kunsthandwerkermarkt|markt|messe|basar)\b/i.test(t)) return 'markt';
    if (/stadtfest|altstadtfest|dorffest|straßenfest|strassenfest|vereinsfest|feuerwehrfest|sommerfest|volksfest|weinfest|bierfest|oktoberfest|brunnenfest|bürgerfest|buergerfest|festwochen|festumzug/i.test(t)) return 'stadtfest';
    if (/theater|kabarett|lesung|vortrag|oper\b|ballett|tanztheater|kultur|kunstführung|bühne|schauspiel/i.test(t)) return 'kultur';
    return 'sonstiges';
  }
  function decorate(event) {
    const kind = classify(event);
    const type = find(kind);
    return { ...event, displayCategory:kind, displayLabel:type.name, displayColor:type.color };
  }
  function filter(events, selected, predicate = () => true) {
    const set = new Set(selected);
    return events.map(decorate).filter(ev => set.has(ev.displayCategory) && predicate(ev));
  }
  return {TYPES,defaultSelected,classify,decorate,filter};
});

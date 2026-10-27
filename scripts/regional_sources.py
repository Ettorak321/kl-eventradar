"""Zusätzliche Regionalquellen. Nicht-erkennbare Strukturen lösen SourceError aus.
Nur belegte Einzeltermine, keine Schätzung der üblichen jährlichen Kerwen.
"""
from __future__ import annotations
import json
import re
from datetime import date, datetime, timedelta
from urllib.parse import urljoin
from bs4 import BeautifulSoup
try:
    from .event_taxonomy import LABELS, classify_event
    from .regions import REGIONS, classify_region
except ImportError:  # Start via python scripts/fetch_events.py
    from event_taxonomy import LABELS, classify_event
    from regions import REGIONS, classify_region

OPEN_RLP = 'https://open-rlp.egovernor.de/metaData/event/data'
RAMSTEIN = 'https://www.ramstein-miesenbach.de/de/kultur-freizeit/veranstaltungskalender/'
PFALZ = 'https://www.pfalz.de/de/veranstaltungen-im-landkreis-kaiserslautern'

MONTHS = {n.lower(): i for i,n in enumerate(['Januar','Februar','März','April','Mai','Juni','Juli','August','September','Oktober','November','Dezember'],1)}


def parse_start(value, tz):
    if not isinstance(value,str):return None
    # Datumsangaben mit Offset beibehalten, naive Zeit als Europe/Berlin interpretieren.
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        try:return date.fromisoformat(value).isoformat(), True
        except ValueError:return None
    try:
        d = datetime.fromisoformat(value.replace('Z','+00:00'))
        if d.tzinfo is None:d=d.replace(tzinfo=tz)
        return d.astimezone(tz).isoformat(timespec='seconds'),False
    except ValueError:pass
    try:return date.fromisoformat(value[:10]).isoformat(),True
    except ValueError:return None


def parse_rlp_json(payload, tz, make_id, stamp, category, status_from):
    """rlpDirekt OpenData EventJSON: Liste oder gebündelte Datenfelder.

    Nur Daten mit gültigem Beginn und eindeutigem Landkreis-Ort. Die API darf
    auch andere Kreisverwaltungen enthalten, diese werden verworfen.
    """
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        items = next((payload[k] for k in ('events','data','results','items') if isinstance(payload.get(k),list)),None)
    else:items=None
    if items is None:raise ValueError('EventJSON: kein bekanntes Listenformat')
    out=[]
    for ev in items:
        if not isinstance(ev,dict):continue
        title=str(ev.get('name') or ev.get('title') or '').strip()
        if len(title)<3:continue
        loc=ev.get('location') or ev.get('place') or ''
        if isinstance(loc,dict):
            parts=[loc.get('name'),loc.get('address'),loc.get('city')]
            if isinstance(loc.get('address'),dict):
                parts=[loc.get('name'),loc['address'].get('addressLocality'),loc['address'].get('streetAddress')]
            loc=' '.join(str(x) for x in parts if isinstance(x,str))
        if not isinstance(loc,str):continue
        # Eine Anreise nach Kaiserslautern ist kein dort stattfindendes Event.
        if re.search(r'\b(?:abfahrt|busfahrt|theaterfahrt|tagesfahrt)\b',loc,re.I):
            continue
        region,locality=classify_region(loc)
        if not region:continue
        start_info=parse_start(ev.get('startDate') or ev.get('start'),tz)
        if start_info is None:continue
        start,all_day=start_info
        end_info=parse_start(ev.get('endDate') or ev.get('end'),tz)
        end=end_info[0] if end_info else None
        if end and end<=start:end=None
        link=ev.get('url') or ev.get('link') or OPEN_RLP
        if not isinstance(link,str) or not link.startswith(('https://','http://')):link=OPEN_RLP
        identifier=str(ev.get('id') or ev.get('uid') or f'{title}|{start}|{loc}')
        typ=category(title)
        out.append(dict(id=make_id('rlp',identifier),sourceKey='rlp',title=title,
            start=start,end=end,allDay=all_day,location=loc[:180],locality=locality,region=region,
            category=typ,eventType=event_type(title,typ),description=str(ev.get('description') or '')[:650],
            organizer='',source=link,status=status_from(title),isStadium=False,
            isMajor=typ=='stadtfest',lastChecked=stamp()))
    return out


def event_type(title, category):
    """Beschriftung der Veranstaltung statt Herkunftsfarbe."""
    kind = classify_event(title)
    return LABELS[kind]

def parse_ramstein_html(text, tz, make_id, stamp, category, status_from):
    """Konservative HTML-Tabellenparser-Variante. Erkennt Tabellen mit
    Monatsüberschrift und drei Spalten: Datum, Uhrzeit, Veranstaltung.
    Falls kein passendes HTML-Tabellenlayout vorliegt: Fehler statt Fantasiedaten.
    """
    soup=BeautifulSoup(text,'html.parser')
    results=[]
    # Datumszeilen können auch nach Monatsüberschriften in Tabellen liegen.
    current_month=None
    current_year=None
    for element in soup.find_all(['h2','h3','h4','tr']):
        if element.name.startswith('h'):
            t=element.get_text(' ',strip=True)
            m=re.fullmatch(r'(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+(20\d{2})',t,re.I)
            if m:current_month,current_year=MONTHS[m.group(1).lower()],int(m.group(2))
            continue
        cells=[td.get_text(' ',strip=True) for td in element.find_all(['td','th'],recursive=False)]
        if len(cells)<2:continue
        # `Mi. 21.10.` / `21.10.`; optional Zeitspalte.
        rng=re.search(r'(?<!\d)(\d{1,2})\s*\.\s*[-–]\s*(\d{1,2})\.(\d{1,2})\.',cells[0])
        m=re.search(r'(?<!\d)(\d{1,2})\.(\d{1,2})\.(?!\d)',cells[0]) if not rng else None
        if not rng and not m:continue
        if rng:
            day,lastday,month=map(int,rng.groups())
        else:
            day,month=map(int,m.groups());lastday=None
        if not current_year:continue
        if current_month and abs(current_month-month)>1 and not (current_month==1 and month==12):continue
        try:
            when=date(current_year,month,day)
            exclusive=(date(current_year,month,lastday)+timedelta(days=1)).isoformat() if lastday else None
        except ValueError:continue
        desc=' '.join(cells[2:]).strip() if len(cells)>=3 else cells[1].strip()
        if len(desc)<5:continue
        # Ramsteiner Quelle enthält auch Veranstaltungen in Landstuhl; nicht ungeprüft Ramstein zuordnen.
        region,locality=classify_region(desc)
        if region is None:
            # Gemeinden der Webseite: bei unbekanntem Ort NICHT in VG hineinraten.
            continue
        times=cells[1] if len(cells)>=3 else ''
        tm=re.search(r'(\d{1,2})(?:[.:](\d{2}))?\s*Uhr',times,re.I)
        if tm and not lastday:
            start=datetime(when.year,when.month,when.day,int(tm.group(1)),int(tm.group(2) or 0),tzinfo=tz).isoformat(timespec='seconds')
            allday=False
        else:start=when.isoformat();allday=True
        typ=category(desc)
        results.append(dict(id=make_id('ramstein',f'{when}|{desc}'),sourceKey='ramstein',title=desc[:200],
            start=start,end=exclusive,allDay=allday,location=locality,locality=locality,region=region,
            category=typ,eventType=event_type(desc,typ),description='',organizer='',source=RAMSTEIN,
            status=status_from(desc),isStadium=False,isMajor=typ=='stadtfest',lastChecked=stamp()))
    return results


def parse_pfalz_jsonld(html_text, tz, make_id, stamp, category, status_from, base=PFALZ):
    """Zusätzlicher Kreis-Kalender: ausschließlich explizite schema.org/Event-Daten.
    Keine aus dem Layout geschätzten Datumsangaben.
    """
    soup=BeautifulSoup(html_text,'html.parser');events=[]
    def walk(obj):
        if isinstance(obj,list):
            for x in obj:yield from walk(x)
        elif isinstance(obj,dict):
            tp=obj.get('@type')
            if tp=='Event' or (isinstance(tp,list) and 'Event' in tp):yield obj
            for v in obj.values():
                if isinstance(v,(dict,list)):yield from walk(v)
    for node in soup.select('script[type="application/ld+json"]'):
        try:raw=json.loads(node.string or node.get_text())
        except (ValueError,TypeError):continue
        for obj in walk(raw):
            where=obj.get('location') or {}
            if isinstance(where,dict):
                address=where.get('address') or {}
                town=address.get('addressLocality','') if isinstance(address,dict) else str(address)
                place=' '.join([str(where.get('name') or ''),str(town)])
            else:place=str(where)
            region,locality=classify_region(place)
            if not region:continue
            title=str(obj.get('name') or '').strip()
            if len(title)<3:continue
            start_info=parse_start(obj.get('startDate'),tz)
            if not start_info:continue
            start,all_day=start_info
            end_info=parse_start(obj.get('endDate'),tz)
            typ=category(title)
            events.append(dict(id=make_id('pfalz',str(obj.get('url') or f'{title}|{start}|{place}')),
                sourceKey='pfalz',title=title,start=start,end=end_info[0] if end_info else None,allDay=all_day,
                location=place.strip(),locality=locality,region=region,category=typ,eventType=event_type(title,typ),
                description=str(obj.get('description') or '')[:650],organizer='',source=str(obj.get('url') or base),
                status=status_from(title),isStadium=False,isMajor=typ=='stadtfest',lastChecked=stamp()))
    return events

WITTICH_ROOT = 'https://ol.wittich.de'
WITTICH_EDITION = 'https://ol.wittich.de/titel/798/ausgabe/{week}/{year}/rubrik/alle/seite/0/sortiert/inhaltsverzeichnis'

def weilerbach_article_links(index_html,base):
    """Kandidaten nur bei ausdrücklichem Veranstaltungskalender-Titel."""
    soup=BeautifulSoup(index_html,'html.parser')
    links=[]
    for a in soup.select('a[href*="/artikel/"]'):
        # Titel oft direkt im Anker oder in umgebender Kartenkachel.
        anchor_text=a.get_text(' ',strip=True)
        parent_text=a.parent.get_text(' ',strip=True)[:230] if a.parent else ''
        if 'veranstaltungskalender verbandsgemeinde weilerbach' not in (anchor_text+' '+parent_text).casefold():
            continue
        url=urljoin(base,a.get('href',''))
        if url.startswith('https://ol.wittich.de/titel/798/') and url not in links:
            links.append(url)
    return links


def parse_weilerbach_article(html_text, article_url, tz, make_id, stamp, category, status_from):
    """Wittich-Veranstaltungskalender: ausschließlich Zeilen mit Datum und Ort.
    Beispiel: '25. – 28.09.' | '18.00 Uhr' | 'Kerwe in Weilerbach' | ...
    """
    yearmatch=re.search(r'/ausgabe/\d+/(20\d{2})/',article_url)
    if not yearmatch:raise ValueError('Artikeljahr fehlt')
    year=int(yearmatch.group(1))
    soup=BeautifulSoup(html_text,'html.parser')
    if 'veranstaltungskalender verbandsgemeinde weilerbach' not in soup.get_text(' ',strip=True).casefold():
        raise ValueError('Kein Weilerbacher Veranstaltungskalender')
    out=[]
    for tr in soup.select('tr'):
        cells=[td.get_text(' ',strip=True) for td in tr.find_all(['td','th'],recursive=False)]
        if len(cells)<4:continue
        rawdate,rawtime,title=cells[0],cells[1],cells[2]
        if len(title)<3:continue
        # Letztes Feld trägt den Veranstaltungsort, vorletztes den Veranstalter.
        venue=cells[-1];organizer=cells[-2]
        # Datum: 25.–28.09. oder 04.09., innerhalb eines Monats.
        range_match=re.search(r'(\d{1,2})\s*\.\s*[-–]\s*(\d{1,2})\.\s*(\d{1,2})\.',rawdate)
        single_match=re.search(r'(\d{1,2})\.\s*(\d{1,2})\.',rawdate)
        if range_match:
            day,endday,month=map(int,range_match.groups())
        elif single_match:
            day,month=map(int,single_match.groups());endday=None
        else:continue
        try:
            first=date(year,month,day)
            exclusive=date(year,month,endday)+timedelta(days=1) if endday else None
            if exclusive and exclusive<=first:continue
        except ValueError:continue
        # Nur Orte der VG Weilerbach zulassen; gleichnamige Fremdorte nicht automatisch als VG markieren.
        region,locality=classify_region(' '.join([venue,title,organizer]))
        if region!='vg-weilerbach':continue
        timematch=re.search(r'(\d{1,2})\s*[.,:]\s*(\d{2})\s*Uhr',rawtime,re.I)
        if timematch and not exclusive:
            try:start=datetime(year,month,day,int(timematch.group(1)),int(timematch.group(2)),tzinfo=tz).isoformat(timespec='seconds')
            except ValueError:continue
            all_day=False
        else:start=first.isoformat();all_day=True
        typ=category(title)
        out.append(dict(id=make_id('weilerbach',f'{year}|{first}|{title}|{venue}'),sourceKey='weilerbach',
            title=title,start=start,end=exclusive.isoformat() if exclusive else None,allDay=all_day,
            location=venue or locality,locality=locality,region=region,category=typ,eventType=event_type(title,typ),
            description='',organizer=organizer,source=article_url,status=status_from(title),
            isStadium=False,isMajor=typ=='stadtfest',lastChecked=stamp()))
    return out

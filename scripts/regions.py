"""Amtliche Zuordnung: Kreisfreie Stadt KL sowie sechs VGs im Landkreis KL.
Ortslisten: kaiserslautern-kreis.de/landkreis/gemeinden-und-buergermeister/ortsgemeinden/
Geografische Zuordnung ist eine konservative Textheuristik, KEIN Geocoder.
"""
import re
import unicodedata

REGIONS = {
    'stadt-kl': {'name':'Stadt Kaiserslautern', 'places':['Kaiserslautern','Einsiedlerhof','Erfenbach','Erlenbach','Hohenecken','Dansenberg','Mölschbach','Morlautern','Siegelbach']},
    'vg-bruchmuehlbach': {'name':'VG Bruchmühlbach-Miesau', 'places':['Bruchmühlbach-Miesau','Bruchmühlbach','Miesau','Gerhardsbrunn','Lambsborn','Langwieden','Martinshöhe','Vogelbach','Elchbach']},
    'vg-enkenbach': {'name':'VG Enkenbach-Alsenborn', 'places':['Enkenbach-Alsenborn','Enkenbach','Alsenborn','Fischbach','Frankenstein','Hochspeyer','Mehlingen','Neuhemsbach','Sembach','Waldleiningen','Baalborn']},
    'vg-landstuhl': {'name':'VG Landstuhl', 'places':['Landstuhl','Bann','Hauptstuhl','Kindsbach','Krickenbach','Linden','Mittelbrunn','Oberarnbach','Queidersbach','Schopp','Stelzenberg','Trippstadt']},
    'vg-otterbach': {'name':'VG Otterbach-Otterberg', 'places':['Otterbach','Otterberg','Frankelbach','Heiligenmoschel','Hirschhorn','Katzweiler','Mehlbach','Niederkirchen','Olsbrücken','Schallodenbach','Schneckenhausen','Sulzbachtal']},
    'vg-ramstein': {'name':'VG Ramstein-Miesenbach', 'places':['Ramstein-Miesenbach','Ramstein','Miesenbach','Hütschenhausen','Kottweiler-Schwanden','Niedermohr','Steinwenden','Spesbach','Katzenbach','Weltersbach','Obermohr','Schrollbach','Reuschbach']},
    'vg-weilerbach': {'name':'VG Weilerbach', 'places':['Weilerbach','Erzenhausen','Eulenbis','Kollweiler','Mackenbach','Reichenbach-Steegen','Reichenbach','Rodenbach','Schwedelbach','Fockenberg-Limbach','Fockenberg','Limbach','Albersbach']},
}
# Nur eindeutig städtische Veranstaltungsorte ohne ausgeschriebenen Ortsnamen.
KL_VENUES = ['Fritz-Walter-Stadion','Betzenberg','Kammgarn','Pfalztheater','Fruchthalle','Stadtmuseum','Pfalzgalerie','Friedenskapelle','Volkspark','Messeplatz','Japanischer Garten','Theodor-Zink-Museum']

def norm(text):
    s = unicodedata.normalize('NFKD', str(text or '').casefold())
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'\s+', ' ', s).strip()

def mentions(text, word):
    # Wortgrenzen vermeiden u.a. 'Ramstein' in längeren Wortteilen.
    return bool(re.search(r'(?<!\w)'+re.escape(norm(word))+r'(?!\w)', norm(text)))

def classify_region(location, title=''):
    """(region_id, erkanntes Ortsteilwort), sonst (None,None).
    Keine Zuordnung allein aus 'Landkreis Kaiserslautern' oder Quellname.
    """
    place = str(location or '').strip()
    # 'unter den Linden' ist ein Platz-/Straßenname, KEIN Nachweis für die
    # Ortsgemeinde Linden (VG Landstuhl). Die Phrase vor Ortsabgleich entfernen.
    place = re.sub(r'\bunter den linden\b', ' ', place, flags=re.I).strip()
    if not place and title:
        place = title
    if not place:
        return None, None
    hits=[]
    for key, cfg in REGIONS.items():
        for locality in cfg['places']:
            if mentions(place, locality):
                hits.append((len(norm(locality)), key, locality))
    # Ein expliziter Teilort hat Vorrang gegenüber einem ebenfalls erwähnten 'Kaiserslautern'.
    non_city=[h for h in hits if h[1]!='stadt-kl']
    if non_city:
        _, key, locality = max(non_city)
        return key, locality
    if hits and 'landkreis kaiserslautern' not in norm(place):
        _,key,locality=max(hits)
        return key,locality
    if 'landkreis kaiserslautern' not in norm(place):
        for venue in KL_VENUES:
            if mentions(place,venue):
                return 'stadt-kl','Kaiserslautern'
    return None,None

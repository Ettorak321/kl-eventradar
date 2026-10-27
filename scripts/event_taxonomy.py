"""KL EventRadar V5: Veranstaltungstyp ist unabhängig von Region und Datenquelle.
Konservative Schlagwortklassifikation; Quellen und Orte getrennt.
"""
import re

LABELS = {
    'fussball': 'FCK-Heimspiel', 'kerwe': 'Kerwe',
    'stadtfest': 'Stadt- / Vereinsfest', 'konzert': 'Konzert / Musik',
    'sport': 'Sportveranstaltung', 'markt': 'Markt / Messe',
    'ausstellung': 'Ausstellung', 'museum': 'Museum',
    'kultur': 'Kultur / Theater', 'sonstiges': 'Sonstiges',
}
IMPORTANT = ('fussball', 'kerwe', 'stadtfest', 'konzert', 'sport', 'markt')


def classify_event(title, is_stadium=False, source_key=None):
    """Klassifizierung anhand des Veranstaltungstitels (nicht des Webseiten-Hosts).
    Nur verifizierte Stadiontermine aus dem FCK-Feed heißen FCK-Heimspiel.
    """
    if is_stadium and source_key == 'fck':
        return 'fussball'
    text = str(title or '').casefold()
    if re.search(r'kerwe|kerb\b|kirchweih|kirmes', text):
        return 'kerwe'
    if re.search(r'ausstellung|vernissage|kunstausstellung|fotoausstellung|exposition', text):
        return 'ausstellung'
    if re.search(r'museum|museumsnacht|museumsführung', text):
        return 'museum'
    if re.search(r'sportfest|fußball|fussball|turnier|laufveranstaltung|marathon|radrennen|handball|volleyball|basketball|leichtathletik', text):
        return 'sport'
    if re.search(r'konzert|musik|sommerswing|jazz|blues|livemusik|live-musik|bandabend|rocknacht|open.air', text):
        return 'konzert'
    if re.search(r'\b(?:weihnachtsmarkt|flohmarkt|wochenmarkt|jahrmarkt|bauernmarkt|kunsthandwerkermarkt|markt|messe|basar)\b', text):
        return 'markt'
    if re.search(r'stadtfest|altstadtfest|dorffest|straßenfest|strassenfest|vereinsfest|feuerwehrfest|sommerfest|volksfest|weinfest|bierfest|oktoberfest|brunnenfest|bürgerfest|buergerfest|festwochen|festumzug', text):
        return 'stadtfest'
    if re.search(r'theater|kabarett|lesung|vortrag|oper\b|ballett|tanztheater|kultur|kunstführung|bühne|schauspiel', text):
        return 'kultur'
    return 'sonstiges'


def relabel(ev):
    """Auch alte Events aus einzelnen Quellen-Caches beim nächsten Lauf korrigieren."""
    result = dict(ev)
    kind = classify_event(result.get('title', ''), result.get('isStadium') is True
                          and result.get('venueVerified') is True,
                          result.get('sourceKey'))
    result['category'] = kind
    result['eventType'] = LABELS[kind]
    if kind == 'fussball':
        result['isStadium'] = True
        result['isMajor'] = True
    else:
        # Unbestätigte alte FCK-Caches nie als Stadionbelegung deklarieren.
        result['isStadium'] = False
    # Sportfest/Kerwe/Stadtfest sind ggf. publikumswirksam; nur grobe Kennzeichnung.
    result['isMajor'] = kind in ('fussball', 'kerwe', 'stadtfest') or (kind == 'konzert' and bool(result.get('isMajor')))
    return result

"""Ausstellungsreihen in Museums-Spielplänen vorsichtig erkennen.

Die Quellen melden Ausstellungen teils nur als tagweise 'Sonstiges'. Wir
identifizieren solche Reihen anhand der Museums-Spielstätte und wiederholter,
unmittelbar benachbarter Öffnungstage, nicht anhand eines Titels allein.
Einzelne Veranstaltungen/Führungen/Konzerte bleiben erhalten. Rohcaches
bleiben unverändert; nur öffentliche Darstellungsdaten werden ergänzt.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import timedelta
from .event_series import day_of, is_single_day

# Die hier aufgeführten Veranstaltungsorte sind in der städtischen Datenquelle
# als Museums-Spielstätten verifiziert. Weitere Orte nur nach Prüfung ergänzen.
MUSEUM_VENUES = re.compile(
    r"(?:^|\b)(?:museum pfalzgalerie(?: kaiserslautern)?|stadtmuseum kaiserslautern)\b",
    re.IGNORECASE,
)
EXCLUDE_TITLES = re.compile(
    r"\b(?:führungen?|fuehrungen?|museumsführungen?|vorträge?|vortraege?|"
    r"workshops?|kurse?|konzerte?|lesungen?|vernissagen?|"
    r"führungsprogramm|familienführung|theater|aufführungen?|"
    r"kabarett|musik|exkursion|gespräch|diskussion)\b",
    re.IGNORECASE,
)


def candidate(ev):
    """Nur unklassifizierte veröffentlichte Museumstermine."""
    return (ev.get("sourceKey") == "city"
            and ev.get("category") == "sonstiges"
            and ev.get("status") == "confirmed"
            and not any(ev.get(k) for k in ("forecast", "isAnnualDay", "isCustom", "isSeries"))
            and ev.get("title") and ev.get("location")
            and MUSEUM_VENUES.search(str(ev["location"])) is not None
            and EXCLUDE_TITLES.search(str(ev["title"])) is None
            and is_single_day(ev))


def annotate_exhibition_series(events):
    """Nur Tage mit belegtem Nachbartag werden Ausstellung; keine Lücken füllen.

    Wiederholtes Auftreten allein reicht NICHT: erst direkt benachbarte Tage
    desselben Titels am selben Museum (ohne Mehrfachtermine am selben Tag).
    """
    groups = defaultdict(list)
    for ev in events:
        if not candidate(ev):
            continue
        group = tuple(str(ev.get(f) or "").strip().casefold()
                      for f in ("sourceKey", "title", "location", "region", "locality", "status"))
        groups[group].append(ev)
    chosen = set()
    for values in groups.values():
        days = Counter(day_of(ev) for ev in values)
        uniques = sorted(day for day, count in days.items() if day is not None and count == 1)
        set_days = set(uniques)
        for ev in values:
            d = day_of(ev)
            if d is None or days[d] != 1:
                continue
            if d - timedelta(days=1) in set_days or d + timedelta(days=1) in set_days:
                chosen.add(id(ev))
    result = []
    for ev in events:
        if id(ev) in chosen:
            altered = dict(ev)
            altered["category"] = "ausstellung"
            altered["eventType"] = "Ausstellung"
            altered["exhibitionSeries"] = True
            result.append(altered)
        else:
            result.append(ev)
    return result

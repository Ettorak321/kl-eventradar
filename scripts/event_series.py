"""Identische tägliche Veranstaltungsreihen als mehrtägige Balken bündeln.

Die täglichen Rohdaten bleiben in den Quellencaches unverändert. Es werden
ausschließlich unmittelbar aufeinanderfolgende veröffentlichte Einträge
derselben Veranstaltung am selben Ort und aus derselben Quelle aggregiert.
"""
from collections import Counter, defaultdict
from datetime import date, timedelta
from hashlib import sha256
import re

SERIES_CATEGORIES = frozenset({"markt", "kerwe", "stadtfest", "ausstellung"})
# Wiederkehrende Markt-/Ausstellungsreihen können von der Quelle als Kultur
# oder Sonstiges eingestuft werden. Theater, Konzerte und Aufführungen bleiben
# dagegen Einzeltermine mit eigener Uhrzeit/Ticketierung.
SERIES_TITLE = re.compile(r"(?:markt|messe|ausstellung|kulturtage|festival)\b", re.I)


def eligible_series(event):
    category = event.get("category")
    if category in SERIES_CATEGORIES:
        return True
    if category in ("kultur", "sonstiges"):
        return bool(SERIES_TITLE.search(str(event.get("title") or "")))
    return False


def day_of(event):
    try:
        return date.fromisoformat(str(event["start"])[:10])
    except (KeyError, TypeError, ValueError):
        return None


def is_single_day(event):
    start = day_of(event)
    if start is None:
        return False
    finish = event.get("end")
    if not finish:
        return True
    try:
        last = date.fromisoformat(str(finish)[:10])
    except ValueError:
        return False
    # Ganztägige Termine verwenden ein exklusives Enddatum.
    return last == start + timedelta(days=1) if event.get("allDay") is True else last == start


def key_for(event):
    if (not eligible_series(event)
            or event.get("status") != "confirmed"
            or event.get("isCustom") or event.get("isSeries")
            or event.get("forecast") or event.get("isAnnualDay")
            or not event.get("title") or not event.get("location")
            or not is_single_day(event)):
        return None
    # Titel, Ort, Art, Quelle, Status und Programmtext müssen übereinstimmen.
    # Der Link kann pro Veranstaltungstag abweichen.
    fields = ("sourceKey", "title", "location", "region", "locality",
              "category", "status", "description", "organizer", "address",
              "stale", "isMajor", "isStadium", "venueVerified")
    return tuple(str(event.get(field) or "").strip().casefold() for field in fields)


def collapse_adjacent_series(events):
    """Nur wirklich aufeinanderfolgende Kalendertage werden verbunden.

    Erzeugte Balken sind FullCalendar-All-Day-Spannen mit exklusivem Enddatum.
    Original-Startzeiten und tageweise Quelllinks bleiben in seriesDays erhalten.
    """
    buckets = defaultdict(list)
    untouched = []
    for event in events:
        key = key_for(event)
        if key is None:
            untouched.append(event)
        else:
            buckets[key].append(event)

    output = list(untouched)
    for key, group in buckets.items():
        group = sorted(group, key=lambda e: (day_of(e), str(e["start"])))
        # Mehrere Termine am gleichen Tag können echte getrennte Vorstellungen sein.
        # Solche Gruppen werden nicht zusammengelegt.
        dates = [day_of(e) for e in group]
        if any(count > 1 for count in Counter(dates).values()):
            output.extend(group)
            continue
        run = []
        def flush():
            if len(run) < 2:
                output.extend(run)
                return
            first, last = run[0], run[-1]
            beginning, ending = day_of(first), day_of(last)
            identifying = "\x1f".join(key) + "\x1f" + beginning.isoformat()
            combined = dict(first)
            combined.update({
                "id": "serie-" + sha256(identifying.encode("utf-8")).hexdigest()[:24],
                "start": beginning.isoformat(),
                "end": (ending + timedelta(days=1)).isoformat(),
                "allDay": True,
                "isSeries": True,
                "seriesCount": len(run),
                "seriesDays": [
                    {"date": day_of(e).isoformat(), "start": e["start"],
                     "end": e.get("end"), "source": e.get("source"),
                     "originalId": e["id"]}
                    for e in run
                ],
            })
            output.append(combined)
        for event in group:
            if run and day_of(event) != day_of(run[-1]) + timedelta(days=1):
                flush()
                run = []
            run.append(event)
        if run:
            flush()
    return sorted(output, key=lambda e: (e["start"], e.get("title", ""), e.get("id", "")))

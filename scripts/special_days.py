"""Jährliche Kalenderdaten für Rheinland-Pfalz: Gesetzliche Feiertage und Anlässe.

Keine Veranstaltungstermine oder Besucherprognosen. Gesetzliche Feiertage laut
Innenministerium Rheinland-Pfalz; die Anlässe sind davon getrennt markiert.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

LEGAL_SOURCE = "https://mdi.rlp.de/themen/buerger-und-staat/verfassung-und-verwaltung/sonn-und-feiertagsrecht"


def easter_sunday(year: int) -> date:
    """Gregorianischer Ostertermin nach dem Meeus/Jones/Butcher-Algorithmus."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


def nth_weekday(year: int, month: int, weekday: int, ordinal: int) -> date:
    """0=Montag, 6=Sonntag; ordinal=2 für zweiten Sonntag."""
    first = date(year, month, 1)
    result = first + timedelta(days=(weekday - first.weekday()) % 7 + 7 * (ordinal - 1))
    if result.month != month:
        raise ValueError("Kalenderregel reicht über Monatsende hinaus")
    return result


def annual_days(year: int) -> list[dict]:
    """Gesetzliche Feiertage (RLP) + ausgewählte wiederkehrende Anlässe."""
    easter = easter_sunday(year)
    fixed = lambda month, day: date(year, month, day)
    offset = lambda days: easter + timedelta(days=days)
    statutory = [
        ("Neujahr", fixed(1, 1)),
        ("Karfreitag", offset(-2)),
        ("Ostermontag", offset(1)),
        ("Tag der Arbeit", fixed(5, 1)),
        ("Christi Himmelfahrt (Vatertag)", offset(39)),
        ("Pfingstmontag", offset(50)),
        ("Fronleichnam", offset(60)),
        ("Tag der Deutschen Einheit", fixed(10, 3)),
        ("Allerheiligen", fixed(11, 1)),
        ("1. Weihnachtstag", fixed(12, 25)),
        ("2. Weihnachtstag", fixed(12, 26)),
    ]
    occasions = [
        ("Valentinstag", fixed(2, 14)),
        ("Weiberfastnacht", offset(-52)),
        ("Rosenmontag", offset(-48)),
        ("Fastnachtsdienstag", offset(-47)),
        ("Aschermittwoch", offset(-46)),
        ("St. Patrick's Day", fixed(3, 17)),
        ("Ostersonntag", easter),
        ("Tanz in den Mai", fixed(4, 30)),
        ("Muttertag", nth_weekday(year, 5, 6, 2)),
        ("Pfingstsonntag", offset(49)),
        ("Halloween", fixed(10, 31)),
        ("Martinstag", fixed(11, 11)),
        ("Beginn der Fastnachtssaison (11.11.)", fixed(11, 11)),
        ("Nikolaustag", fixed(12, 6)),
        ("Heiligabend", fixed(12, 24)),
        ("Silvester", fixed(12, 31)),
    ]
    result = []
    for legal, days in ((True, statutory), (False, occasions)):
        for name, day in days:
            kind = "feiertag" if legal else "anlass"
            slug = ("gesetzlich" if legal else "anlass") + "-" + str(len(result))
            result.append({
                "id": f"kalendertag-{year}-{slug}",
                "title": name,
                "start": day.isoformat(),
                "end": (day + timedelta(days=1)).isoformat(),
                "allDay": True,
                "sourceKey": "calendar_days",
                "category": kind,
                "eventType": "Gesetzlicher Feiertag (RLP)" if legal else "Besonderer Anlass",
                "region": "alle-regionen",
                "locality": "Stadt und Landkreis Kaiserslautern",
                "location": "Gilt überregional – kein konkreter Veranstaltungsort",
                "description": (
                    "Gesetzlicher Feiertag in Rheinland-Pfalz. "
                    "Es wird keine konkrete Veranstaltung behauptet."
                    if legal else
                    "Wiederkehrender Kalenderanlass; kein gesetzlicher Feiertag in Rheinland-Pfalz "
                    "und keine automatisch bestätigte örtliche Veranstaltung."
                ),
                "status": "calendar",
                "isAnnualDay": True,
                "isPublicHoliday": legal,
                "isStadium": False,
                "venueVerified": False,
                "isMajor": False,
                "source": LEGAL_SOURCE if legal else "",
            })
    return sorted(result, key=lambda e: (e["start"], e["id"]))


def attach_calendar_days(events: list[dict], today: date | None = None, future_years: int = 5) -> list[dict]:
    """Berechnet aktuelles Jahr und fünf Folgejahre; erneute Läufe sind idempotent."""
    today = today or datetime.now(ZoneInfo("Europe/Berlin")).date()
    if not 0 <= future_years <= 10:
        raise ValueError("Ungültiger Zeitraum")
    original = [e for e in events if e.get("sourceKey") != "calendar_days" and not e.get("isAnnualDay")]
    additions = [ev for year in range(today.year, today.year + future_years + 1)
                 for ev in annual_days(year)]
    return sorted(original + additions, key=lambda e: (e["start"], e["title"]))

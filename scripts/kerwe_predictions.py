"""Unverbindliche Kerwe-Vorschauen aus dokumentierten historischen Wiederholungsregeln."""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

RULES_FILE = Path(__file__).resolve().parent.parent / "data" / "kerwe_rules.json"
KERWE = re.compile(r"kerwe|kerb\b|kirchweih|kirmes", re.I)


def clean(value):
    s = unicodedata.normalize("NFKD", str(value or "")).casefold()
    return "".join(ch for ch in s if not unicodedata.combining(ch)).replace("ß", "ss")


def nth_weekday(year, month, weekday, nth):
    if not 1 <= month <= 12 or not 0 <= weekday <= 6 or not 1 <= nth <= 5:
        raise ValueError("Ungültige Kalenderregel")
    first = date(year, month, 1)
    result = first + timedelta(days=(weekday - first.weekday()) % 7 + 7 * (nth - 1))
    if result.month != month:
        raise ValueError("Kein passender Wochentag in diesem Monat")
    return result


def load_rules(path=RULES_FILE):
    path = Path(path)
    if not path.is_file():
        return []
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schemaVersion") != 1 or not isinstance(document.get("rules"), list):
        raise ValueError("Unbekanntes Kerwe-Regelformat")
    return document["rules"]


def confirmed_exists(events, rule, year):
    place = clean(rule["locality"])
    for e in events:
        if e.get("forecast") or e.get("sourceKey") == "kerwe_forecast":
            continue
        if e.get("region") != rule["region"] or str(e.get("start", ""))[:4] != str(year):
            continue
        title = str(e.get("title", ""))
        if not KERWE.search(title) and e.get("category") != "kerwe":
            continue
        # Keine Kerwe einer benachbarten Ortsgemeinde derselben VG unterdrücken.
        if place in clean(title + " " + str(e.get("location", ""))) or clean(e.get("locality")) == place:
            return True
    return False


def create_forecasts(events, rules, today=None, years=4):
    today = today or datetime.now(ZoneInfo("Europe/Berlin")).date()
    if not 1 <= years <= 5:
        raise ValueError("Ungültiger Vorschauzeitraum")
    forecasts, seen = [], set()
    for rule in rules:
        if not all(rule.get(k) for k in ("id", "name", "region", "locality", "location", "ruleText", "evidence")):
            raise ValueError("Unvollständige Regel")
        duration = int(rule["durationDays"])
        if not 1 <= duration <= 14:
            raise ValueError("Ungültige Veranstaltungsdauer")
        for year in range(today.year + 1, today.year + 1 + years):
            key = (rule["id"], year)
            if key in seen:
                raise ValueError("Doppelte Regel")
            seen.add(key)
            if confirmed_exists(events, rule, year):
                continue
            center = nth_weekday(year, int(rule["month"]), int(rule["weekday"]), int(rule["nth"]))
            start = center + timedelta(days=int(rule["startOffsetDays"]))
            end = start + timedelta(days=duration)
            forecasts.append({
                "id": f"kerwe-vorschau-{rule['id']}-{year}",
                "sourceKey": "kerwe_forecast", "title": rule["name"] + " (Prognose)",
                "start": start.isoformat(), "end": end.isoformat(), "allDay": True,
                "category": "kerwe", "eventType": "Kerwe",
                "region": rule["region"], "locality": rule["locality"], "location": rule["location"],
                "description": "Nur aus Vorjahresterminen berechnet, nicht offiziell bestätigt. " + rule.get("notes", ""),
                "status": "predicted", "forecast": True, "isStadium": False,
                "venueVerified": False, "isMajor": False, "forecastYear": year,
                "forecastRule": rule["ruleText"], "forecastNotes": rule.get("notes", ""),
                "forecastEvidence": rule["evidence"], "source": rule["evidence"][-1]["url"],
            })
    return sorted(forecasts, key=lambda e: (e["start"], e["title"]))


def attach_forecasts(events, rules_path=RULES_FILE, today=None):
    official = [e for e in events if e.get("sourceKey") != "kerwe_forecast" and not e.get("forecast")]
    forecasts = create_forecasts(official, load_rules(rules_path), today=today)
    return sorted(official + forecasts, key=lambda e: (e["start"], e["title"]))

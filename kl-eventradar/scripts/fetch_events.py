#!/usr/bin/env python3
"""KL EventRadar: konservativer Quellensammler mit atomaren, getrennten Caches.
Keine Quelle wird bei einem Fehler durch ein leeres Ergebnis ersetzt.
"""
from __future__ import annotations

import hashlib
import html
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs, unquote, urljoin, urlparse
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
try:
    from .regions import classify_region, REGIONS
    from .regional_sources import OPEN_RLP, RAMSTEIN, PFALZ, parse_rlp_json, parse_ramstein_html, parse_pfalz_jsonld, event_type, WITTICH_EDITION, weilerbach_article_links, parse_weilerbach_article
except ImportError:
    from regions import classify_region, REGIONS
    from regional_sources import OPEN_RLP, RAMSTEIN, PFALZ, parse_rlp_json, parse_ramstein_html, parse_pfalz_jsonld, event_type, WITTICH_EDITION, weilerbach_article_links, parse_weilerbach_article

LOG = logging.getLogger("kl-eventradar")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CACHE = DATA / "cache"
TZ = ZoneInfo("Europe/Berlin")
FCK_PAGE = "https://fck.de/kalender/"
# Der direkte ICS-Link ist aus dem offiziell verlinkten Google-Kalender-Button abgeleitet.
OFFICIAL_ICS = "https://calendar.google.com/calendar/ical/3f0c5167b8dd2fc4ab037e57ea84b976ce2a091f93dd9c3d3e813d879f4e3fc0%40group.calendar.google.com/public/basic.ics"
FALLBACK_ICS = "https://www.google.com/calendar/ical/vrqsl06jqijtgbubkk01i3n6fk%40group.calendar.google.com/public/basic.ics"
CITY_PAGE = "https://www.kaiserslautern.de/tourismus_freizeit_kultur/veranstaltungen/index.html.de"
SWING_PAGE = "https://sommerswing.de/bands.html"
HEADERS = {"User-Agent": "KLEventRadar/3.0 (public event calendar; repository maintainer contact required)", "Accept-Language": "de-DE,de;q=0.9"}
DATE_RE = re.compile(r"(?:(\d{1,2}):(\d{2})\s*Uhr\s*,?\s*)?(\d{1,2})\.\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+(20\d{2})", re.I)
MONTHS = {n.lower(): i for i, n in enumerate(("Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"), 1)}
VENUE_KL = ("kaiserslautern", "fritz-walter-stadion", "betzenberg", "kammgarn", "pfalztheater", "fruchthalle", "stadtmuseum", "pfalzgalerie", "friedenskapelle", "volkspark", "messeplatz", "japanischer garten", "42kaiserslautern", "emmerich-smola", "kasino der kammgarn", "theodor-zink-museum", "jugendhaus", "stiftskirche", "union-kino", "salon schmitt", "swr studio")
OUTSIDE_KL = ("kusel", "steinwenden", "landstuhl", "ramstein", "mehlingen", "mehlbach", "otterbach", "weilerbach", "enkenbach", "hochspeyer", "pirmasens", "zweibrücken", "homburg", "neustadt", "trippstadt", "kind(s)bach")

class SourceError(Exception):
    pass

def stamp():
    return datetime.now(TZ).isoformat(timespec="seconds")

def atomic_json(path: Path, content: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(content, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)

def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default

def fetch(url: str, session=None, timeout=22):
    req = session or requests
    try:
        res = req.get(url, timeout=timeout, headers=HEADERS)
        res.raise_for_status()
        if not res.content:
            raise SourceError(f"Leere Antwort: {url}")
        return res
    except requests.RequestException as exc:
        raise SourceError(f"Abruf fehlgeschlagen ({url}): {exc}") from exc

def stable_id(namespace, identifier):
    return namespace + "-" + hashlib.sha256(identifier.encode("utf-8")).hexdigest()[:20]

def normalize_title(title):
    return re.sub(r"\W+", "", title.casefold(), flags=re.UNICODE)

def category(title):
    t = title.casefold()
    if any(k in t for k in ("sommerswing", "konzert", "jazz", "musik", "blues", "band", "swing")):
        return "konzert"
    if any(k in t for k in ("stadtfest", "altstadtfest", "kerwe", "fest", "festival")):
        return "stadtfest"
    if any(k in t for k in ("markt", "messe", "basar")):
        return "markt"
    return "kultur"

def status_from(text, ics_status=""):
    val = text.casefold()
    if ics_status.upper() == "CANCELLED" or any(s in val for s in ("abgesagt", "entfällt", "cancelled")):
        return "cancelled"
    if "verschoben" in val:
        return "postponed"
    if ics_status.upper() == "TENTATIVE":
        return "tentative"
    return "confirmed"

# -------- ICS ohne Zusatzbibliothek, inklusive folded lines und TZID --------
def unescape_ics(s):
    return re.sub(r"\\([nN,;\\])", lambda m: "\n" if m.group(1).lower() == "n" else m.group(1), s)

def ics_components(payload: bytes):
    text = payload.decode("utf-8-sig", errors="replace")
    unfolded = re.sub(r"\r?\n[ \t]", "", text).splitlines()
    if "BEGIN:VCALENDAR" not in unfolded:
        raise SourceError("Ungültige ICS-Datei (VCALENDAR fehlt)")
    events, current = [], None
    for line in unfolded:
        if line == "BEGIN:VEVENT":
            current = {}
        elif line == "END:VEVENT" and current is not None:
            events.append(current)
            current = None
        elif current is not None and ":" in line:
            key, val = line.split(":", 1)
            name = key.split(";", 1)[0].upper()
            current[name] = (key, unescape_ics(val))
    return events

def parse_ics_date(prop):
    if not prop:
        return None, False
    key, value = prop
    all_day = "VALUE=DATE" in key.upper() or re.fullmatch(r"\d{8}", value) is not None
    if all_day:
        return date.fromisoformat(f"{value[:4]}-{value[4:6]}-{value[6:8]}").isoformat(), True
    tzid = re.search(r"TZID=([^;:]+)", key, re.I)
    dt = datetime.strptime(value.rstrip("Z"), "%Y%m%dT%H%M%S" if len(value.rstrip("Z")) == 15 else "%Y%m%dT%H%M")
    if value.endswith("Z"):
        dt = dt.replace(tzinfo=timezone.utc).astimezone(TZ)
    elif tzid:
        try:
            dt = dt.replace(tzinfo=ZoneInfo(tzid.group(1))).astimezone(TZ)
        except Exception as exc:
            raise SourceError(f"Unbekannte ICS-Zeitzone {tzid.group(1)}") from exc
    else:
        dt = dt.replace(tzinfo=TZ)
    return dt.isoformat(timespec="seconds"), False

def is_fixture(summary):
    """Nur Paarungen der Profis mit FCK als *erstgenanntem* Heimteam."""
    normalized = re.sub(r"\s+", " ", summary.casefold())
    if re.search(r"u\s?(?:17|19|21|23)|training|pressekonferenz|museum|geburtstag", normalized):
        return False
    return bool(re.match(
        r"^\s*(?:(?:1\.\s*)?fc\s*kaiserslautern|fck)\s*(?:-|–|—|vs\.?|gegen)\s+\S",
        normalized,
    ))

def is_home_game(summary, location):
    """Spielpaarung FCK zuerst + ausdrücklich Fritz-Walter-Stadion."""
    if not is_fixture(summary):
        return False
    norm = re.sub(r"\s+", " ", location.casefold())
    return "fritz-walter" in norm or "betzenberg" in norm

def discover_official_ics(session=None):
    """Folgt nicht Google-OAuth, sondern extrahiert cid aus dem offiziellen Profi-Button."""
    try:
        soup = BeautifulSoup(fetch(FCK_PAGE, session).text, "html.parser")
        for a in soup.find_all("a", href=True):
            if "profi-termine" not in a.get_text(" ", strip=True).casefold():
                continue
            href = html.unescape(a["href"])
            query = parse_qs(urlparse(href).query)
            for item in query.get("cid", []):
                candidate = unquote(item).replace("webcal://", "https://")
                if candidate.startswith("https://") and "/calendar/ical/" in candidate and candidate.endswith(".ics"):
                    return candidate
            if href.startswith("https://") and "/calendar/ical/" in href and href.endswith(".ics"):
                return href
    except SourceError as exc:
        LOG.warning("Offizielle Kalenderseite nicht erreichbar: %s", exc)
    return OFFICIAL_ICS

def parse_fck_ics(ics_url, session=None):
    payload = fetch(ics_url, session).content
    events = []
    for item in ics_components(payload):
        summary = item.get("SUMMARY", ("", ""))[1].strip()
        loc = item.get("LOCATION", ("", ""))[1].strip()
        if not is_home_game(summary, loc):
            continue
        try:
            start, all_day = parse_ics_date(item.get("DTSTART"))
            end, _ = parse_ics_date(item.get("DTEND"))
        except (ValueError, SourceError) as exc:
            LOG.warning("Ungültiger FCK-Eintrag: %s", exc)
            continue
        if not start:
            continue
        uid = item.get("UID", ("", ""))[1]
        recurrence_id = item.get("RECURRENCE-ID", ("", ""))[1]
        source_id = f"{uid}/{recurrence_id}" if uid else f"{summary}|{start}"
        events.append({
            "id": stable_id("fck", source_id), "sourceKey": "fck", "title": summary, "region":"stadt-kl", "locality":"Kaiserslautern", "eventType":"FCK-Heimspiel",
            "start": start, "end": end, "allDay": all_day,
            "location": "Fritz-Walter-Stadion, Kaiserslautern", "address": "Fritz-Walter-Straße 1, 67663 Kaiserslautern",
            "category": "fussball", "description": "Öffentlich bestätigter Profifußball-Termin",
            "organizer": "1. FC Kaiserslautern", "source": FCK_PAGE,
            "sourceUrl": ics_url, "status": status_from(summary, item.get("STATUS", ("", ""))[1]),
            "isStadium": True, "venueVerified": True, "isMajor": True,
            "lastChecked": stamp(),
        })
    # Akzeptiere keine komplett leere Antwort als belastbaren neuen Stand.
    if not events:
        raise SourceError("ICS abrufbar, aber kein nachweislich im Fritz-Walter-Stadion stattfindendes Profispiel enthalten")
    return dedupe_exact(events)

def fetch_fck(session=None):
    primary = discover_official_ics(session)
    errors = []
    for url in dict.fromkeys((primary, OFFICIAL_ICS, FALLBACK_ICS)):
        try:
            return parse_fck_ics(url, session)
        except SourceError as exc:
            errors.append(str(exc))
            LOG.warning("FCK-Feed fehlgeschlagen: %s", exc)
    raise SourceError("; ".join(errors)[:500])

# -------- Stadt: durch Seitenzähler gesteuerte echte Paginierung --------
def in_city(location):
    name = " ".join(location.casefold().split())
    if not name:
        return False
    if any(bad in name for bad in OUTSIDE_KL):
        return False
    return any(good in name for good in VENUE_KL)

def parse_german_schedule(text):
    """Ergebnis (start, exclusive_end, all_day) oder None."""
    # Ganztägige Stadtveranstaltung über mehrere Tage/Monate.
    range_match = re.search(
        r"(\d{1,2})\.\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s*"
        r"(?:bis|[-–])\s*(\d{1,2})\.\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+(20\d{2})",
        text, re.I,
    )
    if range_match:
        sd,sm,ed,em,y=range_match.groups()
        try:
            sd,sm,ed,em,y=int(sd),MONTHS[sm.lower()],int(ed),MONTHS[em.lower()],int(y)
            first=date(y-(sm>em),sm,sd)
            last=date(y,em,ed)
            if last < first:
                return None
            return first.isoformat(),(last+timedelta(days=1)).isoformat(),True
        except ValueError:
            return None
    m = DATE_RE.search(text)
    if not m:
        return None
    hour, minute, day, monthname, year = m.groups()
    try:
        day = date(int(year), MONTHS[monthname.lower()], int(day))
        if hour is None or (hour == "00" and minute == "00"):
            return day.isoformat(), None, True
        return datetime(day.year, day.month, day.day, int(hour), int(minute), tzinfo=TZ).isoformat(timespec="seconds"), None, False
    except ValueError:
        return None

def parse_german_date(text):
    parsed = parse_german_schedule(text)
    return (parsed[0],parsed[2]) if parsed else None

def pagination_marker(soup):
    text = soup.get_text(" ", strip=True)
    found = re.search(r"(\d[\d.]*)\s+Einträge\s*-\s*Seite\s+(\d+)\s+von\s+(\d+)", text, re.I)
    if not found:
        return None
    return tuple(int(x.replace(".", "")) for x in found.groups())

def extract_city_page(html_text, base_url=CITY_PAGE):
    soup = BeautifulSoup(html_text, "html.parser")
    found = []
    seen = set()
    for a in soup.select('a[href*="/miadi/view.php?event="]'):
        href = urljoin(base_url, a.get("href", ""))
        parsed_url = urlparse(href)
        if not parsed_url.hostname or not parsed_url.hostname.endswith("kaiserslautern.de"):
            continue
        uid = parse_qs(parsed_url.query).get("event", [""])[0]
        if not re.fullmatch(r"[\w-]{3,80}", uid) or uid in seen:
            continue
        # Kleinster Container mit vollständigem Titel, Datum und Ort.
        container = a
        candidate = None
        for _ in range(6):
            container = container.parent
            if not container:
                break
            text = container.get_text(" ", strip=True)
            if 15 <= len(text) <= 1200 and DATE_RE.search(text) and container.find(["h3", "h4", "h2"]):
                candidate = container
                break
        if candidate is None:
            continue
        heading = candidate.find(["h3", "h4", "h2"])
        title = heading.get_text(" ", strip=True) if heading else ""
        body = candidate.get_text(" ", strip=True)
        parsed = parse_german_schedule(body)
        if not parsed or len(title) < 3:
            continue
        # Typisches Layout: Titel, Uhrzeit / Datum, Veranstaltungsort, Mehr.
        # Sauberer: Match-Ende + danach verbleibende Ortsangabe.
        dt_match = DATE_RE.search(body)
        tail = body[dt_match.end():].strip(" ,:-") if dt_match else ""
        tail = re.sub(r"\s*(?:Mehr|Details|Weiterlesen)\s*$", "", tail, flags=re.I).strip()
        # Bei uneindeutigen Mehrfachcontainern keine ungesicherte Ortsangabe übernehmen.
        location = tail[:110]
        if not in_city(location):
            continue
        start, end, all_day = parsed
        seen.add(uid)
        cat = category(title)
        found.append({
            "id": stable_id("city", uid), "sourceKey": "city", "region":"stadt-kl", "locality":"Kaiserslautern", "eventType":event_type(title, cat),
            "title": title, "start": start, "end": end, "allDay": all_day,
            "location": location, "address": "", "category": cat,
            "description": "", "organizer": "", "source": href,
            "status": status_from(title), "isStadium": False,
            "venueVerified": False, "isMajor": cat == "stadtfest",
            "lastChecked": stamp(),
        })
    return found

def fetch_city(session=None, max_pages=40):
    first = BeautifulSoup(fetch(CITY_PAGE, session).text, "html.parser")
    meta = pagination_marker(first)
    if not meta:
        raise SourceError("Stadt-Pagination nicht erkennbar; Datensatz bleibt unverändert")
    count, current, total = meta
    if current != 1 or not 1 <= total <= max_pages:
        raise SourceError(f"Unerwartete Seitenzahl: {meta}")
    pages = [first]
    for n in range(2, total + 1):
        # Die Stadt stellt eine numerierte Paginierung bereit. Die URL wird anhand
        # der tatsächlich zurückgegebenen Seitenmarkierung geprüft, niemals angenommen.
        url = f"{CITY_PAGE}?page={n}"
        page = BeautifulSoup(fetch(url, session).text, "html.parser")
        marker = pagination_marker(page)
        if marker is None or marker[1] != n:
            raise SourceError(f"Stadt-Paginierung für Seite {n} nicht bestätigt: {marker}")
        pages.append(page)
        time.sleep(0.15)
    events = []
    for page in pages:
        events.extend(extract_city_page(str(page)))
    events = dedupe_exact(events)
    if count > 0 and len(events) < max(1, count // 4):
        raise SourceError(f"Stadt-Parser erkennt auffällig wenige Termine ({len(events)}/{count}); Cache geschützt")
    LOG.info("Stadt: %d von %d Listeneinträgen als innerstädtisch eingestuft", len(events), count)
    return events

# -------- Sommerswing: explizite Band-Programm-Daten, keine Wochen-Erfindung --------
def parse_sommerswing_html(page):
    soup = BeautifulSoup(page, "html.parser")
    main_text = soup.get_text(" ", strip=True)
    years = {int(s) for s in re.findall(r"\b20(?:2[5-9]|[3-9]\d)\b", main_text)}
    if len(years) != 1:
        raise SourceError("Sommerswing-Jahr nicht eindeutig veröffentlicht; keine Termine erfunden")
    year = next(iter(years))
    results = []
    for heading in soup.find_all(re.compile(r"^h[1-5]$")):
        heading_text = heading.get_text(" ", strip=True)
        match = re.fullmatch(r"(\d{1,2})\.\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)", heading_text, re.I)
        if not match:
            continue
        day, month = int(match.group(1)), MONTHS[match.group(2).lower()]
        try:
            actual = date(year, month, day)
        except ValueError:
            continue
        # Bandname: Text unmittelbar vor Datumsüberschrift, nicht die Beschreibung danach.
        prev = heading.find_previous_sibling()
        if prev is None:
            prev = heading.find_previous(["h2", "h3", "h4", "p"])
        band = prev.get_text(" ", strip=True) if prev else ""
        band = re.sub(r"\s+", " ", band)[:100]
        if not band or len(band) > 100 or band.casefold().startswith("liebe musikfreunde"):
            raise SourceError("Sommerswing-Bandname konnte nicht verlässlich erkannt werden")
        start = datetime(year, month, day, 19, tzinfo=TZ)
        end = start + timedelta(hours=3)
        results.append({
            "id": f"sommerswing-{actual.isoformat()}", "sourceKey": "sommerswing", "region":"stadt-kl", "locality":"Kaiserslautern", "eventType":"Sommerswing",
            "title": f"Sommerswing: {band}", "start": start.isoformat(timespec="seconds"),
            "end": end.isoformat(timespec="seconds"), "allDay": False,
            "location": "Volkspark Kaiserslautern", "address": "Entersweilerstraße 1, 67657 Kaiserslautern",
            "category": "konzert", "description": "Sommerswing im Volkspark",
            "organizer": "Sommerswing / Franz Wosnitza", "source": SWING_PAGE,
            "status": "confirmed", "isStadium": False, "isMajor": True,
            "lastChecked": stamp(),
        })
    if not results:
        raise SourceError("Keine expliziten Sommerswing-Datumsüberschriften gefunden")
    return dedupe_exact(results)

def fetch_sommerswing(session=None):
    return parse_sommerswing_html(fetch(SWING_PAGE, session).text)

# -------- Persistenz / Veröffentlichung --------
def dedupe_exact(events):
    chosen = {}
    for ev in events:
        key = ev["id"]
        chosen[key] = ev
    return list(chosen.values())

def dedupe_cross_sources(events):
    """Nur eindeutige Sommerswing-Tagesdoppelungen werden zusammengeführt."""
    swing_dates = {e["start"][:10] for e in events if e["sourceKey"] == "sommerswing"}
    out = []
    seen = set()
    for ev in sorted(events, key=lambda e: {"sommerswing": 0, "fck": 1, "city": 2}.get(e["sourceKey"], 9)):
        if ev["sourceKey"] == "city" and "sommerswing" in ev["title"].casefold() and ev["start"][:10] in swing_dates:
            continue
        key = (normalize_title(ev["title"]), ev["start"][:10], ev.get("region"), (ev.get("locality") or ev.get("location") or "").casefold())
        if key not in seen:
            out.append(ev)
            seen.add(key)
    return sorted(out, key=lambda e: (e["start"], e["title"]))

def update_sources(loaders, cache_dir=CACHE, data_dir=DATA):
    """Tests injizieren Loader; fehlgeschlagene Quelle übernimmt *nur* ihren Cache."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    stat_file = data_dir / "source_status.json"
    status = read_json(stat_file, {})
    all_events = []
    successes = 0
    for key, loader in loaders.items():
        previous = read_json(cache_dir / f"{key}.json", {})
        entry = status.setdefault(key, {})
        entry["lastAttempt"] = stamp()
        try:
            fresh = loader()
            if not isinstance(fresh, list) or not fresh:
                raise SourceError("Quelle lieferte keine verwertbaren Veranstaltungen")
            if any(e.get("sourceKey") != key for e in fresh):
                raise SourceError("Falsche Quellenkennung im Datensatz")
            for e in fresh:
                if not e.get('region'):
                    region, locality = classify_region(e.get('location',''), e.get('title',''))
                    if region:
                        e['region'], e['locality'] = region, locality
                if e.get('region') not in REGIONS or not e.get('start'):
                    raise SourceError("Unvollständige Ortszuordnung – Cache geschützt")
            atomic_json(cache_dir / f"{key}.json", {"lastSuccess": stamp(), "events": fresh})
            entry.update(status="ok", lastSuccess=stamp(), eventCount=len(fresh))
            entry.pop("error", None)
            entry["stale"] = False
            all_events.extend(fresh)
            successes += 1
        except Exception as exc:
            LOG.error("Quelle %s nicht aktualisiert: %s", key, exc)
            old = previous.get("events", [])
            all_events.extend([{**ev, "stale": True} for ev in old])
            entry.update(status="error", error=str(exc)[:350], eventCount=len(old), stale=True)
            if not entry.get("lastSuccess") and previous.get("lastSuccess"):
                entry["lastSuccess"] = previous["lastSuccess"]
    merged = dedupe_cross_sources(all_events)
    now = stamp()
    prior = read_json(data_dir / "events.json", {})
    # lastSuccessfulSync wird nur geändert, wenn wirklich mind. eine Quelle erfolgreich war.
    success_time = now if successes else prior.get("lastSuccessfulSync")
    output = {"generatedAt": now, "lastSuccessfulSync": success_time,
              "sourceStatus": status, "eventCount": len(merged), "events": merged}
    atomic_json(data_dir / "events.json", output)
    atomic_json(stat_file, status)
    return output

def fetch_regional_rlp(session=None):
    try:
        response = fetch(OPEN_RLP, session, timeout=38)
        payload = response.json()
        events = parse_rlp_json(payload, TZ, stable_id, stamp, category, status_from)
    except (ValueError, requests.RequestException) as exc:
        raise SourceError(f"RLP EventJSON: {exc}") from exc
    if not events:raise SourceError("RLP: keine eindeutig zugeordneten Landkreistermine; Cache geschützt")
    return dedupe_exact(events)

def fetch_ramstein(session=None):
    events=parse_ramstein_html(fetch(RAMSTEIN, session).text, TZ, stable_id, stamp, category, status_from)
    if not events:raise SourceError("Ramstein-HTML nicht erkannt oder keine verifizierbaren Termine")
    return dedupe_exact(events)

def fetch_pfalz(session=None):
    events=parse_pfalz_jsonld(fetch(PFALZ, session).text, TZ, stable_id, stamp, category, status_from)
    if not events:raise SourceError("Pfalz.de: keine strukturierten Event-Einträge gefunden")
    return dedupe_exact(events)

def fetch_weilerbach(session=None):
    # 8 jüngste Ausgaben bis einschließlich dieser Woche; keine fest kodierten Event-Daten.
    # Nur explizite, veröffentlichte Kalenderartikel werden ausgelesen.
    current = date.today()
    issue_links=[]
    for back in range(8):
        d=current-timedelta(weeks=back)
        yr,wk,_=d.isocalendar()
        edition=WITTICH_EDITION.format(week=wk,year=yr)
        try:
            issue_links.extend(weilerbach_article_links(fetch(edition,session).text,edition))
        except SourceError as exc:
            LOG.warning("Wittich-Ausgabe nicht abrufbar: %s", exc)
    events=[]
    for url in dict.fromkeys(issue_links):
        try:
            events.extend(parse_weilerbach_article(fetch(url,session).text,url,TZ,stable_id,stamp,category,status_from))
        except (SourceError,ValueError) as exc:
            LOG.warning("Weilerbach-Artikel verworfen: %s", exc)
    if not events:raise SourceError("Keine lesbaren Weilerbacher Veranstaltungskalender-Artikel")
    return dedupe_exact(events)

def main():
    # Jede Quelle einzeln persistent. Bei Fehler wird ihr letzter valider Stand genutzt.
    output = update_sources({"fck": fetch_fck, "city": fetch_city, "sommerswing": fetch_sommerswing,
                             "rlp":fetch_regional_rlp, "ramstein":fetch_ramstein, "pfalz":fetch_pfalz,
                             "weilerbach":fetch_weilerbach})
    LOG.info("%d Veranstaltungen veröffentlicht; Quellenstatus: %s", output["eventCount"], ", ".join(f"{k}={v['status']}" for k,v in output["sourceStatus"].items()))
    # Workflow darf weiterhin Caches veröffentlichen, aber Fehler bleiben sichtbar.
    return 0

if __name__ == "__main__":
    sys.exit(main())

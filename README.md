# KL EventRadar V5 – Getränkedisposition Stadt + Landkreis Kaiserslautern

**Zweck:** öffentlich veröffentlichte FCK-Heimspiele, Kerwen, Stadtfeste, Konzerte und weitere Termine als Orientierung für die Getränkedisposition. **Kein garantiert vollständiger Veranstaltungskalender und keine automatische Absatzprognose.** Eine Veranstaltung kann fehlen, wenn sie nicht veröffentlicht wird, eine Ortsangabe fehlt oder eine Quelle ausfällt.

## Enthaltene Regionen

Die **kreisfreie Stadt Kaiserslautern** plus alle sechs Verbandsgemeinden im Landkreis Kaiserslautern:

| Gebiet | Region-Marker (kleiner Punkt) | Beispiele |
| --- | --- | --- |
| Stadt Kaiserslautern | Lila | Kaiserslautern, Hohenecken, Siegelbach |
| VG Bruchmühlbach-Miesau | Ocker | Bruchmühlbach-Miesau, Lambsborn, Martinshöhe |
| VG Enkenbach-Alsenborn | Petrol | Enkenbach, Alsenborn, Hochspeyer, Mehlingen, Sembach |
| VG Landstuhl | Blau | Landstuhl, Kindsbach, Trippstadt, Queidersbach |
| VG Otterbach-Otterberg | Violett | Otterbach, Otterberg, Katzweiler, Niederkirchen |
| VG Ramstein-Miesenbach | Grün | Ramstein, Hütschenhausen, Steinwenden, Niedermohr |
| VG Weilerbach | Orange | Weilerbach, Rodenbach, Mackenbach, Schwedelbach |

## Filter und Farblogik (Version 5)

**Entscheidende Änderung:** Die **Farbe der Veranstaltung im Kalender** zeigt jetzt die **Veranstaltungsart**. Die **Region** wird als kleiner farbiger Punkt am Kalendereintrag angezeigt; die **Datenquelle** ist separat in der Detailansicht nachvollziehbar. Ein Veranstaltungseintrag aus einer städtischen Website wird nicht allein deshalb der Stadt zugeordnet.

| Farbe der Kalenderkarte | Art | Standardmäßig sichtbar? |
| --- | --- | --- |
| Rot | **Nur nachgewiesene FCK-Heimspiele im Fritz-Walter-Stadion** | Ja |
| Orange | Kerwen / Kirmes | Ja |
| Ocker | Stadt-, Dorf- und Vereinsfeste | Ja |
| Blau | Konzerte / Musik | Ja |
| Türkis | Sonstige Sportveranstaltungen | Ja |
| Grün | Märkte / Messen | Ja |
| Helles Violett | Ausstellungen | Nein |
| Grauviolett | Museumstermine | Nein |
| Violett | Kultur / Theater | Nein |
| Grau | Sonstiges | Nein |

Oben in **„Veranstaltungsarten: 6 von 10“** lässt sich jede Kategorie einzeln **an- oder abwählen**. Mehrere Kategorien können gleichzeitig aktiv sein. **„Für Getränkedisposition“** setzt die sechs üblichen Kategorien; **„Alle“** zeigt auch Museum/Kultur/Ausstellung; **„Keine“** leert die Auswahl. Die Auswahl bleibt im Browser gespeichert. Daneben können Region, Ort, Datenquelle, Kerwe, Stadion und Großveranstaltungen weiter gefiltert werden. Die Sidebar zeigt „X von Y Terminen“; Such- und ICS-Export übernehmen die Filter.

**Hinweis zur Datenqualität:** V5 korrigiert bekannte Fehlzuordnungen bei unklaren Ortsangaben (z. B. „Platz unter den Linden“ ist kein belastbarer Nachweis für die Ortsgemeinde Linden; eine Busabfahrt außerhalb des Landkreises zum Pfalztheater ist kein Vor-Ort-Termin). Allein aus Texten lässt sich die geografische Zuordnung trotzdem nicht in jedem Fall sicher beweisen.

Die vollständige verwaltungsrechtliche Liste der Ortsgemeinden und Ortsteile ist in `scripts/regions.py` hinterlegt. Referenz: https://www.kaiserslautern-kreis.de/landkreis/gemeinden-und-buergermeister/ortsgemeinden/ . Die Zuordnung erfolgt **über Wort- und Ortsnamenvergleich**, nicht über Geocoding: gleichnamige Orte in anderen Landkreisen oder fehlende Ortsangaben können zu Fehlern bzw. ausgelassenen Terminen führen. Quelle vor einer Dispositionsentscheidung öffnen.

## Bestehende V4-GitHub-Seite auf V5 aktualisieren (ohne Datenverlust)

**Für bestehende Repositories bitte das separate `KL_EventRadar_V5_UPDATE_NUR_GEÄNDERTE_DATEIEN.zip` verwenden.** Diese ZIP enthält **kein** `data/` und **keine** `.github/`; dadurch bleiben bereits erfolgreich geladene Live-Events, Quellen-Caches und der eingerichtete automatische Workflow erhalten.

1. ZIP entpacken, **Inhalt** (nicht übergeordneten ZIP-/Projektordner) in `https://github.com/Ettorak321/kl-eventradar` unter **Code → Add file → Upload files** hochladen. Die Ordner `css`, `js`, `scripts` und `tests` müssen erhalten bleiben; gleichnamige Dateien werden aktualisiert. Zur Vermeidung des bereits aufgetretenen Doppelordners nur den *Inhalt* ziehen.
2. Unten **Commit changes** klicken. Anschließend unter **Actions → KL EventRadar Daten aktualisieren → Run workflow** starten, damit auch zuvor zwischengespeicherte Events die neue Kategorie erhalten und geografische Regeln genutzt werden.
3. GitHub Pages öffnen: `https://ettorak321.github.io/kl-eventradar/`; Browser ggf. mit **Strg+F5** neu laden. Oben **Veranstaltungsarten** öffnen und mehrere Häkchen setzen. Bei „Nur Stadion“ und „Nur Kerwen“ wird die entsprechende Kategorie gegebenenfalls automatisch aktiviert.
4. Kontrollieren: FCK-Heimspiel **rote Karte**, Kerwe **orange Karte**, Region **kleiner Farbpunkt**; Kultur/Museen/Ausstellungen standardmäßig nicht sichtbar. Datenquelle im Veranstaltungs-Detailfenster kontrollieren.

**Die Website veröffentlicht keine neuen Daten, solange der Parser seine Quelle nicht erreicht.** Ein grüner Action-Haken beweist nur den technischen Ablauf, nicht die Vollständigkeit aller Veranstaltungen. Wenn bestimmte Termine trotz aktivierter Kategorien fehlen, `data/source_status.json`, Quelle und Actions-Log prüfen.

## Installation auf GitHub Pages (neues Repository)

1. ZIP-Datei entpacken. **Den Inhalt des Ordners `kl-eventradar`** in ein neues GitHub-Repository gleichen Namens hochladen. Die Ordner `.github`, `data`, `scripts`, `js`, `css`, `tests` müssen erhalten bleiben. Beim Upload über den Browser die Pfade prüfen; `.github` darf nicht fehlen.
2. In GitHub unter **Settings → Actions → General → Workflow permissions** `Read and write permissions` für Actions zulassen. Bei Organisationsrichtlinien kann eine abweichende Einrichtung nötig sein.
3. Unter **Actions → KL EventRadar Daten aktualisieren → Run workflow** den ersten Lauf starten.
4. In **Actions → letzter Lauf → Quellen abgleichen** die Fehlermeldungen prüfen. `data/source_status.json` zeigt je Quelle `ok` oder `error`, Zeitpunkt des letzten erfolgreichen Abrufs und Anzahl der übernommenen Termine. Ein fehlgeschlagener Abruf behält den alten Quellen-Cache, sofern er existiert.
5. Unter **Settings → Pages → Build and deployment → Source: Deploy from a branch → Branch `main`, Ordner `/(root)`** aktivieren. Anschließend wird die Adresse `https://BENUTZERNAME.github.io/kl-eventradar/` angezeigt (bei anderem Repository-Namen entsprechend anpassen).
6. Kalender öffnen, oben nach Region filtern (z. B. **VG Weilerbach**) und **Nur Kerwen** aktivieren. Bei Problemen zuerst **Datenquellen** und die Action-Logs prüfen.

Die Action ist auf ungefähr **alle sechs Stunden** terminiert; GitHub kann planmäßige Läufe verzögern. Der Button „Daten neu laden“ lädt die vorhandene JSON erneut, er startet keine GitHub Action. Nach dem ersten erfolgreichen Lauf sollte `data/events.json` Ereignisse enthalten. **Vor dem ersten Import ist die Datei absichtlich leer** und die Benutzeroberfläche zeigt Warnungen, keine erfundenen Termine.

## Lokal auf Windows testen – GitHub ist dafür nicht erforderlich

Python von https://www.python.org/downloads/ installieren, ZIP entpacken, im Ordner `kl-eventradar` im Explorer in der Adressleiste `cmd` eintippen, anschließend:

```bat
py -m pip install -r scripts/requirements.txt
py -m unittest discover -s tests -p "test_*.py" -v
py scripts/fetch_events.py
py -m http.server 8000
```

Jetzt im Browser `http://localhost:8000` öffnen. Ohne Internet können die Abrufe fehlschlagen und FullCalendar vom CDN nicht geladen werden. Für einen reinen Funktionstest der Kalenderoberfläche genügt ein lokaler Webserver; für echte Termine muss mindestens eine Quelle erfolgreich sein. `index.html` per Doppelklick (`file://`) zu öffnen ist wegen der JSON-Laderegeln nicht zuverlässig.

macOS/Linux: meist `python3` statt `py`. Node.js ist nur für die zusätzlichen ICS-Tests nötig (`node --test tests/test_ics.cjs`), nicht zum Betrieb der Website.

## Datenquellen und technische Grenzen

| Quelle / Schlüssel | Öffentliche Website | Automatische Importstrategie | Live-Status zum Erstellzeitpunkt |
| --- | --- | --- | --- |
| `fck` | https://fck.de/kalender/ | offizieller Profi-ICS, ggf. externer Feed, nur ausdrücklich verifiziertes Fritz-Walter-Stadion | **nicht live ausführbar** |
| `city` | https://kaiserslautern.de/tourismus_freizeit_kultur/veranstaltungen/index.html.de | alle bestätigten Paginierungsseiten; eindeutig städtische Einträge | **nicht live ausführbar** |
| `sommerswing` | https://sommerswing.de/bands.html | explizite Programmtermine; keine wöchentlichen Schätzungen | **nicht live ausführbar** |
| `rlp` | https://open-rlp.egovernor.de/metaData/event/data | offenes EventJSON aus Rheinland-Pfalz, Ort auf sechs VGs und Stadt filtern | **Endpunkt hier nicht erreichbar/verifizierbar** |
| `ramstein` | https://www.ramstein-miesenbach.de/de/kultur-freizeit/veranstaltungskalender/ | veröffentlichte HTML-Kalendertabellen, konkrete Orte | **HTML-Struktur nicht live geprüft** |
| `pfalz` | https://www.pfalz.de/de/veranstaltungen-im-landkreis-kaiserslautern | strukturierte `schema.org/Event`-Einträge, falls vorhanden | **JSON-LD-Verfügbarkeit nicht verifiziert** |
| `weilerbach` | https://ol.wittich.de/titel/798 | Amtsblatt: jüngste Ausgaben durchsuchen, eindeutig erkannte Weilerbacher Monatskalender mit Zeilen und veröffentlichten Kerwetagen übernehmen | **Artikellayout nicht live geprüft** |

Die RLP-OpenData-Schnittstelle ist eine **mögliche, aber nicht garantierte** überregionale Quelle. Manche Verbandsgemeinden haben keinen offenen Maschinenfeed oder führen ihre Veranstaltungen stattdessen in der „meinOrt“-App. Deshalb ist die **geografische Abdeckung der Filter vollständig**, die **Veranstaltungsabdeckung jedoch nicht**. Die VGs Bruchmühlbach-Miesau, Enkenbach-Alsenborn, Landstuhl und Otterbach-Otterberg hängen derzeit wesentlich von RLP-/Pfalz-Einträgen ab. Der statusabhängige Rückfall auf ältere Daten darf nicht als aktuelle Prüfung verstanden werden.

**Besondere Fallstricke:** `rlp` ordnet Ortsnamen heuristisch zu; gleichnamige Orte anderswo in Rheinland-Pfalz sind nicht vollständig auszuschließen. Mehrtägige Termine verwenden intern exklusives `end`, sodass die letzte Veranstaltungstag im Kalender korrekt erscheint. Unbekannte Uhrzeiten werden als ganztägig angezeigt, aber das heißt nicht zwingend „ganztägiger Betrieb“. Veranstaltungsabsagen, geänderte Kickoff-Zeiten und kurzfristige Kerwetermine unbedingt beim Veranstalter gegenprüfen. Keine garantierten Besucherzahlen oder Getränkemengen.

Wenn ein Parser eine unerwartete Seitenstruktur oder null verwertbare Termine erkennt, wird `error` angezeigt und sein **alter individueller Cache** bleibt erhalten. Bei einem vollständigen Erfolg kann eine Veranstaltung aus dem alten Cache entfallen, z. B. weil sie nicht mehr auf der Quellseite steht; das wird **nicht automatisch als Absage** gewertet.

## Eigene Termine und Kollegen

`+ Eigener Termin` erlaubt Anlegen, Bearbeiten und Löschen mit freier Ortsangabe und expliziter Auswahl der Region. Diese Termine verbleiben nur im `localStorage` des **jeweiligen Browsers** und werden **nicht** in GitHub oder auf andere PCs synchronisiert. „Fußball“ als eigener Termin ist **keine nachgewiesene Stadionbelegung**. Der ICS-Export berücksichtigt die gesetzten Filter und korrekte Zeitzonen für Terminbeginn. Für betriebsweit gemeinsame Zusatztermine wäre später eine getrennte, zentral gepflegte Datenquelle nötig.

## Tests / Fehlerbehebung

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/test_ics.cjs
node --check js/app.js
```

Der ZIP-Inhalt enthält `TESTBERICHT.md` mit tatsächlich durchgeführten Tests und nicht verifizierbaren Teilen.

- **Kalender bleibt leer:** erster Import nicht erfolgreich; `data/events.json` und GitHub-Action-Log prüfen.
- **Quelle zeigt Fehler:** Daten nicht aktuell bestätigt, auch wenn ein alter Cache angezeigt wird. Nicht als „kein Event“ interpretieren.
- **Kerwe in Weilerbach fehlt:** nach „VG Weilerbach“ und „Nur Kerwen“ filtern; Quellartikel prüfen. Bei fehlendem Eintrag unter „+ Eigener Termin“ erfassen (nur auf diesem Gerät sichtbar).
- **Kein FCK-Spiel:** nur klar nachgewiesene Heimspiele werden aufgenommen. Der ICS-Kalender kann ohne Spielort unvollständig sein.
- **Kalendarische Anzeige fehlt:** CDN-Zugriff auf FullCalendar prüfen, Browser-Konsole öffnen.
- **Auswärtsspiele:** dürfen niemals als Stadionbelegung markiert sein. Offizielle Spielstätte gegenprüfen.

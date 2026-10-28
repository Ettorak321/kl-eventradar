# KL EventRadar V6 – Veranstaltungskalender Stadt und Landkreis Kaiserslautern

Öffentliche Übersicht der FCK-Heimspiele, Kerwen, Feste, Konzerte, Märkte und weiterer Veranstaltungen.

## Kerwe-Vorschau 2027 bis 2030

V6 erzeugt **unverbindliche Vorschauen** aus hinterlegten historischen Mustern. Aktuell sind nur drei Regeln dokumentiert: Rodenbach (erster Septembersonntag), Mackenbach (üblicherweise zweiter Septembersonntag; 2024 abweichend) und Weilerbach (vierter Septembersonntag). Historische Links und genaue Parameter liegen in `data/kerwe_rules.json`. Fehlende Ortsregeln werden nicht geschätzt.

Gestrichelte Karten mit „Prognose“ sind **keine offiziellen Termine**. Die berechneten Zeiträume sind Freitag bis Montag; die tatsächliche Veranstaltungsdauer kann abweichen. Sobald ein veröffentlichter Kerwetermin für die jeweilige Ortsgemeinde und das jeweilige Jahr vorliegt, unterdrückt er die Vorschau, auch bei einem anderen Datum.

## Bedienung

Die Veranstaltungskategorien lassen sich mehrfach auswählen. Über den neuen Terminstatus-Filter kannst du nur veröffentlichte Termine oder nur Kerwe-Prognosen anzeigen. Veranstaltungstypen besitzen eigene Farben, die Region wird als kleiner Farbpunkt angezeigt. Historische Quellen werden im Detailfenster verlinkt.

## Installation

Repository: https://github.com/Ettorak321/kl-eventradar

1. Unter **Settings → Pages** die Veröffentlichung aus `main` und `/(root)` aktivieren.
2. Unter **Actions → KL EventRadar Daten aktualisieren** den Workflow ausführen.
3. Den Kalender unter https://ettorak321.github.io/kl-eventradar/ öffnen und gegebenenfalls den Browser-Cache aktualisieren.

## Tests und lokaler Betrieb

```bash
python -m pip install -r scripts/requirements.txt
python -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.cjs
python scripts/fetch_events.py
python -m http.server 8000
```

Der Kalender steht anschließend unter http://localhost:8000/ zur Verfügung. Eine reine `file://`-Öffnung kann wegen des JSON-Abrufs scheitern.

## Einschränkungen

Kerwe-Vorschauen sind historisch abgeleitet und können falsch sein; maßgeblich sind offizielle Veröffentlichungen. Einige regionale Quellen können ausfallen. Der Quellenstatus zeigt solche Fehler an und getrennte Daten-Caches schützen bisherige Einträge. Die Stadionübersicht ist kein vollständiger interner Belegungsplan. Eigene Termine verbleiben im jeweiligen Browser.

## Projektstruktur

- `scripts/fetch_events.py`: Datenabrufe und Quellen-Caches
- `scripts/kerwe_predictions.py`: Prognoseberechnung und Unterdrückung durch Veröffentlichungen
- `data/kerwe_rules.json`: belegte Wiederholungsregeln
- `data/events.json`: veröffentlichter Datenstand einschließlich Prognosen
- `js/app.js`, `js/taxonomy.js`, `css/style.css`, `index.html`: Kalenderdarstellung
- `tests/`: Regressionstests
- `.github/workflows/update-events.yml`: Tests und Aktualisierung

## FCK-Auswärtsspiele (V7)

Der Profi-Kalender importiert nun Heimspiele (rot, nur mit nachgewiesenem Fritz-Walter-Stadion) und eindeutige FCK-Auswärtsspiele (kupferfarben). Auswärtsspiele werden niemals als lokale Stadionbelegung behandelt und können getrennt gefiltert werden. Der Spielort außerhalb des Landkreises ist eine Information zur Begegnung, kein regionaler Veranstaltungsort. Ob ein Lokal die Übertragung zeigt, wird nicht behauptet.

**Datenstand prüfen** lädt die bereits veröffentlichte `events.json` erneut. **Quellenabruf starten** öffnet den GitHub-Actions-Workflow; dort können angemeldete Berechtigte mit „Run workflow“ einen neuen Abruf auslösen. Eine öffentliche GitHub-Pages-Seite darf nicht ohne Authentisierung Schreibaktionen ausführen. Automatische Abrufe laufen weiterhin ungefähr alle sechs Stunden.

## Feiertage und besondere Anlässe (V8)

KL EventRadar berechnet jährlich **alle 11 gesetzlichen Feiertage Rheinland-Pfalz** und gesondert besondere Kalenderanlässe für das aktuelle Jahr sowie fünf Folgejahre. Eingeschlossen sind unter anderem St. Patrick's Day (17. März), Halloween (31. Oktober), Silvester (31. Dezember), Valentinstag, Weiberfastnacht, Rosenmontag, Fastnachtsdienstag, Aschermittwoch, Ostersonntag, Tanz in den Mai, Muttertag, Pfingstsonntag, Martinstag, Beginn der Fastnachtssaison, Nikolaustag und Heiligabend.

Im Kategorienfilter stehen **Gesetzliche Feiertage (RLP)** und **Besondere Anlässe** getrennt zur Verfügung. Die Angaben gelten unabhängig von der gewählten Verbandsgemeinde und werden aus Kalenderregeln berechnet; **sie sind keine offiziellen Veranstaltungsankündigungen**. Vorhandene Quellen-Caches bleiben unberührt. Bestehende Filterprofile werden einmalig ergänzt; eine bewusst leere Auswahl bleibt leer.

Gesetzliche Feiertage beruhen auf der Liste des Ministeriums des Innern und für Sport Rheinland-Pfalz: https://mdi.rlp.de/themen/buerger-und-staat/verfassung-und-verwaltung/sonn-und-feiertagsrecht

Bewegliche Feiertage basieren auf dem gregorianischen Ostertermin, Muttertag auf dem zweiten Sonntag im Mai. Schulferien, ortsspezifische Feste und nicht verifizierte Veranstaltungsreihen werden dadurch nicht automatisch erzeugt. Keine Aussagen über Besucherzahlen oder wirtschaftliche Auswirkungen.

Weitere feste oder regelbasierte Kalendertage: Black Friday (Freitag nach dem vierten Donnerstag im November) sowie die vier Adventssonntage. Diese sind keine gesetzlichen Feiertage. Der Statusfilter „Nur veröffentlichte Veranstaltungen“ blendet berechnete Kalendertage ebenso aus wie Kerwe-Vorschauen.

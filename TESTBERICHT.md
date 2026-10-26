# KL EventRadar V4 – Testbericht

Stand: 22. Oktober 2026

## Offline tatsächlich ausgeführt

- `python -m unittest discover -s tests -p 'test_*.py' -q` – **29 von 29 Tests erfolgreich**.
- `node --test tests/test_ics.cjs` – **5 von 5 Tests erfolgreich**.
- `node --check js/app.js`, `node --check js/ics.js` – **Syntaxprüfungen erfolgreich**.
- `python -m py_compile scripts/*.py` – **erfolgreich**.

Die Python-Tests prüfen Auswärtsspiele, sichere Stadionzuordnung, Zeitzonen, Stadt-Paginierung, Sommerswing, quellenspezifischen Cache, alle sechs VGs + Stadt, wichtige Ortsteile, Kerwe-Datumsspannen, Abgrenzung von Kusel und Beispielstrukturen der neu eingebundenen Quellen. Die Node-Tests prüfen RFC-5545-/ICS-Export, UTC, mehrtägige Ganztagstermine und Zeilenfaltung.

## Nicht erfolgreich live verifiziert

- **Externe Netzaufrufe:** Die Containerlaufzeit konnte `open-rlp.egovernor.de`, `ramstein-miesenbach.de`, `pfalz.de` und `kaiserslautern.de` nicht per DNS auflösen. Dies verhindert einen echten Import-Durchlauf über `requests`. Der öffentliche RLP-Endpunkt war auch über das Web-Lesewerkzeug nicht zugänglich.
- **Live-HTML-Adapter:** Ramstein-Miesenbach, Weilerbach-Amtsblatt und Pfalz-JSON-LD wurden nur gegen eigens angelegte Testfixtures geprüft, nicht gegen echte heruntergeladene HTML-Quellbytes. Sie können bis zu Anpassungen Warnungen liefern.
- **Browser-End-to-End-Test mit FullCalendar:** Kein vollständig bestätigter browserseitiger Test gegen einen öffentlich deployten GitHub-Pages-Stand. Der lokale Browser benötigt Zugriff auf das externe FullCalendar-CDN.
- **Echte aktuelle Termine:** Die ausgelieferte `data/events.json` ist absichtlich **leer**, um keine ungesicherten Veranstaltungstermine vorzutäuschen. Echte FCK-Spiele, Weilerbacher Kerwen und sonstige Kreis-Termine erscheinen erst nach einem erfolgreichen GitHub-Actions-Quellenabgleich.

## Abnahme auf GitHub Pages

1. Action `Run workflow` erfolgreich starten; `source_status.json` kontrollieren.
2. Einen FCK-Heimspieltag und einen dokumentierten Spielort manuell anhand `fck.de` gegenprüfen.
3. Einen veröffentlichten Kerwetermin in Weilerbach oder Rodenbach mit einem Amtsblatt vergleichen.
4. Alle sieben Regionsfilter öffnen und auf ungeklärte Quellenhinweise achten.
5. Datum, Zeitzone und ICS-Export mit einem echten Termin prüfen.

**Fachliches Fazit:** Geografische Auswahl und Farblogik sind implementiert und automatisiert geprüft. Vollständigkeit, Aktualität und Betriebssicherheit für die Getränkedisposition sind nicht ohne realen Testlauf bei erreichbaren Kommunalquellen belegbar.

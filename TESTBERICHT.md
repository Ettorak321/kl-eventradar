# KL EventRadar V5 – Testbericht (26.10.2026)

## Tatsächlich lokal ausgeführte Prüfungen

- `python -m unittest discover -s tests -p 'test_*.py' -v`: **34 Tests bestanden**.
- `node --test tests/test_ics.cjs`: **11 Tests bestanden**, inklusive V5-Veranstaltungskategorien.
- `node --check js/app.js` und `node --check js/taxonomy.js`: **Syntaxprüfungen bestanden**.
- Testfälle: FCK nur bei verifiziertem Heimspiel, Kerwe aus Veranstaltungstitel statt Region, mehrere Eventtypen gleichzeitig, Kultur/Museum/Ausstellung standardmäßig verborgen und wieder aktivierbar, manuelle Veranstaltungstypen, bestehende Quellen-Caches, ICS-Zeitformate, Mehrtageskalender, geografische Zuordnung und Problemfälle wie "Platz unter den Linden" oder Theaterbus-Abfahrten außerhalb der Stadt.

## Nicht als bestanden ausgewiesen

- **Kein echter Browser-End-to-End-Test**: In dieser Laufzeit fehlt die installierte Chromium-Browser-Binärdatei. Die FullCalendar-Darstellung (insbesondere das farbige Event im tatsächlichen Tagesraster) konnte daher hier nicht visuell bestätigt werden. CSS/JS sind für Monats-, Wochen- und Listenansicht explizit gesetzt, tatsächliches Rendering nach GitHub Pages Upload prüfen.
- **Kein vollständiger Live-Parser-Durchlauf**: DNS/Netzwerkzugriff dieser Laufzeit ist eingeschränkt. Der öffentlich auslesbare GitHub-Rohdatensatz wurde extern auf Beispiele für mögliche Falschzuordnungen geprüft, aber neue Live-Abfragen der Eventquellen konnten hier nicht durchgeführt werden.
- **Kein Beleg, dass alle Veranstaltungsorte korrekt zugeordnet sind**: Der reine Textvergleich bleibt bei manchen Ortsnamen mehrdeutig. Die geänderten Regeln beheben einzelne nachgewiesene Ursachen; sie machen daraus kein geographisches Nachschlagewerk.
- **Keine Absatzprognose** und keine garantierte Vollständigkeit der FCK- und Gemeindequellen.

## Besonderheiten bei GitHub-Updates

Die separate Update-ZIP enthält **weder `data/events.json` noch `data/cache/`, `data/source_status.json` oder `.github/workflows/`**. Bestehende Live-Veranstaltungen und der eingerichtete Workflow bleiben beim Aktualisieren des GitHub-Repositories erhalten. Nach dem Upload GitHub Action manuell ausführen; alte Cache-Einträge werden beim Abgleich neu typisiert. Wenn eine Quelle ausfällt, bleiben ihre alten Daten erhalten und können damit weiterhin falsch zugeordnet sein – die Quellenwarnung beachten.

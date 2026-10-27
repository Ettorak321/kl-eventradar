# KL EventRadar V5 – Installation der Korrektur im bestehenden GitHub-Projekt

**Diese UPDATE-ZIP überschreibt KEINE Veranstaltungsdaten.** Die Ordner `data/` und `.github/` sind bewusst nicht enthalten.

1. ZIP unter Windows mit Rechtsklick → **Alle extrahieren** entpacken.
2. **GitHub-Repository öffnen:** https://github.com/Ettorak321/kl-eventradar
3. **Code → Add file → Upload files** anklicken. Im Explorer **den Inhalt des entpackten Update-Ordners** auswählen und per Drag-and-drop hochladen. Wichtig: **nicht den Update-Ordner selbst** hochladen, sonst entsteht wieder eine falsche Unterordnerebene.
4. Es müssen **index.html direkt im Hauptverzeichnis** und `css/style.css`, `js/app.js`, `js/taxonomy.js`, `scripts/*.py` sowie `tests/*.py`/`*.cjs` in ihren jeweiligen Ordnern landen.
5. **Commit changes** unten anklicken.
6. **Actions → KL EventRadar Daten aktualisieren → Run workflow** starten. Bei grüner Anzeige Quellenstatus und Zahl der Events prüfen.
7. Website öffnen: https://ettorak321.github.io/kl-eventradar/ und bei Bedarf mit **Strg+F5** aktualisieren.
8. Oben auf **Veranstaltungsarten** klicken, mehrere Kategorien anhaken. Die Standardeinstellung ist für die Getränkedisposition optimiert; Kultur, Museen und Ausstellungen sind anfangs ausgeblendet. **Alle** blendet sie wieder ein.
9. Farbprüfung: **FCK-Heimspiel rot**, **Kerwe orange**, Stadtfest ocker, Konzert blau, Markt grün. Der **kleine zusätzliche Punkt** kennzeichnet die Region, die Datenquelle wird in den Veranstaltungsdetails angegeben.

**Achtung:** Frühere fehlerhafte Ortszuordnungen können aus dem bisherigen Cache stammen. Der nächste erfolgreiche Datenabruf ersetzt die betroffenen Quelldaten. Bei einem Quellenfehler bleibt der letzte bekannte Stand sichtbar, kann aber weiterhin ungenau sein. Fehlende oder verschobene Termine immer beim Veranstalter gegenprüfen.

**Tests:** `python -m unittest discover -s tests -p "test_*.py" -v` und `node --test tests/test_ics.cjs`. Browser-End-to-End-Test nicht durchgeführt, da in der Erstellungsumgebung kein Chromium-Browser installiert ist; Live-Datenimport nicht durchgängig verifiziert.

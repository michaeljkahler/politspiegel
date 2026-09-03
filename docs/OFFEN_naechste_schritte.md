# Offene Punkte

Stand 3. September 2026, nachgeführt.

---

## Erledigt am 3. September 2026: Umbau auf drei Ebenen

- **Namensraum.** Politspiegel (Dach, `/`), Kantonsratsspiegel (vorher «Abstimmungsspiegel
  Kantonsrat», `/kantonsrat/`), Abstimmungsspiegel (vorher «Argumentespiegel»,
  `/abstimmung/<slug>/`). Ordner `argumentespiegel/` heisst jetzt `abstimmungsspiegel/`.
- **Repository umbenannt** auf `politspiegel`; Adresse
  `https://michaeljkahler.github.io/politspiegel/`. Fernadresse ohne Token, das Token geht
  nur noch an den Push-Befehl.
- **`.gitignore` repariert.** Eine Regel schloss fünf der acht Grafiken aus, die die
  Verkehrsfluss-Seite einbindet; die Bilder wären online kaputt gewesen. Verwaiste Grafiken
  räumt `argumente.py` selbst. Von den 45 MB des Abstimmungsordners gehen 6 MB ins
  Repository: Vorlage, Docs, Skripte, die Datenkette von roh bis freigegeben, die SVGs.
- **Übersicht aus den Vorlagen.** `politspiegel/bauen.py` liest `abstimmungen/*/vorlage.json`
  statt einer Handliste; kommend als Kasten, vergangen als Liste mit nachgetragenem
  Ergebnis (Felder `status` und `ergebnis`, Schema in `abstimmungsspiegel/docs/14_TECHNIK.md`).
- **Bilder für Social Media im Abstimmungsspiegel**, `bausteine/teilen.py`: Vorlage,
  Gegenüberstellung, Aussagenpaare, Kantonsrat, und je Argument ein Karussell mit allen
  Inhalten der Karte. Letzte Folie immer die Gegenseite.
- **Vorschauangaben** (og-Tags, Beschreibung, Zeichen) auch auf den Abstimmungsseiten.

## Erledigt am 2. September 2026

- **Formfilter als Mehrfachauswahl**, Kästchen statt Auswahlfeld, mit Zähler je Form.
- **Bilder der Ratsmitglieder** in Tabelle, Profil und Ranglisten, mit Ring in der
  Parteifarbe, damit die Parteizuordnung auf einen Blick erhalten bleibt.
- **Verknüpfung mit dem Wortprotokoll** bei jedem Abstimmungstitel, in den Rubriken
  Abstimmungen und Themen sowie bei jeder Einzelstimme im Mitgliederprofil.
- **Ranglisten führen ins Profil.**
- **Handelsregisterangaben** aus `data/interessen_pruefung.json` im Infokasten des
  Beziehungsnetzes.
- **Zitate nur paarweise.** Steht nur eine Seite zur Verfügung, bleiben beide Felder leer.
  Von 72 Fragen tragen 2 ein Zitatpaar.
- **Alle 72 Fragetexte geschrieben.** `data/frage_texte.json` deckt die Fragenliste
  vollständig ab, keine Karte zeigt mehr den blossen Betreff des Geschäfts.
- **Fragenauswahl repariert.** Mindesttrennschärfe, Ringverfahren je Vorlage, Motionen und
  Postulate zugelassen, weitere Verfahrensfragen und Dubletten ausgeschlossen. Einzelheiten
  im Anhang von `docs/UEBERGABE_betrieb-und-hosting.md`.
- **Ausgabeordner aufgeräumt**, nur noch `output/dashboard.html`.
- **Wiederkehrender Auftrag angepasst**, ruft `build3.py` und führt die Fragetexte nach.

---

## 1 · Schlagworte gegen das Protokoll prüfen

Noch offen, und seit dieser Runde grösser als gedacht. Entschieden ist das Vorgehen: Abgleich
gegen den **Debattentext des Geschäfts**, nicht nur gegen den Geschäftstitel. Ergibt eine
Plausibilitätsprüfung mit Trefferquote je Schlagwort; Widersprüche kommen auf eine Prüfliste,
analog zur Umkehrprüfung.

Beim Schreiben der Fragetexte sind offensichtlich falsche Zuordnungen aufgefallen: eine
Deckelung der Kosten für Spezialdienste ist mit «Gewässer» verschlagwortet, ein Antrag zum
Sozialamt mit «Waffen und Gewalt», eine Frage zum Verkehrstarif mit «Klima und Natur».

**Neu dazu:** Die Prüfung sollte auch vergleichen, ob **Titel und Stimmenverhältnis**
zusammenpassen. Bei zwei Abstimmungen der Budgetsitzung vom 17.11.2025 sind sie
gegeneinander verschoben; beide sind darum aus dem Matching ausgeschlossen. Wie oft das sonst
vorkommt, ist unbekannt, weil bisher nur die Umkehrabstimmungen am Protokoll geprüft wurden.

---

## 2 · Social-Media-Bilder im Kantonsratsspiegel ausbauen

Noch offen. Beschlossen sind drei neue Motive:

- **Mein Ergebnis: Fraktionen**, die eigene Übereinstimmung als Balken, mit Anzahl
  beantworteter Fragen
- **Mein Ergebnis: Top-Ratsmitglieder**, die fünf höchsten Übereinstimmungen mit Porträt
- **Einzelnes Ratsmitglied**, Profilkarte mit Porträt, Zustimmungsquote, Präsenz und
  Themenschwerpunkten

Alle im Hochformat 1080 × 1350, wie die vier bestehenden Motive.

---

## 3 · Veröffentlichen

Der Auftrag dafür steht in `docs/UEBERGABE_betrieb-und-hosting.md`, Teil 2. Kurz: eigene
Domain statt `github.io`, die Datei heisst im Netz `index.html`, Vorschaubild und Favicon
ergänzen, und vor dem Aufschalten Impressum, Quellenangabe, Lizenzhinweis für die
Parteifarben und einen Datenschutzhinweis einbauen.

---

## Nicht vergessen

- `output/dashboard.html` ist die einzige gültige Ausgabe, erzeugt von `scripts/build3.py`.
  `build2.py` und `matching.py` sind abgelöst und liegen nur noch als Rückfallebene im
  Ordner. Sie können gelöscht werden, sobald build3 zwei, drei Läufe des wiederkehrenden
  Auftrags ohne Beanstandung überstanden hat.
- Die Abstimmungsliste zeigt höchstens 120 Karten auf einmal.
- Für die Sitzung vom 24.08.2026 liegt noch kein Wortprotokoll vor. Das ist normal,
  Protokolle erscheinen mit Verzögerung. Sobald es da ist, klärt ein erneuter Lauf von
  `umkehr_regeln.py` die fünf offenen Umkehrfälle dieser Sitzung.
- Die Fragenauswahl hängt an der Trennschärfe und verschiebt sich mit jeder neuen Sitzung.
  Nach jedem Lauf prüfen, ob Fragen ohne handgeschriebenen Text dazugekommen sind; `build3.py`
  meldet die Zahl.

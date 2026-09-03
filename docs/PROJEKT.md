# Kantonsrat Schaffhausen: Abstimmungsdashboard

Übergabe-Dokumentation für die Weiterarbeit (z. B. in Claude Cowork).
Stand: Juli 2026 (Projekt in Ordnerstruktur `scripts/`, `data/`, `output/`, `docs/` überführt)

> **Nachtrag 3. September 2026.** Das Projekt heisst jetzt **Politspiegel Schaffhausen**
> und hat drei Ebenen: die Übersicht (`politspiegel/`), den **Kantonsratsspiegel** (dieses
> Dashboard, Generator `scripts/build3.py`, veröffentlicht unter `/kantonsrat/`) und den
> **Abstimmungsspiegel** (`abstimmungsspiegel/`, je kantonale Vorlage eine Seite unter
> `/abstimmung/<slug>/`). Einstieg für den Betrieb: `docs/UEBERGABE_betrieb-und-hosting.md`
> und `docs/OFFEN_naechste_schritte.md`; für den Abstimmungsspiegel
> `abstimmungsspiegel/docs/00_UEBERSICHT.md`. Was unten steht, beschreibt den
> Kantonsratsspiegel und ist in Teilen älter (build2 ist durch build3 abgelöst).

---

## 1. Ziel und Zielgruppe

Ein öffentliches Dashboard, das alle namentlichen Abstimmungen des Kantonsrats
Schaffhausen visuell und verständlich aufbereitet. Zielgruppe ist die **breite
Bevölkerung**, nicht Fachpublikum. Geplantes Hosting: WordPress-Website.

Vorbild für die Idee war smartvote.ch, mit einem entscheidenden Unterschied:
Smartvote misst *Positionen* aus einem Fragebogen, dieses Dashboard misst
*tatsächliches Abstimmungsverhalten*.

## 2. Grundprinzipien (wichtig, bitte einhalten)

- **Keine politische Wertung.** Das Dashboard beschreibt Verhalten, es bewertet
  es nicht. Es gibt bewusst keine Links-Rechts-Achse und keine Aussage, ob eine
  Stimme "gut" oder "richtig" war.
- **Themen-Zuordnung braucht menschliche Freigabe.** Die Zuordnung von
  Geschäften zu Themengruppen wird automatisch *vorgeschlagen*, aber vom
  Menschen geprüft. Keine automatische Blackbox.
- **Quoten immer relativ.** Präsenz, Ja-, Nein- und Enthaltungsquoten werden je
  Person relativ zu den Sitzungen berechnet, an denen sie tatsächlich im Rat
  war. Sonst würden Nachrücker als "Abwesenheitskönige" erscheinen.
- **Nur amtierende Mitglieder in Ranglisten**, damit ausgeschiedene Personen die
  Auswertung nicht verzerren.

## 3. Ordnerstruktur

```
Kantonsratsdashboard/
├── scripts/   scraper.py, themen.py, umkehr.py, build2.py   (die Pipeline)
├── data/      all_sessions.json, themen_zuordnung.json, umkehr_zuordnung.json, themen_pruefung.xlsx
│   ├── raw/         heruntergeladene Abstimmungs-xlsx (legt der Scraper an)
│   └── protokolle/  heruntergeladene Wortprotokoll-PDFs (legt der Scraper an)
├── output/    kantonsrat-dashboard.html          (das fertige Dashboard)
├── docs/      PROJEKT.md, KONZEPT_waehler-matching.md, GLOSSAR_und_quellen.md
└── archiv/    kantonsrat-projekt.zip              (Original-Paket, unverändert)
```

Die Skripte finden ihre Ein- und Ausgaben selbständig relativ zum Skriptstandort
(`Path(__file__)`), lassen sich also aus jedem Verzeichnis starten. Empfohlen ist
der Aufruf aus der Projektwurzel, z. B. `python3 scripts/build2.py`.

## 4. Architektur (drei Teile)

### a) `scraper.py`: Datenbeschaffung
Holt die Abstimmungs-Excel automatisch von sh.ch (Ablage in `data/raw/`) und die
Wortprotokolle als PDF (Ablage in `data/protokolle/`), und schreibt das
konsolidierte `data/all_sessions.json`.

Ablauf: Übersichtsseite öffnen, über die Jahres-Reiter (JS-Filter) iterieren,
aus jeder Sitzungskachel die `contentid` lesen, daraus deterministisch die
Detailseiten-URL bauen, dort die Datei-Links einsammeln, nur Dateien mit
"Abstimmungsergebnis" im Namen und Endung `.xlsx` laden, parsen.

Konfiguration: die Liste `JAHRE` oben im Skript steuert, welche Jahrgänge
gescraped werden. Aktuell `["2026","2025","2024"]`. Mehr Jahre bedeuten längere
Laufzeit (der Vollausbau über 9 Jahre lief in ein Timeout).

Ausführen: `python3 scripts/scraper.py`
Braucht: `playwright` (+ `python3 -m playwright install chromium`), `openpyxl`, `requests`

### b) `themen.py`: thematische Zuordnung
Ordnet jedes Geschäft einer der 9 Hauptgruppen der Schaffhauser Rechtssammlung
zu (rechtsbuch.sh.ch), anhand gewichteter Stichwörter im Geschäftstitel.

- `python3 scripts/themen.py` erzeugt/aktualisiert `data/themen_zuordnung.json`.
  Bereits geprüfte Einträge (`"geprüft": true`) bleiben erhalten, neue Geschäfte
  kommen mit automatischem Vorschlag dazu.
- Prüfung durch den Menschen (Korrektur der Gruppe, dann `geprüft: true`).
- `python3 scripts/themen.py --apply` schreibt die Tags in `data/all_sessions.json`.

**Achtung bei der Excel-Prüftabelle:** Bei der Erstellung eines Dropdowns dürfen
die Optionen keine Kommas enthalten, sonst zerhackt Excel sie. Die Gruppennamen
enthalten Kommas, besser die Gruppennummer als Dropdown-Wert nehmen.

### c) `build2.py`: Dashboard-Generator
Liest `data/all_sessions.json` und schreibt das fertige, eigenständige
`output/kantonsrat-dashboard.html` (alles inline: CSS, JS, Daten). Keine
Build-Tools, kein Server nötig, die Datei läuft standalone im Browser und lässt
sich in WordPress per Custom-HTML-Block oder iframe einbinden.

Ausführen: `python3 scripts/build2.py`

### d) `umkehr.py`: Richtungskorrektur der Umkehrabstimmungen
Erfasst die Abstimmungen mit dem Hinweis «Ja bedeutet ...» und normalisiert die
Stimmrichtung, damit «Ja» überall dieselbe inhaltliche Bedeutung hat. Arbeitet
wie `themen.py` mit menschlicher Freigabe: `python3 scripts/umkehr.py` erzeugt
die Prüftabelle `data/umkehr_zuordnung.json`, nach der Prüfung schreibt
`python3 scripts/umkehr.py --apply` ein Flag `richtung_invertiert` je Abstimmung,
ohne die Rohstimmen zu verändern. Grundlage der Prüfung ist das Wortprotokoll.

## 5. Eigenheiten der Datenquelle (teuer erlernt)

- **Elektronische Abstimmung erst seit 2018.** Davor keine namentlichen Daten.
- **Vormittag / Nachmittag / Abend** sind getrennte Sitzungshälften mit eigenen
  Excel-Dateien. Das Label wird aus dem Dateinamen abgeleitet.
- **Umkehrabstimmungen:** Manche Abstimmungen tragen den Hinweis "Ja bedeutet
  Zustimmung zum Kommissionsantrag". Dort bedeutet ein Nein inhaltlich
  Zustimmung zu einem Minderheitsantrag. Diese sind im Dashboard **markiert**,
  aber in aggregierten Kennzahlen **nicht richtungskorrigiert** (offener Punkt).
- **Metadaten können überzählig sein:** In Budget-Sitzungen läuft die
  Traktanden-Nummerierung über den ganzen Tag durch, eine einzelne Datei hat
  aber nur die Stimmspalten ihrer Tageshälfte. Der Parser begrenzt die
  Metadatenliste deshalb auf `n_votes` (die tatsächlichen Stimmspalten).
- **Legislaturgrenzen** werden automatisch erkannt: ein Wechsel von mehr als 15
  Mitgliedern gegenüber der Vorsitzung markiert eine neue Legislatur. In den
  Daten erkannt: Wechsel am 19.05.2025.
- **Namen mit Leerzeichen:** Im Excel gibt es Varianten wie "Flubacher " mit
  angehängtem Leerzeichen. Der Parser trimmt alle Namensfelder.
- **Doppelt verlinkte Dateien:** Dieselbe Datei kann zweimal auf der Seite
  hängen. Dedup erfolgt über einen Hash des Dateiinhalts.

## 6. Aktueller Stand

- **46 Sitzungshälften** aus 2024 bis 2026, **383 Abstimmungen**
- **225 Abstimmungen mit geprüftem Thema** (der Rest sind Einzelanträge,
  Planungserklärungen und Ordnungsanträge ohne Geschäftsbezug, die haben
  systematisch kein Thema)
- **77 Geschäfte** thematisch zugeordnet und vollständig geprüft
- 2 Legislaturen erkannt: 1. Legislatur mit 18 erfassten Sitzungshälften
  (13.05. bis 16.12.2024), 2. Legislatur mit 28 (19.05.2025 bis 29.06.2026),
  je 60 Mitglieder
- **Datenlücke Anfang 2025:** Die Sitzungen 1 bis 9 von 2025 (Januar bis Mai
  2025, noch 1. Legislatur) fehlen in den Daten. Ob dort keine namentlichen
  Abstimmungen stattfanden oder der Scraper sie ausliess, ist beim nächsten Lauf
  zu prüfen.

### Dashboard-Aufbau (Reihenfolge nach Nutzer-Priorität)
1. **Überblick**: Startseite mit grossen Eckzahlen und Top-3-Teasern
2. **Ranglisten**: Mitglieder und Parteien (Präsenz, Abwesenheit, Ja, Nein, Enthaltung)
3. **Mitglied im Detail**: jede einzelne Stimme über eine Legislatur, plus Themen-Aufschlüsselung
4. **Themen**: alle Abstimmungen je Themengruppe, mit Partei- und Mitgliederauswertung
5. **Fraktionen**: Kennzahlen je Fraktion
6. **Fraktionsprofil**: Spider-Grafik, nach Legislatur oder Einzelsitzung
7. **Ratsmitglieder**: Tabelle pro Sitzung
8. **Abstimmungen**: Detailansicht einer Sitzung

Navigation ist responsiv: Dropdown auf dem Handy (unter 720px), Tab-Leiste auf
dem Desktop.

## 7. Offene nächste Schritte

1. **Wiederkehrender Auftrag (eingerichtet):** Ein wöchentlicher Task
   («kantonsrat-dashboard-update», Mittwoch früh) fährt die Pipeline und meldet
   neue Prüffälle. Voraussetzung ist eine Browser-fähige Umgebung für den Scraper
   (Playwright/Chromium mit System-Bibliotheken wie libXdamage). Das Deployment
   auf die Live-Site muss ausserhalb verdrahtet werden.
2. **WordPress-Deployment:** statische Einbindung des HTML per Custom-HTML-Block
   oder iframe ist der robusteste Weg.
3. **Umkehrabstimmungen prüfen:** Die Infrastruktur steht (`umkehr.py`,
   `data/umkehr_zuordnung.json`, Flag `richtung_invertiert`). Die 22 Fälle müssen
   anhand der Protokolle inhaltlich geprüft werden (Feld `ja_ist_zustimmung`),
   danach `python3 scripts/umkehr.py --apply`.
4. **Datenlücke Anfang 2025 klären** (siehe Abschnitt 6): prüfen, ob die
   Sitzungen 1 bis 9 von 2025 nachgeladen werden müssen.
5. **Wähler-Matching (Prototyp vorhanden):** `scripts/matching.py` erzeugt
   `output/matching-prototyp.html` (Konzept in `docs/KONZEPT_waehler-matching.md`).
   Offen: laienverständliche Fragetexte aus den Protokollen, Prüfung der
   Umkehrfälle, demografischer Relevanzfilter, öffentliche Methodenseite.
   Achtung: Hier käme Wertung ins Spiel, transparente Regeln sind zentral.

## 8. Dateien im Projekt

| Datei | Zweck |
|---|---|
| `scripts/scraper.py` | holt Abstimmungsdaten und Protokolle von sh.ch |
| `scripts/themen.py` | Themen-Zuordnung (Vorschlag + Anwendung) |
| `scripts/umkehr.py` | Richtungskorrektur der Umkehrabstimmungen |
| `scripts/build2.py` | erzeugt das Dashboard-HTML |
| `scripts/matching.py` | erzeugt den Wähler-Matching-Prototyp |
| `data/all_sessions.json` | aktueller Datenstand (46 Sitzungen, 383 Abstimmungen) |
| `data/themen_zuordnung.json` | geprüfte Themen-Zuordnung der 77 Geschäfte |
| `data/umkehr_zuordnung.json` | Prüftabelle der 22 Umkehrabstimmungen |
| `data/themen_pruefung.xlsx` | Excel-Prüftabelle (ausgefüllt) |
| `output/kantonsrat-dashboard.html` | das fertige Dashboard, standalone lauffähig |
| `output/matching-prototyp.html` | interaktiver Wähler-Matching-Prototyp |
| `docs/PROJEKT.md` | diese Übergabe-Dokumentation |
| `docs/KONZEPT_waehler-matching.md` | Konzept für das Wähler-Matching-Tool |
| `docs/GLOSSAR_und_quellen.md` | Begriffe und Quellen (auch fürs Matching) |
| `archiv/kantonsrat-projekt.zip` | Original-Paket vor der Umstrukturierung |

### Reihenfolge beim Neuaufbau (aus der Projektwurzel)
```
python3 scripts/scraper.py         # Daten + Protokolle holen -> data/all_sessions.json
python3 scripts/themen.py          # Themen vorschlagen       -> data/themen_zuordnung.json
python3 scripts/umkehr.py          # Umkehrfälle erfassen     -> data/umkehr_zuordnung.json
#   ... themen_zuordnung.json und umkehr_zuordnung.json prüfen ...
python3 scripts/themen.py --apply  # Themen-Tags schreiben
python3 scripts/umkehr.py --apply  # Richtungs-Flags schreiben
python3 scripts/build2.py          # Dashboard bauen          -> output/kantonsrat-dashboard.html
```

## 9. Datenquelle und Haftung

Quelle: Kanton Schaffhausen, namentliche Abstimmungen des Kantonsrats
(Excel-Publikation der Parlamentsdienste), abgerufen über sh.ch.
Der Scraper hängt an der aktuellen Seitenstruktur (CSS-Klasse `list_item_grid`,
Attribut `contentid`, Dateiname-Konvention). Ändert der Kanton sein CMS, muss je
eine Stelle im Scraper angepasst werden. Aufbereitung ohne Gewähr.

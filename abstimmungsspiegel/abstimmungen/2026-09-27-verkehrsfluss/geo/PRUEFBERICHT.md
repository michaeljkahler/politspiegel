# Pruefbericht Geodaten · 2026-09-27-verkehrsfluss

Erzeugt am 03.09.2026 von `abstimmungsspiegel/bausteine/geo_freigeben.py`. Nicht von Hand aendern, die Datei wird bei jedem Lauf neu geschrieben.

**7 Ebenen freigegeben, keine zurueckgehalten.**

Freigegeben heisst: jede Koordinate liegt im Rahmen des Kantons, jede Geometrie ist vollstaendig, jede Eigenschaft, welche die Karte braucht, ist vorhanden. Zurueckgehalten heisst: die Ebene erscheint nicht auf der Seite, der Grund steht unten.

## Ebenen

| Ebene | Objekte | vorher | freigegeben | Stand | Anmerkung |
|---|---|---|---|---|---|
| `anlagen` | 92 | 17 kB | 15 kB | freigegeben | keine Erwartung hinterlegt, nur Rahmen und Geometrie geprueft |
| `anwohner_hektaren` | 681 | 228 kB | 164 kB | freigegeben | keine |
| `busnetz_wgs84` | 448 | 74 kB | 74 kB | freigegeben | keine |
| `geltung_gegenvorschlag` | 191 | 220 kB | 162 kB | freigegeben | keine |
| `geltung_initiative` | 302 | 347 kB | 254 kB | freigegeben | keine |
| `haltestellen_bus_wgs84` | 283 | 38 kB | 38 kB | freigegeben | keine |
| `kandidaten_wgs84` | 891 | 204 kB | 148 kB | freigegeben | keine |

## Herkunft je Ebene

### `anlagen`

nicht hinterlegt

- Rohdaten: `unbekannt`
- Objekte: 92
- Stand: freigegeben

### `anwohner_hektaren`

Eigene Rechnung (geo/skripte/haushalte.py): Hektaren der Bevoelkerungsstatistik STATPOP 2024 (BFS, ueber api3.geo.admin.ch), die eine betroffene Strasse schneiden, mit Einwohnerzahl und der Angabe, ob eine Fassade ueber 65 dB(A) darin liegt.

- Rohdaten: `01_roh/statpop_2024_hektaren.json, laerm_fassadenpunkte_tag_roh.xml`
- Objekte: 681
- Stand: freigegeben

### `busnetz_wgs84`

OpenStreetMap, Buslinien im Kanton, ueber die Overpass-API abgerufen.

- Rohdaten: `01_roh/busnetz_roh.json`
- Objekte: 448
- Stand: freigegeben

### `geltung_gegenvorschlag`

Eigene Rechnung (geo/skripte/geltungsbereich.py): verkehrsorientierte Kantonsstrassen innerorts (ueberregional, regional nach Feld typ der Achsen), Stuecke des Laermkatasters mit Tempo bis 50. Attribute je Stueck.

- Rohdaten: `01_roh/laerm_strassenachse_roh.xml, kantonsstrassen_alle_roh.xml`
- Objekte: 191
- Stand: freigegeben

### `geltung_initiative`

Eigene Rechnung (geo/skripte/geltungsbereich.py): Kantonsstrassen innerorts, die vom oeffentlichen Verkehr genutzt werden. Stuecke des kantonalen Laermkatasters mit Tempo bis 50, auf Kantonsstrassenachsen, mit Buslinie (OpenStreetMap) oder Haltestelle (BAV). Attribute je Stueck.

- Rohdaten: `01_roh/laerm_strassenachse_roh.xml, kantonsstrassen_alle_roh.xml, busnetz_linien_roh.json`
- Objekte: 302
- Stand: freigegeben

### `haltestellen_bus_wgs84`

Bundesamt fuer Verkehr, Ebene ch.bav.haltestellen-oev, ueber map.geo.admin.ch abgerufen.

- Rohdaten: `01_roh/haltestellen_bus_lv95.json`
- Objekte: 283
- Stand: freigegeben

### `kandidaten_wgs84`

Eigene Auswertung aus der Uebergabe vom Juli 2026: Kantonsstrassen innerorts im Umkreis von Schule, Kindergarten oder Heim.

- Rohdaten: `01_roh/kandidaten_kurze_abschnitte.geojson (LV95)`
- Objekte: 891
- Stand: freigegeben

## Was gepruefte Koordinaten heisst

Die Koordinaten werden auf 5 Nachkommastellen gekuerzt, das sind rund 1.1 Meter in Nord-Sued-Richtung. Genauer traegt keine Webkarte, und jede weitere Stelle kostet nur Dateigroesse. Wer die volle Genauigkeit braucht, nimmt `02_aufbereitet` oder die Rohdaten in `01_roh`.

Der Rahmen, gegen den geprueft wird: Laengengrad 8.3 bis 9.05, Breitengrad 47.45 bis 47.95. Er ist absichtlich grosszuegig; er soll nicht den Kanton abgrenzen, sondern eine Verwechslung des Bezugssystems auffangen. LV95 liefert Werte um 2 690 000 und 1 285 000 und faellt sofort auf.

# Pruefbericht Geodaten · 2026-09-27-verkehrsfluss

Erzeugt am 03.09.2026 von `abstimmungsspiegel/bausteine/geo_freigeben.py`. Nicht von Hand aendern, die Datei wird bei jedem Lauf neu geschrieben.

**4 Ebenen freigegeben, keine zurueckgehalten.**

Freigegeben heisst: jede Koordinate liegt im Rahmen des Kantons, jede Geometrie ist vollstaendig, jede Eigenschaft, welche die Karte braucht, ist vorhanden. Zurueckgehalten heisst: die Ebene erscheint nicht auf der Seite, der Grund steht unten.

## Ebenen

| Ebene | Objekte | vorher | freigegeben | Stand | Anmerkung |
|---|---|---|---|---|---|
| `busnetz_wgs84` | 448 | 74 kB | 74 kB | freigegeben | keine |
| `haltestellen_bus_wgs84` | 283 | 38 kB | 38 kB | freigegeben | keine |
| `kandidaten_wgs84` | 517 | 115 kB | 109 kB | freigegeben | keine |
| `kantonsstrassen_vo_wgs84` | 34 | 19 kB | 19 kB | freigegeben | keine |

## Herkunft je Ebene

### `busnetz_wgs84`

OpenStreetMap, Buslinien im Kanton, ueber die Overpass-API abgerufen.

- Rohdaten: `01_roh/busnetz_roh.json`
- Objekte: 448
- Stand: freigegeben

### `haltestellen_bus_wgs84`

Bundesamt fuer Verkehr, Ebene ch.bav.haltestellen-oev, ueber map.geo.admin.ch abgerufen.

- Rohdaten: `01_roh/haltestellen_bus_lv95.json`
- Objekte: 283
- Stand: freigegeben

### `kandidaten_wgs84`

Eigene Auswertung aus der Uebergabe vom Juli 2026: Kantonsstrassen innerorts im Umkreis von Schule, Kindergarten oder Heim.

- Rohdaten: `01_roh/kandidaten_kurze_abschnitte.geojson (LV95)`
- Objekte: 517
- Stand: freigegeben

### `kantonsstrassen_vo_wgs84`

Kanton Schaffhausen, Kantonaler Strassenrichtplan, Funktionszuweisung verkehrsorientiert, ueber wfs.geo.sh.ch abgerufen.

- Rohdaten: `01_roh/kantonsstrassen_vo_roh.json`
- Objekte: 34
- Stand: freigegeben

## Was gepruefte Koordinaten heisst

Die Koordinaten werden auf 5 Nachkommastellen gekuerzt, das sind rund 1.1 Meter in Nord-Sued-Richtung. Genauer traegt keine Webkarte, und jede weitere Stelle kostet nur Dateigroesse. Wer die volle Genauigkeit braucht, nimmt `02_aufbereitet` oder die Rohdaten in `01_roh`.

Der Rahmen, gegen den geprueft wird: Laengengrad 8.3 bis 9.05, Breitengrad 47.45 bis 47.95. Er ist absichtlich grosszuegig; er soll nicht den Kanton abgrenzen, sondern eine Verwechslung des Bezugssystems auffangen. LV95 liefert Werte um 2 690 000 und 1 285 000 und faellt sofort auf.

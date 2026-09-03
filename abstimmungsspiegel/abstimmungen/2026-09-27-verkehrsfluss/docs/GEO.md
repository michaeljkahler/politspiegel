# Geodaten · Verkehrsflussinitiative Schaffhausen

Welche Ebenen auf der Karte liegen, woher sie kommen und was beim Beschaffen
schiefgegangen ist. Die allgemeinen Regeln, insbesondere «die Karte zeigt den
Geltungsbereich, nicht die Wirkung», stehen in
[../../../docs/13_GEODATEN.md](../../../docs/13_GEODATEN.md).

Der aktuelle Stand der Freigabe steht in [../geo/PRUEFBERICHT.md](../geo/PRUEFBERICHT.md)
und wird bei jedem Lauf neu geschrieben.

---

## 1 · Karte: wer ist wo betroffen

Beschlossen am 3. September 2026. Bei räumlich wirksamen Vorlagen gehört eine
Karte auf die Seite. Michael hat für einen früheren Fall bereits eine gebaut; sein
Ansatz ist die Grundlage, dieses Kapitel hält nur die Regeln fest.

### Was diese Vorlage besonders macht

Initiative und Gegenvorschlag erfassen **nicht dieselben Strassen**:

| Erlass | Geltungsbereich laut Wortlaut |
|---|---|
| Initiative, Art. 12 Abs. 3 | Kantonsstrassen innerorts, **die auch durch den öffentlichen Verkehr genutzt werden** |
| Gegenvorschlag, Art. 12 Abs. 3 | **verkehrsorientierte** Kantonsstrassen innerorts, ohne ÖV-Bedingung |

Das sind zwei verschiedene Mengen, und keines der beiden Komitees sagt, wie sie
sich überschneiden. Die Initiative gilt enger, aber mit strengerer Regel; der
Gegenvorschlag greift womöglich weiter, aber schwächer. Zwei Kartenebenen
nebeneinander beantworten das, und die Antwort ist in keinem Argumentarium zu
finden. Das allein rechtfertigt die Karte.

### Vier Ebenen, alle mit Quellenangabe an der Ebene

1. **Geltungsbereich beider Texte.** Kantonsstrassennetz vom Amt für
   Geoinformation Schaffhausen, Innerorts-Abgrenzung über die Bauzone,
   ÖV-Linienführung aus den Fahrplandaten. Die Verschneidung ist die Kernaussage.
2. **Heutiger Zustand.** Wo gilt auf Kantonsstrassen bereits Tempo 30, wo 50.
   Zeigt, wie gross die tatsächlich strittige Fläche ist, und relativiert beide
   Kampagnenbilder.
3. **Betroffenheit, beschreibend.** Wohnbevölkerung aus dem STATPOP-Hektarraster,
   Lärmbelastung aus sonBASE, Schulen und Kindergärten entlang der erfassten
   Abschnitte. Jede Ebene mit Herausgeber, Stand und Link, keine Verrechnung zu
   einem Gesamtwert.
4. **Unfälle mit Personenschaden seit 2011**, ASTRA-Datensatz
   «Strassenverkehrsunfallorte».

### Warnung zur Unfallebene

Dieselbe Karte betreibt das Nein-Komitee als Kampagnenmittel. Wenn wir sie
zeigen, dann nur mit dem, was dort fehlt: Bezugsgrösse statt absoluter Punktzahl,
Mehrjahresmittel statt Jahreswerten, und ein sichtbarer Hinweis, dass eine Häufung
von Punkten vor allem Verkehrsmenge abbildet und nicht Gefährlichkeit. Ohne diese
Einordnung wäre sie das genaue Gegenteil dessen, was der Abstimmungsspiegel soll.
Punktdichte ist keine Risikokarte.

### Datenlage

Alles offen und lizenzfrei: Kanton Schaffhausen stellt seine Geodaten seit 2021
als WMS, WFS, Shapefile und GeoPackage bereit, zusätzlich über opendata.swiss;
die ASTRA-Unfallorte liegen als Open Data mit REST-API und WMS vor. Kein Layer
dieser Karte hängt an einer Quelle, die wir nicht zitieren dürfen.

---

## 2 · Was aus der Übergabe übernommen wurde

Michaels Analyse vom Juli und August 2026 liegt unter `geo/`. Sie ist ein
eigenständiges, quellenbasiertes Werk mit Projectbrief, Bericht, Rechenmodell,
17 Übersichtsgrafiken, 17 Gemeindekarten und den Rohdaten je Abschnitt.

**Der Befund, der das Vorgehen bestätigt:** Die Analyse schliesst genau die
Lücken, welche die Argumentprüfung unabhängig davon markiert hatte. Das ist kein
Zufall, sondern zeigt, dass das Prüfschema die richtigen Fragen stellt.

| Prüfung sagte «fehlt» | Geoanalyse liefert |
|---|---|
| pro-1, Blaulicht: keine Zahl, und Sonderrechte nach Art. 100 Ziff. 4 SVG | G6 mit Richtwerten von +0,5 bis +2,5 Minuten und derselben Rechtslage |
| pro-2, öV: keine Schaffhauser Zahl | G5 mit Zusatzzeit je Buslinie, Linie 21 rund +7,8 Minuten |
| contra-1, Unfälle: keine kantonale Zahl | 1189 Unfälle über 15 Jahre, davon 144 mit Fussgängern; 901 auf verkehrsorientierten Abschnitten |
| contra-4, Lärm: «Tausende» unbeziffert | 1816 Fassaden über dem Immissionsgrenzwert, davon 1164 auf verkehrsorientierten Abschnitten |

**Wichtig für die Redlichkeit:** Die Punktzahl der Karten ändert sich dadurch
**nicht**. Bewertet wird, ob das Komitee einen Beleg genannt hat, nicht ob
irgendwo einer existiert. Was sich ändert, ist der Präzisierungssatz: Er nennt
jetzt die Zahl, statt nur ihr Fehlen zu rügen. Und er sagt es auch dann, wenn
die Zahl der geprüften Seite hilft, wie bei den Buslinien.

**Erledigt: die Farben.** `scripts/grafiken_umfaerben.py` bildet die Palette der
Geoanalyse auf das Farbsystem des Dashboards ab und schreibt nach
`grafiken/` und `grafiken/gemeinden/`; die Originale bleiben
unverändert. Grundlage war eine Auszählung aller 69 Hexwerte in den 17 Grafiken.

Der wichtigste Eingriff betrifft die Ampelskala. Rot, Orange und Grün verletzen
nicht nur Abschnitt 1 der Design-Entscheide, wo Grün für die SVP und Rot für die
SP steht. Eine Ampel färbt auch eine Wertung ein, «rot gleich schlimm», die in
einer neutralen Abstimmungshilfe nichts zu suchen hat. Rangfolgen werden deshalb
zu einer Graustufenrampe von hell nach dunkel. Information geht keine verloren,
weil in diesen Grafiken die Zahl ohnehin am Balken steht.

| Rolle | vorher | nachher |
|---|---|---|
| Blattgrund, Titel, Fliesstext, Haarlinie | `#f5f4f1`, `#0b0b0b`, `#52514e`, `#e1e0d9` | die Token `--flaeche`, `--text`, `--text-leise`, `--linie` |
| Akzent der Kopfleiste | `#2a78d6` Blau | `#3c4652` Graphit, die Oberfläche hat keine Akzentfarbe |
| Ampel hoch, mittel, gering | `#d03b3b`, `#c9871c`, `#0ca30c` | `#1f2833`, `#6e7783`, `#a9b1be` |
| sequenzielle Skala, 5 Stufen | Grünskala `#08492f` bis `#9cbcae` | Graphitrampe `#1f2833` bis `#b9c2ce` |

**Offen: die kategorialen Farben der Gemeindekarten.** Sechs Werte kodieren die
vier Nutzungsgruppen und die zwei Kandidatenstufen, laut Übergabedokument
bewusst gesetzt:

| Gruppe | Farbe | Signatur |
|---|---|---|
| Schule | `#d95f0e` orange | Quadrat |
| Kindergarten | `#1b9e77` grün | Dreieck |
| Alters- und Pflegeheim | `#6a51a3` violett | Kreis |
| weitere Sozialeinrichtung | `#2166ac` blau | Raute |
| Kandidat bis 100 m | `#e6194b` rot | Linie kräftig |
| Kandidat bis 300 m | `#f4a6ae` rosa | Linie blass |

Dafür gibt es im Farbsystem keine Entsprechung, und eine zu erfinden ist eng:
Petrol und Purpur sind für Ja und Nein reserviert, Grün ist die SVP, Blau die
FDP, Ocker die Mitte, Braun die EDU. Entlastend wirkt, dass jede Gruppe eine
eigene Signatur trägt, die Farbe also nicht allein tragen muss. Das ist ein
Entscheid, kein Vorschlag von mir; bis dahin bleiben die sechs Werte unverändert.

**Offen: die Einbindung.** Die Seite verweist mit relativen Pfaden auf
`grafiken/` und `grafiken/gemeinden/`, sie ist damit nicht mehr
eigenständig. Für die Veröffentlichung sind die Dateien entweder einzubetten
oder mitzudeployen.

---

## 3 · Kartenviewer

Gebaut mit Leaflet. Grundkarte wahlweise OpenStreetMap, Landeskarte grau oder
swissTLM grau. Zuschaltbar sind vier amtliche Kachelebenen, alle am 3. September
2026 gegen `wmts.geo.admin.ch` geprüft und ladend:

| Ebene | Kennung | Stand |
|---|---|---|
| Unfälle mit Personenschaden | `ch.astra.unfaelle-personenschaeden_alle` | `99990101` |
| davon mit Fussgängern | `ch.astra.unfaelle-personenschaeden_fussgaenger` | `99990101` |
| Strassenlärm am Tag | `ch.bafu.laerm-strassenlaerm_tag` | `current` |
| Hauptstrassennetz | `ch.astra.hauptstrassennetz` | `current` |

Kachelmuster: `https://wmts.geo.admin.ch/1.0.0/{layer}/default/{stand}/3857/{z}/{x}/{y}.{format}`

**Was eingebettet ist und was live kommt.** Eingebettet sind nur die eigenen
517 Kandidatenlinien, umprojiziert von LV95 nach WGS84, rund 115 kB. Alles andere
wird bei jedem Aufruf frisch von Bund und Kanton geladen. So veralten die
amtlichen Daten nicht in unserer Kopie, und wir behaupten nichts über sie.

**Zwei Fehler, die die Gegenprüfung gefunden hat.** Die Gemeinde heisst in der
Auswertungstabelle «Bargen», im GeoJSON aber «Bargen (SH)»; der Sprung wäre ins
Leere gelaufen. Und in fünf Gemeinden gibt es überhaupt keine Kandidatenlinie,
weil dort keine betroffene Strasse innerhalb 300 Metern einer sensiblen Nutzung
liegt. Beides ist jetzt behoben: Der Name wird beim Umprojizieren normalisiert,
und die fünf Gemeinden stehen als gesperrte Einträge mit dem Vermerk «keine
Kandidaten» im Menü, statt still nichts zu tun.

**Warnhinweis fest bei der Karte.** Eine Häufung von Unfallpunkten heisst zuerst,
dass dort viel Verkehr ist. Ein Risikovergleich bräuchte eine Bezugsgrösse und
ein Mehrjahresmittel. Der Satz steht unter der Karte, nicht in einer Fussnote.

### Kantonale Ebenen und der Geltungsbereich-Umschalter

Der Kanton Schaffhausen veröffentlicht seine Geodaten offen. Endpunkte und
Ebenennamen am 3. September 2026 gegen `wms.geo.sh.ch` geprüft, alle rendern
samt amtlicher Legende:

| Ebene | Kennung |
|---|---|
| Strassenrichtplan, Funktion | `sh.richtplan.strassenrichtplan.kanton.strassen.bestehend.fkt` |
| Ortstafeln | `sh.richtplan.strassenrichtplan.kanton.ortstafeln` |
| Baugebiet | `sh.nutzungsplanung.rechtsgueltig.baugebiet` |

WMS `https://wms.geo.sh.ch/wms`, WFS `https://wfs.geo.sh.ch/wfs`, Download
`https://data.geo.sh.ch/ogd/strassenrichtplan.zip`. Der Datensatz ist über
opendata.swiss als «Strassenrichtplan Kanton Schaffhausen» geführt, Stand
12. Mai 2026. Das Geoportal `map.geo.sh.ch` ist dafür kein Weg, seine
Konfigurations-API antwortet mit 401.

**Zwei Knöpfe, Initiative und Gegenvorschlag**, blenden den Richtplan samt
Ortstafeln ein und schreiben darunter, woran der jeweilige Text anknüpft. Sie
zeigen bewusst dasselbe Kartenbild, denn der Unterschied liegt nicht im Bild,
sondern im Kriterium, und genau das ist die Aussage:

- Der **Gegenvorschlag** knüpft an die Funktionszuweisung an, also an das, was
  die eingeblendete Ebene zeigt. Sein Geltungsbereich ist direkt aus amtlichen
  Daten ablesbar.
- Die **Initiative** knüpft daran an, ob ein Bus fährt. Dafür sind zusätzlich die
  Bushaltestellen eingeblendet, siehe unten.

### Die Bushaltestellen als Annäherung an das Kriterium der Initiative

Der Bund führt die Ebene `ch.bav.haltestellen-oev` des Bundesamts für Verkehr.
Über die identify-Schnittstelle von `api3.geo.admin.ch` lassen sich die
Haltestellen als echte Objekte abfragen, mit Name, Verkehrsmittel und Betreiber.
Für den Kanton und sein Umland ergibt das **328 Haltestellen, davon 283 Bus**:
235 der Verkehrsbetriebe Schaffhausen, 38 PostAuto, 6 SBG, 4 SBB. Sie liegen
umprojiziert in `geo/02_aufbereitet/haltestellen_bus_wgs84.geojson` und sind im Viewer
einzeln anklickbar.

Haltestellen allein sind allerdings nicht die Linienführung. Eine Strasse kann
vom Bus befahren werden, ohne dass eine Haltestelle darauf liegt, gerade auf den
langen Abschnitten zwischen zwei Dörfern, also dort, wo Tempo 30 den Bus am
meisten kosten würde. Darum kam die Linienführung dazu.

### Die Linienführung, und warum zwei Quellen besser sind als eine

Bei geo.admin.ch gibt es kein Busnetz als Linien, dort liegt nur das Schienennetz
vor. Der Kanton führt ebenfalls keine ÖV-Linienebene, geprüft an den 429 Ebenen
seines WMS. Die praktikable Quelle sind die **Buslinien-Relationen von
OpenStreetMap**, abgefragt über Overpass, gefiltert auf die Schweizer Betreiber
VBSH, PostAuto und PAZ.

Ergebnis: **242 Kilometer befahrene Strassen**, aus 124 Linienrelationen. Die
3340 einzelnen OSM-Wegstücke wurden zu 448 durchgehenden Linienzügen verkettet
und mit Douglas-Peucker auf 10 Meter Toleranz vereinfacht; das kostet 2 Prozent
Netzlänge und spart 80 Prozent Datenmenge. Ablage in
`geo/02_aufbereitet/busnetz_wgs84.geojson`, 74 kB.

**Die Gegenprobe ist der eigentliche Gewinn.** Haltestellen und Linienführung
stammen aus zwei voneinander unabhängigen Quellen, einer amtlichen und einer
betrieblichen. Legt man sie übereinander, muss jede Haltestelle auf einer Linie
liegen. Für 25 zufällig gezogene Haltestellen beträgt der **Median 4 Meter**,
**24 von 25 liegen unter 50 Metern**. Das ist eine unabhängige Bestätigung
beider Datensätze. Der eine Ausreisser mit 519 Metern gehört vermutlich zu einer
Linie, die der Betreiberfilter ausschliesst.

**Was trotzdem gilt:** OpenStreetMap ist betrieblich, nicht amtlich, und die
Linienführung ändert mit jedem Fahrplanwechsel. Das steht so auf der Seite. Die
amtliche Alternative wären die Fahrplandaten von opentransportdata.swiss, deren
`shapes` dieselbe Information tragen; sie liegen als grosses GTFS-Paket vor und
wären der nächste Ausbauschritt, wenn die Seite dauerhaft betrieben wird.

**Reproduzierbar:** `geo/skripte/busnetz_holen.py` holt beide Datensätze neu,
verkettet, vereinfacht und rechnet die Gegenprobe selbst nach. Das Skript läuft
nicht in der Sandbox, weil Overpass dort gesperrt ist, aber auf jedem Rechner
mit freiem Netz.

**Der Ortstafel-Fund.** Der Kanton führt die Ortstafeln als eigene Ebene. Damit
liesse sich «innerorts» rechtlich sauber abgrenzen, statt über das Baugebiet.
Das Übergabedokument nennt die Baugebiet-Näherung ausdrücklich als offenen Punkt.
Beide Ebenen sind im Viewer zuschaltbar, der Unterschied ist also sichtbar.

**Ehrlich bleiben:** Solange die Geltungsbereiche nicht gerechnet, sondern nur
illustriert sind, steht das auch so da. Ein Knopf, der eine amtliche Ebene
einblendet und dazu den Gesetzestext erklärt, ist etwas anderes als eine
berechnete Menge, und der Unterschied darf nicht verwischt werden.

---

## 4 · Herkunft der Geoanalyse und das Rechenmodell

Die ursprüngliche Arbeitssitzung existiert nicht mehr, sie lief in einer
Cloud-Umgebung, die zurückgesetzt wurde. Michael hat statt dessen ein
Übergabepaket geliefert, das die Lücke schliesst. Es liegt unter `geo/`:

| Datei | Inhalt |
|---|---|
| `geo/PROJEKT_KONTEXT.md` | 206 Zeilen Übergabe: Fragestellung, Datengrundlagen, Methodik samt Formeln, Ergebnisse, Vorbehalte |
| `geo/skripte/` | elf rekonstruierte Rechenskripte, darunter `knv.py`, `suit.py`, `map_lib.py` |

Damit ist die Analyse reproduzierbar, was sie vorher nicht war.

### Das Kosten-Nutzen-Modell, offen dokumentiert

`geo/skripte/knv.py` rechnet je Abschnitt:

```
zeitkosten   = fahrleistung × 20 s/km ÷ 3600 × 365 × 42.50 CHF/Fz-h
unfallnutzen = unf/15 × 139'275 CHF × 0.20
laermnutzen  = fass_igw × 900'000 CHF × 0.005/dB × 3 dB × 0.03
```

**Ergebnis:** Zeitkosten rund 31 Mio. CHF im Jahr gegen monetarisierte Nutzen von
rund 2,9 Mio. Das Kosten-Nutzen-Verhältnis bleibt für jeden Abschnitt und jede
Gemeinde unter 1.

**Entscheid vom 3. September 2026: Die Rechnung kommt nicht auf die Seite.**
Michael hat das entschieden, und die Begründung ist tragfähiger, als ich sie
zuerst gefasst hatte.

**Der eigentliche Grund ist nicht die Unsicherheit einzelner Annahmen, sondern
eine strukturelle Einseitigkeit.** Auf der Kostenseite wird der Zeitverlust
vollständig monetarisiert, jede Sekunde jedes Fahrzeugs. Auf der Nutzenseite
werden nur Unfälle und Lärm monetarisiert. Aufenthaltsqualität, Gesundheit und
subjektive Sicherheit fehlen ganz, weil es dafür keine belastbaren Ansätze im
Modell gibt. Ein Verhältnis, das so gebaut ist, **kann gar nicht anders als
unter 1 herauskommen**, unabhängig davon, wie man die Parameter setzt. Es misst
nicht, ob Tempo 30 sich lohnt, sondern nur, welcher Teil seiner Wirkung sich
in Franken fassen lässt.

Damit fällt die Rechnung an der Achse **Reichweite** durch, und zwar nach
demselben Massstab, den wir an die Komitees anlegen: Sie gilt nicht so
allgemein, wie ihre Ergebniszahl nahelegt. Sie hier abzudrucken wäre genau der
Fehler, den der Abstimmungsspiegel bei anderen aufdeckt.

Dazu kommen zwei kleinere Einwände: Das Szenario ist flächendeckendes Tempo 30,
was weder Initiative noch Gegenvorschlag zur Debatte stellen. Und die
Unfallreduktion von 20 Prozent sowie der Fassadenwert von 900'000 Franken sind
gesetzte Annahmen.

**Eine Präzisierung zum Staukosten-Einwand.** Michael hat den ASTRA-Wert als
Schwachstelle genannt. Der Blick in `knv.py` zeigt, dass die Rechnung diesen
Fehler nicht macht: Sie verwendet `VTTS = 42.50` CHF je Fahrzeugstunde, also den
Zeitkostenansatz nach ARE und VSS SN 641 822a, nicht die ASTRA-Staukostenzahl.
Der Projectbrief hatte diese Unterscheidung ausdrücklich verlangt, und sie wurde
eingehalten. Der Grund, die Rechnung wegzulassen, ist also nicht dieser, sondern
die Asymmetrie oben.

**Was den Entscheid umkehren würde:** belastbare Ansätze, die auch die fehlenden
Nutzen bewerten. In Frage kämen die externen Kosten des Verkehrs nach ARE, wo
Gesundheit und Lärm bereits beziffert sind, oder das HEAT-Verfahren der WHO für
den Gesundheitsnutzen von Fuss- und Veloverkehr. Beides müsste geprüft und auf
Schaffhausen übertragbar sein. Solange die Nutzenseite unvollständig bleibt,
bleibt die Rechnung draussen.

### Zwei Zählebenen: Gemeinde und benannter Abschnitt

Die Datengrundlage zählt auf zwei Ebenen, nachgerechnet am 4. September 2026 aus
`geo/02_aufbereitet/`:

1. Blatt «Gemeinden» (Kantonsstrassen innerorts je Gemeinde, vollständig):
   1189 Unfälle mit Personenschaden 2011 bis 2025, davon 144 mit Fussgängern und
   327 mit Velofahrenden; 1816 Fassaden über dem Immissionsgrenzwert.
2. `per_abschnitt.json` (nur die 163 benannten Abschnitte aus den
   Verkehrszähldaten, Zuordnung per Nachbarschaftssuche mit 20 beziehungsweise
   25 Metern Fangdistanz): 1184 Unfälle (140 Fussgänger, 322 Velo) und 1707
   Fassaden. Davon auf den 75 verkehrsorientierten Abschnitten 901 Unfälle und
   1164 Fassaden, auf den 88 siedlungsorientierten 283 und 543.

Die Differenz (5 Unfälle, 109 Fassaden) sind Fälle ausserhalb der Fangdistanz
eines benannten Abschnitts. Auf der Seite stehen die Kantonswerte der ersten
Ebene (1189, 144, 327, 1816) und für die von der Initiative erfassten Strassen
die Werte der verkehrsorientierten Abschnitte (901, 1164). Die Grafiken G8 und
G10 zeigen dieselben Zahlen.

### Zur Umfärbung, mit einer Korrektur an mir selbst

Das Übergabedokument zeigt, dass die Farbwahl bereits durchdacht war: die
sequenzielle Grünskala wurde ausdrücklich gewählt, weil sie «nicht wertend rot»
ist, und die Unfalldichte-Bänder blau, um eine Ampel zu vermeiden. Die Umfärbung
korrigiert also nicht mangelnde Sorgfalt, sondern eine Kollision, die erst im
Dashboard-Zusammenhang entsteht: Grün ist dort die SVP.

Zwei Punkte bleiben trotzdem: Die Ampelskala in G5 und G6 widerspricht dem
eigenen Grundsatz des Dokuments, dort ist die Umfärbung eine Verbesserung, nicht
nur eine Anpassung. Und die kategorialen Farben der Gemeindekarten sind laut
Übergabe bewusst gruppenweise gesetzt (Schule orange, Kindergarten grün,
Heim violett, weitere blau), sie tragen also Bedeutung und dürfen nicht einfach
in Graustufen aufgelöst werden.

### Was weiterhin fehlt

`infra_SH_v2.gpkg` mit den 213 Standorten. Die Skripte brauchen es, um die Karten
neu zu erzeugen; vorhanden sind nur die abgeleiteten Ergebnisse. Ebenso
`roads_fkt.geojson`, `baugebiet.geojson`, `netzbelastung.geojson` und
`master_gemeinde.json`.

---

## Betroffene Strassen beider Vorlagen (Stand 4. September 2026)

Zwei Vektorebenen mit Attributen je Strassenstück, gerechnet von
`geo/skripte/geltungsbereich.py`, freigegeben als
`geo/03_freigegeben/geltung_initiative.geojson` und `geltung_gegenvorschlag.geojson`.

1. Grundlage: die Strassenstücke des kantonalen Lärmkatasters (Strassenname,
   signalisierte Höchstgeschwindigkeit, DTV, Emissionswert), auf den
   Kantonsstrassenachsen (Funktion, Nummer, Achsenname aus dem Feld `typ`).
2. Innerorts: Tempo bis 50 km/h und Siedlungslage (Baugebiet mit 30 m Puffer zu
   mindestens 10 %, oder Haltestelle in 150 m, oder Ortstafel in 250 m).
   Ergebnis 78,0 km; Übergabe Juli 2026: 80,4 km.
3. Initiative: innerorts mit Buslinie (OpenStreetMap, 20 m) oder Haltestelle
   (BAV, 30 m); befährt die Linie nur einen Teil, zählt der Teil.
   58,7 km in 297 Stücken.
4. Gegenvorschlag: innerorts und verkehrsorientiert (überregional, regional).
   43,1 km in 191 Stücken; Übergabe: 43,9 km.
5. Schnittmenge: beide 35,1 km, nur Initiative 23,6 km,
   nur Gegenvorschlag 7,9 km.
6. Attribute je Stück: Nummer, Achse, Strassenname, Gemeinde, Funktion, Tempo,
   DTV, Emissionswert, Bus (ja, teilweise, nein) mit Liniennummern und
   Haltestellen, Länge, und aus `per_abschnitt.json` Unfälle 2011 bis 2025 und
   Fassaden über dem Immissionsgrenzwert des benannten Abschnitts.
7. Nicht als Innerortsgrenze tauglich: das Baugebiet allein (deckt die
   Stadtkerne nicht, 0 % an Bahnhof-, Hoch- und Fulachstrasse) und die
   Ortstafeln allein (140 Punkte, unvollständig). Beides steht darum nur als
   Siedlungsmerkmal neben dem Tempo.
8. Ausgeschlossen als Ausserortsstrecken mit Tempo 40 oder 50:
   31 Stücke,
   7,8 km
   (Randenstrasse, Im Gehren und weitere), Liste in `geltungsbereich.json`.
9. Die frühere Ebene `kantonsstrassen_vo_wgs84` (106,8 km, das ganze
   verkehrsorientierte Netz ohne Innerortsschnitt) ist entfernt.
10. Darstellung im Viewer: Initiative blau (5 px), Gegenvorschlag rot (11 px),
    beide mit heller Kontur; wo beide gelten, liegt Blau auf Rot. Klick auf ein
    Stück zeigt die Attribute.

## Stichprobe Bus-Zuordnung (4. September 2026)

Geprüft wurden die verkehrsorientierten Stücke ohne Bus (vorher 7,9 km), je mit
Abstand zur nächsten OSM-Buslinie und zur nächsten BAV-Haltestelle:

1. Ohne Linie und ohne Haltestelle im Umkreis von 600 m, also ohne Busbetrieb:
   Trasadingen Zollstrasse (708 m, H13 Richtung Erzingen), Buch Steinerstrasse
   (375 m), Bargen H4 (339 m), Neuhausen Zollstrasse (80 m).
2. Linie auf einer Parallelstrasse, Haltestelle 100 bis 280 m entfernt, also
   kein Bus auf dieser Strasse: Stein am Rhein Oehningerstrasse (Linie 33 in
   211 m), Wilchingen Trasadingerstrasse (Linien 27/N77 in 78 m), Hallau
   Neunkircherstrasse (151 m), Neunkirch Wilchingerstrasse (262 m), Thayngen
   Erlengasse (46 m), Ramsen und Buch Richtung Brücke (Linie 25, 108 bis 140 m).
3. Nur Nachtbus N77 quert: Neunkirch Hallauerstrasse (563 m).
4. Zwei Fehlzuordnungen, beide wegen getrennter Fahrbahnen oder einer
   Wendeschleife: Schaffhausen Ebnatstrasse (Linien 5, 6, 10, 24 in 35 m,
   Haltestelle Falkeneck in 49 m) und Schleitheim Schwarzwaldstrasse (Linie 21
   endet dort, Haltestelle Bahnhofstrasse in 36 m). Korrektur: Haltestellen
   zählen bis 50 m statt 30 m. Ergebnis danach: Initiative 60,2 km (vorher
   58,7), nur Gegenvorschlag 7,4 km (vorher 7,9).

## Anwohner und Lärmfassaden (4. September 2026)

`geo/skripte/haushalte.py`, Ergebnis in `geo/02_aufbereitet/haushalte.json`, Ebene
`anwohner_hektaren` im Viewer, Tabelle im Kartenblock, Zahlen in contra-4.

1. Anwohner: Einwohner der STATPOP-Hektaren (BFS, 2024, über api3.geo.admin.ch),
   die eine betroffene Strasse schneiden. Initiative 20,658 Personen
   (9,837 Haushalte zu 2,1), Gegenvorschlag 14,014 (6,673).
2. Fassaden: Fassadenpunkte des kantonalen Lärmkatasters (Tag, Sanierungshorizont
   2043) höchstens 25 m von einer betroffenen Strasse. Über 65 dB(A), dem
   Immissionsgrenzwert der ES III: Initiative 883 Punkte an
   404 Gebäuden, Gegenvorschlag 353 Gebäude. Über 60 dB(A)
   (ES II): 1422 beziehungsweise 1244 Gebäude. Die
   Empfindlichkeitsstufe je Gebäude liegt nicht als Ebene vor, darum beide Werte.
3. Anwohner in Hektaren mit mindestens einer Fassade über 65 dB(A): Initiative
   6,481, Gegenvorschlag 5,562; die Hektare zählt
   ganz, Obergrenze.
4. Die 1816 Fassaden der Übergabe zählten Punkte über dem Grenzwert entlang aller
   Kantonsstrassen innerorts (80,4 km) mit einer nicht dokumentierten
   Grenzwertregel; sie stehen nicht mehr auf der Seite.

## Gemeindekarten und Umkreise (4. September 2026)

`geo/skripte/gemeindekarten.py` ersetzt die Karten und Kennzahlen der Übergabe.

1. Jede Karte zeigt beide Vorlagen (Rot Gegenvorschlag, Blau Initiative),
   Umkreise 100, 300 und 500 m um die Anlagen, betroffene Strassen in 100 m
   (schwarz) und 300 m (grau) hervorgehoben.
2. Anlagen: OpenStreetMap (amenity school, college, kindergarten, childcare,
   nursing_home, social_facility, hospital), 42 / 31 / 19 / 0 nach Schulen,
   Kindergärten, Heimen, weiteren. Liegt das GeoPackage der Übergabe
   (`infra_SH_v2.gpkg`, 213 Standorte aus OSM und kantonalen Quellen) unter
   `geo/01_roh/`, nimmt das Skript dieses; die OSM-Liste ist dünner (im
   Stadtgebiet Schaffhausen 6 Schulen statt rund 15).
3. Kanton: betroffen 67,77 km (mindestens eine Vorlage), davon
   6 Prozent in 100 m, 32 Prozent in 300 m, 47 Prozent in 500 m einer
   Anlage. Übergabe: 13, 56 und 73 Prozent, bezogen auf 43,9 km und 213 Standorte.
4. `kandidaten_wgs84` (Strassen in 100 und 300 m) ist neu gerechnet, die Zahlen
   in `karte.gemeinden`, `karte.total`, `karte.anlagen_total` und in der
   Textkritik (Stelle 1, Punkt 2) sind eingetragen (`zahlen_eintragen.py`).

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
| contra-1, Unfälle: keine kantonale Zahl | 1184 Unfälle über 15 Jahre, davon 140 mit Fussgängern |
| contra-4, Lärm: «Tausende» unbeziffert | 1707 Fassaden über dem Immissionsgrenzwert, davon 1164 auf betroffenen Abschnitten |

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

### Zwei Zahlen, die nicht ganz zusammenpassen

Der Bericht nennt 1189 Unfälle und 1816 Fassaden über dem Immissionsgrenzwert.
Aus der gelieferten Abschnittstabelle nachgerechnet ergeben sich 1184 und 1707.
Die Streckenlängen stimmen dagegen auf die Kommastelle überein, es ist also
dieselbe Netzbasis. Vermutlich zählt der Bericht auch Unfälle und Fassaden mit,
die keinem benannten Abschnitt zugeordnet werden konnten; die Zuordnung läuft
über eine Nachbarschaftssuche mit 20 beziehungsweise 25 Metern Fangdistanz.
Aufgelöst ist es nicht. Auf der Seite steht die kleinere, nachrechenbare Zahl,
zusammen mit einem sichtbaren Hinweis auf die Abweichung. Das ist derselbe
Massstab, den wir an die Komitees anlegen.

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

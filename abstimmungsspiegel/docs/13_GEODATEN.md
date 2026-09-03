# Geodaten

Wie Geodaten in eine Abstimmungsseite kommen und was zwischen Rohdaten und
Karte mit ihnen passieren darf. Die Ebenen einer einzelnen Vorlage stehen im
Abstimmungsordner unter `docs/GEO.md`, das Ergebnis der Prüfung in
`geo/PRUEFBERICHT.md`.

---

## 1 · Die eine Regel, die alles trägt

**Die Karte zeigt den Geltungsbereich, nicht die Wirkung.** Welche Flächen ein
Erlass erfasst, folgt aus seinem Wortlaut plus amtlichen Geodaten und ist damit
nachrechenbar wie eine Zahl. Was dort dann geschieht, ist Prognose und gehört
auf die Argumentkarten, wo die Evidenzbasis geprüft wird.

Sobald die Karte Abschnitte nach «wird gefährlicher» oder «wird ruhiger»
einfärbt, ist sie Kampagnenmaterial und nicht mehr Abstimmungsspiegel. Diese
Grenze ist scharf und nicht verhandelbar, weil eine Karte stärker wirkt als ein
Satz: Wer eine rote Linie sieht, glaubt sie, auch wenn im Kleingedruckten
«Prognose» steht.

Daraus folgt eine zweite Regel: **eine Häufung ist keine Gefahr.** Viele
Unfallpunkte heissen zuerst, dass dort viel Verkehr ist. Viele farbige Kreise
heissen zuerst, dass dort viele Menschen wohnen. Ein Risikovergleich bräuchte
eine Bezugsgrösse und ein Mehrjahresmittel. Der entsprechende Warnhinweis steht
sichtbar bei der Karte, nicht in einer Fussnote.

---

## 2 · Drei Stufen, und warum es drei sein müssen

```
geo/01_roh/           unverändert, wie vom Server geladen
geo/02_aufbereitet/   umprojiziert, verschnitten, ausgewertet
geo/03_freigegeben/   geprüft, gekürzt, genau das was die Seite einbindet
geo/PRUEFBERICHT.md   je Ebene: Herkunft, Objektzahl, Grösse, Befund
```

Der Grund für die dritte Stufe ist eine Erfahrung: Zwischen «die Daten sind da»
und «die Daten sind richtig» liegt Arbeit, und wenn diese Arbeit im Bauskript
steckt, sieht sie niemand. Ein verwechseltes Bezugssystem, eine leere Geometrie
oder eine fehlende Beschriftung fällt auf der Karte nicht als Fehler auf,
sondern als Aussage. Eine eigene Stufe macht die Prüfung zum Arbeitsschritt mit
eigenem Ergebnis.

### Was jede Stufe darf

| Stufe | Erlaubt | Nicht erlaubt |
|---|---|---|
| `01_roh` | Ablegen, wie geladen, mit Abrufdatum | Jede Änderung. Auch keine Formatierung |
| `02_aufbereitet` | Umprojizieren, vereinfachen, verschneiden, rechnen | Zusammenfassen ohne Skript |
| `03_freigegeben` | Prüfen, Koordinaten kürzen | Inhaltliche Änderung |

`01_roh` bleibt unangetastet, damit jede Aufbereitung wiederholbar ist. Wer
eine Zahl anzweifelt, geht dort hin und rechnet nach. Das ist auch der Grund,
weshalb die Rohdaten mitversioniert werden, obwohl sie sich neu laden liessen:
Der Server von heute liefert nicht die Daten von damals.

`03_freigegeben` enthält keine inhaltliche Änderung mehr. Der Schritt kürzt nur
Koordinaten auf fünf Nachkommastellen, rund einen Meter, weil mehr keine
Webkarte trägt und jede weitere Stelle nur Dateigrösse kostet.

### Die Prüfung, und was sie im Zweifel tut

`bausteine/geo_freigeben.py` prüft je Ebene:

1. **Rahmen.** Liegt jede Koordinate im Bereich des Kantons? Der Rahmen ist
   absichtlich weit gefasst. Er soll nicht den Kanton abgrenzen, sondern eine
   Verwechslung des Bezugssystems auffangen. LV95 liefert Werte um 2 690 000
   und 1 285 000 und fällt sofort heraus.
2. **Vollständigkeit.** Keine Geometrie ohne Koordinaten.
3. **Pflichteigenschaften.** Je Ebene ist hinterlegt, welche Felder die Karte
   braucht. Fehlt eines, zeigt die Karte leere Beschriftungen.
4. **Geometrietyp.** Eine Linienebene, in der plötzlich Punkte stehen, ist
   ein anderes Datenprodukt als erwartet.

**Fällt eine Prüfung durch, wird die Ebene nicht freigegeben.** Sie bleibt in
`02_aufbereitet` liegen, der Grund steht im Prüfbericht, und der Kartenbaustein
findet die Ebene nicht und lässt sie weg. Lieber eine Ebene fehlt, als dass
eine falsche erscheint. Das Bauskript meldet die Lücke auf der Fehlerausgabe,
damit sie nicht stillschweigend durchgeht.

---

## 3 · Eingebettet oder live

Eine Entscheidung je Ebene, mit einer klaren Regel:

- **Eigene Auswertungen werden eingebettet.** Sie sind unsere Aussage, sie
  müssen genau so bleiben, wie sie geprüft wurden, und sie müssen zu jeder
  Version der Seite passen.
- **Amtliche Ebenen kommen live** von Bund und Kanton, über WMTS und WMS. So
  veralten sie nicht in unserer Kopie, und wir behaupten nichts über sie. Die
  Legende kommt, wo möglich, ebenfalls vom Amt.

Der Preis der Live-Variante ist, dass die Karte ohne Netz leer bleibt und dass
ein Ausfall beim Amt wie ein Fehler bei uns aussieht. Das ist es wert: Die
Alternative wäre, amtliche Daten unter unserem Namen weiterzugeben.

### Quellen, die sich bewährt haben

| Quelle | Zugang | Anmerkung |
|---|---|---|
| swisstopo, Bundesebenen | `wmts.geo.admin.ch` | Kachelmuster `/1.0.0/{layer}/default/{stand}/3857/{z}/{x}/{y}.{fmt}` |
| Bundesebenen, Objektabfrage | `api3.geo.admin.ch` | Mit `sr=2056` abfragen, nicht mit `sr=4326` |
| Kanton Schaffhausen, Raster | `wms.geo.sh.ch` | Rendert samt amtlicher Legende |
| Kanton Schaffhausen, Vektor | `wfs.geo.sh.ch` | **WFS 1.1.0** mit `TYPENAME` und `MAXFEATURES` |
| OpenStreetMap, Netze | Overpass-API | Für Linienführungen, die amtlich nicht offen sind |
| opendata.swiss | CKAN-API | Zum Auffinden, nicht zum Beziehen |

Zwei dieser Zeilen sind teuer erkauft. **WFS 2.0.0 mit `TYPENAMES` antwortet auf
`wfs.geo.sh.ch` mit einem Serverfehler**, nur 1.1.0 mit `TYPENAME` funktioniert.
Und **die Objektabfrage des Bundes liefert bei `sr=4326` und einem Rahmen in
LV95 null Treffer**, ohne zu melden, dass die Angaben nicht zusammenpassen. Sie
gibt eine leere, gültige Antwort. Wer sie glaubt, schliesst auf «hier ist
nichts».

---

## 4 · Raster oder Vektor

Wo eine Ebene als Vektor zu bekommen ist, wird sie als Vektor genommen, auch
wenn das Raster schneller eingebunden wäre. Der Anlass war der kantonale
Strassenrichtplan: Als WMS-Raster kam er in Haarlinien und in Rot, Gelb und
Grün, also unlesbar und im falschen Farbschema. Über WFS kommen die Geometrien,
und dann ist die Darstellung unsere Entscheidung, nicht die des Servers.

Das gilt auch, wenn der Vektorweg Nacharbeit bedeutet. Beim Strassenrichtplan
waren es 2585 Einzelstücke, die zu 34 durchgehenden Linien verkettet werden
mussten, 107 km und 19 kB. Der Aufwand ist einmalig, der Nutzen bleibt.

---

## 5 · Wo zwei Quellen besser sind als eine

Wo dieselbe Sache aus zwei unabhängigen Quellen zu bekommen ist, wird sie aus
beiden geholt, und ihre Abweichung ist die beste verfügbare Prüfung. Sie ist
besser als jede Plausibilitätsüberlegung, weil sie eine Zahl liefert.

Für die Buslinien standen die Haltestellen des Bundesamts für Verkehr und die
Linienführung aus OpenStreetMap zur Verfügung, zwei Datenbestände ohne
gemeinsame Herkunft. Sie liegen im Median 4 Meter auseinander, 24 von 25 unter
50 Metern. Damit sind beide bestätigt, und der eine Ausreisser ist ein Hinweis
darauf, wo nachzuschauen ist.

---

## 6 · Was in der Legende stehen muss

Jede Ebene trägt ihre Herkunft an sich selbst, nicht in einer Sammelfussnote.
Vier Marken werden unterschieden, und sie sehen verschieden aus:

| Marke | Bedeutung |
|---|---|
| **Eigene Auswertung** | Aus diesem Projekt, mit offengelegter Rechnung |
| Amtliche Quelle | Bund oder Kanton, unverändert weitergegeben |
| Aussage eines Komitees | Steht so im Argumentarium oder auf der Website |
| Extern | Studie, Medien, Verband |

Der Grund ist derselbe wie bei den Grafiken: Wer eine Linie sieht, soll ohne
Rückfrage wissen, wessen Linie das ist. Eine eigene Auswertung neben einer
amtlichen Ebene ohne Unterscheidung darzustellen leiht sich Autorität, die uns
nicht zusteht.

## Skripte der Verkehrsflussinitiative, Reihenfolge

1. `geo/skripte/geltungsbereich.py`: die beiden Ebenen der betroffenen Strassen.
2. `python3 abstimmungsspiegel/bausteine/geo_freigeben.py <slug>`: Freigabe nach 03.
3. `geo/skripte/haushalte.py`: Anwohner und Lärmfassaden (braucht 03).
4. `geo/skripte/gemeindekarten.py`: Umkreise, Gemeindekarten, `karte.gemeinden`.
5. `geo_freigeben.py` erneut (Kandidaten, Hektaren), dann `geo/skripte/zahlen_eintragen.py`.
6. `abstimmungsspiegel/bausteine/argumente.py <slug>` und `politspiegel/bauen.py`.

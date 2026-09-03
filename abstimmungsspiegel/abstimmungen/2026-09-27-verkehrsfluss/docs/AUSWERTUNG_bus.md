# Auswertung Busverkehr · Verkehrsflussinitiative Schaffhausen

Zwei Rechnungen zur Aussage, Tempo 30 verteuere den öffentlichen Verkehr:
Braucht es zusätzliche Fahrzeuge, und wie schnell fährt der Bus überhaupt?

Beide sind eigene Auswertungen. Die Skripte liegen in [../skripte/](../skripte/),
die Ergebnisse als JSON in [../geo/02_aufbereitet/](../geo/02_aufbereitet/), die
Grafiken in [../grafiken/](../grafiken/). Die Prüffallen, in die dabei zu
tappen war, sind in [../../../docs/12_QS.md](../../../docs/12_QS.md) unter
Abschnitt 2 festgehalten.

---

## 1 · Umlaufrechnung: braucht Tempo 30 einen zusätzlichen Bus?

Gerechnet am 3. September 2026. Das ist die Zahl, die bei `pro-2` als fehlend
vermerkt ist: Die Zusatzzeit allein kostet nichts, teuer wird es erst, wenn sie
die Fahrplanreserve aufbraucht und ein weiteres Fahrzeug samt Personal nötig
wird. Ergebnisse in `geo/02_aufbereitet/umlaufrechnung.json`.

### Das Modell

```
Umlaufzeit        = Fahrzeit hin + Fahrzeit zurück + Wendezeit
Fahrzeugbedarf n  = aufgerundet( Umlaufzeit / Takt )
Reserve           = n × Takt − Fahrzeit          (die verfügbare Wendezeit)
Zusatzzeit T30    = 20 s/km × betroffene km × 2  (hin und zurück)
```

Der Fahrzeugbedarf ist eine **Treppenfunktion**. Solange die Zusatzzeit in die
Reserve passt, kostet sie nichts. Überschreitet sie eine Taktschwelle, springt
der Bedarf um ein ganzes Fahrzeug.

### Datengrundlage

Fahrzeiten je Richtung aus dem Fahrplan, abgefragt über `transport.opendata.ch`
für Kurse am Dienstag, 8. September 2026 ab 07:30, gelesen aus der Halteliste
von Endstation zu Endstation. Takt aus dem Median der Abfahrtsabstände am
Bahnhof Schaffhausen über zwei Stunden. Betroffene Kilometer aus der Geoanalyse,
Grafik G5.

Die Stadtlinien 1, 3, 4, 5 und 6 fahren im **Zehnminutentakt**, Linie 7 im
Viertelstundentakt, die Regionallinien 21 bis 25 im Halb- bis Stundentakt.

### Nachtrag: die Wendezeit ist messbar, nicht zu schätzen

Michaels Einwand am 3. September traf den wunden Punkt: Die Wendezeit muss nicht
gesetzt werden, sie steht im Fahrplan. An einer Endstation lassen sich Ankunft
und nächste Abfahrt derselben Linie getrennt abfragen; die Differenz **ist** die
planmässige Wendezeit.

Gemessen über je rund 95 Kurspaare je Endstation:

| Linie | Endstation | Wendezeit Median | Endstation | Wendezeit Median | je Umlauf |
|---|---|---|---|---|---|
| 1 | Waldfriedhof | 0 min | Herbstäcker | 5 min | 5 min |
| 3 | Krummacker | 3 min | Sommerwies | 2 min | 5 min |
| 4 | Gruben | 0 min | Birch | 2 min | 2 min |
| 6 | Falkeneck | 4 min | Buchthalen | 2 min | 6 min |

**Erster Befund: mehrere Endstationen haben gar keine planmässige Wende.** Wo 0
Minuten steht, weist der Fahrplan für die Endstation nur eine Zeit aus, der Bus
kehrt also ohne Puffer. Meine ursprüngliche Annahme von 6 Minuten je Umlauf war
für die Hälfte der Linien zu grosszügig.

### Die Taktprobe, und was sie bestätigt

Damit wird eine Gegenprobe möglich, die das ganze Modell trägt. Bei einer Linie
mit striktem Takt muss gelten:

```
Fahrzeit + Wendezeit  =  Fahrzeugzahl × Takt
```

Nachgerechnet mit allen vierzehn Kursen der sieben Stadtlinien, Hin- und
Rückrichtung je aus der Halteliste:

| Linie | Fahrzeit | Wende | Umlauf | Takt | Umlauf / Takt | Fahrzeuge | Probe |
|---|---|---|---|---|---|---|---|
| 1 | 55 min | 5 min | 60 min | 10 min | **6,00** | 6 | ja |
| 3 | 56 min | 5 min | 61 min | 10 min | 6,10 | 6 | ja |
| 4 | 38 min | 2 min | 40 min | 10 min | **4,00** | 4 | ja |
| 5 | 29 min | 11 min | 40 min | 10 min | **4,00** | 4 | ja |
| 6 | 55 min | 6 min | 61 min | 10 min | 6,10 | 6 | ja |
| 7 | 31 min | 15 min | 46 min | 15 min | 3,07 | 3 | ja |
| 8 | 17 min | 8 min | 25 min | 30 min | 0,83 | 1 | nein |

**Sechs von sieben Linien gehen auf**, drei davon exakt. Das ist keine Annahme
mehr, sondern eine Herleitung: Der Fahrzeugbedarf folgt aus gemessener Fahrzeit,
gemessener Wendezeit und gemessenem Takt. Linie 8 fällt heraus, ihr Umlauf ist
kürzer als der Takt, das Fahrzeug macht also etwas anderes dazwischen.

Zwei frühere Fehler sind damit erledigt. **Erstens die falsche Endstation:** bei
den Linien 7, 22 und 23 hatte ich sie aus dem Zielfeld der Abfahrtstafel
abgeleitet statt aus der Halteliste. Linie 23 hat zwei Äste, Bargen SH und
Kleinbuchberg; meine Fahrzeit von 8 Minuten war nur der eine. **Zweitens die
fehlende Gegenrichtung:** Linie 6 fehlte ganz, bei 4 und 7 nur die Rückfahrt.
Michael hat das gesehen, bevor ich es gesehen habe. Jetzt sind alle sieben
Stadtlinien in beiden Richtungen drin.

**Die Regionallinien 21 bis 25 bleiben draussen**, aus einem inhaltlichen Grund:
Sie bedienen von Schaffhausen aus mehrere Äste, 21 nach Beggingen, Siblingen und
Schleitheim, 24 nach Büttenhardt und Barzheim, 25 nach Ramsen und Dörflingen.
Ein Fahrzeug fährt nacheinander verschiedene Äste. «Fahrzeit hin plus zurück»
ist dort gar nicht der Umlauf, und dafür bräuchte es den Dienstplan, den der
Fahrplan nicht hergibt.

### Die Zusatzzeit, zweimal gerechnet

Die Zusatzzeit lässt sich nicht exakt bestimmen, darum steht sie als Bandbreite
zwischen zwei Modellen:

**Physikalisch, die untere Schranke.** Aus der Messung in Kapitel 16a ist je
Kurs bekannt, wie schnell der Bus zwischen den Haltestellen tatsächlich fährt.
Wo er heute schon langsamer ist, als Tempo 30 zuliesse, kostet Tempo 30 nichts.
Gerechnet wird nur die Differenz auf den Abschnitten, wo er schneller ist.

**Nach ASTRA, die obere Schranke.** 20 Sekunden je Kilometer betroffener
Strecke, Forschungsbericht 1663, unbesehen auf beide Richtungen angewendet.

| Linie | Reserve | physikalisch | nach ASTRA | Fahrzeuge heute | physikalisch | nach ASTRA |
|---|---|---|---|---|---|---|
| 1 | 5 min | 0,00 min | 3,4 min | 6 | 6 | **7** |
| 3 | 4 min | 0,00 min | 3,3 min | 6 | 6 | 6 |
| 4 | 2 min | 0,00 min | 1,5 min | 4 | 4 | 4 |
| 5 | 11 min | 2,33 min | 1,5 min | 4 | 4 | 4 |
| 6 | 5 min | 0,00 min | 3,3 min | 6 | 6 | 6 |
| 7 | 14 min | 2,01 min | 1,1 min | 3 | 3 | 3 |
| | | | **Summe** | **29** | **29** | **30** |

**Vier der sechs Linien bekommen null Zusatzzeit**, weil sie schon heute
langsamer fahren, als Tempo 30 zuliesse. Bei den Linien 5 und 7, den einzigen
mit nennenswertem Spielraum, liegt das physikalische Modell **über** dem
ASTRA-Richtwert; die beiden Modelle kreuzen sich also, sie sind keine saubere
Ober- und Untergrenze je Linie, sondern nur in der Summe.

**Nur Linie 1 kippt, und nur nach ASTRA.** Ihre 5 Minuten Reserve schrumpfen auf
1,6, und das reicht nicht mehr für die 2 Minuten, die in Neuhausen Herbstäcker
planmässig gewendet werden. Alle anderen bleiben unter der Schwelle.

**Die ehrliche Antwort lautet damit: null bis ein zusätzliches Fahrzeug**, gegen
29 heute. Das Argument «mehr Busse und Personal» ist nicht falsch, aber die
Grössenordnung liegt bei 0 bis 3 Prozent des Stadtbusbestands, nicht bei einer
neuen Linie. Genau diese Grössenordnung nennt das Komitee nicht, und genau das
steht bei `pro-2` unter «Was fehlt».

Dargestellt in `grafiken/E2_Fahrzeugbedarf.svg`, erzeugt von
`skripte/grafik_fahrzeugbedarf.py`. Die Grafik zeigt je Linie die vorhandene
Wendezeit, was Tempo 30 davon verbraucht und wo die Mindestwende liegt, damit
die Treppenfunktion sichtbar wird statt nur ihr Ergebnis.

### Was die Rechnung nicht kann

Sie gilt für den Taktfahrplan am Werktagvormittag, nicht für die Hauptverkehrszeit,
wo die Fahrzeiten ohnehin länger sind und die Reserve knapper. Sie unterstellt,
dass der Fahrplan bei Tempo 30 unverändert bleibt; in der Praxis würde man
zuerst die Fahrzeit nachführen und erst dann über Fahrzeuge reden. Und sie sagt
nichts über die Kosten je Fahrzeug, weil dafür Zahlen der Verkehrsbetriebe
nötig wären, die nicht öffentlich sind.

---

## 2 · Die Gegenprobe an der Distanz: wie schnell fährt der Bus überhaupt?

Michaels zweiter Einwand am 3. September: Die Fahrzeiten gehören an der
zurückzulegenden Distanz gemessen. Das ist möglich, weil die
Haltestellenkoordinaten des Bundesamts für Verkehr vorliegen. Weglänge aus der
Luftlinie zwischen aufeinanderfolgenden Halten, mit Umwegfaktor 1,2 auf die
Strassenlänge gebracht, geteilt durch die Fahrplanzeit.

**Das Ergebnis stellt die ganze Debatte auf den Kopf.**

| Kurs | Weg | Zeit | Reisegeschwindigkeit |
|---|---|---|---|
| 1 Waldfriedhof → Herbstäcker | 8,28 km | 30 min | **16,6 km/h** |
| 4 Gruben → Birch | 5,13 km | 18 min | 17,1 km/h |
| 1 Herbstäcker → Waldfriedhof | 7,36 km | 25 min | 17,7 km/h |
| 3 und 6 | rund 9,5 km | 28 min | 20,2 bis 20,3 km/h |
| 5 Schlossweiher → Bahnhof | 6,06 km | 17 min | 21,4 km/h |
| 7 Bahnhof → Neuhausen | 5,98 km | 15 min | 23,9 km/h |
| 5 Bahnhof → Schlossweiher | 5,81 km | 13 min | **26,8 km/h** |

**Kein einziger der zehn gemessenen Kurse erreicht im Mittel 30 km/h.** Der
Mittelwert liegt bei 20,2.

### Und die Fahrdynamik erklärt, warum

Die Haltestellen liegen im Mittel **382 Meter** auseinander. Rechnet man einen
Abschnitt dieser Länge mit realistischen Werten für einen Bus, 1,0 m/s²
Beschleunigung und 1,2 m/s² Verzögerung, ergibt sich: Selbst ohne jeden Verkehr,
ohne Lichtsignal und ohne Fussgängerquerung kommt der Bus auf **höchstens rund
34 km/h Durchschnitt** zwischen zwei Halten. Beschleunigen und Bremsen brauchen
den Abschnitt auf, bevor 50 erreicht wäre.

**Die Spanne zwischen 50 und 30, um die im Abstimmungskampf gestritten wird,
existiert für einen Stadtbus in dieser Form gar nicht.** Der ASTRA-Richtwert von
20 Sekunden je Kilometer stammt aus Messungen am fliessenden Verkehr; für eine
Linie mit Halt alle 380 Meter ist er eher die Obergrenze als der Erwartungswert.

**Was das für die frühere Rechnung heisst:** Der Befund, Linie 1 brauche ein
siebtes Fahrzeug, steht auf einer Zusatzzeit von 3,4 Minuten, die mit eben diesem
Richtwert gerechnet ist. Linie 1 ist zugleich die langsamste Linie überhaupt,
16,6 km/h. Die 3,4 Minuten sind damit eher zu hoch angesetzt, und der Befund
verliert an Kraft. Er bleibt als Möglichkeit stehen, nicht als Feststellung.

### Zwei Korrekturen, beide auf Michaels Einwände hin

**Erstens die Weglänge.** Der erste Anlauf rechnete Luftlinie zwischen den
Halten mal einem gesetzten Umwegfaktor 1,2. Das Busnetz liegt aber vor, also
gehört der Weg entlang der Achsen gesucht. Ein erster Versuch mit dem
*vereinfachten* Netz scheiterte, weil die Verkettung die Verzweigungen zerstört
hatte; fast jeder Abschnitt fiel auf die Luftlinie zurück, und der «gemessene»
Faktor 1,198 war nur die eigene Annahme, die zu sich selbst zurückkam. Neu
gebaut aus den 2566 unvereinfachten OpenStreetMap-Wegen: 16'521 Knoten,
Haltestellen daraufgezogen mit Median 4 m, Dijkstra von Halt zu Halt.

**Gemessener Umwegfaktor 1,08 bis 1,33, im Mittel 1,15**, nicht die gesetzten
1,20. Von 246 Abschnitten liessen sich 79 nicht über das Netz führen, dort steht
weiterhin Luftlinie mal 1,2; das ist der verbleibende Vorbehalt.

**Zweitens die Haltezeit.** Die Reisegeschwindigkeit enthält das Ein- und
Aussteigen. Zieht man es ab, steigt die reine Fahrgeschwindigkeit, und genau die
entscheidet, ob Tempo 30 überhaupt greift. Die Haltezeit ist damit der wichtigste
Parameter der ganzen Rechnung, und sie ist nicht direkt gemessen.

**Sie lässt sich aber aus den Daten eingrenzen.** Weil bei Haltestellen alle rund
370 Meter physikalisch höchstens etwa 34 km/h Schnitt möglich sind, darf die
angesetzte Haltezeit nicht so hoch sein, dass die rechnerische
Fahrgeschwindigkeit darüber läge. Die schärfste Schranke liefert der schnellste
Kurs, Linie 5 vom Bahnhof zum Schlossweiher: **höchstens 14 Sekunden je Halt.**
In der Literatur gilt 10 Sekunden als Planungsrichtwert für die reine
Fahrgastwechselzeit; Türöffnen und -schliessen kommen dazu. Angesetzt sind
deshalb **12 Sekunden**, in der Mitte zwischen Literaturwert und Schranke.

**Das ändert das Bild, und meine frühere Aussage war zu absolut.** Samt Haltezeit
erreicht kein Kurs 30 km/h. Ohne Haltezeit bleiben 12 der 14 Kurse darunter, aber
**zwei kommen darüber**: Linie 5 Richtung Schlossweiher mit 31,3 und Linie 7
Richtung Neuhausen mit 30,3 km/h. Auf diesen beiden Auswärtsrichtungen greift
Tempo 30 tatsächlich. Die richtige Aussage lautet also nicht «der Bus ist ohnehin
langsamer als 30», sondern: **Tempo 30 kostet etwas, aber nur auf wenigen
Abschnitten und deutlich weniger, als die Spanne 50 zu 30 nahelegt.**

Wie stark das Ergebnis an der Haltezeit hängt, zeigt die Empfindlichkeit:

| Haltezeit je Halt | Anteil an der Fahrplanzeit | Kurse über 30 km/h |
|---|---|---|
| 10 s | 15 % | 0 von 14 |
| **12 s** | 18 % | **2 von 14** |
| 15 s | 22 % | 3 von 14 |
| 20 s | 29 % | 4 von 14 |
| 30 s | 44 % | 10 von 14, physikalisch unmöglich |

Die Zeile mit 30 Sekunden ist der Beleg für die Schranke: Sie ergäbe
Fahrgeschwindigkeiten bis 57 km/h, was mit Halt alle 370 Meter nicht geht.

**Weitere Grenzen**, die dazugehören: Die Fahrplanzeiten sind auf ganze Minuten
gerundet, weshalb Werte je Abschnitt unbrauchbar sind und nur die
Gesamtgeschwindigkeit je Kurs zählt. Gemessen ist je ein Kurs in der
Hauptverkehrszeit, nicht der Tagesdurchschnitt. Und die Haltezeit ist je Halt
gleich angesetzt, obwohl sie am Bahnhof deutlich höher liegt als an einer
Quartierhaltestelle.

Erzeugt von `skripte/grafik_reisegeschwindigkeit.py`, Daten in
`geo/02_aufbereitet/reisegeschwindigkeit.json`, Grafik als
`grafiken/E1_Reisegeschwindigkeit.svg` auf der Karte von `pro-2`.

### Der bessere Massstab für die Regionallinien: der Anschluss an den Zug

Weil das Fahrzeugmodell bei den Astlinien nicht greift, wurde für sie die Frage
gestellt, die sachlich näher liegt. **Ein Regionalbus, der seinen Zug verpasst,
kostet die Fahrgäste nicht Sekunden, sondern eine halbe oder eine ganze Stunde.**
Gemessen als Abstand zwischen Busankunft in Schaffhausen und der nächsten
Zugabfahrt, bei mindestens 2 Minuten Umsteigezeit:

| Linie | Anschlüsse | kürzester | Median | unter 5 min | Zusatzzeit Tempo 30 |
|---|---|---|---|---|---|
| 24 | 17 | **2 min** | 4 min | 11 | 3,6 min |
| 25 | 12 | 3 min | 4 min | 7 | 2,7 min |
| 632 | 11 | 3 min | 4 min | **11 von 11** | 0,6 min |
| 634 | 6 | 2 min | **2 min** | 5 | 0,6 min |
| 22 | 9 | 3 min | 4 min | 5 | 1,6 min |
| 23 | 5 | 2 min | 6 min | 2 | 0,8 min |
| 21 | 17 | 5 min | 7 min | 0 | 3,9 min |
| 630 | 5 | 5 min | 10 min | 0 | 0,6 min |

**Der Befund ist ein struktureller, kein rechnerischer.** Im Median halten die
Anschlüsse fast überall, nur der kürzeste Anschluss der Linie 24 bricht.
Entscheidend ist aber die Verteilung: **41 der 82 gemessenen Anschlüsse haben
weniger als 5 Minuten Luft, 78 weniger als 10.** Bei den Linien 632 und 634 liegt
*jeder* gemessene Anschluss unter 5 Minuten. Ein System mit dieser
Umsteigezeit hat praktisch keine Reserve; jede zusätzliche Minute Fahrzeit trifft
direkt auf eine Anschlussbindung.

**Für den Abstimmungsspiegel heisst das:** Auf den Regionallinien ist die Frage
nicht, ob ein Fahrzeug mehr nötig wird, sondern ob Anschlüsse brechen. Diese
Frage lässt sich mit dem Fahrplan grob prüfen, aber nicht entscheiden, weil
Anschlüsse bei einer Fahrplanänderung neu gelegt werden können. Was sich sagen
lässt, und was auf die Seite gehört: Die Umsteigezeiten sind heute so knapp
bemessen, dass eine Verlängerung der Busfahrzeit ohne Fahrplananpassung nicht
folgenlos bliebe. Das stützt das Anliegen der Initiative, ohne es zu beweisen.

### Ergebnis auf den belastbaren Linien

| Linie | Fahrzeuge | Reserve | Tempo 30 kostet | bleibt | Minimum beobachtet | Folge |
|---|---|---|---|---|---|---|
| **1** | 6 | 5 min | 3,4 min | **1,6 min** | 2 min | **siebtes Fahrzeug** |
| 3 | 6 | 4 min | 3,3 min | 0,7 min | 0 min | passt, hauchdünn |
| 4 | 4 | 2 min | 1,5 min | 0,5 min | 0 min | passt, hauchdünn |
| 6 | 6 | 5 min | 3,3 min | 1,7 min | 1 min | passt, knapp |
| 8 | 1 | 12 min | 1,4 min | 10,6 min | 1 min | passt |

**Das kehrt mein erstes Ergebnis um.** Mit gesetzter Wendezeit kam heraus, keine
Linie brauche ein zusätzliches Fahrzeug. Mit gemessener Wendezeit kippt Linie 1:
Ihre Reserve von 5 Minuten reicht nach Abzug der 3,4 Minuten nicht mehr für die
2 Minuten, die in Herbstäcker planmässig gewendet werden. Die Linien 3, 4 und 6
bleiben nur deshalb knapp darunter, weil an ihren Endstationen ohnehin kaum
gewendet wird.

Auf den fünf belastbaren Linien heisst das: **23 Fahrzeuge heute, 24 mit
Tempo 30.** Ein zusätzliches Fahrzeug samt Personal, für fünf von zwölf Linien
gerechnet.

**Damit ist das ÖV-Argument der Initiative auf diesen Linien sachlich gestützt**,
und zwar besser, als das Komitee es selbst belegt hat. Das gehört genau so auf
die Seite. Zugleich bleibt der Vorbehalt: gerechnet ist flächendeckendes
Tempo 30, was gar nicht zur Abstimmung steht, und die Fahrzeiten stammen aus je
einem Kurs.

### Ergebnis der ersten Rechnung, mit gesetzter Wendezeit

Bei einer angenommenen Mindestwendezeit von 6 Minuten je Umlauf braucht **keine
einzige Linie ein zusätzliches Fahrzeug**. Das klingt nach einer klaren Antwort
auf das Argument der Initiative, ist aber keine, denn das Ergebnis hängt
vollständig an einer Annahme, die wir nicht kennen:

| Wendezeit je Umlauf | 15 s/km | 20 s/km | 25 s/km | 30 s/km |
|---|---|---|---|---|
| 4 Minuten | 42 → 45 | 42 → 45 | 42 → 45 | 42 → 45 |
| **6 Minuten** | 45 → 45 | **45 → 45** | 45 → 45 | 45 → 46 |
| 8 Minuten | 45 → 46 | 45 → 46 | 45 → 46 | 45 → 46 |
| 10 Minuten | 46 → 46 | 46 → 47 | 46 → 48 | 46 → 51 |
| 12 Minuten | 47 → 50 | 47 → 52 | 47 → 52 | 47 → 53 |

Gelesen als «Fahrzeuge heute → Fahrzeuge mit Tempo 30».

**Das Modell reagiert stärker auf die angenommene Wendezeit als auf Tempo 30.**
Damit ist die Frage nicht beantwortet, und genau das ist das Ergebnis: Ohne den
tatsächlichen Umlaufplan der Verkehrsbetriebe lässt sich das Argument weder
bestätigen noch widerlegen. Wer es bestätigt oder widerlegt, ohne diese Zahl zu
kennen, behauptet mehr, als er weiss.

### Was die Rechnung trotzdem zeigt

**Linie 5 ist der Kipppunkt.** Sie verträgt rechnerisch 2,0 Minuten zusätzliche
Umlaufzeit, Tempo 30 brächte 1,5. Bleiben 0,5 Minuten Luft. Alle anderen Linien
haben mehr Spielraum:

| Linie | verträgt | Tempo 30 bringt | Luft |
|---|---|---|---|
| 5 | 2,0 min | 1,5 min | **0,5 min** |
| 7 | 5,0 min | 1,1 min | 3,9 min |
| 4 | 6,0 min | 1,5 min | 4,5 min |
| 3 | 8,0 min | 3,3 min | 4,7 min |
| 8 | 6,0 min | 1,4 min | 4,6 min |
| 1 | 9,0 min | 3,4 min | 5,6 min |
| 6 | 9,0 min | 3,3 min | 5,7 min |
| 21 | 16,0 min | 7,7 min | 8,3 min |
| 24 | 20,0 min | 7,2 min | 12,8 min |
| 22, 23, 25 | 22 bis 44 min | 1,7 bis 5,5 min | reichlich |

**Der Befund kehrt die Intuition um.** Die Regionallinien 21, 24 und 25 sammeln
zwar die meiste Zusatzzeit, haben aber wegen des weiten Takts auch die grösste
Reserve. Eng wird es bei den kurzen, dicht getakteten Stadtlinien, obwohl deren
Zusatzzeit klein ist. Die Grafik G5 zeigt darum das Gegenteil dessen, was für
den Fahrzeugbedarf zählt: Sie sortiert nach Zusatzzeit, entscheidend ist aber
das Verhältnis von Zusatzzeit zu Reserve.

### Vorbehalte, vollständig

- Die Mindestwendezeit ist gesetzt, nicht erhoben. Sie ist der wichtigste
  Parameter und stammt nicht aus den Daten.
- Für die Linien 5, 7, 8, 22, 23 und die Äste von 21, 24, 25 wurde nur eine
  Richtung gemessen, die Gegenrichtung ist als gleich lang angenommen.
- Der Takt ist der Hauptverkehrszeit entnommen. Ausserhalb ist er weiter, die
  Reserve also grösser.
- Die Zusatzzeit unterstellt, dass heute überall 50 gefahren wird. In dichten
  Stadtabschnitten mit kurzen Haltestellenabständen erreichen Busse zwischen
  den Halten selten 50, dort ist die reale Wirkung kleiner.
- Gerechnet ist flächendeckendes Tempo 30 auf allen betroffenen Kantonsstrassen.
  Das steht gar nicht zur Abstimmung.

### Für die Seite

Diese Rechnung kann auf die Karte von `pro-2`, aber nur mit der
Empfindlichkeitstabelle daneben. Ihre Aussage ist nicht «kein zusätzlicher Bus
nötig», sondern «die Frage lässt sich ohne den Umlaufplan der Verkehrsbetriebe
nicht entscheiden, und der Fahrzeugbedarf hängt an anderen Linien als der
Fahrzeitverlust». Das ist ehrlicher und für die Leserin nützlicher als eine
Zahl, die nicht trägt.

**Nachtrag:** Diese Anfrage hat sich erledigt, die Wendezeiten stehen im
Fahrplan und sind oben gemessen. Offen bleibt nur noch der Umlaufplan der
Regionallinien, die keinen strengen Takt fahren.

---

### Und zur Darstellung des Strassenrichtplans

Die WMS-Ebene des Kantons war für diese Seite unbrauchbar: haarfeine Linien, die
über einer Grundkarte verschwinden, und eine Farbskala in Rot, Gelb und Grün,
also genau die Ampel, die wir überall sonst entfernt haben. An einem Rasterbild
lässt sich beides nicht ändern.

Ersetzt durch **Vektoren aus dem WFS** desselben Amts. Wichtig für die
Wiederholung: Der Dienst liefert nur unter WFS 1.1.0 mit `TYPENAME` und
`MAXFEATURES`; Version 2.0.0 mit `TYPENAMES` antwortet mit HTTP 500.

Aus 2585 Objekten wurden nach Verkettung und Vereinfachung auf 5 Meter
**34 Linienzüge mit 107 km**, 19 kB. Gezeichnet in der Farbsprache des Projekts:
überregional als kräftige, regional als dünnere Graphitlinie, unterschieden
durch Strichstärke statt durch Farbe. Legende gebaut statt vom Server geholt.

Nebenbei ist damit die Datengrundlage für die exakte Berechnung der beiden
Geltungsbereiche vorhanden, siehe nächste Schritte.

---

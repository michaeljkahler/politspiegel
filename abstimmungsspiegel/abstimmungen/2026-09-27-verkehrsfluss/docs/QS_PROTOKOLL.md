# QS-Protokoll · Verkehrsflussinitiative Schaffhausen

Was geprüft wurde, was durchfiel und was daraus geworden ist. Die Prüfliste
selbst steht in [../../../docs/12_QS.md](../../../docs/12_QS.md), die
Nummerierung unten bezieht sich darauf.

Ein Protokoll und nicht bloss eine Liste von Häkchen: Ein Fehler, dessen Ursache
nicht aufgeschrieben ist, kommt wieder. Vier der sechs inhaltlichen Fehler unten
hat Michael gefunden, nicht das Prüfskript. Das ist der Grund, weshalb die
Prüfliste in 12_QS.md die Fallen einzeln nennt statt allgemein zu mahnen.

---

## Stand

| Bereich | Stand |
|---|---|
| 1 Inhalt | offen: 1.2 drei Fundstellen. 1.9 Anhörung als Bedingung gestrichen (3.9.2026) |
| 2 Zahlen | durchlaufen, sechs Korrekturen, siehe unten |
| 3 Geodaten | bestanden, 4 von 4 Ebenen freigegeben |
| 4 Layout | bestanden am 3.9.2026, acht Befunde behoben |
| 5 Veröffentlichung | offen, hängt an 1.9 |

---

## Was bei den Zahlen durchfiel

### 2.2 Kleine Zahlen als Zufall geprüft

**Befund.** Die Gegenseite nennt eine starke Zunahme der Verkehrstoten ohne
Zahlen. Tatsächlich 2 auf 6 Fälle, also 200 Prozent, ohne Bezug auf das
Bevölkerungswachstum.

**Korrektur.** Bei einem Erwartungswert von 4 liegt die Wahrscheinlichkeit, 1
bis 8 Fälle zu beobachten, bei 96 Prozent. Eine Zunahme dieser Grösse ist von
Zufall nicht zu unterscheiden. Im ersten Anlauf hatte ich 93 Prozent
geschrieben; nachgerechnet sind es 96. Der Fehler stand bereits im Konzept und
in den Daten und ist an beiden Orten berichtigt.

**Gelernt.** Auch die Prüfzahl gehört nachgerechnet, nicht nur die geprüfte.

### 2.6 Herleitung nicht im Kreis

**Befund, von Michael.** Auf seine Frage, warum ich die Weglänge als Luftlinie
nehme, obwohl die Strassenachsen vorliegen, kam heraus: Mein erster
Netzaufbau baute den Graphen aus dem **vereinfachten** Netz. Die Verkettung
hatte die Kreuzungstopologie zerstört, worauf fast jeder Abschnitt auf Luftlinie
mal 1,2 zurückfiel. Der «gemessene» Umwegfaktor 1,198 war damit nichts anderes
als der gesetzte Faktor 1,2, der sich selbst bestätigte.

**Korrektur.** Neu aufgebaut aus 2566 unvereinfachten OSM-Wegen, 16 521 Knoten,
grösste Komponente 81,3 Prozent. Gemessener Faktor 1,08 bis 1,33, im Mittel
1,15. Die Geschwindigkeiten fielen dadurch von 16,6 bis 26,8 auf 15,9 bis
24,1 km/h. 79 von 246 Abschnitten fallen weiterhin auf Luftlinie zurück, und
das steht in der Fussnote der Grafik.

**Gelernt.** Wer einen Faktor an Daten messen will, muss prüfen, ob dieser
Faktor bei der Erzeugung dieser Daten schon verwendet wurde.

### 2.7 Alle Fälle vollständig

**Befund, von Michael.** «Du hast die Linie 6 und die Kehrlinie für 4 und 7
vergessen.» Zutreffend: Ich hatte 7 von 14 Kursen, also nur die Hinrichtungen
und eine Linie überhaupt nicht.

**Korrektur.** Alle sieben Stadtlinien in beiden Richtungen, 14 Kurse. Die
Endstationen werden jetzt aus der Halteliste gelesen, nicht aus dem Zielfeld der
Abfahrtstafel; über das Zielfeld waren die Endstationen der Linien 7, 22 und 23
falsch, und Linie 23 hat zwei Äste.

**Gelernt.** Eine Auswertung über «die Linien» muss die Zahl der Fälle nennen,
dann fällt eine Lücke auf.

### Ein- und Aussteigezeit

**Befund, von Michael.** «Wir sollten auch noch eine Ein- und Aussteigezeit
berücksichtigen, gibt es dazu Daten oder Studien?»

Das war der Einwand mit der grössten Folge. Meine Aussage «kein Bus erreicht 30,
also hat Tempo 30 wenig Spielraum» hielt der Prüfung nicht stand: Rechnet man
die Haltezeit heraus, überschreiten 2 von 14 Kursen die 30 km/h.

**Korrektur.** Die Haltezeit wurde aus den Daten begrenzt statt aus der
Literatur gesetzt: Bei rund 370 Metern Haltestellenabstand ist die
Fahrgeschwindigkeit physikalisch auf etwa 34 km/h begrenzt, also muss die
Haltezeit bei 14 Sekunden oder darunter liegen, sonst ergäbe sich eine unmögliche
Fahrgeschwindigkeit. Angesetzt sind 12 Sekunden. Die Aussage auf der Seite ist
entsprechend berichtigt, und die Grafik zeigt beide Werte, Reisegeschwindigkeit
samt Haltezeit und Fahrgeschwindigkeit ohne.

**Gelernt.** Eine Grenze, die aus den eigenen Daten folgt, ist belastbarer als
ein Literaturwert, und sie lässt sich überprüfen.

### Wendezeit gemessen statt gesetzt

**Befund, von Michael.** «Bei den Takten kennst du ja die Distanz zwischen den
Haltestellen sowie die Endstationen, somit könntest du den Takt sauber
herleiten. Und allfällige Puffer klären.»

Meine Annahme von 6 Minuten Wendezeit je Umlauf war für die Hälfte der Linien
zu grosszügig. Mehrere Endstationen haben gar keine planmässige Wende.

**Korrektur.** Die Wendezeit steht im Fahrplan: An einer Endstation lassen sich
Ankunft und nächste Abfahrt derselben Linie getrennt abfragen, und die Differenz
ist die planmässige Wendezeit. Gemessen über je rund 95 Kurspaare. Bestätigt
durch die Taktprobe, die bei sechs von sieben Linien aufgeht, bei drei davon
exakt.

**Gelernt.** Vor jeder Annahme die Frage, ob die Grösse irgendwo bereits steht.

### Der Zeitkostensatz in der Kosten-Nutzen-Rechnung

**Befund.** Michael nahm an, die Rechnung verwende den Staukostenwert des ASTRA,
und nannte das als Grund, sie weglassen zu wollen.

**Korrektur, gegen Michael.** Sie rechnet mit `VTTS = 42.50`, dem Zeitkostensatz
nach ARE und VSS SN 641 822a. Der Ansatz war korrekt gewählt. Der Grund, die
Rechnung weglassen zu müssen, ist ein anderer und ein schwerwiegenderer, siehe
[ENTSCHEIDE.md](ENTSCHEIDE.md).

**Gelernt.** Auch ein Einwand gehört geprüft, nicht nur übernommen. Wäre die
Begründung so stehen geblieben, hätte im Konzept ein falscher Vorwurf gegen eine
korrekte Rechnung gestanden.

---

## Was bei den Geodaten geprüft wurde

Am 3. September 2026, durch `bausteine/geo_freigeben.py`. 4 von 4 Ebenen
freigegeben, keine zurückgehalten. Der Bericht steht in
[../geo/PRUEFBERICHT.md](../geo/PRUEFBERICHT.md).

Zusätzlich von Hand:

**3.6 Zwei Quellen verglichen.** Bushaltestellen des Bundesamts für Verkehr
gegen die Linienführung aus OpenStreetMap: Median 4 Meter Abstand, 24 von 25
unter 50 Metern. Beide Quellen damit bestätigt.

**Zwei Fehler, die eine Gegenprüfung fand.** Die Gemeinde heisst in der
Auswertungstabelle «Bargen», im GeoJSON aber «Bargen (SH)»; der Sprung in der
Gemeindeauswahl wäre ins Leere gelaufen. Und in fünf Gemeinden gibt es
überhaupt keine Kandidatenlinie, weil dort keine betroffene Strasse innerhalb
300 Metern einer sensiblen Nutzung liegt. Beides behoben: Der Name wird beim
Umprojizieren normalisiert, und die fünf Gemeinden stehen als gesperrte
Einträge mit dem Vermerk «keine Kandidaten» im Menü, statt still nichts zu tun.

**Zwei Schnittstellenfallen**, beide in 13_GEODATEN.md festgehalten, weil sie
jede künftige Vorlage wieder treffen: WFS 2.0.0 mit `TYPENAMES` antwortet auf
`wfs.geo.sh.ch` mit einem Serverfehler, und die Objektabfrage des Bundes liefert
bei `sr=4326` mit einem LV95-Rahmen eine leere, gültige Antwort.

---

## Was bei der Layout-QS durchfiel

Am 3. September 2026, bei 1280 und 390 Pixeln, in hell und dunkel, in einem
Browser ohne Fenster.

| Nr | Befund | Behoben |
|---|---|---|
| 4.8 | **Die zehn Mininetze fehlten vollständig.** Dem Abschnittsbaustein war ein Argument zu viel übergeben worden, worauf der ganze Netzblock im Parameter für «offen» landete. Der Abschnitt zeigte nur seinen Einleitungstext | ja, Seite dadurch 938 Pixel höher |
| 4.2 | In den Werturteil-Zeilen der Übersicht lief «Werturteil, wird nicht bewertet» über «ohne Note» | ja, zusammengelegt zu «Werturteil, ohne Note» |
| 4.4 | Im Kartenviewer war die Karte 560 Pixel hoch, die Ebenenliste rund 880; rechts klaffte eine grosse Leerfläche | ja, Karte zieht auf Sidebarhöhe |
| 4.3 | Kästen und Trennlinien endeten bei 80 Zeichen mitten in der Spalte, während die Karten daneben bis zum Rand gingen | ja, Zeilenmass sitzt jetzt auf dem Text |
| 4.4 | Die Kantonsratskarten waren ungleich hoch | ja, unten bündig |
| — | Der Grafikkasten hiess «Eigene Auswertung · Auswertung» | ja, nennt jetzt die Zahl der Grafiken |
| 4.1 | Auf 390 Pixeln lief die zusammengelegte Werturteil-Zelle über den Rand | ja |
| — | In `E2_Fahrzeugbedarf.svg` waren die linken Beschriftungen abgeschnitten und der rechte Text von Linie 7 lief aus dem Bild | ja, Ränder erweitert, Fussnote umgebrochen |

Die Tabellen wurden zunächst ebenfalls als Überlauf gemeldet. Das war ein
Fehlalarm meines Prüfskripts: Eine Tabelle in einem scrollenden Kasten ragt
immer über den Rand, das ist ihr Zweck. Der Test prüft seither, ob ein Vorfahr
scrollt, und meldet nur echte Überläufe. Ein Test, der harmlose Fälle meldet,
gewöhnt einen daran, Meldungen zu übergehen.

---

## Bestanden: die amtliche Gegenprobe

**5.6** Der Ratsblock zeigt für alle sechs namentlichen Abstimmungen vom
19. Mai 2025 dieselben Zahlen wie das amtliche Abstimmungsmagazin: 35 : 20 bei
der Initiative, 39 : 16 beim Gegenvorschlag, 37 : 17 bei der Stichfrage. Auf die
Stimme genau, aus den Wortprotokollen gerechnet, nicht abgeschrieben.

Das ist die stärkste Einzelprüfung der ganzen Kette, weil sie eine amtliche Zahl
gegen die eigene Verarbeitung stellt und dabei Protokollauslesung, Namenszuordnung
und Auszählung auf einmal prüft.

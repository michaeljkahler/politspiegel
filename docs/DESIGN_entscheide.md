# Design-Entscheide Kantonsratsdashboard

Stand: 1. September 2026. Festgelegt in drei Fragerunden auf Basis der Vergleichsseite
`output/design-vorschlaege.html`. Diese Datei ist die verbindliche Referenz für alle
weiteren Umbauten.

---

## 1 · Farbsystem

Grundsatz: **Parteifarben und Abstimmungsfarben sind zwei getrennte Sprachen.** Keine Farbe
darf für beides stehen.

### Abstimmungsskala (parteiunabhängig)

| Bedeutung | Fläche hell | Text auf Weiss | Fläche/Text dunkel | Text auf der Fläche |
|---|---|---|---|---|
| Ja | `#0F766E` | `#0C6A62` | `#3FB3A8` | hell / dunkel |
| Nein | `#8E44AD` | `#7E3C9A` | `#C08AD8` | hell / dunkel |
| Enthaltung | `#8B93A1` | `#646C79` | `#A9B1BE` | hell / dunkel |
| abwesend | `#DFE3E8` | `#6E7783` | `#39434F` | dunkel / hell |

**Warum nicht Grün/Rot:** Grün ist die SVP, Rot die SP. In der Fraktionsansicht stünde
dieselbe Farbe für zwei Dinge. Zusätzlich fallen Grün und Rot bei Deuteranopie fast
zusammen (ΔE 12), Petrol und Purpur bleiben klar getrennt (ΔE 35 bzw. 52).

### Parteifarben

Basis: [srfdata/swiss-party-colors](https://github.com/srfdata/swiss-party-colors),
CC BY-SA 4.0. Methodik: nah am Original, gleiches visuelles Gewicht, reduzierte Sättigung.

| Partei | Fläche hell | Text auf Weiss | Fläche/Text dunkel |
|---|---|---|---|
| SVP, JSVP, SVP Senioren/Agro/KMU | `#4B8A3E` | `#417B36` | `#6BA55E` |
| EDU | `#A65E42` | `#8E4E36` | `#C08268` |
| SP, JUSO | `#F0554D` | `#CE362E` | `#F0554D` |
| Grüne, Junge Grüne | `#84B547` | `#5D8132` | `#9BC961` |
| AL | `#B02E7A` | `#A02A6F` | `#D470AC` |
| GLP | `#C4C43D` | `#6F6F16` | `#D2D257` |
| EVP | `#DEAA28` | `#8A6606` | `#EABE4F` |
| FDP, JF | `#3872B5` | `#2F639F` | `#6D9FD8` |
| Die Mitte, CVP | `#D6862B` | `#9E590C` | `#E3A053` |
| parteilos | `#A8AEB6` | `#69707A` | `#C3C9D0` |

**Zwei bewusste Abweichungen vom SRF-Standard, beide beschlossen:**

1. **AL wird Magenta** statt Dunkelrot `#A83232`. Sonst liegen AL, SP und EDU im selben
   Rotbereich und sind in Ranglisten nicht auseinanderzuhalten.
2. **GLP bekommt eine dunklere Textvariante** `#6F6F16` statt `#999900`. Das SRF-Gelb
   erreicht auf Weiss nur 4.3:1, die dunklere Variante 5.3:1 und damit WCAG AA.

**Fraktionsfarben** = Farbe der jeweils grössten Partei. AL-Grüne läuft über die AL,
damit sie sich von SP-JUSO-Grüne unterscheidet.

### Regeln für die Anwendung

- Jede Farbe hat drei Rollen: Fläche, Text auf hellem Grund, Variante für Dunkelmodus.
  Alle Textvarianten erreichen mindestens 4.5:1 (WCAG AA).
- **Nie Farbe allein.** Jeder farbige Balken bekommt seine Zahl direkt hineingeschrieben,
  jeder Punkt eine Beschriftung oder einen Tooltip.
- Legenden stehen unmittelbar bei den Daten, nie am Seitenkopf.
- Die Oberfläche selbst hat **keine** eigene Akzentfarbe. Aktive Zustände werden über
  Tiefe und Schriftfarbe gelöst, damit keine UI-Farbe mit einer Datenfarbe verwechselt wird.
  Einzige Ausnahme: der Fokusring.

---

## 2 · Layout und Bedienung

| Thema | Entscheid |
|---|---|
| Navigation | Seitenleiste links, 236 px, per Pfeil auf 64 px einklappbar. Unter 960 px wird sie zur Overlay-Leiste mit Hamburger und Scrim. |
| Rubriken | Flach, acht Punkte: Zuletzt entschieden · Abstimmungen · Ratsmitglieder · Fraktionen · Themen · Ranglisten · Interessenbindungen · Wer stimmt wie ich? «Mitglied im Detail» entfällt als eigener Punkt und wird zur Detailseite aus der Mitgliederliste. «Überblick» geht in «Zuletzt entschieden» auf. |
| Flächenstil | Mischung. Weiche Karten mit 14 px Radius und leichtem Schatten für interaktive Blöcke, Haarlinien und Weissraum für Tabellen, Ranglisten und Punktraster. |
| Dichte | Luftig. Fraktionsaufteilung und Namenslisten stecken hinter `<details>`, standardmässig zu. |
| Startseite | «Zuletzt entschieden»: die neuste Sitzung mit allen Abstimmungen zuoberst, Kennzahlen darunter. |
| Dunkelmodus | Folgt `prefers-color-scheme`, Umschalter überschreibt und merkt sich die Wahl. |

---

## 3 · Typografie

- **Archivo** 500/600/700 für Titel, Kennzahlen und alle Tabellenziffern.
- **Public Sans** 400/500/600/700 für Fliesstext und Bedienelemente.
- Zahlenkolonnen immer mit `font-variant-numeric: tabular-nums`.
- Fliesstext auf 62 bis 70 Zeichen Zeilenlänge begrenzen.
- Georgia entfällt vollständig.

---

## 4 · Sprache

- Ranglisten werden sachlich benannt. «Abwesenheitskönige» wird zu «Höchste
  Abwesenheitsquote», «Ja-Sager» zu «Höchste Zustimmungsquote». Gleiche Daten, keine Wertung.
- Umkehrabstimmungen bekommen einen sichtbaren Hinweisblock in der Karte, nicht nur eine
  Fussnote.

---

## 5 · Aufbereitung der Abstimmungstexte

Die Quelldaten benennen Abstimmungen entweder rein formal («Antrag P. Scheck») oder sehr
weitschweifig («Postulat Nr. 2026/4 von Linda De Ventura vom 30. März 2026 betreffend
Stärkung des Medienplatzes Schaffhausen»). Beides ist als Überschrift unbrauchbar.

### Überschrift

Regeln, implementiert in `scripts/prototyp.py`, Funktion `ueberschrift()`:

1. **Vorstösse** (Motion, Postulat, Interpellation, Petition, Volksmotion): Der Sachtitel
   nach «betreffend» oder «mit dem Titel» wird zur Überschrift, die formale Referenz
   («Postulat 2026/4, Linda De Ventura») rückt als kleine Zeile darunter.
2. **Anträge und andere kurze Titel** unter 42 Zeichen: Der erste sinntragende Teil des
   Detailtexts wird angehängt, abgeschnitten vor «wie folgt» oder dem ersten Doppelpunkt.
   Aus «Antrag P. Scheck» wird «Antrag P. Scheck: Streichung Art. 75 Abs. 1bis».
3. **Leerer Titel** (289 von 1441 Abstimmungen): erster Teilsatz aus den Details.
4. Überschriften über 108 Zeichen werden gekürzt. Der vollständige Originaltitel bleibt
   im `title`-Attribut erhalten, es geht nichts verloren.

### Gruppierung

Abstimmungen werden **nach Geschäft gebündelt**, nicht flach aufgelistet. In der Sitzung
vom 24.08.2026 gehören 12 der 14 Abstimmungen zu vier Geschäften, allein fünf zum
Pensionskassengesetz. Der Betreff wird aus dem Geschäftstitel gezogen (Text nach
«betreffend», «zur», «zum», «über»); er steht einmal als Zwischentitel statt fünfmal in
den Karten. Der volle Geschäftstitel steht klein unter dem Zwischentitel.

Gruppen erscheinen in der Reihenfolge ihres ersten Auftretens. Ein Geschäft, das später
in der Sitzung nochmals aufgerufen wird, sammelt seine Abstimmungen in derselben Gruppe;
die Nummer auf jeder Karte hält die tatsächliche Reihenfolge nachvollziehbar. Abstimmungen
ohne Geschäft kommen als Block «Einzelne Vorlagen und Vorstösse» ans Ende.

---

## 6 · Umkehrabstimmungen

**488 der 1441 Abstimmungen sind richtungsverkehrt** (34 %). Die Klassierung liegt in
`data/umkehr_zuordnung.json` als `ja_ist_zustimmung` vor, erzeugt von
`scripts/umkehr_regeln.py`, und deckt sich vollständig mit `richtung_invertiert` in
`all_sessions.json`.

**Entscheid: aggregierte Quoten werden richtungskorrigiert.** Bei richtungsverkehrten
Abstimmungen werden Ja und Nein vor der Aggregation getauscht. Die Kennzahl heisst danach
**Zustimmungsquote**, nicht mehr Ja-Quote.

Warum das nötig ist, am Beispiel der Legislatur 2025–2028:

| Fraktion | roh | korrigiert | Differenz |
|---|---|---|---|
| FDP-Die Mitte | 77,8 % | 64,8 % | −12,9 |
| GLP-EVP | 77,7 % | 65,5 % | −12,2 |
| SP-JUSO-Grüne-Junge Grüne | 65,4 % | 69,1 % | +3,7 |
| SVP-EDU | 68,1 % | 65,4 % | −2,7 |

In der Rangliste der Ratsmitglieder wechseln **alle fünf** Spitzenplätze. Die
unkorrigierte Liste ist damit nicht ungenau, sondern schlicht falsch.

**Gilt für:** Ranglisten, Fraktionskennzahlen, Mitgliederstatistik, Themenauswertung.
**Gilt nicht für:** die einzelne Abstimmungskarte. Dort steht weiterhin das protokollierte
Ergebnis, erklärt durch den Umkehr-Hinweisblock.

**Ergebnisbadge:** Aus der Umkehrlogik lässt sich das sachliche Ergebnis ableiten. Ist
`ja_ist_zustimmung` falsch, bedeutet eine Ja-Mehrheit die Ablehnung dessen, was im Titel
steht. Das Badge zeigt darum immer «Angenommen» oder «Abgelehnt», nie mehr das
mehrdeutige «Mehrheit für Ja». Gegenprobe am Wortprotokoll (Antrag Tim Bucher,
4. Sitzung vom 04.03.2024): Excel 23 Ja zu 31 Nein, Protokoll «mit 31 : 23 Stimmen
zugestimmt» — die Regel liefert korrekt «Angenommen».

### Gegenprobe am Wortprotokoll

`scripts/umkehr_regeln.py` hält seit dem 01.09.2026 jeden Fall gegen das Wortprotokoll der
Sitzung. Die 466 Protokolldateien liegen samt Volltext lokal in `data/protokolle`.

Entscheidend ist nicht das Ergebniswort, sondern sein Gegenstand. «Der Kommissionsvorlage
wird mit 39 : 16 Stimmen zugestimmt» heisst bei einem Titel «Antrag A. Penkov» genau das
Gegenteil von «Dem Antrag von Franziska Brenn wird zugestimmt». Aus Gegenstand, Ergebniswort
und der Frage, welche Seite gewonnen hat, folgt `ja_ist_zustimmung` eindeutig.

Der Abgleich entscheidet bewusst nur dort, wo er es sicher kann. Stand nach der
Durcharbeitung aller Fälle:

| Herkunft des Entscheids | Fälle | Bedeutung |
|---|---|---|
| `protokoll` | 227 | Wortprotokoll setzt den Wert, 215 bestätigt, 12 korrigiert |
| `konvention` | 216 | Sachtitel ohne Antragsteller, siehe unten |
| `manuell` | 29 | von Hand am Protokoll gelesen und entschieden |
| `regel` | 85 | nicht gegengeprüft, Regelentscheid gilt |

**Fehlerquote des Regelwerks: 5,2 %**, gemessen an den 227 Fällen, in denen das Protokoll
entscheiden konnte. Die Zahl der richtungsverkehrten Abstimmungen ging von 488 auf **478**
zurück.

### Was der Abgleich am Regelwerk selbst aufgedeckt hat

`akteur_titel()` las aus «Antrag zu Art. 14bis betreffend …» die «Akteure» `1bis` oder
`betreffend` heraus und erklärte solche Abstimmungen für richtungsverkehrt. Die Funktion
liest jetzt den Originaltitel und verlangt Grossschreibung, weil das das einzige
verlässliche Merkmal ist, das einen Namen von einem Gesetzeswort trennt. Zusätzlich
erkennt sie «Josef Würms beantragt …» als Antragsteller.

### Konvention für Sachtitel

Bei Sachtiteln ohne Antragsteller (Budgetpositionen, Traktandenreihenfolge,
Geschäftstitel) belegt das Protokoll zwar das Ergebnis, aber nicht, worauf sich
«Zustimmung» beziehen soll. Festgelegt am 01.09.2026: **Abgestimmt wird über den
Änderungsantrag aus dem Rat, ein Ja stützt die Fassung von Kommission oder Regierung und
gilt darum nicht als Zustimmung.** Die Quote misst damit, wie oft jemand Anträge aus dem
Rat mitträgt. In der laufenden Legislatur betrifft das nur 6 von 316 Abstimmungen, die
Fraktionswerte verschieben sich um höchstens 0,8 Prozentpunkte.

### Handentscheide

`data/umkehr_manuell.json` enthält 29 Fälle, die von Hand am Wortprotokoll entschieden
wurden, je mit Begründung und zitierter Belegstelle. Diese Datei hat Vorrang vor Regelwerk
und automatischem Abgleich; wer einen Entscheid ändern will, ändert ihn dort.

Von den 29 bestätigten 28 den Regelentscheid, einer korrigierte ihn. Ein Beispiel für den
Wert des Nachlesens: Beim «Antrag Urs Capaul» legte der Hinweis eine Korrektur nahe, das
Protokoll zeigte aber, dass das Präsidium die 9er-Kommission vorschlug und Capaul für die
GrüZ plädierte. Die Regel lag richtig.

### Was offen bleibt

69 Fälle in `data/umkehr_pruefliste.md`, dort gilt der Regelentscheid:

- **39** ohne Fundstelle: das Protokoll hält das Ergebnis nicht mit Stimmenzahlen fest
- **15** ohne Protokolltext: für diese Sitzungen liegt kein Wortprotokoll im Bestand
- **15** bei Stimmengleichheit: aus dem Ausgang lässt sich keine Richtung ableiten

Dazu 16 Ausmehrungen, die von der Sache her keine Richtung haben und aus allen Quoten
draussen bleiben.

---

## 7 · Aufbau des Generators

`scripts/build3.py` erzeugt `output/dashboard.html`. Neu gegenüber `build2.py`:

- **CSS und JS liegen als eigene Dateien** in `scripts/assets/` und werden beim Bauen
  eingebettet. In `build2.py` steckte beides in Python-Strings, in denen jede geschweifte
  Klammer verdoppelt werden musste; das war die grösste Fehlerquelle.
- **Kompakte Datenkodierung.** Stimmen stehen als Zeichenkette (`J`, `N`, `E`, `A`) statt
  als Liste von Wörtern. Die Ausgabedatei schrumpft von 3,7 MB auf 2,2 MB, obwohl sie mehr
  enthält als vorher.
- **Alles aus build2 ist übernommen:** die dreistufige Schlagworthierarchie mit Zählern je
  Ebene, der Formfilter, die Kontexttexte auf den Karten, die Mitgliederprofile mit Beruf,
  Amtsdauer und Interessenbindungen sowie das Interessennetz. Der Netzcode ist inhaltlich
  unverändert aus `build2.py` übernommen, angepasst wurden nur die Farben: sie kommen jetzt
  aus den CSS-Token und folgen damit dem Hell- und Dunkelmodus.
- **Richtungskorrektur zentral.** Die Funktion `korr()` tauscht bei Umkehrabstimmungen Ja
  und Nein, bevor irgendetwas aggregiert wird. Die Rohstimmen bleiben unverändert, die
  Abstimmungskarten zeigen weiterhin das protokollierte Ergebnis samt Herkunftsvermerk.
- **Geschlossenheit neu berechnet.** Früher wurde gezählt, wie oft eine Fraktion vollständig
  einig war. Das bevorzugte kleine Fraktionen massiv: eine 7er-Fraktion ist rein zufällig
  viel öfter einstimmig als eine 23er. Jetzt zählt der durchschnittliche Anteil der
  Fraktion, der gleich stimmt. Aus 44 % für die SVP-EDU und 74 % für die GLP-EVP werden
  damit 90 % und 92 %, also vergleichbare Werte.

`build2.py` und `matching.py` bleiben unverändert als Rückfallebene liegen.

---

## 8 · Wer stimmt wie ich?

Das frühere zweite Dashboard ist als eigene Rubrik eingebaut. Grundsätze aus
`docs/KONZEPT_waehler-matching.md` gelten weiter: keine politische Wertung, die Richtung
bewertet der Nutzer selbst, Enthaltung und Abwesenheit zählen nicht.

**Drei Umfänge zur Wahl.** Die Fragen sind durchgehend nach Trennschärfe geordnet, also
danach, wie stark eine Abstimmung die Fraktionen geteilt hat. Der kurze Modus ist damit der
Anfang des langen, und Antworten bleiben beim Wechsel erhalten. Vorgesehen sind 12, 36 und
72 Fragen; weil je Geschäft nur die trennschärfste Abstimmung zählt, stehen derzeit
**66** zur Verfügung, der grösste Modus zeigt deshalb 66.

**Auswahlregeln:**

- nur die laufende Legislatur
- nur Sitzungen mit publiziertem Wortprotokoll
- nur Abstimmungen mit geklärter Richtung; bei Umkehrabstimmungen muss die Richtung am
  Protokoll geprüft oder per Konvention festgelegt sein
- mindestens 30 abgegebene Ja- und Nein-Stimmen
- je Geschäft nur die trennschärfste Abstimmung
- thematische Streuung, mitwachsend mit dem Umfang

**Was sich inhaltlich geändert hat:** `matching.py` schloss offene Umkehrfälle aus,
korrigierte die Richtung aber nicht. Von den zwölf gewählten Fragen waren **fünf
Umkehrabstimmungen** — dort wurde ein Ja des Nutzers gegen ein Ja im Rat verrechnet, das
inhaltlich das Gegenteil bedeutete. In `build3.py` wird die Richtung vor dem Vergleich
korrigiert.

---

## 9 · Bilder für Social Media

Ein Knopf unten rechts öffnet den Bildexport. Vier Motive, alle im Instagram-Hochformat
1080 × 1350, gezeichnet auf einem Canvas ohne externe Bibliothek:

1. **Neuste Abstimmung** – die knappste Abstimmung der letzten Sitzung, mit Ergebnisbadge,
   Balken und Fraktionsaufteilung
2. **Sitzungsüberblick** – vier Kennzahlen plus die drei knappsten Entscheide
3. **Fraktionsvergleich** – Zustimmung, Geschlossenheit und Präsenz je Fraktion
4. **Rangliste Zustimmungsquote** – die ersten acht

Das Bild folgt dem gewählten Hell- oder Dunkelmodus. Wasserzeichen unten:
«Kantonsrat Schaffhausen · Kantonsratsspiegel» und «Daten: Parlamentsdienste Kanton
Schaffhausen».

---

## 10 · Vorgehen

1. ✅ Prototyp der Rubrik «Zuletzt entschieden»
2. ✅ Sprechende Überschriften, Gruppierung nach Geschäft, korrigiertes Ergebnisbadge
3. ✅ Gegenprobe am Wortprotokoll, Handentscheide, Prüfliste
4. ✅ `build3.py`: alle sieben Rubriken, Matching eingebaut, Bildexport
5. Offen: `output/dashboard.html` gegen `output/kantonsrat-dashboard.html` tauschen,
   sobald du zufrieden bist

---

## Offene Punkte

- **Tippfehler in der Quelle.** «weiterer Gesetzs», «Gesetz übder die», «Rechtpflegekommisison»,
  «Schaffhasuen» stehen so in der Excel-Publikation. Eine Korrekturliste wäre möglich, wurde
  aber bewusst noch nicht angelegt: Sie müsste gepflegt werden und weicht von der Quelle ab.
- **Fehlende Wortprotokolle.** Für 15 Umkehrfälle liegt kein Protokolltext vor, darunter
  alle fünf der neusten Sitzung vom 24.08.2026. Deren PDF ist verlinkt, aber nicht
  heruntergeladen. `python3 scripts/scraper.py --protokolle` holt die fehlenden Dateien;
  danach klärt ein erneuter Lauf von `umkehr_regeln.py` diese Fälle vermutlich mit.
  Bis dahin steht auf der Startseite bei jeder Umkehrabstimmung der Vermerk
  «regelbasiert, nicht am Protokoll überprüft», was zutrifft.
- **Stimmengleichheit.** 15 Fälle endeten unentschieden und wurden per Stichentscheid
  geklärt. Aus dem Ausgang lässt sich die Richtung nicht ableiten, hier hilft nur Lesen.

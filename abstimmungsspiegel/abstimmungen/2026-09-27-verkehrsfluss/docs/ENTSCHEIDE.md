# Entscheide · Verkehrsflussinitiative Schaffhausen

Was für diese Vorlage entschieden wurde, mit Datum und Begründung, und was noch
offen ist. Entscheide, die für jede Vorlage gelten, stehen nicht hier, sondern
in [../../../docs/10_METHODE.md](../../../docs/10_METHODE.md).

Der Sinn eines eigenen Blattes: Ein Entscheid ohne Begründung wird beim nächsten
Mal wieder aufgemacht, und ein Entscheid ohne Datum lässt sich nicht gegen den
Stand der Daten prüfen.

---

## Entschieden

### Die Kosten-Nutzen-Rechnung bleibt draussen

**3. September 2026.** Michaels Entscheid, und er hat recht.

Die Rechnung wäre ein zu starkes Argument für eine Seite, und zwar aus einem
Grund, der sich nicht durch besseres Rechnen beheben lässt: **Die Asymmetrie
sitzt im Modell, nicht in den Zahlen.** Alle Kosten sind monetarisierbar,
Bauaufwand, Fahrzeitverlust, Fahrzeugbedarf. Vom Nutzen ist nur ein Teil
monetarisierbar, nämlich verhinderte Unfälle und weniger Lärm. Aufenthaltsqualität
und Gesundheit fallen heraus, weil es dafür keine belastbaren Ansätze gibt. Ein
Verhältnis, dessen Zähler unvollständig und dessen Nenner vollständig ist, liegt
notwendig unter eins. Es sieht dann aus wie ein Befund, ist aber eine Folge der
Modellierung.

Eine Korrektur an Michaels Begründung: Er nahm an, die Rechnung verwende den
Staukostenwert des ASTRA. Der Blick in `../geo/00_uebergabe_michael/skripte/knv.py`
zeigt, dass sie mit `VTTS = 42.50` rechnet, dem Zeitkostensatz nach ARE und
VSS SN 641 822a. Der Ansatz war also korrekt gewählt; der Grund, die Rechnung
weglassen zu müssen, ist ein anderer und ein schwerwiegenderer.

**Wieder aufnehmen** nur dann, wenn sich Gesundheit und Aufenthaltsqualität
belastbar beziffern lassen. Bis dahin steht in der Textkritik, dass die
Kostenfrage offen ist, und das ist die ehrlichere Aussage.

### Die Grafik zum Fahrzeugbedarf wird gebaut

**3. September 2026.** Michaels Einwand: sie wäre am aussagekräftigsten. Er hat
recht gehabt, sie war nur nie gebaut worden.

Sie zeigt, was die reine Zahl «29 oder 30 Fahrzeuge» verschweigt: Der
Fahrzeugbedarf ist eine Treppenfunktion. Solange die Zusatzzeit in die Wendezeit
passt, kostet sie nichts. Ohne diese Darstellung liest man «eine Minute mehr
Fahrzeit» als «ein Sechzigstel mehr Kosten», und das ist falsch in beide
Richtungen. Ergebnis in `../grafiken/E2_Fahrzeugbedarf.svg`, hergeleitet in
[AUSWERTUNG_bus.md](AUSWERTUNG_bus.md).

### Zwei Modelle statt einer Zahl bei der Zusatzzeit

**3. September 2026.** Die Zusatzzeit lässt sich nicht exakt bestimmen, also
wird sie auch nicht so dargestellt. Die physikalische Rechnung und der
ASTRA-Richtwert stehen nebeneinander, und die Antwort lautet «null bis ein
zusätzliches Fahrzeug».

Das ist unbefriedigend und richtig. Eine einzelne Zahl wäre befriedigend und
falsch.

### Der Strassenrichtplan kommt über WFS, nicht über WMS

**3. September 2026.** Das WMS-Raster war unbrauchbar: Haarlinien in Rot, Gelb
und Grün, also unlesbar und im falschen Farbschema. Über WFS kommen 2585
Einzelstücke, verkettet zu 34 durchgehenden Linien, 107 km, 19 kB. Die
Darstellung ist damit unsere Entscheidung.

### Michaels Übergabe bleibt im Original liegen

**3. September 2026.** Der Stand vom Juli 2026 liegt unangetastet in
`../geo/00_uebergabe_michael/`, samt seinen Skripten und Grafiken in den
Originalfarben. Was daraus übernommen wurde, steht in [GEO.md](GEO.md).

Der Grund: Bei einer eigenen Auswertung muss nachvollziehbar bleiben, was aus
der Quelle stammt und was wir daran geändert haben. Eine umgefärbte Grafik ohne
das Original ist eine Behauptung über das Original.

---

## Offen

### Kategoriale Farben der Gemeindekarten

**Entscheid nötig, von Michael.** Die Gemeindekarten verwenden noch die
kategorialen Farben der Übergabe:

| Farbe | Bedeutung |
|---|---|
| `#1b9e77` | Kindergarten |
| `#2166ac` | weitere Sozialeinrichtung |
| `#6a51a3` | Heim |
| `#d95f0e` | Schule |
| `#e6194b` / `#f4a6ae` | Kandidatenstufen |

Grün und Rot sind im Farbschema des Projekts ausgeschlossen, weil Grün die
Farbe der SVP und Rot die der SP ist und weil rot gegen grün für einen Teil der
Leser nicht unterscheidbar ist. Bei kategorialen Marken, die keine Wertung
tragen, ist die Regel weniger zwingend als bei einer Bewertungsskala; deshalb
wurden sie beim Umfärben ausgenommen und nicht eigenmächtig ersetzt.

Drei Wege stehen offen: die Kategorien über Form statt Farbe unterscheiden, eine
Palette ohne Rot und Grün wählen, oder es so lassen mit einem Satz, der die
Ausnahme begründet.

### Wendezeiten von den Verkehrsbetrieben

Die Wendezeiten sind jetzt aus dem Fahrplan gemessen, nicht mehr geschätzt, und
die Taktprobe bestätigt sie bei sechs von sieben Linien. Eine Bestätigung durch
die Verkehrsbetriebe Schaffhausen wäre trotzdem wertvoll, weil die planmässige
Wendezeit im Fahrplan nicht dasselbe ist wie die betrieblich nötige.

Das ist keine Voraussetzung mehr, sondern eine Verbesserung. Vor der Messung war
es die entscheidende Lücke.

### Geltungsbereiche exakt rechnen

Alle Zutaten sind beschafft: Richtplanfunktion und Ortstafeln über den
kantonalen WFS, Bushaltestellen über die BAV-Ebene, Linienführung über
OpenStreetMap. Was fehlt, ist der Verschnitt. Zu rechnen wäre:

```
Gegenvorschlag = Kantonsstrassen(überregional, regional) ∩ innerorts
Initiative     = Kantonsstrassen ∩ innerorts ∩ Puffer(Busnetz, 15 m)
```

Damit liesse sich beziffern, wie stark sich die beiden Mengen überschneiden.
Diese Zahl nennt **keines der beiden Komitees**, und sie ist die einzige, die
den praktischen Unterschied zwischen Initiative und Gegenvorschlag greifbar
macht. Bis dahin sind die Geltungsbereiche im Viewer nur eingeblendet, nicht
gerechnet.

### Fehlende Fundstellen

- Die FAQ-Antworten auf `pro30.ch` liessen sich nicht vollständig auslesen.
- Die Argumentarien der Parteien sind nicht erfasst, nur die der beiden Komitees.
- Die Lärmbelastungszahl «Tausende» wäre am kantonalen Lärmbelastungskataster
  prüfbar.

### Redaktion

- **Zweitprüfung** durch mindestens eine Person ausserhalb des Projekts, ohne
  sichtbare Seitenzuordnung. Noch nicht organisiert.
- **Anhörung beider Komitees** vor der Veröffentlichung. Noch nicht erfolgt. Bei
  einem Termin am 27. September muss sie in den nächsten Tagen laufen.

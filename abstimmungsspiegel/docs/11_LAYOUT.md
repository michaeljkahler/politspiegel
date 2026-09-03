# Layout des Abstimmungsspiegels

Wie die Seite aufgebaut ist und warum. Die Methode dahinter steht in
[10_METHODE.md](10_METHODE.md), die Prüfliste in [12_QS.md](12_QS.md).

Farben, Schriften und die Regel «nie Farbe allein» stehen nicht hier, sondern
zentral in [../../docs/DESIGN_entscheide.md](../../docs/DESIGN_entscheide.md).
Der Abstimmungsspiegel übernimmt sie unverändert, damit Kantonsratsspiegel und
Abstimmungsseite als eine Anwendung gelesen werden.

---

## 1 · Aufbau der Seite

```
Kopf        Vorlage, Abstimmungsdatum, ein Satz «worum es geht»
            Was ändert sich bei Ja / bei Nein  (rein beschreibend, aus der Botschaft)

Netzgrafik  Fünf Achsen, zwei Polygone, darunter je ein Satz zur Lesart

Zwei Spalten
  Pro                                   Contra
  ─ Argumentkarte                       ─ Argumentkarte
      Aussage im Wortlaut                   Aussage im Wortlaut
      wer sagt es, wo, wann  →  Link
      Typ: Tatsache | Prognose | Wertung
      fünf Belegbalken mit Zahl
      Was zutrifft / Was fehlt
      Kritische Fragen zum Argumenttyp
      Quellen als Liste

Fuss        Methode, Prüfstand, Korrekturprotokoll, Trägerschaft
```

**Gestaltungsregeln, aus `docs/DESIGN_entscheide.md` übernommen:**

- Pro und Contra in der bestehenden Abstimmungssprache, also **Petrol `#0F766E`
  für Ja/Pro und Purpur `#8E44AD` für Nein/Contra**. Kein Grün-Rot, weil Grün die
  SVP und Rot die SP ist, und weil beide bei Deuteranopie zusammenfallen.
- Die Belegbalken bekommen **keine** Farbe, sondern eine neutrale Graustufe mit
  hineingeschriebener Zahl. Sonst entsteht der Eindruck, eine Seite sei
  eingefärbt «gut».
- Nie Farbe allein: jeder Balken trägt seine Zahl, jede Achse ihre Beschriftung.
- Archivo für Titel und Ziffern, Public Sans für Fliesstext.

---

---

## 2 · Darstellung der Prüfung

### Ein Netz je Aussage, kein Durchschnitt je Seite

Entschieden am 3. September 2026, nach dem ersten Durchlauf. Die ursprüngliche
Idee waren zwei Polygone, eines je Komitee, gebildet aus dem Mittelwert seiner
Aussagen. Das ist aus drei Gründen die falsche Ebene:

1. **Der Mittelwert beschreibt am Ende keine der Aussagen.** Beim Nein-Komitee
   liegt die Quellenlage zwischen 2 und 4. Der Durchschnitt 3 trifft auf keine
   der beiden Karten zu, und die Frage der Leserin lautet ohnehin «welche
   Behauptung ist schwach belegt», nicht «wie steht das Lager im Schnitt da».
2. **Ungleiche Nenner.** Weil nicht auf jede Aussage alle Achsen passen, würde
   ein Polygon Achsen mit drei und mit vier zugrundeliegenden Werten in derselben
   Form zeigen, ohne das kenntlich zu machen.
3. **Eine Durchschnittsnote je Komitee ist ein Urteil über die Kampagne.** Genau
   das soll der Abstimmungsspiegel nicht abgeben. Bewertet wird die einzelne
   Aussage, und dort bleibt die Note auch.

**Umgesetzt als Small Multiples:** ein kleines Netz je Aussage, alle im selben
Massstab, in zwei Reihen nach Seite. So sieht man die *Form*, und die ist das
Informative: Zwei Aussagen mit gleicher Punktzahl können an ganz verschiedenen
Stellen hohl sein. Nicht anwendbare Achsen erscheinen als gestrichelte Speiche
und werden vom Polygon übersprungen, statt als Null eingezeichnet zu werden.
Ein Legendennetz mit Achsenbeschriftung steht daneben.

Was von der Zusammenfassung bleibt, ist schlichte Arithmetik statt einer
erfundenen Fläche: die Summe der erreichten und der erreichbaren Punkte je Seite,
unter der Übersichtsliste.

### Übersichtsliste vor den Karten

Vor den Argumentkarten steht eine Liste aller Aussagen mit Seite, Kurzfassung,
Typ, Balken und Punktzahl «x von y», jede Zeile verlinkt auf ihre Karte. Sie
beantwortet die erste Frage jeder Besucherin in fünf Sekunden und macht die
Seite ohne Scrollen navigierbar.

Die Form «x von y» ist dabei nicht Kosmetik: Weil die erreichbare Punktzahl mit
der Zahl der anwendbaren Achsen sinkt, ist sie je Aussage verschieden. Ein
Prozentwert würde das verstecken, «7 von 12» und «7 von 20» zeigen es.

### Der Präzisierungssatz

Das eigentliche Herzstück. Zu jeder geprüften Aussage gehören zwei Felder,
immer in dieser Reihenfolge:

- **Was zutrifft:** «Die Zahl stieg von 2 auf 6.»
- **Was fehlt:** «Bei so kleinen Zahlen ist eine Zunahme in dieser Grösse nicht
  von Zufall zu unterscheiden. Ein Vergleich braucht ein Mehrjahresmittel und
  einen Bezug auf Fahrzeugkilometer.»

Nie umgekehrt. Wer mit der Widerlegung beginnt, wird als Gegner gelesen.

---

## 3 · Bausteine, die jede Seite verwendet

Der Generator kennt eine kleine Zahl wiederkehrender Bausteine. Wer eine neue
Abstimmung aufsetzt, kommt mit diesen aus, und die Seite bleibt vertraut.

| Baustein | Funktion in `bausteine/argumente.py` | Wofür |
|---|---|---|
| Abschnitt | `abschnitt(kennung, titel, hinweis, inhalt)` | Ein- und ausklappbarer Block mit Eintrag im Inhaltsverzeichnis |
| Klappe | `klappe(titel, text, art)` | Unterkasten in einer Argumentkarte, etwa «Was zutrifft» |
| Herkunftsmarke | `marke(art)` | Kennzeichnet eigen, amtlich, komitee, extern |
| Netz | `netzgrafik`, `mininetz` | Fünf Achsen, ein Netz je Aussage |
| Grafikkasten | `grafik_block(arg)` | Sammelt alle Grafiken einer Aussage in einen Klappkasten |
| Karte | `karte(...)`, `viewer_block(...)` | Statische Gemeindekarte und Kartenviewer |
| Textkritik | `textkritik_block(...)` | Offene Begriffe im Abstimmungstext |
| Ratsblock | `kantonsrat_block(...)` | Namentliche Abstimmungen, live aus den Ratsdaten |

### Vier Regeln, die für alle Bausteine gelten

1. **Alles ist ein- und ausklappbar.** Jeder Block trägt einen Pfeil und einen
   Eintrag im Inhaltsverzeichnis. Die Seite ist lang; wer eine Frage hat, soll
   nicht scrollen müssen.
2. **Eigene Auswertung wird sichtbar abgegrenzt.** Was aus diesem Projekt kommt,
   trägt die dunkle Marke «Eigene Auswertung» und einen stärkeren Rahmen. Was von
   einem Komitee stammt, trägt eine gestrichelte Marke. Wer eine Zahl sieht, soll
   ohne Rückfrage wissen, wessen Zahl das ist.
3. **Jede Grafik ist anklickbar.** Ein Klick öffnet sie gross über der Seite.
   Ohne das sind die Balkengrafiken auf dem Telefon nicht lesbar.
4. **Zahlen stehen am Objekt.** Jeder Balken trägt seinen Wert, jedes Netz seine
   Punktzahl. Eine Achsenbeschriftung allein reicht nicht.

### Das Zeilenmass sitzt auf dem Text, nicht auf dem Kasten

Fliesstext läuft auf rund 74 bis 80 Zeichen, sonst wird er unlesbar. Der Kasten
darum reicht trotzdem bis zur Spaltenkante. Andernfalls endet ein Rahmen mitten
in der Fläche, während die Karte daneben bis zum Rand geht, und die Seite sieht
kaputt aus. Diese Unterscheidung ist bei der Layout-QS vom 3. September
aufgefallen und in den Formatvorlagen umgesetzt.

---

## 4 · Was auf dem Telefon anders ist

Die Seite wird überwiegend auf dem Telefon gelesen. Drei Dinge sind darum
gesondert festgelegt:

- **Zweispaltiges wird einspaltig** unter 900 Pixel: Pro und Contra, Netzblock,
  Kartenviewer.
- **Tabellen scrollen in ihrem Kasten**, nicht die Seite. Jede Tabelle steht in
  einem Rahmen mit `overflow-x`, mit einer Mindestbreite, unter der die Spalten
  nicht zusammenfallen.
- **Die Karte wird flacher**, aber nicht kleiner als 420 Pixel; darunter lässt
  sich nichts mehr erkennen.

Geprüft wird bei 390 und bei 1280 Pixel Breite, in beiden Farbschemata. Das
Vorgehen steht in [12_QS.md](12_QS.md).

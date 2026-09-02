# Konzept: Wähler-Matching-Tool für das Kantonsrats-Dashboard

Arbeitsstand: Juli 2026. Dieses Dokument hält das Design fest, bevor Code
entsteht. Es ist die Grundlage für die spätere Umsetzung und für die Diskussion
der heiklen methodischen Punkte.

---

## 1. Zweck

Ein Werkzeug, mit dem eine Wählerin oder ein Wähler herausfindet, welche Partei
und welche einzelnen Ratsmitglieder dem eigenen Standpunkt am nächsten stehen.
Das Prinzip ist dasselbe wie bei smartvote, mit dem entscheidenden Unterschied
des Gesamtprojekts: Grundlage ist nicht ein Fragebogen, den die Politiker
ausfüllen, sondern ihr *tatsächliches, protokolliertes Abstimmungsverhalten* im
Kantonsrat.

Zwei Bausteine:

1. **Fragebogen**: 10 bis 15 kontroverse Sachabstimmungen der Legislatur, die der
   Nutzer selbst mit Ja oder Nein beantwortet. Daraus wird die Übereinstimmung
   mit jedem Ratsmitglied und jeder Fraktion berechnet.
2. **Relevanzfilter (optional)**: demografische Angaben (Alter, Einkommen,
   Kinder, Auto, Wohneigentum) blenden ein, welche Abstimmungen den Nutzer in
   seiner Lebenssituation besonders betreffen. Der Filter wählt die Themen aus,
   er bewertet die Richtung nicht.

## 2. Vereinbarkeit mit den Grundprinzipien

Das bestehende Dashboard beschreibt Verhalten, ohne es zu werten (siehe
`PROJEKT.md`, Abschnitt 2). Ein Matching-Tool ist der Punkt, an dem Wertung
droht. Deshalb gelten zusätzliche Regeln:

- Die inhaltliche Richtung (was ist «gut» oder «in meinem Interesse») legt immer
  der Nutzer selbst fest, nie das Tool.
- Jede automatische Zuordnung (Frageauswahl, Themen, Betroffenheit) ist
  transparent dokumentiert und wird vom Menschen freigegeben. Keine Blackbox.
- Die Methode wird offengelegt, damit das Ergebnis nachvollziehbar und
  überprüfbar ist.

## 3. Die Demografie-Frage: kann man aus Merkmalen Interessen ablesen?

Kurzantwort: Man kann aus demografischen Merkmalen *statistische Tendenzen*
ablesen, aber keine individuellen Interessen. Diese Unterscheidung ist der
wissenschaftliche Kern und bestimmt das ganze Design.

### 3.1 Was die Forschung stützt

Dass soziale Merkmale mit politischen Präferenzen zusammenhängen, ist gut
belegt. Die **Cleavage-Theorie** von Lipset und Rokkan (1967) erklärt
Parteiensysteme aus dauerhaften Konfliktlinien zwischen sozialen Gruppen
(Stadt gegen Land, Kapital gegen Arbeit, Staat gegen Kirche, Zentrum gegen
Peripherie). Für die Schweiz zeigen die Wahl- und Abstimmungsforschung von
**Selects** und die **VOTO-Studien** (FORS Lausanne und Zentrum für Demokratie
Aarau), dass Alter, Bildungsniveau und Einkommen das Abstimmungsverhalten
mitprägen. Die Forschungsgruppe **sotomo** (Hermann und Leuthold, Universität
Zürich) hat im «Atlas der politischen Landschaften» gezeigt, dass sich ähnliche
Lebensstile und Haltungen räumlich bündeln und sich politische Konflikte entlang
weniger Grundachsen ordnen lassen (links gegen rechts, liberal gegen
konservativ, ökologisch gegen technokratisch).

### 3.2 Der Fallstrick: ecological fallacy

Der Schluss von der Gruppe auf das Individuum ist ein anerkannter Denkfehler,
der **ecological fallacy** (ökologischer Fehlschluss, klassisch Robinson 1950).
«Personen mit hohem Einkommen stimmen im Schnitt eher für X» bedeutet nicht,
dass eine bestimmte Person mit hohem Einkommen für X ist. Der Grund: Die
Streuung *innerhalb* einer demografischen Gruppe ist in der Regel grösser als
die Unterschiede *zwischen* den Gruppen. Merkmale wie «hat ein Auto» oder «hat
Kinder» erklären daher nur einen begrenzten Teil der individuellen Haltung, nie
die ganze.

### 3.3 Warum der Standard auf Selbstauskunft setzt

Voting-Advice-Applications wie smartvote arbeiten bewusst nicht mit Demografie,
sondern mit den eigenen Sachpositionen des Nutzers. Sie folgen dem
**Proximity-Modell**: Die Übereinstimmung ergibt sich aus der Nähe zwischen den
eigenen Antworten und den Positionen der Politiker über alle Sachfragen hinweg
(gemessen als Distanz). Die Forschung zu diesen Anwendungen zeigt, dass die
Aussagekraft mit der Zahl und der thematischen Breite der Fragen steigt, und
dass sie bei wirtschaftlichen und Links-Rechts-Fragen zuverlässiger ist als bei
kulturellen Themen.

### 3.4 Konsequenz für das Design

Die Demografie wird nur als **Relevanzfilter** genutzt: Sie entscheidet, welche
Abstimmungen dem Nutzer angezeigt werden, weil sie seine Lebenssituation
berühren. Sie sagt nie, wie er zu stimmen «hätte». Die Meinung bildet der Nutzer
selbst über den Ja-Nein-Fragebogen. Damit stützt sich das Tool auf gesicherte
Methodik und bleibt wertneutral.

## 4. Datengrundlage

### 4.1 Vorhanden
- `all_sessions.json`: 46 Sitzungshälften, 383 Abstimmungen, Stimmen je Mitglied
  (Ja, Nein, Enth, oder V/A/N für keine Teilnahme), Fraktion und Partei.
- Geprüfte Themenzuordnung von 77 Geschäften zu 9 Hauptgruppen.

### 4.2 Zu beschaffen: Wortprotokolle
Die Wortprotokolle jeder Sitzung sind auf sh.ch als PDF publiziert (eigene
Protokoll-Seite, gleiche `get/file`-Struktur wie die Abstimmungs-Excel). Sie
werden gebraucht, um

- jede ausgewählte Abstimmung als verständliche Ja-Nein-Frage zu formulieren,
- die inhaltliche Bedeutung von Ja und Nein zweifelsfrei zu bestimmen (wichtig
  bei den Umkehrabstimmungen, siehe 5.3),
- die Intensität der Debatte als ein Auswahlsignal zu messen (siehe 5.2).

Der Scraper wird dazu um einen Protokoll-Download erweitert (neuer Ordner
`data/protokolle/`).

### 4.3 Bekannte Datenprobleme (aus der Analyse)
- Das Feld `typ` ist unbrauchbar (Parsing-Artefakt, 212 von 383 Einträgen tragen
  fälschlich «Ja»). «Sachabstimmung» muss inhaltlich bestimmt werden, nicht über
  den Typ.
- Nur rund die Hälfte der Abstimmungen trägt einen Geschäftstext. Für die
  Frageauswahl sind die Protokolle nötig.
- 22 Umkehrabstimmungen sind noch nicht richtungskorrigiert.

## 5. Auswahl der Fragen (10 bis 15)

Ziel ist ein kompakter Satz von Abstimmungen, der die Politiker möglichst gut
unterscheidet. Die Auswahl erfolgt automatisch nach drei Signalen und wird
danach einmal von Hand auf inhaltliche Sinnhaftigkeit gesichtet.

### 5.1 Fokus auf Schlussabstimmungen
Grundlage sind inhaltliche Sachentscheide (Schlussabstimmungen und
substanzielle Anträge), nicht prozedurale Abstimmungen (Ordnungsanträge,
Abschreibungen, Traktandenlisten). Diese lassen sich über den Geschäftsbezug und
das Protokoll identifizieren.

### 5.2 Geringe Einigkeit plus Debattenintensität
Zwei Signale bestimmen, wie kontrovers eine Abstimmung war:

- **Knappheit des Ergebnisses**: Anteil der Minderheit an den gültigen Ja- und
  Nein-Stimmen. Nahe 50 zu 50 heisst hoch umstritten. (In der laufenden
  Legislatur gibt es 242 Abstimmungen mit substanzieller Beteiligung, viele
  davon knapp.)
- **Intensität der Debatte**: Umfang der Wortmeldungen im Protokoll zu diesem
  Geschäft (Zahl der Redner, Länge). Ein starkes Signal dafür, dass ein Thema
  politisch bedeutsam war, auch wenn das Ergebnis am Ende klar ausfiel.

### 5.3 Trennschärfe statt reiner Knappheit
Wichtiger Zusatz: Eine knappe Abstimmung nützt dem Matching nur, wenn sie die
Parteien *trennt*. Ein 50-zu-50-Ergebnis, bei dem alle Fraktionen intern
gespalten sind (Gewissensfrage), unterscheidet die Parteien nicht. Deshalb wird
zusätzlich gemessen, wie stark die Abstimmung entlang der Fraktionslinien
verläuft. Bevorzugt werden Fragen, die sowohl umstritten als auch parteitrennend
sind. So deckt der kurze Fragebogen ein möglichst breites Meinungsspektrum ab.

### 5.4 Richtungskorrektur der Umkehrabstimmungen
Bei Umkehrabstimmungen bedeutet ein Nein inhaltlich Zustimmung. Vor jeder
Berechnung wird die Stimmrichtung dieser Fälle anhand des Protokolls korrigiert,
sodass Ja im Fragebogen immer dieselbe inhaltliche Bedeutung hat. Ohne diesen
Schritt würde das Tool falsch matchen. (Zugleich löst das den offenen Punkt 3
aus `PROJEKT.md`.)

## 6. Berechnung der Übereinstimmung

Angelehnt an das Proximity-Modell der etablierten Anwendungen.

- Der Nutzer beantwortet jede der ausgewählten Fragen mit Ja oder Nein, optional
  mit «keine Meinung» (zählt dann nicht).
- Optionale Gewichtung: Der Nutzer kann einzelne Fragen als besonders wichtig
  markieren; diese zählen doppelt (wie bei smartvote).
- Für jedes Ratsmitglied wird die Übereinstimmung als Anteil der Fragen
  berechnet, bei denen seine (richtungskorrigierte) Stimme mit der Antwort des
  Nutzers übereinstimmt. Enthaltung oder Nichtteilnahme des Mitglieds bei einer
  Frage: diese Frage zählt für dieses Mitglied nicht mit (relative Berechnung,
  konsistent mit dem bestehenden Quotenprinzip).
- Die Partei- oder Fraktionsübereinstimmung ergibt sich aus dem
  Mehrheitsverhalten der Fraktion je Frage oder aus dem Mittel ihrer Mitglieder.
- Ergebnis: eine Rangliste «grösste Übereinstimmung» für Mitglieder und für
  Fraktionen, plus eine Aufschlüsselung Frage für Frage, damit der Nutzer sieht,
  *warum* ein Match zustande kommt.

## 7. Der demografische Relevanzfilter (konkret)

Der Filter ordnet demografische Merkmale bestimmten Themen und damit
Abstimmungen zu. Die Zuordnung ist eine geprüfte, offengelegte Tabelle und sagt
ausschliesslich «betrifft dich», nie «so stimm richtig».

| Merkmal | Betrifft typischerweise (Beispiele) |
|---|---|
| Auto | Verkehrsabgaben, Strassenbau, Tempo- und Parkierungsfragen |
| Kinder | Schule, Kita, Familienzulagen, Bildung |
| Wohneigentum | Eigenmietwert, Grundstückgewinnsteuer, Bau- und Zonenrecht |
| Einkommen | Steuertarife, Prämienverbilligung, Gebühren |
| Alter | Altersvorsorge, Pflege und Altersbetreuung, Gesundheit |

So sieht ein Nutzer mit Kindern und Auto zuerst die Abstimmungen zu Schule und
Verkehr. Er beantwortet sie weiterhin selbst. Der Filter erhöht nur die
persönliche Relevanz der gezeigten Fragen, er nimmt keine Wertung vorweg.

## 8. Transparenz und Fairness

- Die Auswahlkriterien und die Betroffenheits-Tabelle werden im Tool sichtbar
  gemacht.
- Nur amtierende Mitglieder erscheinen in den Ranglisten (konsistent mit dem
  bestehenden Prinzip); ausgeschiedene Personen verzerren das Matching nicht.
- Das Matching bezieht sich immer auf eine Legislatur, da sich Zusammensetzung
  und Geschäfte zwischen Legislaturen ändern.
- Es gibt bewusst keine Links-Rechts-Einordnung und keine inhaltliche Bewertung
  der Positionen.

## 9. Grenzen und Risiken (ehrlich benannt)

- **Wenige Fragen, kantonale Ebene**: 10 bis 15 Fragen bilden nur einen
  Ausschnitt ab. Die Aussagekraft steigt mit Zahl und thematischer Breite der
  Fragen; ein sehr kurzer Fragebogen ist entsprechend gröber.
- **Fraktionszwang und strategisches Abstimmen**: Eine Stimme im Rat ist nicht
  immer die persönliche Überzeugung; Fraktionsdisziplin kann sie überlagern. Das
  Tool misst Verhalten, nicht Gesinnung.
- **Betroffenheit ist nicht Interesse**: Auch die Themen-Zuordnung im Filter ist
  eine Vereinfachung und wird als solche gekennzeichnet.
- **Repräsentativität der Daten**: Nur namentliche Abstimmungen ab 2018 liegen
  vor; eine Datenlücke Anfang 2025 ist noch offen (siehe `PROJEKT.md`).

## 10. Umsetzungsschritte (Vorschlag)

1. Scraper um den Protokoll-Download erweitern (`data/protokolle/`).
2. Umkehrabstimmungen anhand der Protokolle richtungskorrigieren.
3. Kennzahlen je Abstimmung berechnen: Knappheit, Fraktionstrennung,
   Debattenintensität; daraus eine Kandidatenliste erzeugen.
4. Kandidatenliste einmal von Hand sichten (Sinnhaftigkeit, Verständlichkeit).
5. Fragen als klare Ja-Nein-Aussagen formulieren (aus Protokoll und Geschäft).
6. Betroffenheits-Tabelle (Merkmal zu Thema) erstellen und freigeben.
7. Matching-Logik und Oberfläche in das bestehende Dashboard integrieren.
8. Test mit realen Beispielprofilen, dann Veröffentlichung.

## 11. Quellen

- Lipset, S. M. und Rokkan, S. (1967): Cleavage Structures, Party Systems, and
  Voter Alignments. In: Party Systems and Voter Alignments. New York, Free Press.
- Robinson, W. S. (1950): Ecological Correlations and the Behavior of
  Individuals. American Sociological Review.
- Hermann, M. und Leuthold, H.: Atlas der politischen Landschaften. Ein
  weltanschauliches Porträt der Schweiz (Forschungsgruppe sotomo, Universität
  Zürich); sowie Hermann und Leuthold (2001), Swiss Political Science Review.
- VOTO-Studien (FORS Lausanne und Zentrum für Demokratie Aarau, ZDA):
  https://www.voto.swiss/
- Wahlforschungsprojekt Selects (FORS).
- Zur Methodik von Voting-Advice-Applications: Übersichtsliteratur zu
  Proximity-Modell und Match-Berechnung (Acta Politica, Springer).

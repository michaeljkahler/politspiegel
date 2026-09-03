# Technik

Welche Datei was tut, wie eine Seite gebaut wird und wie sie ins Netz kommt.

---

## 1 · Ordner

```
abstimmungsspiegel/
  docs/                        gilt für jede Vorlage
    00_UEBERSICHT.md           Einstieg, dieser Ordner erklärt
    10_METHODE.md              Prüfschema, Achsen, Redaktion
    11_LAYOUT.md               Aufbau der Seite, Bausteine
    12_QS.md                   Prüfliste vor jeder Veröffentlichung
    13_GEODATEN.md             Drei Stufen, Quellen, Regeln
    14_TECHNIK.md              dieses Blatt
  bausteine/                   der Generator, für alle Vorlagen derselbe
    argumente.py               baut eine Abstimmungsseite
    teilen.py                  Bilder für Social Media, im Browser gezeichnet
    geo_freigeben.py           prüft Geodaten und gibt sie frei
    grafiken_umfaerben.py      bringt fremde Grafiken ins Farbschema
  abstimmungen/
    2026-09-27-verkehrsfluss/
      vorlage.json             die Argumente, Schema unten
      docs/                    vorlagenspezifisch
        INHALT.md              Aussagen, Fundstellen, Textkritik
        GEO.md                 welche Ebenen, woher, warum
        AUSWERTUNG_bus.md      eigene Rechnungen zu dieser Vorlage
        ENTSCHEIDE.md          was entschieden wurde und warum
        QS_PROTOKOLL.md        was geprüft und korrigiert wurde
      geo/
        00_uebergabe_michael/  Originalstand der Übergabe, unangetastet
        01_roh/                wie geladen
        02_aufbereitet/        umprojiziert, verschnitten, gerechnet
        03_freigegeben/        geprüft, das bindet die Seite ein
        PRUEFBERICHT.md        wird erzeugt, nicht von Hand geschrieben
        skripte/               Beschaffung und Aufbereitung
      grafiken/                fertige Grafiken im Farbschema
      skripte/                 Auswertungen und Grafikerzeugung
```

Ein Ordner je Abstimmung ist der Kern der Aufteilung. Als alles in einem
Konzeptpapier stand, wuchs es bei einer einzigen Vorlage auf 1259 Zeilen. Bei
der dritten Abstimmung wäre es nicht mehr lesbar gewesen, und beim Nachschlagen
hätte man nie gewusst, ob eine Regel allgemein gilt oder nur für den einen Fall.
Jetzt entscheidet der Ort darüber: Was in `docs/` steht, gilt immer. Was in
`abstimmungen/<slug>/docs/` steht, gilt für diese Vorlage.

---

## 2 · Eine Seite bauen

Aus der Projektwurzel, in dieser Reihenfolge:

```
python3 abstimmungsspiegel/bausteine/geo_freigeben.py 2026-09-27-verkehrsfluss
python3 abstimmungsspiegel/bausteine/argumente.py     2026-09-27-verkehrsfluss
python3 politspiegel/bauen.py
```

Der erste Schritt prüft die Geodaten und füllt `03_freigegeben`. Der zweite
baut die Seite nach `site/abstimmung/<slug>/index.html` und legt die
eingebundenen Grafiken daneben. Der dritte erneuert die Übersichtsseite; sie
findet die Abstimmung von selbst, ein Eintrag von Hand ist nicht mehr nötig
(siehe Abschnitt 5).

Die Reihenfolge ist zwingend. `argumente.py` liest ausschliesslich aus
`03_freigegeben`; wer den ersten Schritt vergisst, bekommt eine Seite ohne
Kartenebenen und eine Meldung auf der Fehlerausgabe.

### Warum die Seite ihre Grafiken neben sich hat

`site/abstimmung/<slug>/` ist für sich vollständig: die Seite, ihre Grafiken,
ihre eingebetteten Geodaten. Bilder werden relativ eingebunden. Damit lässt sich
der Ordner verschieben, kopieren oder einzeln veröffentlichen, ohne Pfade
nachzuziehen, und eine alte Abstimmung bleibt erreichbar, auch wenn ihre
Quelldaten längst umgebaut sind.

---

## 3 · Datenschema

Verbindlich sind je Aussage `aussage`, `traeger`, `fundstelle`, `typ`,
`pruefung`, `trifft_zu`, `fehlt`, und je Vorlage `stand` und `status`.

Auf der obersten Ebene der Datei:

| Feld | Bedeutung |
|---|---|
| `stand` | Datum des Inhaltsstands, `JJJJ-MM-TT` |
| `hinweis_quellen` | Ein Satz zur Herkunft der Argumente, steht im Kasten «Quellen und Methode» |
| `lesehilfe` | Ein Absatz unter den Netzgrafiken, optional |
| `vorlage.seiten` | Namen der beiden Seiten: je `name`, `komitee`, `empfehlung`. Ohne Angabe: «Für die Vorlage / Befürworter / Ja» und «Gegen die Vorlage / Gegner / Nein» |
| `vorlage.ja_titel`, `nein_titel` | Überschriften der beiden Folgenkästen, Voreinstellung «Bei einem Ja» und «Bei einem Nein» |
| `vorlage.doppelvorlage`, `doppelvorlage_titel`, `rechtsrahmen`, `kontext` | Kontextabsätze im Kopf, alle optional; `kontext` ist eine Liste von `{titel, text}` |
| `vorlage.kantonsrat_suche`, `kantonsrat_hinweis` | Suchwort für die Ratsdaten und ein optionaler Satz dazu |
| `argumente`, `textkritik`, `karte` | Dürfen leer sein. Ohne Aussagen zeigt die Seite einen Platzhalter, ohne `karte.gemeinden` keine Karte |
| `status` | `entwurf` oder `veroeffentlicht`. Ein Entwurf erscheint in der Übersicht mit dem Vermerk «noch nicht veröffentlichungsreif». Fehlt das Feld, gilt Entwurf |
| `vorlage.abstimmung` | Abstimmungstermin, `JJJJ-MM-TT`. Daran entscheidet die Übersicht, ob die Abstimmung kommend oder vergangen ist |
| `ergebnis` | Wird nach dem Abstimmungssonntag nachgetragen, Schema unten. Ohne das Feld steht in der Übersicht «Ergebnis noch nicht nachgetragen» |

```
"ergebnis": {
  "stimmbeteiligung": 48.3,
  "quelle": "sh.ch, amtliches Ergebnis vom 27. September 2026",
  "fragen": [
    {"titel": "Initiative", "ja": 38.1, "angenommen": false},
    {"titel": "Gegenvorschlag", "ja": 61.5, "angenommen": true},
    {"titel": "Stichfrage", "ja": 44.0, "angenommen": false}
  ]
}
```

Eine einfache Vorlage hat eine Frage, eine Doppelvorlage zwei oder drei. Die
Seite selbst bleibt nach der Abstimmung unverändert; sie zeigt, was vor dem
Entscheid zu wissen war. Das Ergebnis steht in der Übersicht daneben.

| Feld | Bedeutung |
|---|---|
| `aussage` | Wortlaut, so wie er beim Träger steht |
| `traeger` | Wer die Aussage erhebt |
| `fundstelle` | Wo sie steht, mit Verweis |
| `typ` | `tatsache`, `prognose` oder `wertung` |
| `pruefung` | Die fünf Achsen, 0 bis 4 oder `null` |
| `trifft_zu` | Was an der Aussage stimmt. Steht immer zuerst |
| `fehlt` | Was fehlt oder nicht trägt |
| `grafiken` | Liste, je mit `datei`, `titel`, `hinweis`, `quelle` |
| `kritische_fragen` | Die Prüffragen zum Argumenttyp, mit Antwortstand |
| `belege` | Die Quellen, je mit Art und Verweis |

Textform in allen Feldern (`trifft_zu`, `fehlt`, `kommentar`, `zahlhinweis`,
`problem`, `folge`, `bei_ja`, `bei_nein`): Absätze durch eine Leerzeile getrennt.
Aufzählungen als nummerierte Liste, eine Zeile je Punkt, beginnend mit `1. `,
`2. ` und so weiter; die Seite macht daraus eine Liste, das Social-Media-Bild
setzt sie mit hängendem Einzug. Nur prüfbare Fakten, keine Wertungen, keine
Verweise auf interne Dokumente. Zahlen, die aus Unterlagen nicht direkt
hervorgehen, werden nachgerechnet und als Ergebnis genannt, nicht als Hinweis
auf eine Differenz.

Drei Regeln dazu:

- Ohne Fundstelle wird eine Karte mit dem Vermerk «Fundstelle offen» ausgegeben
  und geht nicht in die Netzgrafik ein.
- In `pruefung` bedeutet `null` «nicht anwendbar» und bleibt aus der erreichbaren
  Punktzahl draussen. `0` bedeutet «geprüft und nicht erfüllt». Das ist nicht
  dasselbe, und die Unterscheidung ist der Grund für die Form «x von y».
- Werturteile tragen ein leeres `pruefung`-Objekt und erscheinen ohne Note.

In `grafiken.quelle` entscheidet der Anfang über die Herkunftsmarke: beginnt der
Text mit «Eigene», wird die Grafik als eigene Auswertung gekennzeichnet und
stärker gerahmt.

---

## 4 · Die Brücke zum Kantonsratsspiegel

Das Feld `vorlage.kantonsrat_suche` verbindet die Vorlage über den
Geschäftstitel mit den namentlichen Abstimmungen in `data/all_sessions.json`.
`argumente.py` liest die Ratsdaten bei jedem Lauf frisch, schreibt also nichts
ab. Fällt die Verbindung aus, fehlt der Ratsblock, und der Rest der Seite steht
weiterhin.

Im ersten Durchlauf hat das eine unerwartete Bestätigung geliefert: Die sechs
Abstimmungen zur Verkehrsflussinitiative vom 19. Mai 2025 stehen im
Datenbestand, und die daraus berechneten Ergebnisse **35 : 20** (Initiative
abgelehnt), **39 : 16** (Gegenvorschlag angenommen) und **37 : 17** (Stichfrage)
decken sich Stimme für Stimme mit den Angaben im amtlichen
Abstimmungsmagazin. Das ist eine unabhängige Gegenprobe auf die ganze
Datenkette, nicht nur auf diese Rubrik.

Genau diese Verbindung ist der Mehrwert, den kein bestehendes Schweizer Angebot
hat: neben dem Argument steht, wie die Fraktionen tatsächlich abgestimmt haben,
als dieselbe Frage im Rat lag.

---

## 4a · Eine Vorlage als Rohling

Ein neuer Ordner braucht nur eine `vorlage.json` mit `vorlage.titel`,
`vorlage.abstimmung`, `achsen` und leeren `argumente`. Die Seite baut dann Kopf,
Platzhalter, Ratsblock (falls das Suchwort trifft) und Methode; die Übersicht
zeigt den Kasten mit «Entwurf, noch nicht veröffentlichungsreif». Muster:
`abstimmungen/2026-11-29-spitalgesetz/`, angelegt am 4. September 2026.

## 5 · Veröffentlichung

Alles Öffentliche liegt in `site/` und wird als Ganzes über GitHub Pages
ausgeliefert, unter `https://michaeljkahler.github.io/politspiegel/`. Die
Struktur:

```
site/
  index.html                   Politspiegel Schaffhausen, die Übersicht
  kantonsrat/index.html        Kantonsratsspiegel
  abstimmung/index.html        Abstimmungsspiegel, alle Abstimmungen
  abstimmung/<slug>/index.html je Vorlage eine Seite, mit Grafiken daneben
```

### Die Übersicht findet die Abstimmungen selbst

`politspiegel/bauen.py` liest alle `abstimmungen/*/vorlage.json`. Auf der
Startseite steht ein Kasten «Abstimmungsspiegel» mit der nächsten Abstimmung und
einem Aufklappfeld (aktuell, kommend, vergangen); unter `abstimmung/` liegt die
vollständige Liste mit Ergebnissen, sobald sie nachgetragen sind. Verlinkt wird
nur, was gebaut ist: Fehlt `site/abstimmung/<slug>/index.html`, meldet der Lauf
das und lässt den Eintrag weg.

Bis zum 3. September 2026 standen die Kästen samt Kennzahlen von Hand in einer
JSON-Datei. Handzahlen auf einer Übersichtsseite veralten unbemerkt, und zwar
genau dann, wenn die Seite darunter aktuell ist. Was die Übersicht sonst noch
braucht (Titel, Untertitel, den Satz zum Kantonsratsspiegel), steht in
`politspiegel/politspiegel.json`; dort lässt sich mit `ausblenden` auch eine
Abstimmung aus der Übersicht nehmen, ohne ihren Ordner anzurühren.

Der Arbeitsablauf in `.github/workflows/pages.yml` nimmt genau `site/` und baut
nichts. Die fertigen Seiten liegen im Repository; jeder Push auf `main` löst die
Veröffentlichung aus.

### Warum kein Bauen in der Werkstatt

Die Erzeugung braucht die Wortprotokolle, rund 143 MB, die aus gutem Grund
nicht im Repository liegen. Ein Bauschritt in der Werkstatt müsste sie jedes
Mal neu beschaffen, wäre also von der Verfügbarkeit von sh.ch abhängig, und
eine Veröffentlichung würde stillschweigend fehlschlagen, wenn dort etwas
umgestellt wird. Fertige Dateien zu versionieren kostet Historie, aber es macht
jede veröffentlichte Fassung nachvollziehbar.

### Bilder für Social Media

Jede Abstimmungsseite trägt unten links den Knopf «Bild für Social Media».
Er öffnet eine Vorschau mit Motivwahl; das Bild entsteht im Browser auf einer
Leinwand 1080 × 1350 und folgt dem gewählten Hell- oder Dunkelmodus, gleich
wie im Kantonsratsspiegel. Die Logik liegt in `bausteine/teilen.py`, die
Daten dafür nimmt die Seite als JSON mit (`<script id="bild-daten">`).

Motive: die Vorlage (Titel, Termin, worum es geht, bei Ja / bei Nein), die
Gegenüberstellung der Belegqualität (Netzgrafik beider Seiten), je ein
Aussagenpaar (Pro und Contra untereinander, mit Netz und Punktzahl), der
Kantonsrat (wie die Fraktionen gestimmt haben) und je Argument ein Karussell.

Das Karussell zeigt die Karte einer Aussage Folie für Folie: Aussage und
Träger, Belegprüfung mit Netz und Balken, was zutrifft, was fehlt (lange
Texte auf mehreren Folien, Absätze bleiben zusammen), die Grafiken, die
kritischen Fragen, die Grundlagen der Prüfung. Die letzte Folie zeigt
immer die Aussage der Gegenseite mit gleicher Nummer und deren Belegwert.
Das ist die Regel gegen einseitiges Teilen: Kein Karussell verlässt die Seite
ohne Gegenseite. «Alle Folien herunterladen» speichert die Folge als
nummerierte PNG-Dateien.

Im Bild des Kantonsrats sind die Balken bewusst nicht in den Seitenfarben
gehalten (Ja dunkel, Nein hell): Wer für die Initiative ist, stimmt beim
Gegenvorschlag mit Nein, und eine grüne Nein-Stimme wäre irreführend.

### Verweise in den Kantonsratsspiegel

Jede namentliche Abstimmung im Ratsblock verweist auf die Karte im
Kantonsratsspiegel: `kantonsrat/#s=<Sitzung>&nr=<Nummer>`, die Sitzung so, wie
sie in den Daten heisst, mit `encodeURIComponent` kodiert. `dashboard.js` liest
die Adresse beim Laden (`leseAdresse`), setzt die Sitzung als Bereich, öffnet
die Rubrik Abstimmungen und lässt die Karte kurz aufblitzen.

### Impressum

`politspiegel/politspiegel.json` trägt unter `impressum` die verantwortliche
Person, die Mailadresse (zweiteilig, wird im Browser zusammengesetzt), einen
Satz zum Projekt und den Datenschutzhinweis. `politspiegel/impressum.py` baut
daraus den Block, den Übersicht, Abstimmungsliste und jede Abstimmungsseite im
Fuss einbinden; der Kantonsratsspiegel führt dieselben Angaben in seinem Fuss.

### Die alte Adresse

Bis zum Umbau lag der Kantonsratsspiegel unter der blanken Adresse. Er liegt
jetzt unter `/kantonsrat/`, und an der alten Stelle steht die Übersicht. Damit
geteilte Links gültig bleiben, trägt die Übersichtsseite einen sichtbaren
Verweis auf den Kantonsratsspiegel an erster Stelle, und `site/dashboard.html`
leitet dorthin weiter.

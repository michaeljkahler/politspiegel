# Finanzspiegel

Vierte Ebene des Politspiegels, unter `/finanzen/`. Budget, Staatsrechnung und
Finanzplan des Kantons Schaffhausen, vom Gesamtbild bis zum einzelnen Konto und
Investitionsvorhaben.

```
python3 finanzspiegel/budget_pdf.py finanzspiegel/daten/pdf/budget2027_vorlage.pdf finanzspiegel/daten/budget2027.csv
python3 finanzspiegel/budget_pdf.py finanzspiegel/daten/pdf/budget2026.pdf finanzspiegel/daten/budget2026.csv
python3 finanzspiegel/budget_pdf.py finanzspiegel/daten/pdf/rechnung2025.pdf finanzspiegel/daten/rechnung2025.csv
python3 finanzspiegel/finanzplan_pdf.py finanzspiegel/daten/pdf/budget2027_vorlage.pdf finanzspiegel/daten/finanzplan2027.json
python3 finanzspiegel/daten.py      # zusammenführen, Kontrollen    -> daten/finanzspiegel.json
python3 finanzspiegel/analyse.py    # Prüfhinweise                  -> daten/finanzspiegel.json
python3 finanzspiegel/bauen.py      # Seite                         -> site/finanzen/index.html
python3 finanzspiegel/pruefen.py    # Seite im Browser prüfen (Playwright, Rückgabewert 1 bei Abweichung)
python3 politspiegel/bauen.py       # Übersicht mit Finanzkasten
```

Bilder und Texte für Social Media: `python3 scripts/finanzen_social.py --jahr b27`
(Entwürfe unter `site/social/finanzen/<serie>/`, Freigabe über Metricool).

## Datensätze

| Schlüssel | Datensatz | Quelle | Tiefe |
|---|---|---|---|
| b25 | Budget 2025 | Vergleichsspalte der Staatsrechnung 2025 | Konto |
| r25 | Rechnung 2025 | Staatsrechnung 2025 | Konto, Vorhaben |
| b26 | Budget 2026 | beschlossen vom Kantonsrat am 17. November 2025 | Konto, Vorhaben |
| b27 | Budget 2027 | Vorlage des Regierungsrates vom 15. September 2026 | Konto, Vorhaben |
| p28, p29, p30 | Finanzplan 2028 bis 2030 | Bericht zum Budget 2027, Ziffern 2.1, 2.2, 2.3, Kapitel 7 | zweistellige Sachgruppe |

Wo zwei Dokumente denselben Wert liefern, gilt das spätere. Die Vergleichsspalten
des Budgets 2027 (Budget 2026, Rechnung 2025) dienen nur dem Dokumentenabgleich.

Massgebend ist beim Budget die vom Kantonsrat beschlossene Fassung (Deckblatt
«beschlossen vom Kantonsrat am ...»). Für 2027 liegt bis zur Budgetdebatte nur die
Vorlage vor; Seite, Übersicht und Social-Media-Texte führen den Zusatz «Vorlage».

## Woher die Zahlen kommen

Der Kanton publiziert Budget und Staatsrechnung nur als PDF.

1. `budget_pdf.py` liest die Detailzahlen (Kapitel 6) über die Wortpositionen im PDF:
   Erfolgsrechnung je Konto mit dem Kommentar der Dienststelle, Investitionsrechnung
   je Konto und Vorhaben. Die Spaltenkanten stammen aus der Kopfzeile jeder Seite.
   Selbstprüfung: Die Summe der gelesenen Konten je Dienststelle, Fonds und
   Departement muss der gedruckten entsprechen, in der Investitionsrechnung zusätzlich
   je Konto bzw. Vorhaben. Ausgabe `<name>.csv`, `<name>_ir.csv`, `<name>_pruefung.json`.
2. `finanzplan_pdf.py` liest die Übersichtstabellen des Berichts (Ziffern 1.6, 2.1,
   2.2, 2.3, 2.5, 4.4.2, 4.4.3, 5.3.1, 5.3.2, Steuerfuss, Kapitel 7) in 1'000 Franken
   und rechnet jede Zwischensumme aus ihren Teilen nach (Toleranz 2 wegen Rundung).
   Aus Ziffer 5.3.10 nimmt es die Nummern der Verpflichtungskredite für den Abgleich
   mit Kapitel 6.
3. `daten.py` führt alles zusammen und vergleicht die Summen je zweistelliger
   Sachgruppe mit Ziffer 2.1, je Departement mit Ziffer 4.4.2 und die
   Nettoinvestitionen mit Ziffer 2.2.
4. `analyse.py` schreibt die Prüfhinweise: Veränderungen je Dienststelle und Vorhaben
   über den Schwellen in `SCHWELLEN`, Strukturänderungen, Dokumentenabgleich. Jeder
   Hinweis nennt Beträge und die Kommentare der Dienststellen im Wortlaut.

Stand der Selbstprüfung:

| Dokument | Konten ER | Dienststellen | Summen ER | Zeilen IR | Abweichungen |
|---|---:|---:|---:|---:|---:|
| Budget 2027, Vorlage | 2'933 | 126 | 471 | 187 | 0 |
| Budget 2026, beschlossen | 2'951 | 124 | 474 | 188 | 0 |
| Staatsrechnung 2025 | 3'034 | 123 | 471 | 160 | 0 |
| Finanzplan 2027–2030, Übersichten | | | | | 0 |

Zwei Abweichungen zwischen Dokumenten stehen als Prüfhinweis auf der Seite:

1. Nettoinvestitionen Budget 2027: Detailzahlen 111.1 Mio. Franken, Ziffer 2.2 des
   Berichts 110.1 Mio. Die Seite rechnet mit 111.1. Die Differenz von 0.95 Mio.
   entspricht den Verpflichtungskrediten IPR0142 (0.55 Mio.) und IPR0189 (0.40 Mio.)
   des Baudepartements, die in Kapitel 6 stehen und in der Liste der Ziffer 5.3.10
   fehlen.
2. Konto 3638.11 im Fonds 2298.7251 Lotteriegewinn-Fonds: Budget 2026 in der
   beschlossenen Fassung 180'000 Franken, in der Vergleichsspalte des Budgets 2027
   200'000 Franken.

Die Sachgruppennamen stammen aus der Artengliederung des FS-Modells der
Eidgenössischen Finanzverwaltung (`daten/kontenplan.xlsx`, Blatt fs_er), ergänzt um
die Gruppen, die das Statistikmodell nicht führt (durchlaufende Beiträge, interne
Verrechnungen, Abschluss, Investitionsrechnung), nach Kontenrahmen HRM2 in `daten.py`.

## Was die Seite zeigt

1. Auswahl: bis zu drei Datensätze A, B, C aus Rechnung, Budget und Finanzplan 2025
   bis 2030. A ist der Bezug für alle Differenzen.
2. Woher, wohin: ordentlicher Ertrag und Aufwand von A nach Sachgruppe als zwei
   Balken auf derselben Skala, dazu die Rechnung vom ordentlichen zum Gesamtergebnis.
3. Entwicklung 2025 bis 2030: Kennzahl im Zeitverlauf (Rechnung, Budget, Finanzplan),
   Nettoaufwand je Departement und je Aufgabenfeld des Finanzplans.
4. Vergleich: Kennzahlen, Icicle je Datensatz auf gemeinsamer Skala, Tabelle mit
   Differenzen und Kommentaren. Erfolgs- oder Investitionsrechnung, Gliederung nach
   Dienststelle (Departement, Dienststelle, Fonds, Konto) oder Sachgruppe (zwei- und
   dreistellig, Konto), Ansicht Aufwand, Ertrag oder netto, ordentliche oder alle
   Konten, Suche, CSV. Ist ein Finanzplanjahr gewählt, gilt die Gliederung nach
   Sachgruppe auf der obersten Ebene.
5. Prüfhinweise aus `analyse.py`, mit Filter nach Art und Sprung in den Vergleich.
6. Methode und Quellen.

Grafik (`grafik.js`, Knopf unten rechts): Kuchen, Balkenliste, Ringdiagramm mit bis zu
drei Datensätzen (A aussen), Woher und wohin, Entwicklung, Kennzahlen; Ebene wählbar
bis «alle Konten»; Formate 4:5 (1080 × 1350), 16:9 (1920 × 1080), 3:2 (1800 × 1200);
PNG oder Zwischenablage. Die Grafik zeichnet die gewählte Ansicht, ohne eigene Rechnung.

Jede Ansicht steht in der Adresse (`#d=b27,b26&r=er&g=inst&a=A&u=ord&p=d22/s2210`)
und lässt sich teilen.

Gezeigt ist als Vorgabe das Ordentliche (Sachgruppen 30 bis 37, 40 bis 47).
Ausserordentliches (38, 48) und Fondsabschlüsse (90) rechnet der Überblick vor,
interne Verrechnungen (39, 49) stehen beidseits gleich. So stimmen die Totale mit
Ziffer 2.1 des Berichts überein.

## Neues Dokument

1. PDF nach `daten/pdf/` legen (nicht im Repo) und in `daten/quellen.json` eintragen.
2. `budget_pdf.py` darauf laufen lassen, Selbstprüfung lesen: 0 abweichend.
3. Beim neuen Budget mit Finanzplan: `finanzplan_pdf.py`, Ausgabe `finanzplanJJJJ.json`.
4. In `daten.py` `JAHRE`, `PLAN`, `ER_QUELLEN`, `IR_QUELLEN` ergänzen; in `analyse.py`
   die Jahre der Regeln.
5. `daten.py`, `analyse.py`, `bauen.py`, `pruefen.py`, `politspiegel/bauen.py`.

Beschlossenes Budget 2027 (nach der Budgetdebatte):

1. PDF der beschlossenen Fassung als `daten/pdf/budget2027.pdf` ablegen, Eintrag in
   `quellen.json` ersetzen (Datei, Adresse, Fassung «beschlossen vom Kantonsrat am ...»,
   Datum der Publikation).
2. `budget_pdf.py` und `finanzplan_pdf.py` auf die neue Datei.
3. In `daten.py` bei `JAHRE` (b27) und `PLAN` die Fassung ändern und `"vorlage": 1`
   entfernen. Seite, Grafiken, Übersicht und Social-Media-Texte lassen den Zusatz
   «Vorlage» dann weg.
4. In `bauen.py` unter «Datengrundlage» den Satz zu den Nettoinvestitionen
   (Ziffer 2.2) mit den neuen Zahlen prüfen.
5. Schritt 5 oben.

Die Spaltenreihenfolge unterscheidet sich zwischen Budget (Budget, Budget Vorjahr,
Rechnung Vorvorjahr) und Staatsrechnung (Rechnung, Budget, Rechnung Vorjahr);
`budget_pdf.py` liest sie aus der Kopfzeile. Die Investitionsrechnung gliedert im
Budget Konto vor Vorhaben, in der Staatsrechnung Vorhaben vor Konto.

## Grenzen

1. Der Finanzplan liegt nur zusammengefasst vor: zweistellige Sachgruppen,
   Nettoinvestitionen, Bilanz, Aufgabenfelder. Kein Drilldown auf Dienststelle oder
   Konto.
2. Funktionale Gliederung (Bildung, Gesundheit, ...) gibt es im Bericht nur einstufig
   (Ziffer 4.4.3). Brutto und feiner beim Bund (EFV, Finanzstatistik).
3. Rechnung 2024 ist kein eigener Datensatz. Sie steht als Vergleichsspalte in der
   Staatsrechnung 2025 und im Budget 2026 (`rechnung_2024`); beide ergeben ein
   Gesamtergebnis von +19.1 Mio. Franken. Die frühere Summe von 15.8 Mio. aus der
   Staatsrechnung 2025 war ein Lesefehler auf Seite 279 (Fonds 2398.7236: neun
   Beträge der Abweichungsspalte in der Spalte 2024, zusammen 3.29 Mio.), behoben
   mit den Spaltenkanten aus der Kopfzeile.
4. Der Parser hängt am Seitenlayout des Kantons. Ändert es, meldet die Selbstprüfung
   Abweichungen; dann `budget_pdf.py` anpassen.

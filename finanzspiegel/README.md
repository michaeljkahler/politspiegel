# Finanzspiegel

Vierte Ebene des Politspiegels, unter `/finanzen/`. Budget und Staatsrechnung des
Kantons Schaffhausen, vom Gesamtbild bis zum einzelnen Konto.

```
python3 finanzspiegel/budget_pdf.py finanzspiegel/daten/pdf/budget2026.pdf finanzspiegel/daten/budget2026.csv
python3 finanzspiegel/budget_pdf.py finanzspiegel/daten/pdf/rechnung2025.pdf finanzspiegel/daten/rechnung2025.csv
python3 finanzspiegel/daten.py      # CSV zusammenfuehren   -> daten/finanzspiegel.json
python3 finanzspiegel/bauen.py      # Seite bauen           -> site/finanzen/index.html
python3 politspiegel/bauen.py       # Uebersicht mit Finanzkasten neu bauen
```

## Woher die Zahlen kommen

Der Kanton publiziert Budget und Staatsrechnung nur als PDF. `budget_pdf.py` liest
die Detailzahlen der Erfolgsrechnung (Kapitel 6) ueber die Wortpositionen im PDF
aus und prueft sich selbst: Die Summe der gelesenen Konten je Dienststelle, je
Spezialfinanzierung und je Departement muss der gedruckten entsprechen. Budget
2026 und Staatsrechnung 2025: alle Summen exakt, Gesamtergebnisse auf den Franken
(Budget 2025 −49.0, Rechnung 2025 +14.9, Budget 2026 −62.1 Mio.).

Massgebend ist die vom Kantonsrat beschlossene Fassung des Budgets (Deckblatt
«beschlossen vom Kantonsrat am ...»), nicht die Vorlage des Regierungsrates vom
August. sh.ch fuehrt beide auf der Budgetseite.

Die Sachgruppennamen stammen aus der Artengliederung des FS-Modells der
Eidgenoessischen Finanzverwaltung (`daten/kontenplan.xlsx`, Blatt fs_er), ergaenzt um
die Gruppen, die das Statistikmodell nicht fuehrt (durchlaufende Beitraege, interne
Verrechnungen, Abschluss), nach Kontenrahmen HRM2 in `daten.py`.

## Was die Seite zeigt

1. Ueberblick «Woher, wohin»: ordentlicher Ertrag und Aufwand als zwei Balken auf
   derselben Skala, nach Sachgruppe, mit Erklaerung je Gruppe. Kennzahlen und die
   Rechnung vom ordentlichen zum Gesamtergebnis.
2. Drilldown als Icicle: Departement, Dienststelle, Fonds, Konto, oder Sachgruppe
   zwei- und dreistellig, Konto. Klick geht eine Stufe tiefer. Tabelle mit Betrag,
   Anteil und Vergleichsjahr.
3. Bild fuer Social Media, 1080 x 1350, im Browser gezeichnet. Drei Motive: Kuchen
   der geoeffneten Ebene, Balkenliste der geoeffneten Ebene, Ueberblick Woher/Wohin.

Gezeigt ist das Ordentliche (Sachgruppen 30 bis 37, 40 bis 47). Ausserordentliches
(38, 48) und Fondsabschluesse (90) rechnet der Ueberblick vor, interne Verrechnungen
(39, 49) stehen beidseits gleich und fehlen. So stimmen die Totale mit Kapitel 1.7
des Berichts ueberein.

## Neues Jahr

1. PDF nach `daten/pdf/` legen (nicht im Repo). Beim Budget die beschlossene Fassung
   nehmen, sobald sie da ist (nach der Novembersitzung); bis dahin die Vorlage, mit
   Hinweis auf der Seite.
2. `budget_pdf.py` darauf laufen lassen, Selbstpruefung lesen: 0 abweichend.
3. In `daten.py` die Liste `JAHRE` und die beiden `lade(...)`-Aufrufe ergaenzen.
4. `daten.py`, `bauen.py`, `politspiegel/bauen.py`.

Die Spaltenreihenfolge unterscheidet sich zwischen Budget (Budget, Budget Vorjahr,
Rechnung Vorvorjahr) und Staatsrechnung (Rechnung, Budget, Rechnung Vorjahr);
`budget_pdf.py` liest sie aus der Kopfzeile.

## Grenzen

- Funktionale Gliederung (Bildung, Gesundheit, ...) gibt es nur einstufig im
  Bericht; ein Drilldown ist dort nicht moeglich. Brutto und feiner beim Bund
  (EFV, Finanzstatistik), bis Rechnungsjahr 2024.
- Rechnung 2024 fehlt, weil die Vergleichsspalten der PDF nur Konten fuehren, die
  im spaeteren Dokument noch vorkommen (Summe 15.8 statt 19.1 Mio.).
- Der Parser haengt am Seitenlayout des Kantons. Aendert es, meldet die
  Selbstpruefung Abweichungen; dann `budget_pdf.py` anpassen.

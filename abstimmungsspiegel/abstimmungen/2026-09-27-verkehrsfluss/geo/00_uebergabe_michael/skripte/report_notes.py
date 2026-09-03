# -*- coding: utf-8 -*-
# Methodik- und Quellen-Fussnoten je Kapitel/Grafik fuer den Hauptbericht (Strang A).
# Werte konsistent mit knv.py, suit.py und dem Datengrundlagen-xlsx.

DG_NOTE = (
 "Betroffen sind die Kantonsstrassen der Funktionsklassen überregional und regional (verkehrsorientiert) innerhalb des "
 "Baugebiets; überlokale (siedlungsorientierte) Abschnitte dienen nur als Kontext. Innerorts ist das rechtsgültige Baugebiet "
 "der Nutzungsplanung. Unfälle zählen zu einer Strasse, wenn der Unfallort im Baugebiet und höchstens 25 m von einer "
 "Kantonsstrasse (ohne Nationalstrasse) liegt; Auswertungszeitraum 2011 bis 2025 (15 Jahre). Längen aus der Achsgeometrie "
 "in LV95 (EPSG:2056). Näherungswerte für die politische Diskussion, keine amtliche Statistik."
)

G14_NOTE = (
 "Je Gemeinde alle benannten Abschnitte auf einheitlichen Achsen (Verkehrsleistung 0 bis 25'000 Fz-km pro Tag, Unfalldichte "
 "0 bis 6). Blaue Bänder je 1 Unfall pro km und Jahr, rote Linie der kantonale Median (0,75 Unfälle pro km und Jahr). Farbig "
 "und nummeriert die verkehrsorientierten, blass die siedlungsorientierten Abschnitte. Quellen: DTV, Kantonsstrassen und "
 "Lärmbelastungskataster geo.sh.ch; Unfälle ASTRA (data.geo.admin.ch)."
)

G16B_NOTE = (
 "Je Abschnitt der Nutzen je km gegen die Zeitkosten je km (beide in Franken pro km und Jahr), dadurch unabhängig von der "
 "Gemeindegrösse vergleichbar. Einheitliche Achsen, Zonen die Terzile des Kosten-Nutzen-Verhältnisses, Sätze wie in der "
 "kantonsweiten Streuung. Quellen: Zeitwert ARE/VSS; Unfallkosten bfu/Ecoplan; Lärm und Wertminderung BAFU, ZKB/Baranzini."
)

METHODS = {
 "G4_Karte_Breiten.png":
   "Mittlere Fahrbahnbreite je Ortsdurchfahrt aus den Breitenklassen von swissTLM3D (10, 8, 6, 4, 3, 2 m), längengewichtet "
   "über die innerorts liegenden Abschnitte. Quellen: swissTLM3D (swisstopo, geo.admin.ch); Kantonsstrassen und Baugebiet geo.sh.ch.",
 "G11_Histogramm.png":
   "Längengewichtete Verteilung der betroffenen Kantonsstrassen-Kilometer nach swissTLM3D-Breitenklasse, Anteile in Prozent "
   "der rund 80,4 km innerorts. Quellen: swissTLM3D (swisstopo); Kantonsstrassen und Baugebiet geo.sh.ch.",
 "G1_Strassenbreiten.png":
   "Massstäblicher Fahrbahnquerschnitt mit den Normprofilen für Personenwagen, Lastwagen, Bus und Velo und der je "
   "Begegnungsfall nötigen Fahrbahnbreite, Tempo 50 gegenüber Tempo 30. Quellen: VSS SN 640 201 (geometrisches Normalprofil), "
   "SN 640 070 (Fuss- und Veloverkehr).",
 "G2_Kreuzungen.png":
   "Erforderliche Sichtweite an Einmündungen nach Geschwindigkeit, rund 40 m bei Tempo 50 und rund 20 m bei Tempo 30. "
   "Quellen: VSS SN 640 273a (Knoten, Sichtweiten), SN 640 263.",
 "G8_Unfallstruktur.png":
   "Alle Unfälle mit Personenschaden 2011 bis 2025 (15 Jahre) auf Kantonsstrassen innerorts, zugeordnet, wenn der Unfallort "
   "im Baugebiet und höchstens 25 m von einer Kantonsstrasse (ohne Nationalstrasse) liegt, aufgeteilt nach beteiligter "
   "Verkehrsart. Quelle: ASTRA, Strassenverkehrsunfälle mit Personenschaden (data.geo.admin.ch).",
 "G9_Breite_Unfaelle.png":
   "Unfalldichte (Unfälle je km und Jahr) je Ortsdurchfahrt gegen die mittlere Fahrbahnbreite; Länge aus der Achsgeometrie "
   "im Baugebiet (LV95). Quellen: ASTRA (data.geo.admin.ch); swissTLM3D (swisstopo); Kantonsstrassen geo.sh.ch.",
 "G10_Laerm.png":
   "Zahl der Gebäudefassaden über dem Immissionsgrenzwert entlang der Kantonsstrassen innerorts aus dem "
   "Lärmbelastungskataster; Tempo 30 senkt den Pegel um rund 3 dB(A). Quellen: Lärmbelastungskataster Kanton Schaffhausen "
   "(geo.sh.ch); Wirkung BAFU; Lärmschutz-Verordnung LSV.",
 "G3_KostenNutzen.png":
   "Szenario flächendeckend Tempo 30. Zeitkosten: Fahrleistung mal 20 s je km, 365 Tage, 42,50 CHF je Stunde. Nutzen: "
   "Unfallkostenersparnis (20 Prozent von rund 139'000 CHF je Unfall, über 15 Jahre annualisiert) und annualisierte "
   "Lärmaufwertung (900'000 CHF je Fassade, 0,5 Prozent je dB, 3 dB, 3 Prozent Kapitalisierung). Rein monetär, ohne "
   "nicht-monetäre Nutzen. Quellen: Zeitwert ARE/VSS (SN 641 822a); Unfallkosten bfu/Ecoplan; Reisezeitwirkung ASTRA FB 1663; "
   "Lärm und Wertminderung BAFU, ZKB/Baranzini.",
 "G12_Prioritaeten.png":
   "Alle 57 verkehrsorientierten Abschnitte ab 0,2 km. Waagrecht die Verkehrsleistung (DTV mal Länge), senkrecht die "
   "Unfalldichte (15 Jahre), Kreisfläche die Fassaden über dem Grenzwert, Farbe die Eignung aus Unfalldichte und Lärm "
   "(Nutzen-Score: Unfälle je km und Jahr plus Fassaden geteilt durch 50; hoch ab 1,5, mittel ab 0,6). Rote Linie: kantonaler "
   "Median 0,75. Quellen: geo.sh.ch (DTV, Kantonsstrassen und Richtplan, Lärmkataster); Unfälle ASTRA.",
 "G15_Nutzen_Karte.png":
   "Kantonsstrassen innerorts, aufgelöst nach benannten Abschnitten (Verschnitt Strassenrichtplan mit Baugebiet, Namen und "
   "DTV aus der Netzbelastung). Verkehrsorientiert sind die Funktionsklassen überregional und regional. Eignung aus dem "
   "Nutzen-Score (Unfälle je km und Jahr plus Fassaden geteilt durch 50). Quellen: Strassenrichtplan und Netzbelastung "
   "geo.sh.ch; Unfälle ASTRA; Lärmkataster geo.sh.ch.",
 "G16_KostenNutzen_Streuung.png":
   "Je Abschnitt der monetarisierte Nutzen (Unfall- und Lärmkostenersparnis) gegen die Zeitkosten, in Franken pro Jahr, "
   "dieselben Sätze wie im Blatt Wirtschaftlichkeit. Zonen: Terzile des Verhältnisses über die Abschnitte ab 2000 Fz-km pro "
   "Tag (hoch ab 0,11, mittel ab 0,07). Verfahren analog NISTRA (ASTRA). Quellen: Zeitwert ARE/VSS; Unfallkosten bfu/Ecoplan; "
   "Lärm BAFU/ZKB.",
 "G17_Gemeinde_KNV.png":
   "Summe des Nutzens geteilt durch die Summe der Zeitkosten je Gemeinde, über die verkehrsorientierten Abschnitte "
   "(Gemeinden mit mindestens zwei Abschnitten). Zonen: Terzile der Abschnittsverteilung. Rein monetär, kein Wert erreicht "
   "1,0. Quellen: wie bei der Streuung (ARE/VSS, bfu/Ecoplan, BAFU/ZKB).",
 "G5_Buslinien.png":
   "Zusatzfahrzeit je Regionalkurs: innerorts gefahrene Kantonsstrassen-Kilometer je Linie mal 20 s je km, hin und zurück. "
   "Linienführung aus OpenStreetMap. Quellen: OpenStreetMap-Mitwirkende; Reisezeitwirkung ASTRA FB 1663.",
 "G6_Blaulicht.png":
   "Rechnerische Mehrzeit rund 30 s je km; rechtlich sind Blaulichtfahrten nach Art. 100 Ziff. 4 SVG nicht an das "
   "signalisierte Tempo gebunden. Quellen: SVG Art. 100; ASTRA-Merkblatt Blaulicht und Wechselklanghorn; Studien Freiburg "
   "und Luzern.",
 "G7_Tempo30_Zone30.png":
   "Gegenüberstellung der Instrumente Tempo-30-Strecke (streckenbezogen, auf verkehrsorientierten Strassen) und Zone 30 "
   "(flächig, Quartierstrassen) nach Signalisationsrecht. Quellen: Signalisationsverordnung SSV (Art. 22a, 108); "
   "UVEK-Verordnung SR 741.213.3.",
}

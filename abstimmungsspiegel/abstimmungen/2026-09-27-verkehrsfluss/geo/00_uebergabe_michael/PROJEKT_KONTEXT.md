# Projekt-Kontext und Übergabe: Verkehrsflussinitiative Kanton Schaffhausen

**Zweck dieses Dokuments:** Vollständige Übergabe des Projekts an ein anderes Cowork-Projekt. Es fasst Fragestellung, Datengrundlagen, Methodik samt Formeln, Ergebnisse, gelieferte Dateien und Skripte so zusammen, dass eine andere Claude-Sitzung das Projekt ohne den ursprünglichen Chatverlauf fortführen kann.

**Stand:** ursprüngliche Analysen 24. Juli 2026 (Faktengrundlagen/Wirtschaftlichkeit) und 19./20. August 2026 (Infrastruktur-Nähe), Übergabe erstellt 3. September 2026.

**Hinweis zur Datenlage:** Die Cloud-Arbeitsumgebung, in der die Berechnungen liefen, wurde zwischenzeitlich zurückgesetzt. Die Rohdaten und Zwischenergebnisse liegen deshalb nicht mehr in der Sitzung, sind aber vollständig in den bereits gelieferten ZIP-Paketen (siehe Abschnitt 7) und in den ursprünglichen Nutzer-Uploads enthalten. Die Rechenskripte sind in diesem Bundle unter `Skripte/` rekonstruiert.

---

## 1. Fragestellung und Kontext

Am **27. September 2026** stimmt der Kanton Schaffhausen über die **Verkehrsflussinitiative** ab (Volksinitiative «für flüssigen Verkehr auf kantonalen Hauptstrassen»). Die Initiative will auf den **verkehrsorientierten Kantonsstrassen innerorts** grundsätzlich **Tempo 50** festschreiben und bauliche Massnahmen sowie Verkehrsanordnungen verbieten, die den Verkehrsfluss behindern. Sie lässt Ausnahmen für **«kurze Abschnitte»** zu. Der Kantonsrat lehnt die Initiative ab und stellt einen Gegenvorschlag gegenüber.

Das Projekt liefert eine **neutrale, quellenbasierte Faktengrundlage** (bewusst nicht wertend, für ein Abstimmungsdokument geeignet) und besteht aus zwei Arbeitssträngen:

- **Strang A – Faktengrundlagen, Grafiken, Wirtschaftlichkeit:** kantonsweite Übersichten (Fahrbahnbreiten, Unfallstruktur, Lärm), eine Kosten-Nutzen-Betrachtung (KNV) und Detailgrafiken je Gemeinde. Ergebnis: 34-seitiger Bericht + Datengrundlage-Excel + Grafiken.
- **Strang B – Infrastruktur-Nähe / «kurze Abschnitte»:** je Gemeinde eine Karte der betroffenen Strassen mit Umkreisen (100/300/500 m) um Schulen, Kindergärten, Alters-/Pflegeheime und weitere Sozialeinrichtungen, um zu bestimmen, wie sich der Passus «kurze Abschnitte» an konkreten Beispielen definieren lässt.

**Nutzerpräferenzen (durchgehend beachten):** kein Gedankenstrich „ – " (stattdessen Komma oder „und"); immer generisches Maskulinum nach deutscher Rechtschreibung, nie gendern. Der Nutzer bevorzugt zügiges Handeln mit Rückfragen in Prosa statt formaler Multiple-Choice-Abfragen. Der Nutzer arbeitet bei Winzeler + Bühl (Raumplanung, Schaffhausen).

---

## 2. Datengrundlagen

Alle Geodaten im Bezugssystem **LV95 (EPSG:2056)**, Koordinaten in Metern (Ostwert ~2'680'000–2'710'000, Nordwert ~1'279'000–1'295'000).

| Datei | Inhalt | Quelle | Struktur (Kernfelder) |
|---|---|---|---|
| `roads_fkt.geojson` | Kantonsstrassen mit Funktionsklasse (Netzhierarchie), 2585 LineStrings | geo.sh.ch (Strassenrichtplan „bestehend.fkt") | `typ` (= Netzhierarchie), `gemeinde`, `ortsteil`, `strasse_nr`, `uuid` |
| `baugebiet.geojson` | Nutzungsplanung Baugebiet, 226 Polygone | geo.sh.ch | `baugebiet` („ja"/„nein"), `gemeinde`, `ortsteil`, `uuid` |
| `netzbelastung.geojson` | Strassennamen + DTV, 981 LineStrings | geo.sh.ch | `strassenname`, `durchschnittlicher_taeglicher_verkehr_fz_d` (DTV), `uuid` |
| `laerm_tag.geojson` | Lärmbelastungskataster Tag (Fassaden/Immissionen) | geo.sh.ch | Immissionswerte je Fassade |
| `per_abschnitt.json` | 163 benannte Strassenabschnitte mit allen abgeleiteten Kennwerten (zentrale Analysetabelle) | eigene Berechnung | siehe unten |
| `master_gemeinde.json` | Kennwerte je Gemeinde (Unfälle nach Schwere, Fahrleistung, Fassaden > IGW, km) | eigene Berechnung | `Gemeinde`, `getoetet`, `schwer`, `leicht`, `unf_total`, `fahrleistung`, `fass_igw`, `km_innerorts` |
| `infra_SH_v2.gpkg` | Infrastruktur-Standorte + Grenzen (Nutzer-Upload, Version 2) | Nutzer (OSM + kantonal) | Layer siehe Abschnitt 5 |
| `richtplan/` (ZIP-Inhalt) | Kantonaler Strassenrichtplan (dxf/gpkg/interlis/shape) | Nutzer-Upload / geo.sh.ch | — |
| `unfaelle_ch.csv(.zip)` | ASTRA-Unfälle Personenschaden 2011–2025 | ASTRA (data.geo.admin.ch) | Unfallort LV95, Schweregrad |

**Netzhierarchie in `roads_fkt.geojson` (`typ`) und ihre Zuordnung:**

- `Kanton.ueberregionale Strasse` (279) und `Kanton.regionale Strasse` (798) → **verkehrsorientiert (VO)** = von der Initiative betroffen.
- `Kanton.ueber lokale Strasse` (1394) → **siedlungsorientiert (SO)** = Kontext, nicht Kern.
- `Kanton.Nationalstrasse` (114) → ausgeschlossen.

**Innerorts-Abgrenzung:** Vereinigung der Baugebiet-Polygone mit `baugebiet == "ja"`. Bewusste, transparente Näherung; nicht identisch mit der signalisierten Innerorts-Strecke zwischen den Ortstafeln (auf Wunsch über einen Ortstafel-Layer verfeinerbar).

**`per_abschnitt.json` – Felder je Abschnitt:** `gemeinde`, `name`, `nrs`, `typ`, `fkt` (`VO`/`SO`), `km`, `dtv`, `fahrleistung` (= DTV × km), `unf` (Unfälle im Abschnitt, 15 Jahre), `fuss`, `velo`, `unf_km_jahr` (Unfalldichte = unf / km / 15), `fass_igw` (Fassaden über Immissionsgrenzwert), `uuids`. Aufgebaut per Spatial Join `roads_fkt ∩ baugebiet`, Namen/DTV aus `netzbelastung`, Unfälle (≤ 20 m) und Lärmfassaden (> IGW, ≤ 25 m) dem nächsten Abschnitt via STRtree zugeordnet. Generische Namen („Namenlos"/reine Nummern) werden zu „Kantonsstrasse {nr}".

---

## 3. Methodik Strang A: Faktengrundlagen und Wirtschaftlichkeit (KNV)

### 3.1 Kosten-Nutzen-Verhältnis (KNV), rein monetär, illustratives Szenario

Zentrales Modul `knv.py`. Szenario: flächendeckend Tempo 30 statt 50 auf den betroffenen Strassen. **Nutzen = Unfallkostenersparnis + annualisierte Lärmaufwertung; Kosten = Zeitkosten.** Nicht enthalten sind nicht-monetäre Nutzen (Aufenthaltsqualität, Gesundheit, subjektive Sicherheit); die Zeitkosten sind in dichten Stadtabschnitten eher überschätzt.

**Konstanten (Sätze):**

- `VTTS = 42.50` CHF je Fahrzeugstunde (Zeitwert, ARE/VSS, SN 641 822a)
- `DT_S = 20` Sekunden Zusatzzeit je km (empirisch, ASTRA FB 1663); theoretische Variante 48 s/km
- `DAYS = 365`
- `RED = 0.20` Unfallreduktion durch Tempo 30 (Szenario-Annahme)
- `YEARS = 15` Auswertungszeitraum Unfälle
- `VAL_FASS = 900000` CHF Wert je lärmbelastete Fassade (Annahme)
- `NSDI = 0.005` Wertminderung je dB (ZKB/Baranzini)
- `DB = 3` dB-Reduktion durch Tempo 30 (BAFU)
- `CAP = 0.03` Kapitalisierungssatz zur Annualisierung
- `UNFALLKOSTEN_MEAN = 139275` CHF, mittlere Kosten je Personenschaden-Unfall, kantonal gewichtet aus Schweregraden: (Getötete × 3'170'000 + Schwerverletzte × 530'000 + Leichtverletzte × 33'000) / Unfälle_total (bfu/Ecoplan)

**Formeln (je Abschnitt p):**

```
zeitkosten(p)   = p.fahrleistung * DT_S/3600 * DAYS * VTTS
unfallnutzen(p) = (p.unf / YEARS) * UNFALLKOSTEN_MEAN * RED
laermnutzen(p)  = p.fass_igw * VAL_FASS * NSDI * DB * CAP
nutzen(p)       = unfallnutzen(p) + laermnutzen(p)
knv(p)          = nutzen(p) / zeitkosten(p)          # 0 falls Zeitkosten 0
```

**Eignungszonen (datengetrieben, Terzile):** über die VO-Abschnitte mit relevantem Verkehr (`fahrleistung ≥ 2000` Fz-km/Tag) werden die KNV-Terzile gebildet: `ZONE_T1 ≈ 0.066` (untere Grenze), `ZONE_T2 ≈ 0.113` (obere Grenze). `knv_cat(v)` = „hoch" ab T2, „mittel" ab T1, sonst „gering". Absolute Referenz wäre KNV = 1 (Nutzen = Kosten); **kein Abschnitt und keine Gemeinde erreicht 1,0 im rein monetären Szenario.**

**Intensität je km (skaleninvariant):** `zeitkosten(p)/p.km` gegen `nutzen(p)/p.km`; das Verhältnis (KNV) bleibt unverändert, macht aber Gemeinden unabhängig von ihrer Grösse vergleichbar (Grafikserie G16b).

### 3.2 Massnahmeneignung (Sicherheits- und Lärmnutzen), Modul `suit.py`

```
nutzen_score(p) = p.unf_km_jahr + p.fass_igw / 50
Kategorie: hoch ab 1.5, mittel ab 0.6, sonst gering
```

Farbskala bewusst sequenziell grün (nicht wertend rot), da neutrales Abstimmungsdokument: `CAT_FILL = {hoch:#0f7a54, mittel:#63c39b, gering:#d2e2da}`.

### 3.3 Unfalldichte-Zonen

Blaue, sequenzielle Bänder je 1 Unfall pro km und Jahr (bewusst neutral, nicht Ampel-rot/grün, da neutrales Dokument und Kollision mit der grünen Eignungsskala vermieden). Rote gestrichelte Linie = **kantonaler Median 0,75 Unfälle pro km und Jahr** über die VO-Abschnitte. Der Schweizer Median ist aus den Daten **nicht ableitbar** (Unfall-CSV ohne Innerorts-Flag und ohne Streckenlängen), deshalb nicht ausgewiesen.

---

## 4. Methodik Strang B: Infrastruktur-Nähe / «kurze Abschnitte»

Modul `map_lib.py` (Kartenbasis + Renderer), Treiber `build_infra_maps.py`.

**Betroffene Strassen je Gemeinde:** VO-Strassen aus `roads_fkt` (überregional + regional), verschnitten mit der Innerorts-Fläche (`baugebiet == "ja"`) der jeweiligen Gemeinde. Ergebnis: **43,9 km in 17 Gemeinden** (Zuordnung räumlich via STRtree, löst auch `gemeinde = None`-Segmente).

**Infrastruktur (4 Gruppen)** aus `infra_SH_v2.gpkg` (siehe Abschnitt 5): `schule`, `kindergarten`, `altersheim` (= Pflegeheim), `sozial` (weitere Sozialeinrichtungen). Farbcodierung je Gruppe: Schule Orange `#d95f0e` (Quadrat), Kindergarten Grün `#1b9e77` (Dreieck), Alters-/Pflegeheim Violett `#6a51a3` (Kreis), weitere Sozialeinrichtung Blau `#2166ac` (Raute).

**Umkreise (Puffer, Luftlinie):** 100 m, 300 m, 500 m je Gruppe, zunehmend blasser (Fill-Opazität 0.17/0.09/0.05; 100-m-Ring zusätzlich mit dünner Umrisslinie).

**Kandidaten „kurzer Abschnitt":** betroffene Strasse innerhalb **100 m** (eng, kräftig rot `#e6194B`) bzw. innerhalb **300 m** (weiter, blass rosa `#f4a6ae`) einer Nutzung. Berechnet als Verschnitt der VO-Abschnitte mit der Vereinigung der Puffer aller Standorte.

**Kartenausschnitt:** auf betroffene Strassen + relevante Anlagen fokussiert (nicht auf die volle Innerorts-Fläche, da diese in einzelnen Gemeinden weit gestreute Exklaven hat und den Ausschnitt sonst verzerrt). Anlagen im Ausschnitt = innerhalb ~560 m der betroffenen Strassen.

**Benennung der Beispiel-Abschnitte:** Kandidatensegmente werden über den nächsten `netzbelastung`-Strassennamen (≤ 45 m) benannt und nach Länge sortiert („direkte Beispiele").

---

## 5. Infrastruktur-GeoPackage `infra_SH_v2.gpkg` (Nutzer-Upload, Version 2)

Alle Layer EPSG:2056. Verwendete Punktlayer und Zuordnung zu den 4 Gruppen:

- `schulen` (91) → **schule** (inkl. Berufs-/Fachschule, Musikschule)
- `kindergaerten` (77) → **kindergarten** (inkl. Kindertagesstätte/Hort)
- `pflegeheime` (30) → **altersheim** (inkl. Wohngruppe, betreutes Wohnen)
- `unklar_sozialeinrichtungen` (15) → **sozial** (betreutes Wohnen, Wohngruppen; Kategorie im Layer leer)

**Summe 213 Standorte.** Kernfelder je Punkt: `kategorie`, `unterkategorie`, `einstufung` (eindeutig/wahrscheinlich), `name`/`bezeichnung`, `gemeinde`, `adresse`, `e_lv95`, `n_lv95`. Weitere Layer im GeoPackage: `alle_standorte` (198 = ohne sozial), `areale_*` (nach Sammelstandort aggregiert), `nebengebaeude` (4, nicht verwendet, um Doppelzählung zu vermeiden), `gemeindegrenzen` (26), `kantonsgrenze` (1).

Version 1 des Uploads (`..._2056.gpkg`) hatte 189 Standorte (91/70/28) und die sozialen Einrichtungen noch nicht in `pflegeheime` integriert; v2 ersetzt v1.

---

## 6. Zentrale Ergebnisse (Kennzahlen)

**Betroffenheit / Netz:**
- rund **80,4 km** Kantonsstrassen innerorts insgesamt (von 227 km Netz); 83 % höchstens 6 m breit.
- **43,9 km** davon sind **verkehrsorientiert (betroffen)**, verteilt auf 17 Gemeinden. Grösste: Schaffhausen 15,1 km, Stein am Rhein 5,4 km, Neuhausen am Rheinfall 4,5 km, Thayngen 3,5 km.
- 1'189 Personenschaden-Unfälle 2011–2025 auf diesen Strassen; rund 40 % betreffen Fussgänger oder Velofahrer. Unfalldichte folgt der Verkehrsmenge, nicht der Enge der Strasse.
- 1'816 Fassaden über dem Lärm-Immissionsgrenzwert, stark auf Schaffhausen konzentriert.

**Wirtschaftlichkeit (Szenario flächendeckend Tempo 30):**
- Zeitkosten rund **31 Mio. CHF/Jahr** gegen monetarisierte Nutzen rund **2,9 Mio. CHF/Jahr**.
- KNV bleibt für jeden Abschnitt und jede Gemeinde **unter 1**. Aussagekräftig ist die relative Reihung: gezielte Massnahmen an stark belasteten Abschnitten schneiden deutlich besser ab als eine flächendeckende Lösung.
- Konzentration des Nutzens auf wenige Achsen: in Schaffhausen Bachstrasse, Hochstrasse, Mühlenstrasse; dazu Neuhausen am Rheinfall und Stein am Rhein.

**Infrastruktur-Nähe / «kurze Abschnitte» (Datensatz 213 Standorte):**
- Anteil des betroffenen Netzes innerhalb einer sensiblen Nutzung: **≤ 100 m: 5,7 km (13 %)**, **≤ 300 m: 24,6 km (56 %)**, **≤ 500 m: 32,1 km (73 %)**.
- Je Gruppe (≤ 100 m): Schulen 2,57 km, Kindergärten 2,30 km, Alters-/Pflegeheime 1,00 km, weitere Sozialeinrichtungen 0,92 km.
- Spannweite je Gemeinde (≤ 100 m) von 0 % (Buch, Trasadingen, Hemishofen, Beringen, Rüdlingen; Durchfahrt hält Abstand) bis rund einem Drittel (Bargen, Ramsen); bei 300 m bis über 90 %.
- **Kernaussage für die Definition:** Ein reiner Umkreis ist grobkörnig. 100 m Umkreis entsprechen entlang der Strasse bis rund 200 m Fahrbahn je Anlage (300 m → bis ~600 m); auf anlagendichten Achsen summiert sich das (Schaffhausen Bachstrasse ~560 m schon bei ≤ 100 m). Für eine wirklich enge Fassung des Passus bieten sich an: Beschränkung auf die tatsächliche Strassenfront/Querung statt Kreisumkreis, eine Längenobergrenze je Abschnitt (z. B. 50–150 m), Kopplung mit einem Sicherheits- oder Querungskriterium.

---

## 7. Gelieferte Dateien (liegen beim Nutzer, aus früheren Lieferungen)

Diese Pakete wurden im ursprünglichen Chat via Dateilieferung übergeben und enthalten Daten und Ergebnisse. Für die Fortführung im anderen Projekt genügt es, sie dort hochzuladen.

**Strang A:**
- `Verkehrsflussinitiative_SH_komplett.zip` (Master): `Bericht_Verkehrsflussinitiative_SH.pdf` (34 Seiten, mit Zusammenfassung und Methodik-/Quellen-Fussnoten je Kapitel), `Datengrundlage_Verkehrsflussinitiative_SH.xlsx` (Blätter u. a. Gemeinden, Wirtschaftlichkeit, Kennwerte, Methodik, Ortsdurchfahrten, Buslinien, Abschnitte inkl. KNV-Spalte, Gemeinde-KNV), `Projectbrief_...md`, `Grafiken/` (G1–G12, G15, G16 Streuung, G17) und `Grafiken/Gemeinden/` (G14 ×8, G16b ×8), `Daten/per_abschnitt.json`.
- `Grafiken_Abschnitte.zip` (ergänzende Einzelgrafiken).

**Strang B:**
- `Karten_Infrastruktur_kurze_Abschnitte_SH.zip`: `Karten_Infrastruktur_kurze_Abschnitte_SH.pdf` (20 Seiten: Deckblatt mit Definitionsanalyse, Übersichtstabelle 100/300/500 m, 17 Gemeindekarten mit benannten Beispielen, Hinweise), `Auswertung_Infrastruktur_kurze_Abschnitte_SH.xlsx` (Blätter Uebersicht, Nach_Gruppe, Kandidaten_Beispiele), `kandidaten_kurze_abschnitte.geojson` (Kandidatenlinien mit `radius_m` 100/300, LV95), `Karten_Gemeinden/` (17 Karten je PNG und SVG), `LIESMICH.txt`.

**Nutzer-Uploads (Rohdaten, beim Nutzer):** die beiden Infrastruktur-GeoPackages (v1 `..._2056.gpkg`, v2 `..._LV95.gpkg`) und der Strassenrichtplan-ZIP.

---

## 8. Skripte (rekonstruiert unter `Skripte/`)

- `knv.py` – KNV-Wirtschaftlichkeitsmodell (Abschnitt 3.1), importiert von den Wirtschaftlichkeits-Grafiken und dem xlsx.
- `suit.py` – Massnahmeneignung/Nutzen-Score (Abschnitt 3.2).
- `map_lib.py` – Kartenbasis (VO-Strassen ∩ Innerorts je Gemeinde) und SVG-Renderer für die Infrastruktur-Karten (Puffer 100/300/500, Kandidaten-Stufen, Legende, Statistik).
- `build_infra_maps.py` – rendert die 17 Karten, benennt Kandidaten, schreibt `infra_results.json` und `kandidaten_kurze_abschnitte.geojson`.
- `build_infra_pdf.py` – 20-seitiges Karten-PDF (reportlab).
- `build_infra_xlsx.py` – Auswertungs-Excel (openpyxl), 3 Blätter.
- `report_notes.py` – Methodik-/Quellen-Fussnoten je Kapitel für den Hauptbericht.
- `build_g12_prio.py`, `build_gemeinde_nk.py` (G16b), `build_g16_scatter.py`, `build_g17_gemeinde_knv.py` – Grafik-Builder Strang A (soweit rekonstruiert).

**Wichtige benötigte Datendateien, die die Skripte erwarten** (im selben Ordner): `roads_fkt.geojson`, `baugebiet.geojson`, `netzbelastung.geojson`, `per_abschnitt.json`, `master_gemeinde.json`, `facilities.json` (aus dem GeoPackage extrahiert, 4 Gruppen), `infra_results.json`. `facilities.json` je Eintrag: `{cat, name, gem, x, y}` in LV95; `cat ∈ {schule, kindergarten, altersheim, sozial}`.

**Abhängigkeiten (pip):** `shapely`, `fiona`, `cairosvg`, `reportlab`, `openpyxl`, `pypdf`, `Pillow`. Unicode-Umlaute in Dateien mit `io.open(..., encoding='utf-8')` schreiben.

---

## 9. Reproduktion / wie fortfahren

1. Rohdaten bereitstellen: entweder aus `Verkehrsflussinitiative_SH_komplett.zip` (`Daten/per_abschnitt.json`) und den Nutzer-GeoPackages, oder die geo.sh.ch-Layer (Kantonsstrassen/Richtplan, Baugebiet, Netzbelastung, Lärmkataster) neu beziehen. **Achtung:** In der Anthropic-Cloud-Sandbox sind `geo.sh.ch` und OpenStreetMap/Overpass über den WebFetch-Proxy gesperrt (HTTP 403), und ein Umgehen per curl/Python ist nicht erlaubt. Rohdaten daher als Datei bereitstellen (Upload) oder, falls ein Rechner verbunden ist, über dessen Netz beziehen.
2. `facilities.json` aus dem GeoPackage erzeugen (Layer `schulen`, `kindergaerten`, `pflegeheime`, `unklar_sozialeinrichtungen`; Geometrie-Koordinaten als `x`/`y`).
3. `python3 build_infra_maps.py` → Karten + `infra_results.json` + GeoJSON; danach `build_infra_pdf.py` und `build_infra_xlsx.py`.

**Naheliegende nächste Schritte / offene Punkte:**
- Engere Schwelle für „kurz" testen (z. B. 50 m oder eine reine Frontlänge/Querung statt Kreisumkreis); Längenobergrenze je Abschnitt.
- Umkreise als Netz-/Fusswegdistanz statt Luftlinie.
- Innerorts über Ortstafel-Layer statt Baugebiet verfeinern.
- Einzelne Standorte prüfen (ein Teil ist als „wahrscheinlich" eingestuft).

---

## 10. Quellen

geo.sh.ch (Amt für Geoinformation Kanton Schaffhausen): Strassenrichtplan/Funktionsklassen, Netzbelastung/DTV, Baugebiet, Lärmbelastungskataster. swissTLM3D (swisstopo, geo.admin.ch): Fahrbahnbreiten. ASTRA (data.geo.admin.ch): Strassenverkehrsunfälle mit Personenschaden 2011–2025. OpenStreetMap-Mitwirkende: Buslinienführung, Infrastruktur-Standorte (im Nutzer-GeoPackage, teils kantonal ergänzt). Kennwerte: ARE/VSS (Zeitwert, SN 641 822a), bfu/Ecoplan (Unfallkosten), ASTRA FB 1663 (Reisezeitwirkung), BAFU/ZKB/Baranzini (Lärm/Wertminderung). Verfahren analog NISTRA (ASTRA). VSS-Normen für Geometrie (SN 640 201, 640 070, 640 273a). Signalisationsrecht: SSV (Art. 22a, 108), UVEK-Verordnung SR 741.213.3; Blaulicht Art. 100 Ziff. 4 SVG.

## 11. Vorbehalte

Näherungswerte für die politische Diskussion, keine amtliche Statistik. Umkreise sind Luftlinien um den Standort, keine Netz-/Fusswegdistanzen. KNV rein monetär, ohne nicht-monetäre Nutzen; Zeitkosten in dichten Stadtabschnitten eher überschätzt. Innerorts über Baugebiet abgegrenzt, nicht über Ortstafeln. Rundungsdifferenzen möglich.

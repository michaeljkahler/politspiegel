#!/usr/bin/env python3
"""Prueft aufbereitete Geodaten und gibt sie fuer die Seite frei.

Aufruf aus der Projektwurzel:
    python3 abstimmungsspiegel/bausteine/geo_freigeben.py 2026-09-27-verkehrsfluss

Liest    abstimmungsspiegel/abstimmungen/<slug>/geo/02_aufbereitet/*.geojson
Schreibt abstimmungsspiegel/abstimmungen/<slug>/geo/03_freigegeben/*.geojson
         abstimmungsspiegel/abstimmungen/<slug>/geo/PRUEFBERICHT.md

Warum eine eigene Stufe zwischen Aufbereitung und Einbindung: In die Seite darf
nur, was geprueft ist. Sonst wandert ein Koordinatenfehler oder eine kaputte
Geometrie unbemerkt in die Karte, und dort sieht sie aus wie eine Aussage. Die
Stufe hier macht drei Dinge und nichts weiter:

  1. Sie prueft. Liegt jede Koordinate im Rahmen des Kantons? Ist jede Geometrie
     vollstaendig? Fehlen Eigenschaften, die die Karte braucht?
  2. Sie kuerzt die Koordinaten auf fuenf Nachkommastellen, rund einen Meter.
     Mehr traegt keine Webkarte, und der Rest ist nur Dateigroesse.
  3. Sie schreibt einen Bericht, der Herkunft, Abrufdatum, Objektzahl und die
     Aenderung der Dateigroesse festhaelt.

Faellt eine Pruefung durch, wird die Ebene NICHT freigegeben. Die Datei bleibt
in 02_aufbereitet liegen, der Bericht nennt den Grund, und der Kartenbaustein
findet die Ebene nicht und laesst sie weg. Lieber eine Ebene fehlt, als dass
eine falsche erscheint.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent.parent
NACHKOMMA = 5          # rund 1 m, mehr traegt keine Webkarte
GRENZE_KB = 400        # ab hier ein Hinweis im Bericht, keine Sperre

# Rahmen des Kantons Schaffhausen samt Umgebung, grosszuegig gefasst.
# Wer hier herausfaellt, hat mit hoher Wahrscheinlichkeit ein Bezugssystem
# verwechselt: LV95 liefert Werte um 2 690 000 und 1 285 000, nicht um 8 und 47.
RAHMEN = {"lon": (8.30, 9.05), "lat": (47.45, 47.95)}

# Was die Seite je Ebene braucht. Fehlt eine Eigenschaft, wird nicht
# freigegeben, denn die Karte wuerde leere Beschriftungen zeigen.
ERWARTET = {
    "kandidaten_wgs84":        {"pflicht": {"g", "r"},  "geometrie": {"LineString"}},
    "haltestellen_bus_wgs84":  {"pflicht": {"n"},       "geometrie": {"Point"}},
    "busnetz_wgs84":           {"pflicht": set(),       "geometrie": {"LineString"}},
    "kantonsstrassen_vo_wgs84": {"pflicht": {"k"},      "geometrie": {"LineString"}},
    "geltung_initiative":       {"pflicht": {"strasse", "gemeinde", "fkt", "tempo", "laenge_m", "bus"},
                                 "geometrie": {"LineString", "MultiLineString"}},
    "geltung_gegenvorschlag":   {"pflicht": {"strasse", "gemeinde", "fkt", "tempo", "laenge_m", "bus"},
                                 "geometrie": {"LineString", "MultiLineString"}},
}

# Woher die Ebene stammt. Steht im Bericht und in der Legende der Karte, damit
# niemand raten muss, wessen Aussage eine Linie ist.
HERKUNFT = {
    "kandidaten_wgs84": (
        "Eigene Auswertung aus der Uebergabe vom Juli 2026: Kantonsstrassen "
        "innerorts im Umkreis von Schule, Kindergarten oder Heim.",
        "01_roh/kandidaten_kurze_abschnitte.geojson (LV95)"),
    "haltestellen_bus_wgs84": (
        "Bundesamt fuer Verkehr, Ebene ch.bav.haltestellen-oev, ueber "
        "map.geo.admin.ch abgerufen.", "01_roh/haltestellen_bus_lv95.json"),
    "busnetz_wgs84": (
        "OpenStreetMap, Buslinien im Kanton, ueber die Overpass-API abgerufen.",
        "01_roh/busnetz_roh.json"),
    "kantonsstrassen_vo_wgs84": (
        "Kanton Schaffhausen, Kantonaler Strassenrichtplan, Funktionszuweisung "
        "verkehrsorientiert, ueber wfs.geo.sh.ch abgerufen.",
        "01_roh/kantonsstrassen_vo_roh.json"),
    "geltung_initiative": (
        "Eigene Rechnung (geo/skripte/geltungsbereich.py): Kantonsstrassen innerorts, "
        "die vom oeffentlichen Verkehr genutzt werden. Stuecke des kantonalen "
        "Laermkatasters mit Tempo bis 50, auf Kantonsstrassenachsen, mit Buslinie "
        "(OpenStreetMap) oder Haltestelle (BAV). Attribute je Stueck.",
        "01_roh/laerm_strassenachse_roh.xml, kantonsstrassen_alle_roh.xml, busnetz_linien_roh.json"),
    "geltung_gegenvorschlag": (
        "Eigene Rechnung (geo/skripte/geltungsbereich.py): verkehrsorientierte "
        "Kantonsstrassen innerorts (ueberregional, regional nach Feld typ der "
        "Achsen), Stuecke des Laermkatasters mit Tempo bis 50. Attribute je Stueck.",
        "01_roh/laerm_strassenachse_roh.xml, kantonsstrassen_alle_roh.xml"),
}


def punkte(c):
    """Alle Koordinatenpaare einer beliebig tief verschachtelten Geometrie."""
    if not isinstance(c, list):
        return
    if c and isinstance(c[0], (int, float)):
        yield c
        return
    for y in c:
        yield from punkte(y)


def kuerzen(c):
    """Koordinaten auf NACHKOMMA Stellen, Struktur unveraendert."""
    if isinstance(c, list):
        if c and isinstance(c[0], (int, float)):
            return [round(float(v), NACHKOMMA) for v in c]
        return [kuerzen(y) for y in c]
    return c


def pruefen(name, d):
    """Gibt eine Liste von Beanstandungen zurueck. Leer heisst bestanden."""
    fehler, hinweise = [], []
    fs = d.get("features")
    if not isinstance(fs, list) or not fs:
        return ["keine Objekte enthalten"], []

    regel = ERWARTET.get(name, {})
    erlaubt = regel.get("geometrie")
    pflicht = regel.get("pflicht", set())

    aussen = leer = 0
    typen, fehlend = set(), set()
    for x in fs:
        g = x.get("geometry") or {}
        typen.add(g.get("type"))
        ps = list(punkte(g.get("coordinates")))
        if not ps:
            leer += 1
            continue
        for lon, lat, *_ in ps:
            if not (RAHMEN["lon"][0] <= lon <= RAHMEN["lon"][1]
                    and RAHMEN["lat"][0] <= lat <= RAHMEN["lat"][1]):
                aussen += 1
                break
        eig = x.get("properties") or {}
        fehlend |= {k for k in pflicht if k not in eig or eig[k] in (None, "")}

    if leer:
        fehler.append(f"{leer} Objekte ohne Koordinaten")
    if aussen:
        fehler.append(f"{aussen} Objekte ausserhalb des Kantonsrahmens, "
                      f"Bezugssystem pruefen")
    if fehlend:
        fehler.append("Pflichteigenschaft fehlt: " + ", ".join(sorted(fehlend)))
    if erlaubt and not typen <= erlaubt:
        fehler.append(f"unerwarteter Geometrietyp: "
                      f"{', '.join(str(t) for t in sorted(typen - erlaubt))}")
    if name not in ERWARTET:
        hinweise.append("keine Erwartung hinterlegt, nur Rahmen und Geometrie geprueft")
    return fehler, hinweise


def freigeben(slug: str) -> int:
    basis = WURZEL / "abstimmungsspiegel" / "abstimmungen" / slug / "geo"
    quelle, ziel = basis / "02_aufbereitet", basis / "03_freigegeben"
    if not quelle.is_dir():
        print(f"nicht gefunden: {quelle}", file=sys.stderr)
        return 1
    ziel.mkdir(parents=True, exist_ok=True)

    zeilen, ok, weg = [], 0, 0
    for f in sorted(quelle.glob("*.geojson")):
        name = f.stem
        d = json.loads(f.read_text(encoding="utf-8"))
        fehler, hinweise = pruefen(name, d)
        vorher = f.stat().st_size
        anzahl = len(d.get("features", []))
        beschrieb, roh = HERKUNFT.get(name, ("nicht hinterlegt", "unbekannt"))

        if fehler:
            weg += 1
            (ziel / f.name).unlink(missing_ok=True)
            zeilen.append((name, anzahl, vorher, None, "**nicht freigegeben**",
                           "; ".join(fehler), beschrieb, roh))
            continue

        for x in d["features"]:
            g = x.get("geometry")
            if g:
                g["coordinates"] = kuerzen(g.get("coordinates"))
        knapp = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
        (ziel / f.name).write_text(knapp, encoding="utf-8")
        nachher = (ziel / f.name).stat().st_size
        ok += 1
        note = "freigegeben"
        if nachher / 1024 > GRENZE_KB:
            note += f", gross ({nachher/1024:.0f} kB)"
        zeilen.append((name, anzahl, vorher, nachher, note,
                       "; ".join(hinweise) or "keine", beschrieb, roh))

    bericht = bauen_bericht(slug, zeilen, ok, weg)
    (basis / "PRUEFBERICHT.md").write_text(bericht, encoding="utf-8")
    print(f"{ok} Ebenen freigegeben, {weg} zurueckgehalten")
    print(f"Bericht: {basis / 'PRUEFBERICHT.md'}")
    return 0


def bauen_bericht(slug, zeilen, ok, weg) -> str:
    t = [f"# Pruefbericht Geodaten · {slug}", "",
         f"Erzeugt am {date.today():%d.%m.%Y} von "
         f"`abstimmungsspiegel/bausteine/geo_freigeben.py`. Nicht von Hand aendern, "
         f"die Datei wird bei jedem Lauf neu geschrieben.", "",
         f"**{ok} Ebenen freigegeben"
         + (f", {weg} zurueckgehalten." if weg else ", keine zurueckgehalten.")
         + "**", "",
         "Freigegeben heisst: jede Koordinate liegt im Rahmen des Kantons, jede "
         "Geometrie ist vollstaendig, jede Eigenschaft, welche die Karte "
         "braucht, ist vorhanden. Zurueckgehalten heisst: die Ebene erscheint "
         "nicht auf der Seite, der Grund steht unten.", "",
         "## Ebenen", "",
         "| Ebene | Objekte | vorher | freigegeben | Stand | Anmerkung |",
         "|---|---|---|---|---|---|"]
    for name, n, vor, nach, note, anm, _, _ in zeilen:
        g = f"{nach/1024:.0f} kB" if nach else "—"
        t.append(f"| `{name}` | {n} | {vor/1024:.0f} kB | {g} | {note} | {anm} |")
    t += ["", "## Herkunft je Ebene", ""]
    for name, n, _, nach, note, _, beschrieb, roh in zeilen:
        t += [f"### `{name}`", "", beschrieb, "",
              f"- Rohdaten: `{roh}`",
              f"- Objekte: {n}",
              f"- Stand: {note}", ""]
    t += ["## Was gepruefte Koordinaten heisst", "",
          f"Die Koordinaten werden auf {NACHKOMMA} Nachkommastellen gekuerzt, "
          f"das sind rund {round(111320 / 10**NACHKOMMA, 1)} Meter in "
          f"Nord-Sued-Richtung. Genauer traegt keine Webkarte, und jede weitere "
          f"Stelle kostet nur Dateigroesse. Wer die volle Genauigkeit braucht, "
          f"nimmt `02_aufbereitet` oder die Rohdaten in `01_roh`.", "",
          f"Der Rahmen, gegen den geprueft wird: Laengengrad "
          f"{RAHMEN['lon'][0]} bis {RAHMEN['lon'][1]}, Breitengrad "
          f"{RAHMEN['lat'][0]} bis {RAHMEN['lat'][1]}. Er ist absichtlich "
          f"grosszuegig; er soll nicht den Kanton abgrenzen, sondern eine "
          f"Verwechslung des Bezugssystems auffangen. LV95 liefert Werte um "
          f"2 690 000 und 1 285 000 und faellt sofort auf.", ""]
    return "\n".join(t)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__.split("Warum")[0].strip(), file=sys.stderr)
        sys.exit(2)
    sys.exit(freigeben(sys.argv[1]))

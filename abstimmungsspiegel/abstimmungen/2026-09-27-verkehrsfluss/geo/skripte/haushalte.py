#!/usr/bin/env python3
"""Anwohner und Laermfassaden entlang der betroffenen Strassen.

Aufruf aus der Projektwurzel:
    python3 abstimmungsspiegel/abstimmungen/2026-09-27-verkehrsfluss/geo/skripte/haushalte.py

Liest  geo/03_freigegeben/geltung_initiative.geojson, geltung_gegenvorschlag.geojson
Holt   wfs.geo.sh.ch   sh.verkehr.laermbelastung.haupt_uebrigestrassen.punkt.tag
                       Fassadenpunkte des Laermkatasters mit Belastung Tag (dB(A)),
                       je Gebaeude und Stockwerk, Referenz Sanierungshorizont 2043
       api3.geo.admin.ch  ch.bfs.volkszaehlung-bevoelkerungsstatistik_einwohner
                       STATPOP, Einwohner je Hektare, Stand 2024
Legt   geo/01_roh/laerm_fassadenpunkte_tag_roh.xml   (21 MB, nicht im Repository)
       geo/01_roh/statpop_2024_hektaren.json         Einwohner je Hektare im Suchraum
       geo/02_aufbereitet/haushalte.json             Kennzahlen je Vorlage und Gemeinde
       geo/02_aufbereitet/anwohner_hektaren.geojson  die Hektaren, fuer die Karte

Was gezaehlt wird, je Vorlage (Initiative, Gegenvorschlag, mindestens eine):

1. Anwohner: Einwohner der Hektaren, die eine betroffene Strasse beruehren
   (Hektarraster 100 x 100 m; die Strasse muss die Zelle schneiden, nicht
   nur ein Puffer). Das ist die Bevoelkerung in unmittelbarer Strassennaehe,
   nach oben grob, weil eine Hektare auch Wohnungen in zweiter Reihe enthaelt.
2. Fassaden ueber dem Grenzwert: Fassadenpunkte des Laermkatasters mit
   Belastung am Tag ueber 65 dB(A), hoechstens 25 m von einer betroffenen
   Strasse. 65 dB(A) ist der Immissionsgrenzwert am Tag der
   Empfindlichkeitsstufe III (Misch- und Kernzonen, LSV Anhang 3); fuer reine
   Wohnzonen (ES II) gilt 60 dB(A), diese Zahl steht daneben. Gezaehlt werden
   Punkte (je Stockwerk) und Gebaeude (Punkte am selben Ort).
3. Anwohner an Fassaden ueber dem Grenzwert: Einwohner der Hektaren, die
   mindestens einen solchen Fassadenpunkt enthalten. Das ist eine Obergrenze,
   weil die ganze Hektare zaehlt.

Haushalte: STATPOP je Hektare liefert die Zahl der Personen; Haushalte
ergeben sich mit der Haushaltsgroesse des Kantons Schaffhausen (2,1 Personen,
BFS STATPOP 2023). Beide Zahlen stehen in den Kennzahlen.
"""

from __future__ import annotations

import datetime
import json
import math
import re
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import LineString, Point, box, mapping, shape
from shapely.ops import transform, unary_union
from shapely.strtree import STRtree

VORLAGE = Path(__file__).resolve().parent.parent.parent
ROH = VORLAGE / "geo" / "01_roh"
FERTIG = VORLAGE / "geo" / "02_aufbereitet"
FREI = VORLAGE / "geo" / "03_freigegeben"

WFS = "https://wfs.geo.sh.ch/wfs"
API = "https://api3.geo.admin.ch/rest/services/api/MapServer/identify"
STATPOP_EBENE = "ch.bfs.volkszaehlung-bevoelkerungsstatistik_einwohner"
STATPOP_JAHR = 2024
HAUSHALT = 2.1            # Personen je Haushalt, Kanton Schaffhausen, BFS STATPOP 2023
FASSADE_FANG = 25.0       # m, Fassadenpunkt zur betroffenen Strasse
IGW_ES3 = 65.0            # dB(A) Tag, ES III
IGW_ES2 = 60.0            # dB(A) Tag, ES II
KACHEL = 1000             # m, Kachel fuer die STATPOP-Abfrage (max. 100 Hektaren, Limit 200)

nach_lv95 = Transformer.from_crs(4326, 2056, always_xy=True).transform
nach_wgs = Transformer.from_crs(2056, 4326, always_xy=True).transform


def bloecke(text):
    return re.findall(r"<gml:featureMember>(.*?)</gml:featureMember>", text, re.S)


def feld(blk, name):
    m = re.search(rf"<qgs:{name}>([^<]*)</qgs:{name}>", blk)
    return m.group(1).strip() if m else ""


def punkt(blk):
    m = re.search(r"<pos[^>]*>([^<]+)</pos>", blk)
    if not m:
        return None
    z = [float(v) for v in m.group(1).split()]
    return (z[0], z[1])


def fassaden_holen(ziel: Path):
    if not (ziel.exists() and ziel.stat().st_size > 100000):
        q = urllib.parse.urlencode({"SERVICE": "WFS", "VERSION": "1.1.0", "REQUEST": "GetFeature",
                                    "TYPENAME": "sh.verkehr.laermbelastung.haupt_uebrigestrassen.punkt.tag",
                                    "SRSNAME": "EPSG:2056"})
        print("  hole Fassadenpunkte …")
        with urllib.request.urlopen(f"{WFS}?{q}", timeout=600) as r:
            ziel.write_bytes(r.read())
    t = ziel.read_text(encoding="utf-8", errors="replace")
    aus = []
    for b in bloecke(t):
        p = punkt(b)
        if not p:
            continue
        try:
            tag = float(feld(b, "laermbelastung_tag"))
        except ValueError:
            continue
        aus.append((Point(p), tag, feld(b, "stockwerk")))
    print(f"  {len(aus)} Fassadenpunkte")
    return aus


def geltung_lesen(name):
    d = json.loads((FREI / name).read_text(encoding="utf-8"))
    return [(transform(nach_lv95, shape(f["geometry"])), f["properties"]) for f in d["features"]]


def statpop_holen(kacheln, ziel: Path) -> dict:
    """Einwohner je Hektare (Schluessel «x_y» der Suedwestecke) fuer die
    gegebenen Kacheln. Zwischenstand in ziel, damit ein abgebrochener Lauf
    weitermacht; eine Kachel ohne Einwohner steht als leere Liste drin."""
    cache = json.loads(ziel.read_text(encoding="utf-8")) if ziel.exists() else {"jahr": STATPOP_JAHR, "kacheln": {}}
    if cache.get("jahr") != STATPOP_JAHR:
        cache = {"jahr": STATPOP_JAHR, "kacheln": {}}
    for i, (x0, y0) in enumerate(kacheln):
        k = f"{x0}_{y0}"
        if k in cache["kacheln"]:
            continue
        q = urllib.parse.urlencode({
            "geometry": f"{x0},{y0},{x0 + KACHEL},{y0 + KACHEL}", "geometryType": "esriGeometryEnvelope",
            "layers": f"all:{STATPOP_EBENE}", "tolerance": 0, "sr": 2056, "returnGeometry": "true",
            "lang": "de", "timeInstant": STATPOP_JAHR, "limit": 500})
        with urllib.request.urlopen(f"{API}?{q}", timeout=120) as r:
            d = json.loads(r.read().decode("utf-8"))
        zellen = []
        for res in d.get("results", []):
            a = res.get("attributes") or {}
            if a.get("i_year") != STATPOP_JAHR:
                continue
            bb = res.get("bbox") or []
            if len(bb) == 4:
                zellen.append([int(bb[0]), int(bb[1]), int(a.get("number") or 0)])
        cache["kacheln"][k] = zellen
        if (i + 1) % 10 == 0 or i + 1 == len(kacheln):
            ziel.write_text(json.dumps(cache, separators=(",", ":")), encoding="utf-8")
            print(f"  STATPOP: {i + 1} von {len(kacheln)} Kacheln", flush=True)
    hekt = {}
    for zellen in cache["kacheln"].values():
        for x, y, n in zellen:
            hekt[(x, y)] = n
    return hekt


def main() -> int:
    print("Betroffene Strassen")
    ini = geltung_lesen("geltung_initiative.geojson")
    gv = geltung_lesen("geltung_gegenvorschlag.geojson")
    netze = {"initiative": unary_union([g for g, _ in ini]),
             "gegenvorschlag": unary_union([g for g, _ in gv])}
    netze["eine"] = unary_union([netze["initiative"], netze["gegenvorschlag"]])
    gem_von = {}
    for g, p in ini + gv:
        gem_von[id(g)] = p.get("gemeinde", "")
    alle_st = [(g, p.get("gemeinde", "")) for g, p in ini + gv]
    st_baum = STRtree([g for g, _ in alle_st])

    def gemeinde_an(pt: Point) -> str:
        best, dist = "", 1e9
        for i in st_baum.query(pt.buffer(200)):
            d = alle_st[i][0].distance(pt)
            if d < dist:
                best, dist = alle_st[i][1], d
        return best

    for k, g in netze.items():
        print(f"  {k:14s} {g.length/1000:6.1f} km")

    print("\nFassadenpunkte")
    fass = fassaden_holen(ROH / "laerm_fassadenpunkte_tag_roh.xml")
    fass_baum = STRtree([p for p, _, _ in fass])
    naehe = {k: set() for k in netze}
    for k, netz in netze.items():
        for i in fass_baum.query(netz.buffer(FASSADE_FANG)):
            if fass[i][0].distance(netz) <= FASSADE_FANG:
                naehe[k].add(i)
    def fassaden_zahlen(idx):
        pkt65 = [i for i in idx if fass[i][1] > IGW_ES3]
        pkt60 = [i for i in idx if fass[i][1] > IGW_ES2]
        geb = lambda ids: len({(round(fass[i][0].x, 1), round(fass[i][0].y, 1)) for i in ids})
        return {"punkte": len(idx), "punkte_ueber_65": len(pkt65), "gebaeude_ueber_65": geb(pkt65),
                "punkte_ueber_60": len(pkt60), "gebaeude_ueber_60": geb(pkt60)}
    for k in netze:
        z = fassaden_zahlen(naehe[k])
        print(f"  {k:14s} {z['punkte']:5d} Punkte, ueber 65 dB: {z['punkte_ueber_65']} Punkte an "
              f"{z['gebaeude_ueber_65']} Gebaeuden, ueber 60 dB: {z['gebaeude_ueber_60']} Gebaeude")

    print("\nSTATPOP")
    suchraum = netze["eine"].buffer(60)
    b = suchraum.bounds
    kacheln = [(x, y) for x in range(int(b[0] // KACHEL * KACHEL), int(b[2]) + 1, KACHEL)
               for y in range(int(b[1] // KACHEL * KACHEL), int(b[3]) + 1, KACHEL)
               if box(x, y, x + KACHEL, y + KACHEL).intersects(suchraum)]
    print(f"  {len(kacheln)} Kacheln zu {KACHEL} m")
    hekt = statpop_holen(kacheln, ROH / f"statpop_{STATPOP_JAHR}_hektaren.json")
    print(f"  {len(hekt)} bewohnte Hektaren im Suchraum, {sum(hekt.values())} Einwohner")

    zellen = {xy: box(xy[0], xy[1], xy[0] + 100, xy[1] + 100) for xy in hekt}
    zellen_baum = STRtree(list(zellen.values()))
    zellen_keys = list(zellen.keys())

    def hektaren_an(netz):
        return {zellen_keys[i] for i in zellen_baum.query(netz) if zellen[zellen_keys[i]].intersects(netz)}

    ergebnis = {"gerechnet_am": datetime.date.today().isoformat(),
                "statpop_jahr": STATPOP_JAHR, "personen_je_haushalt": HAUSHALT,
                "fassade_fang_m": FASSADE_FANG, "igw_es3_db": IGW_ES3, "igw_es2_db": IGW_ES2,
                "vorlagen": {}, "je_gemeinde": {}}
    hekt_features = []
    for k, netz in netze.items():
        an = hektaren_an(netz)
        laut65 = set()
        for i in naehe[k]:
            if fass[i][1] > IGW_ES3:
                p = fass[i][0]
                xy = (int(p.x // 100 * 100), int(p.y // 100 * 100))
                if xy in an:
                    laut65.add(xy)
        ew = sum(hekt[xy] for xy in an)
        ew65 = sum(hekt[xy] for xy in laut65)
        fz = fassaden_zahlen(naehe[k])
        ergebnis["vorlagen"][k] = {
            "strassen_km": round(netz.length / 1000, 1),
            "hektaren": len(an), "anwohner": ew, "haushalte": round(ew / HAUSHALT),
            "hektaren_mit_fassade_ueber_65": len(laut65),
            "anwohner_an_fassaden_ueber_65": ew65, "haushalte_an_fassaden_ueber_65": round(ew65 / HAUSHALT),
            **fz,
        }
        print(f"  {k:14s} {len(an):4d} Hektaren, {ew:6d} Anwohner ({round(ew / HAUSHALT)} Haushalte); "
              f"an Fassaden ueber 65 dB: {ew65} Anwohner in {len(laut65)} Hektaren")
        if k == "eine":
            for xy in an:
                hekt_features.append({"type": "Feature", "properties": {
                    "einwohner": hekt[xy], "laut65": xy in laut65,
                    "initiative": xy in hektaren_an(netze["initiative"]),
                    "gegenvorschlag": xy in hektaren_an(netze["gegenvorschlag"])},
                    "geometry": mapping(transform(nach_wgs, zellen[xy]))})

    # je Gemeinde, fuer «eine»
    an = hektaren_an(netze["eine"])
    je = defaultdict(lambda: {"hektaren": 0, "anwohner": 0, "gebaeude_ueber_65": set(), "punkte_ueber_65": 0})
    for xy in an:
        gm = gemeinde_an(zellen[xy].centroid)
        je[gm]["hektaren"] += 1
        je[gm]["anwohner"] += hekt[xy]
    for i in naehe["eine"]:
        if fass[i][1] > IGW_ES3:
            gm = gemeinde_an(fass[i][0])
            je[gm]["punkte_ueber_65"] += 1
            je[gm]["gebaeude_ueber_65"].add((round(fass[i][0].x, 1), round(fass[i][0].y, 1)))
    ergebnis["je_gemeinde"] = {g: {"hektaren": v["hektaren"], "anwohner": v["anwohner"],
                                   "haushalte": round(v["anwohner"] / HAUSHALT),
                                   "punkte_ueber_65": v["punkte_ueber_65"],
                                   "gebaeude_ueber_65": len(v["gebaeude_ueber_65"])}
                               for g, v in sorted(je.items(), key=lambda x: -x[1]["anwohner"])}
    ergebnis["quellen"] = {
        "statpop": f"BFS, STATPOP {STATPOP_JAHR}, Einwohner je Hektare, ueber api3.geo.admin.ch ({STATPOP_EBENE})",
        "fassaden": "Kanton Schaffhausen, Laermbelastungskataster Strassenverkehr, Fassadenpunkte Tag, "
                    "Referenz Sanierungshorizont 2043, wfs.geo.sh.ch",
        "grenzwerte": "LSV Anhang 3: Immissionsgrenzwert Tag 65 dB(A) in ES III, 60 dB(A) in ES II",
        "haushaltsgroesse": "BFS, durchschnittliche Haushaltsgroesse Kanton Schaffhausen 2,1 Personen",
    }
    (FERTIG / "haushalte.json").write_text(json.dumps(ergebnis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (FERTIG / "anwohner_hektaren.geojson").write_text(json.dumps(
        {"type": "FeatureCollection", "features": hekt_features}, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8")
    print("\ngeschrieben: haushalte.json, anwohner_hektaren.geojson")
    return 0


if __name__ == "__main__":
    sys.exit(main())

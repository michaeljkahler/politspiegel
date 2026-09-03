#!/usr/bin/env python3
"""Rechnet die Geltungsbereiche von Initiative und Gegenvorschlag aus.

Aufruf aus der Projektwurzel:
    python3 abstimmungsspiegel/abstimmungen/2026-09-27-verkehrsfluss/geo/skripte/geltungsbereich.py

Holt   wfs.geo.sh.ch   sh.verkehr.individual.kantonsstrassen             Achsen mit Funktion, Nummer, Name
                       sh.verkehr.laermbelastung.haupt_uebrigestrassen.linie.strassenachse
                                                                         Strassenstuecke mit Strassenname,
                                                                         signalisiertem Tempo, DTV, Emission
                       sh.richtplan.strassenrichtplan.kanton.ortstafeln  Ortstafeln, Punkte
                       sh.nutzungsplanung.rechtsgueltig.baugebiet        Baugebiet und Gemeinde
       overpass-api.de Buslinien (Relationen route=bus) mit Liniennummer
Liest  geo/03_freigegeben/haltestellen_bus_wgs84.geojson                Bushaltestellen (BAV)
       geo/02_aufbereitet/per_abschnitt.json                             Unfaelle, Laermfassaden je Abschnitt
Legt   geo/01_roh/*_roh.xml, busnetz_linien_roh.json
       geo/02_aufbereitet/geltung_initiative.geojson
       geo/02_aufbereitet/geltung_gegenvorschlag.geojson
       geo/02_aufbereitet/geltungsbereich.json                           Kennzahlen und Pruefliste

Die beiden Vorlagen erfassen verschiedene Strassen:

    Initiative      Kantonsstrassen innerorts, die auch durch den
                    oeffentlichen Verkehr genutzt werden
    Gegenvorschlag  verkehrsorientierte Kantonsstrassen innerorts,
                    ohne Bedingung zum oeffentlichen Verkehr

Geometrische Grundlage sind die Strassenstuecke des Laermkatasters (981
Stuecke, im Mittel rund 280 m). Sie tragen Strassenname, signalisierte
Hoechstgeschwindigkeit, DTV und Emissionswert, und sie liegen auf der amtlichen
Achse. Ein Stueck ist Kantonsstrasse, wenn seine Mitte hoechstens 15 m von einer
Kantonsstrassenachse liegt; Funktion, Nummer und Achsenname kommen von dieser
Achse (Feld «typ»: ueberregional und regional sind verkehrsorientiert,
ueberlokal siedlungsorientiert, Nationalstrasse zaehlt nicht).

innerorts: signalisierte Hoechstgeschwindigkeit am Tag hoechstens 50 km/h, und
dazu eines von drei Merkmalen einer Siedlungslage: mindestens 10 % der Laenge
im Baugebiet (mit 30 m Puffer), eine Bushaltestelle in 150 m, eine Ortstafel in
250 m. Das zweite Kriterium trennt Ortsdurchfahrten von Ausserortsstrecken mit
Tempo 40 oder 50 (Randenstrasse, Im Gehren). Kontrollwerte: die Uebergabe vom
Juli 2026 kam mit dem Baugebiet allein auf 80,4 km innerorts und 43,9 km
verkehrsorientiert; diese Rechnung ergibt 78,0 und 43,1 km. Das Baugebiet
allein ist als Innerortsgrenze untauglich: Die Ebene deckt die Stadtkerne nicht
(Bahnhofstrasse, Hochstrasse, Fulachstrasse in Schaffhausen liegen zu 0 %
darin), und die Ortstafelebene ist mit 140 Punkten nicht vollstaendig.

Bus: Ein Stueck gilt als vom oeffentlichen Verkehr genutzt, wenn ein Teil davon
innerhalb von 20 m einer Buslinie aus OpenStreetMap liegt oder eine
BAV-Haltestelle hoechstens 50 m entfernt ist. Faehrt die Linie nur ueber einen
Teil des Stuecks, wird das Stueck fuer die Initiative auf diesen Teil
geschnitten; im Gegenvorschlag bleibt es ganz und traegt «Bus: teilweise». Der Puffer faengt den
Versatz zwischen amtlicher Achse und OSM-Linienfuehrung auf; wie stark das
Ergebnis daran haengt, steht als Empfindlichkeitsprobe in den Kennzahlen.

Attribute je Stueck: Nummer, Achse, Strassenname, Gemeinde, Funktion, Tempo,
DTV, Emissionswert Tag, Bus mit Liniennummern und Haltestellen in 30 m,
Laenge, und aus per_abschnitt.json Unfaelle 2011 bis 2025 und Fassaden ueber
dem Immissionsgrenzwert des benannten Abschnitts (Strassenname und Gemeinde).
"""

from __future__ import annotations

import datetime
import json
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import LineString, Point, Polygon, mapping, shape
from shapely.ops import transform, unary_union
from shapely.strtree import STRtree

VORLAGE = Path(__file__).resolve().parent.parent.parent
ROH = VORLAGE / "geo" / "01_roh"
FERTIG = VORLAGE / "geo" / "02_aufbereitet"
FREI = VORLAGE / "geo" / "03_freigegeben"

WFS = "https://wfs.geo.sh.ch/wfs"
OVERPASS = "https://overpass-api.de/api/interpreter"
ACHSE_FANG = 15.0          # m, Stueckmitte zur Kantonsstrassenachse
BUS_PUFFER = 20.0          # m, OSM-Buslinie zur Achse
BUS_MIN = 0.1              # ab diesem Anteil der Laenge im Puffer zaehlt der Bus
BUS_GANZ = 0.9             # ab diesem Anteil gilt das ganze Stueck als befahren
HALTE_FANG = 50.0          # m, Haltestelle zum Stueck (Bus-Kriterium); 50 wegen getrennter Fahrbahnen (Ebnatstrasse)
PROBE = (10.0, 15.0, 20.0, 30.0, 40.0)
TEMPO_INNERORTS = 50
BAUGEBIET_PUFFER = 30.0
BAUGEBIET_ANTEIL = 0.10
HALTE_SIEDLUNG = 150.0     # m, Haltestelle als Siedlungsmerkmal
TAFEL_SIEDLUNG = 250.0     # m, Ortstafel als Siedlungsmerkmal
BBOX_WGS = (47.55, 8.35, 47.85, 8.90)

VO = {"Überregionale Strassen", "Regionale Strassen"}
SO = {"Überlokale Strassen"}

nach_wgs = Transformer.from_crs(2056, 4326, always_xy=True).transform
nach_lv95 = Transformer.from_crs(4326, 2056, always_xy=True).transform


# ---------------------------------------------------------------- Beschaffung

def holen(typename: str, ziel: Path) -> str:
    if ziel.exists() and ziel.stat().st_size > 5000:
        print(f"  vorhanden: {ziel.name} ({ziel.stat().st_size/1024:.0f} kB)")
        return ziel.read_text(encoding="utf-8", errors="replace")
    q = urllib.parse.urlencode({"SERVICE": "WFS", "VERSION": "1.1.0", "REQUEST": "GetFeature",
                                "TYPENAME": typename, "SRSNAME": "EPSG:2056"})
    print(f"  hole {typename} …")
    with urllib.request.urlopen(f"{WFS}?{q}", timeout=600) as r:
        t = r.read().decode("utf-8", errors="replace")
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(t, encoding="utf-8")
    print(f"  gespeichert: {ziel.name} ({len(t)/1024:.0f} kB)")
    return t


def bloecke(text: str):
    return re.findall(r"<gml:featureMember>(.*?)</gml:featureMember>", text, re.S)


def felder(blk: str, namen: tuple[str, ...]) -> dict:
    return {f: (re.search(rf"<qgs:{f}>([^<]*)</qgs:{f}>", blk) or [None, ""])[1].strip()
            for f in namen}


def poslisten(blk: str):
    """Koordinatenlisten; die Dimension steht am Element (2 oder 3), die Hoehe
    wird weggelassen."""
    for tag, pl in re.findall(r"(<posList[^>]*>)([^<]+)</posList>", blk):
        m = re.search(r'srsDimension="(\d)"', tag)
        d = int(m.group(1)) if m else 2
        z = [float(v) for v in pl.split()]
        yield list(zip(z[0::d], z[1::d]))


def punkt(blk: str):
    m = re.search(r"<pos[^>]*>([^<]+)</pos>", blk)
    if not m:
        return None
    z = [float(v) for v in m.group(1).split()]
    return (z[0], z[1])


def zahl(s: str):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def liniensort(s: str):
    m = re.match(r"(\d+)", s)
    return (0, int(m.group(1)), s) if m else (1, 0, s)


def bus_holen(ziel: Path) -> list[dict]:
    """Buslinien mit Liniennummer. Je Weg die Menge der Linien, die ihn befahren."""
    if ziel.exists() and ziel.stat().st_size > 5000:
        print(f"  vorhanden: {ziel.name}")
        return json.loads(ziel.read_text(encoding="utf-8"))
    s, w, n, o = BBOX_WGS
    abfrage = f"""[out:json][timeout:180];
(
  rel["type"="route"]["route"="bus"]["operator"~"VBSH|PostAuto|PAG|PAZ",i]({s},{w},{n},{o});
  rel["type"="route"]["route"="bus"]["network"~"Ostwind|ZVV",i]({s},{w},{n},{o});
);
out geom;"""
    print("  hole Buslinien von Overpass …")
    req = urllib.request.Request(OVERPASS, data=abfrage.encode("utf-8"),
                                 headers={"User-Agent": "politspiegel-sh/1.0"})
    with urllib.request.urlopen(req, timeout=300) as r:
        daten = json.loads(r.read().decode("utf-8"))
    wege: dict[int, dict] = {}
    linien = 0
    for e in daten.get("elements", []):
        if e.get("type") != "relation":
            continue
        tags = e.get("tags") or {}
        ref = (tags.get("ref") or tags.get("name") or "?").strip()
        linien += 1
        for m in e.get("members", []):
            if m.get("type") == "way" and m.get("geometry"):
                w_ = wege.setdefault(m["ref"], {"pk": [[p["lon"], p["lat"]] for p in m["geometry"]],
                                                "linien": set()})
                w_["linien"].add(ref)
    aus = [{"pk": w_["pk"], "linien": sorted(w_["linien"], key=liniensort)}
           for w_ in wege.values() if len(w_["pk"]) >= 2]
    ziel.write_text(json.dumps(aus, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"  {linien} Linienrelationen, {len(aus)} Wege gespeichert: {ziel.name}")
    return aus


def km(g) -> float:
    return 0.0 if g.is_empty else g.length / 1000


# ---------------------------------------------------------------- Hauptlauf

def main() -> int:
    ROH.mkdir(parents=True, exist_ok=True)
    FERTIG.mkdir(parents=True, exist_ok=True)

    print("Rohdaten")
    ks_xml = holen("sh.verkehr.individual.kantonsstrassen", ROH / "kantonsstrassen_alle_roh.xml")
    la_xml = holen("sh.verkehr.laermbelastung.haupt_uebrigestrassen.linie.strassenachse",
                   ROH / "laerm_strassenachse_roh.xml")
    ot_xml = holen("sh.richtplan.strassenrichtplan.kanton.ortstafeln", ROH / "ortstafeln_roh.xml")
    bg_xml = holen("sh.nutzungsplanung.rechtsgueltig.baugebiet", ROH / "baugebiet_roh.xml")
    bus = bus_holen(ROH / "busnetz_linien_roh.json")

    # ---- Kantonsstrassenachsen
    print("\nKantonsstrassenachsen")
    achsen = []
    for blk in bloecke(ks_xml):
        e = felder(blk, ("typ", "achse_name", "achse_nummer"))
        if e["typ"] not in VO | SO:
            continue
        for pk in poslisten(blk):
            if len(pk) >= 2:
                achsen.append((LineString(pk), e))
    achsen_baum = STRtree([g for g, _ in achsen])
    print(f"  {len(achsen)} Achsen, {sum(km(g) for g, _ in achsen):.1f} km "
          f"(davon verkehrsorientiert {sum(km(g) for g, e in achsen if e['typ'] in VO):.1f} km)")

    def achse_an(p: Point):
        best, dist = None, ACHSE_FANG
        for i in achsen_baum.query(p.buffer(ACHSE_FANG)):
            d = achsen[i][0].distance(p)
            if d < dist:
                best, dist = i, d
        return achsen[best][1] if best is not None else None

    # ---- Baugebiet und Gemeinde
    print("\nBaugebiet")
    bg_ja, gem_flaechen = [], []
    for blk in bloecke(bg_xml):
        e = felder(blk, ("baugebiet", "gemeinde"))
        for aussen in re.findall(r"<(?:gml:)?exterior[^>]*>(.*?)</(?:gml:)?exterior>", blk, re.S):
            for pk in poslisten(aussen):
                if len(pk) >= 4:
                    pg = Polygon(pk).buffer(0)
                    if pg.is_valid and not pg.is_empty:
                        gem_flaechen.append((pg, e["gemeinde"]))
                        if e["baugebiet"].lower() == "ja":
                            bg_ja.append(pg)
    baugebiet = unary_union(bg_ja).buffer(BAUGEBIET_PUFFER)
    gem_baum = STRtree([p for p, _ in gem_flaechen])
    print(f"  {len(bg_ja)} Flaechen Baugebiet, {len(gem_flaechen)} Flaechen mit Gemeinde")

    def gemeinde_an(p: Point) -> str:
        best, dist = "", 1e9
        for i in gem_baum.query(p.buffer(1500)):
            d = gem_flaechen[i][0].distance(p)
            if d < dist:
                best, dist = gem_flaechen[i][1], d
        return best

    # ---- Ortstafeln, Haltestellen, Busnetz
    print("\nOrtstafeln, Haltestellen, Busnetz")
    tafeln = [Point(punkt(b)) for b in bloecke(ot_xml) if punkt(b)]
    tafel_u = unary_union(tafeln)
    halte = json.loads((FREI / "haltestellen_bus_wgs84.geojson").read_text(encoding="utf-8"))
    halte_pts = [(transform(nach_lv95, shape(f["geometry"])), f["properties"].get("n", ""))
                 for f in halte["features"]]
    halte_baum = STRtree([p for p, _ in halte_pts])
    halte_u = unary_union([p for p, _ in halte_pts])
    bus_linien = [(transform(nach_lv95, LineString(w["pk"])), w["linien"]) for w in bus]
    bus_baum = STRtree([g for g, _ in bus_linien])
    busnetz = unary_union([g for g, _ in bus_linien])
    print(f"  {len(tafeln)} Ortstafeln, {len(halte_pts)} Haltestellen, "
          f"{len(bus_linien)} Buswege ({km(busnetz):.0f} km)")

    def linien_an(g: LineString, puffer: float) -> list[str]:
        s = set()
        for i in bus_baum.query(g.buffer(puffer)):
            if bus_linien[i][0].distance(g) <= puffer:
                s.update(bus_linien[i][1])
        return sorted(s, key=liniensort)

    def haltestellen_an(g: LineString) -> list[str]:
        return sorted({halte_pts[i][1] for i in halte_baum.query(g.buffer(HALTE_FANG))
                       if halte_pts[i][0].distance(g) <= HALTE_FANG})

    # ---- Abschnittsdaten
    abschnitte = json.loads((FERTIG / "per_abschnitt.json").read_text(encoding="utf-8"))
    je_name = defaultdict(list)
    for a in abschnitte:
        je_name[((a.get("name") or "").strip().lower(), (a.get("gemeinde") or "").strip().lower())].append(a)

    def abschnitt_zu(strasse: str, gemeinde: str):
        k = ((strasse or "").strip().lower(), (gemeinde or "").strip().lower())
        if k in je_name:
            return je_name[k][0]
        for (n, gm), rows in je_name.items():
            if n == k[0] and (gm.startswith(k[1][:6]) or k[1].startswith(gm[:6])):
                return rows[0]
        return None

    # ---- Stuecke des Laermkatasters auf Kantonsstrassen
    print("\nStrassenstuecke")
    stuecke = []
    for blk in bloecke(la_xml):
        e = felder(blk, ("uuid", "strassenname", "abschnitts_id", "dtv",
                         "signalisierte_geschwindigkeit_am_tag_kmh",
                         "emissionswert_lw_a_am_tag_db_a"))
        for pk in poslisten(blk):
            if len(pk) < 2:
                continue
            g = LineString(pk)
            a = achse_an(g.interpolate(0.5, normalized=True))
            if a is None:
                continue
            stuecke.append((g, e, a))
    print(f"  {len(stuecke)} Stuecke auf Kantonsstrassen, {sum(km(g) for g, _, _ in stuecke):.1f} km")

    bus_puffer_g = busnetz.buffer(BUS_PUFFER)
    features, ausgeschlossen = [], []
    for g, e, a in stuecke:
        tempo = zahl(e["signalisierte_geschwindigkeit_am_tag_kmh"])
        if tempo is None or tempo > TEMPO_INNERORTS:
            continue
        bg_anteil = g.intersection(baugebiet).length / g.length
        d_halte, d_tafel = g.distance(halte_u), g.distance(tafel_u)
        mitte = g.interpolate(0.5, normalized=True)
        gem = gemeinde_an(mitte)
        siedlung = (bg_anteil >= BAUGEBIET_ANTEIL or d_halte <= HALTE_SIEDLUNG or d_tafel <= TAFEL_SIEDLUNG)
        if not siedlung:
            ausgeschlossen.append({"strasse": e["strassenname"], "gemeinde": gem, "tempo": int(tempo),
                                   "laenge_m": round(g.length), "baugebiet_anteil": round(bg_anteil, 2),
                                   "haltestelle_m": round(d_halte), "ortstafel_m": round(d_tafel)})
            continue
        linien = linien_an(g, BUS_PUFFER)
        halte_hier = haltestellen_an(g)
        bus_teil = g.intersection(bus_puffer_g)
        bus_anteil = bus_teil.length / g.length
        # Bus: ganz, teilweise oder nicht. Faehrt die Linie nur ueber einen
        # Teil des Stuecks (sie biegt mittendrin ab), zaehlt fuer die
        # Initiative genau dieser Teil; das Stueck wird dort geschnitten.
        bus_ja = bus_anteil >= BUS_MIN or bool(halte_hier)
        ab = abschnitt_zu(e["strassenname"], gem)
        fkt = "VO" if a["typ"] in VO else "SO"
        eig = {
            "nr": a["achse_nummer"], "achse": a["achse_name"],
            "strasse": e["strassenname"], "gemeinde": gem,
            "fkt": fkt, "fkt_text": "verkehrsorientiert" if fkt == "VO" else "siedlungsorientiert",
            "tempo": int(tempo),
            "dtv": int(zahl(e["dtv"])) if zahl(e["dtv"]) is not None else None,
            "laerm_tag_db": round(zahl(e["emissionswert_lw_a_am_tag_db_a"]), 1)
                            if zahl(e["emissionswert_lw_a_am_tag_db_a"]) is not None else None,
            "bus": bus_ja, "linien": linien, "haltestellen": halte_hier,
            "bus_anteil": round(bus_anteil, 2),
            "bus_text": ("ja" if bus_anteil >= BUS_GANZ or (halte_hier and bus_anteil < BUS_MIN)
                         else ("teilweise" if bus_ja else "nein")),
            "laenge_m": round(g.length),
            "abschnitt": ab["name"] if ab else "",
            "abschnitt_km": ab["km"] if ab else None,
            "unfaelle": ab["unf"] if ab else None,
            "unf_fuss": ab["fuss"] if ab else None,
            "unf_velo": ab["velo"] if ab else None,
            "fassaden_igw": ab["fass_igw"] if ab else None,
            "initiative": bus_ja, "gegenvorschlag": fkt == "VO",
        }
        # Geometrie fuer die Initiative: nur der befahrene Teil
        if bus_ja and BUS_MIN <= bus_anteil < BUS_GANZ:
            teile = [x for x in (bus_teil.geoms if hasattr(bus_teil, "geoms") else [bus_teil])
                     if x.geom_type == "LineString" and x.length >= 20]
            g_ini = unary_union(teile) if teile else None
        else:
            g_ini = g if bus_ja else None
        features.append((g, eig, g_ini))

    innerorts_km = sum(km(g) for g, _, _ in features)
    ini = [(gi, dict(e, laenge_m=round(gi.length))) for g, e, gi in features if gi is not None and not gi.is_empty]
    gv = [(g, e) for g, e, _ in features if e["gegenvorschlag"]]
    gv_u = unary_union([g for g, _ in gv]).buffer(3) if gv else None
    beide = [(g, e) for g, e in ini if gv_u is not None and g.intersection(gv_u).length > 0.5 * g.length]
    nur_ini = [(g, e) for g, e in ini if not (gv_u is not None and g.intersection(gv_u).length > 0.5 * g.length)]
    ini_u = unary_union([g for g, _ in ini]).buffer(3) if ini else None
    nur_gv = [(g, e) for g, e in gv if not e["bus"]]
    nur_gv_km = sum(km(g.difference(ini_u)) if ini_u is not None else km(g) for g, _ in gv)
    print(f"\nInnerorts (Tempo <= {TEMPO_INNERORTS}, Siedlungslage): {innerorts_km:.1f} km, "
          f"{len(features)} Stuecke; ausgeschlossen {len(ausgeschlossen)} Stuecke, "
          f"{sum(x['laenge_m'] for x in ausgeschlossen)/1000:.1f} km")
    print("\nGeltungsbereiche")
    print(f"  Initiative      {sum(km(g) for g, _ in ini):6.1f} km  ({len(ini)} Stuecke)")
    print(f"  Gegenvorschlag  {sum(km(g) for g, _ in gv):6.1f} km  ({len(gv)} Stuecke)")
    print(f"  beide           {sum(km(g) for g, _ in beide):6.1f} km")
    print(f"  nur Initiative  {sum(km(g) for g, _ in nur_ini):6.1f} km   (Bus, aber siedlungsorientiert)")
    print(f"  nur Gegenvorsch.{nur_gv_km:6.1f} km   (verkehrsorientiert, kein Bus)")
    ohne_abschnitt = [e for _, e, _ in features if not e["abschnitt"]]
    print(f"  ohne Abschnittsdaten: {len(ohne_abschnitt)} Stuecke, "
          f"{sum(e['laenge_m'] for e in ohne_abschnitt)/1000:.1f} km")

    print("\nEmpfindlichkeit auf den Buspuffer (nur OSM-Kriterium)")
    probe = {}
    for pb in PROBE:
        bp = busnetz.buffer(pb)
        probe[str(int(pb))] = round(sum(km(g.intersection(bp)) for g, _, _ in features), 1)
        print(f"  {pb:5.0f} m  {probe[str(int(pb))]:6.1f} km")

    def je_gemeinde(st):
        s = defaultdict(lambda: {"km": 0.0, "stuecke": 0})
        for g, e in st:
            s[e["gemeinde"] or "(ohne)"]["km"] += g.length / 1000
            s[e["gemeinde"] or "(ohne)"]["stuecke"] += 1
        return {k: {"km": round(v["km"], 2), "stuecke": v["stuecke"]}
                for k, v in sorted(s.items(), key=lambda x: -x[1]["km"])}

    def geojson(st, vorlage):
        return {"type": "FeatureCollection", "features": [
            {"type": "Feature", "properties": dict(e, vorlage=vorlage),
             "geometry": mapping(transform(nach_wgs, g))} for g, e in st]}

    (FERTIG / "geltung_initiative.geojson").write_text(
        json.dumps(geojson(ini, "initiative"), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (FERTIG / "geltung_gegenvorschlag.geojson").write_text(
        json.dumps(geojson(gv, "gegenvorschlag"), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    kennzahlen = {
        "gerechnet_am": datetime.date.today().isoformat(),
        "regeln": {
            "kantonsstrasse": f"Stueckmitte hoechstens {ACHSE_FANG:.0f} m von einer Kantonsstrassenachse",
            "innerorts": f"signalisiertes Tempo am Tag <= {TEMPO_INNERORTS} km/h und Siedlungslage "
                         f"(>= {BAUGEBIET_ANTEIL:.0%} im Baugebiet mit {BAUGEBIET_PUFFER:.0f} m Puffer, "
                         f"oder Haltestelle in {HALTE_SIEDLUNG:.0f} m, oder Ortstafel in {TAFEL_SIEDLUNG:.0f} m)",
            "bus": f"Teil des Stuecks in {BUS_PUFFER:.0f} m einer OSM-Buslinie (ab {BUS_MIN:.0%} der Laenge; "
                   f"unter {BUS_GANZ:.0%} wird das Stueck auf den befahrenen Teil geschnitten), "
                   f"oder BAV-Haltestelle in {HALTE_FANG:.0f} m",
            "verkehrsorientiert": "Feld typ der Kantonsstrassenachse: Ueberregionale oder Regionale Strassen",
        },
        "kantonsstrassen_km": round(sum(km(g) for g, _ in achsen), 1),
        "stuecke_auf_kantonsstrassen": len(stuecke),
        "innerorts_km": round(innerorts_km, 1), "innerorts_stuecke": len(features),
        "initiative_km": round(sum(km(g) for g, _ in ini), 1), "initiative_stuecke": len(ini),
        "gegenvorschlag_km": round(sum(km(g) for g, _ in gv), 1), "gegenvorschlag_stuecke": len(gv),
        "beide_km": round(sum(km(g) for g, _ in beide), 1),
        "nur_initiative_km": round(sum(km(g) for g, _ in nur_ini), 1),
        "nur_gegenvorschlag_km": round(nur_gv_km, 1),
        "ohne_abschnittsdaten_km": round(sum(e["laenge_m"] for e in ohne_abschnitt) / 1000, 1),
        "puffer_probe_km": probe,
        "je_gemeinde": {"initiative": je_gemeinde(ini), "gegenvorschlag": je_gemeinde(gv)},
        "ausgeschlossen_tempo50_ohne_siedlung": sorted(ausgeschlossen, key=lambda x: -x["laenge_m"]),
        "kontrolle_uebergabe_juli_2026": {"innerorts_km": 80.4, "verkehrsorientiert_innerorts_km": 43.9},
        "quellen": {
            "kantonsstrassen": "sh.verkehr.individual.kantonsstrassen, wfs.geo.sh.ch",
            "stuecke": "sh.verkehr.laermbelastung.haupt_uebrigestrassen.linie.strassenachse, wfs.geo.sh.ch "
                       "(Strassenname, signalisierte Geschwindigkeit, DTV, Emissionswert)",
            "ortstafeln": "sh.richtplan.strassenrichtplan.kanton.ortstafeln, wfs.geo.sh.ch",
            "baugebiet": "sh.nutzungsplanung.rechtsgueltig.baugebiet, wfs.geo.sh.ch (auch Gemeinde)",
            "busnetz": "OpenStreetMap, Linienrelationen VBSH, PostAuto, PAZ, Ostwind, ZVV, via Overpass",
            "haltestellen": "Bundesamt fuer Verkehr, ch.bav.haltestellen-oev",
            "abschnitte": "per_abschnitt.json (Unfaelle ASTRA 2011 bis 2025, Laermfassaden geo.sh.ch)",
        },
    }
    (FERTIG / "geltungsbereich.json").write_text(
        json.dumps(kennzahlen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\ngeschrieben: geltung_initiative.geojson, geltung_gegenvorschlag.geojson, geltungsbereich.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())

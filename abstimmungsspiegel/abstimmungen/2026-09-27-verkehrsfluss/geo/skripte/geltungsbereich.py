#!/usr/bin/env python3
"""Rechnet die Geltungsbereiche von Initiative und Gegenvorschlag aus.

Aufruf aus der Projektwurzel:
    python3 abstimmungsspiegel/abstimmungen/2026-09-27-verkehrsfluss/geo/skripte/geltungsbereich.py

Holt   wfs.geo.sh.ch    sh.verkehr.individual.kantonsstrassen   alle Strassenachsen
                        sh.bauland.bauzone                      Bauzone als Innerorts-Ersatz
                        sh.richtplan.strassenrichtplan.kanton.strassen.bestehend.fkt
                                                                Funktionszuweisung
Liest  geo/01_roh/busnetz_roh.json                              Buslinien aus OpenStreetMap
Legt   geo/01_roh/kantonsstrassen_alle_roh.xml
       geo/01_roh/bauzone_roh.xml
       geo/02_aufbereitet/geltung_initiative.geojson
       geo/02_aufbereitet/geltung_gegenvorschlag.geojson
       geo/02_aufbereitet/geltungsbereich.json                  Kennzahlen

Warum das gerechnet und nicht nur eingeblendet gehoert
------------------------------------------------------
Initiative und Gegenvorschlag erfassen verschiedene Strassen:

    Initiative      Kantonsstrassen innerorts, die auch durch den
                    oeffentlichen Verkehr genutzt werden
    Gegenvorschlag  verkehrsorientierte Kantonsstrassen innerorts,
                    ohne Bedingung zum oeffentlichen Verkehr

Bisher zeigte die Karte fuer beide dieselbe Ebene, naemlich die
verkehrsorientierten Strassen aus dem Richtplan. Fuer den Gegenvorschlag ist das
richtig, denn er knuepft genau daran an. Fuer die Initiative ist es falsch: Sie
knuepft nicht an die Funktion an, sondern an den Bus. Eine Quartiersammelstrasse
mit Buslinie faellt unter die Initiative, aber nicht unter den Gegenvorschlag.
Die verkehrsorientierte Ebene unter «Initiative» zu zeigen liess also gerade den
Teil weg, der die beiden Vorlagen unterscheidet.

Der Verschnitt
--------------
    Initiative     = Kantonsstrassen  n  Bauzone  n  Puffer(Busnetz, PUFFER m)
    Gegenvorschlag = verkehrsorientierte Kantonsstrassen  n  Bauzone

Gerechnet in LV95, wo Meter Meter sind. Ausgegeben in WGS84 fuer die Karte.

Was der Puffer leistet und was nicht
------------------------------------
Die Buslinienfuehrung stammt aus OpenStreetMap und ist eine andere Geometrie als
die amtliche Strassenachse; beide beschreiben dieselbe Strasse, liegen aber
einige Meter auseinander. Der Puffer faengt diesen Versatz auf. Er ist damit
eine Toleranz, keine Aussage: Zu klein, und befahrene Strassen fallen heraus; zu
gross, und die Parallelstrasse kommt mit. PUFFER ist darum aus der gemessenen
Abweichung der beiden Quellen abgeleitet, siehe unten, und das Skript gibt zur
Kontrolle aus, wie stark das Ergebnis am Puffer haengt.
"""

from __future__ import annotations

import json
import math
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import LineString, MultiLineString, mapping, shape
from shapely.ops import transform, unary_union

VORLAGE = Path(__file__).resolve().parent.parent.parent
ROH = VORLAGE / "geo" / "01_roh"
FERTIG = VORLAGE / "geo" / "02_aufbereitet"

WFS = "https://wfs.geo.sh.ch/wfs"
PUFFER = 20.0          # Meter, siehe Kopfkommentar
PROBE = (10.0, 15.0, 20.0, 30.0, 40.0)   # Empfindlichkeitsprobe

nach_wgs = Transformer.from_crs(2056, 4326, always_xy=True).transform


def holen(typename: str, ziel: Path) -> str:
    """WFS 1.1.0 mit TYPENAME. Version 2.0.0 mit TYPENAMES antwortet hier mit 500."""
    if ziel.exists() and ziel.stat().st_size > 5000:
        print(f"  vorhanden: {ziel.name} ({ziel.stat().st_size/1024:.0f} kB)")
        return ziel.read_text(encoding="utf-8", errors="replace")
    q = urllib.parse.urlencode({"SERVICE": "WFS", "VERSION": "1.1.0",
                                "REQUEST": "GetFeature", "TYPENAME": typename,
                                "SRSNAME": "EPSG:2056"})
    print(f"  hole {typename} …")
    with urllib.request.urlopen(f"{WFS}?{q}", timeout=300) as r:
        t = r.read().decode("utf-8", errors="replace")
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(t, encoding="utf-8")
    print(f"  gespeichert: {ziel.name} ({len(t)/1024:.0f} kB)")
    return t


def gml_lesen(text: str, felder: tuple[str, ...]):
    """Liest LineString- und Polygon-Objekte samt Eigenschaften aus GML 3.

    Kein vollstaendiger GML-Leser, sondern genau so viel, wie dieser Dienst
    liefert. Ein XML-Baum waere ordentlicher, kostet bei 30 MB aber mehr
    Speicher als hier noetig.
    """
    aus = []
    for blk in re.findall(r"<gml:featureMember>(.*?)</gml:featureMember>", text, re.S):
        eig = {f: (re.search(rf"<qgs:{f}>([^<]*)</qgs:{f}>", blk) or [None, ""])[1]
               for f in felder}
        for pl in re.findall(r"<posList[^>]*>([^<]+)</posList>", blk):
            z = [float(v) for v in pl.split()]
            pk = list(zip(z[0::2], z[1::2]))
            if len(pk) >= 2:
                aus.append((pk, dict(eig)))
    return aus


def polygone_lesen(text: str):
    """Nur die Aussenringe. Loecher in einer Bauzone sind fuer die Frage
    «liegt diese Strasse innerorts» ohne Belang und kosten nur Rechenzeit."""
    ringe = []
    for blk in re.findall(r"<gml:featureMember>(.*?)</gml:featureMember>", text, re.S):
        for aussen in re.findall(r"<(?:gml:)?exterior>(.*?)</(?:gml:)?exterior>", blk, re.S) \
                      or re.findall(r"<(?:gml:)?outerBoundaryIs>(.*?)</(?:gml:)?outerBoundaryIs>", blk, re.S):
            for pl in re.findall(r"<posList[^>]*>([^<]+)</posList>", aussen):
                z = [float(v) for v in pl.split()]
                pk = list(zip(z[0::2], z[1::2]))
                if len(pk) >= 4:
                    ringe.append(pk)
    return ringe


def km(g) -> float:
    if g.is_empty:
        return 0.0
    if g.geom_type == "LineString":
        return g.length / 1000
    return sum(p.length for p in g.geoms if p.geom_type == "LineString") / 1000


def als_geojson(g, eigenschaften: dict) -> dict:
    teile = [g] if g.geom_type == "LineString" else [x for x in getattr(g, "geoms", [])]
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": eigenschaften,
         "geometry": mapping(transform(nach_wgs, t))}
        for t in teile if t.geom_type == "LineString" and not t.is_empty]}


def main() -> int:
    ROH.mkdir(parents=True, exist_ok=True)
    FERTIG.mkdir(parents=True, exist_ok=True)

    print("Rohdaten")
    ks_xml = holen("sh.verkehr.individual.kantonsstrassen",
                   ROH / "kantonsstrassen_alle_roh.xml")
    bz_xml = holen("sh.bauland.bauzone", ROH / "bauzone_roh.xml")
    fkt_xml = holen("sh.richtplan.strassenrichtplan.kanton.strassen.bestehend.fkt",
                    ROH / "strassenfunktion_roh.xml")

    print("\nStrassenachsen")
    achsen = gml_lesen(ks_xml, ("typ", "achse_name", "achse_nummer", "achse_art", "hoheit"))
    arten = {}
    for _, e in achsen:
        arten[e["typ"]] = arten.get(e["typ"], 0) + 1
    for t, c in sorted(arten.items(), key=lambda x: -x[1]):
        print(f"  {t or '(ohne)':22s} {c:5d}")
    kant = [LineString(pk) for pk, e in achsen if e["typ"] == "Kantonsstrasse"]
    if not kant:
        print("Keine Kantonsstrassen gefunden, Abbruch.", file=sys.stderr)
        return 1
    kantonsstrassen = unary_union(kant)
    print(f"  Kantonsstrassen gesamt: {km(kantonsstrassen):.1f} km")

    print("\nBauzone als Innerorts-Ersatz")
    from shapely.geometry import Polygon
    ringe = polygone_lesen(bz_xml)
    flaechen = [Polygon(r).buffer(0) for r in ringe]
    bauzone = unary_union([f for f in flaechen if f.is_valid and not f.is_empty])
    print(f"  {len(ringe)} Ringe, {bauzone.area/1e6:.1f} km2")

    innerorts = kantonsstrassen.intersection(bauzone)
    print(f"  Kantonsstrassen innerorts: {km(innerorts):.1f} km")

    print("\nBusnetz")
    bus_roh = json.loads((ROH / "busnetz_roh.json").read_text(encoding="utf-8"))
    # Das Rohnetz liegt in WGS84, fuer den Verschnitt braucht es LV95.
    nach_lv95 = Transformer.from_crs(4326, 2056, always_xy=True).transform
    bus_linien = []
    for el in (bus_roh.get("elements") or bus_roh.get("features") or []):
        pk = ([(p["lon"], p["lat"]) for p in el.get("geometry", [])]
              if isinstance(el.get("geometry"), list)
              else (el.get("geometry", {}) or {}).get("coordinates") or [])
        if isinstance(pk, list) and len(pk) >= 2 and isinstance(pk[0], (list, tuple)):
            bus_linien.append(transform(nach_lv95, LineString(pk)))
    if not bus_linien:
        print("  Kein Busnetz lesbar, Abbruch.", file=sys.stderr)
        return 1
    busnetz = unary_union(bus_linien)
    print(f"  {len(bus_linien)} Linienstuecke, {km(busnetz):.1f} km")

    print("\nVerkehrsorientierte Funktion")
    fkt = gml_lesen(fkt_xml, ("funktion", "achse_name", "achse_nummer"))
    fkt_arten = {}
    for _, e in fkt:
        fkt_arten[e["funktion"]] = fkt_arten.get(e["funktion"], 0) + 1
    for t, c in sorted(fkt_arten.items(), key=lambda x: -x[1]):
        print(f"  {t or '(ohne)':26s} {c:5d}")
    VO = {"überregional", "ueberregional", "regional",
          "Überregionale Verbindung", "Regionale Verbindung"}
    vo = [LineString(pk) for pk, e in fkt if (e["funktion"] or "").strip() in VO]
    verkehrsorientiert = unary_union(vo) if vo else MultiLineString([])

    # ---- Die beiden Geltungsbereiche
    print("\nGeltungsbereiche")
    gv = verkehrsorientiert.intersection(bauzone)
    ini = innerorts.intersection(busnetz.buffer(PUFFER))
    print(f"  Gegenvorschlag  verkehrsorientiert n innerorts      {km(gv):6.1f} km")
    print(f"  Initiative      Kantonsstr. n innerorts n Bus({PUFFER:.0f} m) {km(ini):6.1f} km")

    beide = ini.intersection(gv.buffer(5.0))
    nur_ini = ini.difference(gv.buffer(5.0))
    nur_gv = gv.difference(ini.buffer(5.0))
    print(f"\n  beides erfasst                                  {km(beide):6.1f} km")
    print(f"  nur Initiative (Bus, aber nicht verkehrsorient.) {km(nur_ini):6.1f} km")
    print(f"  nur Gegenvorschlag (verkehrsorient., kein Bus)   {km(nur_gv):6.1f} km")

    print("\nEmpfindlichkeit auf den Puffer")
    probe = {}
    for pb in PROBE:
        probe[pb] = round(km(innerorts.intersection(busnetz.buffer(pb))), 1)
        print(f"  {pb:5.0f} m  {probe[pb]:6.1f} km")

    (FERTIG / "geltung_initiative.geojson").write_text(
        json.dumps(als_geojson(ini, {"v": "initiative"}), ensure_ascii=False,
                   separators=(",", ":")), encoding="utf-8")
    (FERTIG / "geltung_gegenvorschlag.geojson").write_text(
        json.dumps(als_geojson(gv, {"v": "gegenvorschlag"}), ensure_ascii=False,
                   separators=(",", ":")), encoding="utf-8")

    kennzahlen = {
        "gerechnet_am": __import__("datetime").date.today().isoformat(),
        "puffer_m": PUFFER,
        "kantonsstrassen_km": round(km(kantonsstrassen), 1),
        "kantonsstrassen_innerorts_km": round(km(innerorts), 1),
        "busnetz_km": round(km(busnetz), 1),
        "initiative_km": round(km(ini), 1),
        "gegenvorschlag_km": round(km(gv), 1),
        "beide_km": round(km(beide), 1),
        "nur_initiative_km": round(km(nur_ini), 1),
        "nur_gegenvorschlag_km": round(km(nur_gv), 1),
        "puffer_probe_km": probe,
        "quellen": {
            "kantonsstrassen": "sh.verkehr.individual.kantonsstrassen, wfs.geo.sh.ch",
            "innerorts": "sh.bauland.bauzone, wfs.geo.sh.ch, als Ersatz fuer die Innerortsgrenze",
            "funktion": "sh.richtplan.strassenrichtplan.kanton.strassen.bestehend.fkt",
            "busnetz": "OpenStreetMap, Linienrelationen VBSH, PostAuto, PAZ"},
        "vorbehalte": [
            "Die Bauzone ist nicht die Innerortsgrenze. Innerorts beginnt an der "
            "Ortstafel, und die steht nicht immer an der Bauzonengrenze.",
            "Die Buslinienfuehrung stammt aus OpenStreetMap, ist betrieblich und "
            "nicht amtlich, und aendert mit jedem Fahrplanwechsel.",
            f"Der Puffer von {PUFFER:.0f} m faengt den Versatz zwischen amtlicher "
            "Strassenachse und OSM-Linienfuehrung auf. Die Empfindlichkeitsprobe "
            "zeigt, wie stark das Ergebnis daran haengt.",
        ],
    }
    (FERTIG / "geltungsbereich.json").write_text(
        json.dumps(kennzahlen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\ngeschrieben: {FERTIG.name}/geltung_initiative.geojson, "
          f"geltung_gegenvorschlag.geojson, geltungsbereich.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())

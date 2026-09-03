#!/usr/bin/env python3
"""Gemeindekarten und Kennzahlen je Gemeinde aus den gerechneten Geltungsbereichen.

Aufruf aus der Projektwurzel:
    python3 abstimmungsspiegel/abstimmungen/2026-09-27-verkehrsfluss/geo/skripte/gemeindekarten.py

Liest  geo/03_freigegeben/geltung_initiative.geojson, geltung_gegenvorschlag.geojson
       geo/01_roh/baugebiet_roh.xml, kantonsstrassen_alle_roh.xml
Holt   overpass-api.de   Schulen, Kindergaerten, Alters- und Pflegeheime, weitere
                         Sozialeinrichtungen (OpenStreetMap)
Legt   geo/01_roh/anlagen_osm_roh.json
       geo/02_aufbereitet/anlagen.geojson              die Standorte, WGS84
       geo/02_aufbereitet/kandidaten_wgs84.geojson     betroffene Strassen in 100 und 300 m
       geo/02_aufbereitet/gemeinden.json               Kennzahlen je Gemeinde und Kanton
       grafiken/gemeinden/karte_<Gemeinde>.svg         eine Karte je Gemeinde
       vorlage.json                                    karte.gemeinden, karte.total, karte.anlagen_total

Bis zum 4. September 2026 stammten Karten und Zahlen aus der Uebergabe vom
Juli 2026 (verkehrsorientierte Strassen, 43,9 km, Standorte aus einem
GeoPackage, das nicht im Repository liegt). Jetzt zeigt jede Karte beide
Vorlagen, Rot fuer den Gegenvorschlag, Blau fuer die Initiative, und die
Standorte kommen aus OpenStreetMap, damit die Rechnung wiederholbar ist:

    schule        amenity=school, college
    kindergarten  amenity=kindergarten, childcare
    altersheim    amenity=nursing_home; social_facility mit social_facility=
                  nursing_home, assisted_living, group_home
    sozial        uebrige social_facility, amenity=hospital

Betroffen je Gemeinde: die Stuecke beider Ebenen, deren Mitte in der Gemeinde
liegt (Feld gemeinde der Ebenen). Umkreise 100, 300 und 500 m Luftlinie um
jeden Standort; gezaehlt wird die Laenge der betroffenen Strassen (mindestens
eine Vorlage) im Umkreis.
"""

from __future__ import annotations

import collections
import json
import re
import sys
import urllib.request
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import LineString, Point, Polygon, box, mapping, shape
from shapely.ops import transform, unary_union
from shapely.strtree import STRtree

VORLAGE = Path(__file__).resolve().parent.parent.parent
ROH = VORLAGE / "geo" / "01_roh"
FERTIG = VORLAGE / "geo" / "02_aufbereitet"
FREI = VORLAGE / "geo" / "03_freigegeben"
GRAFIKEN = VORLAGE / "grafiken" / "gemeinden"
DATEI = VORLAGE / "vorlage.json"

OVERPASS = "https://overpass-api.de/api/interpreter"
BBOX_WGS = (47.55, 8.35, 47.85, 8.90)
RADIEN = (100, 300, 500)

nach_lv95 = Transformer.from_crs(4326, 2056, always_xy=True).transform
nach_wgs = Transformer.from_crs(2056, 4326, always_xy=True).transform

CAT_ORDER = ["schule", "kindergarten", "altersheim", "sozial"]
CAT = {"schule": {"label": "Schule", "col": "#d95f0e"},
       "kindergarten": {"label": "Kindergarten", "col": "#1b9e77"},
       "altersheim": {"label": "Alters-/Pflegeheim", "col": "#6a51a3"},
       "sozial": {"label": "Weitere Sozialeinrichtung", "col": "#2166ac"}}
FONT = "Archivo, 'Public Sans', Arial, 'Helvetica Neue', sans-serif"
INK, INK2, MUTED = "#141414", "#555", "#8a8881"
ROAD_CTX, INNER_FILL, INNER_STROKE = "#cbc9c2", "#f2f1ec", "#e4e2da"
ROAD_GV, ROAD_INI = "#DC2626", "#1D4ED8"
CAND100, CAND300 = "#141414", "#9a9a9a"
FILLOP = {500: 0.05, 300: 0.09, 100: 0.17}


def bloecke(text):
    return re.findall(r"<gml:featureMember>(.*?)</gml:featureMember>", text, re.S)


def feld(blk, name):
    m = re.search(rf"<qgs:{name}>([^<]*)</qgs:{name}>", blk)
    return m.group(1).strip() if m else ""


def poslisten(blk):
    for tag, pl in re.findall(r"(<posList[^>]*>)([^<]+)</posList>", blk):
        m = re.search(r'srsDimension="(\d)"', tag)
        d = int(m.group(1)) if m else 2
        z = [float(v) for v in pl.split()]
        yield list(zip(z[0::d], z[1::d]))


def slug(g):
    return (g.replace(" (SH)", "").replace(" am Rheinfall", "").replace(" am Rhein", "_am_Rhein")
            .replace(" ", "_"))


def anlagen_holen(ziel: Path):
    if ziel.exists() and ziel.stat().st_size > 1000:
        return json.loads(ziel.read_text(encoding="utf-8"))
    s, w, n, o = BBOX_WGS
    q = f"""[out:json][timeout:180];
(
  nwr["amenity"~"^(school|college|kindergarten|childcare|nursing_home|social_facility|hospital)$"]({s},{w},{n},{o});
);
out center tags;"""
    print("  hole Anlagen von Overpass …")
    req = urllib.request.Request(OVERPASS, data=q.encode("utf-8"), headers={"User-Agent": "politspiegel-sh/1.0"})
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.loads(r.read().decode("utf-8"))
    ziel.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return d


def anlagen_aus_gpkg(pfad: Path, gemeinde_an):
    """Das GeoPackage der Uebergabe (infra_SH_v2.gpkg, 213 Standorte aus OSM
    und kantonalen Quellen), falls es unter geo/01_roh liegt. Gelesen ueber
    sqlite3; die Geometrie ist WKB mit GeoPackage-Kopf, LV95."""
    import sqlite3
    from shapely import wkb
    layer_cat = {"kindergaerten": "kindergarten", "schulen": "schule",
                 "pflegeheime": "altersheim", "unklar_sozialeinrichtungen": "sozial"}
    con = sqlite3.connect(str(pfad))
    aus = []
    for layer, cat in layer_cat.items():
        try:
            spalten = [r[1] for r in con.execute(f'PRAGMA table_info("{layer}")')]
        except sqlite3.Error:
            continue
        geo_sp = next((s for s in spalten if s.lower() in ("geom", "geometry", "the_geom")), None)
        if not geo_sp:
            continue
        name_sp = next((s for s in spalten if s.lower() in ("name", "bezeichnung")), None)
        for row in con.execute(f'SELECT "{geo_sp}"{", " + chr(34) + name_sp + chr(34) if name_sp else ""} FROM "{layer}"'):
            blob = row[0]
            if not blob:
                continue
            # GeoPackage-Binary: Magic «GP», Version, Flags, SRS-ID, dann Envelope je nach Flag
            flags = blob[3]
            env_len = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}.get((flags >> 1) & 7, 0)
            g = wkb.loads(bytes(blob[8 + env_len:]))
            if g.geom_type != "Point":
                g = g.centroid
            gem = gemeinde_an(g)
            if gem:
                aus.append({"cat": cat, "name": (row[1] if name_sp else "") or "", "gem": gem, "x": g.x, "y": g.y})
    return aus


def kategorie(tags: dict):
    a = tags.get("amenity", "")
    if a in ("school", "college"):
        return "schule"
    if a in ("kindergarten", "childcare"):
        return "kindergarten"
    if a == "nursing_home":
        return "altersheim"
    if a == "social_facility":
        sf = tags.get("social_facility", "")
        if sf in ("nursing_home", "assisted_living", "group_home") or "senior" in tags.get("social_facility:for", ""):
            return "altersheim"
        return "sozial"
    if a == "hospital":
        return "sozial"
    return None


def main() -> int:
    print("Betroffene Strassen")
    def lesen(name):
        d = json.loads((FREI / name).read_text(encoding="utf-8"))
        return [(transform(nach_lv95, shape(f["geometry"])), f["properties"]) for f in d["features"]]
    ini, gv = lesen("geltung_initiative.geojson"), lesen("geltung_gegenvorschlag.geojson")
    alle = [(g, p, "ini") for g, p in ini] + [(g, p, "gv") for g, p in gv]
    netz = unary_union([g for g, _, _ in alle])
    print(f"  Initiative {sum(g.length for g, _ in ini)/1000:.1f} km, Gegenvorschlag "
          f"{sum(g.length for g, _ in gv)/1000:.1f} km, mindestens eine {netz.length/1000:.1f} km")

    print("\nGemeinden und Baugebiet")
    bg = (ROH / "baugebiet_roh.xml").read_text(encoding="utf-8", errors="replace")
    gem_fl, innen = [], collections.defaultdict(list)
    for blk in bloecke(bg):
        gem, ja = feld(blk, "gemeinde"), feld(blk, "baugebiet").lower() == "ja"
        for aussen in re.findall(r"<(?:gml:)?exterior[^>]*>(.*?)</(?:gml:)?exterior>", blk, re.S):
            for pk in poslisten(aussen):
                if len(pk) >= 4:
                    pg = Polygon(pk).buffer(0)
                    if pg.is_valid and not pg.is_empty:
                        gem_fl.append((pg, gem))
                        if ja:
                            innen[gem].append(pg)
    gem_baum = STRtree([p for p, _ in gem_fl])
    innen_u = {g: unary_union(v) for g, v in innen.items()}

    def gemeinde_an(pt: Point) -> str:
        """Gemeinde, in deren Flaeche der Punkt liegt; die Flaechen der
        Nutzungsplanung decken das Kantonsgebiet. Ausserhalb (deutsche
        Nachbarschaft im Suchrahmen) bleibt es leer."""
        for i in gem_baum.query(pt):
            if gem_fl[i][0].contains(pt):
                return gem_fl[i][1]
        return ""

    ks = (ROH / "kantonsstrassen_alle_roh.xml").read_text(encoding="utf-8", errors="replace")
    kontext = [LineString(pk) for blk in bloecke(ks) for pk in poslisten(blk) if len(pk) >= 2]

    print("\nAnlagen")
    gpkg = ROH / "infra_SH_v2.gpkg"
    quelle_anlagen = "OpenStreetMap"
    anlagen = []
    if gpkg.exists():
        anlagen = anlagen_aus_gpkg(gpkg, gemeinde_an)
        quelle_anlagen = "GeoPackage infra_SH_v2 (OpenStreetMap und kantonale Quellen)"
        print(f"  aus {gpkg.name}")
    roh = anlagen_holen(ROH / "anlagen_osm_roh.json") if not anlagen else {"elements": []}
    for el in roh.get("elements", []):
        tags = el.get("tags") or {}
        cat = kategorie(tags)
        if not cat:
            continue
        lon, lat = (el.get("lon"), el.get("lat")) if el.get("type") == "node" else \
                   ((el.get("center") or {}).get("lon"), (el.get("center") or {}).get("lat"))
        if lon is None:
            continue
        p = transform(nach_lv95, Point(lon, lat))
        gem = gemeinde_an(p)
        if not gem:
            continue
        anlagen.append({"cat": cat, "name": tags.get("name", ""), "gem": gem, "x": p.x, "y": p.y})
    # Doppelte (Node und Flaeche derselben Anlage) auf 40 m zusammenfassen
    eindeutig = []
    for a in anlagen:
        if any(b["cat"] == a["cat"] and abs(b["x"] - a["x"]) < 40 and abs(b["y"] - a["y"]) < 40 for b in eindeutig):
            continue
        eindeutig.append(a)
    anlagen = eindeutig
    zaehl = collections.Counter(a["cat"] for a in anlagen)
    print(f"  {len(anlagen)} Standorte: " + ", ".join(f"{zaehl[c]} {CAT[c]['label']}" for c in CAT_ORDER))
    (FERTIG / "anlagen.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"kat": a["cat"], "name": a["name"], "gemeinde": a["gem"]},
         "geometry": mapping(transform(nach_wgs, Point(a["x"], a["y"])))} for a in anlagen]},
        ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    umkreis = {r: unary_union([Point(a["x"], a["y"]).buffer(r) for a in anlagen]) for r in RADIEN}

    print("\nJe Gemeinde")
    je = {}
    kandidaten = []
    for gem in sorted({p["gemeinde"] for _, p, _ in alle if p["gemeinde"]}):
        st_ini = [g for g, p in ini if p["gemeinde"] == gem]
        st_gv = [g for g, p in gv if p["gemeinde"] == gem]
        u = unary_union(st_ini + st_gv)
        z = {"gemeinde": gem, "betroffen_km": round(u.length / 1000, 2),
             "initiative_km": round(unary_union(st_ini).length / 1000, 2) if st_ini else 0.0,
             "gegenvorschlag_km": round(unary_union(st_gv).length / 1000, 2) if st_gv else 0.0}
        for r in RADIEN:
            teil = u.intersection(umkreis[r])
            z[f"km{r}"] = round(teil.length / 1000, 2)
            z[f"p{r}"] = round(100 * teil.length / u.length) if u.length else 0.0
            if r in (100, 300):
                for t in (teil.geoms if hasattr(teil, "geoms") else [teil]):
                    if t.geom_type == "LineString" and t.length >= 5:
                        kandidaten.append((t, gem, r))
        n = collections.Counter(a["cat"] for a in anlagen if a["gem"] == gem)
        z["anlagen"] = "/".join(str(n[c]) for c in CAT_ORDER)
        z["linien"] = sum(1 for _, g_, _ in kandidaten if g_ == gem)
        z["quelle_anlagen"] = quelle_anlagen.split(" (")[0]
        je[gem] = z
        print(f"  {gem:24s} {z['betroffen_km']:6.2f} km  100 m {z['p100']:3.0f} %  300 m {z['p300']:3.0f} %  Anlagen {z['anlagen']}")

    total = {"gemeinde": "Kanton total", "betroffen_km": round(netz.length / 1000, 2),
             "initiative_km": round(unary_union([g for g, _ in ini]).length / 1000, 2),
             "gegenvorschlag_km": round(unary_union([g for g, _ in gv]).length / 1000, 2)}
    for r in RADIEN:
        l = netz.intersection(umkreis[r]).length
        total[f"km{r}"] = round(l / 1000, 2)
        total[f"p{r}"] = round(100 * l / netz.length)
    total["anlagen"] = "/".join(str(zaehl[c]) for c in CAT_ORDER)

    (FERTIG / "kandidaten_wgs84.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"g": gem, "r": r}, "geometry": mapping(transform(nach_wgs, t))}
        for t, gem, r in kandidaten]}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    print("\nKarten")
    GRAFIKEN.mkdir(parents=True, exist_ok=True)
    for gem, z in je.items():
        st_ini = [g for g, p in ini if p["gemeinde"] == gem]
        st_gv = [g for g, p in gv if p["gemeinde"] == gem]
        inner = innen_u.get(gem)
        if inner is None:
            continue
        svg = karte(gem, st_ini, st_gv, inner, kontext, anlagen, umkreis, z)
        (GRAFIKEN / f"karte_{slug(gem)}.svg").write_text(svg, encoding="utf-8")
    print(f"  {len(je)} Karten nach {GRAFIKEN.relative_to(VORLAGE)}")

    # ---- vorlage.json
    d = json.loads(DATEI.read_text(encoding="utf-8"), object_pairs_hook=collections.OrderedDict)
    d["karte"]["total"] = total
    d["karte"]["gemeinden"] = sorted(je.values(), key=lambda x: -x["betroffen_km"])
    d["karte"]["anlagen_total"] = (f"{len(anlagen)} Standorte, Quelle {quelle_anlagen}: {zaehl['schule']} Schulen, "
                                   f"{zaehl['kindergarten']} Kindergärten, {zaehl['altersheim']} Alters- und Pflegeheime, "
                                   f"{zaehl['sozial']} weitere Sozialeinrichtungen und Spitäler")
    d["karte"]["quellen"] = [q for q in d["karte"]["quellen"] if "Standorte sensibler" not in q["titel"]] + [
        {"titel": f"Standorte sensibler Nutzungen: {quelle_anlagen}" + ("" if gpkg.exists() else
                  " (amenity school, college, kindergarten, childcare, nursing_home, social_facility, hospital), via Overpass"),
         "art": "eigen"}]
    DATEI.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (FERTIG / "gemeinden.json").write_text(json.dumps({"total": total, "gemeinden": d["karte"]["gemeinden"]},
                                                      ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("eingetragen: karte.gemeinden, karte.total, karte.anlagen_total")
    return 0


def karte(gem, st_ini, st_gv, inner, kontext, anlagen, umkreis, z, W=1500, pad=46, header=74, footer=214):
    """Eine Gemeindekarte als SVG, Aufbau wie in der Uebergabe vom Juli 2026,
    neu mit beiden Vorlagen."""
    vo = st_ini + st_gv
    ref = unary_union(vo) if vo else inner
    facs = [a for a in anlagen if Point(a["x"], a["y"]).distance(ref) <= 560]
    parts = list(vo) + [Point(a["x"], a["y"]).buffer(320) for a in facs] or [inner]
    minx, miny, maxx, maxy = unary_union(parts).bounds
    mgx, mgy = max(130, (maxx - minx) * 0.05), max(130, (maxy - miny) * 0.05)
    minx -= mgx; maxx += mgx; miny -= mgy; maxy += mgy
    mw, mh = maxx - minx, maxy - miny
    scale = (W - 2 * pad) / mw
    mapH = mh * scale
    H = int(header + mapH + footer)
    X = lambda x: pad + (x - minx) * scale
    Y = lambda y: header + mapH - (y - miny) * scale
    el = []
    A = el.append
    esc = lambda t: (t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def path(geom, stroke, sw, dash="none", op=1.0):
        for g in (geom.geoms if geom.geom_type.startswith("Multi") else [geom]):
            if g.geom_type != "LineString" or g.is_empty:
                continue
            d = "M" + " L".join(f"{X(x):.1f},{Y(y):.1f}" for x, y in g.coords)
            A(f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" '
              f'stroke-linejoin="round" stroke-dasharray="{dash}" opacity="{op}"/>')

    def poly(geom, fill, stroke, sw, op=1.0):
        for g in (geom.geoms if geom.geom_type.startswith("Multi") else [geom]):
            if g.geom_type != "Polygon" or g.is_empty:
                continue
            ext = "M" + " L".join(f"{X(x):.1f},{Y(y):.1f}" for x, y in g.exterior.coords) + " Z"
            hs = "".join(" M" + " L".join(f"{X(x):.1f},{Y(y):.1f}" for x, y in r.coords) + " Z" for r in g.interiors)
            A(f'<path d="{ext}{hs}" fill="{fill}" fill-rule="evenodd" stroke="{stroke}" stroke-width="{sw}" opacity="{op}"/>')

    def txt(x, y, t, size=13, col=INK, anchor="start", weight="normal"):
        A(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{col}" text-anchor="{anchor}" '
          f'font-weight="{weight}">{esc(t)}</text>')

    def marker(cat, x, y, r=5.4):
        col = CAT[cat]["col"]
        if cat == "schule":
            A(f'<rect x="{x-r:.1f}" y="{y-r:.1f}" width="{2*r:.1f}" height="{2*r:.1f}" fill="{col}" stroke="#fff" stroke-width="1.3"/>')
        elif cat == "kindergarten":
            A(f'<polygon points="{x:.1f},{y-r-0.6:.1f} {x-r-0.4:.1f},{y+r-0.6:.1f} {x+r+0.4:.1f},{y+r-0.6:.1f}" fill="{col}" stroke="#fff" stroke-width="1.3"/>')
        elif cat == "altersheim":
            A(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{col}" stroke="#fff" stroke-width="1.3"/>')
        else:
            A(f'<polygon points="{x:.1f},{y-r-1:.1f} {x+r+1:.1f},{y:.1f} {x:.1f},{y+r+1:.1f} {x-r-1:.1f},{y:.1f}" fill="{col}" stroke="#fff" stroke-width="1.3"/>')

    A(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">')
    A(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>')
    A(f'<clipPath id="mp"><rect x="0" y="{header}" width="{W}" height="{mapH:.1f}"/></clipPath>')
    A('<g clip-path="url(#mp)">')
    poly(inner, INNER_FILL, INNER_STROKE, 1.0)
    view = box(minx, miny, maxx, maxy)
    for g in kontext:
        if g.intersects(view):
            path(g, ROAD_CTX, 1.5)
    facpts = {c: [Point(a["x"], a["y"]) for a in facs if a["cat"] == c] for c in CAT_ORDER}
    for r in (500, 300, 100):
        for c in CAT_ORDER:
            if not facpts[c]:
                continue
            u = unary_union([p.buffer(r) for p in facpts[c]])
            poly(u, CAT[c]["col"], "none", 0, op=FILLOP[r])
            if r == 100:
                path(u.boundary, CAT[c]["col"], 1.1, op=0.5)
    u = unary_union(vo) if vo else None
    if u is not None:
        hi3 = u.intersection(umkreis[300])
        if not hi3.is_empty:
            path(hi3, CAND300, 9.0, op=0.55)
        hi1 = u.intersection(umkreis[100])
        if not hi1.is_empty:
            path(hi1, CAND100, 11.0, op=0.9)
    for g in st_gv:
        path(g, ROAD_GV, 4.2)
    for g in st_ini:
        path(g, ROAD_INI, 2.4)
    for a in facs:
        marker(a["cat"], X(a["x"]), Y(a["y"]))
    A("</g>")
    disp = gem.replace(" (SH)", "")
    txt(pad, 34, f"{disp}: betroffene Strassen und Umkreise sensibler Nutzungen", 23, INK, "start", "bold")
    txt(pad, 56, "Rot: Gegenvorschlag (verkehrsorientierte Kantonsstrassen innerorts). Blau: Initiative "
                 "(Kantonsstrassen innerorts mit Bus). Umkreise 100, 300 und 500 m um Schulen, Kindergärten, "
                 "Alters-/Pflegeheime und weitere Sozialeinrichtungen.", 12.5, INK2)
    fy = header + mapH
    A(f'<line x1="0" y1="{fy:.1f}" x2="{W}" y2="{fy:.1f}" stroke="#e4e2da" stroke-width="1"/>')

    def leg_line(x, y, col, sw, label, w2=34, extra=None):
        A(f'<line x1="{x}" y1="{y-4:.1f}" x2="{x+w2}" y2="{y-4:.1f}" stroke="{col}" stroke-width="{sw}"/>')
        if extra:
            A(f'<line x1="{x}" y1="{y-4:.1f}" x2="{x+w2}" y2="{y-4:.1f}" stroke="{extra}" stroke-width="3"/>')
        txt(x + w2 + 8, y, label, 12, INK)
        return x + w2 + 8 + len(label) * 6.7 + 26

    yA = fy + 24
    x = pad
    x = leg_line(x, yA, ROAD_GV, 4.2, "Gegenvorschlag")
    x = leg_line(x, yA, ROAD_INI, 2.6, "Initiative")
    x = leg_line(x, yA, CAND100, 9, "Anlage in 100 m", 34, ROAD_GV)
    x = leg_line(x, yA, CAND300, 9, "Anlage in 300 m", 34, ROAD_GV)
    x = leg_line(x, yA, ROAD_CTX, 2.2, "übrige Kantonsstrasse")
    yB = fy + 50
    x = pad
    for c in CAT_ORDER:
        marker(c, x + 8, yB - 4)
        txt(x + 22, yB, CAT[c]["label"], 12, INK)
        x += 22 + len(CAT[c]["label"]) * 6.9 + 26
    yC = fy + 76
    x = pad
    for r in (100, 300, 500):
        A(f'<rect x="{x}" y="{yC-11:.1f}" width="15" height="12" fill="#6a51a3" opacity="{FILLOP[r]+0.02}"/>')
        x += 18
    txt(x + 4, yC, "Umkreis 100 / 300 / 500 m (zunehmend blasser)", 12, INK)
    yD = fy + 102
    km = lambda v: f"{v:.2f}".replace(".", ",")
    txt(pad, yD, f"Betroffen {km(z['betroffen_km'])} km (Gegenvorschlag {km(z['gegenvorschlag_km'])}, "
                 f"Initiative {km(z['initiative_km'])})  ·  in 100 m: {km(z['km100'])} km ({z['p100']:.0f} %)  ·  "
                 f"in 300 m: {km(z['km300'])} km ({z['p300']:.0f} %)  ·  in 500 m: {km(z['km500'])} km ({z['p500']:.0f} %)",
        12.5, INK, "start", "bold")
    sb = 500 * scale
    bx, by = pad, H - 16
    A(f'<line x1="{bx:.1f}" y1="{by:.1f}" x2="{bx+sb:.1f}" y2="{by:.1f}" stroke="{INK}" stroke-width="2"/>')
    A(f'<line x1="{bx:.1f}" y1="{by-4:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="{INK}" stroke-width="2"/>')
    A(f'<line x1="{bx+sb:.1f}" y1="{by-4:.1f}" x2="{bx+sb:.1f}" y2="{by:.1f}" stroke="{INK}" stroke-width="2"/>')
    txt(bx + sb + 8, by, "500 m", 11, INK2)
    txt(W - pad, by, "Strassen: Kantonsstrassen, Lärmkataster, Ortstafeln, Baugebiet (geo.sh.ch), Buslinien (OSM), "
                     "Haltestellen (BAV) · Anlagen: " + z.get("quelle_anlagen", "OpenStreetMap") + " · LV95", 9.5, MUTED, "end")
    A("</svg>")
    return "\n".join(el)


if __name__ == "__main__":
    sys.exit(main())

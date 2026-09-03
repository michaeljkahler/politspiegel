#!/usr/bin/env python3
"""Holt das Busnetz und die Bushaltestellen des Raums Schaffhausen neu.

Aufruf aus der Projektwurzel:
    python3 geo/skripte/busnetz_holen.py

Schreibt nach geo/daten/:
    busnetz_wgs84.geojson            Linienfuehrung, aus OpenStreetMap
    haltestellen_bus_lv95.json       Haltestellen in LV95, vom Bundesamt fuer Verkehr
    haltestellen_bus_wgs84.geojson   dieselben in WGS84 fuer den Viewer

Warum zwei Quellen: Die Haltestellen sind amtlich (BAV), haben aber keine
Linienfuehrung. Die Linienfuehrung ist betrieblich (OSM), dafuer vollstaendig.
Zusammen decken sie sich gegenseitig ab; das Skript rechnet die Gegenprobe am
Ende selber nach.

Braucht: requests, pyproj
Achtung: In der Anthropic-Sandbox sind Overpass und geo.sh.ch gesperrt. Dieses
Skript laeuft auf einem Rechner mit freiem Netz.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import requests
from pyproj import Transformer

WURZEL = Path(__file__).resolve().parent.parent.parent
ZIEL = WURZEL / "geo" / "daten"

# Kanton Schaffhausen und Umland
BBOX_WGS = (47.60, 8.40, 47.83, 8.90)          # Sued, West, Nord, Ost
BBOX_LV95 = (2675000, 1278000, 2709000, 1296000)
AUSSCHNITT = dict(lat0=47.63, lat1=47.82, lon0=8.44, lon1=8.90)

# Schweizer Betreiber. Suedbadenbus und Flixbus bleiben draussen.
BETREIBER_CH = {"VBSH", "PAG", "PAZ"}

OVERPASS = "https://overpass-api.de/api/interpreter"
GEOADMIN = "https://api3.geo.admin.ch/rest/services/all/MapServer/identify"

R = 6371000.0
RAD = math.pi / 180


# ------------------------------------------------------------------ Geometrie

def meter(a, b):
    """Abstand zweier Punkte [lon, lat] in Metern, lokal eben gerechnet."""
    dx = (b[0] - a[0]) * RAD * R * math.cos(a[1] * RAD)
    dy = (b[1] - a[1]) * RAD * R
    return math.hypot(dx, dy)


def laenge(linie):
    return sum(meter(linie[i - 1], linie[i]) for i in range(1, len(linie)))


def douglas_peucker(punkte, toleranz):
    if len(punkte) < 3:
        return punkte
    kx = RAD * R * math.cos(punkte[0][1] * RAD)
    ky = RAD * R
    ax, ay = punkte[0][0] * kx, punkte[0][1] * ky
    bx, by = punkte[-1][0] * kx, punkte[-1][1] * ky
    dx, dy = bx - ax, by - ay
    len2 = dx * dx + dy * dy
    groesst, index = 0.0, 0
    for i in range(1, len(punkte) - 1):
        px, py = punkte[i][0] * kx, punkte[i][1] * ky
        t = ((px - ax) * dx + (py - ay) * dy) / len2 if len2 else 0.0
        t = max(0.0, min(1.0, t))
        d = math.hypot(px - (ax + t * dx), py - (ay + t * dy))
        if d > groesst:
            groesst, index = d, i
    if groesst <= toleranz:
        return [punkte[0], punkte[-1]]
    return (douglas_peucker(punkte[:index + 1], toleranz)[:-1]
            + douglas_peucker(punkte[index:], toleranz))


def verketten(linien):
    """Zusammenhaengende Wegstuecke zu durchgehenden Linien verbinden."""
    def key(p):
        return f"{p[0]:.5f},{p[1]:.5f}"

    enden: dict[str, list[int]] = {}
    for i, l in enumerate(linien):
        for k in (key(l[0]), key(l[-1])):
            enden.setdefault(k, []).append(i)

    benutzt = [False] * len(linien)
    ketten = []
    for i in range(len(linien)):
        if benutzt[i]:
            continue
        benutzt[i] = True
        kette = list(linien[i])
        weiter = True
        while weiter:
            weiter = False
            for ende, wohin in ((key(kette[-1]), "hinten"), (key(kette[0]), "vorne")):
                for j in enden.get(ende, []):
                    if benutzt[j]:
                        continue
                    l = linien[j]
                    if key(l[0]) == ende:
                        stueck = l[1:]
                    elif key(l[-1]) == ende:
                        stueck = list(reversed(l[:-1]))
                    else:
                        continue
                    benutzt[j] = True
                    kette = kette + stueck if wohin == "hinten" else list(reversed(stueck)) + kette
                    weiter = True
                    break
                if weiter:
                    break
        ketten.append(kette)
    return ketten


# ------------------------------------------------------------------- Beziehen

def busnetz_holen():
    sued, west, nord, ost = BBOX_WGS
    abfrage = f"""[out:json][timeout:180];
(
  rel["type"="route"]["route"="bus"]["operator"~"VBSH|PostAuto|PAG|PAZ",i]({sued},{west},{nord},{ost});
  rel["type"="route"]["route"="bus"]["network"~"Ostwind|ZVV",i]({sued},{west},{nord},{ost});
);
out geom;"""
    antwort = requests.post(OVERPASS, data=abfrage.encode("utf-8"), timeout=300)
    antwort.raise_for_status()
    daten = antwort.json()

    wege: dict[int, list] = {}
    relationen = 0
    for e in daten.get("elements", []):
        if e.get("type") != "relation":
            continue
        if (e.get("tags") or {}).get("operator") not in BETREIBER_CH:
            continue
        relationen += 1
        for m in e.get("members", []):
            if m.get("type") == "way" and m.get("geometry") and m["ref"] not in wege:
                wege[m["ref"]] = [[round(p["lon"], 5), round(p["lat"], 5)] for p in m["geometry"]]

    a = AUSSCHNITT
    drin = [l for l in wege.values()
            if any(a["lat0"] < p[1] < a["lat1"] and a["lon0"] < p[0] < a["lon1"] for p in l)]
    ketten = verketten(drin)
    netz = [douglas_peucker(k, 10) for k in ketten]
    netz = [l for l in netz if len(l) > 1 and laenge(l) >= 15]
    print(f"Busnetz: {relationen} Linien, {len(netz)} Wegzuege, "
          f"{sum(laenge(l) for l in netz)/1000:.0f} km")
    return netz


def haltestellen_holen():
    x0, y0, x1, y1 = BBOX_LV95
    gefunden = {}
    for i in range(4):
        for j in range(3):
            bx0 = x0 + (x1 - x0) * i / 4
            bx1 = x0 + (x1 - x0) * (i + 1) / 4
            by0 = y0 + (y1 - y0) * j / 3
            by1 = y0 + (y1 - y0) * (j + 1) / 3
            bb = f"{bx0:.0f},{by0:.0f},{bx1:.0f},{by1:.0f}"
            r = requests.get(GEOADMIN, timeout=60, params={
                "geometry": bb, "geometryType": "esriGeometryEnvelope",
                "layers": "all:ch.bav.haltestellen-oev", "mapExtent": bb,
                "imageDisplay": "100,100,96", "tolerance": "0", "sr": "2056",
                "limit": "200", "returnGeometry": "true"})
            r.raise_for_status()
            for e in r.json().get("results", []):
                a = e.get("attributes") or {}
                pts = (e.get("geometry") or {}).get("points") or []
                if not pts or a.get("verkehrsmittel_de") != "Bus":
                    continue
                x, y = round(pts[0][0]), round(pts[0][1])
                gefunden[(a.get("name"), x, y)] = [a.get("name"), a.get("tuabkuerzung"), x, y]
    liste = sorted(gefunden.values(), key=lambda h: (h[0] or ""))
    print(f"Haltestellen: {len(liste)} Bushaltestellen")
    return liste


# ----------------------------------------------------------------- Gegenprobe

def gegenprobe(netz, halte_wgs, stichprobe=25):
    """Wie weit liegen die amtlichen Haltestellen von der OSM-Linienfuehrung weg?"""
    import random
    random.seed(1)
    probe = random.sample(halte_wgs, min(stichprobe, len(halte_wgs)))
    abstaende = []
    for pt in probe:
        best = float("inf")
        for l in netz:
            for i in range(1, len(l)):
                a, b = l[i - 1], l[i]
                kx = RAD * R * math.cos(a[1] * RAD)
                ky = RAD * R
                px, py = (pt[0] - a[0]) * kx, (pt[1] - a[1]) * ky
                dx, dy = (b[0] - a[0]) * kx, (b[1] - a[1]) * ky
                L = dx * dx + dy * dy
                t = max(0.0, min(1.0, (px * dx + py * dy) / L)) if L else 0.0
                best = min(best, math.hypot(px - t * dx, py - t * dy))
        abstaende.append(best)
    abstaende.sort()
    unter50 = sum(1 for d in abstaende if d < 50)
    print(f"Gegenprobe: Median {abstaende[len(abstaende)//2]:.0f} m, "
          f"{unter50} von {len(abstaende)} unter 50 m, groesster Abstand {abstaende[-1]:.0f} m")


def main() -> None:
    ZIEL.mkdir(parents=True, exist_ok=True)
    netz = busnetz_holen()
    halte = haltestellen_holen()

    (ZIEL / "busnetz_wgs84.geojson").write_text(json.dumps({
        "type": "FeatureCollection",
        "quelle": "OpenStreetMap, Buslinien-Relationen der Betreiber VBSH, PostAuto (PAG) und PAZ, "
                  "über Overpass. Wege zu durchgehenden Linien verkettet, Douglas-Peucker 10 m.",
        "hinweis": "Betriebliche Linienführung, nicht amtlich. Ändert mit jedem Fahrplanwechsel.",
        "features": [{"type": "Feature", "properties": {},
                      "geometry": {"type": "LineString", "coordinates": l}} for l in netz],
    }, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    (ZIEL / "haltestellen_bus_lv95.json").write_text(json.dumps({
        "quelle": "Bundesamt für Verkehr, Ebene ch.bav.haltestellen-oev, über die "
                  "identify-Schnittstelle von api3.geo.admin.ch",
        "filter": "verkehrsmittel_de = Bus, Perimeter Kanton Schaffhausen und Umgebung",
        "crs": "EPSG:2056",
        "felder": ["name", "transportunternehmen", "e_lv95", "n_lv95"],
        "hinweis": "Haltestellen sind nicht die Linienführung.",
        "haltestellen": halte,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    t = Transformer.from_crs("EPSG:2056", "EPSG:4326", always_xy=True)
    halte_wgs = []
    feats = []
    for name, tu, x, y in halte:
        lon, lat = t.transform(x, y)
        lon, lat = round(lon, 5), round(lat, 5)
        halte_wgs.append([lon, lat])
        feats.append({"type": "Feature", "properties": {"n": name, "tu": tu},
                      "geometry": {"type": "Point", "coordinates": [lon, lat]}})
    (ZIEL / "haltestellen_bus_wgs84.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": feats},
                   ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    gegenprobe(netz, halte_wgs)
    print(f"geschrieben nach {ZIEL}")


if __name__ == "__main__":
    main()

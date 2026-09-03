#!/usr/bin/env python3
"""Misst die Weglaenge der Buskurse entlang der Strassenachsen statt per Luftlinie.

Aufruf aus der Projektwurzel:
    python3 abstimmungsspiegel/abstimmungen/2026-09-27-verkehrsfluss/skripte/weglaenge_netz.py

Liest   geo/02_aufbereitet/busnetz_wgs84.geojson       Linienfuehrung aus OpenStreetMap
        geo/02_aufbereitet/haltestellen_bus_lv95.json  Haltestellen des Bundesamts fuer Verkehr
        scripts/kurse_fahrplan.py             Haltefolgen mit Fahrplanzeiten
Schreibt geo/02_aufbereitet/reisegeschwindigkeit.json

Warum nicht Luftlinie: Der erste Anlauf rechnete Luftlinie zwischen den Halten mal
einem gesetzten Umwegfaktor 1,2. Das Netz liegt aber vor, also wird der Weg
entlang der Achsen gesucht. Der Faktor wird damit gemessen statt gesetzt.

Verfahren: Aus den Linienzuegen wird ein Graph gebaut. Weil die Zuege beim
Verketten durch Knoten hindurch verschmolzen wurden, werden Punkte, die naeher
als TOLERANZ beieinander liegen, zum selben Knoten zusammengefasst; so entstehen
die Verzweigungen wieder. Jede Haltestelle wird auf den naechsten Knoten
gezogen, dann laeuft eine Dijkstra-Suche von Halt zu Halt.
"""

from __future__ import annotations

import heapq
import json
import math
from collections import defaultdict
from pathlib import Path

VORLAGE = Path(__file__).resolve().parent.parent
NETZ = VORLAGE / "geo" / "02_aufbereitet" / "busnetz_wgs84.geojson"
HALTE = VORLAGE / "geo" / "02_aufbereitet" / "haltestellen_bus_lv95.json"
ZIEL = VORLAGE / "geo" / "02_aufbereitet" / "reisegeschwindigkeit.json"

TOLERANZ = 6.0        # Meter, ab hier gelten zwei Punkte als derselbe Knoten
MAX_SNAP = 120.0      # Meter, weiter darf eine Haltestelle nicht vom Netz weg sein

R = 6371000.0
RAD = math.pi / 180


def m_pro_grad(lat: float) -> tuple[float, float]:
    return RAD * R * math.cos(lat * RAD), RAD * R


def abstand(a, b) -> float:
    kx, ky = m_pro_grad((a[1] + b[1]) / 2)
    return math.hypot((b[0] - a[0]) * kx, (b[1] - a[1]) * ky)


def graph_bauen(linien):
    """Punkte auf ein Raster von TOLERANZ ziehen, damit Verzweigungen wieder greifen."""
    kx, ky = m_pro_grad(47.7)
    def knoten(p):
        return (round(p[0] * kx / TOLERANZ), round(p[1] * ky / TOLERANZ))

    kanten = defaultdict(dict)
    lage = {}
    for linie in linien:
        for i in range(1, len(linie)):
            a, b = linie[i - 1], linie[i]
            ka, kb = knoten(a), knoten(b)
            lage.setdefault(ka, a)
            lage.setdefault(kb, b)
            if ka == kb:
                continue
            d = abstand(a, b)
            if d < kanten[ka].get(kb, math.inf):
                kanten[ka][kb] = d
                kanten[kb][ka] = d
    return kanten, lage


def naechster_knoten(punkt, lage):
    best, bestd = None, math.inf
    for k, p in lage.items():
        d = abstand(punkt, p)
        if d < bestd:
            best, bestd = k, d
    return best, bestd


def kuerzester_weg(kanten, start, ziel, obergrenze=8000.0):
    """Dijkstra mit Abbruch, sobald die Obergrenze ueberschritten ist."""
    if start == ziel:
        return 0.0
    dist = {start: 0.0}
    halde = [(0.0, start)]
    while halde:
        d, k = heapq.heappop(halde)
        if k == ziel:
            return d
        if d > dist.get(k, math.inf) or d > obergrenze:
            continue
        for nachbar, laenge in kanten[k].items():
            nd = d + laenge
            if nd < dist.get(nachbar, math.inf):
                dist[nachbar] = nd
                heapq.heappush(halde, (nd, nachbar))
    return None


def main() -> None:
    import sys
    sys.path.insert(0, str(VORLAGE / "scripts"))
    from kurse_fahrplan import KURSE

    netz = json.loads(NETZ.read_text(encoding="utf-8"))
    linien = [f["geometry"]["coordinates"] for f in netz["features"]]
    kanten, lage = graph_bauen(linien)
    print(f"Graph: {len(lage)} Knoten, {sum(len(v) for v in kanten.values())//2} Kanten")

    h = json.loads(HALTE.read_text(encoding="utf-8"))
    from pyproj import Transformer
    t = Transformer.from_crs("EPSG:2056", "EPSG:4326", always_xy=True)
    pos = {}
    for name, tu, x, y in h["haltestellen"]:
        lon, lat = t.transform(x, y)
        pos[name] = (lon, lat)

    # Haltestellen einmalig auf das Netz ziehen
    snap, snap_d = {}, {}
    for name, p in pos.items():
        k, d = naechster_knoten(p, lage)
        snap[name], snap_d[name] = k, d

    mi = lambda s: int(s[:2]) * 60 + int(s[3:])
    erg, warnungen = [], []
    for kurs, halte in KURSE.items():
        fehlt = [n for n, _ in halte if n not in pos]
        if fehlt:
            warnungen.append(f"{kurs}: Koordinate fehlt fuer {fehlt[:2]}")
            continue
        weit = [n for n, _ in halte if snap_d[n] > MAX_SNAP]
        netzweg, luft, luecken = 0.0, 0.0, []
        for i in range(1, len(halte)):
            a, b = halte[i - 1][0], halte[i][0]
            lu = abstand(pos[a], pos[b])
            luft += lu
            w = kuerzester_weg(kanten, snap[a], snap[b])
            if w is None or w > max(lu * 3.0, lu + 800):
                luecken.append(f"{a} → {b}")
                netzweg += lu * 1.2          # Rueckfall, klar vermerkt
            else:
                netzweg += w
        zeit = mi(halte[-1][1]) - mi(halte[0][1])
        erg.append(dict(
            kurs=kurs, halte=len(halte), minuten=zeit,
            weg_km=round(netzweg / 1000, 2),
            luftlinie_km=round(luft / 1000, 2),
            umwegfaktor=round(netzweg / luft, 3) if luft else None,
            v_kmh=round(netzweg / 1000 / (zeit / 60), 1),
            v_kmh_luftlinie=round(luft / 1000 / (zeit / 60), 1),
            abschnitte_ohne_netzweg=len(luecken),
            haltestellen_weit_vom_netz=weit,
        ))
        if luecken:
            warnungen.append(f"{kurs}: {len(luecken)} Abschnitte ohne Netzweg, "
                             f"z. B. {luecken[0]}")

    faktoren = [e["umwegfaktor"] for e in erg if e["umwegfaktor"]]
    mittel = sum(faktoren) / len(faktoren) if faktoren else None
    json.dump({
        "verfahren": "Weglaenge entlang der Buslinien-Achsen, Dijkstra von Halt zu Halt. "
                     f"Knoten zusammengefasst ab {TOLERANZ:.0f} m, Haltestellen auf den "
                     f"naechsten Knoten gezogen, hoechstens {MAX_SNAP:.0f} m.",
        "quelle": "Busnetz OpenStreetMap; Haltestellen ch.bav.haltestellen-oev; "
                  "Fahrplan transport.opendata.ch, Kurse vom 08.09.2026",
        "gemessener_umwegfaktor": round(mittel, 3) if mittel else None,
        "hinweis": "Fahrplanzeiten sind auf ganze Minuten gerundet; Werte je Abschnitt sind "
                   "darum unsicher, die Gesamtgeschwindigkeit je Kurs ist belastbar.",
        "warnungen": warnungen,
        "kurse": erg,
    }, open(ZIEL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"\n{'Kurs':<30}{'Netzweg':>10}{'Luftlinie':>11}{'Faktor':>8}{'v Netz':>9}{'v Luft':>9}")
    print("-" * 78)
    for e in erg:
        print(f"{e['kurs']:<30}{e['weg_km']:>8.2f} km{e['luftlinie_km']:>9.2f} km"
              f"{e['umwegfaktor']:>8.2f}{e['v_kmh']:>7.1f} km/h{e['v_kmh_luftlinie']:>7.1f} km/h")
    print("-" * 78)
    if mittel:
        print(f"Gemessener Umwegfaktor im Mittel: {mittel:.3f}  (gesetzt war 1,200)")
    for w in warnungen:
        print("  Hinweis:", w)
    print(f"\ngeschrieben: {ZIEL}")


if __name__ == "__main__":
    main()

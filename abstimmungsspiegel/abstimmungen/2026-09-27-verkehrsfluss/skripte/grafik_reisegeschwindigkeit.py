#!/usr/bin/env python3
"""Erzeugt die Grafik zur Reisegeschwindigkeit der Schaffhauser Buslinien.

Aufruf aus der Projektwurzel:
    python3 abstimmungsspiegel/abstimmungen/2026-09-27-verkehrsfluss/skripte/grafik_reisegeschwindigkeit.py

Liest  geo/02_aufbereitet/reisegeschwindigkeit.json
Schreibt  grafiken/E1_Reisegeschwindigkeit.svg

Kernaussage: Kein Kurs erreicht im Mittel 30 km/h. Bei Haltestellen alle rund
380 Meter ist ein Bus schon physikalisch auf etwa 34 km/h begrenzt, weil
Beschleunigen und Bremsen den Abschnitt aufbrauchen. Die Debatte ueber
"50 gegen 30" beschreibt fuer einen Stadtbus also einen Spielraum, den es so
gar nicht gibt.

Farben nach docs/DESIGN_entscheide.md: keine Ampel, Graphitrampe, jede Zahl
steht am Balken.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

VORLAGE = Path(__file__).resolve().parent.parent
QUELLE = VORLAGE / "geo" / "02_aufbereitet" / "reisegeschwindigkeit.json"
ZIEL = VORLAGE / "grafiken" / "E1_Reisegeschwindigkeit.svg"

# Farbtokens, gleich wie im Abstimmungsspiegel
GRUND, TEXT, LEISE, LINIE = "#f7f8fa", "#12161c", "#5a626d", "#e2e6eb"
BALKEN, MARKE = "#3c4652", "#8b93a1"

BREITE, ZEILE = 1000, 30
RAND_L, RAND_R, RAND_O = 250, 130, 158
VMAX = 55.0


def fahrzeit(strecke_m: float, vmax_kmh: float, a: float = 1.0, b: float = 1.2) -> float:
    """Fahrzeit ueber einen Abschnitt mit Beschleunigen, Konstantfahrt, Bremsen."""
    v = vmax_kmh / 3.6
    bremsweg = v * v / (2 * a) + v * v / (2 * b)
    if bremsweg >= strecke_m:
        vs = math.sqrt(2 * strecke_m * a * b / (a + b))
        return vs / a + vs / b
    return v / a + v / b + (strecke_m - bremsweg) / v


def e(t) -> str:
    return (str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def bauen() -> str:
    d = json.loads(QUELLE.read_text(encoding="utf-8"))
    kurse = sorted(d["kurse"], key=lambda k: k["v_kmh"])
    n = len(kurse)
    EINORDNUNG = [
        "Alle sieben Stadtlinien in beiden Richtungen. Samt Haltezeit erreicht kein Kurs 30 km/h:",
        "15,9 bis 24,1, im Mittel 19,6.",
        "Ohne Haltezeit, mit 12 Sekunden je Halt, liegen 12 der 14 Kurse weiterhin unter 30.",
        "Nur die Auswärtsrichtungen der Linien 5 und 7 kommen mit 31,3 und 30,3 knapp darüber.",
        "Bei Haltestellen alle {abst} Meter sind ohnehin höchstens rund {vphys} km/h möglich,",
        "weil Beschleunigen und Bremsen den Abschnitt aufbrauchen. Tempo 30 kostet also etwas,",
        "aber nur auf wenigen Abschnitten und viel weniger, als die Spanne 50 zu 30 nahelegt.",
    ]
    kasten = 40 + len(EINORDNUNG) * 18
    hoehe = RAND_O + n * ZEILE - 6 + 66 + kasten + 56
    x = lambda v: RAND_L + (BREITE - RAND_L - RAND_R) * v / VMAX

    t = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {BREITE} {hoehe}" '
         f'width="{BREITE}" height="{hoehe}" font-family="Public Sans, Helvetica, Arial, sans-serif">',
         f'<rect width="{BREITE}" height="{hoehe}" fill="{GRUND}"/>',
         f'<text x="40" y="52" font-size="27" font-weight="700" fill="{TEXT}" '
         f'font-family="Archivo, Helvetica, Arial, sans-serif">'
         f'Wie schnell sind die Schaffhauser Busse wirklich?</text>',
         f'<text x="40" y="80" font-size="15" fill="{LEISE}">Dunkel die Reisegeschwindigkeit '
         f'samt Haltezeit, hell die reine Fahrgeschwindigkeit ohne Halte.</text>',
         f'<text x="40" y="101" font-size="13" fill="{LEISE}">Fahrplan vom 8. September 2026, '
         f'Haltestellen des Bundesamts für Verkehr, Weglänge entlang der Strassenachsen '
         f'aus OpenStreetMap.</text>']

    # Achse
    for v in range(0, int(VMAX) + 1, 10):
        t.append(f'<line x1="{x(v):.1f}" y1="{RAND_O - 16}" x2="{x(v):.1f}" '
                 f'y2="{RAND_O + n * ZEILE - 6}" stroke="{LINIE}" stroke-width="1"/>')
        t.append(f'<text x="{x(v):.1f}" y="{RAND_O - 24}" font-size="12" fill="{LEISE}" '
                 f'text-anchor="middle">{v}</text>')
    t.append(f'<text x="{x(VMAX):.1f}" y="{RAND_O - 46}" font-size="12" fill="{LEISE}" '
             f'text-anchor="end">km/h</text>')

    # Referenzlinien: signalisiert 50, signalisiert 30, physikalisch erreichbar
    abst = sum(k["weg_km"] * 1000 / (k["halte"] - 1) for k in kurse) / n
    v_phys = abst / fahrzeit(abst, 50) * 3.6
    unten = RAND_O + n * ZEILE - 6
    for v, stil in ((50, "4 4"), (30, "4 4"), (v_phys, "")):
        strich = f' stroke-dasharray="{stil}"' if stil else ""
        farbe = MARKE if stil else TEXT
        breite = 1.5 if stil else 2
        t.append(f'<line x1="{x(v):.1f}" y1="{RAND_O - 16}" x2="{x(v):.1f}" y2="{unten}" '
                 f'stroke="{farbe}" stroke-width="{breite}"{strich}/>')
    t.append(f'<text x="{x(50):.1f}" y="{unten + 20}" font-size="12.5" fill="{LEISE}" '
             f'text-anchor="middle">signalisiert 50</text>')
    t.append(f'<text x="{x(30):.1f}" y="{unten + 20}" font-size="12.5" fill="{LEISE}" '
             f'text-anchor="middle">signalisiert 30</text>')
    t.append(f'<text x="{x(v_phys):.1f}" y="{unten + 40}" font-size="12.5" fill="{TEXT}" '
             f'text-anchor="middle" font-weight="600">physikalisch erreichbar {v_phys:.0f}</text>')

    # Balken: hell die Fahrgeschwindigkeit, darauf dunkel die Reisegeschwindigkeit
    for i, k in enumerate(kurse):
        y = RAND_O + i * ZEILE
        vf = k.get("v_fahrt_kmh", k["v_kmh"])
        t.append(f'<text x="{RAND_L - 12}" y="{y + 14}" font-size="13" fill="{TEXT}" '
                 f'text-anchor="end">{e(k["kurs"])}</text>')
        t.append(f'<rect x="{RAND_L}" y="{y + 3}" width="{x(vf) - RAND_L:.1f}" height="15" '
                 f'rx="3" fill="{MARKE}" fill-opacity="0.45"/>')
        t.append(f'<rect x="{RAND_L}" y="{y + 3}" width="{x(k["v_kmh"]) - RAND_L:.1f}" height="15" '
                 f'rx="3" fill="{BALKEN}"/>')
        t.append(f'<text x="{x(vf) + 8:.1f}" y="{y + 15}" font-size="12.5" '
                 f'font-weight="600" fill="{TEXT}" '
                 f'font-family="Archivo, Helvetica, Arial, sans-serif">'
                 f'{str(k["v_kmh"]).replace(".", ",")} / '
                 f'{str(round(vf,1)).replace(".", ",")}</text>')

    # Einordnung
    ey = unten + 66
    zeilen = [z.format(abst=f"{abst:.0f}", vphys=f"{v_phys:.0f}") for z in EINORDNUNG]
    t.append(f'<rect x="40" y="{ey}" width="{BREITE - 80}" height="{kasten}" rx="10" '
             f'fill="none" stroke="{LINIE}"/>')
    t.append(f'<text x="60" y="{ey + 25}" font-size="14" font-weight="700" fill="{TEXT}" '
             f'font-family="Archivo, Helvetica, Arial, sans-serif">Einordnung</text>')
    for j, satz in enumerate(zeilen):
        t.append(f'<text x="60" y="{ey + 46 + j * 18}" font-size="13" fill="{LEISE}">'
                 f'{e(satz)}</text>')

    for j, z in enumerate([
        "Quellen: transport.opendata.ch, ch.bav.haltestellen-oev, OpenStreetMap. Fahrdynamik "
        "1,0 und 1,2 m/s². Haltezeit 12 s je Halt, aus den Daten hergeleitet: höhere Werte",
        "ergäben für die schnellsten Kurse eine physikalisch unmögliche Fahrgeschwindigkeit. "
        "Von 246 Abschnitten liessen sich 79 nicht über das Netz führen, dort Luftlinie mal 1,2. "
        "Eigene Auswertung, ohne Gewähr."]):
        t.append(f'<text x="40" y="{hoehe - 30 + j * 15}" font-size="11" fill="{LEISE}">'
                 f'{e(z)}</text>')
    t.append("</svg>")
    return "\n".join(t)


def main() -> None:
    ZIEL.parent.mkdir(parents=True, exist_ok=True)
    ZIEL.write_text(bauen(), encoding="utf-8")
    print(f"geschrieben: {ZIEL} ({ZIEL.stat().st_size/1024:.0f} kB)")


if __name__ == "__main__":
    main()

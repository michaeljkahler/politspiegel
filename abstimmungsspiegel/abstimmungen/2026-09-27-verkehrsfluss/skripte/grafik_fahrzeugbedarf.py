#!/usr/bin/env python3
"""Erzeugt die Grafik zum Fahrzeugbedarf: braucht Tempo 30 einen zusaetzlichen Bus?

Aufruf aus der Projektwurzel:
    python3 abstimmungsspiegel/abstimmungen/2026-09-27-verkehrsfluss/skripte/grafik_fahrzeugbedarf.py

Liest    geo/02_aufbereitet/umlaufrechnung.json
Schreibt grafiken/E2_Fahrzeugbedarf.svg

Der Fahrzeugbedarf ist eine Treppenfunktion. Solange die Zusatzzeit in die
Wendezeit passt, kostet sie nichts. Ueberschreitet sie die Schwelle, springt der
Bedarf um ein ganzes Fahrzeug samt Personal. Die Grafik zeigt je Linie, wie viel
Wendezeit vorhanden ist, wie viel Tempo 30 davon frisst und wie viel Wendezeit
mindestens bleiben muss.

Zwei Modelle als Bandbreite, weil sich die Zusatzzeit nicht exakt bestimmen laesst:
  physikalisch  nur wo der Bus heute schneller faehrt als Tempo 30 zulaesst
  ASTRA         20 Sekunden je Kilometer betroffener Strecke, Forschungsbericht 1663
"""

from __future__ import annotations

import json
from pathlib import Path

VORLAGE = Path(__file__).resolve().parent.parent
QUELLE = VORLAGE / "geo" / "02_aufbereitet" / "umlaufrechnung.json"
ZIEL = VORLAGE / "grafiken" / "E2_Fahrzeugbedarf.svg"

GRUND, TEXT, LEISE, LINIE = "#f7f8fa", "#12161c", "#5a626d", "#e2e6eb"
RESERVE, VERBRAUCH, SCHWELLE = "#c3c9d2", "#3c4652", "#12161c"

BREITE, ZEILE = 1000, 46
RAND_L, RAND_R, RAND_O = 168, 300, 172


def e(t) -> str:
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def bauen() -> str:
    d = json.loads(QUELLE.read_text(encoding="utf-8"))
    linien = [x for x in d["linien"] if x["taktprobe"]]
    raus = [x for x in d["linien"] if not x["taktprobe"]]
    n = len(linien)
    vmax = max(x["reserve_min"] for x in linien) * 1.08

    EINORDNUNG = [
        "Der Fahrzeugbedarf ist eine Treppenfunktion: Solange die Zusatzzeit in die Wendezeit",
        "passt, kostet sie nichts. Reicht die Wendezeit nicht mehr, braucht es ein ganzes",
        "Fahrzeug samt Personal.",
        "Nach dem physikalischen Modell braucht keine Linie ein zusätzliches Fahrzeug, weil vier",
        "der sechs schon heute langsamer fahren, als Tempo 30 zuliesse. Nach dem ASTRA-Richtwert",
        "kippt Linie 1: ihre 5 Minuten Reserve reichen nach Abzug von 3,4 nicht mehr für die",
        "2 Minuten, die in Neuhausen Herbstäcker planmässig gewendet werden.",
        "Die ehrliche Antwort lautet damit: null bis ein zusätzliches Fahrzeug.",
    ]
    kasten = 40 + len(EINORDNUNG) * 18
    hoehe = RAND_O + n * ZEILE + 40 + kasten + 68
    x = lambda v: RAND_L + (BREITE - RAND_L - RAND_R) * v / vmax

    t = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {BREITE} {hoehe}" '
         f'width="{BREITE}" height="{hoehe}" font-family="Public Sans, Helvetica, Arial, sans-serif">',
         f'<rect width="{BREITE}" height="{hoehe}" fill="{GRUND}"/>',
         f'<text x="40" y="52" font-size="27" font-weight="700" fill="{TEXT}" '
         f'font-family="Archivo, Helvetica, Arial, sans-serif">'
         f'Braucht Tempo 30 einen zusätzlichen Bus?</text>',
         f'<text x="40" y="80" font-size="15" fill="{LEISE}">Wendezeit je Umlauf: was vorhanden '
         f'ist, was Tempo 30 davon braucht, was mindestens bleiben muss.</text>',
         f'<text x="40" y="101" font-size="13" fill="{LEISE}">Fahrzeiten, Wendezeiten und Takt '
         f'aus dem Fahrplan vom 8. September 2026, alles gemessen statt angenommen.</text>']

    # Legende
    lx = 40
    for farbe, txt in ((RESERVE, "vorhandene Wendezeit"), (VERBRAUCH, "Tempo 30 nach ASTRA"),
                       (SCHWELLE, "nötige Mindestwende")):
        if txt.startswith("nötige"):
            t.append(f'<line x1="{lx}" y1="{RAND_O - 34}" x2="{lx}" y2="{RAND_O - 22}" '
                     f'stroke="{SCHWELLE}" stroke-width="3"/>')
            lx += 10
        else:
            t.append(f'<rect x="{lx}" y="{RAND_O - 34}" width="16" height="12" rx="2" fill="{farbe}"/>')
            lx += 22
        t.append(f'<text x="{lx}" y="{RAND_O - 24}" font-size="12.5" fill="{LEISE}">{e(txt)}</text>')
        lx += len(txt) * 6.6 + 26

    for v in range(0, int(vmax) + 1, 2):
        t.append(f'<line x1="{x(v):.1f}" y1="{RAND_O - 4}" x2="{x(v):.1f}" '
                 f'y2="{RAND_O + n * ZEILE - 12}" stroke="{LINIE}" stroke-width="1"/>')
        t.append(f'<text x="{x(v):.1f}" y="{RAND_O + n * ZEILE + 4}" font-size="11" '
                 f'fill="{LEISE}" text-anchor="middle">{v}</text>')
    t.append(f'<text x="{x(vmax):.1f}" y="{RAND_O + n * ZEILE + 4}" font-size="11" '
             f'fill="{LEISE}" text-anchor="start"> Minuten</text>')

    for i, k in enumerate(linien):
        y = RAND_O + i * ZEILE
        res, za, zp = k["reserve_min"], k["zusatz_astra_min"], k["zusatz_physik_min"]
        kippt = k["fahrzeuge_astra"] > k["fahrzeuge"]

        t.append(f'<text x="{RAND_L - 14}" y="{y + 17}" font-size="15" fill="{TEXT}" '
                 f'text-anchor="end" font-family="Archivo, Helvetica, Arial, sans-serif" '
                 f'font-weight="600">Linie {e(k["linie"])}</text>')
        t.append(f'<text x="{RAND_L - 14}" y="{y + 32}" font-size="11.5" fill="{LEISE}" '
                 f'text-anchor="end">{k["fahrzeuge"]} Fahrzeuge, {k["takt_min"]}-Min-Takt</text>')

        # vorhandene Wendezeit
        t.append(f'<rect x="{RAND_L}" y="{y + 6}" width="{x(res) - RAND_L:.1f}" height="20" '
                 f'rx="3" fill="{RESERVE}"/>')
        # was Tempo 30 davon braucht, ASTRA als der ungünstigere Fall
        t.append(f'<rect x="{RAND_L}" y="{y + 6}" width="{x(za) - RAND_L:.1f}" height="20" '
                 f'rx="3" fill="{VERBRAUCH}"/>')
        # physikalisches Modell als schmaler Strich darin
        if zp > 0:
            t.append(f'<line x1="{x(zp):.1f}" y1="{y + 6}" x2="{x(zp):.1f}" y2="{y + 26}" '
                     f'stroke="{GRUND}" stroke-width="2" stroke-dasharray="3 2"/>')
        # Mindestwende, vom rechten Ende der Reserve her gemessen
        mw = k["wende_min_beobachtet"]
        if mw > 0:
            t.append(f'<line x1="{x(res - mw):.1f}" y1="{y + 2}" x2="{x(res - mw):.1f}" '
                     f'y2="{y + 30}" stroke="{SCHWELLE}" stroke-width="3"/>')

        rest = res - za
        txt = (f'{res} vorhanden, {str(za).replace(".", ",")} gebraucht, '
               f'{str(round(rest, 1)).replace(".", ",")} bleiben')
        t.append(f'<text x="{x(res) + 12:.1f}" y="{y + 14}" font-size="12" fill="{TEXT}">'
                 f'{e(txt)}</text>')
        t.append(f'<text x="{x(res) + 12:.1f}" y="{y + 29}" font-size="12" '
                 f'fill="{TEXT if kippt else LEISE}" '
                 f'font-weight="{700 if kippt else 400}">'
                 f'{"zusätzliches Fahrzeug nötig" if kippt else "reicht aus"}</text>')

    ey = RAND_O + n * ZEILE + 24
    t.append(f'<rect x="40" y="{ey}" width="{BREITE - 80}" height="{kasten}" rx="10" '
             f'fill="none" stroke="{LINIE}"/>')
    t.append(f'<text x="60" y="{ey + 25}" font-size="14" font-weight="700" fill="{TEXT}" '
             f'font-family="Archivo, Helvetica, Arial, sans-serif">Einordnung</text>')
    for j, satz in enumerate(EINORDNUNG):
        t.append(f'<text x="60" y="{ey + 46 + j * 18}" font-size="13" fill="{LEISE}">'
                 f'{e(satz)}</text>')

    fuss = [
        'Quellen: Fahrplan transport.opendata.ch, Kurse vom 08.09.2026. Zusatzzeit physikalisch aus '
        'Haltestellenabstand und Fahrdynamik,',
        'oder nach ASTRA-Forschungsbericht 1663 mit 20 s je km. Nicht dargestellt: '
        + (', '.join(f'Linie {x["linie"]}' for x in raus) or 'keine')
        + ' (Taktprobe nicht bestanden) und die Regionallinien 21 bis 25',
        'mit mehreren Ästen. Eigene Auswertung, ohne Gewähr.',
    ]
    for j, z in enumerate(fuss):
        t.append(f'<text x="40" y="{hoehe - 44 + j * 15}" font-size="11" fill="{LEISE}">'
                 f'{e(z)}</text>')
    t.append("</svg>")
    return "\n".join(t)


def main() -> None:
    ZIEL.parent.mkdir(parents=True, exist_ok=True)
    ZIEL.write_text(bauen(), encoding="utf-8")
    print(f"geschrieben: {ZIEL} ({ZIEL.stat().st_size/1024:.0f} kB)")


if __name__ == "__main__":
    main()

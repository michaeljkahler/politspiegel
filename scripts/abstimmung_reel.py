#!/usr/bin/env python3
"""
Reel des Abstimmungsspiegels aus den Social-Media-Bildern
=========================================================
Setzt Bilder aus site/social/abstimmung/<slug>/ (1080 x 1350, gezeichnet von
abstimmung_social.py) in ein Hochformat 1080 x 1920: Kopf mit Ebene und Datum,
darunter das Bild in voller Breite, unten die Adresse. Am Schluss eine Tafel mit
der Adresse. Diashow mit eigener Tonspur wie die Kantonsrat-Reels (social.video,
scripts/ton.py), keine fremde Musik.

Ausführen:
    python3 scripts/abstimmung_reel.py --aus site/social/abstimmung/2026-11-29/reel-spitalgesetz.mp4 \
        --kopf "Kanton Schaffhausen" --datum 2026-11-29 \
        --adresse michaeljkahler.github.io/politspiegel/abstimmung/2026-11-29-spitalgesetz/ \
        2026-11-29-spitalgesetz/vorlage.png:7 2026-11-29-spitalgesetz/kantonsrat.png:4 …
Pfade der Bilder relativ zu site/social/abstimmung/, Sekunden nach dem Doppelpunkt.
"""
import argparse
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from social import REEL, absatz, font, video  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
QUELLE = ROOT / "site" / "social" / "abstimmung"
WEISS, TINTE, TINTE2, TINTE3, LINIE = "#FFFFFF", "#111827", "#374151", "#6B7280", "#E5E7EB"
MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
          "September", "Oktober", "November", "Dezember"]


def lang(iso):
    j, m, t = iso.split("-")
    return f"{int(t)}. {MONATE[int(m) - 1]} {j}"


def rahmen(bild, kopf, datum, adresse):
    W, H = REEL
    img = Image.new("RGB", REEL, WEISS)
    d = ImageDraw.Draw(img)
    d.text((72, 110), f"Abstimmung vom {lang(datum)}", font=font("a", 50, "Bold"), fill=TINTE)
    d.text((72, 182), kopf, font=font("p", 34, "Regular"), fill=TINTE3)
    karte = Image.open(bild).convert("RGB")
    if karte.size != (1080, 1350):
        karte = karte.resize((1080, 1350))
    img.paste(karte, (0, 285))
    d.line((72, 1660, W - 72, 1660), fill=LINIE, width=2)
    d.text((72, 1700), "Alle Argumente und die Prüfung:", font=font("p", 30, "Regular"), fill=TINTE3)
    d.text((72, 1748), adresse, font=font("a", 32, "SemiBold"), fill=TINTE)
    return img


def schluss(kopf, datum, adresse, zeilen):
    W, H = REEL
    img = Image.new("RGB", REEL, WEISS)
    d = ImageDraw.Draw(img)
    y = 640
    d.text((72, y), f"Abstimmung vom {lang(datum)}", font=font("a", 56, "Bold"), fill=TINTE)
    y += 90
    d.text((72, y), kopf, font=font("p", 34, "Regular"), fill=TINTE3)
    y += 90
    for z in zeilen:
        y = absatz(d, (72, y), z, font("p", 34, "Regular"), TINTE2, W - 144, 46) + 18
    y += 40
    d.text((72, y), adresse, font=font("a", 34, "SemiBold"), fill=TINTE)
    y += 70
    d.text((72, y), "Politspiegel Schaffhausen · privates, nichtkommerzielles Projekt",
           font=font("p", 24, "Regular"), fill=TINTE3)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aus", required=True)
    ap.add_argument("--kopf", required=True)
    ap.add_argument("--datum", required=True)
    ap.add_argument("--adresse", required=True)
    ap.add_argument("--schluss", action="append", default=[], help="Zeile der Schlusstafel, mehrfach")
    ap.add_argument("bilder", nargs="+", help="pfad.png:sekunden")
    a = ap.parse_args()
    tmp = Path(tempfile.mkdtemp())
    pfade, dauern = [], []
    for i, eintrag in enumerate(a.bilder):
        pfad, sek = eintrag.rsplit(":", 1)
        ziel = tmp / f"{i:02d}.png"
        rahmen(QUELLE / pfad, a.kopf, a.datum, a.adresse).save(ziel)
        pfade.append(ziel)
        dauern.append(float(sek))
    ziel = tmp / "99.png"
    schluss(a.kopf, a.datum, a.adresse, a.schluss).save(ziel)
    pfade.append(ziel)
    dauern.append(3.5)
    aus = ROOT / a.aus
    aus.parent.mkdir(parents=True, exist_ok=True)
    if video(pfade, dauern, aus):
        print(f"{aus.relative_to(ROOT)}: {len(pfade)} Bilder, {sum(dauern):.1f} s")
    else:
        raise SystemExit("Video nicht erzeugt")


if __name__ == "__main__":
    main()

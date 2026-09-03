#!/usr/bin/env python3
"""
Profilbild und Titelbilder für die Social-Media-Konten
======================================================
Aus dem Zeichen des Politspiegels (drei Balken in den Abstimmungsfarben, wie
site/favicon.svg) entstehen:

  site/social/profil/profilbild.png       1080 x 1080, Zeichen mittig, tauglich für runden Zuschnitt
  site/social/profil/titelbild-facebook.png   1640 x 624
  site/social/profil/titelbild-youtube.png    2560 x 1440, Inhalt in der sicheren Mitte 1546 x 423
  site/social/profil/titelbild-x.png          1500 x 500 (auch für LinkedIn/Bluesky brauchbar)

Ausführen: python3 scripts/profilbilder.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "scripts" / "assets" / "fonts"
AUS = ROOT / "site" / "social" / "profil"

GRUND = "#171E27"
JA, NEIN, ENTH = "#3FB3A8", "#C08AD8", "#8B93A1"
WEISS = "#FFFFFF"
LEISE = "#A9B1BE"


def font(art, groesse, gewicht):
    f = ImageFont.truetype(str(FONTS / ("Archivo.ttf" if art == "a" else "PublicSans.ttf")), groesse)
    f.set_variation_by_name(gewicht)
    return f


def zeichen(d, cx, cy, s):
    """Die drei Balken aus favicon.svg (64er-Raster), skaliert mit s, um (cx, cy)."""
    for x, y, w, h, farbe in ((10.2, 27.6, 9.0, 26.2, JA), (27.5, 10.2, 9.0, 43.6, NEIN),
                              (44.8, 38.9, 9.0, 14.9, ENTH)):
        x0 = cx + (x - 32) * s
        y0 = cy + (y - 32) * s
        d.rounded_rectangle((x0, y0, x0 + w * s, y0 + h * s), radius=3.2 * s, fill=farbe)


def profilbild():
    W = 1080
    img = Image.new("RGB", (W, W), GRUND)
    d = ImageDraw.Draw(img)
    # Das Zeichen füllt rund 60 % der Breite: bleibt im runden Zuschnitt ganz sichtbar.
    zeichen(d, W / 2, W / 2, W * 0.60 / 44)
    return img


def passend(d, text, art, gewicht, max_b, start):
    g = start
    while g > 10 and d.textlength(text, font=font(art, g, gewicht)) > max_b:
        g -= 2
    return font(art, g, gewicht), g


def titelbild(W, H, sicher=None):
    """Wortmarke links in zwei Zeilen, Satz darunter, Zeichen rechts; alles in der sicheren Fläche."""
    img = Image.new("RGB", (W, H), GRUND)
    d = ImageDraw.Draw(img)
    sx0, sy0, sx1, sy1 = sicher or (0, 0, W, H)
    sh = sy1 - sy0
    rand = sh * 0.14
    z_s = sh * 0.66 / 44                      # Massstab des Zeichens
    z_b = 44 * z_s                            # dessen Breite
    x = sx0 + rand
    text_b = (sx1 - rand - z_b - rand) - x    # Breite für den Text
    fa, g = passend(d, "Schaffhausen", "a", "Bold", text_b, int(sh * 0.30))
    fp, k = passend(d, "Wie der Kantonsrat abstimmt, und was bei der nächsten", "p", "Regular", text_b, int(sh * 0.10))
    zh = g * 1.05
    gesamt = 2 * zh + k * 1.3 * 2 + sh * 0.04
    y = (sy0 + sy1) / 2 - gesamt / 2
    d.text((x, y), "Politspiegel", font=fa, fill=WEISS)
    d.text((x, y + zh), "Schaffhausen", font=fa, fill=WEISS)
    y += 2 * zh + sh * 0.04
    d.text((x, y), "Wie der Kantonsrat abstimmt, und was bei der nächsten", font=fp, fill=LEISE)
    d.text((x, y + k * 1.3), "Abstimmung auf dem Zettel steht.", font=fp, fill=LEISE)
    zeichen(d, sx1 - rand - z_b / 2, (sy0 + sy1) / 2, z_s)
    return img


def main():
    AUS.mkdir(parents=True, exist_ok=True)
    profilbild().save(AUS / "profilbild.png", optimize=True)
    titelbild(1640, 624, (120, 80, 1520, 544)).save(AUS / "titelbild-facebook.png", optimize=True)
    titelbild(2560, 1440, (507, 508, 2053, 931)).save(AUS / "titelbild-youtube.png", optimize=True)
    titelbild(1500, 500, (80, 60, 1420, 440)).save(AUS / "titelbild-x.png", optimize=True)
    for p in sorted(AUS.glob("*.png")):
        print(f"  {p.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

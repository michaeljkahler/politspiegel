#!/usr/bin/env python3
"""
Datenreels zum Abstimmungsspiegel: animierte 9:16-Videos aus den Geo- und
Zahlendaten einer Vorlage, nicht aus den Standbildern.

  ueberflug   Kamerafahrt über die graue Landeskarte (swisstopo) mit den
              Strassen, die Initiative (blau) und Gegenvorschlag (rot)
              erfassen; Halt in den Gemeinden mit Kilometern und Anwohnern.
  zeitstrahl  Fussgängerunfälle 2011 bis 2025 (ASTRA): Schweiz, die grossen
              Städte, Kanton Schaffhausen. Balken wachsen Jahr für Jahr.

Ausgabe: site/social/abstimmung/<slug>/reel-<name>.mp4 (1080 x 1920, 30 fps,
H.264, Tonspur aus scripts/ton.py) und ein Deckbild reel-<name>.png.

Kartengrundlage: swisstopo Pixelkarte grau über den WMTS-Dienst
(wmts.geo.admin.ch), offene Verwaltungsdaten des Bundes, Quellenangabe
«© swisstopo» im Bild. Kacheln werden unter ~/.cache/swisstopo abgelegt.

Ausführen:
    python3 scripts/datenreel.py 2026-09-27-verkehrsfluss ueberflug
    python3 scripts/datenreel.py 2026-09-27-verkehrsfluss zeitstrahl
    python3 scripts/datenreel.py 2026-09-27-verkehrsfluss alle
"""
import json
import math
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ton import tonspur  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "scripts" / "assets" / "fonts"
W, H = 1080, 1920
FPS = 30
INI, GV = "#1D4ED8", "#DC2626"          # wie auf der Seite (--geo-ini, --geo-gv)
TEXT, TEXT2, TEXT3 = "#111827", "#4B5563", "#6B7280"
GRUND = "#F6F7F9"
KARTE = "#FFFFFF"
LINIE = "#E5E7EB"
SEITE_KURZ = "michaeljkahler.github.io/politspiegel"

_fonts = {}


def font(art, groesse, gewicht="Regular"):
    k = (art, groesse, gewicht)
    if k not in _fonts:
        f = ImageFont.truetype(str(FONTS / ("Archivo.ttf" if art == "a" else "PublicSans.ttf")), groesse)
        try:
            f.set_variation_by_name(gewicht)
        except Exception:
            pass
        _fonts[k] = f
    return _fonts[k]


def ease(t):
    """Weiche Kamera: langsam anfahren, langsam ankommen."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def umbrechen(d, text, f, max_b):
    zeilen, akt = [], ""
    for w in text.split():
        probe = (akt + " " + w).strip()
        if d.textlength(probe, font=f) <= max_b:
            akt = probe
        else:
            zeilen.append(akt)
            akt = w
    if akt:
        zeilen.append(akt)
    return zeilen


def kasten(img, box, fill=(255, 255, 255, 235), radius=18):
    """Halbtransparenter Kasten für Text über der Karte."""
    ebene = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(ebene).rounded_rectangle(box, radius=radius, fill=fill)
    img.alpha_composite(ebene)


# ── Video schreiben ──────────────────────────────────────────────────────────
class Schreiber:
    """Nimmt Einzelbilder entgegen und schiebt sie roh in ffmpeg."""

    def __init__(self, ziel, dauern):
        self.ziel = Path(ziel)
        self.ton = Path(tempfile.mkstemp(suffix=".wav")[1])
        tonspur(dauern, self.ton)
        self.p = subprocess.Popen(
            ["ffmpeg", "-y", "-loglevel", "error",
             "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
             "-i", str(self.ton),
             "-c:v", "libx264", "-preset", "medium", "-crf", "25", "-maxrate", "4M", "-bufsize", "8M",
             "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(self.ziel)],
            stdin=subprocess.PIPE)
        self.n = 0
        self.deckbild = None

    def bild(self, img):
        if img.mode != "RGB":
            img = img.convert("RGB")
        if self.n == FPS:            # Deckbild nach einer Sekunde
            self.deckbild = img.copy()
        self.p.stdin.write(img.tobytes())
        self.n += 1

    def schliessen(self):
        self.p.stdin.close()
        self.p.wait()
        self.ton.unlink(missing_ok=True)
        if self.deckbild is not None:
            self.deckbild.save(self.ziel.with_suffix(".png"), optimize=True)
        return self.n / FPS


# ── Karte ────────────────────────────────────────────────────────────────────
Z = 14
TILE = 256
CACHE = Path.home() / ".cache" / "swisstopo"


def tile_xy(lon, lat, z=Z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y


class Karte:
    """Graue Landeskarte als ein grosses Bild, dazu die Umrechnung Lon/Lat → Pixel."""

    def __init__(self, bbox):
        lon0, lat0, lon1, lat1 = bbox
        x0, y1 = tile_xy(lon0, lat0)
        x1, y0 = tile_xy(lon1, lat1)
        self.tx0, self.ty0 = int(x0), int(y0)
        tx1, ty1 = int(x1), int(y1)
        self.img = Image.new("RGB", ((tx1 - self.tx0 + 1) * TILE, (ty1 - self.ty0 + 1) * TILE), "#E5E7EB")
        CACHE.mkdir(parents=True, exist_ok=True)
        fehl = 0
        for tx in range(self.tx0, tx1 + 1):
            for ty in range(self.ty0, ty1 + 1):
                p = CACHE / f"grau-{Z}-{tx}-{ty}.jpg"
                if not p.exists():
                    # Adressmuster des Dienstes: {z}/{x}/{y}
                    url = (f"https://wmts.geo.admin.ch/1.0.0/ch.swisstopo.pixelkarte-grau/default/"
                           f"current/3857/{Z}/{tx}/{ty}.jpeg")
                    try:
                        req = urllib.request.Request(url, headers={"User-Agent": "Politspiegel Schaffhausen"})
                        p.write_bytes(urllib.request.urlopen(req, timeout=30).read())
                    except Exception:
                        fehl += 1
                        continue
                try:
                    self.img.paste(Image.open(p).convert("RGB"), ((tx - self.tx0) * TILE, (ty - self.ty0) * TILE))
                except Exception:
                    fehl += 1
        if fehl:
            print(f"  {fehl} Kacheln fehlen")
        # Die Karte etwas aufhellen, damit die farbigen Linien vorne stehen.
        self.img = Image.blend(self.img, Image.new("RGB", self.img.size, "white"), 0.25)
        # Verkleinerte Stufen für die Übersicht: aus der vollen Karte wäre jedes
        # Übersichtsbild ein Verkleinern von 30 Millionen Pixeln.
        self.stufen = [(1.0, self.img)]
        f = 0.5
        while f >= 0.1:
            self.stufen.append((f, self.img.resize((int(self.img.size[0] * f), int(self.img.size[1] * f)), Image.LANCZOS)))
            f /= 2

    def linien_einbrennen(self, L_gv, L_ini):
        """Zeichnet die Strassen fest in jede Stufe der Karte. So kostet ein
        Kamerabild nur einen Ausschnitt statt 500 Linienzüge. Die leeren
        Stufen bleiben für den Aufbau-Effekt der Übersicht erhalten."""
        self.stufen_leer = [(f, img.copy()) for f, img in self.stufen]
        for f, img in self.stufen:
            d = ImageDraw.Draw(img)
            # In den kleinen Stufen (Übersicht) etwas kräftiger, sonst verschwinden die Linien.
            bg = max(6 if f < 0.3 else 3, int(11 * f))
            bi = max(3 if f < 0.3 else 2, int(5 * f))
            for ls in L_gv:
                d.line([(x * f, y * f) for x, y in ls], fill=GV, width=bg, joint="curve")
            for ls in L_ini:
                d.line([(x * f, y * f) for x, y in ls], fill=INI, width=bi, joint="curve")

    def ausschnitt(self, x0, y0, bw, bh, s, leer=False):
        """Kartenausschnitt (in Pixeln der vollen Karte) als Bild W x H beim Massstab s."""
        stufen = self.stufen_leer if leer else self.stufen
        f, img = stufen[0]
        for ff, ii in stufen:
            if ff >= s:
                f, img = ff, ii
        box = (int(x0 * f), int(y0 * f), int((x0 + bw) * f) + 1, int((y0 + bh) * f) + 1)
        # Ausserhalb der Karte bleibt heller Grund, kein Schwarz.
        grund = Image.new("RGB", (box[2] - box[0], box[3] - box[1]), GRUND)
        cx0, cy0 = max(box[0], 0), max(box[1], 0)
        cx1, cy1 = min(box[2], img.size[0]), min(box[3], img.size[1])
        if cx1 > cx0 and cy1 > cy0:
            grund.paste(img.crop((cx0, cy0, cx1, cy1)), (cx0 - box[0], cy0 - box[1]))
        return grund.resize((W, H), Image.BILINEAR)

    def px(self, lon, lat):
        x, y = tile_xy(lon, lat)
        return (x - self.tx0) * TILE, (y - self.ty0) * TILE


def ueberflug(slug, ordner):
    geo = ROOT / "abstimmungsspiegel" / "abstimmungen" / slug / "geo"
    ini = json.loads((geo / "03_freigegeben" / "geltung_initiative.geojson").read_text(encoding="utf-8"))["features"]
    gv = json.loads((geo / "03_freigegeben" / "geltung_gegenvorschlag.geojson").read_text(encoding="utf-8"))["features"]
    gem = json.loads((geo / "02_aufbereitet" / "gemeinden.json").read_text(encoding="utf-8"))
    hh = json.loads((geo / "02_aufbereitet" / "haushalte.json").read_text(encoding="utf-8"))["vorlagen"]
    daten = json.loads((ROOT / "abstimmungsspiegel" / "abstimmungen" / slug / "vorlage.json").read_text(encoding="utf-8"))
    v = daten["vorlage"]

    alle = [c for f in ini + gv for c in f["geometry"]["coordinates"]]
    lons = [c[0] for c in alle]
    lats = [c[1] for c in alle]
    bbox = (min(lons) - 0.03, min(lats) - 0.02, max(lons) + 0.03, max(lats) + 0.02)
    print("  Karte laden …")
    karte = Karte(bbox)
    print(f"  Karte {karte.img.size[0]} x {karte.img.size[1]} px")

    def linien(features):
        return [[karte.px(*c) for c in f["geometry"]["coordinates"]] for f in features]

    L_ini, L_gv = linien(ini), linien(gv)
    karte.linien_einbrennen(L_gv, L_ini)
    # Mittelpunkte je Gemeinde aus den Linien der Initiative und des Gegenvorschlags
    punkte = {}
    for f, ls in zip(ini + gv, L_ini + L_gv):
        punkte.setdefault(f["properties"]["gemeinde"], []).extend(ls)
    mitte = {g: (sum(p[0] for p in ps) / len(ps), sum(p[1] for p in ps) / len(ps)) for g, ps in punkte.items()}
    gemeinden = {g["gemeinde"]: g for g in gem["gemeinden"]}

    # Kamerastationen: Übersicht, dann die Gemeinden mit den meisten Kilometern
    reihenfolge = ["Schaffhausen", "Neuhausen am Rheinfall", "Thayngen", "Stein am Rhein",
                   "Wilchingen", "Beringen", "Schleitheim", "Ramsen"]
    reihenfolge = [g for g in reihenfolge if g in mitte][:7]
    ueber_s = min(W / karte.img.size[0], (H - 700) / karte.img.size[1])
    ueber_c = (karte.img.size[0] / 2, karte.img.size[1] / 2)

    stationen = [("uebersicht", ueber_c, ueber_s, 3.0, 4.0)]   # (name, zentrum, massstab, fahrt, halt)
    for g in reihenfolge:
        s = 1.0 if g == "Schaffhausen" else 1.25
        stationen.append((g, mitte[g], s, 2.2, 3.2))
    stationen.append(("schluss", ueber_c, ueber_s, 2.4, 4.0))

    dauern = []
    for i, st in enumerate(stationen):
        dauern.append((0 if i == 0 else st[3]) + st[4])
    ziel = ordner / "reel-ueberflug.mp4"
    sw = Schreiber(ziel, dauern)

    overlays = {}

    def overlay(kopf, panel):
        """Kopf, Legende, Panel und Fuss als eine durchsichtige Ebene, je Station einmal gerechnet."""
        k = (kopf, panel)
        if k in overlays:
            return overlays[k]
        frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        kasten(frame, (48, 150, W - 48, 330))
        d = ImageDraw.Draw(frame)
        d.text((80, 178), "ABSTIMMUNGSSPIEGEL", font=font("a", 24, "Bold"), fill=TEXT)
        d.text((80, 214), (kopf or v["titel"]), font=font("a", 44, "SemiBold"), fill=TEXT)
        d.text((80, 278), f"Welche Strassen erfasst sind · Abstimmung {v['abstimmung'][8:10]}.{v['abstimmung'][5:7]}.{v['abstimmung'][:4]}",
               font=font("p", 24, "Regular"), fill=TEXT2)

        # Legende und Panel unten
        y = H - 640
        kasten(frame, (48, y, W - 48, y + 300 if panel else y + 150))
        d = ImageDraw.Draw(frame)
        d.rounded_rectangle((80, y + 36, 130, y + 50), 4, fill=INI)
        d.text((150, y + 26), "Initiative", font=font("p", 30, "Medium"), fill=TEXT)
        d.rounded_rectangle((80, y + 96, 130, y + 116), 4, fill=GV)
        d.text((150, y + 88), "Gegenvorschlag", font=font("p", 30, "Medium"), fill=TEXT)
        if panel:
            titel, z1, z2 = panel
            d.text((520, y + 26), titel, font=font("a", 36, "SemiBold"), fill=TEXT)
            d.text((520, y + 82), z1, font=font("p", 28, "Regular"), fill=TEXT2)
            d.text((520, y + 122), z2, font=font("p", 28, "Regular"), fill=TEXT2)
        else:
            d.text((520, y + 26), f"{gem['total']['initiative_km']:.1f} km", font=font("a", 40, "SemiBold"), fill=INI)
            d.text((520, y + 88), f"{gem['total']['gegenvorschlag_km']:.1f} km", font=font("a", 40, "SemiBold"), fill=GV)
        if panel:
            yy = y + 190
            d.line((80, yy - 10, W - 80, yy - 10), fill=LINIE, width=2)
            d.text((80, yy), "Anwohner an diesen Strassen im Kanton", font=font("p", 24, "Regular"), fill=TEXT3)
            d.text((80, yy + 36), f"Initiative {hh['initiative']['anwohner']:,} · Gegenvorschlag {hh['gegenvorschlag']['anwohner']:,}".replace(",", " "),
                   font=font("a", 30, "SemiBold"), fill=TEXT)
        # Fuss
        kasten(frame, (48, H - 300, W - 48, H - 200), fill=(255, 255, 255, 215))
        d = ImageDraw.Draw(frame)
        d.text((80, H - 282), SEITE_KURZ + "/abstimmung/" + slug + "/", font=font("a", 24, "SemiBold"), fill=TEXT)
        d.text((80, H - 246), "Karte © swisstopo · Strassen: Geltungsbereich aus Wortlaut und amtlichen Geodaten, eigene Auswertung",
               font=font("p", 19, "Regular"), fill=TEXT3)
        overlays[k] = frame
        return frame

    def zeichne(zentrum, s, anteil_ini=1.0, anteil_gv=1.0, kopf=None, panel=None, aufbau=False):
        cx, cy = zentrum
        bw, bh = W / s, H / s
        x0, y0 = cx - bw / 2, cy - bh / 2
        frame = karte.ausschnitt(x0, y0, bw, bh, s, leer=aufbau).convert("RGBA")
        if aufbau:
            d = ImageDraw.Draw(frame)

            def tr(p):
                return ((p[0] - x0) * s, (p[1] - y0) * s)

            for L, anteil, farbe, breite in ((L_gv, anteil_gv, GV, 5), (L_ini, anteil_ini, INI, 3)):
                for ls in L[:int(len(L) * anteil)]:
                    pts = [tr(p) for p in ls]
                    if len(pts) >= 2:
                        d.line(pts, fill=farbe, width=breite, joint="curve")
        frame.alpha_composite(overlay(kopf, panel))
        return frame

    print("  Bilder rechnen …")
    vorher = None
    for i, (name, zentrum, s, fahrt, halt) in enumerate(stationen):
        if vorher is not None:
            n = int(fahrt * FPS)
            for k in range(n):
                t = ease((k + 1) / n)
                # Massstab logarithmisch interpolieren, sonst «springt» der Zoom
                sk = math.exp(math.log(vorher[1]) * (1 - t) + math.log(s) * t)
                zk = (vorher[0][0] * (1 - t) + zentrum[0] * t, vorher[0][1] * (1 - t) + zentrum[1] * t)
                sw.bild(zeichne(zk, sk))
        n = int(halt * FPS)
        for k in range(n):
            if name == "uebersicht":
                t = (k + 1) / n
                a_gv = min(1.0, t * 1.6)
                a_ini = max(0.0, min(1.0, (t - 0.35) * 1.6))
                sw.bild(zeichne(zentrum, s, a_ini, a_gv, aufbau=True))
            elif name == "schluss":
                sw.bild(zeichne(zentrum, s, panel=(f"{gem['total']['initiative_km']:.1f} km Initiative",
                                                    f"{gem['total']['gegenvorschlag_km']:.1f} km Gegenvorschlag",
                                                    "Kantonsstrassen innerorts, gesamter Kanton")))
            else:
                g = gemeinden.get(name, {})
                sw.bild(zeichne(zentrum, s, panel=(name,
                                                    f"Initiative {g.get('initiative_km', 0):.1f} km",
                                                    f"Gegenvorschlag {g.get('gegenvorschlag_km', 0):.1f} km")))
        vorher = (zentrum, s)
    sek = sw.schliessen()
    print(f"  {ziel.name}: {sek:.1f} s")
    return ziel


# ── Zeitstrahl ───────────────────────────────────────────────────────────────
def zeitstrahl(slug, ordner):
    geo = ROOT / "abstimmungsspiegel" / "abstimmungen" / slug / "geo"
    u = json.loads((geo / "02_aufbereitet" / "fussgaengerunfaelle.json").read_text(encoding="utf-8"))
    jahre = u["jahre"]
    n_j = len(jahre)
    ziel = ordner / "reel-zeitstrahl.mp4"
    phasen = [("titel", 3.0), ("schweiz", 9.0), ("staedte", 9.0), ("sh", 9.0), ("schluss", 4.0)]
    sw = Schreiber(ziel, [p[1] for p in phasen])

    def rahmen(untertitel):
        img = Image.new("RGBA", (W, H), GRUND)
        d = ImageDraw.Draw(img)
        d.text((72, 170), "ABSTIMMUNGSSPIEGEL", font=font("a", 26, "Bold"), fill=TEXT)
        d.text((72, 212), "Fussgängerunfälle 2011 bis 2025", font=font("a", 46, "SemiBold"), fill=TEXT)
        d.text((72, 276), untertitel, font=font("p", 27, "Regular"), fill=TEXT2)
        d.line((72, 326, W - 72, 326), fill=TEXT, width=3)
        d.line((72, H - 330, W - 72, H - 330), fill=LINIE, width=2)
        d.text((72, H - 310), "Quelle: ASTRA, Strassenverkehrsunfälle mit Personenschaden, Unfälle mit Fussgängerbeteiligung je Jahr",
               font=font("p", 20, "Regular"), fill=TEXT3)
        d.text((72, H - 278), SEITE_KURZ + "/abstimmung/" + slug + "/", font=font("a", 24, "SemiBold"), fill=TEXT)
        return img, d

    def balken(d, box, werte, sichtbar, farbe, max_w=None, beschriften=True, jahr_alle=False):
        x0, y0, x1, y1 = box
        max_w = max_w or max(werte)
        bw = (x1 - x0) / n_j
        for i, (j, w) in enumerate(zip(jahre, werte)):
            if i >= sichtbar:
                break
            h = (y1 - y0 - 40) * w / max_w
            bx = x0 + i * bw + bw * 0.12
            d.rounded_rectangle((bx, y1 - 40 - h, bx + bw * 0.76, y1 - 40), 6, fill=farbe)
            if beschriften:
                f = font("a", 22, "SemiBold")
                d.text((bx + bw * 0.38, y1 - 46 - h), str(w), font=f, fill=TEXT, anchor="mb")
            if jahr_alle or j in (2011, 2015, 2020, 2025):
                d.text((bx + bw * 0.38, y1 - 8), str(j)[2:] if not jahr_alle else str(j), font=font("p", 20, "Regular"), fill=TEXT3, anchor="mb")

    for name, dauer in phasen:
        n = int(dauer * FPS)
        for k in range(n):
            t = (k + 1) / n
            if name == "titel":
                img, d = rahmen("Was die Unfallstatistik des Bundes zeigt")
                d.text((72, 520), "Drei Zahlenreihen,\ndieselbe Quelle:", font=font("a", 60, "Bold"), fill=TEXT, spacing=12)
                y = 720
                for i, z in enumerate(["ganze Schweiz", "die grössten Städte", "Kanton Schaffhausen"], 1):
                    d.text((72, y), f"{i}. {z}", font=font("p", 40, "Regular"), fill=TEXT2)
                    y += 64
                d.text((72, 1000), "Gezählt sind Unfälle mit Personenschaden,\nan denen Fussgänger beteiligt waren.",
                       font=font("p", 28, "Regular"), fill=TEXT3, spacing=8)
            elif name == "schweiz":
                img, d = rahmen("Ganze Schweiz")
                sichtbar = min(n_j, int(t * (n_j + 1)))
                balken(d, (72, 420, W - 72, 1180), u["schweiz"], sichtbar, "#0F766E")
                if sichtbar >= n_j:
                    a, b = u["schweiz"][0], u["schweiz"][-1]
                    d.text((72, 1240), f"{jahre[0]}: {a} Unfälle · {jahre[-1]}: {b} Unfälle", font=font("p", 30, "Medium"), fill=TEXT)
                    d.text((72, 1290), f"Veränderung {(b - a) / a * 100:+.0f} Prozent", font=font("p", 30, "Regular"), fill=TEXT2)
            elif name == "staedte":
                img, d = rahmen("Die grössten Städte, je eigene Skala")
                staedte = list(u["staedte"].items())
                sichtbar = min(n_j, int(t * (n_j + 1)))
                cols, zeilen_ = 3, 3
                kw, kh = (W - 144) / cols, 340
                for i, (stadt, werte) in enumerate(staedte[:9]):
                    cx, cy = 72 + (i % cols) * kw, 400 + (i // cols) * kh
                    d.text((cx + 8, cy), stadt, font=font("a", 26, "SemiBold"), fill=TEXT)
                    d.text((cx + 8, cy + 34), f"{werte[0]} → {werte[-1]}" if sichtbar >= n_j else "", font=font("p", 22, "Regular"), fill=TEXT2)
                    farbe = "#8E44AD" if stadt == "Schaffhausen" else "#8B93A1"
                    balken(d, (cx + 8, cy + 70, cx + kw - 16, cy + kh - 30), werte, sichtbar, farbe, beschriften=False)
            elif name == "sh":
                img, d = rahmen("Kanton Schaffhausen, alle Gemeinden")
                sichtbar = min(n_j, int(t * (n_j + 1)))
                balken(d, (72, 420, W - 72, 1180), u["kanton_sh"], sichtbar, "#8E44AD")
                if sichtbar >= n_j:
                    w = u["kanton_sh"]
                    d.text((72, 1240), f"Höchster Wert {max(w)} ({jahre[w.index(max(w))]}), tiefster {min(w)} ({jahre[w.index(min(w))]})",
                           font=font("p", 30, "Medium"), fill=TEXT)
                    d.text((72, 1290), f"Mittel 2011 bis 2025: {sum(w) / len(w):.0f} Unfälle je Jahr", font=font("p", 30, "Regular"), fill=TEXT2)
            else:
                img, d = rahmen("Zum Nachrechnen")
                d.text((72, 520), "Alle Zahlen stammen aus\ndem offenen Datensatz\ndes Bundesamts für Strassen.", font=font("a", 52, "Bold"), fill=TEXT, spacing=12)
                d.text((72, 800), "1. Unfälle mit Personenschaden, Fussgänger beteiligt\n2. Unfalljahr 2011 bis 2025\n3. Gemeinde nach BFS-Nummer",
                       font=font("p", 32, "Regular"), fill=TEXT2, spacing=14)
                d.text((72, 1000), "Was die Zahlen für die Vorlage bedeuten,\nsteht in der Argumentprüfung auf der Seite.",
                       font=font("p", 28, "Regular"), fill=TEXT3, spacing=8)
            sw.bild(img)
    sek = sw.schliessen()
    print(f"  {ziel.name}: {sek:.1f} s")
    return ziel


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    slug, was = sys.argv[1], sys.argv[2]
    ordner = ROOT / "site" / "social" / "abstimmung" / slug
    ordner.mkdir(parents=True, exist_ok=True)
    if was in ("ueberflug", "alle"):
        ueberflug(slug, ordner)
    if was in ("zeitstrahl", "alle"):
        zeitstrahl(slug, ordner)


if __name__ == "__main__":
    main()

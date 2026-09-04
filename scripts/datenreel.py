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
    """Fussgängerunfälle im Kanton Schaffhausen 2011 bis 2025, je Jahr ein
    Balken, gestapelt nach Schwere (Leichtverletzte, Schwerverletzte, Getötete)."""
    geo = ROOT / "abstimmungsspiegel" / "abstimmungen" / slug / "geo"
    u = json.loads((geo / "02_aufbereitet" / "fussgaengerunfaelle.json").read_text(encoding="utf-8"))
    jahre = u["jahre"]
    n_j = len(jahre)
    stufen = [("Unfall mit Leichtverletzten", "Leichtverletzte", "#8B93A1"),
              ("Unfall mit Schwerverletzten", "Schwerverletzte", "#8E44AD"),
              ("Unfall mit Getöteten", "Getötete", "#111827")]
    werte = {k: [u["kanton_sh_schwere"].get(str(j), {}).get(k, 0) for j in jahre] for k, _, _ in stufen}
    total = [sum(werte[k][i] for k, _, _ in stufen) for i in range(n_j)]
    ziel = ordner / "reel-zeitstrahl.mp4"
    phasen = [("titel", 3.0), ("balken", 16.0), ("stand", 5.0), ("schluss", 4.0)]
    sw = Schreiber(ziel, [p[1] for p in phasen])

    def rahmen(untertitel):
        img = Image.new("RGBA", (W, H), GRUND)
        d = ImageDraw.Draw(img)
        d.text((72, 170), "ABSTIMMUNGSSPIEGEL", font=font("a", 26, "Bold"), fill=TEXT)
        d.text((72, 212), "Fussgängerunfälle im Kanton Schaffhausen", font=font("a", 42, "SemiBold"), fill=TEXT)
        d.text((72, 272), untertitel, font=font("p", 27, "Regular"), fill=TEXT2)
        d.line((72, 322, W - 72, 322), fill=TEXT, width=3)
        d.line((72, H - 330, W - 72, H - 330), fill=LINIE, width=2)
        d.text((72, H - 310), "Quelle: ASTRA, Strassenverkehrsunfälle mit Personenschaden, Unfälle mit Fussgängerbeteiligung, alle Gemeinden",
               font=font("p", 19, "Regular"), fill=TEXT3)
        d.text((72, H - 278), SEITE_KURZ + "/abstimmung/" + slug + "/", font=font("a", 24, "SemiBold"), fill=TEXT)
        return img, d

    def diagramm(d, sichtbar, anteil_letzter=1.0):
        x0, y0, x1, y1 = 72, 420, W - 72, 1240
        max_w = max(total) * 1.12
        bw = (x1 - x0) / n_j
        for i, j in enumerate(jahre):
            if i >= sichtbar:
                break
            f = anteil_letzter if i == sichtbar - 1 else 1.0
            bx = x0 + i * bw + bw * 0.1
            yb = y1 - 50
            for k, _, farbe in stufen:
                h = (y1 - 50 - y0) * werte[k][i] / max_w * f
                if h > 0:
                    d.rectangle((bx, yb - h, bx + bw * 0.8, yb), fill=farbe)
                    yb -= h
            if f >= 1.0:
                d.text((bx + bw * 0.4, yb - 8), str(total[i]), font=font("a", 24, "SemiBold"), fill=TEXT, anchor="mb")
            d.text((bx + bw * 0.4, y1 - 14), str(j)[2:], font=font("p", 20, "Regular"), fill=TEXT3, anchor="mb")
        # Legende
        x = 72
        for k, name, farbe in stufen:
            d.rectangle((x, 1290, x + 26, 1316), fill=farbe)
            d.text((x + 38, 1303), name, font=font("p", 26, "Regular"), fill=TEXT2, anchor="lm")
            x += 38 + d.textlength(name, font=font("p", 26, "Regular")) + 44

    for name, dauer in phasen:
        n = int(dauer * FPS)
        for k in range(n):
            t = (k + 1) / n
            if name == "titel":
                img, d = rahmen("Nur Unfälle mit Fussgängerbeteiligung, 2011 bis 2025")
                d.text((72, 520), "Jedes Jahr ein Balken,\ngestapelt nach Schwere.", font=font("a", 58, "Bold"), fill=TEXT, spacing=12)
                y = 740
                for i, (_, nm, farbe) in enumerate(stufen, 1):
                    d.rectangle((72, y + 8, 100, y + 40), fill=farbe)
                    d.text((120, y), f"{i}. {nm}", font=font("p", 38, "Regular"), fill=TEXT2)
                    y += 66
                d.text((72, 1000), "Gezählt sind polizeilich erfasste Unfälle\nmit Personenschaden, alle Gemeinden des Kantons.",
                       font=font("p", 28, "Regular"), fill=TEXT3, spacing=8)
            elif name == "balken":
                img, d = rahmen("Ein Balken je Jahr, wächst mit dem Jahr")
                pos = t * n_j
                sichtbar = min(n_j, int(pos) + 1)
                diagramm(d, sichtbar, min(1.0, (pos - int(pos)) * 1.6 + 0.001) if sichtbar <= n_j and pos < n_j else 1.0)
            elif name == "stand":
                img, d = rahmen("Alle 15 Jahre im Überblick")
                diagramm(d, n_j)
                a, b_ = total[0], total[-1]
                d.text((72, 1370), f"Höchster Wert {max(total)} ({jahre[total.index(max(total))]}), tiefster {min(total)} ({jahre[total.index(min(total))]})",
                       font=font("p", 28, "Medium"), fill=TEXT)
                d.text((72, 1414), f"Mittel: {sum(total) / n_j:.0f} je Jahr · Getötete 2011 bis 2025: {sum(werte['Unfall mit Getöteten'])}",
                       font=font("p", 28, "Regular"), fill=TEXT2)
            else:
                img, d = rahmen("Zum Nachrechnen")
                d.text((72, 520), "Offener Datensatz des\nBundesamts für Strassen,\nStand Februar 2026.", font=font("a", 52, "Bold"), fill=TEXT, spacing=12)
                d.text((72, 800), "1. Unfälle mit Personenschaden, Fussgänger beteiligt\n2. Unfalljahr 2011 bis 2025\n3. Kanton Schaffhausen, alle Gemeinden",
                       font=font("p", 32, "Regular"), fill=TEXT2, spacing=14)
                d.text((72, 1000), "Was die Zahlen für die Vorlage bedeuten,\nsteht in der Argumentprüfung auf der Seite.",
                       font=font("p", 28, "Regular"), fill=TEXT3, spacing=8)
            sw.bild(img)
    sek = sw.schliessen()
    print(f"  {ziel.name}: {sek:.1f} s")
    return ziel


# ── Gemeinsames für Kartenreels ──────────────────────────────────────────────
def karte_laden(slug):
    geo = ROOT / "abstimmungsspiegel" / "abstimmungen" / slug / "geo"
    ini = json.loads((geo / "03_freigegeben" / "geltung_initiative.geojson").read_text(encoding="utf-8"))["features"]
    gv = json.loads((geo / "03_freigegeben" / "geltung_gegenvorschlag.geojson").read_text(encoding="utf-8"))["features"]
    alle = [c for f in ini + gv for c in f["geometry"]["coordinates"]]
    lons = [c[0] for c in alle]
    lats = [c[1] for c in alle]
    karte = Karte((min(lons) - 0.03, min(lats) - 0.02, max(lons) + 0.03, max(lats) + 0.02))
    L_ini = [[karte.px(*c) for c in f["geometry"]["coordinates"]] for f in ini]
    L_gv = [[karte.px(*c) for c in f["geometry"]["coordinates"]] for f in gv]
    karte.linien_einbrennen(L_gv, L_ini)
    punkte = {}
    for f, ls in zip(ini + gv, L_ini + L_gv):
        punkte.setdefault(f["properties"]["gemeinde"], []).extend(ls)
    mitte = {g: (sum(p[0] for p in ps) / len(ps), sum(p[1] for p in ps) / len(ps)) for g, ps in punkte.items()}
    return geo, karte, mitte


def kopf_fuss(frame, slug, titel, untertitel, fuss):
    kasten(frame, (48, 150, W - 48, 330))
    d = ImageDraw.Draw(frame)
    d.text((80, 178), "ABSTIMMUNGSSPIEGEL", font=font("a", 24, "Bold"), fill=TEXT)
    d.text((80, 214), titel, font=font("a", 44, "SemiBold"), fill=TEXT)
    d.text((80, 278), untertitel, font=font("p", 24, "Regular"), fill=TEXT2)
    kasten(frame, (48, H - 300, W - 48, H - 200), fill=(255, 255, 255, 215))
    d = ImageDraw.Draw(frame)
    d.text((80, H - 282), SEITE_KURZ + "/abstimmung/" + slug + "/", font=font("a", 24, "SemiBold"), fill=TEXT)
    d.text((80, H - 246), fuss, font=font("p", 19, "Regular"), fill=TEXT3)


def fahrt(sw, stationen, bild):
    """Kamera über die Stationen (name, zentrum, massstab, fahrt_s, halt_s).
    bild(zentrum, s, name, t) liefert das Einzelbild; t läuft im Halt von 0 bis 1."""
    vorher = None
    for name, zentrum, s, fahrt_s, halt in stationen:
        if vorher is not None:
            n = int(fahrt_s * FPS)
            for k in range(n):
                t = ease((k + 1) / n)
                sk = math.exp(math.log(vorher[1]) * (1 - t) + math.log(s) * t)
                zk = (vorher[0][0] * (1 - t) + zentrum[0] * t, vorher[0][1] * (1 - t) + zentrum[1] * t)
                sw.bild(bild(zk, sk, None, 0.0))
        n = int(halt * FPS)
        for k in range(n):
            sw.bild(bild(zentrum, s, name, (k + 1) / n))
        vorher = (zentrum, s)


def dauern_von(stationen):
    return [(0 if i == 0 else st[3]) + st[4] for i, st in enumerate(stationen)]


# ── Lärm ─────────────────────────────────────────────────────────────────────
def laerm(slug, ordner):
    """Hektaren mit Fassaden über dem Immissionsgrenzwert (65 dB am Tag) an den
    betroffenen Strassen leuchten auf; Zahlen aus der Lärm- und Anwohnerauswertung."""
    geo, karte, mitte = karte_laden(slug)
    hekt = json.loads((geo / "03_freigegeben" / "anwohner_hektaren.geojson").read_text(encoding="utf-8"))["features"]
    hh = json.loads((geo / "02_aufbereitet" / "haushalte.json").read_text(encoding="utf-8"))
    vi, vg = hh["vorlagen"]["initiative"], hh["vorlagen"]["gegenvorschlag"]
    laut = [([karte.px(*c) for c in f["geometry"]["coordinates"][0]], f["properties"])
            for f in hekt if f["properties"].get("laut65")]
    leise = [([karte.px(*c) for c in f["geometry"]["coordinates"][0]], f["properties"])
             for f in hekt if not f["properties"].get("laut65")]
    ueber_s = min(W / karte.img.size[0], (H - 700) / karte.img.size[1])
    ueber_c = (karte.img.size[0] / 2, karte.img.size[1] / 2)
    stationen = [("uebersicht", ueber_c, ueber_s, 0, 5.0),
                 ("Schaffhausen", mitte["Schaffhausen"], 1.0, 2.5, 5.0),
                 ("Neuhausen am Rheinfall", mitte["Neuhausen am Rheinfall"], 1.25, 2.0, 4.0),
                 ("Thayngen", mitte["Thayngen"], 1.25, 2.0, 3.5),
                 ("Stein am Rhein", mitte["Stein am Rhein"], 1.25, 2.0, 3.5),
                 ("schluss", ueber_c, ueber_s, 2.4, 5.0)]
    ziel = ordner / "reel-laerm.mp4"
    sw = Schreiber(ziel, dauern_von(stationen))
    ORANGE = (224, 123, 0)

    def bild(zentrum, s, name, t):
        cx, cy = zentrum
        bw, bh = W / s, H / s
        x0, y0 = cx - bw / 2, cy - bh / 2
        frame = karte.ausschnitt(x0, y0, bw, bh, s).convert("RGBA")
        ebene = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ebene)
        anteil = min(1.0, t * 1.5) if name == "uebersicht" else 1.0
        puls = 0.75 + 0.25 * math.sin(t * math.pi * 4) if name else 1.0
        for pts, pr in leise:
            q = [((x - x0) * s, (y - y0) * s) for x, y in pts]
            if all(px < -50 or px > W + 50 or py < -50 or py > H + 50 for px, py in q):
                continue
            d.polygon(q, fill=(120, 130, 150, 45))
        for i, (pts, pr) in enumerate(laut):
            if i >= int(len(laut) * anteil):
                break
            q = [((x - x0) * s, (y - y0) * s) for x, y in pts]
            if all(px < -50 or px > W + 50 or py < -50 or py > H + 50 for px, py in q):
                continue
            d.polygon(q, fill=ORANGE + (int(150 * puls),), outline=ORANGE + (230,))
        frame.alpha_composite(ebene)
        kopf_fuss(frame, slug, "Lärm an den betroffenen Strassen",
                  "Hektaren mit Fassaden über 65 dB am Tag (Immissionsgrenzwert Wohnzone)",
                  "Karte © swisstopo · Lärmkataster Kanton SH, Bevölkerungsstatistik BFS (Hektarraster), eigene Auswertung")
        y = H - 640
        kasten(frame, (48, y, W - 48, y + 300))
        d = ImageDraw.Draw(frame)
        d.rectangle((80, y + 30, 112, y + 62), fill=ORANGE)
        d.text((130, y + 46), "Hektare mit Fassaden über 65 dB", font=font("p", 28, "Medium"), fill=TEXT, anchor="lm")
        d.rectangle((80, y + 86, 112, y + 118), fill=(120, 130, 150))
        d.text((130, y + 102), "übrige Hektaren an den Strassen", font=font("p", 28, "Medium"), fill=TEXT, anchor="lm")
        d.line((80, y + 148, W - 80, y + 148), fill=LINIE, width=2)
        if name == "schluss" or name is None and False:
            d.text((80, y + 168), "Anwohner an Fassaden über 65 dB", font=font("p", 24, "Regular"), fill=TEXT3)
            d.text((80, y + 204), f"Initiative {vi['anwohner_an_fassaden_ueber_65']:,}   Gegenvorschlag {vg['anwohner_an_fassaden_ueber_65']:,}".replace(",", " "),
                   font=font("a", 32, "SemiBold"), fill=TEXT)
        else:
            d.text((80, y + 168), "Gebäude mit Fassaden über 65 dB an diesen Strassen", font=font("p", 24, "Regular"), fill=TEXT3)
            d.text((80, y + 204), f"Initiative {vi['gebaeude_ueber_65']}   Gegenvorschlag {vg['gebaeude_ueber_65']}",
                   font=font("a", 32, "SemiBold"), fill=TEXT)
        if name and name not in ("uebersicht", "schluss"):
            d.text((W - 80, y + 46), name, font=font("a", 30, "SemiBold"), fill=TEXT, anchor="rm")
        return frame

    print("  Lärm: Bilder rechnen …")
    fahrt(sw, stationen, bild)
    print(f"  {ziel.name}: {sw.schliessen():.1f} s")
    return ziel


# ── Schulen, Kindergärten, Heime ─────────────────────────────────────────────
def anlagen(slug, ordner):
    geo, karte, mitte = karte_laden(slug)
    an = json.loads((geo / "03_freigegeben" / "anlagen.geojson").read_text(encoding="utf-8"))["features"]
    gem = json.loads((geo / "02_aufbereitet" / "gemeinden.json").read_text(encoding="utf-8"))["total"]
    KAT = {"schule": ("Schulen", (15, 118, 110)), "kindergarten": ("Kindergärten", (29, 78, 216)),
           "altersheim": ("Alters- und Pflegeheime", (142, 68, 173)), "sozial": ("weitere Sozialeinrichtungen, Spitäler", (100, 110, 125))}
    pts = [(karte.px(*f["geometry"]["coordinates"]), f["properties"]["kat"]) for f in an]
    zahl = {k: sum(1 for _, kk in pts if kk == k) for k in KAT}
    # 300 m in Kartenpixeln (Zoom 14, Breite 47.7°): 256 px je Kachel, Kachel = 40075 km · cos(lat) / 2^14
    m_je_px = 40075016 * math.cos(math.radians(47.7)) / (2 ** Z * TILE)
    r300 = 300 / m_je_px
    ueber_s = min(W / karte.img.size[0], (H - 700) / karte.img.size[1])
    ueber_c = (karte.img.size[0] / 2, karte.img.size[1] / 2)
    stationen = [("uebersicht", ueber_c, ueber_s, 0, 5.0),
                 ("Schaffhausen", mitte["Schaffhausen"], 1.0, 2.5, 6.0),
                 ("Neuhausen am Rheinfall", mitte["Neuhausen am Rheinfall"], 1.25, 2.0, 4.0),
                 ("Thayngen", mitte["Thayngen"], 1.25, 2.0, 3.5),
                 ("Stein am Rhein", mitte["Stein am Rhein"], 1.25, 2.0, 3.5),
                 ("schluss", ueber_c, ueber_s, 2.4, 5.0)]
    ziel = ordner / "reel-anlagen.mp4"
    sw = Schreiber(ziel, dauern_von(stationen))

    def bild(zentrum, s, name, t):
        cx, cy = zentrum
        bw, bh = W / s, H / s
        x0, y0 = cx - bw / 2, cy - bh / 2
        frame = karte.ausschnitt(x0, y0, bw, bh, s).convert("RGBA")
        ebene = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ebene)
        anteil = min(1.0, t * 1.4) if name == "uebersicht" else 1.0
        kreis = 1.0 if name in (None, "uebersicht", "schluss") else min(1.0, t * 2.5)
        rr = max(r300 * s * kreis, 3)
        for i, ((x, y), kat) in enumerate(pts):
            if i >= int(len(pts) * anteil):
                break
            px, py = (x - x0) * s, (y - y0) * s
            if px < -100 or px > W + 100 or py < -100 or py > H + 100:
                continue
            farbe = KAT[kat][1]
            if s >= 0.5:
                d.ellipse((px - rr, py - rr, px + rr, py + rr), fill=farbe + (40,), outline=farbe + (140,), width=2)
            r = 7 if s >= 0.5 else 4
            d.ellipse((px - r, py - r, px + r, py + r), fill=farbe + (255,), outline=(255, 255, 255, 255), width=2)
        frame.alpha_composite(ebene)
        kopf_fuss(frame, slug, "Schulen, Kindergärten und Heime",
                  "Wo entlang der betroffenen Strassen eine Ausnahme zur Debatte stünde",
                  "Karte © swisstopo · Standorte OpenStreetMap und kantonale Quellen, Kreise 300 m, eigene Auswertung")
        y = H - 640
        kasten(frame, (48, y, W - 48, y + 320))
        d = ImageDraw.Draw(frame)
        yy = y + 30
        for kat, (nm, farbe) in KAT.items():
            d.ellipse((80, yy + 4, 104, yy + 28), fill=farbe, outline=(255, 255, 255), width=2)
            d.text((122, yy + 16), f"{zahl[kat]} {nm}", font=font("p", 27, "Medium"), fill=TEXT, anchor="lm")
            yy += 48
        d.line((80, yy + 6, W - 80, yy + 6), fill=LINIE, width=2)
        d.text((80, yy + 22), f"Betroffene Strassen innerhalb 300 m einer Anlage: {gem['km300']} km, {gem['p300']} Prozent",
               font=font("a", 26, "SemiBold"), fill=TEXT)
        if name and name not in ("uebersicht", "schluss"):
            d.text((W - 80, y + 46), name, font=font("a", 30, "SemiBold"), fill=TEXT, anchor="rm")
        return frame

    print("  Anlagen: Bilder rechnen …")
    fahrt(sw, stationen, bild)
    print(f"  {ziel.name}: {sw.schliessen():.1f} s")
    return ziel


# ── Bus: Linie 1 und 6 als Ablaufdiagramm ────────────────────────────────────
def bus(slug, ordner):
    """Zwei Busse fahren dieselbe Linie: links nach Fahrplan, rechts mit dem
    Zuschlag für Tempo 30 auf den betroffenen Abschnitten (ASTRA-Ansatz,
    20 s je km, obere Schranke). Haltezeit 12 s je Halt in beiden Fällen."""
    geo = ROOT / "abstimmungsspiegel" / "abstimmungen" / slug / "geo"
    kurse = json.loads((geo / "02_aufbereitet" / "buslinien_halte.json").read_text(encoding="utf-8"))["kurse"]
    uml = {l["linie"]: l for l in json.loads((geo / "02_aufbereitet" / "umlaufrechnung.json").read_text(encoding="utf-8"))["linien"]}
    ini = json.loads((geo / "03_freigegeben" / "geltung_initiative.geojson").read_text(encoding="utf-8"))["features"]
    strassen = [c for f in ini for c in f["geometry"]["coordinates"]]
    R = 6371000.0

    def meter(a, b):
        dx = math.radians(b[0] - a[0]) * R * math.cos(math.radians(a[1]))
        dy = math.radians(b[1] - a[1]) * R
        return math.hypot(dx, dy)

    def nah(p):
        return any(abs(p[0] - q[0]) < 0.0008 and abs(p[1] - q[1]) < 0.0005 and meter(p, q) < 50 for q in strassen)

    def minuten(hhmm):
        h, m = hhmm.split(":")
        return int(h) * 60 + int(m)

    def aufbereiten(name, halte):
        linie = name.split()[0]
        t0 = minuten(halte[0]["ab"])
        seg = []
        for a, b in zip(halte, halte[1:]):
            pa, pb = (a["lon"], a["lat"]), (b["lon"], b["lat"])
            km = meter(pa, pb) * 1.153 / 1000
            proben = [(pa[0] + (pb[0] - pa[0]) * k / 8, pa[1] + (pb[1] - pa[1]) * k / 8) for k in range(9)]
            anteil = sum(1 for p in proben if nah(p)) / 9
            fahrplan = (minuten(b["an"] or b["ab"]) - minuten(a["ab"] or a["an"])) * 60
            seg.append({"km": km, "anteil": anteil, "fahrplan_s": max(fahrplan, 30)})
        roh = sum(20 * s_["km"] * s_["anteil"] for s_ in seg)
        soll = uml[linie]["zusatz_astra_min"] * 60 / 2          # je Richtung
        f = soll / roh if roh else 0
        for s_ in seg:
            s_["zusatz_s"] = 20 * s_["km"] * s_["anteil"] * f
        return {"linie": linie, "name": name, "halte": [h["halt"] for h in halte], "seg": seg,
                "start": t0, "gesamt_s": sum(s_["fahrplan_s"] for s_ in seg),
                "zusatz_s": sum(s_["zusatz_s"] for s_ in seg), "km_betroffen": sum(s_["km"] * s_["anteil"] for s_ in seg)}

    linien = [aufbereiten("1 Waldfriedhof → Herbstäcker", kurse["1 Waldfriedhof → Herbstäcker"]),
              aufbereiten("6 Falkeneck → Buchthalen", kurse["6 Falkeneck → Buchthalen"])]
    HEUTE, T30 = (15, 118, 110), (224, 123, 0)
    HALT = 12.0
    phasen = []
    for L in linien:
        phasen.append((L, 22.0))
    ziel = ordner / "reel-bus.mp4"
    sw = Schreiber(ziel, [p[1] for p in phasen] + [6.0])

    def position(L, t_s, mit_zusatz):
        """Wo der Bus nach t_s Sekunden ist: (Index des Abschnitts, Anteil 0..1, hält?)."""
        rest = t_s
        for i, s_ in enumerate(L["seg"]):
            fahrt_s = s_["fahrplan_s"] + (s_["zusatz_s"] if mit_zusatz else 0)
            if rest < HALT:
                return i, 0.0, True
            rest -= HALT
            if rest < fahrt_s:
                return i, rest / fahrt_s, False
            rest -= fahrt_s
        return len(L["seg"]), 0.0, True

    def linienbild(L, t):
        img = Image.new("RGBA", (W, H), GRUND)
        d = ImageDraw.Draw(img)
        d.text((72, 150), "ABSTIMMUNGSSPIEGEL", font=font("a", 24, "Bold"), fill=TEXT)
        d.text((72, 188), f"Bus Linie {L['linie']}: heute und bei Tempo 30", font=font("a", 42, "SemiBold"), fill=TEXT)
        d.text((72, 246), L["name"][2:] + f" · {len(L['halte'])} Halte, je 12 s Haltezeit", font=font("p", 25, "Regular"), fill=TEXT2)
        d.line((72, 292, W - 72, 292), fill=TEXT, width=3)
        n = len(L["halte"])
        y0, y1 = 360, H - 560
        schritt = (y1 - y0) / (n - 1)
        xl, xr, xm = 300, W - 300, W // 2
        gesamt = L["gesamt_s"] + L["zusatz_s"] + HALT * n
        t_s = t * gesamt * 1.04
        # Strecke
        for i, s_ in enumerate(L["seg"]):
            ya, yb = y0 + i * schritt, y0 + (i + 1) * schritt
            farbe = (220, 38, 38) if s_["anteil"] > 0.3 else (160, 168, 180)
            d.line((xm, ya, xm, yb), fill=farbe, width=10 if s_["anteil"] > 0.3 else 6)
        for i, h in enumerate(L["halte"]):
            y = y0 + i * schritt
            d.ellipse((xm - 9, y - 9, xm + 9, y + 9), fill=(255, 255, 255), outline=TEXT, width=3)
            f = font("p", 21, "Regular")
            lbl = h if len(h) <= 22 else h[:21] + "…"
            if i % 2 == 0:
                d.text((xm - 22, y), lbl, font=f, fill=TEXT2, anchor="rm")
            else:
                d.text((xm + 22, y), lbl, font=f, fill=TEXT2, anchor="lm")
        # Busse
        for mit, x, farbe, name in ((False, xl, HEUTE, "heute"), (True, xr, T30, "Tempo 30")):
            i, a, haelt = position(L, t_s, mit)
            y = y0 + min(i + a, n - 1) * schritt
            d.rounded_rectangle((x - 34, y - 22, x + 34, y + 22), 10, fill=farbe)
            d.text((x, y), "BUS", font=font("a", 20, "Bold"), fill=(255, 255, 255), anchor="mm")
            # Uhr
            verg = min(t_s, sum(s_["fahrplan_s"] + (s_["zusatz_s"] if mit else 0) for s_ in L["seg"]) + HALT * n)
            d.text((x, y0 - 50), name, font=font("a", 26, "SemiBold"), fill=farbe, anchor="mm")
            d.text((x, y0 - 18), f"{int(verg // 60):02d}:{int(verg % 60):02d}", font=font("a", 30, "Bold"), fill=TEXT, anchor="mm")
        # Fuss: Zahlen
        y = H - 520
        d.line((72, y - 20, W - 72, y - 20), fill=LINIE, width=2)
        u = uml[L["linie"]]
        d.text((72, y), f"Fahrzeit heute {L['gesamt_s'] / 60 + HALT * n / 60:.0f} min, bei Tempo 30 bis {(L['gesamt_s'] + L['zusatz_s']) / 60 + HALT * n / 60:.0f} min",
               font=font("p", 27, "Medium"), fill=TEXT)
        d.text((72, y + 40), f"Zuschlag {L['zusatz_s'] / 60:.1f} min je Richtung: 20 s je km betroffener Strecke ({L['km_betroffen']:.1f} km), obere Schranke nach ASTRA",
               font=font("p", 22, "Regular"), fill=TEXT2)
        d.text((72, y + 74), f"Physikalisch gerechnet (Beschleunigen, Bremsen, 12 s Halt): +{u['zusatz_physik_min'] / 2:.1f} min, untere Schranke",
               font=font("p", 22, "Regular"), fill=TEXT2)
        d.text((72, y + 120), f"Fahrzeuge im 10-Minuten-Takt: heute {u['fahrzeuge']}, bei Tempo 30 {u['fahrzeuge_physik']} bis {u['fahrzeuge_astra']}",
               font=font("a", 28, "SemiBold"), fill=TEXT)
        d.rectangle((72, y + 170, 100, y + 180), fill=(220, 38, 38))
        d.text((112, y + 175), "Abschnitt auf einer betroffenen Kantonsstrasse", font=font("p", 22, "Regular"), fill=TEXT3, anchor="lm")
        d.line((72, H - 330, W - 72, H - 330), fill=LINIE, width=2)
        d.text((72, H - 310), "Quelle: Fahrplan transport.opendata.ch (Kurse 08.09.2026), Umlaufrechnung und Geltungsbereich, eigene Auswertung",
               font=font("p", 19, "Regular"), fill=TEXT3)
        d.text((72, H - 278), SEITE_KURZ + "/abstimmung/" + slug + "/", font=font("a", 24, "SemiBold"), fill=TEXT)
        return img

    for L, dauer in phasen:
        n = int(dauer * FPS)
        for k in range(n):
            sw.bild(linienbild(L, (k + 1) / n))
    # Schlussbild
    n = int(6.0 * FPS)
    for k in range(n):
        img = Image.new("RGBA", (W, H), GRUND)
        d = ImageDraw.Draw(img)
        d.text((72, 150), "ABSTIMMUNGSSPIEGEL", font=font("a", 24, "Bold"), fill=TEXT)
        d.text((72, 188), "Braucht Tempo 30 einen zusätzlichen Bus?", font=font("a", 42, "SemiBold"), fill=TEXT)
        d.line((72, 292, W - 72, 292), fill=TEXT, width=3)
        y = 420
        for L in linien:
            u = uml[L["linie"]]
            d.text((72, y), f"Linie {L['linie']}", font=font("a", 40, "Bold"), fill=TEXT)
            d.text((72, y + 60), f"1. Umlauf heute {u['umlauf_min']} min, Takt {u['takt_min']} min, {u['fahrzeuge']} Fahrzeuge, Reserve {u['reserve_min']} min",
                   font=font("p", 28, "Regular"), fill=TEXT2)
            d.text((72, y + 104), f"2. Zuschlag beide Richtungen: {u['zusatz_physik_min']:.1f} bis {u['zusatz_astra_min']:.1f} min",
                   font=font("p", 28, "Regular"), fill=TEXT2)
            d.text((72, y + 148), f"3. Fahrzeuge bei Tempo 30: {u['fahrzeuge_physik']} bis {u['fahrzeuge_astra']}",
                   font=font("a", 32, "SemiBold"), fill=TEXT)
            y += 260
        d.text((72, y + 20), "Untere Schranke physikalisch gerechnet, obere nach ASTRA-Forschungsbericht 1663.\nOb die Reserve im Umlauf reicht, entscheidet über den zusätzlichen Bus.",
               font=font("p", 26, "Regular"), fill=TEXT3, spacing=8)
        d.line((72, H - 330, W - 72, H - 330), fill=LINIE, width=2)
        d.text((72, H - 278), SEITE_KURZ + "/abstimmung/" + slug + "/", font=font("a", 24, "SemiBold"), fill=TEXT)
        sw.bild(img)
    print(f"  {ziel.name}: {sw.schliessen():.1f} s")
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
    if was in ("laerm", "alle"):
        laerm(slug, ordner)
    if was in ("anlagen", "alle"):
        anlagen(slug, ordner)
    if was in ("bus", "alle"):
        bus(slug, ordner)


if __name__ == "__main__":
    main()

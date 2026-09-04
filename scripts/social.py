#!/usr/bin/env python3
"""
Social-Media-Bilder und -Videos je Kantonsratssitzung
=====================================================
Erzeugt aus data/all_sessions.json für eine Sitzung:

  site/social/kantonsrat/<slug>/
      feed-00.png … feed-NN.png   Karussell 1080 x 1350 (Deckblatt + je Abstimmung eine Karte)
      reel.mp4                    Diashow 1080 x 1920 mit eigener Tonspur (ton.py), H.264
      reel-00.png … reel-NN.png   die Einzelbilder der Diashow
      posts.json                  Texte, Medienadressen und Kanäle je Beitrag

Die Dateien liegen in site/, damit publish.py sie mit auf GitHub Pages bringt.
Erst dort haben sie eine öffentliche Adresse, und nur mit einer solchen kann
Metricool sie einplanen. Adresse:

  https://michaeljkahler.github.io/politspiegel/social/kantonsrat/<slug>/feed-00.png

Gestaltung folgt docs/DESIGN_entscheide.md: Abstimmungsfarben Petrol/Purpur,
Parteifarben nur als Punkt vor dem Fraktionsnamen, jede Farbe trägt ihre Zahl.
Texte folgen den Regeln in docs/KONZEPT_social-media.md: nummerierte Listen,
keine Wertung, das Ergebnis heisst «Angenommen» oder «Abgelehnt» wie im Dashboard.

Ausführen:
    python3 scripts/social.py                 # neueste Sitzung
    python3 scripts/social.py --anzahl 3      # die drei neuesten Sitzungen
    python3 scripts/social.py --sitzung 2026-08-24-nachmittag
    python3 scripts/social.py --neu           # vorhandene Ausgabe überschreiben
    python3 scripts/social.py --ohne-video    # nur Bilder

Braucht: Pillow, ffmpeg (für das Video), die Schriften in scripts/assets/fonts/.
"""
import argparse
import collections
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prototyp import (STIMME_KEY, betreff, flach, frak_key, kuerze,  # noqa: E402
                      sess_sort_key, split_titel, ueberschrift)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FONTS = ROOT / "scripts" / "assets" / "fonts"
AUS = ROOT / "site" / "social" / "kantonsrat"
BASIS_URL = "https://michaeljkahler.github.io/politspiegel/"
SEITE_URL = BASIS_URL + "kantonsrat/"
SEITE_KURZ = "michaeljkahler.github.io/politspiegel"

MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
          "September", "Oktober", "November", "Dezember"]

# ── Farben (docs/DESIGN_entscheide.md, Variante «Fläche hell») ──────────────
STIMME = {"ja": "#0F766E", "nein": "#8E44AD", "enth": "#8B93A1", "abw": "#DFE3E8"}
STIMME_TEXT = {"ja": "#0C6A62", "nein": "#7E3C9A", "enth": "#646C79", "abw": "#6E7783"}
STIMME_LABEL = {"ja": "Ja", "nein": "Nein", "enth": "Enthaltung", "abw": "abwesend"}
PARTEI = {"svp": "#4B8A3E", "edu": "#A65E42", "sp": "#F0554D", "gru": "#84B547",
          "al": "#B02E7A", "glp": "#C4C43D", "evp": "#DEAA28", "fdp": "#3872B5",
          "mitte": "#D6862B", "none": "#A8AEB6"}
GRUND = "#F6F7F9"
KARTE = "#FFFFFF"
TEXT = "#111827"
TEXT2 = "#4B5563"
TEXT3 = "#6B7280"
LINIE = "#E5E7EB"

FEED = (1080, 1350)
REEL = (1080, 1920)
MAX_KARUSSELL = 10          # Instagram nimmt höchstens zehn Bilder je Beitrag

# Kurzformen der Fraktionsnamen für die schmale Spalte. Gleiche Reihenfolge
# der Parteien wie im Original, nur ohne die Jungparteien.
FRAK_KURZ = {
    "SP-JUSO-GRÜNE-Junge Grüne": "SP-JUSO-Grüne",
    "AL-GRÜNE-JUNGE GRÜNE": "AL-Grüne",
    "AL-GRÜNE-Junge Grüne": "AL-Grüne",
    "GRÜNE-Junge Grüne": "Grüne",
    "FDP-Die Mitte-JF": "FDP-Die Mitte",
    "FDP-CVP-JF": "FDP-CVP",
}


def listentitel(a):
    """Titel für die Liste auf dem Deckblatt. Formale Kurztitel («Sofortige
    2. Lesung», «Schlussabstimmung») bekommen den Sachbetreff angehängt."""
    t = a["titel"]
    g = a["geschaeft"]
    schon = any(w.lower()[:8] in t.lower() for w in g.split() if len(w) >= 8)
    if len(t) < 36 and g and not schon:
        return f"{t}: {g}"
    return t


# ── Schriften ────────────────────────────────────────────────────────────────
_fonts = {}


def font(art, groesse, gewicht="Regular"):
    """Archivo für Titel und Zahlen, Public Sans für Fliesstext. Variable Fonts."""
    k = (art, groesse, gewicht)
    if k not in _fonts:
        datei = FONTS / ("Archivo.ttf" if art == "a" else "PublicSans.ttf")
        f = ImageFont.truetype(str(datei), groesse)
        try:
            f.set_variation_by_name(gewicht)
        except Exception:
            pass
        _fonts[k] = f
    return _fonts[k]


def breite(d, text, f):
    return d.textlength(text, font=f)


def umbrechen(d, text, f, max_b, max_zeilen=None):
    """Bricht Text an Wortgrenzen um. Letzte Zeile wird mit … gekürzt, wenn nötig."""
    woerter = text.split()
    zeilen, akt = [], ""
    for w in woerter:
        probe = (akt + " " + w).strip()
        if breite(d, probe, f) <= max_b:
            akt = probe
        else:
            if akt:
                zeilen.append(akt)
            akt = w
    if akt:
        zeilen.append(akt)
    if max_zeilen and len(zeilen) > max_zeilen:
        zeilen = zeilen[:max_zeilen]
        letzte = zeilen[-1]
        while breite(d, letzte + "…", f) > max_b and " " in letzte:
            letzte = letzte.rsplit(" ", 1)[0]
        zeilen[-1] = letzte.rstrip(" .,;:") + "…"
    return zeilen


def absatz(d, xy, text, f, farbe, max_b, zeilenhoehe, max_zeilen=None):
    """Zeichnet umbrochenen Text, gibt die y-Position nach dem Absatz zurück."""
    x, y = xy
    for z in umbrechen(d, text, f, max_b, max_zeilen):
        d.text((x, y), z, font=f, fill=farbe)
        y += zeilenhoehe
    return y


def rund(d, box, r, fill, outline=None, w=1):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=w)


# ── Auswertung einer Abstimmung ──────────────────────────────────────────────
def vorstoss_aus_geschaeft(v, titel, referenz):
    """Vorstösse ohne Sachtitel im Titel («Volksmotion 2024/1 von X und Y … vom
    22. März 2024»): der Sachtitel steht dann oft in «…» im Geschäftstitel."""
    m = re.match(r"(Volksmotion|Motion|Postulat|Interpellation|Petition)\s*(?:Nr\.\s*)?([\d/]+)?"
                 r"\s*(?:von\s+(.+?))?(?:\s*\(|\s+sowie\b|\s+vom\s+\d|$)", titel)
    if not m or referenz:
        return titel, referenz
    q = re.search(r"«(.+?)»", flach(v.get("geschaeft")))
    if not q or len(q.group(1)) < 8:
        return titel, referenz
    art, nr, wer = m.group(1), m.group(2), (m.group(3) or "").strip()
    if len(wer) > 40:
        wer = re.split(r"\s+und\s+", wer)[0] + " u. a."
    ref = art + (" " + nr if nr else "") + (", " + wer if wer else "")
    return kuerze(q.group(1), 96), ref


def auswerten(sess, i, v):
    gesamt = collections.Counter()
    nach_frak = collections.OrderedDict()
    for m in sess["members"]:
        roh = m["votes"][i] if i < len(m["votes"]) else "V/A/N"
        k = STIMME_KEY.get(roh, "abw")
        gesamt[k] += 1
        nach_frak.setdefault(m["fraktion"], collections.Counter())[k] += 1
    inv = bool(v.get("richtung_invertiert"))
    if gesamt["ja"] == gesamt["nein"]:
        ergebnis, ekey = "Stimmengleichheit", "enth"
    else:
        ja_gewinnt = gesamt["ja"] > gesamt["nein"]
        an = (not ja_gewinnt) if inv else ja_gewinnt
        ergebnis, ekey = ("Angenommen", "ja") if an else ("Abgelehnt", "nein")
    titel, referenz = ueberschrift(v)
    titel, referenz = vorstoss_aus_geschaeft(v, titel, referenz)
    # Abschreibung eines Vorstosses: «Angenommen» heisst, der Vorstoss ist
    # erledigt. Damit die Karte das nicht als Zustimmung zum Anliegen zeigt,
    # steht die Abstimmungsform vorne im Titel.
    typ = flach(v.get("typ"))
    if typ.lower() == "abschreibung" and not titel.lower().startswith("abschreibung"):
        titel = "Abschreibung: " + titel
    frak = sorted(
        [{"name": f, "key": frak_key(f), "total": sum(c.values()),
          "c": {k: c.get(k, 0) for k in STIMME_KEY.values()}}
         for f, c in nach_frak.items()],
        key=lambda x: -x["total"])
    return {
        "nr": v["nr"], "titel": titel, "referenz": referenz,
        "geschaeft": betreff(v.get("geschaeft")),
        "typ": flach(v.get("typ")), "thema": v.get("thema_name") or "",
        "inv": inv, "inv_note": flach(v.get("inverted_note")) if inv else "",
        "ergebnis": ergebnis, "ekey": ekey,
        "c": {k: gesamt.get(k, 0) for k in STIMME_KEY.values()},
        "total": sum(gesamt.values()), "frak": frak,
    }


def datum_lang(sitzung):
    _, datum, zeit = split_titel(sitzung)
    t, m, j = datum.split(".")
    s = f"{int(t)}. {MONATE[int(m) - 1]} {j}"
    return s, zeit


def slug(sitzung):
    _, datum, zeit = split_titel(sitzung)
    t, m, j = datum.split(".")
    s = f"{j}-{m}-{t}"
    if zeit:
        s += "-" + re.sub(r"[^a-z]", "", zeit.lower())
    return s


# ── Zeichenbausteine ─────────────────────────────────────────────────────────
def balken(d, box, c, total, hoehe_text=True, f=None):
    """Gestapelter Balken Ja/Nein/Enthaltung/abwesend, Zahl in jedem Segment."""
    x0, y0, x1, y1 = box
    b = x1 - x0
    rund(d, box, 8, STIMME["abw"])
    x = x0
    f = f or font("a", int((y1 - y0) * 0.55), "SemiBold")
    for k in ["ja", "nein", "enth", "abw"]:
        n = c.get(k, 0)
        if not n:
            continue
        w = b * n / total
        seg = (x, y0, x + w, y1)
        if k != "abw":
            d.rectangle(seg, fill=STIMME[k])
        if hoehe_text:
            t = str(n)
            tb = breite(d, t, f)
            if tb + 10 <= w:
                farbe = "#FFFFFF" if k != "abw" else STIMME_TEXT["abw"]
                d.text((x + (w - tb) / 2, (y0 + y1) / 2), t, font=f, fill=farbe, anchor="lm")
        x += w
    # Ecken rund halten
    maske = Image.new("L", (int(b), int(y1 - y0)), 0)
    ImageDraw.Draw(maske).rounded_rectangle((0, 0, int(b) - 1, int(y1 - y0) - 1), 8, fill=255)
    return maske


def balken_rund(img, box, c, total, f=None):
    """Wie balken(), aber sauber abgerundet: zeichnet auf eine Ebene und maskiert."""
    x0, y0, x1, y1 = [int(v) for v in box]
    ebene = Image.new("RGB", (x1 - x0, y1 - y0), STIMME["abw"])
    d = ImageDraw.Draw(ebene)
    maske = balken(d, (0, 0, x1 - x0, y1 - y0), c, total, f=f)
    img.paste(ebene, (x0, y0), maske)


def kopf(d, W, links, rechts, y=64):
    d.text((72, y), links, font=font("a", 30, "SemiBold"), fill=TEXT)
    f = font("p", 26, "Regular")
    d.text((W - 72 - breite(d, rechts, f), y + 3), rechts, font=f, fill=TEXT3)
    d.line((72, y + 52, W - 72, y + 52), fill=LINIE, width=2)


def fuss(d, W, H, text_links="Alle Details, Fraktionen und Namen:", y=None):
    y = y or H - 110
    d.line((72, y - 24, W - 72, y - 24), fill=LINIE, width=2)
    d.text((72, y), text_links, font=font("p", 24, "Regular"), fill=TEXT3)
    d.text((72, y + 34), SEITE_KURZ, font=font("a", 28, "SemiBold"), fill=TEXT)
    f = font("p", 22, "Regular")
    q = "Quelle: Kantonsrat Schaffhausen, sh.ch"
    d.text((W - 72 - breite(d, q, f), y + 40), q, font=f, fill=TEXT3)


def chip(d, xy, text, key, gross=True):
    f = font("a", 34 if gross else 24, "SemiBold")
    x, y = xy
    tb = breite(d, text, f)
    h = 56 if gross else 40
    px = 22 if gross else 14
    rund(d, (x, y, x + tb + 2 * px, y + h), h / 2, STIMME[key])
    farbe = "#FFFFFF" if key != "enth" else "#FFFFFF"
    d.text((x + px, y + h / 2), text, font=f, fill=farbe, anchor="lm")
    return x + tb + 2 * px


# ── Rahmen: Kopf, Fuss, Inhaltsfläche ───────────────────────────────────────
def rahmen(groesse, links, rechts):
    """Grundfläche mit Kopf- und Fusszeile. Gibt Bild und die freie Fläche
    (y_oben, y_unten) zurück, in die der Inhalt zentriert gesetzt wird.
    Im Hochformat 9:16 bleiben oben 200 und unten 340 px frei, weil TikTok und
    Instagram dort ihre Bedienelemente einblenden."""
    W, H = groesse
    hoch = H > 1500
    img = Image.new("RGB", groesse, GRUND)
    d = ImageDraw.Draw(img)
    oben = 200 if hoch else 64
    kopf(d, W, links, rechts, y=oben)
    fy = (H - 340) if hoch else (H - 110)
    fuss(d, W, H, y=fy)
    return img, oben + 80, fy - 50


def einpassen(img, inhalt, y_oben, y_unten, y_ende):
    """Setzt die gezeichnete Inhaltsfläche mittig in den freien Bereich."""
    h = min(y_ende, inhalt.height)
    frei = y_unten - y_oben
    y = y_oben + max(0, (frei - h) // 2)
    img.paste(inhalt.crop((0, 0, inhalt.width, h)), (0, y))


# ── Deckblatt ────────────────────────────────────────────────────────────────
def deckblatt(groesse, sess, votes, teil=None, teile=1):
    W, H = groesse
    datum, zeit = datum_lang(sess["sitzung"])
    img, y0, y1 = rahmen(groesse, "Politspiegel Schaffhausen", "Kantonsratsspiegel")
    inhalt = Image.new("RGB", (W, y1 - y0), GRUND)
    d = ImageDraw.Draw(inhalt)
    y = 0
    d.text((72, y), "Kantonsrat", font=font("a", 64, "Bold"), fill=TEXT)
    y += 84
    d.text((72, y), datum + (f", {zeit}" if zeit else ""), font=font("a", 46, "Medium"), fill=TEXT2)
    y += 72
    n = sess["n_votes"]
    satz = f"{n} namentliche Abstimmung{'en' if n != 1 else ''}"
    if teil:
        satz += f" · Teil {teil} von {teile}"
    d.text((72, y), satz, font=font("p", 32, "Regular"), fill=TEXT3)
    y += 84

    # Nummerierte Liste der Abstimmungen mit Ergebnis
    ft = font("p", 29, "Medium")
    fn = font("a", 29, "SemiBold")
    platz = (y1 - y0) - y - 10
    zeile = max(58, min(100, platz // max(1, len(votes))))
    max_n = int(platz // zeile)
    zeigen = votes[:max_n]
    x_chip = W - 72 - 215
    for a in zeigen:
        d.text((72, y + 8), f"{a['nr']}.", font=fn, fill=TEXT3)
        zeilen = umbrechen(d, listentitel(a), ft, x_chip - 150, 2 if zeile >= 76 else 1)
        for k, z in enumerate(zeilen):
            d.text((134, y + 8 + 36 * k), z, font=ft, fill=TEXT)
        chip(d, (x_chip, y + 2), a["ergebnis"], a["ekey"], gross=False)
        y += zeile
    if len(votes) > max_n:
        d.text((134, y + 8), f"… und {len(votes) - max_n} weitere", font=ft, fill=TEXT3)
        y += zeile
    einpassen(img, inhalt, y0, y1, y)
    return img


# ── Karte je Abstimmung ──────────────────────────────────────────────────────
def karte(groesse, sess, a, pos, gesamt_n):
    W, H = groesse
    datum, zeit = datum_lang(sess["sitzung"])
    img, y0, y1 = rahmen(groesse, "Kantonsrat · " + datum, f"Abstimmung {pos} von {gesamt_n}")
    inhalt = Image.new("RGB", (W, y1 - y0 + 400), GRUND)   # Reserve, wird beschnitten
    d = ImageDraw.Draw(inhalt)
    innen = W - 144
    y = 0

    # Titel, Referenz, Geschäft
    ft = font("a", 48, "SemiBold")
    y = absatz(d, (72, y), a["titel"], ft, TEXT, innen, 58, max_zeilen=3)
    if a["referenz"]:
        y += 6
        y = absatz(d, (72, y), a["referenz"], font("p", 29, "Regular"), TEXT2, innen, 38, 1)
    if a["geschaeft"] and a["geschaeft"].lower() not in a["titel"].lower():
        y += 6
        y = absatz(d, (72, y), "Geschäft: " + a["geschaeft"], font("p", 27, "Regular"),
                   TEXT3, innen, 36, max_zeilen=2)
    if a["typ"] or a["thema"]:
        y += 8
        teile = [t for t in (a["typ"], a["thema"]) if t]
        d.text((72, y), " · ".join(teile), font=font("p", 26, "Medium"), fill=TEXT3)
        y += 38

    # Ergebnis
    y += 32
    xe = chip(d, (72, y), a["ergebnis"], a["ekey"])
    c = a["c"]
    zahlen = f"Ja {c['ja']} · Nein {c['nein']} · Enthaltung {c['enth']} · abwesend {c['abw']}"
    fz = font("p", 28, "Regular")
    if breite(d, zahlen, fz) <= W - 72 - xe - 24:
        d.text((xe + 24, y + 28), zahlen, font=fz, fill=TEXT2, anchor="lm")
        y += 84
    else:
        y += 72
        d.text((72, y), zahlen, font=fz, fill=TEXT2)
        y += 44
    if a["inv"]:
        hinweis = "Ja bedeutet: " + re.sub(r"^Ja bedeutet\s*", "", a["inv_note"], flags=re.I)
        fh = font("p", 27, "Medium")
        zeilen = umbrechen(d, hinweis, fh, innen - 48, 2)
        hh = 26 + 36 * len(zeilen)
        rund(d, (72, y, W - 72, y + hh), 12, "#EEF2F7", outline=LINIE, w=2)
        yy = y + 13
        for z in zeilen:
            d.text((96, yy), z, font=fh, fill=TEXT)
            yy += 36
        y += hh + 18
    balken_rund(inhalt, (72, y, W - 72, y + 72), c, a["total"], f=font("a", 34, "SemiBold"))
    y += 72

    # Fraktionen
    y += 44
    d.text((72, y), "Nach Fraktion", font=font("a", 30, "SemiBold"), fill=TEXT)
    y += 52
    fname = font("p", 28, "Medium")
    fzahl = font("a", 28, "SemiBold")
    zeile = 74
    namen_b = 330
    for f in a["frak"]:
        d.ellipse((72, y + 15, 94, y + 37), fill=PARTEI.get(f["key"], PARTEI["none"]))
        name = FRAK_KURZ.get(f["name"], f["name"])
        name = umbrechen(d, name, fname, namen_b - 40, 1)[0]
        d.text((108, y + 26), name, font=fname, fill=TEXT, anchor="lm")
        bx0 = 72 + namen_b
        bx1 = W - 72 - 130
        balken_rund(inhalt, (bx0, y + 2, bx1, y + 50), f["c"], f["total"], f=font("a", 26, "SemiBold"))
        cc = f["c"]
        d.text((W - 72, y + 26), f"{cc['ja']} : {cc['nein']}", font=fzahl, fill=TEXT2, anchor="rm")
        y += zeile

    # Legende
    y += 10
    fl = font("p", 25, "Regular")
    x = 72
    for k in ["ja", "nein", "enth", "abw"]:
        d.rounded_rectangle((x, y + 6, x + 24, y + 30), 5, fill=STIMME[k],
                            outline=LINIE if k == "abw" else None)
        d.text((x + 34, y + 18), STIMME_LABEL[k], font=fl, fill=TEXT3, anchor="lm")
        x += 34 + breite(d, STIMME_LABEL[k], fl) + 38
    y += 40
    einpassen(img, inhalt, y0, y1, y)
    return img


def schluss(groesse, sess):
    W, H = groesse
    img = Image.new("RGB", groesse, GRUND)
    d = ImageDraw.Draw(img)
    datum, _ = datum_lang(sess["sitzung"])
    y = H // 2 - 200
    d.text((72, y), "Wer hat wie abgestimmt?", font=font("a", 56, "Bold"), fill=TEXT)
    y += 90
    y = absatz(d, (72, y), "Alle namentlichen Abstimmungen des Kantonsrats Schaffhausen, "
               "nach Ratsmitglied, Fraktion und Thema.", font("p", 32, "Regular"), TEXT2,
               W - 144, 44)
    y += 30
    d.text((72, y), SEITE_KURZ, font=font("a", 40, "SemiBold"), fill=TEXT)
    y += 70
    d.text((72, y), "Politspiegel Schaffhausen · privates, nichtkommerzielles Projekt",
           font=font("p", 24, "Regular"), fill=TEXT3)
    return img


# ── Video ────────────────────────────────────────────────────────────────────
def video(bilder, dauern, ziel):
    """Diashow aus PNGs mit selbst erzeugter Tonspur (scripts/ton.py): ruhiger
    Flächenklang, Impuls bei jedem Bildwechsel, keine fremden Aufnahmen."""
    if not shutil.which("ffmpeg"):
        print("  ffmpeg fehlt, kein Video.")
        return False
    import tempfile
    from ton import tonspur
    ton_datei = Path(tempfile.mkstemp(suffix=".wav")[1])
    tonspur(dauern, ton_datei)
    # Die Bildliste liegt im Temp-Ordner, nicht neben der Ausgabe: im
    # eingehängten Projektordner darf das Skript keine Dateien löschen.
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as fh:
        for b, t in zip(bilder, dauern):
            fh.write(f"file '{b.resolve().as_posix()}'\nduration {t}\n")
        fh.write(f"file '{bilder[-1].resolve().as_posix()}'\n")
        liste = Path(fh.name)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(liste),
           "-i", str(ton_datei),
           "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
           "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(ziel)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    liste.unlink(missing_ok=True)
    ton_datei.unlink(missing_ok=True)
    if r.returncode:
        print("  ffmpeg:", r.stderr[:400])
        return False
    return True


# ── Texte ────────────────────────────────────────────────────────────────────
def parteien_zeile(netz, sess):
    """«Parteien im Rat: @…» je Netzwerk. Immer alle Parteien, die in der Sitzung
    vertreten waren; wer im Netzwerk kein Konto hat, steht als Name. Konten aus
    data/parteien_social.json. Facebook verlinkt aus der Schnittstelle nicht,
    dort stehen nur die Namen."""
    pfad = DATA / "parteien_social.json"
    if not pfad.exists():
        return ""
    liste = json.loads(pfad.read_text(encoding="utf-8"))["parteien"]
    konten = {e["partei"].lower(): e for e in liste}
    reihe = [e["partei"].lower() for e in liste]     # Reihenfolge wie in der Datei
    im_rat = []
    for m in sess["members"]:
        k = (m.get("partei") or "").strip()
        if k and k.lower() not in [x.lower() for x in im_rat]:
            im_rat.append(k)
    teile = []
    for k in sorted(im_rat, key=lambda x: (reihe.index(x.lower()) if x.lower() in reihe else 99, x.lower())):
        e = konten.get(k.lower())
        h = e.get(netz) if e else None
        teile.append(("@" + h) if h and netz != "facebook" else k)
    return "Parteien im Rat: " + " ".join(teile)


def text_karussell(sess, votes, teil, teile, url_ordner, netz="instagram"):
    datum, zeit = datum_lang(sess["sitzung"])
    n = sess["n_votes"]
    zeilen = [f"Kantonsrat Schaffhausen, {datum}: {n} namentliche Abstimmung{'en' if n != 1 else ''}."
              + (f" Teil {teil} von {teile}." if teile > 1 else ""), ""]
    for a in votes:
        c = a["c"]
        z = f"{a['nr']}. {listentitel(a)}"
        if a["referenz"]:
            z += f" ({a['referenz']})"
        z += f": {a['ergebnis']} (Ja {c['ja']}, Nein {c['nein']}"
        if c["enth"]:
            z += f", Enthaltung {c['enth']}"
        z += ")"
        if a["inv"]:
            z += ". " + a["inv_note"].rstrip(".") + "."
        zeilen.append(z)
    schluss_ = ["", "Alle Details, Fraktionen und Namen: " + SEITE_URL,
                "Quelle: Abstimmungsprotokolle des Kantonsrats, sh.ch"]
    pz = parteien_zeile(netz, sess)
    if pz:
        schluss_ += ["", pz]
    schluss_ += ["", "#Schaffhausen #Kantonsrat #Politspiegel"]
    t = "\n".join(zeilen + schluss_)
    if len(t) > 2100:   # Instagram: 2200 Zeichen
        t = kuerze("\n".join(zeilen), 2000 - len("\n".join(schluss_))) + "\n".join(schluss_)
    return t


def text_reel(sess, netz="instagram"):
    datum, _ = datum_lang(sess["sitzung"])
    n = sess["n_votes"]
    pz = parteien_zeile(netz, sess)
    return (f"Kantonsrat Schaffhausen, {datum}: alle {n} namentlichen Abstimmungen in einer Minute. "
            f"Wer wie gestimmt hat: {SEITE_URL}" + (f"\n\n{pz}" if pz else "")
            + "\n\n#Schaffhausen #Kantonsrat #Politspiegel")


# ── Hauptlauf ────────────────────────────────────────────────────────────────
def sitzung_bauen(sess, ordner, mit_video=True):
    ordner.mkdir(parents=True, exist_ok=True)
    votes = [auswerten(sess, i, v) for i, v in enumerate(sess["votes"])]
    n = len(votes)
    url_ordner = BASIS_URL + "social/kantonsrat/" + ordner.name + "/"
    posts = []

    # Karussell(e), je höchstens MAX_KARUSSELL Bilder inkl. Deckblatt
    je = MAX_KARUSSELL - 1
    gruppen = [votes[i:i + je] for i in range(0, n, je)] or [[]]
    lauf = 0
    for gi, gruppe in enumerate(gruppen, 1):
        medien = []
        img = deckblatt(FEED, sess, gruppe, teil=gi if len(gruppen) > 1 else None, teile=len(gruppen))
        pfad = ordner / f"feed-{lauf:02d}.png"
        img.save(pfad, optimize=True)
        medien.append(url_ordner + pfad.name)
        lauf += 1
        for a in gruppe:
            img = karte(FEED, sess, a, a["nr"], n)
            pfad = ordner / f"feed-{lauf:02d}.png"
            img.save(pfad, optimize=True)
            medien.append(url_ordner + pfad.name)
            lauf += 1
        # Zwei Beiträge je Karussell: die @-Erwähnungen der Parteien sind je
        # Netzwerk andere Konten, und Metricool kennt nur einen Text je Beitrag.
        posts.append({
            "art": "karussell", "teil": gi, "teile": len(gruppen), "netz": "instagram",
            "text": text_karussell(sess, gruppe, gi, len(gruppen), url_ordner, "instagram"),
            "media": medien,
            "providers": ["instagram", "facebook"],
            "instagram": {"type": "POST"}, "facebook": {"type": "POST"},
        })
        posts.append({
            "art": "karussell", "teil": gi, "teile": len(gruppen), "netz": "tiktok",
            "text": text_karussell(sess, gruppe, gi, len(gruppen), url_ordner, "tiktok"),
            "media": medien,
            "providers": ["tiktok"],
            "tiktok": {"privacyOption": "PUBLIC_TO_EVERYONE", "photoCoverIndex": 0},
        })

    # Reel: Deckblatt, alle Karten, Schlussbild
    if mit_video:
        bilder, dauern = [], []
        img = deckblatt(REEL, sess, votes)
        p = ordner / "reel-00.png"
        img.save(p, optimize=True)
        bilder.append(p)
        dauern.append(3.5)
        for k, a in enumerate(votes, 1):
            img = karte(REEL, sess, a, a["nr"], n)
            p = ordner / f"reel-{k:02d}.png"
            img.save(p, optimize=True)
            bilder.append(p)
            dauern.append(4.0)
        img = schluss(REEL, sess)
        p = ordner / f"reel-{n + 1:02d}.png"
        img.save(p, optimize=True)
        bilder.append(p)
        dauern.append(3.0)
        if video(bilder, dauern, ordner / "reel.mp4"):
            datum, _ = datum_lang(sess["sitzung"])
            posts.append({
                "art": "reel", "netz": "instagram",
                "text": text_reel(sess, "instagram"),
                "media": [url_ordner + "reel.mp4"],
                "dauer_s": sum(dauern),
                "providers": ["instagram", "facebook", "youtube"],
                "instagram": {"type": "REEL", "showReelOnFeed": True},
                "facebook": {"type": "REEL"},
                "youtube": {"type": "short", "title": f"Kantonsrat Schaffhausen, {datum}: "
                            f"{n} Abstimmungen", "privacy": "public", "madeForKids": False,
                            "category": "NEWS_POLITICS"},
            })
            posts.append({
                "art": "reel", "netz": "tiktok",
                "text": text_reel(sess, "tiktok"),
                "media": [url_ordner + "reel.mp4"],
                "dauer_s": sum(dauern),
                "providers": ["tiktok"],
                "tiktok": {"privacyOption": "PUBLIC_TO_EVERYONE"},
            })

    (ordner / "posts.json").write_text(json.dumps({
        "sitzung": sess["sitzung"], "slug": ordner.name, "n_votes": n,
        "quelle": sess.get("url"), "status": "entwurf",
        "abstimmungen": [{"nr": a["nr"], "titel": a["titel"], "ergebnis": a["ergebnis"],
                          "c": a["c"]} for a in votes],
        "posts": posts,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    return posts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anzahl", type=int, default=1, help="die N neuesten Sitzungen")
    ap.add_argument("--sitzung", help="Slug einer Sitzung, z. B. 2026-08-24-nachmittag")
    ap.add_argument("--neu", action="store_true", help="vorhandene Ausgabe überschreiben")
    ap.add_argument("--ohne-video", action="store_true")
    a = ap.parse_args()

    d = json.loads((DATA / "all_sessions.json").read_text(encoding="utf-8"))
    sessions = sorted(d["sessions"], key=sess_sort_key, reverse=True)
    if a.sitzung:
        sessions = [s for s in sessions if slug(s["sitzung"]) == a.sitzung]
        if not sessions:
            raise SystemExit(f"Keine Sitzung mit Slug {a.sitzung}.")
    else:
        sessions = sessions[:a.anzahl]

    for s in sessions:
        ordner = AUS / slug(s["sitzung"])
        if (ordner / "posts.json").exists() and not a.neu:
            print(f"{ordner.name}: schon vorhanden, übersprungen (--neu zum Erneuern).")
            continue
        print(f"{ordner.name}: {s['n_votes']} Abstimmungen …")
        posts = sitzung_bauen(s, ordner, mit_video=not a.ohne_video)
        for p in posts:
            print(f"  {p['art']}: {len(p['media'])} Medien, {len(p['text'])} Zeichen Text")
        print(f"  Ordner: {ordner.relative_to(ROOT)}")
        print(f"  Adresse nach dem Veröffentlichen: {BASIS_URL}social/kantonsrat/{ordner.name}/")


if __name__ == "__main__":
    main()

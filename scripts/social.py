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

Inhalt (Entscheid vom 27. September 2026):
  Deckblatt  je Geschäft ein Kasten mit dem Namen des Geschäfts, darunter je
             Abstimmung eine Zeile Stichworte zum Inhalt und eine Zeile mit
             Ergebnis, Antragsteller (Initiale, Name, Partei) und Artikel.
             Keine Stimmenzahlen.
  Karte      Geschäft und Artikel, Stichworte als Titel, Antragsteller, Ergebnis
             mit Stimmenzahlen, Antragstext mit Streichungen und Einfügungen,
             Bedeutung von Ja und Nein, Gesamtbalken, Fraktionsbalken.
  Reel       Deckblatt mit einer Zeile je Abstimmung ohne Namen, danach die Karten.
  Bildtexte  Stichworte, Ergebnis, Antragsteller, Artikel; alle Parteien im Rat
             und alle Medien mit @, soweit das Netz ein Konto kennt.

Quellen der Texte:
  data/stichworte.json      Stichworte je Abstimmung. Schreibt Claude im
                            halbmonatlichen Auftrag aus dem Antragstext; fehlt ein
                            Eintrag, steht der Titel aus dem Protokoll.
  data/antragstexte.json    Antragstexte mit Streichungen und Einfügungen
                            (scripts/antragstexte.py).
  data/parteien_social.json und data/medien_social.json: Konten für die Erwähnungen.

Gestaltung folgt docs/DESIGN_entscheide.md: Abstimmungsfarben Petrol/Purpur,
Parteifarben nur als Punkt vor dem Fraktionsnamen, jede Farbe trägt ihre Zahl.
Texte folgen den Regeln in docs/KONZEPT_social-media.md: nummerierte Listen,
keine Wertung, das Ergebnis heisst «Angenommen» oder «Abgelehnt» wie im Dashboard.

Ausführen:
    python3 scripts/antragstexte.py --neueste 4   # Markierungen der neuen Sitzungen
    python3 scripts/social.py                 # neueste Sitzung
    python3 scripts/social.py --anzahl 3      # die drei neuesten Sitzungen
    python3 scripts/social.py --sitzung 2026-08-24-nachmittag
    python3 scripts/social.py --neu           # vorhandene Ausgabe überschreiben
    python3 scripts/social.py --ohne-video    # nur Bilder

Beim Überschreiben bleiben die Metricool-Angaben (id, uuid, Termin, Status) der
Beiträge in posts.json erhalten.

Braucht: Pillow, ffmpeg (für das Video), die Schriften in scripts/assets/fonts/.
"""
import argparse
import collections
import json
import re
import shutil
import subprocess
import sys
from datetime import date
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
# Ergebnis-Chip: grau für Stimmengleichheit und ungültige Abstimmungen, dunkler
# als der Enthaltungsbalken, damit weisse Schrift lesbar bleibt (Kontrast 4,8 : 1).
CHIP = {"ja": STIMME["ja"], "nein": STIMME["nein"], "enth": "#6B7280"}
PARTEI = {"svp": "#4B8A3E", "edu": "#A65E42", "sp": "#F0554D", "gru": "#84B547",
          "al": "#B02E7A", "glp": "#C4C43D", "evp": "#DEAA28", "fdp": "#3872B5",
          "mitte": "#D6862B", "none": "#A8AEB6"}
GRUND = "#F6F7F9"
KARTE = "#FFFFFF"
KASTEN = "#E9EEF4"
MARKER = "#FCE8A4"          # Hintergrund eingefügter Wörter im Antragstext
TEXT = "#111827"
TEXT2 = "#4B5563"
TEXT3 = "#6B7280"
LINIE = "#E5E7EB"

FEED = (1080, 1350)
REEL = (1080, 1920)
MAX_KARUSSELL = 10          # Instagram nimmt höchstens zehn Bilder je Beitrag
MAX_ERWAEHNUNGEN = 20       # Instagram: höchstens 20 @-Erwähnungen je Bildtext

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
PARTEI_ANZEIGE = {"GRÜNE": "Grüne", "JUNGE GRÜNE": "Junge Grüne"}

# Kürzel im Vermerk «Ja bedeutet Zustimmung Antrag SPK» → Untertitel des Geschäfts
KOMMISSION = {
    "SPK": "der Spezialkommission",
    "GPK": "der Geschäftsprüfungskommission",
    "GPK/RR": "von Geschäftsprüfungskommission und Regierungsrat",
    "GESKO": "der Gesundheitskommission",
}


# ── Datenquellen ─────────────────────────────────────────────────────────────
_quellen = {}


def quelle(name):
    if name not in _quellen:
        p = DATA / name
        _quellen[name] = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    return _quellen[name]


def stichwort(sl, nr):
    return ((quelle("stichworte.json").get("sitzungen") or {}).get(sl) or {}).get(str(nr))


def antragstext(sl, nr):
    s = (quelle("antragstexte.json").get("sitzungen") or {}).get(sl) or {}
    return (s.get("abstimmungen") or {}).get(str(nr)) or {}


def markierungen_sicherstellen(sess):
    """Fehlt die Sitzung in data/antragstexte.json, die Markierungen aus der
    Excel-Datei lesen und nachtragen (wie scripts/antragstexte.py)."""
    sl = slug(sess["sitzung"])
    daten = quelle("antragstexte.json")
    if sl in (daten.get("sitzungen") or {}):
        return
    q = sess.get("quelle") or ""
    pfad = DATA / "raw" / q
    if not q.lower().endswith(".xlsx") or not pfad.exists():
        return
    import antragstexte as at
    abst = {k: v for k, v in at.datei_lesen(pfad).items() if int(k) <= sess["n_votes"]}
    daten.setdefault("sitzungen", {})[sl] = {"quelle": q, "abstimmungen": abst}
    daten.setdefault("hinweis", "Antragstexte mit Markierungen, erzeugt von scripts/antragstexte.py.")
    daten["sitzungen"] = dict(sorted(daten["sitzungen"].items(), reverse=True))
    (DATA / "antragstexte.json").write_text(json.dumps(daten, ensure_ascii=False, indent=1),
                                           encoding="utf-8")
    print(f"  Antragstexte nachgetragen: {len(abst)} Abstimmungen aus {q}")


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


# ── Personen, Artikel, Zusätze ───────────────────────────────────────────────
def person(sess, text):
    """«B. Looser» oder «Bettina Looser» → {"name": "B. Looser", "partei": "SP"}.
    Eindeutig über Initiale und Nachname; mehrdeutig oder unbekannt: ohne Partei.
    Kein Personenname (z. B. «Gesundheitskommission»): None."""
    t = flach(text)
    m = re.match(r"^([A-ZÄÖÜ])\.\s*([A-ZÄÖÜ].+)$", t)
    if m:
        ini, nach = m.group(1), m.group(2).strip()
        treffer = [x for x in sess["members"]
                   if x["nachname"] == nach and x["vorname"][:1] == ini]
        name = f"{ini}. {nach}"
    else:
        treffer = [x for x in sess["members"] if f"{x['vorname']} {x['nachname']}" == t]
        if not treffer:
            return None
        name = f"{treffer[0]['vorname'][:1]}. {treffer[0]['nachname']}"
    partei = ""
    if len(treffer) == 1:
        p = (treffer[0].get("partei") or "").strip()
        partei = PARTEI_ANZEIGE.get(p.upper(), p)
    return {"name": name, "partei": partei}


def wer_klammer(p):
    return f"{p['name']} ({p['partei']})" if p.get("partei") else p["name"]


def wer_komma(p):
    return f"{p['name']}, {p['partei']}" if p.get("partei") else p["name"]


def antragsteller(sess, v):
    """(Antragsteller, Gegenantrag) aus Titel und Vermerken. Der Gegenantrag ist
    nur bei einer Ausmehrung zweier Anträge gesetzt."""
    t = flach(v.get("titel"))
    m = re.match(r"^(?:Ordnungsantrag|Antrag)\s+(?:RR\s+)?(.+)$", t)
    if not m:
        return None, None
    wer = person(sess, m.group(1))
    if not wer:
        return None, None
    ja, nein = flach(v.get("inverted_note")), flach(v.get("gegen_note"))
    gegen = None
    person_ja = re.search(r"Zustimmung Antrag\s+[A-ZÄÖÜ]\.", ja)
    mg = re.search(r"Zustimmung Antrag\s+([A-ZÄÖÜ]\..+)$", nein)
    if mg and (person_ja or flach(v.get("typ")).lower() == "ausmehrung"):
        gegen = person(sess, mg.group(1))
    return wer, gegen


ART_RE = re.compile(r"Art\.\s*(\d+[a-z]*)((?:\s*Abs\.\s*\d+[a-z]*)?(?:\s*lit\.?\s*[a-z]{1,3}\)?)?)")


def artikel(details, hinweise):
    """(kurz, lang): «Art. 18» für das Deckblatt, «Art. 18 Abs. 1a» für die Karte.
    «Gilt auch für Art. 36 Abs. 5, 38 Abs. 5» ergänzt die Kurzform."""
    m = ART_RE.search(details or "")
    if not m:
        return "", ""
    haupt = m.group(1)
    lang = "Art. " + haupt + re.sub(r"lit\.?\s*([a-z]{1,3})\)?", r"lit. \1", m.group(2) or "")
    lang = re.sub(r"\s+", " ", lang).strip()
    if re.match(r"\s*\(neu\)", (details or "")[m.end():m.end() + 8]):
        lang += " (neu)"
    weitere = []
    for h in hinweise or []:
        if re.search(r"gilt auch", h, re.I):
            weitere += re.findall(r"(\d+[a-z]*)\s+Abs\.", h) or re.findall(r"Art\.\s*(\d+[a-z]*)", h)
    nummern = list(dict.fromkeys([haupt] + weitere))
    return "Art. " + ", ".join(nummern), lang


def zusatz(details):
    d = flach(details)
    if re.match(r"R[üu]ckkehr auf (?:die )?(?:Vorlage|Fassung) (?:des )?(?:RR|Regierungsrat)", d, re.I):
        return "Fassung Regierungsrat"
    if d.lower().startswith("konsultativabstimmung"):
        return "Konsultativabstimmung"
    return ""


KUERZEL = {"SPK": "Spezialkommission", "GPK": "Geschäftsprüfungskommission",
           "GESKO": "Gesundheitskommission", "RR": "Regierungsrat"}


def bedeutung(note, wort):
    """«Ja bedeutet Zustimmung Antrag SPK» → «Ja bedeutet: Zustimmung Antrag
    Spezialkommission». Kürzel von Kommissionen und Regierung ausgeschrieben."""
    n = flach(note)
    if not n:
        return ""
    rest = re.sub(r"^%s\s+bedeutet:?\s*" % wort, "", n, flags=re.I)
    rest = re.sub(r"\b(SPK|GPK|GESKO|Gesko|RR)\b", lambda m: KUERZEL[m.group(1).upper()], rest)
    return f"{wort} bedeutet: {rest}"


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
    titel_roh = flach(v.get("titel"))
    ungueltig = bool(re.match(r"ungültige abstimmung", titel_roh.lower()))
    if ungueltig:
        ergebnis, ekey = "Ungültig", "enth"
    elif gesamt["ja"] == gesamt["nein"]:
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
    sl = slug(sess["sitzung"])
    at = antragstext(sl, v.get("nr"))
    wer, gegen = antragsteller(sess, v)
    details = flach(v.get("details"))
    art_kurz, art_lang = artikel(details, at.get("hinweise"))
    return {
        "nr": v["nr"], "titel": titel, "referenz": referenz, "titel_roh": titel_roh,
        "geschaeft": betreff(v.get("geschaeft")),
        "typ": typ, "thema": v.get("thema_name") or "",
        "inv": inv, "inv_note": flach(v.get("inverted_note")) if inv else "",
        "ja_note": flach(v.get("inverted_note")), "nein_note": flach(v.get("gegen_note")),
        "ergebnis": ergebnis, "ekey": ekey, "ungueltig": ungueltig,
        "c": {k: gesamt.get(k, 0) for k in STIMME_KEY.values()},
        "total": sum(gesamt.values()), "frak": frak,
        "slug": sl, "stichwort": None if ungueltig else stichwort(sl, v.get("nr")),
        "wer": wer, "gegen": gegen, "artikel": art_kurz, "artikel_lang": art_lang,
        "zusatz": zusatz(details), "segmente": at.get("segmente") or [],
        "hinweise": at.get("hinweise") or [], "details": details,
    }


def listentitel(a):
    """Kurztitel einer Abstimmung für Listen (Deckblatt, Bildtext, WhatsApp).
    Mit Stichwort: das Stichwort samt Antragsteller. Ohne: der Titel aus dem
    Protokoll; formale Kurztitel («Schlussabstimmung») mit dem Sachbetreff."""
    if a.get("stichwort"):
        s = a["stichwort"]
        if a.get("wer"):
            s += f" ({wer_komma(a['wer'])})"
        return s
    return titel_ohne_stichwort(a)


def titel_ohne_stichwort(a):
    t = a["titel"]
    g = a["geschaeft"]
    schon = any(w.lower()[:8] in t.lower() for w in g.split() if len(w) >= 8)
    if len(t) < 36 and g and not schon:
        return f"{t}: {g}"
    return t


def zeilentitel(a):
    """Erste Zeile eines Listeneintrags: Stichwort oder Titel."""
    if a["ungueltig"]:
        return "Ungültige Abstimmung"
    return a["stichwort"] or titel_ohne_stichwort(a)


def meta_teile(a, komma=False):
    """Antragsteller (gegen Gegenantrag), Artikel, Zusatz."""
    teile = []
    fmt = wer_komma if komma else wer_klammer
    if a["wer"]:
        s = fmt(a["wer"])
        if a["gegen"]:
            s += " gegen " + fmt(a["gegen"])
        teile.append(s)
    elif a["stichwort"] and not a["ungueltig"]:
        # ohne Antragsteller: der formale Titel sagt, worüber abgestimmt wurde
        teile.append(a["referenz"] or kuerze(a["titel"], 60))
    elif a["referenz"]:
        teile.append(a["referenz"])
    if a["artikel"]:
        teile.append(a["artikel"])
    if a["zusatz"]:
        teile.append(a["zusatz"])
    return teile


def gruppen(votes):
    """Aufeinanderfolgende Abstimmungen desselben Geschäfts."""
    aus = []
    for a in votes:
        g = a["geschaeft"] or ""
        if aus and aus[-1]["geschaeft"] == g:
            aus[-1]["votes"].append(a)
        else:
            aus.append({"geschaeft": g, "votes": [a]})
    return aus


def untertitel(gruppe):
    """«Anträge aus dem Rat zur Fassung der Spezialkommission», wenn die Gruppe nur
    aus Anträgen besteht und die Mehrheit gegen dieselbe Fassung gestellt ist."""
    vs = [a for a in gruppe["votes"] if not a["ungueltig"]]
    if not vs or not all(re.match(r"^Antrag\s", a["titel_roh"]) for a in vs):
        return ""
    zahl = collections.Counter()
    for a in vs:
        m = re.search(r"Zustimmung (?:Antrag )?(SPK|GPK/RR|GPK|GESKO)\b", a["ja_note"], re.I)
        if m:
            zahl[m.group(1).upper()] += 1
    if not zahl:
        return ""
    k, n = zahl.most_common(1)[0]
    if 2 * n < len(vs):
        return ""
    return "Anträge aus dem Rat zur Fassung " + KOMMISSION[k]


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


def chip(d, xy, text, key, gross=True, mini=False):
    """Ergebnis-Chip. gross: Karte; klein: bisherige Liste; mini: Deckblatt."""
    if mini:
        f, h, px = font("a", 21, "SemiBold"), 30, 12
    elif gross:
        f, h, px = font("a", 34, "SemiBold"), 56, 22
    else:
        f, h, px = font("a", 24, "SemiBold"), 40, 14
    x, y = xy
    tb = breite(d, text, f)
    rund(d, (x, y, x + tb + 2 * px, y + h), h / 2, CHIP.get(key, STIMME.get(key, TEXT3)))
    d.text((x + px, y + h / 2), text, font=f, fill="#FFFFFF", anchor="lm")
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
    h = min(y_ende, inhalt.height, y_unten - y_oben)
    frei = y_unten - y_oben
    y = y_oben + max(0, (frei - h) // 2)
    img.paste(inhalt.crop((0, 0, inhalt.width, h)), (0, y))


def titelblock(d, sess, y, teil=None, teile=1):
    datum, zeit = datum_lang(sess["sitzung"])
    d.text((72, y), f"Kantonsrat, {datum}", font=font("a", 54, "Bold"), fill=TEXT)
    y += 68
    n = sess["n_votes"]
    satz = (f"{zeit} · " if zeit else "") + f"{n} namentliche Abstimmung{'en' if n != 1 else ''}"
    if teil:
        satz += f" · Teil {teil} von {teile}"
    d.text((72, y), satz, font=font("p", 29, "Regular"), fill=TEXT3)
    return y + 58


def gruppenkopf(d, W, y, gruppe):
    """Kasten mit dem Namen des Geschäfts und, falls bestimmbar, der Art der Anträge."""
    if not gruppe["geschaeft"]:
        return y
    ft = font("a", 36, "SemiBold")
    zeilen = umbrechen(d, gruppe["geschaeft"], ft, W - 144 - 56, 2)
    ut = untertitel(gruppe)
    h = 13 + 43 * len(zeilen) + (34 if ut else 10)
    rund(d, (72, y, W - 72, y + h), 14, KASTEN)
    yy = y + 13
    for z in zeilen:
        d.text((100, yy), z, font=ft, fill=TEXT)
        yy += 43
    if ut:
        d.text((100, yy), ut, font=font("p", 23, "Regular"), fill=TEXT2)
    return y + h + 22


# ── Deckblatt Karussell (1080 x 1350) ───────────────────────────────────────
def _deckblatt_inhalt(inhalt, sess, votes, teil, teile, abstand, max_z):
    W = inhalt.width
    d = ImageDraw.Draw(inhalt)
    y = titelblock(d, sess, 0, teil, teile)
    fk = font("p", 30, "SemiBold")
    fm = font("p", 23, "Regular")
    x = 124
    for g in gruppen(votes):
        y = gruppenkopf(d, W, y, g)
        for a in g["votes"]:
            d.text((72, y + 3), str(a["nr"]), font=font("a", 28, "SemiBold"), fill=TEXT3)
            zeilen = umbrechen(d, zeilentitel(a), fk, W - 72 - x, max_z)
            for k, z in enumerate(zeilen):
                d.text((x, y + 38 * k), z, font=fk, fill=TEXT)
            yy = y + 38 * len(zeilen) + 4
            xe = chip(d, (x, yy), a["ergebnis"], a["ekey"], mini=True)
            meta = " · ".join(meta_teile(a))
            if meta:
                meta = umbrechen(d, meta, fm, W - 72 - xe - 14, 1)[0]
                d.text((xe + 14, yy + 15), meta, font=fm, fill=TEXT3, anchor="lm")
            y = yy + 30 + abstand
    return y - abstand


def deckblatt(groesse, sess, votes, teil=None, teile=1):
    W, H = groesse
    for abstand, max_z in ((17, 2), (12, 2), (8, 2), (8, 1), (4, 1)):
        img, y0, y1 = rahmen(groesse, "Politspiegel Schaffhausen", "Kantonsratsspiegel")
        inhalt = Image.new("RGB", (W, (y1 - y0) + 800), GRUND)
        y = _deckblatt_inhalt(inhalt, sess, votes, teil, teile, abstand, max_z)
        if y <= y1 - y0:
            break
    einpassen(img, inhalt, y0, y1, y)
    return img


# ── Deckblatt Reel (1080 x 1920): eine Zeile je Abstimmung, ohne Namen ──────
def deckblatt_reel(groesse, sess, votes):
    W, H = groesse
    img, y0, y1 = rahmen(groesse, "Politspiegel Schaffhausen", "Kantonsratsspiegel")
    frei = y1 - y0
    inhalt = Image.new("RGB", (W, frei + 400), GRUND)
    d = ImageDraw.Draw(inhalt)
    y = titelblock(d, sess, 0)

    # Legende der Ergebnisfarben
    fl = font("p", 25, "Regular")
    x = 72
    arten = [("Angenommen", "ja"), ("Abgelehnt", "nein")]
    if any(a["ekey"] == "enth" for a in votes):
        arten.append(("Ungültig oder Stimmengleichheit", "enth"))
    for text, key in arten:
        d.ellipse((x, y + 6, x + 26, y + 32), fill=CHIP[key])
        d.text((x + 36, y + 19), text, font=fl, fill=TEXT2, anchor="lm")
        x += 36 + breite(d, text, fl) + 34
    y += 58

    gs = gruppen(votes)
    kopf_h = sum((66 if not untertitel(g) else 90) + 22 for g in gs if g["geschaeft"])
    zeile = int(max(40, min(56, (frei - y - kopf_h) / max(1, len(votes)))))
    fk = font("p", 28 if zeile >= 50 else 25, "SemiBold")
    fz = font("a", 20 if zeile >= 50 else 18, "SemiBold")
    r = 19 if zeile >= 50 else 16
    gezeigt = 0
    for g in gs:
        if y + zeile > frei:
            break
        y = gruppenkopf(d, W, y, g)
        for a in g["votes"]:
            if y + zeile > frei:
                break
            cy = y + zeile / 2 - 4
            d.ellipse((72, cy - r, 72 + 2 * r, cy + r), fill=CHIP[a["ekey"]])
            d.text((72 + r, cy), str(a["nr"]), font=fz, fill="#FFFFFF", anchor="mm")
            t = umbrechen(d, zeilentitel(a), fk, W - 72 - 126, 1)[0]
            d.text((126, cy), t, font=fk, fill=TEXT, anchor="lm")
            y += zeile
            gezeigt += 1
    if gezeigt < len(votes):
        d.text((126, y + 6), f"… und {len(votes) - gezeigt} weitere", font=fk, fill=TEXT3)
        y += zeile
    einpassen(img, inhalt, y0, y1, y)
    return img


# ── Antragstext mit Streichungen und Einfügungen ────────────────────────────
KOPF_ANTRAG = re.compile(r"Antrag\s+[A-ZÄÖÜ]\.\s*[A-ZÄÖÜ][\wäöüÄÖÜéè'-]+")
ELL = {"laeufe": [("gleich", "…")], "leer": "gleich", "geaendert": False, "ell": True}


def antragstext_absaetze(a, sess):
    """Segmente → Absätze [(Beschriftung, [(Zeichen, Art)])]. Der Kopf «Anpassung
    Art. 18 Abs. 1a wie folgt:» entfällt, er steht in der Kopfzeile der Karte.
    Bei einer Ausmehrung stehen beide Anträge untereinander."""
    zeichen = [(c, art) for art, t in a["segmente"] for c in t]
    voll = "".join(c for c, _ in zeichen)
    starts = [m.end() for m in re.finditer(r"wie folgt:\s*", voll)]
    if not starts:
        m = re.match(r"^[^:]{3,60}:\s*", voll)
        starts = [m.end() if m else 0]
    bereiche, schilder = [], [None]
    for k, s in enumerate(starts):
        if k + 1 < len(starts):
            zwischen = voll[s:starts[k + 1]]
            treffer = list(KOPF_ANTRAG.finditer(zwischen))
            if treffer:
                bereiche.append((s, s + treffer[-1].start()))
                schilder.append(treffer[-1].group(0))
            else:
                bereiche.append((s, starts[k + 1]))
                schilder.append(None)
        else:
            bereiche.append((s, len(voll)))
    if len(bereiche) > 1:
        schilder[0] = a["titel_roh"]
    absaetze = []
    for (s, e), sch in zip(bereiche, schilder):
        stueck = zeichen[s:e]
        while stueck and stueck[-1][0] in " ;" and stueck[-1][1] == "gleich":
            stueck = stueck[:-1]
        while stueck and stueck[0][0] == " ":
            stueck = stueck[1:]
        if not stueck:
            continue
        if sch:
            p = person(sess, re.sub(r"^Antrag\s+", "", sch))
            sch = "Antrag " + (wer_klammer(p) if p else re.sub(r"^Antrag\s+", "", sch))
        absaetze.append((sch, stueck))
    return absaetze


def _woerter(zeichen):
    """Zeichen mit Art → Wörter {laeufe: [(Art, Text)], leer: Art des folgenden
    Leerraums, geaendert: enthält Streichung oder Einfügung}."""
    toks, akt = [], []
    for c, art in zeichen:
        if c == " ":
            if akt:
                toks.append({"laeufe": akt, "leer": art})
                akt = []
            continue
        if akt and akt[-1][0] == art:
            akt[-1] = (art, akt[-1][1] + c)
        else:
            akt.append((art, c))
    if akt:
        toks.append({"laeufe": akt, "leer": "gleich"})
    for t in toks:
        t["geaendert"] = any(art != "gleich" for art, _ in t["laeufe"])
    return toks


def _text(tok):
    return "".join(t for _, t in tok["laeufe"])


def _ohne_ganze_saetze(toks):
    """Unveränderte Sätze durch «…» ersetzen. Ohne Markierung bleibt alles."""
    if not any(t["geaendert"] for t in toks):
        return toks
    saetze, akt = [], []
    for k, t in enumerate(toks):
        akt.append(t)
        nxt = toks[k + 1] if k + 1 < len(toks) else None
        if nxt and _text(t)[-1:] in ".;!?" and (_text(nxt)[:1].isupper() or _text(nxt)[:1] == "("):
            saetze.append(akt)
            akt = []
    if akt:
        saetze.append(akt)
    aus, weg = [], False
    for s in saetze:
        if any(t["geaendert"] for t in s):
            if weg:
                aus.append(ELL)
            weg = False
            aus += s
        else:
            weg = True
    if weg:
        aus.append(ELL)
    return aus


def _fenster(toks, k):
    """Unveränderte Wörter, die mehr als k Wörter von einer Änderung entfernt
    stehen, durch «…» ersetzen."""
    idx = [i for i, t in enumerate(toks) if t["geaendert"]]
    if not idx:
        return toks
    behalten = set()
    for i in idx:
        behalten.update(range(max(0, i - k), min(len(toks), i + k + 1)))
    aus, weg = [], False
    for i, t in enumerate(toks):
        if i in behalten and not t.get("ell"):
            if weg and not (aus and aus[-1].get("ell")):
                aus.append(ELL)
            weg = False
            aus.append(t)
        else:
            weg = True
    if weg and not (aus and aus[-1].get("ell")):
        aus.append(ELL)
    return aus


def _zeilen(d, absaetze, f, fb, max_b):
    """Absätze aus Wörtern → Zeilen aus Läufen [(Art, Text)]. Wörter bleiben ganz;
    ein Leerschlag zwischen zwei eingefügten Wörtern bleibt markiert."""
    zeilen = []
    for schild, toks in absaetze:
        zeile, x = [], 0.0
        if schild:
            t = schild + ": "
            zeile.append(("schild", t))
            x = breite(d, t, fb)
        vor = None
        for tok in toks:
            laeufe = tok["laeufe"]
            wb = sum(breite(d, t, f) for _, t in laeufe)
            sb = breite(d, " ", f) if zeile and zeile[-1][0] != "schild" else 0
            if zeile and x + sb + wb > max_b:
                zeilen.append(zeile)
                zeile, x, sb = [], 0.0, 0
            if sb:
                art = "gleich"
                if vor and vor["leer"] == vor["laeufe"][-1][0] == laeufe[0][0] != "gleich":
                    art = vor["leer"]
                zeile.append((art, " "))
                x += sb
            zeile.extend(laeufe)
            x += wb
            vor = tok
        if zeile:
            zeilen.append(zeile)
    return zeilen


def _laeufe_zeichnen(d, xy, zeile, f, fb, lh):
    x, y = xy
    for art, t in zeile:
        ff = fb if art == "schild" else f
        w = breite(d, t, ff)
        if art == "neu":
            d.rectangle((x - 1, y + 3, x + w + 1, y + lh - 5), fill=MARKER)
            d.text((x, y), t, font=ff, fill=TEXT)
        elif art == "alt":
            d.text((x, y), t, font=ff, fill=TEXT3)
            if t.strip():
                ym = y + lh * 0.46
                d.line((x, ym, x + w, ym), fill=TEXT3, width=2)
        elif art == "schild":
            d.text((x, y), t, font=ff, fill=TEXT)
        else:
            d.text((x, y), t, font=ff, fill=TEXT2)
        x += w


def antragstext_kasten(d, W, y, a, sess, max_zeilen):
    """Weisser Kasten mit dem Antragstext. Passt der Text nicht, werden zuerst
    unveränderte Sätze, dann unveränderte Wörter fern der Änderung durch «…»
    ersetzt, damit Streichung und Einfügung immer sichtbar bleiben. Gibt die
    y-Position nach dem Kasten zurück."""
    roh = [(sch, _woerter(z)) for sch, z in antragstext_absaetze(a, sess)]
    if not roh:
        return y
    markiert = any(t["geaendert"] for _, toks in roh for t in toks)
    f, fb = font("p", 25, "Regular"), font("p", 25, "SemiBold")
    lh = 34
    innen = W - 144 - 48
    stufen = [lambda t: t, _ohne_ganze_saetze] + [
        (lambda k: (lambda t: _fenster(_ohne_ganze_saetze(t), k)))(k) for k in (12, 8, 5, 3, 1)]
    for stufe in stufen:
        zeilen = _zeilen(d, [(sch, stufe(toks)) for sch, toks in roh], f, fb, innen)
        if len(zeilen) <= max_zeilen:
            break
    if len(zeilen) > max_zeilen:
        zeilen = zeilen[:max_zeilen]
        letzte = zeilen[-1]
        while letzte and sum(breite(d, t, fb if art == "schild" else f)
                             for art, t in letzte) + breite(d, " …", f) > innen:
            letzte = letzte[:-1]
        zeilen[-1] = letzte + [("gleich", " …")]
    hinweise = [h for h in a["hinweise"] if h]
    fh = font("p", 22, "Regular")
    h = 14 + 34 + lh * len(zeilen) + (30 * len(hinweise)) + 10
    rund(d, (72, y, W - 72, y + h), 14, KARTE, outline=LINIE, w=2)
    fk = font("p", 22, "SemiBold")
    d.text((96, y + 14), "Antragstext" if markiert else "Wortlaut", font=fk, fill=TEXT3)
    if markiert:
        # Legende rechts: gestrichen / neu
        fl = font("p", 21, "Regular")
        t_neu, t_alt = "neu", "gestrichen"
        xr = W - 96 - breite(d, t_neu, fl)
        d.rectangle((xr - 3, y + 15, xr + breite(d, t_neu, fl) + 3, y + 42), fill=MARKER)
        d.text((xr, y + 14), t_neu, font=fl, fill=TEXT)
        xa = xr - 26 - breite(d, t_alt, fl)
        d.text((xa, y + 14), t_alt, font=fl, fill=TEXT3)
        d.line((xa, y + 28, xa + breite(d, t_alt, fl), y + 28), fill=TEXT3, width=2)
    yy = y + 14 + 34
    for z in zeilen:
        _laeufe_zeichnen(d, (96, yy), z, f, fb, lh)
        yy += lh
    for hw in hinweise:
        d.text((96, yy + 1), umbrechen(d, hw, fh, innen, 1)[0], font=fh, fill=TEXT3)
        yy += 30
    return y + h


# ── Karte je Abstimmung ──────────────────────────────────────────────────────
def wer_satz(a):
    """«Antrag B. Looser (SP)», bei einer Ausmehrung beide Anträge."""
    if a["wer"]:
        s = "Antrag " + wer_klammer(a["wer"])
        if a["gegen"]:
            s = "Ausmehrung: " + s + " gegen Antrag " + wer_klammer(a["gegen"])
        if a["zusatz"] == "Fassung Regierungsrat":
            s += ": Rückkehr auf die Fassung des Regierungsrats"
        elif a["zusatz"]:
            s += " · " + a["zusatz"]
        return s
    if a["stichwort"]:
        return a["referenz"] or a["titel"]
    return a["referenz"]


def _karte_inhalt(inhalt, sess, a, max_text):
    W = inhalt.width
    d = ImageDraw.Draw(inhalt)
    innen = W - 144
    y = 0

    # Geschäft und Artikel
    kick = " · ".join(t for t in (a["geschaeft"], a["artikel_lang"]) if t)
    if kick:
        fk = font("p", 26, "Medium")
        d.text((72, y), umbrechen(d, kick, fk, innen, 1)[0], font=fk, fill=TEXT3)
        y += 40
    # Stichworte als Titel
    titel = zeilentitel(a) if (a["stichwort"] or a["ungueltig"]) else a["titel"]
    y = absatz(d, (72, y), titel, font("a", 46, "SemiBold"), TEXT, innen, 56, max_zeilen=3)
    ws = wer_satz(a)
    if ws:
        y += 4
        y = absatz(d, (72, y), ws, font("p", 28, "Regular"), TEXT2, innen, 38, 2)

    # Ergebnis mit Stimmenzahlen
    y += 22
    xe = chip(d, (72, y), a["ergebnis"], a["ekey"])
    c = a["c"]
    zahlen = f"Ja {c['ja']} · Nein {c['nein']} · Enthaltung {c['enth']} · abwesend {c['abw']}"
    fz = font("p", 28, "Regular")
    if breite(d, zahlen, fz) <= W - 72 - xe - 24:
        d.text((xe + 24, y + 28), zahlen, font=fz, fill=TEXT2, anchor="lm")
        y += 74
    else:
        y += 70
        d.text((72, y), zahlen, font=fz, fill=TEXT2)
        y += 44

    # Antragstext
    if a["segmente"] and not a["ungueltig"]:
        y = antragstext_kasten(d, W, y, a, sess, max_text) + 16

    # Bedeutung von Ja und Nein
    bz = [t for t in (bedeutung(a["ja_note"], "Ja"), bedeutung(a["nein_note"], "Nein")) if t]
    if bz:
        fh = font("p", 25, "Medium")
        zeilen = [z for t in bz for z in umbrechen(d, t, fh, innen - 48, 2)]
        hh = 20 + 33 * len(zeilen)
        rund(d, (72, y, W - 72, y + hh), 12, "#EEF2F7", outline=LINIE, w=2)
        yy = y + 10
        for z in zeilen:
            d.text((96, yy), z, font=fh, fill=TEXT)
            yy += 33
        y += hh + 16

    balken_rund(inhalt, (72, y, W - 72, y + 58), c, a["total"], f=font("a", 30, "SemiBold"))
    y += 58

    # Fraktionen
    y += 30
    d.text((72, y), "Nach Fraktion", font=font("a", 30, "SemiBold"), fill=TEXT)
    y += 46
    fname = font("p", 28, "Medium")
    fzahl = font("a", 28, "SemiBold")
    zeile = 56
    namen_b = 330
    for f in a["frak"]:
        d.ellipse((72, y + 11, 94, y + 33), fill=PARTEI.get(f["key"], PARTEI["none"]))
        name = FRAK_KURZ.get(f["name"], f["name"])
        name = umbrechen(d, name, fname, namen_b - 40, 1)[0]
        d.text((108, y + 22), name, font=fname, fill=TEXT, anchor="lm")
        bx0 = 72 + namen_b
        bx1 = W - 72 - 130
        balken_rund(inhalt, (bx0, y + 2, bx1, y + 42), f["c"], f["total"], f=font("a", 24, "SemiBold"))
        cc = f["c"]
        d.text((W - 72, y + 22), f"{cc['ja']} : {cc['nein']}", font=fzahl, fill=TEXT2, anchor="rm")
        y += zeile

    # Legende
    y += 4
    fl = font("p", 25, "Regular")
    x = 72
    for k in ["ja", "nein", "enth", "abw"]:
        d.rounded_rectangle((x, y + 6, x + 24, y + 30), 5, fill=STIMME[k],
                            outline=LINIE if k == "abw" else None)
        d.text((x + 34, y + 18), STIMME_LABEL[k], font=fl, fill=TEXT3, anchor="lm")
        x += 34 + breite(d, STIMME_LABEL[k], fl) + 38
    y += 40
    return y


def karte(groesse, sess, a, pos, gesamt_n):
    W, H = groesse
    datum, _ = datum_lang(sess["sitzung"])
    for max_text in (9, 8, 7, 6, 5, 4, 3, 2):
        img, y0, y1 = rahmen(groesse, "Kantonsrat · " + datum, f"Abstimmung {pos} von {gesamt_n}")
        inhalt = Image.new("RGB", (W, (y1 - y0) + 900), GRUND)
        y = _karte_inhalt(inhalt, sess, a, max_text)
        if y <= y1 - y0:
            break
    einpassen(img, inhalt, y0, y1, y)
    return img


def schluss(groesse, sess):
    W, H = groesse
    img = Image.new("RGB", groesse, GRUND)
    d = ImageDraw.Draw(img)
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
    data/parteien_social.json. YouTube bekommt nur Namen: die Handles sind die
    von Instagram und TikTok und würden dort auf fremde Kanäle zeigen."""
    liste = quelle("parteien_social.json").get("parteien")
    if not liste:
        return ""
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
        h = e.get(netz) if e and netz in ("instagram", "tiktok") else None
        name = PARTEI_ANZEIGE.get(k.upper(), k)
        teile.append(("@" + h) if h else name)
    return "Parteien im Rat: " + ", ".join(teile)


def medien_zeile(netz):
    """«Medien: @…» aus data/medien_social.json, gleiche Regeln wie bei den Parteien."""
    liste = quelle("medien_social.json").get("medien")
    if not liste:
        return ""
    teile = []
    for e in liste:
        h = e.get(netz) if netz in ("instagram", "tiktok") else None
        teile.append(("@" + h) if h else e["medium"])
    return "Medien: " + ", ".join(teile)


def konten_block(netz, sess):
    return [z for z in (parteien_zeile(netz, sess), medien_zeile(netz)) if z]


def erwaehnungen(text):
    return len(re.findall(r"(?<![\w@])@[\w.]+", text))


def kopfsatz(sess, teil=None, teile=1):
    datum, zeit = datum_lang(sess["sitzung"])
    n = sess["n_votes"]
    s = (f"Kantonsrat Schaffhausen, {datum}" + (f", {zeit}" if zeit else "")
         + f": {n} namentliche Abstimmung{'en' if n != 1 else ''}.")
    if teil and teile > 1:
        s += f" Teil {teil} von {teile}."
    return s


def text_karussell(sess, votes, teil, teile, url_ordner, netz="instagram"):
    zeilen = [kopfsatz(sess, teil, teile)]
    for g in gruppen(votes):
        zeilen.append("")
        if g["geschaeft"]:
            ut = untertitel(g)
            zeilen.append(g["geschaeft"] + (f" ({ut})" if ut else "") + ":")
        for a in g["votes"]:
            z = f"{a['nr']}. {zeilentitel(a)}"
            meta = " · ".join(meta_teile(a, komma=True))
            if meta:
                z += f" ({meta})"
            zeilen.append(z + f": {a['ergebnis']}")
    schluss_ = ["", "Alle Details, Fraktionen und Namen: " + SEITE_URL,
                "Quelle: Abstimmungsprotokolle des Kantonsrats, sh.ch"]
    kb = konten_block(netz, sess)
    if kb:
        schluss_ += [""] + kb
    schluss_ += ["", "#Schaffhausen #Kantonsrat #Politspiegel"]
    t = "\n".join(zeilen + schluss_)
    if len(t) > 2150:   # Instagram: 2200 Zeichen
        t = kuerze("\n".join(zeilen), 2140 - len("\n".join(schluss_))) + "\n" + "\n".join(schluss_)
    return t


def geschaefte_satz(votes):
    gs = list(dict.fromkeys(g["geschaeft"] for g in gruppen(votes) if g["geschaeft"]))
    if not gs:
        return ""
    s = "Behandelt: " + "; ".join(gs[:3])
    if len(gs) > 3:
        s += f" und {len(gs) - 3} weitere Geschäfte"
    return s.rstrip(".") + "."


def text_reel(sess, votes, netz="instagram"):
    teile = [kopfsatz(sess)]
    gsatz = geschaefte_satz(votes)
    if gsatz:
        teile.append(gsatz)
    teile.append(f"Wer wie gestimmt hat: {SEITE_URL}")
    t = " ".join(teile)
    kb = konten_block(netz, sess)
    if kb:
        t += "\n\n" + "\n".join(kb)
    return t + "\n\n#Schaffhausen #Kantonsrat #Politspiegel"


def youtube_titel(sess, votes):
    datum, _ = datum_lang(sess["sitzung"])
    gs = list(dict.fromkeys(g["geschaeft"] for g in gruppen(votes) if g["geschaeft"]))
    t = f"Kantonsrat Schaffhausen, {datum}: {gs[0]}" if len(gs) == 1 else ""
    if not t or len(t) > 100:
        t = f"Kantonsrat Schaffhausen, {datum}: {len(votes)} Abstimmungen"
    return t


# ── Hauptlauf ────────────────────────────────────────────────────────────────
def alte_angaben(ordner):
    """Metricool-Angaben und Status aus einer bestehenden posts.json, damit ein
    Neuerzeugen die Verbindung zu den Entwürfen nicht verliert."""
    p = ordner / "posts.json"
    if not p.exists():
        return {}, {}
    d = json.loads(p.read_text(encoding="utf-8"))
    je = {}
    for x in d.get("posts", []):
        k = (x.get("art"), x.get("teil"), x.get("netz"))
        je[k] = {kk: x[kk] for kk in ("metricool", "status") if kk in x}
    kopf_ = {kk: d[kk] for kk in ("status", "hinweis") if kk in d}
    return kopf_, je


def sitzung_bauen(sess, ordner, mit_video=True):
    ordner.mkdir(parents=True, exist_ok=True)
    kopf_alt, je_alt = alte_angaben(ordner)
    markierungen_sicherstellen(sess)
    votes = [auswerten(sess, i, v) for i, v in enumerate(sess["votes"])]
    n = len(votes)
    url_ordner = BASIS_URL + "social/kantonsrat/" + ordner.name + "/"
    posts = []
    ohne = [a["nr"] for a in votes if not a["stichwort"] and not a["ungueltig"]]
    if ohne:
        print(f"  OHNE STICHWORT, dort steht der Titel aus dem Protokoll: Nr. {', '.join(map(str, ohne))}.\n"
              f"  Stichworte in data/stichworte.json unter «{ordner.name}» ergänzen "
              "(Regeln: docs/KONZEPT_social-media.md, Abschnitt 2, Punkt 8), dann mit --neu wiederholen.")

    # Karussell(e), je höchstens MAX_KARUSSELL Bilder inkl. Deckblatt
    je = MAX_KARUSSELL - 1
    gruppen_k = [votes[i:i + je] for i in range(0, n, je)] or [[]]
    lauf = 0
    for gi, gruppe in enumerate(gruppen_k, 1):
        medien = []
        img = deckblatt(FEED, sess, gruppe, teil=gi if len(gruppen_k) > 1 else None,
                        teile=len(gruppen_k))
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
        # Karussell nur für Instagram. Facebook wird seit 27. September 2026 nicht
        # mehr bespielt (Metricool-Kontingent, docs/KONZEPT_social-media.md).
        posts.append({
            "art": "karussell", "teil": gi, "teile": len(gruppen_k), "netz": "instagram",
            "text": text_karussell(sess, gruppe, gi, len(gruppen_k), url_ordner, "instagram"),
            "media": medien,
            "providers": ["instagram"],
            "instagram": {"type": "POST"},
        })
        # Kein TikTok-Fotobeitrag: TikTok nimmt über Metricool nur JPEG oder WebP
        # an, und Michael will dort ohnehin nur Videos (Entscheid 6. September 2026).

    # Reel: Deckblatt, alle Karten, Schlussbild
    if mit_video:
        bilder, dauern = [], []
        img = deckblatt_reel(REEL, sess, votes)
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
        reel_da = video(bilder, dauern, ordner / "reel.mp4")
    else:
        # Ohne Video bleibt das vorhandene reel.mp4; die Texte werden trotzdem neu
        # geschrieben, damit Stichworte und Erwähnungen stimmen.
        reel_da = (ordner / "reel.mp4").exists()
        dauern = [3.5] + [4.0] * n + [3.0]
    if reel_da:
        gemeinsam = {"media": [url_ordner + "reel.mp4"], "dauer_s": sum(dauern)}
        # Je Netz ein eigener Beitrag, weil Metricool nur einen Text je Beitrag
        # kennt und die @-Erwähnungen je Netz verschieden sind. Das Kontingent
        # zählt je Netz, drei Beiträge kosten gleich viel wie einer mit drei Netzen.
        posts.append({
            "art": "reel", "netz": "instagram", "text": text_reel(sess, votes, "instagram"),
            **gemeinsam, "providers": ["instagram"],
            "instagram": {"type": "REEL", "showReelOnFeed": True},
        })
        posts.append({
            "art": "reel", "netz": "youtube", "text": text_reel(sess, votes, "youtube"),
            **gemeinsam, "providers": ["youtube"],
            "youtube": {"type": "short", "title": youtube_titel(sess, votes),
                        "privacy": "public", "madeForKids": False,
                        "category": "NEWS_POLITICS"},
        })
        posts.append({
            "art": "reel", "netz": "tiktok", "text": text_reel(sess, votes, "tiktok"),
            **gemeinsam, "providers": ["tiktok"],
            "tiktok": {"privacyOption": "PUBLIC_TO_EVERYONE"},
        })

    for p in posts:
        k = (p.get("art"), p.get("teil"), p.get("netz"))
        if k in je_alt:
            p.update(je_alt[k])
        if "instagram" in p["providers"] and erwaehnungen(p["text"]) > MAX_ERWAEHNUNGEN:
            print(f"  WARNUNG {p['art']} {p.get('teil') or ''}: {erwaehnungen(p['text'])} "
                  f"@-Erwähnungen, Instagram nimmt höchstens {MAX_ERWAEHNUNGEN}.")

    daten = {
        "sitzung": sess["sitzung"], "slug": ordner.name, "n_votes": n,
        "quelle": sess.get("url"), "status": kopf_alt.get("status", "entwurf"),
        "kontingent": sum(len(p["providers"]) for p in posts),
        "neu_erzeugt": date.today().isoformat(),
        "abstimmungen": [{"nr": a["nr"], "titel": a["titel"], "stichwort": a["stichwort"],
                          "ergebnis": a["ergebnis"], "c": a["c"]} for a in votes],
        "posts": posts,
    }
    if "hinweis" in kopf_alt:
        daten["hinweis"] = kopf_alt["hinweis"]
    (ordner / "posts.json").write_text(json.dumps(daten, ensure_ascii=False, indent=1),
                                       encoding="utf-8")
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
            print(f"  {p['art']} {p['netz']}: {len(p['media'])} Medien, {len(p['text'])} Zeichen Text, "
                  f"{erwaehnungen(p['text'])} Erwähnungen")
        print(f"  Ordner: {ordner.relative_to(ROOT)}")
        print(f"  Kontingent dieser Charge: {sum(len(p['providers']) for p in posts)} (Veröffentlichungen je Netz). "
              "Vor dem Anlegen in Metricool die Monatszählung nach docs/KONZEPT_social-media.md, Abschnitt 1a.")
        print(f"  Adresse nach dem Veröffentlichen: {BASIS_URL}social/kantonsrat/{ordner.name}/")


if __name__ == "__main__":
    main()

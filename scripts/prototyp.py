#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prototyp der Startseite «Zuletzt entschieden» im neuen Design.

Setzt die Design-Entscheide vom 01.09.2026 um (siehe docs/DESIGN_entscheide.md):
Seitenleiste, Mischstil aus weichen Karten und Haarlinien, Archivo + Public Sans,
neutrale Ja/Nein-Farben, Dunkelmodus, luftige Darstellung mit Aufklappen.

Erzeugt eine eigenstaendige HTML-Datei und laesst das bestehende Dashboard unberuehrt.

    python3 scripts/prototyp.py
"""

import collections
import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "all_sessions.json"
UMKEHR = ROOT / "data" / "umkehr_zuordnung.json"
OUT = ROOT / "output" / "prototyp-zuletzt-entschieden.html"

# Woher der Richtungsentscheid stammt, in Worten fürs Publikum
HERKUNFT = {
    "protokoll": "am Wortprotokoll überprüft",
    "manuell": "von Hand am Wortprotokoll geprüft",
    "konvention": "nach Konvention für Sachtitel",
    "regel": "regelbasiert, nicht am Protokoll überprüft",
}

# ─────────────────────────────────────────────────────────────────────────────
# Farbzuordnung  (Basis: srfdata/swiss-party-colors, CC BY-SA 4.0)
# Zwei bewusste Abweichungen: AL wird Magenta, GLP bekommt eine dunklere
# Textvariante. Siehe docs/DESIGN_entscheide.md.
# ─────────────────────────────────────────────────────────────────────────────

FRAK_KEY = {
    "SVP-EDU": "svp",
    "SP": "sp", "SP-JUSO": "sp", "SP-JUSO-GRÜNE-Junge Grüne": "sp",
    "GLP-EVP": "glp",
    "FDP-Die Mitte": "fdp", "FDP-Die Mitte-JF": "fdp",
    "FDP-CVP": "fdp", "FDP-CVP-JF": "fdp",
    "AL-Grüne": "al", "AL-GRÜNE-Junge Grüne": "al", "AL-GRÜNE-JUNGE GRÜNE": "al",
    "GRÜNE-Junge Grüne": "gru",
}
PARTEI_KEY = {
    "svp": "svp", "jsvp": "svp", "svp senioren": "svp", "svp agro": "svp", "svp kmu": "svp",
    "edu": "edu",
    "sp": "sp", "juso": "sp",
    "grüne": "gru", "junge grüne": "gru",
    "al": "al", "al-grüne": "al",
    "glp": "glp", "evp": "evp",
    "fdp": "fdp", "jf": "fdp", "jfdp": "fdp",
    "die mitte": "mitte", "cvp": "mitte",
    "parteilos": "none",
}

# Reihenfolge der Fraktionen: nach Sitzzahl, absteigend
STIMME_ORDER = ["Ja", "Nein", "Enth", "V/A/N"]
STIMME_KEY = {"Ja": "ja", "Nein": "nein", "Enth": "enth", "V/A/N": "abw"}
STIMME_LABEL = {"ja": "Ja", "nein": "Nein", "enth": "Enthaltung", "abw": "abwesend"}

ICONS = {
    "neu": '<path d="M2.5 8.5l4 4 7-9" stroke="currentColor" stroke-width="1.7" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
    "vote": '<rect x="2.5" y="3" width="11" height="10" rx="1.6" stroke="currentColor" stroke-width="1.5" fill="none"/><path d="M5.4 8.3l1.8 1.8 3.4-3.9" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
    "people": '<circle cx="6.2" cy="6" r="2.4" stroke="currentColor" stroke-width="1.5" fill="none"/><path d="M2.2 14c0-2.2 1.8-3.7 4-3.7s4 1.5 4 3.7" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round"/><path d="M11.2 5.3a2.2 2.2 0 0 1 0 4.4M12.4 13.6c0-1.6-.6-2.7-1.4-3.3" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round"/>',
    "group": '<rect x="2" y="9" width="3.4" height="5" rx="1" stroke="currentColor" stroke-width="1.5" fill="none"/><rect x="6.3" y="5.4" width="3.4" height="8.6" rx="1" stroke="currentColor" stroke-width="1.5" fill="none"/><rect x="10.6" y="2.6" width="3.4" height="11.4" rx="1" stroke="currentColor" stroke-width="1.5" fill="none"/>',
    "tag": '<path d="M8.6 2H14v5.4l-6.3 6.3a1.4 1.4 0 0 1-2 0L2.3 10.3a1.4 1.4 0 0 1 0-2z" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linejoin="round"/><circle cx="11" cy="5" r="1" fill="currentColor"/>',
    "rank": '<path d="M2.6 13.4V9.2M8 13.4V3.2M13.4 13.4V6.6" stroke="currentColor" stroke-width="1.7" fill="none" stroke-linecap="round"/>',
}

NAV = [
    ("Zuletzt entschieden", "neu", True),
    ("Abstimmungen", "vote", False),
    ("Ratsmitglieder", "people", False),
    ("Fraktionen", "group", False),
    ("Themen", "tag", False),
    ("Ranglisten", "rank", False),
]


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def flach(s):
    return re.sub(r"\s+", " ", (s or "")).strip()


# ─────────────────────────────────────────────────────────────────────────────
# Sprechende Überschriften
#
# Die Quelldaten benennen Abstimmungen oft nur formal («Antrag P. Scheck») oder
# umgekehrt sehr weitschweifig («Postulat Nr. 2026/4 von Linda De Ventura vom
# 30. März 2026 betreffend …»). Die folgenden Funktionen holen den Sachtitel
# nach vorne und schieben die formale Referenz in eine zweite Zeile.
# ─────────────────────────────────────────────────────────────────────────────

VORSTOSS_ART = (r"(Volksmotion|Motion|Postulat|Interpellation|Kleine Anfrage|"
                r"Petition|Beschlussantrag)")


def kuerze(t, n):
    t = (t or "").strip(" .,;:«»")
    if len(t) <= n:
        return t
    return t[:n].rsplit(" ", 1)[0].rstrip(" .,;:") + "…"


def betreff(geschaeft):
    """Sachbetreff aus dem Geschäftstitel: was nach «betreffend» oder «zur» kommt."""
    ge = flach(geschaeft)
    if not ge:
        return ""
    m = (re.search(r"\bbetreffend\b\s*(.+)$", ge, re.I)
         or re.search(r"\b(?:zur|zum|über)\s+(.+)$", ge, re.I))
    t = m.group(1) if m else re.sub(r"\s+vom\s+\d.*$", "", ge)
    t = re.sub(r"^(?:die|der|das|den|dem|des)\s+", "", t.strip(), flags=re.I)
    t = re.sub(r"\s*\(.*$", "", t).strip(" «».,;")
    return t


def kurzsatz(details, n=86):
    """Erster sinntragender Teil des Detailtexts, vor «wie folgt» oder dem Doppelpunkt."""
    de = flach(details)
    if not de:
        return ""
    t = re.split(r"\s+wie folgt\b", de, maxsplit=1, flags=re.I)[0]
    m = re.search(r"^(.{15,}?):\s", t)
    if m:
        t = m.group(1)
    return kuerze(t, n)


def vorstoss(titel):
    """«Postulat Nr. 2026/4 von X vom … betreffend Y» → («Y», «Postulat 2026/4, X»)."""
    m = re.match(VORSTOSS_ART + r"\s*(?:Nr\.\s*)?([\d/]+)?\b(.*)$", titel, re.I)
    if not m:
        return None
    art, nr, rest = m.group(1), m.group(2), m.group(3)
    ms = (re.search(r"(?:mit dem Titel|betreffend)\s*[«\"]?(.+?)[»\"]?\s*$", rest, re.I)
          or re.search(r"«(.+?)»", rest))
    sache = ms.group(1).strip(" «».,;") if ms else ""
    if len(sache) < 8:
        return None
    mu = re.search(r"\bvon\s+(.+?)(?:\s*\(Erstunterzeichnende\)|\s+sowie\b|"
                   r"\s+vom\s+\d|\s+mit dem Titel|\s+betreffend|$)", rest, re.I)
    wer = re.sub(r"\s*\(.*?\)\s*", " ", mu.group(1)).strip() if mu else ""
    if len(wer) > 40:
        wer = re.split(r"\s+und\s+", wer)[0] + " u. a."
    ref = art + (" " + nr if nr else "") + (", " + wer if wer else "")
    return kuerze(sache, 96), ref


def ueberschrift(v):
    """(Überschrift, Referenzzeile). Die Referenz ist leer, wenn sie nichts hinzufügt."""
    t, de = flach(v.get("titel")), flach(v.get("details"))
    if not t:
        k = kurzsatz(de)
        return (k or "Abstimmung Nr. %s" % v.get("nr")), ""
    vs = vorstoss(t)
    if vs:
        return vs
    ks = kurzsatz(de)
    if ks and len(t) < 42 and not de.lower().startswith(t.lower()):
        return kuerze(t + ": " + ks, 108), ""
    return kuerze(t, 108), ""


def sess_sort_key(s):
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", s["sitzung"])
    d = (int(m.group(3)), int(m.group(2)), int(m.group(1))) if m else (0, 0, 0)
    h = 0 if "Vormittag" in s["sitzung"] else 2 if "Abend" in s["sitzung"] else 1
    return d + (h,)


def frak_key(name):
    return FRAK_KEY.get(name, "none")


def partei_key(name):
    return PARTEI_KEY.get((name or "").strip().lower(), "none")


def split_titel(sitzung):
    """«11. und 12. Sitzung 2026 · 24.08.2026 (Nachmittag)» → Teile."""
    teile = sitzung.split("·")
    name = teile[0].strip()
    rest = teile[1].strip() if len(teile) > 1 else ""
    m = re.match(r"([\d.]+)\s*(?:\((.+)\))?", rest)
    datum = m.group(1).strip() if m else rest
    zeit = m.group(2).strip() if m and m.group(2) else ""
    return name, datum, zeit


def de_datum(d):
    monate = ["Januar", "Februar", "März", "April", "Mai", "Juni",
              "Juli", "August", "September", "Oktober", "November", "Dezember"]
    m = re.match(r"(\d{2})\.(\d{2})\.(\d{4})", d or "")
    if not m:
        return d
    return "%d. %s %s" % (int(m.group(1)), monate[int(m.group(2)) - 1], m.group(3))


def zahl(n):
    return f"{n:,}".replace(",", " ")


def quote(a, b):
    return (a / b * 100) if b else 0.0


def kommazahl(x, nk=1):
    return f"{x:.{nk}f}".replace(".", ",")


# ─────────────────────────────────────────────────────────────────────────────
# Auswertung
# ─────────────────────────────────────────────────────────────────────────────

def umkehr_lesen():
    """Richtungsentscheide samt Herkunft und Protokollbeleg."""
    if not UMKEHR.exists():
        return {}
    daten = json.loads(UMKEHR.read_text(encoding="utf-8"))
    return {e["schluessel"]: e for e in daten["zuordnung"]}


def auswerten(sess):
    """Zaehlt jede Abstimmung aus und liefert eine aufbereitete Liste."""
    members = sess["members"]
    umkehr = umkehr_lesen()
    votes = []
    for i, v in enumerate(sess["votes"]):
        schluessel = f"{sess['sitzung']} #Nr{v['nr']}"
        gesamt = collections.Counter()
        nach_frak = collections.OrderedDict()
        namen = {k: [] for k in STIMME_KEY.values()}
        for m in members:
            roh = m["votes"][i] if i < len(m["votes"]) else "V/A/N"
            k = STIMME_KEY.get(roh, "abw")
            gesamt[k] += 1
            f = m["fraktion"]
            nach_frak.setdefault(f, collections.Counter())[k] += 1
            namen[k].append(m)

        total = sum(gesamt.values())
        abgegeben = gesamt["ja"] + gesamt["nein"] + gesamt["enth"]

        # Umkehrabstimmungen: ein Ja ist dort inhaltlich eine Ablehnung dessen,
        # was im Titel steht. Das Badge nennt darum immer das sachliche Ergebnis,
        # der Balken darunter zeigt weiterhin die protokollierten Stimmen.
        inv = bool(v.get("richtung_invertiert"))
        if gesamt["ja"] == gesamt["nein"]:
            ergebnis, ergebnis_key = "Stimmengleichheit", "enth"
        else:
            ja_gewinnt = gesamt["ja"] > gesamt["nein"]
            angenommen = (not ja_gewinnt) if inv else ja_gewinnt
            ergebnis = "Angenommen" if angenommen else "Abgelehnt"
            ergebnis_key = "ja" if angenommen else "nein"

        titel_h, referenz = ueberschrift(v)

        fr = []
        for f, c in nach_frak.items():
            ft = sum(c.values())
            fr.append({
                "name": f, "key": frak_key(f), "total": ft,
                "c": {k: c.get(k, 0) for k in STIMME_KEY.values()},
            })
        fr.sort(key=lambda x: -x["total"])

        votes.append({
            "i": i,
            "nr": v.get("nr"),
            "titel": titel_h,
            "titel_roh": flach(v.get("titel")),
            "referenz": referenz,
            "typ": v.get("typ") or "",
            "details": flach(v.get("details")),
            "geschaeft": flach(v.get("geschaeft")),
            "betreff": betreff(v.get("geschaeft")),
            "thema": v.get("thema_name") or "",
            "invertiert": inv,
            "inv_note": v.get("inverted_note") or "",
            "beleg": umkehr.get(schluessel, {}).get("protokoll_beleg", ""),
            "herkunft": umkehr.get(schluessel, {}).get("herkunft", ""),
            "c": {k: gesamt.get(k, 0) for k in STIMME_KEY.values()},
            "total": total,
            "abgegeben": abgegeben,
            "ergebnis": ergebnis,
            "ergebnis_key": ergebnis_key,
            "frak": fr,
            "namen": namen,
        })
    return votes


# ─────────────────────────────────────────────────────────────────────────────
# HTML-Bausteine
# ─────────────────────────────────────────────────────────────────────────────

def tally_html(c, total, groß=True):
    """Gestapelter Balken. Zahl nur, wenn das Segment breit genug ist."""
    segs = []
    for k in ["ja", "nein", "enth", "abw"]:
        n = c[k]
        if not n:
            continue
        p = quote(n, total)
        txt = str(n) if p >= 7.5 else ""
        segs.append(
            f'<span class="seg seg-{k}" style="flex:{n} 0 0" '
            f'aria-label="{STIMME_LABEL[k]}: {n}">{txt}</span>'
        )
    cls = "tally" + ("" if groß else " tally-sm")
    return f'<div class="{cls}">{"".join(segs)}</div>'


def legende_html(c):
    teile = []
    for k in ["ja", "nein", "enth", "abw"]:
        teile.append(
            f'<span class="lg lg-{k}"><i></i><b>{c[k]}</b>{STIMME_LABEL[k]}</span>'
        )
    return '<div class="legende">' + "".join(teile) + "</div>"


def frak_rows_html(v):
    rows = []
    for f in v["frak"]:
        c = f["c"]
        abg = c["ja"] + c["nein"] + c["enth"]
        einig = max(c["ja"], c["nein"]) == abg and abg > 0
        tag = ('<em title="Alle abgegebenen Stimmen der Fraktion gleich">geschlossen</em>'
               if einig else "")
        rows.append(f"""
          <div class="frow">
            <div class="fname"><i class="pdot p-{f['key']}"></i>
              <span title="{esc(f['name'])}">{esc(f['name'])}</span></div>
            {tally_html(c, f['total'], groß=False)}
            <div class="fval">{c['ja']}<span class="sep">:</span>{c['nein']}</div>
            <div class="ftag">{tag}</div>
          </div>""")
    return "".join(rows)


def namen_cols_html(v):
    cols = []
    for k in ["ja", "nein", "enth", "abw"]:
        leute = sorted(v["namen"][k], key=lambda m: (m["nachname"], m["vorname"]))
        items = "".join(
            f'<li><i class="pdot p-{partei_key(m["partei"])}"></i>'
            f'{esc(m["nachname"])} {esc(m["vorname"])}'
            f'<em>{esc(m["partei"])}</em></li>'
            for m in leute
        ) or '<li class="leer">niemand</li>'
        cols.append(f"""
          <div class="ncol nc-{k}">
            <h4>{STIMME_LABEL[k]}<span>{len(leute)}</span></h4>
            <ul>{items}</ul>
          </div>""")
    return '<div class="ncols">' + "".join(cols) + "</div>"


def vote_card_html(v):
    chips = []
    if v["typ"]:
        chips.append(f'<span class="chip">{esc(v["typ"])}</span>')
    if v["thema"]:
        chips.append(f'<span class="chip chip-thema">{esc(v["thema"])}</span>')

    inv = ""
    if v["invertiert"]:
        note = v["inv_note"] or "Ja und Nein sind bei dieser Abstimmung vertauscht."
        beleg = ""
        if v.get("beleg"):
            beleg = (f'<span class="ubeleg">Im Wortprotokoll: '
                     f'«{esc(kuerze(v["beleg"], 260))}»</span>')
        quelle = HERKUNFT.get(v.get("herkunft"), "")
        inv = f"""
        <div class="umkehr">
          <b>Umkehrabstimmung</b>
          <p>{esc(note)}. Ein Ja ist hier also keine Zustimmung zur ursprünglichen Vorlage.</p>
          {beleg}
          {f'<span class="uquelle">{esc(quelle)}</span>' if quelle else ''}
        </div>"""

    ref = ""
    if v["referenz"]:
        ref = f'<p class="vref">{esc(v["referenz"])}</p>'

    details = ""
    if v["details"] and v["details"] != v["titel"]:
        details = f'<p class="vdetails">{esc(v["details"])}</p>'

    c = v["c"]
    knapp = abs(c["ja"] - c["nein"])
    knapp_hinweis = ""
    if c["ja"] and c["nein"] and knapp <= 4:
        knapp_hinweis = f'<span class="knapp">knapp, {knapp} Stimmen Unterschied</span>'

    return f"""
    <article class="vcard" id="a{v['i'] + 1}">
      <header class="vhead">
        <span class="vnr">Nr. {esc(v['nr'])}</span>
        {"".join(chips)}
        <span class="badge b-{v['ergebnis_key']}">{esc(v['ergebnis'])}</span>
      </header>
      <h3 class="vtitel" title="{esc(v['titel_roh'])}">{esc(v['titel'])}</h3>
      {ref}
      {details}
      {inv}
      {tally_html(c, v['total'])}
      {legende_html(c)}
      {knapp_hinweis}
      <div class="folds">
        <details class="fold">
          <summary><span class="caret" aria-hidden="true"></span>So haben die Fraktionen gestimmt</summary>
          <div class="foldbody">{frak_rows_html(v)}</div>
        </details>
        <details class="fold">
          <summary><span class="caret" aria-hidden="true"></span>Wer hat wie gestimmt?</summary>
          <div class="foldbody">{namen_cols_html(v)}</div>
        </details>
      </div>
    </article>"""


def gruppieren(votes):
    """Abstimmungen nach Geschäft bündeln. Reihenfolge nach erstem Auftreten,
    Abstimmungen ohne Geschäft kommen als eigener Block ans Ende."""
    gruppen = collections.OrderedDict()
    ohne = []
    for v in votes:
        if v["betreff"]:
            g = gruppen.setdefault(v["betreff"], {"betreff": v["betreff"],
                                                  "geschaeft": v["geschaeft"],
                                                  "votes": []})
            g["votes"].append(v)
        else:
            ohne.append(v)
    liste = list(gruppen.values())
    if ohne:
        liste.append({"betreff": None, "geschaeft": "", "votes": ohne})
    return liste


def gruppen_html(gruppen):
    teile = []
    for g in gruppen:
        n = len(g["votes"])
        zahl = "1 Abstimmung" if n == 1 else f"{n} Abstimmungen"
        if g["betreff"]:
            kopf = f"""
      <div class="ghead">
        <div class="gtitel">
          <span class="glabel">Geschäft</span>
          <h3>{esc(g['betreff'])}</h3>
        </div>
        <span class="gcount">{zahl}</span>
      </div>
      <p class="gfull">{esc(g['geschaeft'])}</p>"""
        else:
            kopf = f"""
      <div class="ghead">
        <div class="gtitel">
          <span class="glabel">Ohne übergeordnetes Geschäft</span>
          <h3>Einzelne Vorlagen und Vorstösse</h3>
        </div>
        <span class="gcount">{zahl}</span>
      </div>"""
        karten = "".join(vote_card_html(v) for v in g["votes"])
        teile.append(f'<section class="gruppe">{kopf}<div class="cards">{karten}</div></section>')
    return "".join(teile)


# ─────────────────────────────────────────────────────────────────────────────
# Seite
# ─────────────────────────────────────────────────────────────────────────────

def build():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    sessions = sorted(d["sessions"], key=sess_sort_key)
    sess = sessions[-1]
    votes = auswerten(sess)

    name, datum, zeit = split_titel(sess["sitzung"])
    leg = d["legislaturen"][str(sess["legislatur"])]

    n_mitglieder = len(sess["members"])
    n_votes = len(votes)
    stimmen_total = sum(v["total"] for v in votes)
    stimmen_abg = sum(v["abgegeben"] for v in votes)
    praesenz = quote(stimmen_abg, stimmen_total)
    knappste = min((abs(v["c"]["ja"] - v["c"]["nein"]) for v in votes if v["c"]["nein"]),
                   default=None)
    einstimmig = sum(1 for v in votes if v["c"]["nein"] == 0 and v["c"]["enth"] == 0)

    # frühere Sitzungen für den Wähler
    vorige = list(reversed(sessions[-9:-1]))

    protokoll = (sess.get("protokolle") or [{}])[0]
    prot_url = protokoll.get("url") or sess.get("url") or ""

    nav_html = "".join(
        f'<a href="#" class="{"on" if on else ""}" {"aria-current=page" if on else ""} title="{esc(t)}">'
        f'<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">{ICONS[ic]}</svg>'
        f'<span>{esc(t)}</span></a>'
        for t, ic, on in NAV
    )

    vorige_html = "".join(
        f'<li><a href="#"><span>{esc(split_titel(s["sitzung"])[0])}</span>'
        f'<em>{esc(split_titel(s["sitzung"])[1])} · {s["n_votes"]} Abstimmungen</em></a></li>'
        for s in vorige
    )

    kennzahlen = [
        (str(n_votes), "namentliche Abstimmungen", "in dieser Sitzung"),
        (str(n_mitglieder), "Ratsmitglieder", leg["label"]),
        (kommazahl(praesenz) + " %", "Präsenz", "abgegebene Stimmen"),
        (str(einstimmig), "ohne Gegenstimme", f"von {n_votes} Abstimmungen"),
    ]
    kz_html = "".join(
        f'<div class="kz"><div class="kzn">{k[0]}</div>'
        f'<div class="kzl">{k[1]}</div><div class="kzsub">{k[2]}</div></div>'
        for k in kennzahlen
    )

    gruppen = gruppieren(votes)
    cards = gruppen_html(gruppen)
    n_gruppen = sum(1 for g in gruppen if g["betreff"])

    page = TEMPLATE.format(
        name=esc(name),
        datum_lang=esc(de_datum(datum)),
        datum=esc(datum),
        zeit=esc(zeit),
        zeit_suffix=(" · " + esc(zeit)) if zeit else "",
        leg_label=esc(leg["label"]),
        n_votes=n_votes,
        n_mitglieder=n_mitglieder,
        knappste=("%d Stimmen" % knappste) if knappste is not None else "–",
        nav=nav_html,
        kennzahlen=kz_html,
        cards=cards,
        n_gruppen=n_gruppen,
        vorige=vorige_html,
        prot_url=esc(prot_url),
        prot_name=esc(protokoll.get("name") or "Ratsprotokoll"),
        quelle=esc(sess.get("quelle") or ""),
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(page, encoding="utf-8")
    print(f"geschrieben: {OUT}  ({len(page)/1024:.0f} KB, {n_votes} Abstimmungen)")


TEMPLATE = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kantonsrat Schaffhausen · Zuletzt entschieden</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700&family=Public+Sans:wght@400;500;600;700&display=swap">
<style>
/* ═══ Farb- und Gestaltungstoken ══════════════════════════════════════════ */
:root{{
  color-scheme:light;
  /* Neutrale */
  --bg:#F2F4F6; --surface:#FFFFFF; --surface-2:#F7F9FA; --sunken:#EDF0F3;
  --ink:#111820; --ink-2:#4E5964; --ink-3:#79838F;
  --line:#E1E6EA; --hair:#EDF0F3;
  --focus:#1F4E79;

  /* Abstimmungsskala, parteiunabhaengig */
  --ja:#0F766E;   --ja-ink:#0C6A62;   --ja-on:#FFFFFF;
  --nein:#8E44AD; --nein-ink:#7E3C9A; --nein-on:#FFFFFF;
  --enth:#8B93A1; --enth-ink:#646C79; --enth-on:#FFFFFF;
  --abw:#DFE3E8;  --abw-ink:#6E7783;  --abw-on:#5B646F;

  /* Parteien und Fraktionen */
  --p-svp:#4B8A3E;   --p-svp-ink:#417B36;
  --p-edu:#A65E42;   --p-edu-ink:#8E4E36;
  --p-sp:#F0554D;    --p-sp-ink:#CE362E;
  --p-gru:#84B547;   --p-gru-ink:#5D8132;
  --p-al:#B02E7A;    --p-al-ink:#A02A6F;
  --p-glp:#C4C43D;   --p-glp-ink:#6F6F16;
  --p-evp:#DEAA28;   --p-evp-ink:#8A6606;
  --p-fdp:#3872B5;   --p-fdp-ink:#2F639F;
  --p-mitte:#D6862B; --p-mitte-ink:#9E590C;
  --p-none:#A8AEB6;  --p-none-ink:#69707A;

  --card-shadow:0 1px 2px rgba(17,24,32,.05), 0 6px 18px rgba(17,24,32,.045);
  --r-card:14px; --r-ctl:9px;
  --nav-w:236px; --nav-w-min:64px;
}}
@media (prefers-color-scheme: dark){{
  :root:not([data-theme="light"]){{
    color-scheme:dark;
    --bg:#0B0F14; --surface:#171E27; --surface-2:#1E2630; --sunken:#232C37;
    --ink:#E8ECF1; --ink-2:#A4AEBA; --ink-3:#7C8794;
    --line:#2C353F; --hair:#232B34;
    --focus:#8FB7E0;
    --ja:#3FB3A8;   --ja-ink:#3FB3A8;   --ja-on:#08201E;
    --nein:#C08AD8; --nein-ink:#C08AD8; --nein-on:#1D1024;
    --enth:#A9B1BE; --enth-ink:#A9B1BE; --enth-on:#141A21;
    --abw:#39434F;  --abw-ink:#98A2AE;  --abw-on:#C3CBD4;
    --p-svp:#6BA55E;   --p-svp-ink:#6BA55E;
    --p-edu:#C08268;   --p-edu-ink:#C08268;
    --p-sp:#F0554D;    --p-sp-ink:#F0554D;
    --p-gru:#9BC961;   --p-gru-ink:#9BC961;
    --p-al:#D470AC;    --p-al-ink:#D470AC;
    --p-glp:#D2D257;   --p-glp-ink:#D2D257;
    --p-evp:#EABE4F;   --p-evp-ink:#EABE4F;
    --p-fdp:#6D9FD8;   --p-fdp-ink:#6D9FD8;
    --p-mitte:#E3A053; --p-mitte-ink:#E3A053;
    --p-none:#C3C9D0;  --p-none-ink:#C3C9D0;
    --card-shadow:0 1px 2px rgba(0,0,0,.45);
  }}
}}
:root[data-theme="dark"]{{
  color-scheme:dark;
  --bg:#0D1116; --surface:#151A21; --surface-2:#1A2029; --sunken:#10151B;
  --ink:#E8ECF1; --ink-2:#A4AEBA; --ink-3:#7C8794;
  --line:#252C35; --hair:#1E242C;
  --focus:#8FB7E0;
  --ja:#3FB3A8;   --ja-ink:#3FB3A8;   --ja-on:#08201E;
  --nein:#C08AD8; --nein-ink:#C08AD8; --nein-on:#1D1024;
  --enth:#A9B1BE; --enth-ink:#A9B1BE; --enth-on:#141A21;
  --abw:#39434F;  --abw-ink:#98A2AE;  --abw-on:#C3CBD4;
  --p-svp:#6BA55E;   --p-svp-ink:#6BA55E;
  --p-edu:#C08268;   --p-edu-ink:#C08268;
  --p-sp:#F0554D;    --p-sp-ink:#F0554D;
  --p-gru:#9BC961;   --p-gru-ink:#9BC961;
  --p-al:#D470AC;    --p-al-ink:#D470AC;
  --p-glp:#D2D257;   --p-glp-ink:#D2D257;
  --p-evp:#EABE4F;   --p-evp-ink:#EABE4F;
  --p-fdp:#6D9FD8;   --p-fdp-ink:#6D9FD8;
  --p-mitte:#E3A053; --p-mitte-ink:#E3A053;
  --p-none:#C3C9D0;  --p-none-ink:#C3C9D0;
  --card-shadow:0 1px 2px rgba(0,0,0,.45);
}}

/* ═══ Grundlagen ══════════════════════════════════════════════════════════ */
*{{box-sizing:border-box}}
html{{-webkit-text-size-adjust:100%}}
body{{
  margin:0; background:var(--bg); color:var(--ink);
  font-family:"Public Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  font-size:16px; line-height:1.55; -webkit-font-smoothing:antialiased;
}}
h1,h2,h3,h4,p,ul,ol,figure{{margin:0}}
ul{{list-style:none; padding:0}}
a{{color:inherit}}
button{{font:inherit; color:inherit}}
:focus-visible{{outline:2px solid var(--focus); outline-offset:2px; border-radius:4px}}
.num{{font-variant-numeric:tabular-nums}}
.sr{{position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0); white-space:nowrap}}

/* ═══ Grundgeruest ════════════════════════════════════════════════════════ */
.app{{display:grid; grid-template-columns:var(--nav-w) 1fr; min-height:100vh}}
body[data-nav="min"] .app{{grid-template-columns:var(--nav-w-min) 1fr}}

/* ─ Seitenleiste ─ */
.side{{
  position:sticky; top:0; align-self:start; height:100vh;
  background:var(--surface); border-right:1px solid var(--line);
  display:flex; flex-direction:column; gap:22px; padding:18px 14px 16px;
  overflow:hidden;
}}
.brandrow{{display:flex; align-items:flex-start; gap:8px}}
.brand{{
  font-family:"Archivo",sans-serif; font-weight:700; font-size:15px; line-height:1.2;
  letter-spacing:-.015em; flex:1; min-width:0;
}}
.brand span{{
  display:block; font-family:"Public Sans",sans-serif; font-weight:600; font-size:10px;
  letter-spacing:.15em; text-transform:uppercase; color:var(--ink-3); margin-top:4px;
}}
.navtoggle{{
  flex:0 0 auto; width:30px; height:30px; border:1px solid var(--line); background:var(--surface-2);
  border-radius:8px; cursor:pointer; display:flex; align-items:center; justify-content:center;
  color:var(--ink-2); transition:background .14s,border-color .14s;
}}
.navtoggle:hover{{background:var(--sunken); border-color:var(--ink-3)}}
.navtoggle svg{{transition:transform .18s ease}}
body[data-nav="min"] .navtoggle svg{{transform:rotate(180deg)}}

.side nav{{display:flex; flex-direction:column; gap:2px}}
.side nav a{{
  display:flex; align-items:center; gap:11px; padding:9px 11px; border-radius:var(--r-ctl);
  font-size:14px; font-weight:600; color:var(--ink-2); text-decoration:none;
  white-space:nowrap; transition:background .14s,color .14s;
}}
.side nav a svg{{flex:0 0 auto; opacity:.9}}
.side nav a:hover{{background:var(--surface-2); color:var(--ink)}}
.side nav a.on{{background:var(--sunken); color:var(--ink)}}
.side nav a.on svg{{color:var(--ink); opacity:1}}
.sidefoot{{margin-top:auto; display:flex; flex-direction:column; gap:12px}}
.themetoggle{{
  display:flex; align-items:center; gap:10px; padding:9px 11px; border-radius:var(--r-ctl);
  border:1px solid var(--line); background:var(--surface-2); cursor:pointer;
  font-size:13px; font-weight:600; color:var(--ink-2); white-space:nowrap;
}}
.themetoggle:hover{{border-color:var(--ink-3); color:var(--ink)}}
.stand{{font-size:11.5px; color:var(--ink-3); line-height:1.45; padding:0 11px}}

body[data-nav="min"] .side{{padding:18px 9px 16px}}
body[data-nav="min"] .brand,
body[data-nav="min"] .side nav a span,
body[data-nav="min"] .themetoggle span,
body[data-nav="min"] .stand{{display:none}}
body[data-nav="min"] .brandrow{{justify-content:center}}
body[data-nav="min"] .side nav a,
body[data-nav="min"] .themetoggle{{justify-content:center; padding:10px 0}}

/* ─ Inhalt ─ */
.main{{min-width:0; display:flex; flex-direction:column}}
.topbar{{
  position:sticky; top:0; z-index:20; display:flex; align-items:center; gap:14px;
  padding:12px 30px; background:color-mix(in srgb, var(--bg) 88%, transparent);
  backdrop-filter:blur(10px); border-bottom:1px solid var(--line); flex-wrap:wrap;
}}
.burger{{display:none}}
.search{{
  flex:1 1 260px; min-width:0; display:flex; align-items:center; gap:9px;
  background:var(--surface); border:1px solid var(--line); border-radius:var(--r-ctl);
  padding:9px 13px; font-size:13.5px; color:var(--ink-3);
}}
.pick{{
  display:flex; align-items:center; gap:8px; background:var(--surface);
  border:1px solid var(--line); border-radius:var(--r-ctl); padding:9px 13px;
  font-size:13px; font-weight:600; color:var(--ink-2); white-space:nowrap;
}}
.wrap{{max-width:900px; width:100%; margin:0 auto; padding:0 30px 72px}}

/* ─ Kopf der Seite ─ */
.hero{{padding:40px 0 26px}}
.eyebrow{{
  font-size:11px; font-weight:700; letter-spacing:.15em; text-transform:uppercase;
  color:var(--ink-3);
}}
h1{{
  font-family:"Archivo",sans-serif; font-weight:700; font-size:clamp(27px,4.2vw,38px);
  line-height:1.08; letter-spacing:-.025em; margin-top:12px; text-wrap:balance;
}}
.subline{{margin-top:12px; color:var(--ink-2); font-size:16px; max-width:62ch}}
.subline b{{color:var(--ink); font-weight:600}}

/* ─ Kennzahlen: Haarlinienstil ─ */
.kzs{{
  display:grid; grid-template-columns:repeat(4,1fr); border-top:1px solid var(--line);
  border-bottom:1px solid var(--line); margin-bottom:38px;
}}
.kz{{padding:20px 22px; border-right:1px solid var(--hair)}}
.kz:first-child{{padding-left:0}}
.kz:last-child{{border-right:0; padding-right:0}}
.kzn{{
  font-family:"Archivo",sans-serif; font-size:30px; font-weight:600; line-height:1;
  letter-spacing:-.03em; font-variant-numeric:tabular-nums;
}}
.kzl{{font-size:13px; color:var(--ink-2); margin-top:9px; line-height:1.35}}
.kzsub{{font-size:11.5px; color:var(--ink-3); margin-top:3px}}

/* ─ Abschnittstitel ─ */
.sec{{display:flex; align-items:baseline; justify-content:space-between; gap:16px;
  margin-bottom:28px; flex-wrap:wrap}}
.sec h2{{font-family:"Archivo",sans-serif; font-size:23px; font-weight:600; letter-spacing:-.02em}}
.sec p{{font-size:13px; color:var(--ink-3)}}

/* ─ Geschäftsgruppe: Haarlinienstil ─ */
.gruppe{{margin-bottom:40px}}
.gruppe:last-of-type{{margin-bottom:0}}
.ghead{{
  display:flex; align-items:flex-end; justify-content:space-between; gap:18px;
  padding-bottom:11px; border-bottom:2px solid var(--ink); flex-wrap:wrap;
}}
.glabel{{
  display:block; font-size:10.5px; font-weight:700; letter-spacing:.15em;
  text-transform:uppercase; color:var(--ink-3); margin-bottom:5px;
}}
.ghead h3{{
  font-family:"Archivo",sans-serif; font-size:19px; font-weight:600; line-height:1.22;
  letter-spacing:-.018em; max-width:46ch; text-wrap:balance;
}}
.gcount{{
  font-size:12px; font-weight:600; color:var(--ink-3); white-space:nowrap;
  font-variant-numeric:tabular-nums; padding-bottom:3px;
}}
.gfull{{
  font-size:12px; color:var(--ink-3); line-height:1.45; margin:10px 0 0; max-width:82ch;
}}

/* ─ Abstimmungskarte: weiche Karte ─ */
.cards{{display:flex; flex-direction:column; gap:14px; margin-top:16px}}
.vcard{{
  background:var(--surface); border:1px solid var(--line); border-radius:var(--r-card);
  padding:22px 24px; box-shadow:var(--card-shadow);
}}
.vhead{{display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin-bottom:11px}}
.vnr{{
  font-family:"Archivo",sans-serif; font-size:11px; font-weight:700; letter-spacing:.09em;
  text-transform:uppercase; color:var(--ink-3);
}}
.chip{{
  font-size:11.5px; font-weight:600; color:var(--ink-2); background:var(--surface-2);
  border:1px solid var(--line); border-radius:99px; padding:3px 10px;
}}
.chip-thema{{background:transparent}}
.badge{{
  margin-left:auto; font-size:11px; font-weight:700; letter-spacing:.05em; text-transform:uppercase;
  border-radius:99px; padding:4px 11px; white-space:nowrap;
}}
.b-ja{{background:var(--ja); color:var(--ja-on)}}
.b-nein{{background:var(--nein); color:var(--nein-on)}}
.b-enth{{background:var(--enth); color:var(--enth-on)}}
.vtitel{{
  font-family:"Archivo",sans-serif; font-size:17.5px; font-weight:600; line-height:1.3;
  letter-spacing:-.01em; text-wrap:balance; max-width:52ch;
}}
.vref{{
  margin-top:5px; font-size:12.5px; font-weight:600; color:var(--ink-3);
  letter-spacing:.005em;
}}
.vdetails{{margin-top:9px; font-size:14.5px; color:var(--ink-2); max-width:70ch}}
.umkehr{{
  margin-top:13px; font-size:13px; line-height:1.5; color:var(--ink-2);
  background:var(--surface-2); border:1px solid var(--line); border-left:3px solid var(--enth);
  border-radius:8px; padding:10px 13px; max-width:76ch;
}}
.umkehr b{{display:block; color:var(--ink); font-size:11.5px; letter-spacing:.07em;
  text-transform:uppercase; margin-bottom:3px}}
.umkehr p{{margin:0}}
.ubeleg{{display:block; margin-top:9px; padding-top:9px; border-top:1px solid var(--line);
  font-size:12.5px; color:var(--ink-3); line-height:1.5; font-style:italic}}
.uquelle{{display:inline-block; margin-top:8px; font-size:11px; font-weight:600;
  letter-spacing:.04em; color:var(--ink-3); border:1px solid var(--line);
  border-radius:99px; padding:2px 9px; font-style:normal}}

/* ─ Balken ─ */
.tally{{display:flex; height:36px; margin-top:18px; border-radius:9px; overflow:hidden; gap:2px}}
.tally-sm{{height:12px; margin-top:0; border-radius:99px; gap:1.5px}}
.tally .seg{{
  display:flex; align-items:center; justify-content:center; font-size:12.5px; font-weight:700;
  font-variant-numeric:tabular-nums; min-width:3px;
}}
.tally-sm .seg{{font-size:0}}
.seg-ja{{background:var(--ja); color:var(--ja-on)}}
.seg-nein{{background:var(--nein); color:var(--nein-on)}}
.seg-enth{{background:var(--enth); color:var(--enth-on)}}
.seg-abw{{background:var(--abw); color:var(--abw-on)}}
.legende{{display:flex; gap:7px; margin-top:11px; flex-wrap:wrap}}
.lg{{
  display:flex; align-items:center; gap:6px; font-size:12.5px; color:var(--ink-2);
  background:var(--surface-2); border-radius:99px; padding:4px 11px;
}}
.lg i{{width:8px; height:8px; border-radius:99px; flex:0 0 auto}}
.lg b{{font-weight:700; color:var(--ink); font-variant-numeric:tabular-nums}}
.lg-ja i{{background:var(--ja)}} .lg-nein i{{background:var(--nein)}}
.lg-enth i{{background:var(--enth)}} .lg-abw i{{background:var(--abw)}}
.knapp{{
  display:inline-block; margin-top:11px; font-size:12px; font-weight:600; color:var(--ink-2);
  border:1px dashed var(--line); border-radius:99px; padding:3px 11px;
}}

/* ─ Aufklappbares ─ */
.folds{{margin-top:16px; border-top:1px solid var(--hair); display:flex; flex-direction:column}}
.fold summary{{
  list-style:none; cursor:pointer; display:flex; align-items:center; gap:9px;
  padding:12px 2px; font-size:13.5px; font-weight:600; color:var(--ink-2);
  border-bottom:1px solid var(--hair);
}}
.fold:last-child summary{{border-bottom:0}}
.fold[open] summary{{color:var(--ink); border-bottom-color:transparent}}
.fold summary::-webkit-details-marker{{display:none}}
.fold summary:hover{{color:var(--ink)}}
.caret{{
  width:8px; height:8px; border-right:1.8px solid currentColor; border-bottom:1.8px solid currentColor;
  transform:rotate(-45deg); margin-left:2px; transition:transform .18s ease; flex:0 0 auto;
}}
.fold[open] .caret{{transform:rotate(45deg)}}
.foldbody{{padding:6px 0 18px}}

.frow{{
  display:grid; grid-template-columns:222px minmax(90px,1fr) 62px 96px;
  gap:14px; align-items:center; padding:7px 0;
}}
.fname{{display:flex; align-items:center; gap:9px; font-size:13px; font-weight:600; min-width:0}}
.fname span{{overflow:hidden; text-overflow:ellipsis; white-space:nowrap}}
.pdot{{width:9px; height:9px; border-radius:99px; flex:0 0 auto; display:inline-block}}
.fval{{
  font-size:12.5px; color:var(--ink-2); text-align:right; font-variant-numeric:tabular-nums;
  white-space:nowrap;
}}
.fval .sep{{color:var(--ink-3); margin:0 3px}}
.ftag{{min-width:0}}
.ftag em{{
  font-style:normal; font-size:10px; font-weight:700; letter-spacing:.06em; text-transform:uppercase;
  color:var(--ink-3); border:1px solid var(--line); border-radius:99px; padding:2px 8px;
  white-space:nowrap;
}}

.ncols{{display:grid; grid-template-columns:1.2fr 1.2fr .68fr 1fr; gap:20px}}
.ncol h4{{
  font-size:11px; font-weight:700; letter-spacing:.08em; text-transform:uppercase;
  padding-bottom:6px; margin-bottom:9px; border-bottom:2px solid;
  display:flex; justify-content:space-between; align-items:baseline; gap:8px;
}}
.ncol h4 span{{font-size:13px; font-variant-numeric:tabular-nums}}
.nc-ja h4{{color:var(--ja-ink); border-color:var(--ja)}}
.nc-nein h4{{color:var(--nein-ink); border-color:var(--nein)}}
.nc-enth h4{{color:var(--enth-ink); border-color:var(--enth)}}
.nc-abw h4{{color:var(--abw-ink); border-color:var(--abw)}}
.ncol li{{
  display:flex; align-items:center; gap:7px; font-size:12.5px; padding:2.5px 0;
  color:var(--ink-2);
}}
.ncol li em{{
  font-style:normal; font-size:10.5px; color:var(--ink-3); margin-left:auto; white-space:nowrap;
}}
.ncol li.leer{{color:var(--ink-3); font-style:italic}}

/* Parteifarben als Punkt */
.p-svp{{background:var(--p-svp)}} .p-edu{{background:var(--p-edu)}}
.p-sp{{background:var(--p-sp)}}   .p-gru{{background:var(--p-gru)}}
.p-al{{background:var(--p-al)}}   .p-glp{{background:var(--p-glp)}}
.p-evp{{background:var(--p-evp)}} .p-fdp{{background:var(--p-fdp)}}
.p-mitte{{background:var(--p-mitte)}} .p-none{{background:var(--p-none)}}

/* ─ Fuss ─ */
.older{{margin-top:44px}}
.olist{{display:grid; grid-template-columns:repeat(auto-fill,minmax(232px,1fr)); gap:1px;
  background:var(--line); border:1px solid var(--line); border-radius:var(--r-card); overflow:hidden}}
.olist a{{
  display:block; background:var(--surface); padding:14px 16px; text-decoration:none;
  transition:background .14s;
}}
.olist a:hover{{background:var(--surface-2)}}
.olist span{{display:block; font-size:13.5px; font-weight:600}}
.olist em{{display:block; font-style:normal; font-size:11.5px; color:var(--ink-3); margin-top:3px}}
.foot{{
  margin-top:44px; padding-top:22px; border-top:1px solid var(--line);
  font-size:12.5px; color:var(--ink-3); line-height:1.6; max-width:80ch;
}}
.foot a{{color:var(--ink-2)}}
.foot b{{color:var(--ink-2)}}

/* ═══ Schmale Bildschirme ═════════════════════════════════════════════════ */
@media (max-width:900px){{
  .app{{grid-template-columns:1fr}}
  body[data-nav="min"] .app{{grid-template-columns:1fr}}
  .side{{
    position:fixed; z-index:60; top:0; left:0; width:264px; height:100dvh;
    transform:translateX(-102%); transition:transform .22s ease; box-shadow:0 0 40px rgba(0,0,0,.18);
  }}
  body[data-nav="open"] .side{{transform:none}}
  body[data-nav="min"] .side{{padding:18px 14px 16px}}
  body[data-nav="min"] .brand,
  body[data-nav="min"] .side nav a span,
  body[data-nav="min"] .themetoggle span,
  body[data-nav="min"] .stand{{display:revert}}
  body[data-nav="min"] .side nav a,
  body[data-nav="min"] .themetoggle{{justify-content:flex-start; padding:9px 11px}}
  .scrim{{
    position:fixed; inset:0; z-index:50; background:rgba(8,12,16,.42); opacity:0;
    pointer-events:none; transition:opacity .22s ease;
  }}
  body[data-nav="open"] .scrim{{opacity:1; pointer-events:auto}}
  .burger{{
    display:flex; align-items:center; justify-content:center; width:38px; height:38px;
    border:1px solid var(--line); background:var(--surface); border-radius:var(--r-ctl);
    cursor:pointer; flex:0 0 auto;
  }}
  .topbar{{padding:10px 16px}}
  .search{{order:3; flex:1 1 100%}}
  .pick{{margin-left:auto}}
  .wrap{{padding:0 16px 60px}}
  .kzs{{grid-template-columns:repeat(2,1fr)}}
  .kz{{padding:16px 16px}}
  .kz:nth-child(odd){{padding-left:0}}
  .kz:nth-child(2n){{border-right:0; padding-right:0}}
  .kz:nth-child(3),.kz:nth-child(4){{border-top:1px solid var(--hair)}}
  .vcard{{padding:18px 16px}}
  .frow{{
    grid-template-columns:1fr auto; grid-template-areas:"name val" "bar bar" "tag tag";
    gap:6px 12px; padding:10px 0; border-bottom:1px solid var(--hair);
  }}
  .frow .fname{{grid-area:name}}
  .frow .tally{{grid-area:bar}}
  .frow .fval{{grid-area:val}}
  .frow .ftag{{grid-area:tag}}
  .frow .ftag:empty{{display:none}}
  .ncols{{grid-template-columns:repeat(2,1fr); gap:16px}}
}}
@media (max-width:520px){{
  .ncols{{grid-template-columns:1fr}}
  .badge{{margin-left:0}}
}}
@media print{{
  .side,.topbar,.scrim{{display:none}}
  .app{{grid-template-columns:1fr}}
  .vcard{{box-shadow:none; break-inside:avoid}}
  .fold{{display:block}}
}}
@media (prefers-reduced-motion: reduce){{
  *{{transition:none !important; animation:none !important}}
}}
</style>
</head>
<body data-nav="closed">
<div class="scrim" id="scrim" hidden></div>
<div class="app">

  <aside class="side" id="side">
    <div class="brandrow">
      <div class="brand">Kantonsrat<br>Schaffhausen<span>Abstimmungsspiegel</span></div>
      <button class="navtoggle" id="navToggle" type="button"
              aria-label="Seitenleiste einklappen" aria-expanded="true">
        <svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true">
          <path d="M10 3L5 8l5 5" stroke="currentColor" stroke-width="1.8" fill="none"
                stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>
    <nav aria-label="Rubriken">{nav}</nav>
    <div class="sidefoot">
      <button class="themetoggle" id="themeToggle" type="button" aria-pressed="false">
        <svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true" id="themeIcon">
          <path d="M13 9.6A5.4 5.4 0 0 1 6.4 3a5.6 5.6 0 1 0 6.6 6.6z" fill="currentColor"/>
        </svg>
        <span id="themeLabel">Dunkelmodus</span>
      </button>
      <div class="stand">Datenstand<br>{datum}</div>
    </div>
  </aside>

  <main class="main">
    <div class="topbar">
      <button class="burger" id="burger" type="button" aria-label="Menü öffnen" aria-expanded="false">
        <svg viewBox="0 0 16 16" width="17" height="17" aria-hidden="true">
          <path d="M2 4h12M2 8h12M2 12h12" stroke="currentColor" stroke-width="1.7"
                stroke-linecap="round"/>
        </svg>
      </button>
      <div class="search">
        <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
          <circle cx="7" cy="7" r="5" stroke="currentColor" stroke-width="1.7" fill="none"/>
          <path d="M11 11l4 4" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/>
        </svg>
        Geschäft, Name oder Thema suchen …
      </div>
      <div class="pick">{leg_label}</div>
    </div>

    <div class="wrap">
      <header class="hero">
        <div class="eyebrow">Zuletzt entschieden</div>
        <h1>{name}</h1>
        <p class="subline">
          Sitzung vom <b>{datum_lang}</b>{zeit_suffix}. Der Rat hat <b>{n_votes} Mal</b>
          namentlich abgestimmt. Alle {n_mitglieder} Ratsmitglieder und ihre Stimmen sind
          zu jeder Frage aufklappbar.
        </p>
      </header>

      <div class="kzs">{kennzahlen}</div>

      <div class="sec">
        <h2>Alle Abstimmungen dieser Sitzung</h2>
        <p>gebündelt nach Geschäft, {n_gruppen} Geschäfte</p>
      </div>
      {cards}

      <section class="older">
        <div class="sec">
          <h2>Frühere Sitzungen</h2>
          <p>Auswahl der letzten acht</p>
        </div>
        <ul class="olist">{vorige}</ul>
      </section>

      <footer class="foot">
        <b>Prototyp.</b> Diese Seite zeigt nur die Rubrik «Zuletzt entschieden» im neuen Design.
        Suche, Legislaturwahl und die übrigen Rubriken sind hier noch ohne Funktion.<br>
        <b>Datenquelle:</b> Kanton Schaffhausen, namentliche Abstimmungen des Kantonsrats
        (Excel-Publikation der Parlamentsdienste, {quelle}).
        <a href="{prot_url}">{prot_name}</a>.
        Aufbereitung ohne Gewähr.<br>
        <b>Parteifarben</b> nach srfdata/swiss-party-colors (CC BY-SA 4.0), angepasst für die
        Schaffhauser Parteien. Ja und Nein sind bewusst parteiunabhängig eingefärbt.
      </footer>
    </div>
  </main>
</div>

<script>
(function(){{
  "use strict";
  var body = document.body;
  var mqNarrow = window.matchMedia("(max-width: 900px)");

  /* ── Seitenleiste ───────────────────────────────────────────── */
  var navToggle = document.getElementById("navToggle");
  var burger = document.getElementById("burger");
  var scrim = document.getElementById("scrim");

  function setNav(state){{
    body.setAttribute("data-nav", state);
    var offen = state !== "min";
    navToggle.setAttribute("aria-expanded", String(offen));
    navToggle.setAttribute("aria-label", offen ? "Seitenleiste einklappen" : "Seitenleiste ausklappen");
    if (!mqNarrow.matches) {{
      try {{ localStorage.setItem("krsh-nav", state); }} catch(e) {{}}
    }}
    if (burger) burger.setAttribute("aria-expanded", String(state === "open"));
    if (scrim) scrim.hidden = state !== "open";
  }}

  navToggle.addEventListener("click", function(){{
    if (mqNarrow.matches) {{ setNav("closed"); return; }}
    setNav(body.getAttribute("data-nav") === "min" ? "closed" : "min");
  }});
  if (burger) burger.addEventListener("click", function(){{ setNav("open"); }});
  if (scrim) scrim.addEventListener("click", function(){{ setNav("closed"); }});
  document.addEventListener("keydown", function(e){{
    if (e.key === "Escape" && body.getAttribute("data-nav") === "open") setNav("closed");
  }});
  mqNarrow.addEventListener("change", function(){{ setNav("closed"); }});

  try {{
    var gespeichert = localStorage.getItem("krsh-nav");
    if (gespeichert === "min" && !mqNarrow.matches) setNav("min"); else setNav("closed");
  }} catch(e) {{ setNav("closed"); }}

  /* ── Hell und Dunkel ────────────────────────────────────────── */
  var themeToggle = document.getElementById("themeToggle");
  var themeLabel = document.getElementById("themeLabel");
  var themeIcon = document.getElementById("themeIcon");
  var SONNE = '<circle cx="8" cy="8" r="3.2" fill="currentColor"/>'
            + '<path d="M8 .8v2M8 13.2v2M.8 8h2M13.2 8h2M2.9 2.9l1.4 1.4M11.7 11.7l1.4 1.4'
            + 'M13.1 2.9l-1.4 1.4M4.3 11.7l-1.4 1.4" stroke="currentColor" stroke-width="1.5"'
            + ' stroke-linecap="round" fill="none"/>';
  var MOND = '<path d="M13 9.6A5.4 5.4 0 0 1 6.4 3a5.6 5.6 0 1 0 6.6 6.6z" fill="currentColor"/>';

  function istDunkel(){{
    var t = document.documentElement.getAttribute("data-theme");
    if (t) return t === "dark";
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  }}
  function themeAnzeigen(){{
    var dunkel = istDunkel();
    themeLabel.textContent = dunkel ? "Hellmodus" : "Dunkelmodus";
    themeIcon.innerHTML = dunkel ? SONNE : MOND;
    themeToggle.setAttribute("aria-pressed", String(dunkel));
    themeToggle.setAttribute("aria-label", dunkel ? "Zum Hellmodus wechseln" : "Zum Dunkelmodus wechseln");
  }}
  themeToggle.addEventListener("click", function(){{
    var neu = istDunkel() ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", neu);
    try {{ localStorage.setItem("krsh-theme", neu); }} catch(e) {{}}
    themeAnzeigen();
  }});
  try {{
    var gt = localStorage.getItem("krsh-theme");
    if (gt === "dark" || gt === "light") document.documentElement.setAttribute("data-theme", gt);
  }} catch(e) {{}}
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", themeAnzeigen);
  themeAnzeigen();
}})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    build()

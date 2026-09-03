#!/usr/bin/env python3
"""Abstimmungsspiegel: erzeugt aus einem Abstimmungsordner eine Seite fuer den Politspiegel.

Aufruf aus der Projektwurzel:
    python3 abstimmungsspiegel/bausteine/argumente.py 2026-09-27-verkehrsfluss

Liest    abstimmungsspiegel/abstimmungen/<slug>/vorlage.json
         abstimmungsspiegel/abstimmungen/<slug>/geo/03_freigegeben/*.geojson
         data/all_sessions.json                 (Ratsdaten, immer frisch)
Schreibt site/abstimmung/<slug>/index.html
         site/abstimmung/<slug>/grafiken/       (Kopie der eingebundenen Grafiken)

Grundsaetze siehe abstimmungsspiegel/docs/10_METHODE.md, Aufbau der Seite in
11_LAYOUT.md. Bewertet wird nie das Argument, sondern sein Beleg. Werturteile
werden dargestellt, aber nicht benotet.

Eingebunden werden nur Geodaten aus 03_freigegeben. Diese Stufe fuellt
abstimmungsspiegel/bausteine/geo_freigeben.py, und zwar erst nach Pruefung. Eine
Ebene, die die Pruefung nicht besteht, fehlt hier einfach; sie erscheint dann
nicht auf der Karte, statt sie mit falschen Linien zu fuellen.

Phase-2-Bruecke: Das Feld vorlage.kantonsrat_suche verbindet die Vorlage mit den
namentlichen Abstimmungen in data/all_sessions.json. Die Ratsdaten werden bei
jedem Lauf frisch gelesen, nicht abgeschrieben.
"""

from __future__ import annotations

import collections
import html
import json
import math
import re
import shutil
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import teilen  # noqa: E402  Bilder fuer Social Media, gleicher Ordner

WURZEL = Path(__file__).resolve().parent.parent.parent
SLUG = sys.argv[1] if len(sys.argv) > 1 else "2026-09-27-verkehrsfluss"
VORLAGE = WURZEL / "abstimmungsspiegel" / "abstimmungen" / SLUG
QUELLE = VORLAGE / "vorlage.json"
SITZUNGEN = WURZEL / "data" / "all_sessions.json"
GRAFIKEN = VORLAGE / "grafiken"
ZIEL = WURZEL / "site" / "abstimmung" / SLUG / "index.html"
ZUGANG = WURZEL / "data" / "github_zugang.json"


def adresse() -> str:
    """Die oeffentliche Adresse dieser Seite, falls der Zugang bekannt ist.

    Sie steht im Bild fuer Social Media und in den Vorschauangaben fuer
    geteilte Links. Ohne github_zugang.json bleibt sie leer; die Seite
    funktioniert dann genauso, nur ohne absolute Verweise auf sich selbst.
    """
    try:
        z = json.loads(ZUGANG.read_text(encoding="utf-8"))
        return f"https://{z['benutzer']}.github.io/{z['repo']}/abstimmung/{SLUG}/"
    except Exception:
        return ""


def quellcode_adresse() -> str:
    """Das oeffentliche Repository, fuer den Verweis im Fuss der Seite."""
    try:
        z = json.loads(ZUGANG.read_text(encoding="utf-8"))
        return f"https://github.com/{z['benutzer']}/{z['repo']}"
    except Exception:
        return ""


def kopfzeilen(v: dict, url: str) -> str:
    """Vorschauangaben fuer geteilte Links, wie sie publish.py fuer den
    Kantonsratsspiegel setzt. Das Vorschaubild ist das des Politspiegels."""
    titel = f"Abstimmungsspiegel · {v['titel']}"
    satz = (f"Abstimmung vom {teilen.datum_lang(v['abstimmung'])}: {v.get('untertitel', '')}. "
            "Die Argumente beider Seiten mit Fundstelle und Prüfung des Belegs.")
    z = [f'<meta name="description" content="{e(satz)}">',
         '<meta property="og:type" content="article">',
         '<meta property="og:site_name" content="Politspiegel Schaffhausen">',
         f'<meta property="og:title" content="{e(titel)}">',
         f'<meta property="og:description" content="{e(satz)}">',
         '<meta property="og:locale" content="de_CH">',
         '<meta name="twitter:card" content="summary_large_image">',
         f'<meta name="twitter:title" content="{e(titel)}">',
         f'<meta name="twitter:description" content="{e(satz)}">']
    if url:
        wurzel = url.rsplit("abstimmung/", 1)[0]
        z += [f'<meta property="og:url" content="{e(url)}">',
              f'<meta property="og:image" content="{e(wurzel)}vorschau.png">',
              f'<meta name="twitter:image" content="{e(wurzel)}vorschau.png">',
              f'<link rel="canonical" href="{e(url)}">']
    z += ['<link rel="icon" href="../../favicon.svg" type="image/svg+xml">',
          '<link rel="icon" href="../../favicon.png" sizes="32x32" type="image/png">',
          '<link rel="apple-touch-icon" href="../../apple-touch-icon.png">',
          '<meta name="theme-color" content="#0B0F14">']
    return "\n".join(z)

# Die beiden Seiten. Namen kommen aus vorlage.json («seiten»), hier stehen
# die Voreinstellungen fuer eine Vorlage ohne benannte Komitees. Die Module
# lesen SEITE_NAME und SEITE_KOMITEE; bauen() fuellt sie aus der Vorlage.
SEITE_NAME = {"pro": "Für die Vorlage", "contra": "Gegen die Vorlage"}
SEITE_KOMITEE = {"pro": "Befürworter", "contra": "Gegner"}
SEITE_EMPFEHLUNG = {"pro": "Ja", "contra": "Nein"}


def seiten_setzen(v: dict) -> None:
    """Uebernimmt die Seitennamen aus vorlage.json:
        "seiten": {"pro": {"name": "Für die Initiative", "komitee": "Initiativkomitee",
                           "empfehlung": "Ja zur Initiative, Nein zum Gegenvorschlag"},
                   "contra": {...}}
    Fehlt ein Feld, bleibt die Voreinstellung."""
    for s in ("pro", "contra"):
        d = (v.get("seiten") or {}).get(s) or {}
        SEITE_NAME[s] = d.get("name", SEITE_NAME[s])
        SEITE_KOMITEE[s] = d.get("komitee", SEITE_KOMITEE[s])
        SEITE_EMPFEHLUNG[s] = d.get("empfehlung", SEITE_EMPFEHLUNG[s])

TYP_NAME = {"tatsache": "Tatsachenbehauptung", "prognose": "Prognose", "wertung": "Werturteil"}
TYP_HINWEIS = {
    "tatsache": "überprüfbar an Daten und Texten",
    "prognose": "nicht wahr oder falsch, geprüft wird die Evidenzbasis",
    "wertung": "nicht am Beleg prüfbar",
}

STATUS_ZEICHEN = {"beantwortet": "beantwortet", "offen": "offen", "nein": "nicht erfüllt"}

QUELLENART = {
    "amtlich": "amtlich",
    "wissenschaft": "Wissenschaft",
    "medien": "Medien",
    "interessengruppe": "Interessengruppe",
    "komitee": "Komitee",
}


def e(text) -> str:
    return html.escape(str(text), quote=True)


# ---------------------------------------------------------------- Netzgrafik

def netzgrafik(achsen, werte_pro, werte_contra, groesse=440) -> str:
    """Fuenfachsige Netzgrafik mit zwei Polygonen. Werte 0 bis 4."""
    mitte = groesse / 2
    radius = groesse * 0.30
    n = len(achsen)

    def punkt(i, wert):
        w = -math.pi / 2 + i * 2 * math.pi / n
        r = radius * (wert / 4.0)
        return (mitte + r * math.cos(w), mitte + r * math.sin(w))

    def rand(i, faktor=1.0):
        w = -math.pi / 2 + i * 2 * math.pi / n
        return (mitte + radius * faktor * math.cos(w), mitte + radius * faktor * math.sin(w))

    t = [f'<svg viewBox="0 0 {groesse} {groesse}" class="netz" role="img" '
         f'aria-label="Belegqualität beider Seiten auf fünf Achsen">']

    for stufe in (1, 2, 3, 4):
        ecken = " ".join(f"{x:.1f},{y:.1f}" for x, y in (rand(i, stufe / 4.0) for i in range(n)))
        t.append(f'<polygon points="{ecken}" class="netz-ring"/>')
    for i in range(n):
        x, y = rand(i)
        t.append(f'<line x1="{mitte}" y1="{mitte}" x2="{x:.1f}" y2="{y:.1f}" class="netz-speiche"/>')

    for werte, klasse in ((werte_contra, "netz-contra"), (werte_pro, "netz-pro")):
        ecken = " ".join(f"{x:.1f},{y:.1f}" for x, y in
                         (punkt(i, werte[a["id"]]) for i, a in enumerate(achsen)))
        t.append(f'<polygon points="{ecken}" class="{klasse}"/>')
        for i, a in enumerate(achsen):
            x, y = punkt(i, werte[a["id"]])
            t.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" class="{klasse}-punkt"/>')

    for i, a in enumerate(achsen):
        x, y = rand(i, 1.30)
        anker = "middle" if abs(x - mitte) <= 8 else ("end" if x < mitte else "start")
        t.append(
            f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anker}" class="netz-titel">{e(a["kurz"])}</text>'
            f'<text x="{x:.1f}" y="{y + 15:.1f}" text-anchor="{anker}" class="netz-wert">'
            f'{werte_pro[a["id"]]:.1f} zu {werte_contra[a["id"]]:.1f}</text>')
    t.append("</svg>")
    return "".join(t)


def mininetz(achsen, pruefung, seite, groesse=132, mit_beschriftung=False) -> str:
    """Ein Netz je Argument. Achsen mit 'nicht anwendbar' werden uebersprungen und
    als gestrichelte Speiche gezeichnet, statt als Null gewertet."""
    mitte = groesse / 2
    radius = groesse * (0.33 if mit_beschriftung else 0.40)
    n = len(achsen)

    def pol(i, faktor):
        w = -math.pi / 2 + i * 2 * math.pi / n
        return (mitte + radius * faktor * math.cos(w), mitte + radius * faktor * math.sin(w))

    t = [f'<svg viewBox="0 0 {groesse} {groesse}" class="mininetz" role="img">']
    for stufe in (2, 4):
        ecken = " ".join(f"{x:.1f},{y:.1f}" for x, y in (pol(i, stufe / 4.0) for i in range(n)))
        t.append(f'<polygon points="{ecken}" class="netz-ring"/>')

    aktiv = []
    for i, a in enumerate(achsen):
        x, y = pol(i, 1.0)
        na = pruefung.get(a["id"]) is None
        t.append(f'<line x1="{mitte}" y1="{mitte}" x2="{x:.1f}" y2="{y:.1f}" '
                 f'class="netz-speiche{" netz-speiche-na" if na else ""}"/>')
        if not na:
            aktiv.append((i, pruefung[a["id"]]))

    if len(aktiv) >= 3:
        ecken = " ".join(f"{x:.1f},{y:.1f}" for x, y in
                         (pol(i, w / 4.0) for i, w in aktiv))
        t.append(f'<polygon points="{ecken}" class="netz-{e(seite)}"/>')
    for i, w in aktiv:
        x, y = pol(i, w / 4.0)
        t.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" class="netz-{e(seite)}-punkt"/>')

    if mit_beschriftung:
        for i, a in enumerate(achsen):
            x, y = pol(i, 1.32)
            anker = "middle" if abs(x - mitte) <= 6 else ("end" if x < mitte else "start")
            t.append(f'<text x="{x:.1f}" y="{y + 3:.1f}" text-anchor="{anker}" '
                     f'class="netz-mini-titel">{e(a["kurz"])}</text>')
    t.append("</svg>")
    return "".join(t)


# ---------------------------------------------------------------- Bausteine

def punkte(arg, achsen):
    """Erreichte und moegliche Punkte. Nicht anwendbare Achsen zaehlen nirgends mit."""
    p = arg.get("pruefung") or {}
    anwendbar = [a["id"] for a in achsen if p.get(a["id"]) is not None]
    return sum(p[i] for i in anwendbar), 4 * len(anwendbar)


def kurzfassung(text, laenge=94) -> str:
    if len(text) <= laenge:
        return text
    schnitt = text[:laenge].rsplit(" ", 1)[0]
    return schnitt + " …"

def belegbalken(achsen, pruefung) -> str:
    zeilen = []
    for a in achsen:
        wert = pruefung.get(a["id"])
        if wert is None:
            zeilen.append(
                f'<div class="balken balken-na" title="{e(a["frage"])}">'
                f'<span class="balken-name">{e(a["kurz"])}</span>'
                f'<span class="balken-spur balken-spur-na">nicht anwendbar</span>'
                f'<span class="balken-zahl">–</span></div>')
            continue
        segmente = "".join(
            f'<span class="seg {"seg-voll" if k < wert else "seg-leer"}"></span>' for k in range(4))
        zeilen.append(
            f'<div class="balken" title="{e(a["frage"])}">'
            f'<span class="balken-name">{e(a["kurz"])}</span>'
            f'<span class="balken-spur">{segmente}</span>'
            f'<span class="balken-zahl">{wert}</span></div>')
    return f'<div class="balken-block">{"".join(zeilen)}</div>'


def fundstelle_block(arg) -> str:
    f = arg.get("fundstelle")
    if not f:
        return ('<p class="fundstelle fundstelle-offen">Fundstelle offen. Diese Aussage ist im '
                'Abstimmungskampf zu hören, aber noch nicht mit Urheber und Datum belegt. '
                'Sie zählt darum nicht in die Netzgrafik.</p>')
    datum = f' · {e(f["datum"])}' if f.get("datum") else ""
    return (f'<p class="fundstelle">Fundstelle: '
            f'<a href="{e(f["url"])}" target="_blank" rel="noopener">{e(f["titel"])}</a>{datum}</p>')


def karte(arg, achsen) -> str:
    seite, typ = arg["seite"], arg.get("typ", "tatsache")
    offen = arg.get("stand") == "fundstelle_offen"

    fragen = "".join(
        f'<li class="kf"><span class="kf-frage">{e(k["frage"])}</span>'
        f'<span class="kf-status kf-{e(k["status"])}">{e(STATUS_ZEICHEN.get(k["status"], k["status"]))}</span>'
        f'<span class="kf-kommentar">{e(k["kommentar"])}</span></li>'
        for k in arg.get("kritische_fragen", []))
    fragen_block = (
        f'<details class="pk pk-neben"><summary><span class="pk-titel">Kritische Fragen'
        f'<span class="schema">{e(arg.get("schema", ""))}</span></span>'
        f'<span class="pk-anriss">{len(arg.get("kritische_fragen", []))} Prüffragen zu diesem '
        f'Argumenttyp, davon {sum(1 for k in arg.get("kritische_fragen", []) if k["status"] != "beantwortet")} offen '
        f'oder nicht erfüllt</span></summary>'
        f'<div class="pk-inhalt"><ul class="kf-liste">{fragen}</ul></div></details>'
    ) if fragen else ""

    belege = "".join(
        f'<li><a href="{e(b["url"])}" target="_blank" rel="noopener">{e(b["titel"])}</a>'
        f' <span class="quellenart">{e(QUELLENART.get(b.get("art", ""), b.get("art", "")))}</span></li>'
        for b in arg.get("belege", []))
    arten = [QUELLENART.get(b.get("art", ""), b.get("art", "")) for b in arg.get("belege", [])]
    belege_block = (
        f'<details class="pk pk-neben"><summary><span class="pk-titel">Grundlagen der Prüfung</span>'
        f'<span class="pk-anriss">{len(belege_liste(arg))} Quellen: {e(", ".join(sorted(set(arten))))}'
        f'</span></summary><div class="pk-inhalt"><ul class="beleg-liste">{belege}</ul></div></details>'
    ) if belege else ""

    ist_wertung = typ == "wertung"
    bewertung = "" if ist_wertung else belegbalken(achsen, arg.get("pruefung", {}))
    hinweis = ('<p class="wertung-hinweis">Werturteil. Steht ohne Note, weil sich '
               'kein Beleg dafür prüfen lässt.</p>') if ist_wertung else ""

    kopf_zu = "Was daran stimmt" if ist_wertung else "Was zutrifft"
    kopf_fehlt = "Warum ohne Note" if ist_wertung else "Was fehlt"

    if ist_wertung:
        note = '<span class="karte-punkte karte-punkte-na">ohne Note</span>'
    else:
        erreicht, moeglich = punkte(arg, achsen)
        note = (f'<span class="karte-punkte">{erreicht} von {moeglich} Punkten</span>')

    return f"""
<article class="karte karte-{e(seite)}{' karte-offen' if offen else ''}{' karte-wertung' if ist_wertung else ''}" id="arg-{e(arg['id'])}">
  <div class="karte-kopf">
    <span class="marke marke-{e(seite)}">{e(SEITE_KOMITEE[seite])}</span>
    <span class="typ">{e(TYP_NAME.get(typ, typ))}<em>{e(TYP_HINWEIS.get(typ, ''))}</em></span>
  </div>
  <div class="karte-note">{note}<a class="karte-zurueck" href="#uebersicht">zur Übersicht</a></div>
  <blockquote class="aussage">{e(arg["aussage"])}</blockquote>
  <p class="traeger">{marke("komitee")}{e(arg["traeger"])}</p>
  {fundstelle_block(arg)}
  {hinweis}
  {bewertung}
  <div class="praezis">
    {klappe(kopf_zu, arg["trifft_zu"], "zu")}
    {klappe(kopf_fehlt, arg["fehlt"], "fehlt")}
  </div>
  <div class="karte-kaesten">
    {grafik_block(arg)}
    {fragen_block}
    {belege_block}
  </div>
</article>"""


def anriss(text: str, laenge: int = 78) -> str:
    """Erster Satzanfang als Vorschau in der zugeklappten Kopfzeile."""
    t = " ".join(text.split())
    if len(t) <= laenge:
        return t
    return t[:laenge].rsplit(" ", 1)[0] + " …"


NUMMER = re.compile(r"^\d+\.\s+")


def absaetze(text: str) -> str:
    """Text zu HTML: Absaetze durch Leerzeile getrennt, nummerierte Listen als
    Liste. Ein Absatz, dessen Zeilen alle mit «1.», «2.» … beginnen, wird zur
    <ol>; die Nummer im Text faellt weg, der Browser zaehlt. Regel seit dem
    3. September 2026: Aufzaehlungen stehen als nummerierte Liste, nicht als
    Fliesstext, damit die Seite schnell zu lesen ist und die Punkte sich
    einzeln zitieren lassen."""
    teile = []
    for a in text.split("\n\n"):
        zeilen = [z.strip() for z in a.strip().split("\n") if z.strip()]
        if zeilen and all(NUMMER.match(z) for z in zeilen):
            li = "".join(f"<li>{e(NUMMER.sub('', z))}</li>" for z in zeilen)
            teile.append(f"<ol>{li}</ol>")
        elif zeilen:
            teile.append(f"<p>{e(' '.join(zeilen))}</p>")
    return "".join(teile)


def klappe(titel: str, text: str, art: str) -> str:
    """Aufklappbarer Block. Zu heisst Anriss sichtbar, auf heisst voller Text."""
    return (f'<details class="pk pk-{e(art)}">'
            f'<summary><span class="pk-titel">{e(titel)}</span>'
            f'<span class="pk-anriss">{e(anriss(text))}</span></summary>'
            f'<div class="pk-inhalt">{absaetze(text)}</div></details>')


def zahlhinweis_block(arg) -> str:
    """Offengelegte Abweichung zwischen nachgerechneter und im Bericht genannter Zahl."""
    h = arg.get("zahlhinweis")
    return f'<p class="zahlhinweis">{e(h)}</p>' if h else ""


def abschnitt(kennung: str, titel: str, hinweis: str, inhalt: str, offen: bool = True) -> str:
    """Ein Seitenabschnitt als aufklappbarer Block, damit die Seite überschaubar bleibt."""
    return (f'<section id="{e(kennung)}" class="ab">'
            f'<details class="ab-klapp"{" open" if offen else ""}>'
            f'<summary><h2>{e(titel)}</h2>'
            f'<span class="ab-hinweis">{hinweis}</span></summary>'
            f'<div class="ab-inhalt">{inhalt}</div></details></section>')


def belege_liste(arg):
    return arg.get("belege", [])


def marke(art: str) -> str:
    """Herkunftsmarke. Eigene Auswertung wird kräftig gesetzt, damit sie sich von
    amtlichen Quellen und von Komitee-Aussagen klar abhebt."""
    texte = {"eigen": "Eigene Auswertung", "amtlich": "Amtliche Quelle",
             "komitee": "Aussage eines Komitees", "extern": "Fremde Quelle"}
    return f'<span class="hk hk-{e(art)}">{e(texte.get(art, art))}</span>'


def grafik_block(arg) -> str:
    """Grafik und Zahlhinweis in einem eigenen Klappkasten, damit die Karte ruhig bleibt."""
    grafiken = arg.get("grafiken") or ([arg["grafik"]] if arg.get("grafik") else [])
    h = arg.get("zahlhinweis")
    if not grafiken and not h:
        return ""

    inhalt = ""
    for g in grafiken:
        eigen = g["quelle"].lower().startswith("eigene")
        inhalt += (f'<figure class="agrafik{" agrafik-eigen" if eigen else ""}">'
                   f'<img src="grafiken/{e(g["datei"])}.svg" alt="{e(g["titel"])}"'
                   f' loading="lazy" class="zoombar" tabindex="0"'
                   f' data-titel="{e(g["titel"])}">'
                   f'<figcaption>{marke("eigen") if eigen else marke("extern")}'
                   f'<b>{e(g["titel"])}</b> {e(g.get("hinweis", ""))}'
                   f'<span class="agrafik-quelle">{e(g["quelle"])}</span></figcaption></figure>')
    if h:
        inhalt += f'<div class="zahlhinweis">{absaetze(h)}</div>'

    anriss = (" · ".join(g["titel"] for g in grafiken) if grafiken
              else "Hinweis zur Herleitung der Zahlen")
    zahl = len(grafiken)
    kopf = (f'{zahl} Grafik' + ("en" if zahl != 1 else "")) if zahl else "Herleitung"
    return (f'<details class="pk pk-eigen"><summary>'
            f'<span class="pk-titel">{marke("eigen")}{kopf}</span>'
            f'<span class="pk-anriss">{e(anriss)}</span></summary>'
            f'<div class="pk-inhalt">{inhalt}</div></details>')


def uebersicht(args, achsen) -> str:
    """Alle Argumente auf einen Blick, mit Punktzahl und Sprung zur Karte."""
    zeilen = []
    for a in args:
        wertung = a.get("typ") == "wertung"
        if wertung:
            zahl = ''
            spur = '<span class="ue-spur-na">Werturteil, ohne Note</span>'
        else:
            erreicht, moeglich = punkte(a, achsen)
            anteil = erreicht / moeglich if moeglich else 0
            zahl = (f'<span class="ue-zahl"><b>{erreicht}</b> von {moeglich}</span>')
            spur = (f'<span class="ue-spur"><span class="ue-fuell ue-{e(a["seite"])}" '
                    f'style="width:{anteil*100:.0f}%"></span></span>')
        zeilen.append(f"""
<a class="ue-zeile ue-zeile-{e(a['seite'])}" href="#arg-{e(a['id'])}">
  <span class="ue-marke ue-marke-{e(a['seite'])}">{e(SEITE_KOMITEE[a['seite']])}</span>
  <span class="ue-text">{e(kurzfassung(a['aussage']))}</span>
  <span class="ue-typ">{e(TYP_NAME.get(a.get('typ',''), ''))}</span>
  {spur}{zahl}
</a>""")

    def summe(seite):
        sel = [a for a in args if a["seite"] == seite and a.get("typ") != "wertung"]
        er = sum(punkte(a, achsen)[0] for a in sel)
        mo = sum(punkte(a, achsen)[1] for a in sel)
        return er, mo

    ep, mp = summe("pro")
    ec, mc = summe("contra")

    return abschnitt("uebersicht", "Alle Argumente auf einen Blick",
        "Die Punktzahl misst den Beleg einer Aussage, nicht ihre Richtigkeit. "
        "Höchstpunktzahl sind 4 Punkte je anwendbare Achse; Achsen, die auf eine Aussage nicht "
        "passen, senken die erreichbare Zahl, statt eine Null zu erzeugen. Darum steht überall "
        "«x von y» und nicht ein Prozentwert.",
        f'<div class="ue-liste">{"".join(zeilen)}</div>'
        f'<p class="ue-summe">Zusammengezählt: {e(SEITE_KOMITEE["pro"])} <b>{ep} von {mp}</b> Punkten, '
        f'{e(SEITE_KOMITEE["contra"])} <b>{ec} von {mc}</b>. Die Werturteile sind in beiden Zahlen nicht '
        f'enthalten.</p>')


def textkritik_block(tk) -> str:
    """Was der Abstimmungstext offen laesst. Keine Wertung, nur Bestandsaufnahme."""
    if not tk:
        return ""
    stellen = []
    for i, s in enumerate(tk["stellen"], 1):
        tab = ""
        if s.get("tabelle"):
            t = s["tabelle"]
            kopf = "".join(f"<th>{e(k)}</th>" for k in t["kopf"])
            zeilen = "".join("<tr>" + "".join(f"<td>{e(z)}</td>" for z in r) + "</tr>"
                             for r in t["zeilen"])
            tab = (f'<div class="tk-tabelle"><p class="tk-tab-titel">{marke("eigen")}{e(t["titel"])}</p>'
                   f'<div class="tk-scroll"><table><thead><tr>{kopf}</tr></thead>'
                   f'<tbody>{zeilen}</tbody></table></div>'
                   f'<p class="tk-tab-fuss">{e(t["fuss"])}</p></div>')
        stellen.append(f"""
<article class="tk-karte">
  <div class="tk-kopf"><span class="tk-nr">{i}</span>
    <div><h3>{e(s['begriff'])}</h3><span class="tk-wo">{e(s['wo'])}</span></div></div>
  <blockquote class="tk-wortlaut">{e(s['wortlaut'])}</blockquote>
  <div class="praezis">
    <div class="praezis-teil"><h4>Was offen bleibt</h4>{absaetze(s['problem'])}</div>
  </div>
  {tab}
  <div class="praezis">
    <div class="praezis-teil praezis-zu"><h4>Was das bedeutet</h4>
      {absaetze(s['folge'])}</div>
  </div>
  <p class="tk-quelle">{e(s['quelle'])}</p>
</article>""")

    return abschnitt("textkritik", "Was der Abstimmungstext offen lässt",
        e(tk["einleitung"]), f'<div class="tk-liste">{"".join(stellen)}</div>')


def karte_block(k) -> str:
    """Geltungsbereich und Umkreise sensibler Nutzungen, je Gemeinde."""
    if not k:
        return ""

    def datei(name):
        n = name.replace(" ", "_")
        return n.split("_am_")[0] if "_am_Rheinfall" in n else n

    g = k["gemeinden"]
    knoepfe = "".join(
        f'<button class="km-knopf{" km-aktiv" if i == 0 else ""}" data-i="{i}">{e(x["gemeinde"])}</button>'
        for i, x in enumerate(g))

    zeilen = "".join(
        f'<tr><td>{e(x["gemeinde"])}</td>'
        f'<td class="z">{x["betroffen_km"]:.2f}</td>'
        f'<td class="z">{x["km100"]:.2f}</td><td class="z z-leise">{x["p100"]:.0f} %</td>'
        f'<td class="z">{x["km300"]:.2f}</td><td class="z z-leise">{x["p300"]:.0f} %</td>'
        f'<td class="z">{x["km500"]:.2f}</td><td class="z z-leise">{x["p500"]:.0f} %</td>'
        f'<td class="z z-leise">{e(x["anlagen"])}</td></tr>'.replace(".", ",")
        for x in g)
    t = k["total"]
    summe = (f'<tr class="km-summe"><td>Kanton</td><td class="z">{t["betroffen_km"]:.2f}</td>'
             f'<td class="z">{t["km100"]:.2f}</td><td class="z z-leise">{t["p100"]:.0f} %</td>'
             f'<td class="z">{t["km300"]:.2f}</td><td class="z z-leise">{t["p300"]:.0f} %</td>'
             f'<td class="z">{t["km500"]:.2f}</td><td class="z z-leise">{t["p500"]:.0f} %</td>'
             f'<td class="z z-leise">{e(t["anlagen"])}</td></tr>').replace(".", ",")

    daten = json.dumps([{"n": x["gemeinde"], "d": datei(x["gemeinde"]), "b": x["betroffen_km"],
                         "k1": x["km100"], "p1": x["p100"], "k3": x["km300"], "p3": x["p300"],
                         "k5": x["km500"], "p5": x["p500"], "a": x["anlagen"]} for x in g],
                       ensure_ascii=False)

    quellen = "".join(f'<li>{e(q["titel"])}</li>' for q in k["quellen"])

    # Der erste Absatz der Einleitung steht in der Kopfzeile des Abschnitts,
    # der Rest (meist eine Liste) im Inhalt: In einer Kopfzeile ist keine
    # Liste moeglich.
    ein_kopf, _, ein_rest = k["einleitung"].partition("\n\n")
    return abschnitt("karte", "Wo die Vorlage gilt, und wer in der Nähe ist",
        marke("eigen") + e(ein_kopf), f"""
  <div class="km-einleitung">{absaetze(ein_rest)}</div>
  <div class="km-block">
    <div class="km-knoepfe">{knoepfe}</div>
    <div class="km-buehne">
      <img id="km-bild" src="grafiken/gemeinden/karte_Schaffhausen.svg"
           class="zoombar" tabindex="0" data-titel="Betroffene Kantonsstrassen und Umkreise"
           alt="Karte der betroffenen Kantonsstrassen und der Umkreise sensibler Nutzungen">
    </div>
    <div class="km-zahlen" id="km-zahlen"></div>
  </div>

  <p class="lesehilfe"><b>Zur Lesart.</b> {e(k['warnung'])}</p>

  <details class="km-tabelle">
    <summary>Alle Gemeinden als Tabelle</summary>
    <div class="tk-scroll"><table>
      <thead><tr><th>Gemeinde</th><th>betroffen km</th>
        <th>≤ 100 m</th><th></th><th>≤ 300 m</th><th></th><th>≤ 500 m</th><th></th>
        <th>Anlagen S/K/H/So</th></tr></thead>
      <tbody>{zeilen}{summe}</tbody>
    </table></div>
    <p class="tk-tab-fuss">{e(k['anlagen_total'])}. S = Schulen, K = Kindergärten,
    H = Alters- und Pflegeheime, So = weitere Sozialeinrichtungen.</p>
  </details>

  <details class="pk pk-neben"><summary><span class="pk-titel">Datengrundlagen der Karte</span>
    <span class="pk-anriss">{len(k["quellen"])} Quellen</span></summary>
    <div class="pk-inhalt"><ul class="beleg-liste">{quellen}</ul></div></details>
  <script id="km-daten" type="application/json">{daten}</script>""")


FREIGEGEBEN = VORLAGE / "geo" / "03_freigegeben"
GEOJSON = FREIGEGEBEN / "kandidaten_wgs84.geojson"
HALTESTELLEN = FREIGEGEBEN / "haltestellen_bus_wgs84.geojson"
BUSNETZ = FREIGEGEBEN / "busnetz_wgs84.geojson"
KANTONSSTRASSEN = FREIGEGEBEN / "kantonsstrassen_vo_wgs84.geojson"

# Amtliche Kachelebenen, alle am 3.9.2026 gegen wmts.geo.admin.ch geprueft.
WMTS = [
    {"id": "ch.astra.unfaelle-personenschaeden_alle", "ts": "99990101", "fmt": "png",
     "name": "Unfälle mit Personenschaden", "quelle": "ASTRA",
     "hinweis": "Alle Unfälle seit 2011. Punktdichte bildet vor allem Verkehrsmenge ab."},
    {"id": "ch.astra.unfaelle-personenschaeden_fussgaenger", "ts": "99990101", "fmt": "png",
     "name": "davon mit Fussgängern", "quelle": "ASTRA", "hinweis": ""},
    {"id": "ch.bafu.laerm-strassenlaerm_tag", "ts": "current", "fmt": "png",
     "name": "Strassenlärm am Tag", "quelle": "BAFU sonBASE",
     "hinweis": "Modellierte Belastung, kein Messwert."},
    {"id": "ch.astra.hauptstrassennetz", "ts": "current", "fmt": "png",
     "name": "Hauptstrassennetz", "quelle": "ASTRA", "hinweis": ""},
]
GRUNDKARTEN = [
    {"key": "osm", "name": "OpenStreetMap"},
    {"key": "ch.swisstopo.pixelkarte-grau", "ts": "current", "fmt": "jpeg", "name": "Landeskarte grau"},
    {"key": "ch.swisstopo.swisstlm3d-karte-grau", "ts": "current", "fmt": "png", "name": "swissTLM grau"},
]

# Kantonale Ebenen, Endpunkt und Namen am 3.9.2026 gegen wms.geo.sh.ch geprueft.
WMS_SH = "https://wms.geo.sh.ch/wms"
SH_LAYER = [
    {"id": "sh.richtplan.strassenrichtplan.kanton.ortstafeln", "name": "Ortstafeln",
     "hinweis": "Die rechtlich massgebende Innerorts-Grenze."},
    {"id": "sh.nutzungsplanung.rechtsgueltig.baugebiet", "name": "Baugebiet",
     "hinweis": "In der Auswertung als Näherung für innerorts verwendet, nicht deckungsgleich mit den Ortstafeln."},
]

# Was die beiden Erlasstexte als Geltungsbereich bestimmen.
GELTUNG = [
    {"key": "initiative", "name": "Initiative",
     "kriterium": "Kantonsstrassen innerorts, <b>die auch durch den öffentlichen Verkehr genutzt werden</b>",
     "ebenen": ["sh.richtplan.strassenrichtplan.kanton.ortstafeln"],
     "strassen": True, "halte": True, "bus": True,
     "text": ("Die Initiative knüpft nicht an die Funktion der Strasse an, sondern daran, ob ein Bus "
              "fährt. Eingeblendet sind darum das Busnetz, 242 Kilometer befahrene Strassen aus den "
              "Linienrelationen von OpenStreetMap für VBSH, PostAuto und PAZ, sowie die 283 "
              "Bushaltestellen aus der Ebene des Bundesamts für Verkehr. Wo eine dunkle "
              "Busnetz-Linie auf einer Kantonsstrasse innerorts liegt, greift die Initiative. "
              "Die beiden Quellen stützen sich gegenseitig: 24 von 25 stichprobenweise geprüften "
              "Haltestellen liegen weniger als 50 Meter von der Linienführung entfernt, der Median "
              "beträgt 4 Meter. Die Linienführung ist allerdings betrieblich und nicht amtlich, "
              "und sie ändert mit jedem Fahrplanwechsel.")},
    {"key": "gegenvorschlag", "name": "Gegenvorschlag",
     "kriterium": "<b>verkehrsorientierte</b> Kantonsstrassen innerorts, ohne Bedingung zum öffentlichen Verkehr",
     "ebenen": ["sh.richtplan.strassenrichtplan.kanton.ortstafeln"],
     "strassen": True,
     "text": ("Der Gegenvorschlag knüpft genau an das an, was der eingeblendete Richtplan zeigt: "
              "die Funktionszuweisung. Verkehrsorientiert sind die überregionalen und regionalen "
              "Kantonsstrassen, zusammen 43,9 km innerorts. Dieser Geltungsbereich ist damit direkt "
              "aus amtlichen Daten ablesbar, der der Initiative nicht.")},
]


def viewer_block(k) -> str:
    """Leaflet-Viewer: eigene Kandidatenlinien plus zuschaltbare amtliche Ebenen."""
    if not GEOJSON.exists() or not k:
        return ""
    geo = GEOJSON.read_text(encoding="utf-8")

    basen = "".join(
        f'<label class="vw-opt"><input type="radio" name="vw-base" value="{e(b["key"])}"'
        f'{" checked" if i == 0 else ""}><span>{e(b["name"])}</span></label>'
        for i, b in enumerate(GRUNDKARTEN))

    eigene = (
        '<label class="vw-opt"><input type="checkbox" id="vw-k100" checked>'
        '<span><i class="vw-linie vw-l100"></i>Kandidat bis 100 m</span></label>'
        '<label class="vw-opt"><input type="checkbox" id="vw-k300" checked>'
        '<span><i class="vw-linie vw-l300"></i>Kandidat bis 300 m</span></label>')

    amtlich = "".join(
        f'<label class="vw-opt" title="{e(w["hinweis"])}">'
        f'<input type="checkbox" class="vw-wmts" data-id="{e(w["id"])}" data-ts="{e(w["ts"])}"'
        f' data-fmt="{e(w["fmt"])}"><span>{e(w["name"])}'
        f'<em>{e(w["quelle"])}</em></span></label>' for w in WMTS)
    # Rasterebenen des Bundes decken die Karte flaechig und ueberdecken die
    # eigenen Linien. Ein Regler statt einer festen Deckung, weil die
    # brauchbare Einstellung von der Ebene und vom Zoom abhaengt.
    amtlich += ('<div class="vw-regler"><label for="vw-deck">Deckung der '
                'Rasterebenen</label>'
                '<input type="range" id="vw-deck" min="20" max="100" step="5" value="55">'
                '<output for="vw-deck" id="vw-deck-aus">55&#8201;%</output></div>')

    kantonal = "".join(
        f'<label class="vw-opt" title="{e(w["hinweis"])}">'
        f'<input type="checkbox" class="vw-shwms" data-id="{e(w["id"])}">'
        f'<span>{e(w["name"])}<em>Kanton Schaffhausen</em></span></label>' for w in SH_LAYER)

    geltung = "".join(
        f'<button class="vw-gknopf" data-key="{e(g["key"])}">{e(g["name"])}</button>'
        for g in GELTUNG)
    geltung_daten = json.dumps({g["key"]: {"k": g["kriterium"], "t": g["text"], "l": g["ebenen"],
                                           "h": bool(g.get("halte")), "b": bool(g.get("bus")),
                                           "s": bool(g.get("strassen"))}
                                for g in GELTUNG}, ensure_ascii=False)

    strassen = KANTONSSTRASSEN.read_text(encoding="utf-8") if KANTONSSTRASSEN.exists() else ""
    strassen_opt = ('<label class="vw-opt" title="Überregional und regional gelten als verkehrsorientiert.">'
                    '<input type="checkbox" id="vw-strassen">'
                    '<span><i class="vw-linie vw-lstr"></i>Kantonsstrassen, verkehrsorientiert'
                    '<em>Strassenrichtplan, 107 km</em></span></label>') if strassen else ""
    strassen_script = (f'<script id="vw-strassen-daten" type="application/json">{strassen}</script>'
                       if strassen else "")

    halte = HALTESTELLEN.read_text(encoding="utf-8") if HALTESTELLEN.exists() else ""
    bus = BUSNETZ.read_text(encoding="utf-8") if BUSNETZ.exists() else ""
    halte_opt = ('<label class="vw-opt" title="Haltestellen sind nicht die Linienführung.">'
                 '<input type="checkbox" id="vw-halte">'
                 '<span><i class="vw-punkt"></i>Bushaltestellen<em>Bundesamt für Verkehr</em>'
                 '</span></label>') if halte else ""
    bus_opt = ('<label class="vw-opt" title="Betriebliche Linienführung, nicht amtlich.">'
               '<input type="checkbox" id="vw-bus">'
               '<span><i class="vw-linie vw-lbus"></i>Busnetz, 242 km<em>OpenStreetMap</em>'
               '</span></label>') if bus else ""
    halte_script = (f'<script id="vw-halte-daten" type="application/json">{halte}</script>'
                    if halte else "")
    bus_script = (f'<script id="vw-bus-daten" type="application/json">{bus}</script>'
                  if bus else "")

    # Gemeinden ohne Kandidatenlinien koennen nicht angesprungen werden, das steht auch so da.
    sprung = "".join(
        f'<option value="{e(x["gemeinde"])}"{"" if x.get("linien") else " disabled"}>'
        f'{e(x["gemeinde"])}'
        f'{"" if x.get("linien") else " (keine Kandidaten)"}</option>'
        for x in k["gemeinden"])
    ohne = [x["gemeinde"] for x in k["gemeinden"] if not x.get("linien")]
    ohne_satz = (f' In {", ".join(ohne[:-1])} und {ohne[-1]} liegt keine betroffene Strasse '
                 f'innerhalb von 300 Metern einer solchen Nutzung; diese Gemeinden lassen sich '
                 f'darum nicht anspringen.') if len(ohne) > 1 else ""

    return abschnitt("viewer", "Selber nachschauen",
        "Dieselben Daten als Karte zum Bewegen und Zoomen. Die dunklen Linien sind die betroffenen "
        "Strassenabschnitte in der Nähe einer Schule, eines Kindergartens oder eines Heims, aus der "
        "eigenen Auswertung. Die übrigen Ebenen kommen live von Bund und Kanton, sie werden hier "
        "nicht kopiert, sondern jedes Mal frisch geladen." + e(ohne_satz), f"""

  <div class="vw-geltung">
    <div class="vw-gknoepfe"><span class="vw-glabel">Geltungsbereich zeigen</span>
      {geltung}<button class="vw-gknopf vw-gaus vw-gaktiv" data-key="">aus</button></div>
    <div class="vw-gtext" id="vw-gtext"></div>
  </div>

  <div class="vw-block">
    <div class="vw-steuer">
      <div class="vw-gruppe"><h4>Grundkarte</h4>{basen}</div>
      <div class="vw-gruppe"><h4>{marke('eigen')}</h4>{eigene}</div>
      <div class="vw-gruppe"><h4>Kanton Schaffhausen</h4>{strassen_opt}{kantonal}</div>
      <div class="vw-gruppe"><h4>Bund</h4>{amtlich}{halte_opt}</div>
      <div class="vw-gruppe"><h4>Öffentlicher Verkehr</h4>{bus_opt}</div>
      <div class="vw-gruppe"><h4>Hinspringen</h4>
        <select id="vw-sprung"><option value="">ganzer Kanton</option>{sprung}</select></div>
    </div>
    <div class="vw-buehne">
      <div id="vw-karte" class="vw-karte"></div>
      <details class="vw-amtleg" id="vw-amtleg" hidden>
        <summary><span id="vw-amtleg-titel">Amtliche Legende</span><span class="vw-amtleg-pfeil" aria-hidden="true">&#9660;</span></summary>
        <div class="vw-amtleg-inhalt" id="vw-amtleg-inhalt"></div>
      </details>
      <div id="vw-legende" class="vw-legende" hidden>
        <p class="vw-legtitel">Strassenrichtplan</p>
        <p><i class="vw-linie vw-lueber"></i>überregional</p>
        <p><i class="vw-linie vw-lreg"></i>regional</p>
        <p class="vw-legfuss">beides gilt als verkehrsorientiert</p>
      </div>
    </div>
  </div>

  <script id="vw-geltung-daten" type="application/json">{geltung_daten}</script>
  {halte_script}
  {bus_script}
  {strassen_script}

  <p class="lesehilfe"><b>Zur Unfallebene.</b> Eine Häufung heisst nicht «hier ist es
  gefährlich». Sie heisst zuerst, dass dort viel Verkehr ist. Ein Risikovergleich bräuchte eine
  Bezugsgrösse, etwa Unfälle je Million Fahrzeugkilometer, und ein Mehrjahresmittel. Beides ist in
  dieser Ansicht nicht enthalten, sie zeigt Ereignisse, nicht Risiko.</p>

  <script id="vw-geo" type="application/json">{geo}</script>""")


# ------------------------------------------------- Kantonsrat (Phase-2-Bruecke)

def kantonsrat_daten(suchwort: str) -> dict | None:
    """Die namentlichen Abstimmungen zum Geschaeft, frisch aus all_sessions.json,
    als Struktur. Daraus entstehen der Seitenblock und das Bild fuer Social
    Media; beide zaehlen so garantiert dieselben Stimmen."""
    if not SITZUNGEN.exists() or not suchwort:
        return None
    daten = json.loads(SITZUNGEN.read_text(encoding="utf-8"))
    for s in daten.get("sessions", []):
        idx = [i for i, v in enumerate(s.get("votes", []))
               if suchwort.lower() in (v.get("geschaeft") or "").lower()]
        if not idx:
            continue
        protokoll = ""
        for p in s.get("protokolle", []) or []:
            if p.get("url"):
                protokoll = p["url"]
                break
        abstimmungen = []
        for i in idx:
            v = s["votes"][i]
            gesamt = collections.Counter()
            frakt = collections.defaultdict(collections.Counter)
            for m in s["members"]:
                st = m["votes"][i]
                gesamt[st] += 1
                frakt[m["fraktion"]][st] += 1
            abstimmungen.append({
                "nr": v["nr"],
                "titel": v.get("titel") or "",
                "details": v.get("details") or "",
                "ja": gesamt.get("Ja", 0), "nein": gesamt.get("Nein", 0),
                "enth": gesamt.get("Enth", 0), "abw": gesamt.get("V/A/N", 0),
                "umkehr": (v.get("inverted_note") or "")
                          if v.get("richtung_invertiert") else "",
                "fraktionen": [{"name": f, "ja": frakt[f].get("Ja", 0),
                                "nein": frakt[f].get("Nein", 0)} for f in sorted(frakt)],
            })
        return {"sitzung": s["sitzung"], "protokoll": protokoll, "abstimmungen": abstimmungen}
    return None


def kantonsrat_block(kr: dict | None, hinweis: str = "") -> str:
    """Der Seitenblock aus kantonsrat_daten(). «hinweis» kommt aus
    vorlage.kantonsrat_hinweis, etwa eine Gegenprobe mit dem Abstimmungsmagazin."""
    if not kr:
        return ""
    prot = (f' · <a href="{e(kr["protokoll"])}" target="_blank" rel="noopener">Wortprotokoll</a>'
            if kr["protokoll"] else "")
    karten = []
    for v in kr["abstimmungen"]:
        ja, nein, enth, abw = v["ja"], v["nein"], v["enth"], v["abw"]
        umkehr = (f'<p class="kr-umkehr">Richtungsverkehrt: «{e(v["umkehr"])}». '
                  f'Angezeigt ist das protokollierte Ergebnis.</p>' if v["umkehr"] else "")
        zeilen = []
        for f in v["fraktionen"]:
            fja, fnein = f["ja"], f["nein"]
            fs = max(fja + fnein, 1)
            zeilen.append(
                f'<div class="kr-frakt"><span class="kr-fname">{e(f["name"])}</span>'
                f'<span class="kr-fbalken">'
                f'<span class="kr-ja" style="flex:{fja}"></span>'
                f'<span class="kr-nein" style="flex:{fnein}"></span>'
                f'<span class="kr-rest" style="flex:{max(fs*0.001,0.001)}"></span></span>'
                f'<span class="kr-fzahl">{fja}:{fnein}</span></div>')
        karten.append(f"""
<div class="kr-karte">
  <div class="kr-kopf"><span class="kr-nr">Abstimmung {v['nr']}</span>
    <span class="kr-ergebnis">{ja} Ja : {nein} Nein</span></div>
  <h4>{e(v['titel'])}</h4>
  <p class="kr-detail">{e(v['details'])}</p>
  {umkehr}
  <div class="kr-gesamt"><span class="kr-ja" style="flex:{max(ja,0.001)}"></span>
    <span class="kr-nein" style="flex:{max(nein,0.001)}"></span></div>
  <p class="kr-neben">{enth} Enthaltungen · {abw} abwesend oder nicht teilgenommen</p>
  <details><summary>Fraktionen</summary><div class="kr-frakt-liste">{''.join(zeilen)}</div></details>
</div>""")
    n = len(kr["abstimmungen"])
    return abschnitt("kantonsrat", "Wie der Kantonsrat dazu gestimmt hat",
        f"Dieselbe Vorlage, {n} namentliche Abstimmung{'en' if n != 1 else ''} am "
        f"{e(kr['sitzung'])}{prot}. Gezählt aus den vom Kantonsrat publizierten "
        f"Abstimmungsergebnissen." + (f" {e(hinweis)}" if hinweis else ""),
        f'<div class="kr-raster">{"".join(karten)}</div>')


# ---------------------------------------------------------------- Seite

CSS = """
:root{
  --pro:#0F766E; --pro-text:#0C6A62; --contra:#8E44AD; --contra-text:#7E3C9A;
  --grund:#FFFFFF; --flaeche:#F7F8FA; --karte:#FFFFFF;
  --text:#12161C; --text-leise:#5A626D; --linie:#E2E6EB;
  --seg-voll:#3C4652; --seg-leer:#E2E6EB;
  /* Kartenebenen nach Herkunft. Fuenf Linienebenen lagen zuvor im selben
     Graphitgrau und waren zu zweit nicht auseinanderzuhalten. Die Farbe sagt
     jetzt, wessen Linie das ist, und die Strichart unterscheidet innerhalb
     einer Herkunft, damit die Unterscheidung nicht allein an der Farbe haengt.

     Diese vier Werte aendern mit dem Farbschema NICHT. Kartenkacheln sind in
     beiden Schemata hell, ob von OpenStreetMap oder von swisstopo. Eine im
     dunklen Schema aufgehellte Linie waere auf der hellen Kachel unsichtbar.
     Getrennt davon stehen die Legendenstriche in der Bedienleiste, die auf
     dem Seitenhintergrund liegen und darum dem Schema folgen. */
  --geo-eigen:#12161C; --geo-kanton:#0F766E; --geo-bund:#8E44AD; --geo-osm:#6E7783;
  --leg-eigen:#12161C; --leg-kanton:#0F766E; --leg-osm:#6E7783;
}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){
  --pro:#3FB3A8; --pro-text:#3FB3A8; --contra:#C08AD8; --contra-text:#C08AD8;
  --grund:#12161C; --flaeche:#171C24; --karte:#1B212B;
  --text:#EEF1F5; --text-leise:#9AA3AF; --linie:#2C3440;
  --seg-voll:#B9C2CE; --seg-leer:#2C3440;
  /* nur die Legendenstriche, nicht die Kartenlinien, siehe oben */
  --leg-eigen:#EEF1F5; --leg-kanton:#3FB3A8; --leg-osm:#9AA3AF; } }
:root[data-theme="dark"]{
  --pro:#3FB3A8; --pro-text:#3FB3A8; --contra:#C08AD8; --contra-text:#C08AD8;
  --grund:#12161C; --flaeche:#171C24; --karte:#1B212B;
  --text:#EEF1F5; --text-leise:#9AA3AF; --linie:#2C3440;
  --seg-voll:#B9C2CE; --seg-leer:#2C3440; }

*{box-sizing:border-box}
body{margin:0;background:var(--grund);color:var(--text);
  font-family:"Public Sans","Helvetica Neue",Arial,sans-serif;font-size:16px;line-height:1.55}
h1,h2,h3,h4{font-family:Archivo,"Helvetica Neue",Arial,sans-serif;font-weight:600}
.wrap{max-width:1180px;margin:0 auto;padding:0 24px 80px}
a{color:inherit}

.kopf{border-bottom:1px solid var(--linie);padding:34px 0 26px;margin-bottom:30px}
.kopf .ober{display:flex;justify-content:space-between;align-items:baseline;gap:16px;flex-wrap:wrap}
.marke-seite{font-size:13px;letter-spacing:.10em;text-transform:uppercase;color:var(--text-leise);
  font-family:Archivo,sans-serif;font-weight:600}
h1{font-size:clamp(28px,4.2vw,42px);line-height:1.12;margin:12px 0 4px;letter-spacing:-.01em}
.untertitel{color:var(--text-leise);margin:0 0 18px;font-size:17px}
.termin{display:inline-flex;align-items:center;gap:8px;border:1px solid var(--linie);
  border-radius:999px;padding:5px 14px;font-size:14px;font-variant-numeric:tabular-nums}
.lead{margin:18px 0 0;font-size:17px}
.warn{margin:22px 0 0;padding:14px 16px;border:1px dashed var(--linie);
  border-radius:12px;background:var(--flaeche);font-size:14.5px;color:var(--text-leise)}
.warn strong{color:var(--text)}

.folgen{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:26px 0 0}
.folge{border:1px solid var(--linie);border-radius:14px;padding:16px 18px;background:var(--karte)}
.folge h3{margin:0 0 6px;font-size:13px;letter-spacing:.08em;text-transform:uppercase}
.folge p{margin:0;font-size:15px;color:var(--text-leise)}
.folge-ja h3{color:var(--pro-text)} .folge-nein h3{color:var(--contra-text)}
.kontext{margin:16px 0 0;padding:14px 16px;background:var(--flaeche);border-radius:12px;
  font-size:14.5px;color:var(--text-leise)}
.kontext b{color:var(--text);font-family:Archivo,sans-serif;font-weight:600}
.kontext p{margin:0 0 8px} .kontext p:last-child{margin:0}

section{margin-top:52px}
section > h2{font-size:24px;margin:0 0 6px;letter-spacing:-.01em}
section > .hint{color:var(--text-leise);margin:0 0 22px;font-size:15.5px}

/* Übersicht */
.ue-liste{border-top:1px solid var(--linie)}
.ue-zeile{display:grid;grid-template-columns:118px 1fr 132px 92px 78px;gap:14px;align-items:center;
  padding:11px 8px;border-bottom:1px solid var(--linie);text-decoration:none;color:inherit;
  border-radius:8px}
.ue-zeile:hover{background:var(--flaeche)}
.ue-marke{font-family:Archivo,sans-serif;font-weight:600;font-size:10.5px;letter-spacing:.07em;
  text-transform:uppercase;padding:2px 8px;border-radius:999px;border:1px solid currentColor;
  justify-self:start;white-space:nowrap}
.ue-marke-pro{color:var(--pro-text)} .ue-marke-contra{color:var(--contra-text)}
.ue-text{font-size:14.5px;line-height:1.4}
.ue-typ{font-size:12.5px;color:var(--text-leise);white-space:nowrap}
.ue-spur{display:block;height:9px;border-radius:3px;background:var(--seg-leer);overflow:hidden}
.ue-fuell{display:block;height:100%;border-radius:3px}
.ue-pro{background:var(--pro)} .ue-contra{background:var(--contra)}
.ue-spur-na{grid-column:4 / 6;font-size:12px;color:var(--text-leise);font-style:italic;
  text-align:right;white-space:nowrap}
.ue-zahl{font-family:Archivo,sans-serif;font-size:13px;color:var(--text-leise);text-align:right;
  font-variant-numeric:tabular-nums;white-space:nowrap}
.ue-zahl b{color:var(--text);font-size:16px}
.ue-na{font-size:12px;color:var(--text-leise);text-align:right;font-style:italic}
.ue-summe{margin:16px 0 0;font-size:14.5px;color:var(--text-leise)}
.ue-summe b{color:var(--text);font-family:Archivo,sans-serif;font-variant-numeric:tabular-nums}

.netz-block{display:grid;grid-template-columns:minmax(340px,1fr) minmax(300px,420px);gap:36px;
  align-items:start;border:1px solid var(--linie);border-radius:16px;padding:22px;
  background:var(--karte)}
.netz{width:100%;height:auto;overflow:visible}
.netz-ring,.netz-speiche{fill:none;stroke:var(--linie);stroke-width:1}
.netz-speiche-na{stroke-dasharray:3 3;opacity:.55}

/* Small Multiples */
.netz-multi{display:flex;flex-direction:column;gap:18px}
.netz-reihe-titel{font-family:Archivo,sans-serif;font-size:11.5px;font-weight:600;
  letter-spacing:.08em;text-transform:uppercase;color:var(--text-leise);display:block;
  margin-bottom:6px}
.netz-reihe-pro{color:var(--pro-text)} .netz-reihe-contra{color:var(--contra-text)}
.netz-zellen{display:grid;grid-template-columns:repeat(auto-fit,minmax(112px,1fr));gap:10px}
.netz-zelle{display:flex;flex-direction:column;align-items:center;gap:2px;text-decoration:none;
  color:inherit;border:1px solid transparent;border-radius:10px;padding:4px}
a.netz-zelle:hover{border-color:var(--linie);background:var(--flaeche)}
.netz-zelle-legende{padding:0}
.mininetz{width:100%;max-width:130px;height:auto;overflow:visible}
/* Das Legendennetz traegt Achsenbeschriftungen, die ueber den Rahmen der
   Zeichnung hinausragen. Es steht darum in einer eigenen, ueber die ganze
   Reihe gehenden Zelle und wird darin mittig gesetzt, statt in der ersten
   Rasterspalte zu kleben, wo die linke Beschriftung aus dem Kasten faellt. */
.netz-zelle-legende{grid-column:1 / -1;align-items:center;padding:6px 0 0}
.netz-zelle-legende .mininetz{max-width:230px}
.netz-zelle-zahl{font-family:Archivo,sans-serif;font-size:11.5px;color:var(--text-leise);
  font-variant-numeric:tabular-nums}
.netz-mini-titel{font-family:Archivo,sans-serif;font-size:10px;font-weight:600;fill:var(--text-leise)}
.netz-legende{fill:var(--linie);fill-opacity:.35;stroke:var(--linie);stroke-width:1}
.netz-legende-punkt{fill:var(--linie)}
.netz-pro{fill:var(--pro);fill-opacity:.20;stroke:var(--pro);stroke-width:2}
.netz-contra{fill:var(--contra);fill-opacity:.20;stroke:var(--contra);stroke-width:2}
.netz-pro-punkt{fill:var(--pro)} .netz-contra-punkt{fill:var(--contra)}
.netz-titel{font-family:Archivo,sans-serif;font-size:13px;font-weight:600;fill:var(--text)}
.netz-wert{font-family:Archivo,sans-serif;font-size:12px;fill:var(--text-leise);
  font-variant-numeric:tabular-nums}
.legende{display:flex;gap:18px;margin:0 0 14px;font-size:14px;flex-wrap:wrap}
.legende span{display:inline-flex;align-items:center;gap:7px}
.punkt{width:12px;height:12px;border-radius:3px;display:inline-block}
.punkt-pro{background:var(--pro)} .punkt-contra{background:var(--contra)}
.achsenliste{margin:0;padding:0;list-style:none;border-top:1px solid var(--linie)}
.achsenliste li{padding:11px 0;border-bottom:1px solid var(--linie);font-size:14.5px}
.achsenliste b{font-family:Archivo,sans-serif}
.achsenliste span{color:var(--text-leise);display:block;font-size:13.5px}
.lesehilfe{margin:16px 0 0;padding:14px 16px;border-left:3px solid var(--linie);
  font-size:14.5px;color:var(--text-leise)}
.lesehilfe b{color:var(--text)}

.spalten{display:grid;grid-template-columns:1fr 1fr;gap:22px;align-items:start}
.spaltenkopf{font-family:Archivo,sans-serif;font-weight:600;font-size:15px;letter-spacing:.05em;
  text-transform:uppercase;padding:0 0 10px;border-bottom:2px solid currentColor;margin-bottom:16px}
.spaltenkopf em{display:block;font-style:normal;text-transform:none;letter-spacing:0;
  font-size:13px;font-weight:400;color:var(--text-leise);margin-top:3px}
.kopf-pro{color:var(--pro-text)} .kopf-contra{color:var(--contra-text)}
.stapel{display:flex;flex-direction:column;gap:20px}

.karte{background:var(--karte);border:1px solid var(--linie);border-radius:14px;padding:20px 20px 16px;
  box-shadow:0 1px 2px rgba(16,24,40,.04)}
.karte-offen{border-style:dashed}
.karte-wertung{background:var(--flaeche)}
.karte-kopf{display:flex;justify-content:space-between;gap:12px;align-items:baseline;flex-wrap:wrap;
  margin-bottom:12px}
.marke{font-family:Archivo,sans-serif;font-weight:600;font-size:11.5px;letter-spacing:.08em;
  text-transform:uppercase;padding:3px 9px;border-radius:999px;border:1px solid currentColor}
.marke-pro{color:var(--pro-text)} .marke-contra{color:var(--contra-text)}
.typ{font-size:12.5px;color:var(--text-leise);text-align:right}
.typ em{display:block;font-style:normal;opacity:.85}
.karte-note{display:flex;justify-content:space-between;align-items:baseline;gap:10px;
  margin:0 0 10px;padding-bottom:9px;border-bottom:1px solid var(--linie)}
.karte-punkte{font-family:Archivo,sans-serif;font-weight:600;font-size:15px;
  font-variant-numeric:tabular-nums}
.karte-punkte-na{font-weight:400;font-size:13px;color:var(--text-leise);font-style:italic}
.karte-zurueck{font-size:12.5px;color:var(--text-leise);text-decoration:none;white-space:nowrap}
.karte-zurueck:hover{text-decoration:underline}
.karte:target{outline:2px solid var(--text-leise);outline-offset:3px}
html{scroll-behavior:smooth}
:target{scroll-margin-top:18px}
.aussage{margin:0 0 8px;font-family:Archivo,sans-serif;font-weight:500;font-size:18px;
  line-height:1.36;letter-spacing:-.005em;border:0;padding:0}
.traeger{margin:0 0 4px;font-size:14px;color:var(--text-leise)}
.fundstelle{margin:0 0 14px;font-size:13.5px;color:var(--text-leise)}
.fundstelle a{color:var(--text)}
.fundstelle-offen{background:var(--flaeche);border-radius:8px;padding:9px 11px}
.wertung-hinweis{font-size:14px;background:var(--grund);border:1px solid var(--linie);
  border-radius:8px;padding:10px 12px;margin:0 0 14px;color:var(--text-leise)}

.balken-block{margin:0 0 16px;border-top:1px solid var(--linie);padding-top:12px}
.balken{display:grid;grid-template-columns:112px 1fr 20px;align-items:center;gap:10px;padding:3px 0}
.balken-name{font-size:12.5px;color:var(--text-leise)}
.balken-spur{display:flex;gap:3px}
.balken-spur-na{font-size:11.5px;color:var(--text-leise);opacity:.7;font-style:italic}
.seg{height:9px;flex:1;border-radius:2px}
.seg-voll{background:var(--seg-voll)} .seg-leer{background:var(--seg-leer)}
.balken-zahl{font-family:Archivo,sans-serif;font-size:13px;font-variant-numeric:tabular-nums;
  text-align:right;color:var(--text-leise)}

.praezis{display:flex;flex-direction:column;gap:8px;margin:0 0 6px}
.praezis-teil{border-left:3px solid var(--linie);padding-left:13px}
.praezis-zu{border-left-color:var(--seg-voll)}
.praezis h4{margin:0 0 3px;font-size:12px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--text-leise)}
.praezis p{margin:0 0 8px;font-size:15px}
.praezis p:last-child{margin-bottom:0}

/* Aufklappbare Präzisierung */
.pk{border-radius:10px;border:1px solid var(--linie);background:var(--grund);overflow:hidden}
.pk summary{list-style:none;cursor:pointer;padding:10px 13px 10px 15px;position:relative;
  display:flex;flex-direction:column;gap:2px;font-size:inherit;color:inherit}
.pk summary::-webkit-details-marker{display:none}
.pk summary::after{content:"";position:absolute;right:13px;top:15px;width:7px;height:7px;
  border-right:2px solid var(--text-leise);border-bottom:2px solid var(--text-leise);
  transform:rotate(45deg);transition:transform .15s}
.pk[open] summary::after{transform:rotate(-135deg);top:18px}
.pk summary:hover{background:var(--flaeche)}
.pk-titel{font-family:Archivo,sans-serif;font-size:12px;letter-spacing:.08em;
  text-transform:uppercase;color:var(--text-leise);padding-right:22px}
.pk-anriss{font-size:14px;color:var(--text-leise);padding-right:22px;line-height:1.4}
.pk[open] .pk-anriss{display:none}
.pk-inhalt{padding:0 15px 13px}
.pk-inhalt p{margin:0 0 9px;font-size:15px}
.pk-inhalt p:last-child{margin:0}
.rohling{border:1px dashed var(--linie);border-radius:14px;padding:22px 24px;margin:0 0 30px;color:var(--text-leise)}
.rohling h2{margin:0 0 8px;font-size:20px;color:var(--text)} .rohling p{margin:0}
.folge ol{margin:0;padding-left:20px} .folge p{margin:0 0 8px} .folge p:last-child{margin:0}
.km-einleitung{margin:0 0 16px;font-size:15px} .km-einleitung ol{margin:0;padding-left:22px} .km-einleitung li{margin:0 0 5px}
.pk-inhalt ol,.praezis-teil ol,.zahlhinweis ol{margin:0 0 9px;padding-left:22px;font-size:15px}
.pk-inhalt ol:last-child,.praezis-teil ol:last-child,.zahlhinweis ol:last-child{margin-bottom:0}
.pk-inhalt ol li,.praezis-teil ol li,.zahlhinweis ol li{margin:0 0 6px;padding-left:4px}
.pk-inhalt ol li::marker,.praezis-teil ol li::marker{font-family:Archivo,sans-serif;font-weight:600;color:var(--text-leise)}
.praezis-teil p{margin:0 0 9px} .praezis-teil p:last-child{margin:0}

/* Klappkästen unterhalb der Wertung */
.karte-kaesten{display:flex;flex-direction:column;gap:7px;margin-top:10px}
.pk-neben,.pk-eigen{background:var(--karte)}
.pk-neben .pk-titel,.pk-eigen .pk-titel{display:flex;align-items:center;gap:2px;flex-wrap:wrap}
.pk-eigen{border-left:3px solid var(--text)}
.pk-inhalt .agrafik{margin:4px 0 0}
.pk-inhalt .agrafik + .agrafik{margin-top:12px}
.pk-inhalt .zahlhinweis{margin:10px 0 0}
.kf-liste,.beleg-liste{margin:0;padding:0;list-style:none}

/* «Was zutrifft» ruhig, «Was fehlt» mit Nachdruck */
.pk-zu{border-left:3px solid var(--seg-leer)}
.pk-fehlt{border-left:4px solid var(--text);background:var(--flaeche)}
.pk-fehlt .pk-titel{color:var(--text);font-weight:700}
.pk-fehlt .pk-anriss{color:var(--text)}
.pk-fehlt summary::after{border-color:var(--text)}
.pk-fehlt summary:hover{background:var(--grund)}

details{font-size:14px}
details summary{cursor:pointer;color:var(--text-leise);padding:7px 0;font-size:13.5px}
.schema{font-family:Archivo,sans-serif;border:1px solid var(--linie);border-radius:999px;
  padding:1px 8px;font-size:11.5px;margin-left:6px;color:var(--text-leise)}
.fragen ul,.belege ul{margin:6px 0 10px;padding:0;list-style:none}
.kf{display:grid;grid-template-columns:1fr auto;gap:2px 12px;padding:8px 0;
  border-top:1px solid var(--linie)}
.kf-frage{font-weight:500}
.kf-status{font-size:11.5px;font-family:Archivo,sans-serif;color:var(--text-leise);
  border:1px solid var(--linie);border-radius:999px;padding:1px 8px;white-space:nowrap;height:fit-content}
.kf-nein{border-style:solid;border-width:1.5px}
.kf-kommentar{grid-column:1/-1;color:var(--text-leise);font-size:13.5px}
.belege li{padding:6px 0;border-top:1px solid var(--linie);font-size:13.5px}
.quellenart{font-size:11.5px;color:var(--text-leise);border:1px solid var(--linie);
  border-radius:999px;padding:0 7px;margin-left:4px;white-space:nowrap}

.zahlhinweis{margin:0 0 10px;padding:9px 12px;border-radius:8px;background:var(--flaeche);
  font-size:12.5px;color:var(--text-leise);border-left:3px solid var(--linie)}

/* Abschnitte als Klappblöcke */
.ab{margin-top:34px}
.ab-klapp{border-top:1px solid var(--linie);padding-top:4px}
.ab-klapp > summary{list-style:none;cursor:pointer;padding:12px 34px 12px 0;position:relative}
.ab-klapp > summary::-webkit-details-marker{display:none}
.ab-klapp > summary::after{content:"";position:absolute;right:6px;top:24px;width:9px;height:9px;
  border-right:2px solid var(--text-leise);border-bottom:2px solid var(--text-leise);
  transform:rotate(45deg);transition:transform .15s}
.ab-klapp[open] > summary::after{transform:rotate(-135deg);top:28px}
.ab-klapp > summary h2{display:inline;font-size:24px;letter-spacing:-.01em;margin:0}
.ab-hinweis{display:block;color:var(--text-leise);margin-top:5px;font-size:15.5px}
.ab-inhalt{padding-top:8px}

/* Inhaltsverzeichnis */
.iv{margin:26px 0 0;border:1px solid var(--linie);border-radius:14px;background:var(--karte);
  padding:16px 20px}
.iv h2{font-size:12px;letter-spacing:.09em;text-transform:uppercase;color:var(--text-leise);
  margin:0 0 10px}
.iv ol{margin:0;padding:0;list-style:none;display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));
  gap:2px 20px;counter-reset:iv}
.iv li{counter-increment:iv}
.iv a{display:flex;gap:9px;padding:6px 0;text-decoration:none;font-size:14.5px;
  border-bottom:1px solid transparent}
.iv a:hover{border-bottom-color:var(--linie)}
.iv a::before{content:counter(iv);font-family:Archivo,sans-serif;font-size:11.5px;
  color:var(--text-leise);min-width:14px;padding-top:2px}
.iv-schalter{margin-top:12px;display:flex;gap:8px}
.iv-schalter button{font-family:Archivo,sans-serif;font-size:12.5px;padding:5px 12px;
  border-radius:999px;border:1px solid var(--linie);background:none;color:var(--text-leise);
  cursor:pointer}
.iv-schalter button:hover{background:var(--flaeche);color:var(--text)}

/* Grafik vergrössern */
.zoombar{cursor:zoom-in}
.lupe{position:fixed;inset:0;z-index:9000;background:rgba(10,14,20,.88);display:flex;
  flex-direction:column;align-items:center;justify-content:center;padding:16px;gap:10px}
.lupe[hidden]{display:none}
.lupe img{max-width:100%;max-height:calc(100vh - 96px);background:#fff;border-radius:8px;
  object-fit:contain}
.lupe-kopf{display:flex;align-items:center;gap:14px;color:#fff;font-size:14px;
  max-width:100%;flex-wrap:wrap;justify-content:center}
.lupe-zu{border:1px solid rgba(255,255,255,.5);background:none;color:#fff;border-radius:999px;
  padding:5px 14px;font-family:Archivo,sans-serif;font-size:13px;cursor:pointer}
.lupe-zu:hover{background:rgba(255,255,255,.15)}

/* Herkunftsmarken */
.hk{display:inline-block;font-family:Archivo,sans-serif;font-size:10.5px;font-weight:600;
  letter-spacing:.07em;text-transform:uppercase;padding:2px 8px;border-radius:4px;
  margin:0 6px 4px 0;vertical-align:middle;white-space:nowrap}
.hk-eigen{background:var(--text);color:var(--grund)}
.hk-amtlich{border:1px solid var(--text-leise);color:var(--text-leise)}
.hk-komitee{border:1px dashed var(--text-leise);color:var(--text-leise)}
.hk-extern{border:1px solid var(--linie);color:var(--text-leise)}
.hk-legende{margin:18px 0 0;padding:14px 16px;border:1px solid var(--linie);
  border-radius:12px;background:var(--karte);font-size:13px;color:var(--text-leise)}
.hk-legende b{display:block;color:var(--text);font-family:Archivo,sans-serif;font-size:11px;
  letter-spacing:.08em;text-transform:uppercase;margin-bottom:10px}
/* Zwei Spalten, damit die drei Marken links an derselben Kante stehen und die
   Erklaerungen daneben ebenfalls fluchten. Eine Flex-Zeile ergab drei
   verschieden weit eingerueckte Zeilen. */
.hk-raster{display:grid;grid-template-columns:max-content 1fr;gap:7px 12px;align-items:baseline}
.hk-raster span.hk{margin:0;justify-self:start}

/* Grafik in der Argumentkarte */
.agrafik{margin:14px 0 6px;padding:0;border:1px solid var(--linie);border-radius:12px;overflow:hidden;
  background:#F7F6F2}
.agrafik img{display:block;width:100%;height:auto}
.agrafik figcaption{padding:9px 12px;font-size:12.5px;color:var(--text-leise);background:var(--karte);
  border-top:1px solid var(--linie)}
.agrafik-eigen{border-color:var(--text)}
.agrafik figcaption b{color:var(--text);font-family:Archivo,sans-serif;display:block;font-size:13px}
.agrafik-quelle{display:block;margin-top:3px;font-size:11.5px;opacity:.85}

/* Textkritik */
.tk-liste{display:flex;flex-direction:column;gap:18px}
.tk-karte{border:1px solid var(--linie);border-radius:14px;padding:20px;background:var(--karte)}
.tk-kopf{display:flex;gap:13px;align-items:flex-start;margin-bottom:12px}
.tk-nr{font-family:Archivo,sans-serif;font-weight:600;font-size:13px;border:1px solid var(--linie);
  border-radius:999px;width:26px;height:26px;display:flex;align-items:center;justify-content:center;
  color:var(--text-leise);flex:none}
.tk-karte h3{margin:0;font-size:18px;letter-spacing:-.005em}
.tk-wo{font-size:12.5px;color:var(--text-leise)}
.tk-wortlaut{margin:0 0 14px;padding:11px 14px;background:var(--flaeche);border-radius:10px;
  border-left:3px solid var(--linie);font-size:15px;font-style:italic}
.tk-tabelle{margin:14px 0}
.tk-tab-titel{margin:0 0 7px;font-family:Archivo,sans-serif;font-size:12.5px;font-weight:600;
  letter-spacing:.05em;text-transform:uppercase;color:var(--text-leise)}
.tk-scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
.tk-scroll table{border-collapse:collapse;width:100%;font-size:13.5px;min-width:460px}
.tk-scroll th{text-align:left;font-family:Archivo,sans-serif;font-size:11.5px;letter-spacing:.05em;
  text-transform:uppercase;color:var(--text-leise);font-weight:600;padding:7px 10px 7px 0;
  border-bottom:1px solid var(--linie);white-space:nowrap}
.tk-scroll td{padding:7px 10px 7px 0;border-bottom:1px solid var(--linie);
  font-variant-numeric:tabular-nums}
.tk-scroll td.z{text-align:right;padding-right:14px}
.tk-scroll td.z-leise{color:var(--text-leise);font-size:12.5px}
.tk-tab-fuss{margin:8px 0 0;font-size:12.5px;color:var(--text-leise)}
.tk-quelle{margin:10px 0 0;font-size:12px;color:var(--text-leise);padding-top:9px;
  border-top:1px solid var(--linie)}

/* Karte */
.km-block{border:1px solid var(--linie);border-radius:16px;padding:18px;background:var(--karte)}
.km-knoepfe{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px}
.km-knopf{font-family:Archivo,sans-serif;font-size:12.5px;padding:5px 11px;border-radius:999px;
  border:1px solid var(--linie);background:none;color:var(--text-leise);cursor:pointer}
.km-knopf:hover{background:var(--flaeche);color:var(--text)}
.km-aktiv{background:var(--text);color:var(--grund);border-color:var(--text)}
.km-buehne{background:#FCFCFA;border:1px solid var(--linie);border-radius:12px;overflow:hidden}
.km-buehne img{display:block;width:100%;height:auto}
.km-zahlen{display:flex;flex-wrap:wrap;gap:10px;margin-top:14px}
.km-kachel{border:1px solid var(--linie);border-radius:10px;padding:9px 13px;min-width:118px}
.km-kachel span{display:block;font-size:11.5px;letter-spacing:.05em;text-transform:uppercase;
  color:var(--text-leise);font-family:Archivo,sans-serif}
.km-kachel b{font-family:Archivo,sans-serif;font-size:19px;font-variant-numeric:tabular-nums}
.km-kachel i{font-style:normal;font-size:12.5px;color:var(--text-leise);margin-left:5px}
.km-summe td{font-family:Archivo,sans-serif;font-weight:600;border-top:2px solid var(--linie)}
.km-tabelle{margin-top:16px}

/* Viewer */
.vw-block{display:grid;grid-template-columns:236px 1fr;gap:16px;align-items:stretch;border:1px solid var(--linie);
  border-radius:16px;padding:16px;background:var(--karte)}
.vw-steuer{display:flex;flex-direction:column;gap:16px}
.vw-gruppe h4{margin:0 0 7px;font-size:11px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--text-leise)}
.vw-opt{display:flex;align-items:flex-start;gap:8px;padding:3px 0;font-size:13.5px;cursor:pointer}
.vw-opt input{margin:3px 0 0;flex:none;accent-color:var(--text)}
.vw-opt span{display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.vw-opt em{display:block;width:100%;font-style:normal;font-size:11.5px;color:var(--text-leise)}
.vw-linie{display:inline-block;width:18px;height:0;flex:none}
.vw-l100{border-top:5px solid var(--leg-eigen)}
.vw-l300{border-top:3px dashed var(--leg-eigen)}
.vw-lbus{border-top:3px dotted var(--leg-osm)}
.vw-punkt{display:inline-block;width:9px;height:9px;border-radius:50%;background:#fff;
  border:1.5px solid #1F2833;flex:none}
.vw-regler{margin-top:12px;padding-top:12px;border-top:1px solid var(--linie);
  font-size:12.5px;color:var(--text-leise)}
.vw-regler label{display:block;margin-bottom:5px}
.vw-regler input[type=range]{width:calc(100% - 46px);accent-color:var(--text);vertical-align:middle}
.vw-regler output{display:inline-block;width:42px;text-align:right;
  font-family:Archivo,sans-serif;font-variant-numeric:tabular-nums;color:var(--text)}
/* Legende der amtlichen Rasterebenen. Das Bild kommt vom Amt, damit die
   Farbskala und ihre Bedeutung aus derselben Hand stammen wie die Kacheln. */
.vw-amtleg{position:absolute;right:10px;top:10px;z-index:500;max-width:min(320px,46%);
  background:var(--karte);border:1px solid var(--linie);border-radius:10px;
  box-shadow:0 2px 12px rgba(16,24,40,.16)}
.vw-amtleg[hidden]{display:none}
.vw-amtleg > summary{cursor:pointer;list-style:none;padding:8px 11px;
  font-family:Archivo,sans-serif;font-size:10.5px;font-weight:600;letter-spacing:.07em;
  text-transform:uppercase;color:var(--text-leise);display:flex;justify-content:space-between;
  gap:10px;align-items:center}
.vw-amtleg > summary::-webkit-details-marker{display:none}
.vw-amtleg-pfeil{flex:none;font-size:10px;transition:transform .12s}
.vw-amtleg[open] .vw-amtleg-pfeil{transform:rotate(180deg)}
/* Die amtlichen Legendenbilder sind gross und viersprachig. Eingeklappt
   nimmt der Kasten eine Zeile, aufgeklappt hoechstens die halbe Kartenhoehe. */
.vw-amtleg-inhalt{max-height:min(52vh,calc(100% - 60px));overflow:auto;padding:0 11px 10px}
.vw-amtleg h5{margin:0 0 5px;font-family:Archivo,sans-serif;font-size:10.5px;font-weight:600;
  letter-spacing:.07em;text-transform:uppercase;color:var(--text-leise)}
.vw-amtleg h5 + img{margin-bottom:9px}
.vw-amtleg img{display:block;max-width:100%;background:#fff;border-radius:4px}
.vw-gruppe select{width:100%;padding:6px 8px;font:inherit;font-size:13.5px;border-radius:8px;
  border:1px solid var(--linie);background:var(--grund);color:var(--text)}
.vw-buehne{position:relative;display:flex;min-height:560px}
.vw-karte{flex:1;min-height:560px;border-radius:12px;overflow:hidden;border:1px solid var(--linie);
  background:var(--flaeche)}
.vw-legende{position:absolute;right:10px;bottom:26px;background:var(--karte);
  border:1px solid var(--linie);border-radius:10px;padding:10px 13px;z-index:500;
  box-shadow:0 2px 8px rgba(16,24,40,.12);font-size:12.5px;color:var(--text-leise)}
.vw-legende[hidden]{display:none}
.vw-legende p{margin:0 0 5px;display:flex;align-items:center;gap:8px}
.vw-legende p:last-child{margin:0}
.vw-legtitel{font-family:Archivo,sans-serif;font-size:11px;letter-spacing:.07em;
  text-transform:uppercase;color:var(--text);font-weight:600}
.vw-legfuss{font-size:11.5px;font-style:italic;margin-top:6px !important}
.vw-lueber{border-top:5px solid var(--leg-kanton);width:22px}
.vw-lreg{border-top:3px solid var(--leg-kanton);width:22px;opacity:.6}
.vw-lstr{border-top:4px solid var(--leg-kanton)}
.vw-geltung{margin:0 0 14px;border:1px solid var(--linie);border-radius:14px;padding:14px 16px;
  background:var(--karte)}
.vw-gknoepfe{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.vw-glabel{font-family:Archivo,sans-serif;font-size:11px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--text-leise);margin-right:4px}
.vw-gknopf{font-family:Archivo,sans-serif;font-size:13.5px;font-weight:600;padding:6px 14px;
  border-radius:999px;border:1px solid var(--linie);background:none;color:var(--text-leise);
  cursor:pointer}
.vw-gknopf:hover{background:var(--flaeche);color:var(--text)}
.vw-gaktiv{background:var(--text);color:var(--grund);border-color:var(--text)}
.vw-gaus{font-weight:400;font-size:12.5px}
.vw-gtext{margin-top:12px;font-size:14.5px}
.vw-gtext[hidden]{display:none}
.vw-gtext p{margin:0 0 7px} .vw-gtext p:last-child{margin:0;color:var(--text-leise)}
.vw-gkrit{padding:9px 12px;background:var(--flaeche);border-radius:8px;
  border-left:3px solid var(--seg-voll)}
.leaflet-container{font:inherit;background:var(--flaeche)}
.vw-pop{font-size:13px;line-height:1.45}
.vw-pop b{font-family:Archivo,sans-serif}
@media (max-width:900px){
  .vw-block{grid-template-columns:1fr}
  .vw-karte{height:420px}
  .vw-steuer{display:grid;grid-template-columns:1fr 1fr;gap:12px}
}

/* Kantonsrat */
.kr-raster{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px}
.kr-karte{border:1px solid var(--linie);border-radius:14px;padding:16px 18px;
  background:var(--karte);display:flex;flex-direction:column}
.kr-karte .kr-detail{flex:1}
.kr-kopf{display:flex;justify-content:space-between;align-items:baseline;gap:10px;
  font-size:12.5px;color:var(--text-leise)}
.kr-nr{font-family:Archivo,sans-serif;letter-spacing:.06em;text-transform:uppercase;font-size:11.5px}
.kr-ergebnis{font-family:Archivo,sans-serif;font-weight:600;font-size:15px;color:var(--text);
  font-variant-numeric:tabular-nums}
.kr-karte h4{margin:6px 0 3px;font-size:15.5px}
.kr-detail{margin:0 0 10px;font-size:14px;color:var(--text-leise)}
.kr-umkehr{margin:0 0 10px;font-size:13px;background:var(--flaeche);border-radius:8px;
  padding:8px 10px;color:var(--text-leise)}
.kr-gesamt,.kr-fbalken{display:flex;height:10px;border-radius:3px;overflow:hidden;
  background:var(--seg-leer)}
.kr-ja{background:var(--pro)} .kr-nein{background:var(--contra)} .kr-rest{background:transparent}
.kr-neben{margin:7px 0 0;font-size:12.5px;color:var(--text-leise)}
.kr-frakt-liste{display:flex;flex-direction:column;gap:6px;padding:4px 0 8px}
.kr-frakt{display:grid;grid-template-columns:1fr 90px 44px;align-items:center;gap:8px;font-size:12.5px}
.kr-fname{color:var(--text-leise);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.kr-fbalken{height:8px}
.kr-fzahl{text-align:right;font-family:Archivo,sans-serif;font-variant-numeric:tabular-nums;
  color:var(--text-leise)}

.fuss{margin-top:64px;border-top:1px solid var(--linie);padding-top:24px;font-size:14px;
  color:var(--text-leise)}
.fuss h2{font-size:17px;color:var(--text);margin:22px 0 8px}
.fuss h2:first-child{margin-top:0}
.fuss ol,.fuss ul{padding-left:20px} .fuss li{margin:5px 0}

.schalter{position:fixed;right:18px;bottom:18px;border:1px solid var(--linie);background:var(--karte);
  color:var(--text);border-radius:999px;padding:9px 16px;font-size:13.5px;cursor:pointer;
  font-family:Archivo,sans-serif;box-shadow:0 2px 10px rgba(16,24,40,.10)}

@media (max-width:900px){
  .netz-block,.spalten,.folgen{grid-template-columns:1fr}
  .spalten .spalte + .spalte{margin-top:14px}
  .ue-zeile{grid-template-columns:1fr 78px;gap:6px 12px;padding:12px 8px}
  .ue-marke{grid-column:1} .ue-zahl,.ue-na{grid-column:2;grid-row:1}
  .ue-text{grid-column:1/-1} .ue-typ{grid-column:1} .ue-spur{grid-column:2;align-self:center}
  .ue-spur-na{grid-column:2;grid-row:1;white-space:normal;font-size:11px;line-height:1.3}
  .vw-block{grid-template-columns:1fr}
  .vw-buehne{min-height:420px} .vw-karte{min-height:420px}
}
"""

JS = """
const w=document.documentElement, k=document.getElementById('schalter');
const g=localStorage.getItem('abstimmungsspiegel-theme'); if(g) w.setAttribute('data-theme',g);
k.addEventListener('click',()=>{
  const d = w.getAttribute('data-theme')==='dark'
    || (!w.getAttribute('data-theme') && matchMedia('(prefers-color-scheme: dark)').matches);
  const n = d?'light':'dark'; w.setAttribute('data-theme',n);
  localStorage.setItem('abstimmungsspiegel-theme',n);
});

// Grafiken vergrössern
const lupe=document.getElementById('lupe'), lupeBild=document.getElementById('lupe-bild'),
      lupeTitel=document.getElementById('lupe-titel');
function zeigeLupe(img){
  lupeBild.src=img.currentSrc||img.src;
  lupeBild.alt=img.alt||'';
  lupeTitel.textContent=img.dataset.titel||img.alt||'';
  lupe.hidden=false; document.body.style.overflow='hidden';
  document.getElementById('lupe-zu').focus();
}
function schliesseLupe(){ lupe.hidden=true; lupeBild.src=''; document.body.style.overflow=''; }
document.addEventListener('click',ev=>{
  const img=ev.target.closest('img.zoombar');
  if(img){ ev.preventDefault(); zeigeLupe(img); return; }
  if(ev.target.closest('#lupe')) schliesseLupe();
});
document.addEventListener('keydown',ev=>{
  if(ev.key==='Escape' && !lupe.hidden) schliesseLupe();
  const img=ev.target.closest && ev.target.closest('img.zoombar');
  if(img && (ev.key==='Enter'||ev.key===' ')){ ev.preventDefault(); zeigeLupe(img); }
});

// Inhaltsverzeichnis: alles auf oder zu
const klappen=()=>[...document.querySelectorAll('details.ab-klapp')];
const auf=document.getElementById('iv-auf'), zu=document.getElementById('iv-zu');
if(auf) auf.addEventListener('click',()=>klappen().forEach(d=>d.open=true));
if(zu)  zu.addEventListener('click',()=>klappen().forEach(d=>d.open=false));
// Sprungziel in einem zugeklappten Abschnitt vorher aufklappen
function oeffneZiel(){
  const id=location.hash.slice(1); if(!id) return;
  const el=document.getElementById(id); if(!el) return;
  let p=el.closest('details'); 
  while(p){ p.open=true; p=p.parentElement && p.parentElement.closest('details'); }
  setTimeout(()=>el.scrollIntoView({behavior:'smooth',block:'start'}),40);
}
window.addEventListener('hashchange',oeffneZiel);
document.addEventListener('click',ev=>{
  const a=ev.target.closest('a[href^="#"]'); if(!a) return;
  const el=document.getElementById(a.getAttribute('href').slice(1)); if(!el) return;
  let p=el.closest('details');
  while(p){ p.open=true; p=p.parentElement && p.parentElement.closest('details'); }
});

// Kartenviewer
const vwEl=document.getElementById('vw-geo');
if(vwEl && window.L){
  const geo=JSON.parse(vwEl.textContent);
  const karte=L.map('vw-karte',{scrollWheelZoom:false}).setView([47.7234,8.6636],11);
  window.vwKarte=karte;   // Zugriff fuer die Layoutpruefung
  karte.on('click',()=>karte.scrollWheelZoom.enable());
  karte.on('mouseout',()=>karte.scrollWheelZoom.disable());
  L.control.scale({imperial:false}).addTo(karte);

  const wmts=(id,ts,fmt)=>L.tileLayer(
    `https://wmts.geo.admin.ch/1.0.0/${id}/default/${ts}/3857/{z}/{x}/{y}.${fmt}`,
    {maxZoom:19, attribution:'&copy; <a href="https://www.geo.admin.ch/">geo.admin.ch</a>'});
  const basen={
    'osm': L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',
      {maxZoom:19, attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'}),
    'ch.swisstopo.pixelkarte-grau': wmts('ch.swisstopo.pixelkarte-grau','current','jpeg'),
    'ch.swisstopo.swisstlm3d-karte-grau': wmts('ch.swisstopo.swisstlm3d-karte-grau','current','png')
  };
  // Im dunklen Schema ist die OSM-Kachel ein hell leuchtendes Rechteck. Die
  // Graukarte von swisstopo ist ruhiger; die Wahl bleibt umschaltbar.
  const dunkel=()=>document.documentElement.getAttribute('data-theme')==='dark'
    || (!document.documentElement.getAttribute('data-theme')
        && window.matchMedia('(prefers-color-scheme: dark)').matches);
  const startBasis=dunkel()?'ch.swisstopo.swisstlm3d-karte-grau':'osm';
  let aktiveBasis=basen[startBasis].addTo(karte);
  const bAus=document.querySelector(`input[name="vw-base"][value="${startBasis}"]`);
  if(bAus) bAus.checked=true;
  document.querySelectorAll('input[name="vw-base"]').forEach(r=>r.addEventListener('change',()=>{
    karte.removeLayer(aktiveBasis); aktiveBasis=basen[r.value].addTo(karte); aktiveBasis.bringToBack();
  }));

  // Farbe aus den CSS-Variablen lesen, damit hell und dunkel dieselbe Quelle haben
  const farbe=n=>getComputedStyle(document.documentElement).getPropertyValue('--geo-'+n).trim();
  const stil=r=>r===100
    ? {color:farbe('eigen'),weight:5,opacity:.95}
    : {color:farbe('eigen'),weight:3,opacity:.9,dashArray:'7 5'};
  const mach=r=>L.geoJSON(geo,{filter:f=>f.properties.r===r, style:()=>stil(r),
    onEachFeature:(f,l)=>l.bindPopup(
      `<div class="vw-pop"><b>${f.properties.g}</b><br>betroffener Abschnitt innerhalb `+
      `${f.properties.r} m einer Schule, eines Kindergartens oder eines Heims</div>`)});
  const ebenen={100:mach(100).addTo(karte), 300:mach(300).addTo(karte)};
  ebenen[100].bringToFront();
  const bind=(id,r)=>document.getElementById(id).addEventListener('change',ev=>{
    if(ev.target.checked){ebenen[r].addTo(karte); if(r===100) ebenen[r].bringToFront();}
    else karte.removeLayer(ebenen[r]);});
  bind('vw-k100',100); bind('vw-k300',300);

  const vorn=()=>Object.values(ebenen).forEach(l=>karte.hasLayer(l)&&l.bringToFront());
  const amt={};
  const regler=document.getElementById('vw-deck');
  const reglerAus=document.getElementById('vw-deck-aus');
  const deckung=()=>regler?Number(regler.value)/100:0.55;

  // Legende: das Bild liegt beim Bund je Ebene bereit. Kommt keines, bleibt
  // der Kasten leer statt eine erfundene Skala zu zeigen.
  const legKasten=document.getElementById('vw-amtleg');
  const legInhalt=document.getElementById('vw-amtleg-inhalt');
  const legTitel=document.getElementById('vw-amtleg-titel');
  const legenden={};
  const legZeichnen=()=>{
    const eintraege=Object.entries(legenden);
    // Bei einer Ebene steht ihr Name schon in der Kopfzeile, dann keine
    // Zwischenueberschrift; bei mehreren braucht jedes Bild seine.
    const eine=eintraege.length===1;
    legInhalt.innerHTML=eintraege.map(([id,n])=>
      (eine?'':`<h5>${n}</h5>`)+`<img alt="Legende ${n}" loading="lazy"`+
      ` src="https://api3.geo.admin.ch/static/images/legends/${id}_de.png">`).join('');
    legTitel.textContent=eine
      ? 'Legende: '+eintraege[0][1]
      : `Amtliche Legenden (${eintraege.length})`;
    legKasten.hidden=eintraege.length===0;
  };
  document.querySelectorAll('.vw-wmts').forEach(c=>c.addEventListener('change',()=>{
    const id=c.dataset.id;
    const name=(c.parentElement.querySelector('span')?.firstChild?.textContent||id).trim();
    if(c.checked){
      amt[id]=wmts(id,c.dataset.ts,c.dataset.fmt);
      amt[id].setOpacity(deckung()); amt[id].addTo(karte);
      legenden[id]=name; vorn();
    } else if(amt[id]){
      karte.removeLayer(amt[id]); delete amt[id]; delete legenden[id];
    }
    legZeichnen();
  }));
  if(regler) regler.addEventListener('input',()=>{
    reglerAus.textContent=regler.value+'\u2009%';
    Object.values(amt).forEach(l=>l.setOpacity(deckung()));
    Object.values(kant).forEach(l=>l.setOpacity(deckung()));
  });

  // Kantonale WMS-Ebenen
  const shWms=id=>L.tileLayer.wms('https://wms.geo.sh.ch/wms',
    {layers:id, format:'image/png', transparent:true, version:'1.3.0', maxZoom:19,
     attribution:'&copy; <a href="https://agi.sh.ch/">Amt für Geoinformation Kanton Schaffhausen</a>'});
  const kant={};
  const schalte=(id,an)=>{
    if(an && !kant[id]){ kant[id]=shWms(id); kant[id].setOpacity(deckung());
      kant[id].addTo(karte); vorn(); }
    else if(!an && kant[id]){ karte.removeLayer(kant[id]); delete kant[id]; }
    const box=document.querySelector(`.vw-shwms[data-id="${id}"]`);
    if(box) box.checked=an;
  };
  document.querySelectorAll('.vw-shwms').forEach(c=>
    c.addEventListener('change',()=>schalte(c.dataset.id, c.checked)));

  // Verkehrsorientierte Kantonsstrassen aus dem Strassenrichtplan, als Vektoren
  let strassen=null;
  const sEl=document.getElementById('vw-strassen-daten');
  if(sEl){
    strassen=L.geoJSON(JSON.parse(sEl.textContent),{
      style:f=>f.properties.k==='ueberregional'
        ? {color:farbe('kanton'),weight:5,opacity:.9}
        : {color:farbe('kanton'),weight:3,opacity:.55},
      onEachFeature:(f,l)=>l.bindPopup('<div class="vw-pop"><b>'+
        (f.properties.k==='ueberregional'?'Überregionale':'Regionale')+
        ' Kantonsstrasse</b><br>verkehrsorientiert laut Strassenrichtplan</div>')});
  }
  const zeigeStrassen=an=>{
    if(!strassen) return;
    if(an){ strassen.addTo(karte); strassen.bringToBack(); if(aktiveBasis) aktiveBasis.bringToBack(); }
    else karte.removeLayer(strassen);
    const b=document.getElementById('vw-strassen'); if(b) b.checked=an;
    const lg=document.getElementById('vw-legende'); if(lg) lg.hidden=!an;
  };
  const sBox=document.getElementById('vw-strassen');
  if(sBox) sBox.addEventListener('change',()=>zeigeStrassen(sBox.checked));

  // Busnetz aus den OSM-Linienrelationen
  let busnetz=null;
  const bEl=document.getElementById('vw-bus-daten');
  if(bEl){
    busnetz=L.geoJSON(JSON.parse(bEl.textContent),
      {style:{color:farbe('osm'),weight:3,opacity:.9,dashArray:'2 5'}, interactive:false});
  }
  const zeigeBus=an=>{
    if(!busnetz) return;
    if(an) busnetz.addTo(karte); else karte.removeLayer(busnetz);
    const b=document.getElementById('vw-bus'); if(b) b.checked=an;
  };
  const bBox=document.getElementById('vw-bus');
  if(bBox) bBox.addEventListener('change',()=>zeigeBus(bBox.checked));

  // Bushaltestellen, eigene Punktebene aus den BAV-Daten
  let halte=null;
  const hEl=document.getElementById('vw-halte-daten');
  if(hEl){
    halte=L.geoJSON(JSON.parse(hEl.textContent),{
      pointToLayer:(f,ll)=>L.circleMarker(ll,{radius:4,color:farbe('osm'),weight:1.5,
        fillColor:'#FFFFFF',fillOpacity:1}),
      onEachFeature:(f,l)=>l.bindPopup(
        `<div class="vw-pop"><b>${f.properties.n}</b><br>Bushaltestelle, ${f.properties.tu}</div>`)});
  }
  const zeigeHalte=an=>{
    if(!halte) return;
    if(an){ halte.addTo(karte); halte.bringToFront(); } else karte.removeLayer(halte);
    const b=document.getElementById('vw-halte'); if(b) b.checked=an;
  };
  const hBox=document.getElementById('vw-halte');
  if(hBox) hBox.addEventListener('change',()=>zeigeHalte(hBox.checked));

  // Geltungsbereich der beiden Erlasstexte
  const gDaten=JSON.parse(document.getElementById('vw-geltung-daten').textContent);
  const gText=document.getElementById('vw-gtext');
  document.querySelectorAll('.vw-gknopf').forEach(b=>b.addEventListener('click',()=>{
    const k=b.dataset.key;
    document.querySelectorAll('.vw-gknopf').forEach(x=>x.classList.toggle('vw-gaktiv',x===b));
    Object.keys(kant).forEach(id=>schalte(id,false));
    zeigeHalte(false); zeigeBus(false); zeigeStrassen(false);
    if(!k){ gText.innerHTML=''; gText.hidden=true; return; }
    const g=gDaten[k];
    g.l.forEach(id=>schalte(id,true));
    if(g.s) zeigeStrassen(true);
    if(g.b) zeigeBus(true);
    if(g.h) zeigeHalte(true);
    gText.hidden=false;
    gText.innerHTML='<p class="vw-gkrit">Gilt für: '+g.k+'</p><p>'+g.t+'</p>';
  }));

  const alle=L.geoJSON(geo);
  document.getElementById('vw-sprung').addEventListener('change',ev=>{
    const g=ev.target.value;
    if(!g){ karte.fitBounds(alle.getBounds(),{padding:[20,20]}); return; }
    const t=L.geoJSON(geo,{filter:f=>f.properties.g===g});
    const b=t.getBounds();
    if(b.isValid()) karte.fitBounds(b,{padding:[30,30]});
  });
  karte.fitBounds(alle.getBounds(),{padding:[20,20]});
}

// Gemeindeauswahl der Karte
const kmEl=document.getElementById('km-daten');
if(kmEl){
  const daten=JSON.parse(kmEl.textContent);
  const bild=document.getElementById('km-bild'), zahlen=document.getElementById('km-zahlen');
  const komma=v=>String(v).replace('.',',');
  function zeige(i){
    const x=daten[i];
    bild.src='grafiken/gemeinden/karte_'+x.d+'.svg';
    bild.alt='Karte '+x.n+': betroffene Kantonsstrassen und Umkreise sensibler Nutzungen';
    zahlen.innerHTML=
      '<div class="km-kachel"><span>betroffen</span><b>'+komma(x.b)+'</b><i>km</i></div>'+
      '<div class="km-kachel"><span>bis 100 m</span><b>'+komma(x.k1)+'</b><i>km · '+x.p1+' %</i></div>'+
      '<div class="km-kachel"><span>bis 300 m</span><b>'+komma(x.k3)+'</b><i>km · '+x.p3+' %</i></div>'+
      '<div class="km-kachel"><span>bis 500 m</span><b>'+komma(x.k5)+'</b><i>km · '+x.p5+' %</i></div>'+
      '<div class="km-kachel"><span>Anlagen S/K/H/So</span><b>'+x.a+'</b></div>';
    document.querySelectorAll('.km-knopf').forEach(b=>
      b.classList.toggle('km-aktiv', +b.dataset.i===i));
  }
  document.querySelectorAll('.km-knopf').forEach(b=>
    b.addEventListener('click',()=>zeige(+b.dataset.i)));
  zeige(0);
}
"""


def mittelwerte(argumente, achsen, seite):
    """Mittelwert je Achse. Werturteile, Karten ohne Fundstelle und Achsen mit
    'nicht anwendbar' bleiben draussen."""
    passend = [a for a in argumente
               if a["seite"] == seite and a.get("stand") != "fundstelle_offen"
               and a.get("typ") != "wertung"]
    werte = {}
    for a in achsen:
        vals = [x["pruefung"][a["id"]] for x in passend
                if x.get("pruefung", {}).get(a["id"]) is not None]
        werte[a["id"]] = sum(vals) / len(vals) if vals else 0.0
    return werte, len(passend)


ROHLING = """
<section class="ab"><div class="rohling">
  <h2>Die Argumente folgen</h2>
  <p>Für diese Vorlage sind noch keine Aussagen erfasst. Sobald die Argumentarien beider Seiten
  vorliegen, stehen hier je Aussage der Wortlaut, die Fundstelle und die Prüfung des Belegs.</p>
</div></section>"""


def bauen() -> str:
    daten = json.loads(QUELLE.read_text(encoding="utf-8"))
    v, achsen, args = daten["vorlage"], daten["achsen"], daten.get("argumente") or []
    seiten_setzen(v)
    karte_daten = daten.get("karte") if (daten.get("karte") or {}).get("gemeinden") else None
    tk_daten = daten.get("textkritik") if (daten.get("textkritik") or {}).get("stellen") else None

    tag, monat, jahr = v["abstimmung"].split("-")[::-1]
    url = adresse()
    repo = quellcode_adresse()
    quellcode = (f' Vorlage, Daten und Skripte: <a href="{e(repo)}" target="_blank" '
                 f'rel="noopener">Quellcode auf GitHub</a>.' if repo else "")
    kr = kantonsrat_daten(v.get("kantonsrat_suche", ""))
    bild_daten = teilen.bild_daten(daten, achsen, args, kr, url, punkte, mittelwerte,
                                   SEITE_KOMITEE, SEITE_NAME, TYP_NAME)

    achsenliste = "".join(
        f'<li><b>{e(a["kurz"])}</b> {e(a["frage"])}'
        f'<span>0 = {e(a["null"])} · 4 = {e(a["voll"])}</span></li>' for a in achsen)

    quellen = "".join(
        f'<li><a href="{e(q["url"])}" target="_blank" rel="noopener">{e(q["titel"])}</a>'
        f' <span class="quellenart">{e(QUELLENART.get(q.get("art",""), q.get("art","")))}</span></li>'
        for q in v["quellen"])

    n_wertung = sum(1 for a in args if a.get("typ") == "wertung")
    aussagen_satz = (f" Von den {len(args)} Aussagen sind {n_wertung} Werturteile; sie stehen ohne "
                     f"Note und gehen nicht in die Netzgrafik ein." if args
                     else " Aussagen sind noch keine erfasst.")

    # Kontextabsaetze im Kopf. «doppelvorlage» und «rechtsrahmen» bleiben als
    # Kurzform erhalten; frei benannte Absaetze stehen unter «kontext».
    kontext_teile = []
    if v.get("doppelvorlage"):
        kontext_teile.append((v.get("doppelvorlage_titel", "Mehrere Fragen auf einem Zettel."), v["doppelvorlage"]))
    if v.get("rechtsrahmen"):
        kontext_teile.append(("Was der Kanton nicht allein entscheiden kann.", v["rechtsrahmen"]))
    for kx in v.get("kontext") or []:
        kontext_teile.append((kx.get("titel", ""), kx.get("text", "")))
    kontext = ('<div class="kontext">' + "".join(
        f"<p><b>{e(ti)}</b> {e(tx)}</p>" for ti, tx in kontext_teile) + "</div>") if kontext_teile else ""

    # Das Inhaltsverzeichnis fuehrt nur, was die Vorlage hat. Eine Vorlage
    # ohne raeumliche Wirkung hat keine Karte, eine ohne Ratsgeschaeft
    # keinen Ratsblock, und ein leerer Rohling hat nur Kopf und Methode.
    verzeichnis = [
        ("uebersicht", "Alle Argumente auf einen Blick", f"{len(args)} Aussagen mit Punktzahl"),
        ("belegqualitaet", "Wie gut sind die Argumente belegt?", "ein Netz je Aussage"),
        ("argumente", "Die Argumente im Einzelnen", "Wortlaut, Fundstelle, Prüfung"),
    ] if args else []
    if tk_daten:
        verzeichnis.append(("textkritik", "Was der Abstimmungstext offen lässt",
                            f"{len(tk_daten['stellen'])} unbestimmte Begriffe"))
    if karte_daten:
        verzeichnis.append(("karte", "Wo die Vorlage gilt", f"{len(karte_daten['gemeinden'])} Gemeinden"))
        if GEOJSON.exists():
            verzeichnis.append(("viewer", "Selber nachschauen", "Karte zum Bewegen"))
    if kr:
        n_kr = len(kr["abstimmungen"])
        verzeichnis.append(("kantonsrat", "Wie der Kantonsrat gestimmt hat",
                            f"{n_kr} namentliche Abstimmung" + ("en" if n_kr != 1 else "")))
    verzeichnis.append(("methode", "Methode und Quellen", "wie geprüft wird"))
    iv = "".join(
        f'<li><a href="#{e(k)}">{e(t)}</a></li>' for k, t, _ in verzeichnis)

    # Lesehilfe unter den Netzen, je Vorlage in vorlage.json «lesehilfe».
    lesehilfe = (f'<p class="lesehilfe"><b>Zur Lesart.</b> {e(daten["lesehilfe"])}</p>'
                 if daten.get("lesehilfe") else "")
    block_belegqualitaet = abschnitt("belegqualitaet", "Wie gut sind die Argumente belegt?",
  "Ein Netz je Aussage, alle im selben Massstab: fünf Achsen, je 0 bis 4 Punkte. Bewertet "
  "wird die einzelne Aussage, nicht die Seite; zwei Aussagen mit derselben Punktzahl können "
  "auf verschiedenen Achsen schwach sein. Gestrichelte Speichen heissen «diese Achse ist auf "
  "diese Aussage nicht anwendbar».", f"""
  <div class="netz-block">
    <div class="netz-multi">
      <div class="netz-reihe">
        <span class="netz-reihe-titel netz-reihe-pro">{e(SEITE_KOMITEE["pro"])}</span>
        <div class="netz-zellen">{''.join(
          f'<a class="netz-zelle" href="#arg-{e(a["id"])}">{mininetz(achsen, a["pruefung"], "pro")}'
          f'<span class="netz-zelle-zahl">{punkte(a, achsen)[0]} von {punkte(a, achsen)[1]}</span></a>'
          for a in args if a['seite'] == 'pro' and a.get('typ') != 'wertung')}</div>
      </div>
      <div class="netz-reihe">
        <span class="netz-reihe-titel netz-reihe-contra">{e(SEITE_KOMITEE["contra"])}</span>
        <div class="netz-zellen">{''.join(
          f'<a class="netz-zelle" href="#arg-{e(a["id"])}">{mininetz(achsen, a["pruefung"], "contra")}'
          f'<span class="netz-zelle-zahl">{punkte(a, achsen)[0]} von {punkte(a, achsen)[1]}</span></a>'
          for a in args if a['seite'] == 'contra' and a.get('typ') != 'wertung')}</div>
      </div>
      <div class="netz-reihe">
        <span class="netz-reihe-titel">So liegen die Achsen</span>
        <div class="netz-zellen"><span class="netz-zelle netz-zelle-legende">
          {mininetz(achsen, {a['id']: 4 for a in achsen}, 'legende', 190, True)}</span></div>
      </div>
    </div>
    <div><ul class="achsenliste">{achsenliste}</ul></div>
  </div>

  {lesehilfe}""")

    block_argumente = abschnitt("argumente", "Die Argumente im Einzelnen",
  "Je Aussage der Wortlaut, der Träger und die Fundstelle, danach was zutrifft und was "
  "fehlt.", f"""
  <div class="spalten">
    <div class="spalte">
      <div class="spaltenkopf kopf-pro">{e(SEITE_NAME["pro"])}<em>{e(SEITE_KOMITEE["pro"])} · {e(SEITE_EMPFEHLUNG["pro"])}</em></div>
      <div class="stapel">{''.join(karte(a, achsen) for a in args if a['seite'] == 'pro')}</div>
    </div>
    <div class="spalte">
      <div class="spaltenkopf kopf-contra">{e(SEITE_NAME["contra"])}<em>{e(SEITE_KOMITEE["contra"])} · {e(SEITE_EMPFEHLUNG["contra"])}</em></div>
      <div class="stapel">{''.join(karte(a, achsen) for a in args if a['seite'] == 'contra')}</div>
    </div>
  </div>""")

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Abstimmungsspiegel · {e(v['titel'])}</title>
{kopfzeilen(v, url)}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700&family=Public+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<style>{CSS}{teilen.CSS}</style>
</head>
<body>
<div class="wrap">

<header class="kopf">
  <div class="ober">
    <span class="marke-seite">Abstimmungsspiegel · {e(v['ebene'])}</span>
    <span class="termin">Abstimmung {tag}.{monat}.{jahr}</span>
  </div>
  <h1>{e(v['titel'])}</h1>
  <p class="untertitel">{e(v['untertitel'])}</p>
  <p class="lead">{e(v['worum_geht_es'])}</p>

  <div class="folgen">
    <div class="folge folge-ja"><h3>{e(v.get('ja_titel', 'Bei einem Ja'))}</h3>{absaetze(v.get('bei_ja', ''))}</div>
    <div class="folge folge-nein"><h3>{e(v.get('nein_titel', 'Bei einem Nein'))}</h3>{absaetze(v.get('bei_nein', ''))}</div>
  </div>

  {kontext}

  <p class="warn"><strong>Quellen und Methode.</strong>
  {e(daten.get('hinweis_quellen') or daten.get('hinweis_prototyp') or '')} Bewertet wird der Beleg
  einer Aussage, nicht die Aussage selbst.{aussagen_satz}</p>

  <div class="hk-legende"><b>Woher stammt was</b>
    <div class="hk-raster">
      {marke('komitee')}<span>steht so im Argumentarium oder auf der Website eines Komitees</span>
      {marke('amtlich')}<span>Erlasstext, Abstimmungsmagazin, Bundesgericht, Statistik von Bund oder Kanton</span>
      {marke('eigen')}<span>Auswertung aus diesem Projekt, mit offengelegter Rechnung</span>
    </div>
  </div>
  <nav class="iv" aria-label="Inhalt">
    <h2>Inhalt</h2>
    <ol>{iv}</ol>
    <div class="iv-schalter">
      <button id="iv-auf" type="button">alles aufklappen</button>
      <button id="iv-zu" type="button">alles zuklappen</button>
    </div>
  </nav>
</header>

{(uebersicht(args, achsen) + block_belegqualitaet + block_argumente) if args else ROHLING}

{textkritik_block(tk_daten)}

{karte_block(karte_daten)}

{viewer_block(karte_daten)}

{kantonsrat_block(kr, v.get('kantonsrat_hinweis', ''))}

<footer class="fuss" id="methode">
  <h2>Methode</h2>
  <ol>
    <li>Argumente werden aus denselben Quellenarten für beide Seiten gesammelt: Website des
      Komitees, amtliches Abstimmungsmagazin, Medienmitteilungen. Gleiche Anzahl je Seite.</li>
    <li>Jede Aussage wird als Tatsachenbehauptung, Prognose oder Werturteil eingestuft.
      Werturteile werden nicht bewertet.</li>
    <li>Geprüft wird der Beleg, nicht die Politik: Quellenlage, Zahlenfestigkeit,
      Ursachennachweis, Reichweite, Übertragbarkeit. Achsen, die auf eine Aussage nicht
      passen, bleiben leer statt null.</li>
    <li>Beide Komitees können sich jederzeit zu ihren Karten äussern. Widerspruch wird als
      Zitat aufgenommen, nicht weggeschrieben.</li>
    <li>Korrekturen werden sichtbar protokolliert, nicht stillschweigend nachgeführt.</li>
  </ol>
  <p>Grundlagen: Toulmin-Schema, Argumentationsschemata mit kritischen Fragen nach Walton,
  IFCN- und EFCSN-Kodex für Faktenprüfung, statistische Prüfregeln der empirischen
  Sozialforschung.</p>

  <h2>Quellen zur Vorlage</h2>
  <ul>{quellen}</ul>

  <p>Stand {e(daten['stand'])}, erzeugt am {date.today().strftime('%d.%m.%Y')}.{quellcode}
  Aufbereitung ohne Gewähr.</p>
</footer>

</div>
<div class="lupe" id="lupe" hidden>
  <div class="lupe-kopf"><span id="lupe-titel"></span>
    <button class="lupe-zu" id="lupe-zu">schliessen</button></div>
  <img id="lupe-bild" alt="">
</div>
<button class="schalter" id="schalter">Hell / Dunkel</button>
{teilen.HTML}
<script id="bild-daten" type="application/json">{bild_daten}</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<script>{JS}</script>
<script>{teilen.JS}</script>
</body>
</html>"""


def grafiken_kopieren() -> int:
    """Legt die eingebundenen Grafiken neben die Seite.

    Die Seite bindet ihre Bilder relativ ein, damit der Ordner
    site/abstimmung/<slug>/ fuer sich vollstaendig ist: verschieben, kopieren
    oder einzeln veroeffentlichen bleibt moeglich, ohne Pfade nachzuziehen.

    Kopiert wird nur, was die Seite tatsaechlich einbindet, und nur als SVG.
    Der Grafikordner der Vorlage enthaelt mehr: PNG fuer Bericht und Druck,
    und Auswertungen, die es nicht auf die Seite geschafft haben. Alles
    mitzunehmen hiesse, das Repository je Abstimmung um Megabyte zu belasten,
    die nie ein Browser anfordert.

    Die eingebundenen Dateien werden aus der gebauten Seite gelesen, nicht aus
    einer Liste. Eine Liste wuerde beim naechsten Umbau veralten, und dann
    fehlt entweder eine Grafik oder es liegt eine zu viel da. Dazu kommen die
    Gemeindekarten, die das Skript in der Seite erst zur Laufzeit
    zusammensetzt und die darum im Text nicht als Pfad stehen.

    Kopiert wird ueber vorhandene Dateien hinweg, statt das Ziel zuerst zu
    leeren. Auf eingehaengten Laufwerken schlaegt das Loeschen fehl, und ein
    Bauschritt, der am Aufraeumen scheitert, ist schlimmer als einer, der eine
    verwaiste Datei liegen laesst. Verwaiste werden einzeln entfernt, soweit
    das Laufwerk es zulaesst.
    """
    if not GRAFIKEN.is_dir():
        return 0
    ziel = ZIEL.parent / "grafiken"
    ziel.mkdir(parents=True, exist_ok=True)

    seite = ZIEL.read_text(encoding="utf-8")
    gebraucht = set(re.findall(r'grafiken/([A-Za-z0-9_/.-]+\.svg)', seite))
    gebraucht |= {f"gemeinden/{p.name}" for p in
                  (GRAFIKEN / "gemeinden").glob("karte_*.svg")}

    soll, fehlt = set(), []
    for rel in sorted(gebraucht):
        q = GRAFIKEN / rel
        if not q.is_file():
            fehlt.append(rel)
            continue
        z = ziel / rel
        z.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(q, z)
        soll.add(z)
    if fehlt:
        print("Hinweis: eingebundene Grafik fehlt: " + ", ".join(fehlt),
              file=sys.stderr)
    for alt in list(ziel.rglob("*")):
        if alt.is_file() and alt not in soll:
            try:
                alt.unlink()
            except OSError:
                print(f"Hinweis: verwaiste Datei bleibt liegen: {alt.name}",
                      file=sys.stderr)
    return len(soll)


def main() -> None:
    if not QUELLE.is_file():
        print(f"nicht gefunden: {QUELLE}", file=sys.stderr)
        raise SystemExit(1)
    fehlend = [p.name for p in (GEOJSON, HALTESTELLEN, BUSNETZ, KANTONSSTRASSEN)
               if not p.is_file()]
    hat_karte = bool((json.loads(QUELLE.read_text(encoding="utf-8")).get("karte") or {}).get("gemeinden"))
    if fehlend and hat_karte:
        print("Hinweis: nicht freigegebene Ebenen, sie fehlen auf der Karte: "
              + ", ".join(fehlend), file=sys.stderr)
    ZIEL.parent.mkdir(parents=True, exist_ok=True)
    ZIEL.write_text(bauen(), encoding="utf-8")
    n = grafiken_kopieren()
    print(f"geschrieben: {ZIEL}  ({ZIEL.stat().st_size/1024:.0f} kB), {n} Grafiken daneben")


if __name__ == "__main__":
    main()

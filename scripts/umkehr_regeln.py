#!/usr/bin/env python3
"""
Regelbasierte Klassierung der Umkehrabstimmungen
================================================
Setzt in data/umkehr_zuordnung.json das Feld "ja_ist_zustimmung" und hält in
"begruendung" fest, welche Regel gegriffen hat.

Der Gedanke dahinter
--------------------
Die Parlamentsdienste drucken den Hinweis "Ja bedeutet ..." genau dann, wenn
ein Ja im Rat nicht das bedeutet, was der Abstimmungstitel vermuten lässt.
Abgestimmt wird über das, was im Titel steht, meist "Antrag <Person>" oder ein
Sachtitel wie "Ausmehrung (Steuerfuss)". Der Hinweis nennt, welche Seite ein
Ja stützt. Stützt das Ja die Gegenseite (Kommission, Regierung, Beibehaltung
des bisherigen Zustands), ist ein Ja inhaltlich eine Ablehnung: echte Umkehr,
ja_ist_zustimmung = false.

Gegenprobe am Wortprotokoll (4. Sitzung vom 4. März 2024): der "Antrag Tim
Bucher" trägt den Hinweis "Ja bedeutet Verbleib bei aktueller Traktandenliste",
im Excel steht Ja 23 zu Nein 31. Das Protokoll hält fest, dem Antrag Bucher sei
"mit 31 : 23 Stimmen zugestimmt" worden. Ein Ja war dort also die Ablehnung.

Gegenprobe am Wortprotokoll
---------------------------
Seit dem 01.09.2026 bleibt es nicht bei der Regel. Jeder Fall wird zusätzlich
gegen das Wortprotokoll der Sitzung gehalten, das lokal in data/protokolle
liegt. Die Protokolle nennen das Ergebnis samt Gegenstand:

    «Der Kommissionsvorlage wird mit 39 : 16 Stimmen zugestimmt.»
    «Mit 35 : 24 Stimmen wird der Antrag von Kantonsrat Matthias Freivogel
     abgelehnt.»

Entscheidend ist nicht das Verb allein, sondern worauf es sich bezieht. Wird
der Kommissionsvorlage zugestimmt, ist ein Ja die Ablehnung des Antrags aus
dem Titel; wird dem Antrag des Titels zugestimmt, ist ein Ja Zustimmung. Aus
Gegenstand, Verb und der Frage, welche Seite gewonnen hat, ergibt sich
ja_ist_zustimmung eindeutig.

Bei Widerspruch gewinnt das Protokoll, die Regelbegründung bleibt im Eintrag
stehen. Was das Protokoll nicht klärt, landet in data/umkehr_pruefliste.md
und wird von Hand entschieden (herkunft = "manuell").

Ausführen:
    python3 scripts/umkehr_regeln.py            # Bericht, schreibt nichts
    python3 scripts/umkehr_regeln.py --apply    # schreibt Zuordnung + Prüfliste
    python3 scripts/umkehr_regeln.py --konflikte  # nur die Widersprüche zeigen
    python3 scripts/umkehr_regeln.py --ohne-protokoll  # nur Regelwerk, wie früher
"""
import collections
import difflib
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAPPING = ROOT / "data" / "umkehr_zuordnung.json"
SESSIONS = ROOT / "data" / "all_sessions.json"
PROTOKOLLE = ROOT / "data" / "protokolle"
PRUEFLISTE = ROOT / "data" / "umkehr_pruefliste.md"
PRUEFLISTE_JSON = ROOT / "data" / "umkehr_pruefliste.json"
MANUELL = ROOT / "data" / "umkehr_manuell.json"

# Gremien und Behörden. Alles Übrige mit einem mehrbuchstabigen Wort gilt als Person.
GREMIEN = {
    "spk", "gpk", "gesko", "jk", "bve", "buero", "buro", "kommission",
    "spezialkommission", "kommissionsvorlage", "gruez", "gesundheitskommission",
    "justizkommission", "erziehungsrat", "regierung", "regierungsrat", "rr",
    "kantonsrat", "9er", "9erspk", "praesidium", "praesident",
}
# Wörter, die vor einem Namen stehen und nicht zum Namen gehören
PRAEFIX = {"kr", "kantonsraetin", "kantonsrat", "antrag", "vorlage", "der", "des", "an"}

# Formulierungen, die den bisherigen Zustand bzw. das Gegenteil des Titels meinen
STATUS_QUO = re.compile(
    r"beibehalt|verbleib|bestehend|aktuelle|aktuell zu|unveraendert|"
    r"nichtabschreibung|nichtgenehmigung|nichteintreten|nicht eintreten|"
    r"ablehnend", re.I)
# Handlungen, die im Titel und im Hinweis dasselbe meinen können
GLEICHE_HANDLUNG = ("fristverlaengerung", "diskussion", "zuweisung", "ueberweisung",
                    "abschreibung", "eintreten", "wiederholung", "beratung",
                    "weiterberatung", "auftrag")


def norm(s):
    """Kleinbuchstaben, ohne Akzente und Satzzeichen."""
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]", " ", s.lower()).strip()


# Wörter, die nach «Antrag» stehen können, ohne ein Akteur zu sein. Ohne diese
# Sperre las die Titelanalyse aus «Antrag zu Art. 14bis betreffend …» den
# «Akteur» 1bis oder betreffend heraus und erklärte die Abstimmung für
# richtungsverkehrt. Der Abgleich mit dem Wortprotokoll hat das aufgedeckt.
NICHT_NAME = {
    "art", "abs", "ziff", "ziffer", "lit", "bst", "satz", "wortlaut", "lautet",
    "betreffend", "betrag", "und", "oder", "neue", "neuer", "neu", "vorliegende",
    "gesetz", "gesetzes", "beschluss", "beschlusses", "vorgehen", "einsetzung",
    "beteiligung", "sitzverteilung", "ubersicht", "nachmittag", "vormittag",
    "erganzen", "anzupassen", "streichung", "anpassung", "einfuhrung", "aufhebung",
    "eintreten", "nichteintreten", "ruckkommen", "uberweisung", "zuweisung",
    "fassung", "traktandenliste", "traktandum", "budget", "rechnung", "variante",
    "fristverlangerung", "diskussion", "abschreibung", "genehmigung", "wahl",
    "pos", "kto", "konto", "seite", "titel", "wie", "folgt", "dass", "nicht",
}

# Ein Akteur steht direkt nach «Antrag» und beginnt im Original mit einem
# Grossbuchstaben: «Antrag Christian Heydecker», «Antrag der GPK».
AKTEUR_NACH = re.compile(
    r"(?:Ordnungs|R[üu]ckweisungs|R[üu]ckkommens|Ab[äa]nderungs|[ÄA]nderungs|"
    r"Dringlichkeits|Streichungs)?[Aa]ntr(?:ag|äge)\s+"
    r"(?:von\s+|der\s+|des\s+)?"
    r"(?:Kantonsr[äa]tin\s+|Kantonsrat\s+|Regierungsr[äa]tin\s+|Regierungsrat\s+|"
    r"RR\.?\s+|alt\s+Kantonsr[äa]tin\s+|alt\s+Kantonsrat\s+)?"
    r"([A-ZÄÖÜ][\wäöüéèà.\-]*(?:\s+[A-ZÄÖÜ][\wäöüéèà.\-]*){0,2})")
PLANUNGSERKLAERUNG_NACH = re.compile(
    r"Planungserkl[äa]rung\s+([A-ZÄÖÜ][\wäöüéèà.\-]*(?:\s+[A-ZÄÖÜ][\wäöüéèà.\-]*){0,2})")
# «Josef Würms beantragt, …», «Bruno Müller beantragt, Anhang 2 abzulehnen»
VORAN_BEANTRAGT = re.compile(
    r"^(?:Kantonsr[äa]tin\s+|Kantonsrat\s+|Regierungsr[äa]tin\s+|Regierungsrat\s+)?"
    r"([A-ZÄÖÜ][\wäöüéèà.\-]*(?:\s+[A-ZÄÖÜ][\wäöüéèà.\-]*){0,2})\s+beantragt")


def akteur_titel(titel):
    """Antragsteller aus dem Abstimmungstitel, falls der Titel einen nennt.

    Gelesen wird der Originaltitel, nicht die normalisierte Fassung: die
    Grossschreibung ist das einzige verlässliche Merkmal, das einen Namen von
    einem Gesetzeswort unterscheidet.
    """
    # «Bericht und Antrag des Regierungsrats vom 14. Januar 2025 betreffend …»
    # ist die Bezeichnung des Geschäfts, kein Antragsteller.
    rein = re.sub(r"Bericht\s+und\s+Antrag\s+(?:des|der)\s+[\wäöüÄÖÜ.\-]+"
                  r"(?:\s+\d{4}/\d+)?(?:\s+vom\s+\d{1,2}\.\s*\w+\s*\d{4})?",
                  " ", titel or "")
    for muster in (AKTEUR_NACH, PLANUNGSERKLAERUNG_NACH, VORAN_BEANTRAGT):
        m = muster.search(rein.strip())
        if not m:
            continue
        woerter = [w for w in norm(m.group(1)).split()
                   if w and w not in PRAEFIX and w not in NICHT_NAME
                   and not any(z.isdigit() for z in w)]
        if woerter:
            return " ".join(woerter)
    return None


def akteur_hinweis(note):
    """Akteur aus dem Hinweis: nach Zustimmung / Annahme / Unterstützung."""
    n = norm(note)
    m = re.search(r"(?:zustimmung|annahme|unterstutzung)\s+(?:zum\s+)?"
                  r"(?:antrag|vorlage|antrage)?\s*(.+)", n)
    if not m:
        # knappe Form ohne Verb: "Ja bedeutet Antrag des Büros"
        m = re.search(r"bedeutet\s+(?:antrag|vorlage)\s+(.+)", n)
    if not m:
        return None
    rest = re.sub(r"\s*\(.*?\)\s*", " ", m.group(1).strip())
    rest = re.sub(r"\b20\d{2}\b|\b\d{1,3}\b", " ", rest)      # Geschäftsnummern weg
    return rest.strip() or None


def zerlege(akteur):
    """(art, kennung) mit art in {'gremium','person','kuerzel'}."""
    if not akteur:
        return (None, None)
    woerter = [w for w in akteur.split() if w and w not in PRAEFIX]
    if not woerter:
        return (None, None)
    def ist_gremium(w):
        # Genitiv mitnehmen: "des Büros" -> "buro"; zusammengesetzte Namen wie
        # "geschaeftsprufungskommission" über die Endung erkennen
        return (w in GREMIEN or w.rstrip("s") in GREMIEN or w.startswith("9er")
                or w.endswith("kommission") or w.endswith("kommissionen"))

    lang = [w for w in woerter if len(w) > 2]
    gremien = [w.rstrip("s") if w not in GREMIEN else w
               for w in woerter if ist_gremium(w)]
    # "RR M. Montanari": Gremienkürzel als Vorsatz vor einem Personennamen
    nicht_gremium = [w for w in lang if not ist_gremium(w)]
    if nicht_gremium:
        return ("person", nicht_gremium[-1])
    if gremien:
        return ("gremium", gremien[0])
    return ("kuerzel", "".join(woerter))


def initialen(name_teile):
    return "".join(w[0] for w in name_teile if w)


NEGATION = re.compile(r"\b(keine?|nicht|kein|abbruch|nichtabschreibung|"
                      r"nichtgenehmigung|nichteintreten|abschreibung|ablehnend)\b")
# Füllwörter, die beim Wortvergleich nichts beitragen
FUELL = {"der", "die", "das", "des", "dem", "den", "von", "vom", "zu", "zur", "zum",
         "eine", "einen", "einer", "im", "in", "an", "auf", "und", "bis", "fur",
         "antrag", "antrags", "ja", "bedeutet", "abs", "art", "nr"}


NAME = r"([A-ZÄÖÜ][\wäöüéèà.\-]*(?:\s+[A-ZÄÖÜ][\wäöüéèà.\-]*){0,2})"
ANTRAG_MUSTER = (
    # "Antrag Peter Scheck: Keine Diskussion der Interpellation"
    r"(?:R[üu]ckweisungs|Ordnungs)?[Aa]ntrag\s+(?:von\s+)?"
    r"(?:Kantonsr[äa]tin\s+|Kantonsrat\s+)?" + NAME + r"\s*:?\s+(.+)",
    # "Linda De Ventura beantragt für die Motion ... eine Fristverlängerung"
    r"(?:Von\s+)?" + NAME + r"\s+beantragte?n?,?\s+(.+)",
)


def antrag_inhalt(text):
    """(Antragsteller, Inhalt des Antrags) aus Titel und Detailtext.

    Titel und Detailspalte der Excel halten oft fest, wer was verlangt hat.
    Das reicht, um den Hinweis dagegenzuhalten, ohne ins Wortprotokoll zu
    müssen."""
    if not text:
        return (None, None)
    for muster in ANTRAG_MUSTER:
        m = re.search(muster, text)
        if not m:
            continue
        person = norm(m.group(1)).split()
        inhalt = re.split(r"\s(?:R[üu]ckweisungs|Ordnungs)?[Aa]ntrag\s+[A-ZÄÖÜ]",
                          m.group(2))[0]
        return (person[-1] if person else None, inhalt)
    return (None, None)


def wortmenge(s):
    return {w for w in norm(s).split() if len(w) > 2 and w not in FUELL}


def _klassiere_roh(titel, note, details=""):
    """(ja_ist_zustimmung, Begründung, entschieden).

    ja_ist_zustimmung darf auch bei entschieden=True None sein: bei einer
    Ausmehrung stehen sich zwei Anträge gegenüber, eine inhaltliche Richtung
    gibt es dort nicht. Solche Abstimmungen bleiben aus dem Matching draussen.
    """
    nt, nn = norm(titel), norm(note)
    at, an = akteur_titel(titel), akteur_hinweis(note)
    art_t, kenn_t = zerlege(at)
    art_n, kenn_n = zerlege(an)

    # R0: Ausmehrung, also Stichentscheid zwischen zwei Anträgen
    if re.search(r"ausmehrung|ausmherung|ausmerhung", nt):
        gegen = f" (Ja stützt {kenn_n})" if kenn_n else ""
        return (None, "Ausmehrung zwischen zwei Anträgen: ein Ja ist Zustimmung "
                      f"zur einen und Ablehnung der anderen Fassung{gegen}. "
                      "Eine einheitliche inhaltliche Richtung gibt es nicht, "
                      "die Abstimmung bleibt aus dem Matching draussen.", True)

    # R1: beide Seiten nennen einen Akteur -> vergleichen
    if kenn_t and kenn_n and "kuerzel" not in (art_t, art_n):
        if kenn_t == kenn_n:
            return (True, f"Hinweis nennt denselben Akteur ({kenn_t}) wie der Titel", True)
        return (False, f"Titel betrifft {kenn_t}, das Ja stützt aber {kenn_n}: "
                       f"Ja ist Ablehnung des Antrags", True)

    # R2: Hinweis nennt nur Initialen -> mit dem Namen im Titel abgleichen
    if art_n == "kuerzel" and at:
        teile = [w for w in at.split() if w not in PRAEFIX]
        kandidaten = {initialen(teile), initialen(teile[-2:]), (teile[-1][0] if teile else "")}
        if kenn_n in kandidaten:
            return (True, f"Initialen «{kenn_n.upper()}» passen zum Antragsteller im Titel", True)
        return (False, f"Initialen «{kenn_n.upper()}» gehören nicht zum Antragsteller "
                       f"im Titel: Ja ist Ablehnung des Antrags", True)

    # R3: Ja meint den bisherigen Zustand oder das Gegenteil des Titels
    if STATUS_QUO.search(nn) and not STATUS_QUO.search(nt):
        return (False, "Ja meint Beibehaltung des bisherigen Zustands, der Titel "
                       "aber dessen Änderung: Ja ist Ablehnung des Antrags", True)

    # R4: Hinweis und Titel meinen dieselbe Handlung
    for h in GLEICHE_HANDLUNG:
        if h in nn and h in nt:
            return (True, f"Hinweis und Titel meinen dieselbe Handlung ({h})", True)

    # R5: Sachtitel, das Ja stützt ein Gremium (Kommissions- oder Regierungsfassung)
    if not at and art_n == "gremium":
        return (False, f"Sachtitel, das Ja stützt die Fassung von {kenn_n}: "
                       f"inhaltliche Zustimmung zur Änderung entspricht einem Nein", True)

    # R6: Sachtitel, das Ja stützt den Antrag einer Person
    if not at and art_n == "person":
        return (True, f"Sachtitel, das Ja stützt den Antrag von {kenn_n}", True)

    # R8: Titel oder Detailspalte nennen den Antrag samt Inhalt -> Hinweis
    # dagegenhalten
    person, inhalt = antrag_inhalt(f"{titel} {details}".strip())
    if inhalt:
        # steht im Hinweis ein anderer Akteur als im Antrag, entscheidet das
        if kenn_n and person and kenn_n != person and art_n in ("person", "gremium"):
            return (False, f"Der Antrag stammt von {person}, das Ja stützt "
                           f"{kenn_n}: Ja ist Ablehnung des Antrags", True)
        gemeinsam = wortmenge(inhalt) & wortmenge(nn.replace("ja bedeutet", ""))
        if gemeinsam:
            neg_inhalt = bool(NEGATION.search(norm(inhalt)))
            neg_note = bool(NEGATION.search(nn))
            if neg_inhalt == neg_note:
                return (True, f"Das Ja meint dasselbe wie der Antrag "
                              f"({', '.join(sorted(gemeinsam))})", True)
            return (False, f"Das Ja kehrt den Antrag um "
                           f"({', '.join(sorted(gemeinsam))}): Ja ist Ablehnung", True)
        if person:
            return (False, f"Das Ja meint etwas anderes als der Antrag von "
                           f"{person}: Ja ist Ablehnung des Antrags", True)

    # R7: Titel nennt einen Antrag, der Hinweis beschreibt die Gegenposition
    if at and not an:
        return (False, "Titel nennt einen Antrag, das Ja beschreibt die "
                       "Gegenposition: Ja ist Ablehnung des Antrags", True)

    # R9: Auswahl zwischen zwei Varianten (wie eine Ausmehrung)
    nd = norm(details)
    if re.search(r"\b\d+\s+oder\s+\d+\b", nd) or " vs " in nd:
        return (None, "Auswahl zwischen zwei Varianten: ein Ja ist Zustimmung zur "
                      "einen und Ablehnung der anderen. Eine einheitliche inhaltliche "
                      "Richtung gibt es nicht, die Abstimmung bleibt aus dem Matching "
                      "draussen.", True)

    # R10: das Ja führt das laufende Verfahren fort, der Antrag wollte es stoppen
    if re.search(r"fortfuhrung|fortsetzung|weiterfuhrung|weiterberatung|"
                 r"sofortige|verbleib", nn):
        return (False, "Das Ja führt das laufende Verfahren fort, der Antrag wollte "
                       "es unterbrechen: Ja ist Ablehnung des Antrags", True)

    return (None, "nicht entscheidbar, am Wortprotokoll zu prüfen", False)


# Regeln, die nur auf einem Indiz beruhen. Ihr Ergebnis ist plausibel, aber
# nicht belegt, darum sind ihre Fälle die eigentlichen Zweifelsfälle.
SCHWACHE_REGELN = (
    "Titel nennt einen Antrag, das Ja beschreibt die Gegenposition",
    "Das Ja führt das laufende Verfahren fort",
    "Hinweis und Titel meinen dieselbe Handlung",
    "Das Ja meint etwas anderes als der Antrag von",
)


def klassiere(titel, note, details=""):
    """(ja_ist_zustimmung, Begründung, entschieden, Stärke).

    Stärke ist «stark», wenn die Regel zwei benannte Akteure vergleichen
    konnte, sonst «schwach».
    """
    wert, grund, entschieden = _klassiere_roh(titel, note, details)
    schwach = any(m in grund for m in SCHWACHE_REGELN)
    return (wert, grund, entschieden, "schwach" if schwach else "stark")


# ═════════════════════════════════════════════════════════════════════════════
# Gegenprobe am Wortprotokoll
# ═════════════════════════════════════════════════════════════════════════════

# «Mit 42 : 9 Stimmen bei 7 Enthaltungen wird der Diskussion zugestimmt.»
# «Der Kommissionsvorlage wird mit 39 : 16 Stimmen zugestimmt.»
# «mit 39 : 19 Stimmen», aber auch «mit 29 : 26 bei 1 Enthaltung»
STIMMENZAHL = re.compile(
    r"\b[Mm]it\s+(\d{1,3})\s*[:.]\s*(\d{1,3})\s+(?:Stimmen|bei\s+\d)")

# Erst verneinen, dann bejahen: «nicht erheblich erklärt» enthält «erheblich erklärt».
# «Nichteintreten» und «Nichtabschreibung» stehen hier bewusst NICHT: das sind
# Hauptwörter, die den Gegenstand benennen («Dem Antrag auf Nichteintreten wird
# gefolgt»), nicht das Ergebnis. Sie werden über GEGENTEIL ausgewertet.
ABGELEHNT = re.compile(
    r"\b(?:abgelehnt|verworfen|abgewiesen|"
    r"nicht\s+(?:erheblich|zugestimmt|genehmigt|gutgeheissen|überwiesen|"
    r"angenommen|eingetreten|zu\s?gestimmt|bewilligt|gefolgt)|"
    r"keine\s+Zustimmung|im\s+ablehnenden\s+Sinn)\b", re.I)
ANGENOMMEN = re.compile(
    r"\b(?:zugestimmt|zu\s?gestimmt|angenommen|genehmigt|gutgeheissen|"
    r"erheblich\s+erklärt|beschlossen|überwiesen|obsiegt|obsiegte|eingetreten|"
    r"bewilligt|erteilt|unterstützt|gefolgt|im\s+zustimmenden\s+Sinn|"
    r"de[rmn]\s+Vorzug\s+(?:gegeben|erhalten))\b", re.I)

# Gegenstand der Abstimmung: die Gegenseite zum Antrag aus dem Titel.
# \w* fängt die Beugung ab: «Kommissionsvorlage», «Änderungsanträgen».
GEGENSEITE = re.compile(
    r"\b(?:Kommissionsvorlage\w*|Kommissionsantr\w+|Kommissionsfassung\w*|"
    r"(?:Vorlage|Antrag|Antrage|Fassung|Version)\s+de[rs]\s+(?:Spezial)?[Kk]ommission\w*|"
    r"(?:Vorlage|Antrag|Antrage|Fassung)\s+de[rs]\s+"
    r"(?:GPK|SPK|GESKO|BVE|Justizkommission|Gesundheitskommission|"
    r"Geschäftsprüfungskommission|Büros|Regierungsrats|Regierung)|"
    r"Regierungsvorlage\w*|Regierungsfassung\w*)\b", re.I)

# Gegenstand ist das, worüber der Titel spricht
TITELSACHE = re.compile(
    r"\b(?:Ordnungsantr\w+|Rückkommensantr\w+|Rückweisungsantr\w+|Abänderungsantr\w+|"
    r"Änderungsantr\w+|Streichungsantr\w+|Antr[aä]g\w*|Postulat\w*|Motion\w*|"
    r"Volksmotion\w*|Interpellation\w*|Planungserklärung\w*|Petition\w*|Vorstoss\w*|"
    r"Diskussion\w*|Verschiebung\w*|Wiederholung\w*|Fristverlängerung\w*|"
    r"Überweisung\w*|Zuweisung\w*|Abschreibung\w*|Traktandenliste\w*|"
    r"zweiten\s+Lesung|Kreditbeschluss\w*|Beschluss\w*|Genehmigung\w*)\b", re.I)

# Teilsätze, die ein zweites Ergebnis nachschieben:
# «… wird gefolgt UND der Antrag von X SOMIT abgelehnt», «… (Antrag RR abgelehnt)»
TEILSATZ = re.compile(r"\s+und\s+(?:damit\s+|somit\s+)?|\s*\(")

# Satzgrenze: Punkt nach einem Kleinbuchstaben. So bleiben «Art. 3», «Abs. 2»
# und «17. Januar 2026» im Satz, «… zugestimmt.» beendet ihn dagegen.
# Gängige Abkürzungen müssen ausgenommen werden, sonst endet der Satz mitten
# in «… um 1 Mio. Franken».
ABKUERZUNG = re.compile(
    r"\b(?:Mio|Mrd|Fr|Nr|Art|Abs|Ziff|lit|Bst|bzw|ca|inkl|exkl|resp|Kto|Pos|"
    r"vgl|evtl|max|min|Prof|Dr|z|B|d|h|u|a|S|Tr)\.$")
SATZENDE = re.compile(r"(?<=[a-zäöüß»)\"])\.")


def echtes_satzende(text, pos):
    """Ob der Punkt an dieser Stelle wirklich einen Satz beendet."""
    return not ABKUERZUNG.search(text[max(0, pos - 12):pos + 1])


def satz_um(text, start, ende):
    """Den Satz herausschneiden, in dem die Fundstelle steht."""
    fenster_links = max(0, start - 320)
    links = fenster_links
    for m in SATZENDE.finditer(text, fenster_links, start):
        if echtes_satzende(text, m.start()):
            links = m.end()
    rechts = min(len(text), ende + 260)
    for m in SATZENDE.finditer(text, ende, rechts):
        if echtes_satzende(text, m.start()):
            rechts = m.end()
            break
    return text[links:rechts].strip()


def protokolltext(sitzung, sess_protokolle, _cache={}):
    """Zusammengefügter Volltext aller Protokolle einer Sitzung, geglättet."""
    if sitzung in _cache:
        return _cache[sitzung]
    teile = []
    for kennung in sess_protokolle.get(sitzung, []):
        pfad = PROTOKOLLE / (kennung + ".txt")
        if pfad.exists():
            teile.append(pfad.read_text(encoding="utf-8", errors="replace"))
    text = "\n".join(teile)
    text = re.sub(r"-\n", "", text)          # Silbentrennung am Zeilenende
    text = re.sub(r"\s+", " ", text)
    _cache[sitzung] = text
    return text


def fundstellen(text):
    """Alle Resultatsätze eines Protokolls: (Position, a, b, Satz)."""
    treffer = []
    for m in STIMMENZAHL.finditer(text):
        a, b = int(m.group(1)), int(m.group(2))
        if a + b < 15:
            continue                          # Kommissionsabstimmung, nicht das Plenum
        treffer.append((m.start(), a, b, satz_um(text, m.start(), m.end())))
    return treffer


# «Antrag von Kantonsrätin Eva Neumann», «Antrag der GPK», «Antrag, von Tim Bucher»
URHEBER_IM_SATZ = re.compile(
    # «Streichungsantrag», «Änderungsantrag», «Antrag 1 von …»,
    # «Antrag des ersten Vizepräsidenten Christian Di Ronco»
    r"(?:[A-ZÄÖÜ][a-zäöüß]+s)?(?:[Aa]ntr(?:ag|ags|äge|äg)|[Vv]orlage|[Ff]assung)"
    r"\s*(?:\d{1,2}|[IVX]{1,4})?\s*,?\s*(?:von\s+|der\s+|des\s+|dem\s+)?"
    r"(?:Frau\s+|Herr\s+|alt\s+)?(?:ersten\s+|zweiten\s+|dritten\s+)?"
    r"(?:Kantonsr[äa]tin\s+|Kantonsrat\s+|Regierungsr[äa]tin\s+|Regierungsrat\s+|"
    r"Vizepr[äa]sident(?:in|en)?\s+|Kantonsratspr[äa]sident(?:in|en)?\s+|"
    r"Kommissionspr[äa]sident(?:in|en)?\s+)?"
    r"(?:Frau\s+|Herr\s+)?"
    r"([A-ZÄÖÜ][\wäöüéèà\-]+(?:\s+[A-ZÄÖÜ][\wäöüéèà\-]+){0,2})")

# Verneinende Zusammensetzungen: das Ja meint das Gegenteil des Titels
GEGENTEIL = re.compile(
    r"\b(?:Nichtabschreibung|Nichtgenehmigung|Nichteintreten|Nichtabnahme|"
    r"Beibehaltung|Verbleib|Aufrechterhaltung|bisherigen\s+Fassung|"
    r"geltenden\s+Fassung)\w*", re.I)

# Ein Satz zählt nur als Resultatsatz, wenn er auch so klingt.
RESULTATSATZ = re.compile(
    r"(?:^|\bAbstimmungen?\b|\bSchlussabstimmung\b|\bwird\b|\bwurde\b|\bist\b)", re.I)


def ergebniswort(text):
    """True bei Annahme, False bei Ablehnung, None wenn unklar oder beides.

    Die Verneinung hat Vorrang und überdeckt das Wort, das in ihr steckt:
    «nicht genehmigt» enthält «genehmigt», ist aber eine Ablehnung.
    """
    nein_spans = [m.span() for m in ABGELEHNT.finditer(text)]
    ja_spans = [m.span() for m in ANGENOMMEN.finditer(text)
                if not any(a <= m.start() < b for a, b in nein_spans)]
    if nein_spans and ja_spans:
        return None
    if nein_spans:
        return False
    if ja_spans:
        return True
    return None


def akteur_im_satz(satz):
    """(art, kennung, Namenswörter) des Urhebers, über dessen Antrag der Satz
    abstimmt.

    Verwendet dieselbe Zerlegung wie das Regelwerk, damit «GPK» im Titel und
    «Antrag der GPK» im Protokoll als derselbe Akteur erkannt werden. Die
    Namenswörter kommen dazu, weil das Protokoll Vor- und Nachnamen vertauscht
    («Antrag von Aellig Pentti»), sie verschieden schreibt («Altdorfer» statt
    «Altorfer») oder «Frau Kantonsrätin» davorsetzt.
    """
    m = URHEBER_IM_SATZ.search(satz)
    if m:
        woerter = {w for w in norm(m.group(1)).split()
                   if len(w) > 2 and w not in PRAEFIX and w not in NICHT_NAME}
        art, kenn = zerlege(norm(m.group(1)))
        if kenn:
            return (art, kenn, woerter)
    m = GEGENSEITE.search(satz)
    if m:
        art, kenn = zerlege(norm(m.group(0)))
        return (art, kenn, set())
    return (None, None, set())


def aehnlich(a, b):
    """Ähnlichkeit zweier Namen zwischen 0 und 1."""
    return difflib.SequenceMatcher(None, a, b).ratio()


def gleicher_akteur(kenn_titel, woerter_titel, kenn_satz, woerter_satz):
    """(gleich, sicher) für den Akteur in Titel und Protokollsatz.

    Der Vergleich läuft über den Nachnamen. Ein blosser Vornamenstreffer
    genügt nicht: «Matthias Frick» und «Matthias Freivogel» sind zwei
    verschiedene Ratsmitglieder.

    Die Protokolle schreiben Namen gelegentlich falsch («Altdorfer» statt
    «Altorfer»). Ein Präfixvergleich reicht dafür nicht, denn der Tippfehler
    kann am Wortanfang stehen. Darum ein echtes Ähnlichkeitsmass, und im
    Graubereich wird nichts entschieden: ein falsch zugeordneter Akteur dreht
    die Richtung der ganzen Abstimmung um.
    """
    if kenn_titel and kenn_satz and kenn_titel == kenn_satz:
        return (True, True)
    if not (kenn_titel and kenn_satz):
        return (False, False)
    # Namen können vertauscht sein: «Aellig Pentti» statt «Pentti Aellig»
    if kenn_titel in woerter_satz or kenn_satz in woerter_titel:
        return (True, True)
    r = aehnlich(kenn_titel, kenn_satz)
    if r >= 0.82:
        return (True, True)              # Schreibvariante derselben Person
    if r >= 0.55:
        return (False, False)            # zu ähnlich, um sicher zu trennen
    return (False, True)                 # klar verschiedene Akteure


def inhaltlich_verwandt(satz, eintrag, details):
    """Grobe Plausibilität: teilen Satz und Abstimmung ein Sachwort?

    Ein Zahlenpaar wie 56 : 0 kommt in einer Sitzung mehrfach vor. Ohne diesen
    Filter würde ein einstimmiger Beschluss zum Wasserwirtschaftsgesetz als
    Beleg für eine Abstimmung über ein Demenzkonzept durchgehen.
    """
    quelle = " ".join([eintrag.get("titel") or "", eintrag.get("geschaeft") or "",
                       details or "", eintrag.get("inverted_note") or ""])
    worte_quelle = {w for w in norm(quelle).split() if len(w) > 5 and w not in FUELL}
    if not worte_quelle:
        return True                      # nichts zu vergleichen, nicht sperren
    worte_satz = {w for w in norm(satz).split() if len(w) > 5}
    return bool(worte_quelle & worte_satz)


def richtung_aus_satz(satz, titel=""):
    """(angenommen, Gegenstand, Grund).

    Gegenstand ist «titelantrag», wenn der Satz über dasselbe abstimmt wie der
    Excel-Titel, und «gegenseite» bei der Gegenposition. Im Zweifel wird nichts
    entschieden: lieber auf die Prüfliste als eine falsche Korrektur.
    """
    if len(satz) > 420 or not RESULTATSATZ.search(satz):
        return (None, None, "kein eindeutiger Resultatsatz")

    angenommen = ergebniswort(satz)
    akteur_t = akteur_titel(titel or "")

    if angenommen is None:
        # Sätze wie «Dem Antrag der Kommission wird gefolgt und der Antrag von
        # A. Schnetzler somit abgelehnt» schieben ein zweites Ergebnis nach.
        # Beide Hälften sagen dasselbe, nur aus verschiedener Sicht. Es zählt
        # die Hälfte, die den Akteur aus dem Titel nennt.
        teile = [t for t in TEILSATZ.split(satz) if t and t.strip()]
        kenn_t = zerlege(akteur_t)[1]
        if len(teile) > 1 and kenn_t:
            for teil in teile:
                erg = ergebniswort(teil)
                if erg is not None and re.search(
                        r"\b" + re.escape(kenn_t) + r"\w*", norm(teil)):
                    return (erg, "titelantrag", None)
            for teil in teile:
                erg = ergebniswort(teil)
                if erg is not None and GEGENSEITE.search(teil):
                    return (erg, "gegenseite", None)
        return (None, None, "Satz nennt Annahme und Ablehnung nebeneinander")
    _, kenn_titel = zerlege(akteur_t)
    woerter_titel = {w for w in (akteur_t or "").split() if len(w) > 2}
    art_satz, kenn_satz, woerter_satz = akteur_im_satz(satz)

    # Nennt der Satz sowohl die Gegenfassung als auch den Akteur aus dem Titel
    # an einer anderen Stelle, stellt er zwei Anträge gegenüber. Welcher Teil
    # das Verb trägt, ist dann nicht sicher zu entscheiden. Fällt der Akteur
    # mit der Gegenfassung zusammen («Antrag GPK» und «Antrag der GPK»), ist
    # das kein Widerspruch.
    m_gegen = GEGENSEITE.search(satz)
    if kenn_titel and m_gegen:
        n_satz = norm(satz)
        n_gegen = norm(m_gegen.group(0))
        if (re.search(r"\b" + re.escape(kenn_titel) + r"\w*", n_satz)
                and not re.search(r"\b" + re.escape(kenn_titel) + r"\w*", n_gegen)):
            return (None, None, "Satz stellt zwei Anträge gegenüber")

    # 1. Beide Seiten nennen einen Akteur: der Vergleich entscheidet.
    if kenn_titel and kenn_satz:
        gleich, sicher = gleicher_akteur(kenn_titel, woerter_titel, kenn_satz, woerter_satz)
        if not sicher:
            return (None, None, f"Akteure «{kenn_titel}» und «{kenn_satz}» zu ähnlich, "
                                "um sie sicher zu trennen")
        return (angenommen, "titelantrag" if gleich else "gegenseite", None)

    # 2. Sachtitel ohne Akteur, der Satz nennt ein Gremium: das ist die
    #    Gegenfassung zum Titel.
    if not kenn_titel and art_satz == "gremium":
        return (angenommen, "gegenseite", None)

    # 3. Verneinende Zusammensetzung, die im Titel nicht vorkommt.
    if GEGENTEIL.search(satz) and not GEGENTEIL.search(titel or ""):
        return (angenommen, "gegenseite", None)

    # 4. Der Titel nennt einen Akteur, der Satz nicht: zu unsicher.
    if kenn_titel:
        return (None, None, "Satz nennt den Akteur aus dem Titel nicht")

    # 5. Weder Titel noch Satz nennen einen Akteur: der Satz spricht über die
    #    Sache aus dem Titel.
    if TITELSACHE.search(satz):
        return (angenommen, "titelantrag", None)

    return (None, None, "Gegenstand der Abstimmung im Satz nicht erkennbar")


def protokoll_pruefen(eintrag, ja, nein, text, details=""):
    """Ergebnis der Gegenprobe als Wörterbuch.

    status: bestaetigt | keine_fundstelle | mehrdeutig | objekt_unklar | kein_text
    """
    if not text:
        return {"status": "kein_text", "wert": None, "beleg": "", "hinweis":
                "Für diese Sitzung liegt kein Protokolltext vor."}
    if ja == nein:
        return {"status": "objekt_unklar", "wert": None, "beleg": "", "hinweis":
                "Stimmengleichheit, aus dem Protokoll nicht eindeutig zuzuordnen."}

    kandidaten = []
    for pos, a, b, satz in fundstellen(text):
        if {a, b} != {ja, nein}:
            continue
        angenommen, gegenstand, warum = richtung_aus_satz(satz, eintrag.get("titel") or "")
        if angenommen is None:
            kandidaten.append({"satz": satz, "wert": None, "hinweis": warum,
                               "verwandt": inhaltlich_verwandt(satz, eintrag, details)})
            continue
        ja_gewinnt = ja > nein
        ja_stuetzt_gegenstand = (ja_gewinnt == angenommen)
        wert = ja_stuetzt_gegenstand if gegenstand == "titelantrag" else not ja_stuetzt_gegenstand
        kandidaten.append({"satz": satz, "wert": wert, "gegenstand": gegenstand,
                           "angenommen": angenommen, "hinweis": None,
                           "verwandt": inhaltlich_verwandt(satz, eintrag, details)})

    if not kandidaten:
        return {"status": "keine_fundstelle", "wert": None, "beleg": "", "hinweis":
                f"Kein Satz mit {ja} : {nein} Stimmen im Protokoll gefunden."}

    # Sachtitel ohne Antragsteller: die Richtung folgt der Konvention, nicht dem
    # Protokoll. Das gilt auch dann, wenn im Satz keine Richtung erkennbar ist,
    # denn erkennbar wäre sie ohnehin nur für den Antrag, den der Titel nicht nennt.
    if not akteur_titel(eintrag.get("titel") or ""):
        return {"status": "titel_ohne_akteur", "wert": None,
                "beleg": kandidaten[0]["satz"],
                "hinweis": "Sachtitel ohne Antragsteller. Das Protokoll belegt das "
                           "Ergebnis, nicht aber die inhaltliche Richtung."}

    mit_wert = [k for k in kandidaten if k["wert"] is not None]
    # Der Inhaltsvergleich greift nur dort ein, wo er gebraucht wird: bei
    # mehreren Fundstellen und bei einstimmigen Resultaten, deren Zahlenpaar
    # in einer Sitzung mehrfach vorkommt.
    if len(mit_wert) > 1 or (mit_wert and min(ja, nein) == 0):
        verwandte = [k for k in mit_wert if k["verwandt"]]
        if verwandte:
            mit_wert = verwandte
        elif min(ja, nein) == 0:
            return {"status": "keine_fundstelle", "wert": None,
                    "beleg": mit_wert[0]["satz"], "hinweis":
                    f"Fundstelle mit {ja} : {nein} Stimmen passt inhaltlich nicht "
                    "zur Abstimmung."}
    # Mehrere Fundstellen mit demselben Zahlenpaar: es zählt die, die den
    # Antragsteller aus dem Titel nennt. In einer Sitzung werden oft mehrere
    # Anträge mit identischem Stimmenverhältnis abgelehnt.
    if len(mit_wert) > 1:
        kenn_t = zerlege(akteur_titel(eintrag.get("titel") or ""))[1]
        if kenn_t:
            passend = [k for k in mit_wert
                       if re.search(r"\b" + re.escape(kenn_t) + r"\w*", norm(k["satz"]))]
            if len(passend) >= 1:
                mit_wert = passend

    werte = {k["wert"] for k in mit_wert}
    if not werte:
        return {"status": "objekt_unklar", "wert": None,
                "beleg": kandidaten[0]["satz"], "hinweis": kandidaten[0]["hinweis"]}
    if len(werte) > 1:
        return {"status": "mehrdeutig", "wert": None,
                "beleg": " ||| ".join(k["satz"] for k in mit_wert[:3]),
                "hinweis": f"{len(mit_wert)} Fundstellen mit {ja} : {nein} Stimmen "
                           "führen zu verschiedenen Ergebnissen."}
    beste = mit_wert[0]
    return {"status": "bestaetigt", "wert": beste["wert"], "beleg": beste["satz"],
            "hinweis": f"Gegenstand: {beste['gegenstand']}, "
                       f"{'angenommen' if beste['angenommen'] else 'abgelehnt'}"
                       + (f", {len(mit_wert)} übereinstimmende Fundstellen"
                          if len(mit_wert) > 1 else "")}


def sitzungsdaten():
    """(Stimmenzahlen je Abstimmung, Protokollkennungen je Sitzung)."""
    if not SESSIONS.exists():
        return {}, {}
    daten = json.load(open(SESSIONS, encoding="utf-8"))
    stimmen, protokolle = {}, {}
    for s in daten["sessions"]:
        protokolle[s["sitzung"]] = [
            m.group(1) for p in (s.get("protokolle") or [])
            for m in [re.search(r"/file/([0-9a-f-]{36})", p.get("url") or "")] if m
        ]
        for i, v in enumerate(s["votes"]):
            zaehler = collections.Counter()
            for mitglied in s["members"]:
                stimme = mitglied["votes"][i] if i < len(mitglied["votes"]) else "V/A/N"
                zaehler[stimme] += 1
            stimmen[f"{s['sitzung']} #Nr{v['nr']}"] = (zaehler["Ja"], zaehler["Nein"])
    return stimmen, protokolle


def details_lesen():
    """Detailtext je Abstimmung aus all_sessions.json (Schlüssel wie in umkehr.py)."""
    pfad = ROOT / "data" / "all_sessions.json"
    if not pfad.exists():
        return {}
    daten = json.load(open(pfad, encoding="utf-8"))
    return {f"{s['sitzung']} #Nr{v['nr']}": (v.get("details") or "")
            for s in daten["sessions"] for v in s["votes"]}


def kurz(s, n=72):
    s = re.sub(r"\s+", " ", s or "").strip()
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "…"


def pruefliste_schreiben(faelle):
    """Restfälle als lesbare Liste für die Handprüfung."""
    zeilen = [
        "# Umkehrabstimmungen: offene Fälle",
        "",
        "Automatisch erzeugt von `scripts/umkehr_regeln.py`. Diese Fälle konnte die",
        "Gegenprobe am Wortprotokoll nicht klären. Entscheid von Hand eintragen in",
        "`data/umkehr_zuordnung.json`: `ja_ist_zustimmung` setzen, `herkunft` auf",
        "`\"manuell\"`, Begründung ergänzen.",
        "",
        f"Offen: **{len(faelle)}**",
        "",
    ]
    nach_grund = collections.Counter(f["protokoll_status"] for f in faelle)
    for grund, anzahl in nach_grund.most_common():
        zeilen.append(f"- `{grund}`: {anzahl}")
    zeilen.append("")
    for f in faelle:
        zeilen += [
            "---",
            "",
            f"### {f['schluessel']}",
            "",
            f"- **Titel:** {kurz(f.get('titel') or '(leer)', 120)}",
            f"- **Hinweis:** {kurz(f.get('inverted_note') or '', 120)}",
            f"- **Stimmen:** {f['ja']} Ja : {f['nein']} Nein",
            f"- **Regel:** `ja_ist_zustimmung = {f['regel_wert']}` "
            f"({f['regel_staerke']}) — {kurz(f['regel_grund'], 110)}",
            f"- **Protokoll:** `{f['protokoll_status']}` — {f['protokoll_hinweis']}",
            "",
        ]
        if f.get("beleg"):
            zeilen += ["> " + kurz(f["beleg"], 600), ""]
    PRUEFLISTE.write_text("\n".join(zeilen), encoding="utf-8")
    json.dump(faelle, open(PRUEFLISTE_JSON, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


def main():
    mit_protokoll = "--ohne-protokoll" not in sys.argv
    daten = json.load(open(MAPPING, encoding="utf-8"))
    rows = daten["zuordnung"]
    details = details_lesen()
    stimmen, sess_protokolle = sitzungsdaten() if mit_protokoll else ({}, {})

    zahlen = collections.Counter()
    konflikte, offene = [], []

    handentscheide = {}
    if MANUELL.exists():
        handentscheide = {e["schluessel"]: e
                          for e in json.load(open(MANUELL, encoding="utf-8"))["entscheide"]}

    for r in rows:
        schluessel = r["schluessel"]

        # Handentscheide haben Vorrang vor allem anderen.
        if schluessel in handentscheide:
            h = handentscheide[schluessel]
            r.update(ja_ist_zustimmung=h["ja_ist_zustimmung"], herkunft="manuell",
                     geprüft=True, begruendung=h["begruendung"],
                     protokoll_status="manuell", protokoll_beleg=h.get("beleg", ""))
            zahlen["manuell"] += 1
            continue

        regel_wert, regel_grund, entschieden, staerke = klassiere(
            r.get("titel") or "", r.get("inverted_note") or "",
            details.get(schluessel, ""))
        zahlen["regel_" + ("stark" if entschieden and staerke == "stark"
                           else "schwach" if entschieden else "offen")] += 1

        prot = {"status": "uebersprungen", "wert": None, "beleg": "", "hinweis": ""}
        ja, nein = stimmen.get(schluessel, (None, None))
        if mit_protokoll and ja is not None:
            prot = protokoll_pruefen(r, ja, nein,
                                     protokolltext(r["sitzung"], sess_protokolle),
                                     details.get(schluessel, ""))
        zahlen["prot_" + prot["status"]] += 1

        # Ausmehrungen haben keine Richtung, die bleibt so.
        if entschieden and regel_wert is None:
            r.update(ja_ist_zustimmung=None, begruendung=regel_grund,
                     herkunft="regel", geprüft=True, regel_staerke=staerke,
                     protokoll_status="entfaellt", protokoll_beleg="")
            zahlen["ohne_richtung"] += 1
            continue

        if prot["status"] == "bestaetigt":
            widerspruch = entschieden and regel_wert is not None and prot["wert"] != regel_wert
            if widerspruch:
                zahlen["konflikt"] += 1
                konflikte.append({
                    "schluessel": schluessel, "titel": r.get("titel"),
                    "inverted_note": r.get("inverted_note"), "ja": ja, "nein": nein,
                    "regel_wert": regel_wert, "regel_grund": regel_grund,
                    "regel_staerke": staerke, "protokoll_wert": prot["wert"],
                    "beleg": prot["beleg"],
                })
            else:
                zahlen["bestaetigt"] += 1
            r.update(ja_ist_zustimmung=prot["wert"], herkunft="protokoll",
                     geprüft=True, regel_staerke=staerke,
                     begruendung=(regel_grund if not widerspruch else
                                  f"Regel sagte {regel_wert} ({regel_grund}); "
                                  f"Wortprotokoll korrigiert auf {prot['wert']}"),
                     protokoll_status=("bestaetigt" if not widerspruch else "korrigiert"),
                     protokoll_beleg=prot["beleg"])
            continue

        # Sachtitel ohne Antragsteller: entschieden per Konvention vom
        # 01.09.2026. Abgestimmt wird über den Änderungsantrag aus dem Rat,
        # ein Ja stützt die Fassung von Kommission oder Regierung und gilt
        # darum nicht als Zustimmung. Das Protokoll belegt das Ergebnis, die
        # Richtung folgt aus der Konvention.
        if prot["status"] == "titel_ohne_akteur":
            r.update(ja_ist_zustimmung=regel_wert, herkunft="konvention",
                     geprüft=True, regel_staerke=staerke,
                     begruendung=f"{regel_grund}. Sachtitel ohne Antragsteller, "
                                 "Richtung nach Konvention für Sachtitel.",
                     protokoll_status="konvention", protokoll_beleg=prot["beleg"])
            zahlen["konvention"] += 1
            continue

        # Protokoll klärt nicht: Regel bleibt vorläufig stehen, Fall kommt
        # auf die Prüfliste.
        if r.get("herkunft") == "manuell":
            zahlen["manuell"] += 1
            continue
        r.update(ja_ist_zustimmung=regel_wert if entschieden else None,
                 begruendung=regel_grund, herkunft="regel" if entschieden else "offen",
                 geprüft=bool(entschieden), regel_staerke=staerke,
                 protokoll_status=prot["status"], protokoll_beleg=prot["beleg"])
        zahlen["ungeprueft"] += 1
        offene.append({
            "schluessel": schluessel, "sitzung": r["sitzung"], "nr": r["nr"],
            "titel": r.get("titel"), "inverted_note": r.get("inverted_note"),
            "ja": ja, "nein": nein, "regel_wert": regel_wert,
            "regel_grund": regel_grund, "regel_staerke": staerke,
            "protokoll_status": prot["status"], "protokoll_hinweis": prot["hinweis"],
            "beleg": prot["beleg"],
        })

    gesamt = len(rows)
    print(f"{gesamt} Umkehrfälle\n")
    print("Regelwerk")
    print(f"  stark entschieden        {zahlen['regel_stark']:4d}")
    print(f"  schwach entschieden      {zahlen['regel_schwach']:4d}   ← die Zweifelsfälle")
    print(f"  nicht entscheidbar       {zahlen['regel_offen']:4d}")
    if mit_protokoll:
        print("\nGegenprobe am Wortprotokoll")
        print(f"  eindeutig belegt         {zahlen['prot_bestaetigt']:4d}")
        print(f"    davon bestätigt        {zahlen['bestaetigt']:4d}")
        print(f"    davon korrigiert       {zahlen['konflikt']:4d}")
        print(f"  Sachtitel ohne Akteur    {zahlen['prot_titel_ohne_akteur']:4d}"
              "   ← Ergebnis belegt, Richtung nicht")
        print(f"  keine Fundstelle         {zahlen['prot_keine_fundstelle']:4d}")
        print(f"  Gegenstand unklar        {zahlen['prot_objekt_unklar']:4d}")
        print(f"  mehrdeutig               {zahlen['prot_mehrdeutig']:4d}")
        print(f"  kein Protokolltext       {zahlen['prot_kein_text']:4d}")
        belegt = zahlen["prot_bestaetigt"]
        if belegt:
            print(f"\n  Trefferquote {belegt/gesamt*100:.1f} %, "
                  f"davon {zahlen['konflikt']/belegt*100:.1f} % Korrekturen am Regelwerk")
    print(f"\nOhne Richtung (Ausmehrung) {zahlen['ohne_richtung']:4d}")
    print(f"Sachtitel per Konvention  {zahlen['konvention']:4d}")
    print(f"Auf der Prüfliste          {zahlen['ungeprueft']:4d}")
    if zahlen["manuell"]:
        print(f"Von Hand entschieden       {zahlen['manuell']:4d}")

    if konflikte and ("--konflikte" in sys.argv or len(konflikte) <= 12):
        print(f"\nKorrekturen durch das Protokoll ({len(konflikte)}):")
        for k in konflikte[: (None if "--konflikte" in sys.argv else 12)]:
            print(f"\n  {k['schluessel']}")
            print(f"    Titel   : {kurz(k['titel'] or '(leer)')}")
            print(f"    Hinweis : {kurz(k['inverted_note'] or '')}")
            print(f"    Regel   : {k['regel_wert']} ({k['regel_staerke']}) "
                  f"{kurz(k['regel_grund'], 60)}")
            print(f"    Protokoll: {k['protokoll_wert']} | {k['ja']} Ja : {k['nein']} Nein")
            print(f"    Beleg   : {kurz(k['beleg'], 150)}")

    if "--apply" in sys.argv:
        json.dump(daten, open(MAPPING, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        pruefliste_schreiben(offene)
        print(f"\n{MAPPING.name} und {PRUEFLISTE.name} geschrieben.")
    else:
        print("\n(Probelauf, nichts geschrieben. Mit --apply schreiben.)")


if __name__ == "__main__":
    main()

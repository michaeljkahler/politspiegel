#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Begründungen für «Wer stimmt wie ich» aus den Wortprotokollen
==============================================================
Zu jeder Matching-Frage wird die zugehörige Debatte im Wortprotokoll gesucht
und daraus je ein Votum belegt, das für die Vorlage sprach, und eines, das
dagegen sprach.

Der Trick, der das rigoros macht: Wir wissen aus dem Excel, wie jedes
Ratsmitglied bei genau dieser Abstimmung gestimmt hat. Wer im Protokoll spricht
und danach dafür stimmt, hat dafür argumentiert. Es braucht also keine
Auslegung des Inhalts, die Stimmabgabe belegt die Seite.

Die Zitate werden **anonymisiert** ausgegeben: kein Name, keine Fraktion. Es
geht um das Argument, nicht darum, wer es vorgetragen hat.

Zusätzlich wird die Eröffnungspassage gesichert, mit der das Geschäft
vorgestellt wurde. Sie ist die Grundlage für die neutrale Zusammenfassung, die
von Hand in data/frage_begruendungen.json ergänzt wird.

Ausführen:
    python3 scripts/frage_begruendungen.py           # Bericht, schreibt nichts
    python3 scripts/frage_begruendungen.py --apply   # schreibt die Rohdaten
"""

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ZIEL = DATA / "frage_begruendungen.json"

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build3                                                     # noqa: E402
import umkehr_regeln as U                                         # noqa: E402

# «Markus Müller (SVP):», «Regierungsrat Marcel Montanari (FDP):»
SPRECHER = re.compile(
    r"(?:^|\s)((?:[A-ZÄÖÜ][\wäöüéèàç\-\.]+\s+){0,3}"
    r"[A-ZÄÖÜ][\wäöüéèàç\-\.]+)\s*"
    r"\(([A-ZÄÖÜ][\wÄÖÜäöü\s\-\./]{1,22})\)\s*:")

# Traktandenwechsel im Protokoll
TRAKTANDUM = re.compile(r"\*\s*\d{1,2}\.\s")

# Sätze, die nichts zur Sache sagen
FLOSKEL = re.compile(
    r"^(?:Die Wortmeldungen|Das Wort wird nicht|Rückkommen wird nicht|"
    r"Wir kommen zur|Besten Dank|Vielen Dank|Damit ist|Es freut mich|"
    r"Zur Traktandenliste|Bevor wir|Wir stimmen|Abstimmung|Ich danke)", re.I)

# Wörter, an denen ein Argument erkennbar ist
ARGUMENT = re.compile(
    r"\b(?:weil|damit|deshalb|darum|denn|weshalb|Grund|Gründe|führt dazu|"
    r"bedeutet|Folge|Kosten|Franken|Nutzen|Wirkung|Vorteil|Nachteil|Risiko|"
    r"notwendig|sinnvoll|unnötig|Aufgabe des Kantons|bitte Sie)\b", re.I)

# Rückgriffe auf andere Ratsmitglieder: das sind Repliken, keine eigenständigen
# Argumente, und sie widersprechen der Anonymisierung
NENNT_PERSON = re.compile(
    r"\b(?:Kantonsr[äa]tin|Kantonsrat|Regierungsr[äa]tin|Regierungsrat|"
    r"Kommissionspr[äa]sident(?:in)?|Frau|Herr)\s+[A-ZÄÖÜ][\wäöüéèà\-]+", re.I)

# Verfahrensrede statt Sachrede
VERFAHREN = re.compile(
    r"\b(?:Ordnungsantrag|Traktandenliste|Wortmeldung|Rückkommen|"
    r"zweite Lesung|Stimmenz[äa]hler|Anwesenheitskontrolle|Protokoll)\b", re.I)

MIN_ZITAT = 120       # kürzere Voten tragen selten ein Argument
MAX_ZITAT = 430
MIN_BEITRAG = 220     # so lang muss eine Wortmeldung sein, um zu zählen


def flach(s):
    return re.sub(r"\s+", " ", s or "").strip()


def sprecherzuege(text):
    """Alle Wortmeldungen eines Protokollabschnitts als (Name, Partei, Text)."""
    treffer = list(SPRECHER.finditer(text))
    raus = []
    for i, m in enumerate(treffer):
        ende = treffer[i + 1].start() if i + 1 < len(treffer) else len(text)
        raus.append({
            "name": flach(m.group(1)),
            "partei": flach(m.group(2)),
            "text": flach(text[m.end():ende]),
            "pos": m.start(),
        })
    return raus


def nachname_von(name):
    """Der letzte grossgeschriebene Bestandteil ist der Nachname.

    Das Protokoll setzt Ämter davor («Kantonsratspräsidentin Eva Neumann»),
    die hier wegfallen müssen.
    """
    teile = [t for t in name.split() if t and t[0].isupper()]
    return teile[-1] if teile else ""


def debattenfenster(text, treffer_pos):
    """Der Abschnitt vor dem Resultatsatz, zurück bis zum Traktandenwechsel."""
    anfang = 0
    for m in TRAKTANDUM.finditer(text, 0, treffer_pos):
        anfang = m.end()
    # Nicht weiter als 22 000 Zeichen zurück, sonst wird es beliebig
    return text[max(anfang, treffer_pos - 22000):treffer_pos]


def erster_satz(t, n=MAX_ZITAT):
    """Erster sinntragender Teil einer Wortmeldung."""
    t = flach(t)
    # Seitenzahlen und Kopfzeilen entfernen
    t = re.sub(r"\b\d{3,4}\s+Kantonsrat Schaffhausen\b", " ", t)
    t = re.sub(r"Protokoll der \d+\. Sitzung vom [^\d]*\d{4}\s*\d*", " ", t)
    t = flach(t)
    saetze = re.split(r"(?<=[a-zäöüß»)\"])\.\s+(?=[A-ZÄÖÜ«])", t)
    raus = ""
    for s in saetze:
        s = s.strip()
        if not s or FLOSKEL.match(s):
            continue
        # Punkt wieder einsetzen, den das Trennen entfernt hat
        kandidat = (raus.rstrip(".") + ". " + s).strip() if raus else s
        if len(kandidat) > n:
            break
        raus = kandidat
        if len(raus) >= MIN_ZITAT:
            break
    return raus.strip(" .") + "." if raus else ""


def stimme_von(sess, idx, nachname, inv):
    """Wie das Ratsmitglied bei dieser Abstimmung gestimmt hat, richtungskorrigiert."""
    kandidaten = [m for m in sess["members"]
                  if m["nachname"].lower() == nachname.lower()]
    if len(kandidaten) != 1:
        return None                                   # mehrdeutig oder unbekannt
    roh = kandidaten[0]["votes"][idx] if idx < len(kandidaten[0]["votes"]) else None
    if roh not in ("Ja", "Nein"):
        return None
    dafuer = (roh == "Nein") if inv else (roh == "Ja")
    return "dafuer" if dafuer else "dagegen"


def eroeffnung(zuege):
    """Die Passage, mit der das Geschäft vorgestellt wurde.

    Das übernimmt in aller Regel der Kommissionspräsident oder ein Mitglied des
    Regierungsrats, und zwar zu Beginn der Debatte. Sie ist die sachlichste
    Beschreibung im ganzen Protokoll und darum die Grundlage für die neutrale
    Zusammenfassung.
    """
    vorne = zuege[:6]
    for z in vorne:
        if re.search(r"Kommissionspr[äa]sident|Regierungsr[äa]tin|Regierungsrat|"
                     r"kommission", z["name"], re.I):
            t = erster_satz(z["text"], 900)
            if len(t) >= MIN_ZITAT:
                return t
    for z in vorne:
        if len(z["text"]) < MIN_BEITRAG:
            continue
        t = erster_satz(z["text"], 900)
        if len(t) >= MIN_ZITAT:
            return t
    return ""


def guete(text):
    """Wie brauchbar eine Wortmeldung als Begründung ist.

    Gesucht sind eigenständige Sachargumente. Repliken auf andere
    Ratsmitglieder, Verfahrensreden und blosse Zwischenfragen fallen ab.
    """
    t = flach(text)
    if len(t) < MIN_BEITRAG:
        return -1
    punkte = min(len(t), 1400) / 200.0
    punkte += 2.0 * len(ARGUMENT.findall(t)) ** 0.5
    punkte -= 3.0 * len(NENNT_PERSON.findall(t))
    punkte -= 2.0 * len(VERFAHREN.findall(t))
    punkte -= 2.5 * t.count("?")
    return punkte


def sammeln():
    d = build3.sitzungen_lesen()
    umkehr = build3.umkehr_lesen()
    M = build3.matching_payload(d, umkehr)
    if not M:
        print("Keine Matching-Fragen gefunden.")
        return []

    stimmen, sess_prot = U.sitzungsdaten()
    nach_sitzung = {s["sitzung"]: s for s in d["sessions"]}

    raus = []
    for f in M["fragen"]:
        sess = nach_sitzung.get(f["sitzung"])
        eintrag = {"sitzung": f["sitzung"], "nr": f["nr"], "kurz": f["kurz"],
                   "thema": f["thema"], "geschaeft": f["geschaeft"],
                   "eroeffnung": "", "dafuer": "", "dagegen": "",
                   "zusammenfassung": None, "status": ""}
        if not sess:
            eintrag["status"] = "Sitzung nicht gefunden"
            raus.append(eintrag); continue

        idx = next((i for i, v in enumerate(sess["votes"])
                    if str(v["nr"]) == str(f["nr"])), None)
        if idx is None:
            eintrag["status"] = "Abstimmung nicht gefunden"
            raus.append(eintrag); continue

        ja, nein = stimmen.get(f"{f['sitzung']} #Nr{f['nr']}", (0, 0))
        text = U.protokolltext(f["sitzung"], sess_prot)
        if not text:
            eintrag["status"] = "kein Protokolltext"
            raus.append(eintrag); continue

        # Resultatsatz zu genau diesem Stimmenverhältnis suchen
        pos = None
        for p, a, b, satz in U.fundstellen(text):
            if {a, b} == {ja, nein}:
                pos = p
                break
        if pos is None:
            eintrag["status"] = "Resultatsatz nicht gefunden"
            raus.append(eintrag); continue

        fenster = debattenfenster(text, pos)
        zuege = sprecherzuege(fenster)
        eintrag["eroeffnung"] = eroeffnung(zuege)

        # Wortmeldungen den Stimmen zuordnen und je Seite die sachlichste nehmen
        inv = bool(sess["votes"][idx].get("richtung_invertiert"))
        nach_seite = {"dafuer": [], "dagegen": []}
        for z in zuege:
            seite = stimme_von(sess, idx, nachname_von(z["name"]), inv)
            if seite:
                nach_seite[seite].append(z)
        for seite, liste in nach_seite.items():
            liste.sort(key=lambda z: -guete(z["text"]))
            # Erst streng: nur klar sachliche Wortmeldungen. Findet sich nichts,
            # eine mildere Runde, die nur noch verlangt, dass das Zitat selbst
            # keine Person nennt.
            for schwelle in (0.0, -99.0):
                for z in liste:
                    if guete(z["text"]) <= schwelle:
                        continue
                    zitat = erster_satz(z["text"])
                    if len(zitat) < MIN_ZITAT or NENNT_PERSON.search(zitat):
                        continue
                    eintrag[seite] = zitat
                    break
                if eintrag[seite]:
                    break

        gefunden = sum(1 for s in ("dafuer", "dagegen") if eintrag[s])
        eintrag["status"] = ("beide Seiten belegt" if gefunden == 2 else
                             "eine Seite belegt" if gefunden == 1 else
                             "keine Wortmeldung zuordenbar")
        eintrag["sprecher_gesamt"] = len(zuege)
        raus.append(eintrag)
    return raus


def main():
    daten = sammeln()
    import collections
    st = collections.Counter(e["status"] for e in daten)
    print(f"\n{len(daten)} Fragen ausgewertet")
    for k, n in st.most_common():
        print(f"  {n:3d}  {k}")
    mit_er = sum(1 for e in daten if e["eroeffnung"])
    print(f"  {mit_er:3d}  mit Eröffnungspassage für die Zusammenfassung")

    if "--apply" in sys.argv:
        # Von Hand ergänzte Zusammenfassungen nicht überschreiben
        alt = {}
        if ZIEL.exists():
            for e in json.loads(ZIEL.read_text(encoding="utf-8"))["fragen"]:
                if e.get("zusammenfassung"):
                    alt[f"{e['sitzung']}#{e['nr']}"] = e["zusammenfassung"]
        behalten = 0
        for e in daten:
            k = f"{e['sitzung']}#{e['nr']}"
            if k in alt:
                e["zusammenfassung"] = alt[k]; behalten += 1
        ZIEL.write_text(json.dumps(
            {"hinweis": ("Belege aus den Wortprotokollen für die Fragen im Reiter "
                         "«Wer stimmt wie ich». Die Zitate sind anonymisiert: die "
                         "Seite ist durch die Stimmabgabe der sprechenden Person "
                         "belegt, der Name gehört nicht zur Sache. Das Feld "
                         "zusammenfassung wird von Hand gefüllt und bleibt bei "
                         "einem erneuten Lauf erhalten."),
             "fragen": daten}, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n{ZIEL.name} geschrieben, {behalten} Zusammenfassungen behalten.")
    else:
        print("\n(Probelauf, nichts geschrieben. Mit --apply schreiben.)")
        for e in daten[:3]:
            print("\n──", e["kurz"][:70])
            print("   Status   :", e["status"], f"({e.get('sprecher_gesamt', 0)} Wortmeldungen)")
            print("   Eröffnung:", (e["eroeffnung"] or "—")[:160])
            print("   Dafür    :", (e["dafuer"] or "—")[:160])
            print("   Dagegen  :", (e["dagegen"] or "—")[:160])


if __name__ == "__main__":
    main()

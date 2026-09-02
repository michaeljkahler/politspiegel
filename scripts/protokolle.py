#!/usr/bin/env python3
"""
Wortprotokolle laden und Abstimmungen darin verorten
====================================================
Die Abstimmungs-Excel nennen bei rund einem Viertel der Abstimmungen nur
«Antrag M. Pfalzgraf», ohne Geschäft und ohne Inhalt. Worum es ging, steht im
Wortprotokoll. Dieses Skript holt die verlinkten Protokoll-PDFs, zieht den Text
heraus und hängt an jede Abstimmung

    traktandum   die Überschrift des Traktandums, unter dem sie stattfand
    kontext      den Protokollsatz zur Abstimmung ("Dem Antrag von ... wird
                 mit 31 : 23 Stimmen zugestimmt")

Gefunden wird die Stelle über das Stimmenverhältnis: die Kombination
Ja : Nein ist innerhalb eines Sitzungstags fast immer eindeutig.

Ausführen:
    python3 scripts/protokolle.py --laden     # PDFs holen, Text zwischenspeichern
    python3 scripts/protokolle.py             # Bericht ohne zu schreiben
    python3 scripts/protokolle.py --apply     # Text in all_sessions.json eintragen
"""
import json
import re
import subprocess
import sys
import tempfile
import concurrent.futures as cf
from collections import Counter
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SESSIONS = DATA / "all_sessions.json"
CACHE = DATA / "protokolle"          # PDFs und extrahierter Text
CACHE.mkdir(parents=True, exist_ok=True)
WORKERS = 6
UA = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")}

# Ergebnissatz einer Abstimmung
ERGEBNIS = re.compile(
    r"[^.\n]{0,220}?\bmit\s+(\d{1,2})\s*:\s*(\d{1,2})\s+Stimmen[^.]{0,160}\.", re.S)

# Fenster der Debatte vor dem Ergebnis, aus dem die Stichwörter stammen
FENSTER = 3000
# Wörter, die in jedem Protokoll vorkommen und nichts über das Thema sagen
STOPP = set("""
kantonsrat kantonsrates kantonsrätin kantonsräte kantonsrats schaffhausen schaffhauser
regierungsrat regierungsrats regierungsrates fraktion fraktionen kommission kommissionen
präsident präsidentin vizepräsident sitzung sitzungen protokoll abstimmung abstimmungen
antrag anträge antrages vorlage vorlagen bericht berichte stimmen stimme enthaltung
enthaltungen zugestimmt abgelehnt beschluss beschlüsse gesetz gesetzes gesetze artikel
absatz ziffer damit dieser diese dieses jenes welche welcher dass nicht auch noch schon
sehr mehr weniger viele vielen wenig andere anderen ersten zweiten dritten heute morgen
kollege kollegin kolleginnen kollegen danke bitte müssen sollen können wollen werden
worden wurde wurden haben hatte hatten geht gehen sagen sagte gesagt sehen finden
denke meine unsere meiner unserer ihrer seiner bereits jedoch allerdings deshalb darum
folgende folgenden nämlich beispielsweise insbesondere grundsätzlich möglich möglichkeit
frage fragen antwort punkt punkte thema themen sache jahren jahre jahr million millionen
franken prozent bezüglich betreffend sowie ohne über unter durch gegen zwischen
lesung eintreten detailberatung schlussabstimmung ordnungsantrag postulat motion
interpellation erheblich erklärung abschreibung wortprotokoll
januar februar märz april juni juli august september oktober november dezember
amtsdruckschrift kommissionsvorlage spezialkommission geschäft geschäfte geschäften
ihnen vorberatung erstgewählter details stellung seite seiten minute minuten
vorstoss vorstösse eingang eingänge traktandum traktanden traktandenliste
votum voten fassung wortlaut ergänzung änderungen buchstabe
""".split())


def _txt_pfad(url):
    return CACHE / (url.rsplit("/", 1)[-1] + ".txt")


def laden(url, name):
    """PDF holen und Text extrahieren, beides im Cache."""
    ziel = _txt_pfad(url)
    if ziel.exists():
        return ziel, "Cache"
    # PDF nur zwischenlagern, dauerhaft gespeichert wird allein der Text
    pdf = Path(tempfile.gettempdir()) / (url.rsplit("/", 1)[-1] + ".pdf")
    try:
        r = requests.get(url, timeout=180, headers=UA)
        r.raise_for_status()
    except Exception as e:
        return None, f"Fehler: {e}"
    if not r.content[:5].startswith(b"%PDF"):
        return None, "kein PDF"
    pdf.write_bytes(r.content)
    try:
        text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                              capture_output=True, text=True).stdout
    finally:
        pdf.unlink(missing_ok=True)
    if len(text) < 2000:
        return None, "Text zu kurz"
    ziel.write_text(text, encoding="utf-8")
    return ziel, "geladen"


def alle_laden(daten):
    aufgaben = {}
    for s in daten["sessions"]:
        for p in (s.get("protokolle") or []):
            aufgaben[p["url"]] = p["name"]
    print(f"{len(aufgaben)} Protokoll-Links", flush=True)
    stat = Counter()
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futs = {pool.submit(laden, u, n): u for u, n in aufgaben.items()}
        for i, fut in enumerate(cf.as_completed(futs), 1):
            _pfad, wie = fut.result()
            stat[wie.split(":")[0]] += 1
            if i % 40 == 0:
                print(f"   ... {i}/{len(aufgaben)}", flush=True)
    print("  ", dict(stat), flush=True)


def protokolltext(s):
    """Alle Protokolltexte einer Sitzung aneinandergehängt."""
    teile = []
    for p in (s.get("protokolle") or []):
        pfad = _txt_pfad(p["url"])
        if pfad.exists():
            teile.append(pfad.read_text(encoding="utf-8"))
    return "\n".join(teile)


def namen_der_mitglieder(daten):
    """Alle Vor- und Nachnamen, die je im Rat sassen. Im Protokoll fällt bei
    jedem Votum der Name des Sprechenden, das sagt nichts über das Thema."""
    namen = set()
    for s in daten["sessions"]:
        for m in s["members"]:
            for teil in re.split(r"[\s-]+", f"{m['nachname']} {m['vorname']}"):
                if len(teil) > 3:
                    namen.add(teil.lower())
    return namen


def stichworte(text, pos, namen=frozenset(), anzahl=16):
    """Häufigste inhaltliche Wörter aus der Debatte vor der Abstimmung.

    Die Überschriften der Traktanden sind in den Protokollen zu uneinheitlich
    formatiert, um sie verlässlich zu erkennen. Die Debatte davor ist dagegen
    eine gute Quelle: worüber gestritten wurde, steht dort oft und oft.
    Einmalige Erwähnungen fallen weg, damit Nebensätze nicht zum Thema werden."""
    fenster = text[max(0, pos - FENSTER):pos]
    zaehler = Counter()
    for w in re.findall(r"[A-ZÄÖÜ][a-zäöüß]{4,}", fenster):   # deutsche Substantive
        wl = w.lower()
        if wl in STOPP or wl in namen:
            continue
        zaehler[wl] += 1
    return [w for w, n in zaehler.most_common(anzahl) if n >= 2]


def tally(s, idx):
    t = {"Ja": 0, "Nein": 0, "Enth": 0}
    for m in s["members"]:
        x = m["votes"][idx]
        if x in t:
            t[x] += 1
    return t


def verorten(s, text):
    """Je Abstimmung (Position im Text, Ergebnissatz) über das Stimmenverhältnis.

    Die Zuordnung läuft der Reihe nach vorwärts: die Abstimmungen einer Sitzung
    stehen im Protokoll in derselben Folge wie in der Excel. Ohne diese Regel
    landet ein Stimmenverhältnis, das an zwei Stellen vorkommt, leicht beim
    falschen Geschäft."""
    trefferliste = []
    for m in ERGEBNIS.finditer(text):
        trefferliste.append((int(m.group(1)), int(m.group(2)), m.start(),
                             re.sub(r"\s+", " ", m.group(0)).strip()))
    zuordnung = {}
    letzte_pos = -1
    for idx, v in enumerate(s["votes"]):
        t = tally(s, idx)
        # Ja:Nein, wie im Protokoll geschrieben; die Reihenfolge kann kippen,
        # weil das Protokoll das Ergebnis nennt, nicht die Ja-Spalte
        passend = [x for x in trefferliste
                   if (x[0], x[1]) in ((t["Ja"], t["Nein"]), (t["Nein"], t["Ja"]))]
        vorwaerts = [x for x in passend if x[2] > letzte_pos]
        kandidaten = vorwaerts or passend
        if not kandidaten:
            continue
        treffer = kandidaten[0]
        letzte_pos = treffer[2]
        zuordnung[idx] = (treffer[2], treffer[3])
    return zuordnung


def main():
    daten = json.load(open(SESSIONS, encoding="utf-8"))
    if "--laden" in sys.argv:
        alle_laden(daten)

    namen = namen_der_mitglieder(daten)
    stat = Counter()
    for s in daten["sessions"]:
        text = protokolltext(s)
        if not text:
            stat["ohne Protokolltext"] += len(s["votes"])
            continue
        zuo = verorten(s, text)
        worte_je_idx = {idx: stichworte(text, pos, namen)
                        for idx, (pos, _s) in zuo.items()}

        for idx, v in enumerate(s["votes"]):
            if idx in zuo:
                stat["verortet"] += 1
                if "--apply" in sys.argv:
                    v["kontext"] = zuo[idx][1][:400]
                    v["stichworte"] = worte_je_idx[idx]
                    v["kontext_quelle"] = "protokoll"
                continue
            # Lücke: Stichwörter der nächstgelegenen getroffenen Abstimmung
            # übernehmen. Abstimmungen einer Beratung folgen aufeinander, der
            # Nachbar betrifft darum fast immer dasselbe Geschäft.
            nachbarn = sorted(worte_je_idx, key=lambda j: (abs(j - idx), j > idx))
            if nachbarn and abs(nachbarn[0] - idx) <= 2:
                stat["Stichwörter vom Nachbarn"] += 1
                if "--apply" in sys.argv:
                    v["stichworte"] = worte_je_idx[nachbarn[0]]
                    v["kontext_quelle"] = "nachbar"
            else:
                stat["nicht verortet"] += 1
    gesamt = sum(len(s["votes"]) for s in daten["sessions"])
    print(f"{gesamt} Abstimmungen: " +
          ", ".join(f"{n} {k}" for k, n in stat.most_common()))

    if "--apply" in sys.argv:
        json.dump(daten, open(SESSIONS, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"{SESSIONS.name} geschrieben.")
    else:
        print("(Probelauf, nichts geschrieben. Mit --apply schreiben.)")


if __name__ == "__main__":
    main()

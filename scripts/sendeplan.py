#!/usr/bin/env python3
"""
Sendeplan für Metricool
=======================
Entscheid Michael vom 11. Oktober 2026, gilt ab 1. November 2026: Die 17 planbaren
Veröffentlichungen eines Kalendermonats (docs/KONZEPT_social-media.md, Abschnitt 1a)
verteilen sich gleichmässig über den ganzen Monat, rund alle 1,8 Tage eine. Bis Oktober
2026 liefen sie in Schüben nach jeder Sitzung; das Oktoberkontingent war am 11. Oktober
aufgebraucht, danach blieben die Kanäle drei Wochen leer.

Regeln
1. 17 Termine je Kalendermonat. Termin k (k = 0 bis 16) liegt am Tag
   1 + floor((k + 0.5) x T / 17), T = Anzahl Tage des Monats.
   November 2026: 1., 3., 5., 7., 8., 10., 12., 14., 16., 17., 19., 21., 23., 24., 26., 28., 30.
   Dezember 2026: 1., 3., 5., 7., 9., 11., 12., 14., 16., 18., 20., 21., 23., 25., 27., 29., 31.
2. Je Termin genau ein Beitrag, also eine Veröffentlichung in einem Netz.
   Uhrzeit: Bild und Karussell 09:00, Reel 16:00.
3. Reserve für kommende Sitzungen: Jede Kantonsratssitzung, die am Startdatum noch
   bevorsteht, hält die ersten 8 freien Termine ab dem zweiten Tag nach der Sitzung frei.
   Reihenfolge der Sitzungen nach Datum. So bleibt nach jeder Sitzung Platz für deren
   Reels und Karussell Teil 1 (2 Halbtage x 4 Beiträge).
4. Termine, an denen nichts anfällt, bleiben leer. Nichts wird nachgeschoben oder verdichtet.
5. Die 3 Reserveplätze des Kontingents sind keine Termine; sie belegt nur Michael.

Aufruf
    python3 scripts/sendeplan.py                        Termine dieses und des nächsten Monats
    python3 scripts/sendeplan.py --monat 2026-11        Termine eines Monats
    python3 scripts/sendeplan.py --frei --ab 2026-11-04 --belegt 2026-11-05,2026-11-07
        Freie Termine ab einem Datum (Folgetag des Laufs) bis Ende des Folgemonats, ohne
        belegte Tage und ohne die Reserve für kommende Sitzungen. --belegt nennt die Tage,
        an denen in Metricool schon ein Beitrag liegt (getScheduledPosts, Entwürfe
        eingeschlossen). --ab fehlt: morgen.
    --json  Ausgabe maschinenlesbar.

SITZUNGEN nachführen, sobald der Kantonsrat neue Sitzungsdaten publiziert (sh.ch).
"""
import argparse
import calendar
import json
import sys
from datetime import date, timedelta

TERMINE_JE_MONAT = 17
RESERVE_JE_SITZUNG = 8
# Sitzungstage des Kantonsrats Schaffhausen. Stand 11. Oktober 2026, nachführen.
SITZUNGEN = ["2026-11-02", "2026-11-16", "2026-11-30", "2026-12-14"]
ZEIT = {"bild": "09:00", "karussell": "09:00", "reel": "16:00"}
WT = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
REGEL = ("Sendeplan (seit 1.11.2026): 17 Termine je Monat, gleichmässig verteilt, je Termin ein Beitrag "
         "(ein Netz), Bild 09:00, Reel 16:00; 8 Termine nach jeder kommenden Sitzung bleiben frei.")


def termine(jahr, monat):
    t = calendar.monthrange(jahr, monat)[1]
    return [date(jahr, monat, 1 + int((k + 0.5) * t / TERMINE_JE_MONAT)) for k in range(TERMINE_JE_MONAT)]


def folgemonat(jahr, monat):
    return (jahr + 1, 1) if monat == 12 else (jahr, monat + 1)


def frei(ab, belegt=(), sitzungen=SITZUNGEN):
    """Freie Termine ab `ab` bis Ende des Folgemonats und die Reserve je kommender Sitzung."""
    j2, m2 = folgemonat(ab.year, ab.month)
    offen = [d for d in termine(ab.year, ab.month) + termine(j2, m2) if d >= ab and d not in set(belegt)]
    reserviert = {}
    for s in sorted(date.fromisoformat(x) for x in sitzungen):
        if s < ab:
            continue
        for d in [d for d in offen if d >= s + timedelta(days=2) and d not in reserviert][:RESERVE_JE_SITZUNG]:
            reserviert[d] = s
    return [d for d in offen if d not in reserviert], reserviert


def tag(d):
    return f"{WT[d.weekday()]} {d.strftime('%d.%m.%Y')}"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--monat", help="JJJJ-MM")
    ap.add_argument("--frei", action="store_true")
    ap.add_argument("--ab", help="JJJJ-MM-TT, Voreinstellung morgen")
    ap.add_argument("--belegt", default="", help="JJJJ-MM-TT,JJJJ-MM-TT,...")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.frei:
        ab = date.fromisoformat(a.ab) if a.ab else date.today() + timedelta(days=1)
        belegt = [date.fromisoformat(x.strip()) for x in a.belegt.split(",") if x.strip()]
        f, r = frei(ab, belegt)
        if a.json:
            print(json.dumps({"ab": ab.isoformat(), "frei": [d.isoformat() for d in f],
                              "reserviert": {d.isoformat(): s.isoformat() for d, s in r.items()},
                              "belegt": sorted(d.isoformat() for d in belegt if d >= ab)}, ensure_ascii=False, indent=1))
        else:
            print(REGEL)
            print(f"Ab {tag(ab)}:")
            print("  frei:       " + (", ".join(tag(d) for d in f) or "keine"))
            for s in sorted(set(r.values())):
                print(f"  reserviert für die Sitzung vom {s.strftime('%d.%m.%Y')}: " + ", ".join(tag(d) for d, x in r.items() if x == s))
            b = sorted(d for d in belegt if d >= ab)
            if b:
                print("  belegt:     " + ", ".join(tag(d) for d in b))
        letzte = max(date.fromisoformat(x) for x in SITZUNGEN)
        j2, m2 = folgemonat(ab.year, ab.month)
        if letzte < date(j2, m2, 1):
            print(f"Hinweis: SITZUNGEN in scripts/sendeplan.py reicht nur bis {letzte.strftime('%d.%m.%Y')}. "
                  "Sitzungsdaten auf sh.ch nachsehen und nachführen.", file=sys.stderr)
        return

    if a.monat:
        monate = [tuple(int(x) for x in a.monat.split("-"))]
    else:
        h = date.today()
        monate = [(h.year, h.month), folgemonat(h.year, h.month)]
    aus = {}
    for j, m in monate:
        aus[f"{j}-{m:02d}"] = [d.isoformat() for d in termine(j, m)]
        if not a.json:
            print(f"{j}-{m:02d}: " + ", ".join(tag(d) for d in termine(j, m)))
    if a.json:
        print(json.dumps(aus, indent=1))
    else:
        print(REGEL)


if __name__ == "__main__":
    main()

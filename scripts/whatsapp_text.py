#!/usr/bin/env python3
"""Beitragstext fuer den WhatsApp-Kanal nach einer Kantonsratssitzung.

WhatsApp-Kanaele haben keine Schnittstelle zum Posten; der Text wird von Hand
in den Kanal eingefuegt. Dieses Skript schreibt ihn aus den Daten, damit er
nach jeder Sitzung in derselben Form vorliegt und nichts von Hand gezaehlt
werden muss.

Aufruf aus der Projektwurzel:
    python3 scripts/whatsapp_text.py              # juengster Sitzungstag
    python3 scripts/whatsapp_text.py 24.08.2026   # bestimmter Sitzungstag

Ausgabe: der Text auf der Konsole und in output/whatsapp_<datum>.txt.

Inhalt: Sitzungstag, Zahl der namentlichen Abstimmungen, die knappsten
Entscheide (bis 4 Stimmen Unterschied, hoechstens drei), die Geschaefte des
Tages, Verweis in den Kantonsratsspiegel und auf den Livestream. Ergebnisse
stehen so, wie sie protokolliert sind (Ja : Nein); bei Umkehrabstimmungen
steht der Hinweis dazu.
"""

from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from prototyp import betreff, ueberschrift  # noqa: E402  dieselben Kurzformen wie im Kantonsratsspiegel

DATA = ROOT / "data"
OUT = ROOT / "output"
BASIS = "https://michaeljkahler.github.io/politspiegel/kantonsrat/"


def zaehlen(s, i):
    c = collections.Counter(m["votes"][i] for m in s["members"])
    return c.get("Ja", 0), c.get("Nein", 0), c.get("Enth", 0)


def kurz(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def main() -> int:
    d = json.loads((DATA / "all_sessions.json").read_text(encoding="utf-8"))
    yt = json.loads((DATA / "youtube_zuordnung.json").read_text(encoding="utf-8")) if (DATA / "youtube_zuordnung.json").exists() else {}
    wunsch = sys.argv[1] if len(sys.argv) > 1 and re.match(r"\d{2}\.\d{2}\.\d{4}", sys.argv[1]) else None
    tage = []
    for s in d["sessions"]:
        m = re.search(r"(\d{2}\.\d{2}\.\d{4})", s["sitzung"])
        if m:
            tage.append((m.group(1), s))
    datum = wunsch or tage[0][0]
    halb = [s for t, s in tage if t == datum]
    if not halb:
        print(f"Keine Sitzung am {datum}.")
        return 1
    halb.sort(key=lambda s: 0 if "Vormittag" in s["sitzung"] else 1)
    name = halb[0]["sitzung"].split(" · ")[0]
    n = sum(len(s["votes"]) for s in halb)
    knapp, geschaefte = [], []
    for s in halb:
        for i, v in enumerate(s["votes"]):
            ja, nein, enth = zaehlen(s, i)
            g = betreff(v.get("geschaeft")) or kurz(v.get("titel") or "")
            if g and g not in geschaefte:
                geschaefte.append(g)
            if ja and nein and abs(ja - nein) <= 4:
                titel = ueberschrift(v)[0]
                note = kurz(v.get("inverted_note") or "")
                knapp.append((abs(ja - nein), f"{titel}: {ja} : {nein}" + (f" ({note})" if v.get("richtung_invertiert") and note else "")))
    knapp.sort()
    video = next((yt[s["sitzung"]]["video"] for s in halb if s["sitzung"] in yt), None)

    z = [f"Kantonsrat Schaffhausen, {name}, {datum}",
         "",
         f"{n} namentliche Abstimmungen, alle Einzelstimmen im Kantonsratsspiegel:",
         BASIS + "#s=" + __import__("urllib.parse").parse.quote(halb[0]["sitzung"], safe=""),
         ""]
    if knapp:
        z.append("Knapp entschieden:")
        z += [f"{i}. {t}" for i, (_, t) in enumerate(knapp[:3], 1)]
        z.append("")
    if geschaefte:
        z.append("Geschäfte des Tages:")
        z += [f"{i}. {g}" for i, g in enumerate(geschaefte[:6], 1)]
        z.append("")
    if video:
        z.append(f"Livestream der Sitzung: https://www.youtube.com/watch?v={video}")
        z.append("")
    z.append("Quelle: Parlamentsdienste Kanton Schaffhausen (Excel-Publikation), Wortprotokoll. Aufbereitung ohne Gewähr; Fehler bitte melden.")
    text = "\n".join(z)
    OUT.mkdir(exist_ok=True)
    ziel = OUT / f"whatsapp_{datum.replace('.', '-')}.txt"
    ziel.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"\n-- geschrieben: {ziel.relative_to(ROOT)} ({len(text)} Zeichen)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

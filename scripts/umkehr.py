#!/usr/bin/env python3
"""
Richtungskorrektur der Umkehrabstimmungen
=========================================
Manche Abstimmungen tragen den Hinweis "Ja bedeutet ...", bei dem ein Ja im
Rat nicht die inhaltliche Zustimmung zum Antrag bedeutet, sondern das Gegenteil
(z. B. Zustimmung zur Kommissionsfassung statt zum Minderheitsantrag). Fürs
Matching und für aggregierte Kennzahlen muss "Ja" aber eine einheitliche
inhaltliche Bedeutung haben.

Dieses Skript erzeugt eine EDITIERBARE, menschlich geprüfte Tabelle der
Umkehrfälle und schreibt daraus ein Flag in all_sessions.json. Die Rohstimmen
der Mitglieder werden nie verändert; nur ein zusätzliches Feld je Abstimmung
markiert, ob die Richtung invertiert ist. Die Auswertung (Matching, Kennzahlen)
berücksichtigt dieses Flag.

Ablauf (analog themen.py, mit menschlicher Freigabe):
  1. python3 scripts/umkehr.py          -> erzeugt/aktualisiert data/umkehr_zuordnung.json
  2. Tabelle prüfen: Feld "ja_ist_zustimmung" setzen, dann "geprüft": true
     - true  = Ja bedeutet inhaltliche Zustimmung zum Antrag (keine Umkehr)
     - false = Ja bedeutet Ablehnung des Antrags (echte Umkehr; die inhaltliche
               Zustimmung entspricht dann einem Nein im Rat)
     Grundlage der Prüfung ist das Wortprotokoll der Sitzung.
  3. python3 scripts/umkehr.py --apply  -> schreibt "richtung_invertiert" je Abstimmung
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SESSIONS = DATA / "all_sessions.json"
MAPPING  = DATA / "umkehr_zuordnung.json"


def schluessel(sitzung, nr):
    """Stabiler Schlüssel je Abstimmung (Sitzungslabel + Nummer)."""
    return f"{sitzung} #Nr{nr}"


def collect(data):
    faelle = []
    for s in data["sessions"]:
        for v in s["votes"]:
            if v.get("inverted_note"):
                faelle.append((s, v))
    return faelle


def build_mapping():
    data = json.load(open(SESSIONS))
    faelle = collect(data)

    existing = {}
    if Path(MAPPING).exists():
        for row in json.load(open(MAPPING))["zuordnung"]:
            existing[row["schluessel"]] = row

    rows = []
    for s, v in faelle:
        key = schluessel(s["sitzung"], v["nr"])
        if key in existing and existing[key].get("geprüft"):
            row = existing[key]                      # geprüfte Zuordnung bewahren
        else:
            row = {
                "schluessel": key,
                "sitzung": s["sitzung"],
                "nr": v["nr"],
                "titel": v.get("titel"),
                "geschaeft": (v.get("geschaeft") or "")[:200],
                "inverted_note": (v.get("inverted_note") or "").strip(),
                "ja_ist_zustimmung": None,           # true/false, bitte prüfen
                "geprüft": False,
            }
        rows.append(row)

    out = {
        "hinweis": ("ja_ist_zustimmung: true = Ja ist Zustimmung zum Antrag, "
                    "false = Ja ist Ablehnung (Umkehr). Grundlage ist das "
                    "Wortprotokoll. Nach der Prüfung geprüft=true setzen."),
        "zuordnung": rows,
    }
    json.dump(out, open(MAPPING, "w"), ensure_ascii=False, indent=1)
    geprueft = sum(1 for r in rows if r.get("geprüft"))
    print(f"{MAPPING.name} geschrieben: {len(rows)} Umkehrfälle, davon geprüft {geprueft}.")
    if geprueft < len(rows):
        print(f"  offen: {len(rows) - geprueft} Fälle "
              f"(ja_ist_zustimmung + geprüft im JSON setzen).")


def apply_mapping():
    data = json.load(open(SESSIONS))
    mp = json.load(open(MAPPING))
    lookup = {r["schluessel"]: r for r in mp["zuordnung"]}

    n_inv = n_geklaert = 0
    for s in data["sessions"]:
        for v in s["votes"]:
            if not v.get("inverted_note"):
                v["richtung_invertiert"] = False      # kein Umkehrhinweis
                continue
            n_inv += 1
            row = lookup.get(schluessel(s["sitzung"], v["nr"]))
            if row and row.get("geprüft") and row.get("ja_ist_zustimmung") is not None:
                v["richtung_invertiert"] = (row["ja_ist_zustimmung"] is False)
                n_geklaert += 1
            else:
                v["richtung_invertiert"] = None       # markiert, aber noch offen
    json.dump(data, open(SESSIONS, "w"), ensure_ascii=False, indent=1)
    print(f"{SESSIONS.name}: {n_inv} Umkehrfälle markiert, davon {n_geklaert} richtungsgeklärt.")


if __name__ == "__main__":
    if "--apply" in sys.argv:
        apply_mapping()
    else:
        build_mapping()

#!/usr/bin/env python3
"""
Themen-Zuordnung für Kantonsrats-Abstimmungen
=============================================
Ordnet jedes Geschäft einer der 9 Hauptgruppen der Schaffhauser
Rechtssammlung (rechtsbuch.sh.ch) zu, anhand von Stichwörtern im
Geschäftstitel. Erzeugt eine EDITIERBARE Tabelle themen_zuordnung.json,
die manuell geprüft und korrigiert werden kann.

Ablauf:
  1. python3 themen.py            -> erzeugt/aktualisiert themen_zuordnung.json
     - bestehende manuelle Zuordnungen ("geprüft": true) bleiben erhalten
     - neue Geschäfte kommen mit automatischem Vorschlag dazu ("geprüft": false)
  2. themen_zuordnung.json von Hand prüfen: "gruppe" korrigieren, "geprüft": true
  3. python3 themen.py --apply    -> schreibt die Tags in all_sessions.json

Die 9 Hauptgruppen (Stufe 1 der Systematik):
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent    # Projektwurzel (scripts/ liegt darunter)
DATA = ROOT / "data"
SESSIONS = DATA / "all_sessions.json"
MAPPING  = DATA / "themen_zuordnung.json"

# Hauptgruppen der Rechtssammlung SH (Stufe 1)
GRUPPEN = {
    "1": "Staat, Volk, Behörden",
    "2": "Privatrecht, Zivilrechtspflege",
    "3": "Strafrecht, Strafvollzug",
    "4": "Erziehung, Kultur, Natur",
    "5": "Verteidigung, Wehrdienste",
    "6": "Finanzen",
    "7": "Raumplanung, Bau, Verkehr, Energie",
    "8": "Gesundheit, Umwelt, Arbeit, Soziales",
    "9": "Wirtschaft",
}

# Gewichtete Stichwörter je Gruppe (spezifischer = höheres Gewicht).
# Bewusst konservativ; unsichere Fälle bleiben "offen" für die manuelle Prüfung.
KEYWORDS = {
    "4": [("schulgesetz",5),("schuldekret",5),("schule",3),("bildung",3),
          ("kultur",3),("kunst",3),("heimatschutz",3),("denkmal",3),
          ("sport",2),("natur",2),("hochschul",4),("kindergarten",4)],
    "5": [("zivilschutz",5),("bevölkerungsschutz",5),("militär",4),
          ("wehrdienst",4),("waffen",3),("feuerwehr",4)],
    "6": [("finanzhaushalt",5),("finahaushalt",5),("finanzausgleich",5),
          ("steuer",4),("budget",3),("staatsrechnung",4),("jahresrechnung",3),
          ("globalbudget",4),("solidaritätsbeitrag",3),("individualbe",3),
          ("verwaltungsbericht",3),("mehrwertabgabe",4)],
    "7": [("raumplanung",5),("bahnübergang",5),("kantonsstrasse",5),
          ("ortsverkehr",4),("biogas",4),("verkehr",3),("energie",3),
          ("gewässer",3),("richtplan",5),("baugesetz",5),("strassenbau",4),
          ("öv",3),("bau",2),("strasse",2)],
    "8": [("spitalgesetz",5),("spital",4),("brustkrebs",5),("screening",4),
          ("altersbetreuung",5),("pflegeges",4),("gesundheit",3),("umwelt",3),
          ("krankenversicherung",4),("prämien",3),("sozialhilfe",4),
          ("arbeitsgesetz",4),("kita",4)],
    "9": [("landwirtschaft",4),("gewerbe",3),("tourismus",4),("binnenmarkt",4),
          ("gastgewerbe",4),("jagd",3),("wald",3),("wirtschaftsförderung",5),
          ("wirtschaft",2)],
    "3": [("strafrecht",4),("strafprozess",4),("strafvollzug",4),("opfer",3),
          ("polizei",3),("justizvollzug",4)],
    "2": [("zivilprozess",4),("betreibung",4),("konkurs",4),("obligation",3)],
    "1": [("verfassung",4),("gemeindegesetz",5),("bürgerrecht",4),("ombud",4),
          ("archivgesetz",4),("aktenführung",4),("datenschutz",4),
          ("gewaltentrennung",4),("stimmrecht",3),("wahlgesetz",4),
          ("personalrecht",3),("pensionskasse",4),("rechtsschutz",3),
          ("kantonsrat",3),("gemeinde",2)],
}


def classify(text):
    """Gibt (gruppe, alle_treffer) zurück oder (None, [])."""
    tl = text.lower()
    scores = {}
    for grp, kws in KEYWORDS.items():
        sc = sum(w for kw, w in kws if kw in tl)
        if sc:
            scores[grp] = sc
    if not scores:
        return None, []
    ranked = sorted(scores, key=scores.get, reverse=True)
    return ranked[0], [(g, scores[g]) for g in ranked]


def collect_geschaefte(data):
    """Alle einzigartigen Geschäftstexte über alle Sitzungen."""
    g = {}
    for s in data["sessions"]:
        for v in s["votes"]:
            gt = (v.get("geschaeft") or "").strip()
            if gt:
                g.setdefault(gt, 0)
                g[gt] += 1
    return g


def build_mapping():
    data = json.load(open(SESSIONS))
    geschaefte = collect_geschaefte(data)

    # bestehende Zuordnung laden (manuelle Prüfungen bewahren)
    existing = {}
    if Path(MAPPING).exists():
        for row in json.load(open(MAPPING))["zuordnung"]:
            existing[row["geschaeft"]] = row

    rows = []
    neu = auto = geprueft = offen = 0
    for gt, anzahl in sorted(geschaefte.items()):
        if gt in existing and existing[gt].get("geprüft"):
            row = existing[gt]
            row["anzahl_abstimmungen"] = anzahl
            geprueft += 1
        else:
            grp, ranked = classify(gt)
            alt = [g for g, _ in ranked[1:3]] if ranked else []
            row = {
                "geschaeft": gt,
                "gruppe": grp,                       # "1".."9" oder null
                "gruppe_name": GRUPPEN.get(grp) if grp else None,
                "alternativen": [GRUPPEN[g] for g in alt],
                "geprüft": False,
                "anzahl_abstimmungen": anzahl,
            }
            neu += 1
            if grp:
                auto += 1
            else:
                offen += 1
        rows.append(row)

    out = {"gruppen": GRUPPEN, "zuordnung": rows}
    json.dump(out, open(MAPPING, "w"), ensure_ascii=False, indent=1)
    print(f"{MAPPING} geschrieben: {len(rows)} Geschäfte")
    print(f"  bereits manuell geprüft: {geprueft}")
    print(f"  automatisch vorgeschlagen: {auto}")
    print(f"  offen (kein Vorschlag, bitte prüfen): {offen}")
    if offen:
        print("\nOffene Geschäfte ohne Vorschlag:")
        for r in rows:
            if r["gruppe"] is None:
                print(f"  - {r['geschaeft'][:80]}")


def apply_mapping():
    data = json.load(open(SESSIONS))
    mp = json.load(open(MAPPING))
    lookup = {r["geschaeft"]: r for r in mp["zuordnung"]}
    tagged = 0
    for s in data["sessions"]:
        for v in s["votes"]:
            gt = (v.get("geschaeft") or "").strip()
            row = lookup.get(gt)
            if row and row.get("gruppe"):
                v["thema_gruppe"] = row["gruppe"]
                v["thema_name"] = row["gruppe_name"]
                tagged += 1
            else:
                v["thema_gruppe"] = None
                v["thema_name"] = None
    data["themen_gruppen"] = mp["gruppen"]
    json.dump(data, open(SESSIONS, "w"), ensure_ascii=False, indent=1)
    total = sum(len(s["votes"]) for s in data["sessions"])
    print(f"Tags in {SESSIONS} geschrieben: {tagged}/{total} Abstimmungen haben ein Thema.")


if __name__ == "__main__":
    if "--apply" in sys.argv:
        apply_mapping()
    else:
        build_mapping()

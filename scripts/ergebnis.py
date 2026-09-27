#!/usr/bin/env python3
"""
Abstimmungsergebnis nachtragen
==============================
Holt nach dem Abstimmungssonntag das Ergebnis einer kantonalen Vorlage aus den
Echtzeitdaten des Bundesamts für Statistik, legt es je Gemeinde im
Abstimmungsordner ab und trägt die Kantonszahlen als Feld «ergebnis» in
vorlage.json ein. Mit diesem Feld führt die Übersicht (politspiegel/bauen.py)
die Abstimmung unter «Vergangen».

Quellen
  Ergebnis         BFS, Echtzeitdaten am Abstimmungstag zu kantonalen
                   Abstimmungsvorlagen (opendata.swiss). Der Kanton liefert
                   seine Ergebnisse dorthin, je Gemeinde und je Frage. Die
                   Datei ist je Abstimmungstag gleich adressiert (URL unten).
  Gemeindegrenzen  swissBOUNDARIES3D, swisstopo, über api3.geo.admin.ch, für
                   die Ergebniskarte (scripts/datenreel.py <slug> ergebnis)

Die Vorlage wird über ihren Titel gefunden (vorlage.titel oder
vorlage.kantonsrat_suche im amtlichen Titel), Gegenvorschlag und Stichfrage
über die Hauptvorlage. Bei der Stichfrage zählt das BFS die Stimmen für die
Initiative als Ja und die für den Gegenvorschlag als Nein.

Vor dem Schreiben wird nachgerechnet:
  1. Summe der Gemeinden gleich Kantonstotal, je Frage für Ja und Nein
  2. Ja-Anteil aus den Stimmen gleich dem gelieferten Anteil
  3. Vorlage abgeschlossen, alle Gemeinden ausgezählt

Ausführen:
    python3 scripts/ergebnis.py 2026-09-27-verkehrsfluss             # Probelauf
    python3 scripts/ergebnis.py 2026-09-27-verkehrsfluss --apply     # schreibt
    python3 scripts/ergebnis.py <slug> --id 614311 --apply           # Vorlage von Hand wählen

Schreibt nach abstimmungsspiegel/abstimmungen/<slug>/ergebnis/
    voteinfo_roh.json        Block des Kantons aus der BFS-Datei, unverändert
    ergebnis.json            Kanton und Gemeinden je Frage
    gemeindegrenzen.geojson  Gemeinden des Kantons, WGS84
und in vorlage.json das Feld «ergebnis» (Schema in abstimmungsspiegel/docs/14_TECHNIK.md).
"""
import json
import re
import sys
import urllib.request
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KANTON = 14      # Schaffhausen, BFS-Kantonsnummer
URL = "https://ogd-static.voteinfo-app.ch/v1/ogd/sd-t-17-02-{tag}-kantAbstimmung.json"
GRENZE = ("https://api3.geo.admin.ch/rest/services/api/MapServer/"
          "ch.swisstopo.swissboundaries3d-gemeinde-flaeche.fill/{bfs}?geometryFormat=geojson&sr=4326&lang=de")
MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
          "September", "Oktober", "November", "Dezember"]


def laden(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Politspiegel Schaffhausen"})
    return json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8"))


def titel_de(x):
    for t in x.get("vorlagenTitel") or []:
        if t.get("langKey") == "de":
            return (t.get("text") or "").strip()
    return ""


def anteil(ja, nein):
    """Ja-Anteil in Prozent aus den Stimmen. Sechs Stellen, damit die Anzeige mit
    einer Stelle nicht doppelt rundet: 82 Ja zu 63 Nein sind 56,5517 %, auf zwei
    Stellen gespeichert 56.55 und angezeigt 56,5 statt 56,6."""
    return round(100 * ja / (ja + nein), 6) if ja + nein else None


def vorlagen_waehlen(kanton, v, vid=None):
    alle = kanton["vorlagen"]
    if vid:
        haupt = [x for x in alle if x["vorlagenId"] == vid]
    else:
        suche = [s.lower() for s in (v.get("titel"), v.get("kantonsrat_suche")) if s]
        haupt = [x for x in alle if not x.get("hauptvorlagenId")
                 and any(s in titel_de(x).lower() for s in suche)]
    if len(haupt) != 1:
        liste = "\n".join(f"  {x['vorlagenId']}  {titel_de(x)}" for x in alle)
        raise SystemExit(f"Vorlage nicht eindeutig gefunden ({len(haupt)} Treffer). "
                         f"Mit --id <vorlagenId> wählen:\n{liste}")
    h = haupt[0]
    gruppe = [h] + [x for x in alle if x.get("hauptvorlagenId") == h["vorlagenId"]]
    return sorted(gruppe, key=lambda x: x.get("reihenfolgeAnzeige") or 0)


def frage_art(x, n):
    """(id, Titel) je Frage. Eine einfache Vorlage hat keinen Fragetitel."""
    t = titel_de(x).lower()
    if "stichfrage" in t:
        return "stichfrage", "Stichfrage"
    if "gegenvorschlag" in t or "gegenentwurf" in t:
        return "gegenvorschlag", "Gegenvorschlag"
    if n == 1:
        return "vorlage", ""
    return ("initiative", "Initiative") if "initiative" in t else ("vorlage", "Vorlage")


def pruefen(gruppe):
    fehler = []
    for x in gruppe:
        name = titel_de(x)[:70]
        r = x["resultat"]
        if not x.get("vorlageBeendet"):
            fehler.append(f"{name}: Vorlage noch nicht abgeschlossen")
        offen = [g["geoLevelname"] for g in x["gemeinden"] if not g["resultat"].get("gebietAusgezaehlt")]
        if offen:
            fehler.append(f"{name}: nicht ausgezählt: {', '.join(offen)}")
        ja = sum(g["resultat"]["jaStimmenAbsolut"] or 0 for g in x["gemeinden"])
        ne = sum(g["resultat"]["neinStimmenAbsolut"] or 0 for g in x["gemeinden"])
        if (ja, ne) != (r["jaStimmenAbsolut"], r["neinStimmenAbsolut"]):
            fehler.append(f"{name}: Summe Gemeinden {ja}:{ne}, Kanton {r['jaStimmenAbsolut']}:{r['neinStimmenAbsolut']}")
        a = anteil(r["jaStimmenAbsolut"], r["neinStimmenAbsolut"])
        if a is None or abs(a - r["jaStimmenInProzent"]) > 0.01:
            fehler.append(f"{name}: Ja-Anteil nachgerechnet {a}, geliefert {r['jaStimmenInProzent']}")
    return fehler


def aufbereiten(gruppe, roh, v, url):
    n = len(gruppe)
    fragen = []
    for x in gruppe:
        art, titel = frage_art(x, n)
        r = x["resultat"]
        gj = sum(1 for g in x["gemeinden"] if g["resultat"]["jaStimmenAbsolut"] > g["resultat"]["neinStimmenAbsolut"])
        gn = sum(1 for g in x["gemeinden"] if g["resultat"]["jaStimmenAbsolut"] < g["resultat"]["neinStimmenAbsolut"])
        f = {"id": art, "titel": titel, "titel_amtlich": titel_de(x), "vorlagen_id": x["vorlagenId"],
             "ja_stimmen": r["jaStimmenAbsolut"], "nein_stimmen": r["neinStimmenAbsolut"],
             "ja": anteil(r["jaStimmenAbsolut"], r["neinStimmenAbsolut"]),
             "angenommen": None if art == "stichfrage" else bool(x.get("vorlageAngenommen")),
             "gemeinden_ja": gj, "gemeinden_nein": gn, "gemeinden_gleich": len(x["gemeinden"]) - gj - gn}
        if art == "stichfrage":
            f["bezeichnung"] = "für die Initiative"
        fragen.append(f)
    bezirke = {str(b["geoLevelnummer"]): b["geoLevelname"] for b in gruppe[0].get("bezirke") or []}
    gem = {}
    for f, x in zip(fragen, gruppe):
        for g in x["gemeinden"]:
            r = g["resultat"]
            e = gem.setdefault(int(g["geoLevelnummer"]), {
                "bfs": int(g["geoLevelnummer"]),
                "name": g["geoLevelname"],
                "kurz": re.sub(r"\s*\(SH\)$", "", g["geoLevelname"]),
                "bezirk": bezirke.get(str(g.get("geoLevelParentnummer")), ""),
                "stimmberechtigte": r["anzahlStimmberechtigte"],
                "eingelegte_stimmzettel": r["eingelegteStimmzettel"],
                "stimmbeteiligung": round(r["stimmbeteiligungInProzent"], 6),
                "fragen": {}})
            e["fragen"][f["id"]] = {"ja_stimmen": r["jaStimmenAbsolut"], "nein_stimmen": r["neinStimmenAbsolut"],
                                    "ja": anteil(r["jaStimmenAbsolut"], r["neinStimmenAbsolut"])}
    k = gruppe[0]["resultat"]
    return {
        "vorlage": v.get("id"),
        "abstimmung": v.get("abstimmung"),
        "quelle": {"name": "Bundesamt für Statistik, Echtzeitdaten am Abstimmungstag zu kantonalen "
                           "Abstimmungsvorlagen (opendata.swiss), geliefert vom Kanton Schaffhausen",
                   "url": url, "stand": roh["timestamp"]},
        "kanton": {"stimmberechtigte": k["anzahlStimmberechtigte"],
                   "eingelegte_stimmzettel": k["eingelegteStimmzettel"],
                   "stimmbeteiligung": round(k["stimmbeteiligungInProzent"], 6)},
        "fragen": fragen,
        "gemeinden": sorted(gem.values(), key=lambda g: g["name"]),
    }


def feld_ergebnis(erg):
    """Das Feld «ergebnis» für vorlage.json: nur Kantonszahlen."""
    stand = datetime.fromisoformat(erg["quelle"]["stand"])
    tag = date.fromisoformat(erg["abstimmung"])
    fragen = []
    for f in erg["fragen"]:
        z = {"titel": f["titel"], "ja": f["ja"]}
        if f.get("bezeichnung"):
            z["bezeichnung"] = f["bezeichnung"]
        if f["angenommen"] is not None:
            z["angenommen"] = f["angenommen"]
        z["ja_stimmen"] = f["ja_stimmen"]
        z["nein_stimmen"] = f["nein_stimmen"]
        fragen.append(z)
    return {
        "stimmbeteiligung": erg["kanton"]["stimmbeteiligung"],
        "quelle": (f"Kanton Schaffhausen, Ergebnis vom {tag.day}. {MONATE[tag.month - 1]} {tag.year}, "
                   f"Echtzeitdaten des BFS, Stand {stand:%H:%M} Uhr"),
        "fragen": fragen,
    }


def grenzen(gemeinden, ziel):
    """Gemeindegrenzen je BFS-Nummer; eine vorhandene Datei mit allen Gemeinden bleibt."""
    if ziel.exists():
        alt = json.loads(ziel.read_text(encoding="utf-8"))
        if {f["properties"]["bfs"] for f in alt["features"]} >= {g["bfs"] for g in gemeinden}:
            return alt, False

    def runden(c):
        return [runden(x) for x in c] if isinstance(c[0], list) else [round(c[0], 6), round(c[1], 6)]

    features = []
    for g in gemeinden:
        f = laden(GRENZE.format(bfs=g["bfs"]))["feature"]
        features.append({"type": "Feature",
                         "properties": {"bfs": g["bfs"], "name": g["kurz"], "jahr": f["properties"].get("jahr")},
                         "geometry": {"type": f["geometry"]["type"],
                                      "coordinates": runden(f["geometry"]["coordinates"])}})
    return {"type": "FeatureCollection",
            "quelle": "swissBOUNDARIES3D, swisstopo (api3.geo.admin.ch), Layer ch.swisstopo.swissboundaries3d-gemeinde-flaeche.fill",
            "features": features}, True


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        raise SystemExit(__doc__)
    slug = args[0]
    schreiben = "--apply" in sys.argv
    vid = int(sys.argv[sys.argv.index("--id") + 1]) if "--id" in sys.argv else None
    ordner = ROOT / "abstimmungsspiegel" / "abstimmungen" / slug
    pfad = ordner / "vorlage.json"
    d = json.loads(pfad.read_text(encoding="utf-8"))
    v = d["vorlage"]
    url = URL.format(tag=v["abstimmung"].replace("-", ""))
    print(f"Lade {url}")
    alles = laden(url)
    kanton = next((k for k in alles["kantone"] if int(k["geoLevelnummer"]) == KANTON), None)
    if not kanton or kanton.get("nochKeineInformation"):
        raise SystemExit("Für den Kanton Schaffhausen liegen noch keine Ergebnisse vor.")
    gruppe = vorlagen_waehlen(kanton, v, vid)
    fehler = pruefen(gruppe)
    roh = {"abstimmtag": alles["abstimmtag"], "timestamp": alles["timestamp"], "quelle": url,
           "kanton": {k: kanton[k] for k in kanton if k != "vorlagen"},
           "vorlagen": gruppe}
    erg = aufbereiten(gruppe, roh, v, url)

    print(f"Stand {roh['timestamp']}, Stimmbeteiligung {erg['kanton']['stimmbeteiligung']} %")
    for f in erg["fragen"]:
        lage = "" if f["angenommen"] is None else (", angenommen" if f["angenommen"] else ", abgelehnt")
        print(f"  {f['titel'] or 'Vorlage':15s} {f['ja']:6.2f} % {f.get('bezeichnung', 'Ja')}{lage}  "
              f"({f['ja_stimmen']}:{f['nein_stimmen']}; Gemeinden {f['gemeinden_ja']} Ja, "
              f"{f['gemeinden_nein']} Nein, {f['gemeinden_gleich']} gleich)")
    if fehler:
        print("Nachrechnung fehlgeschlagen:\n  " + "\n  ".join(fehler))
        raise SystemExit(1)
    print("Nachrechnung: Summen, Anteile und Auszählung stimmen.")
    if not schreiben:
        print("(Probelauf, nichts geschrieben. Mit --apply schreiben.)")
        return

    ziel = ordner / "ergebnis"
    ziel.mkdir(exist_ok=True)
    (ziel / "voteinfo_roh.json").write_text(json.dumps(roh, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (ziel / "ergebnis.json").write_text(json.dumps(erg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    fc, neu = grenzen(erg["gemeinden"], ziel / "gemeindegrenzen.geojson")
    if neu:
        (ziel / "gemeindegrenzen.geojson").write_text(json.dumps(fc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    # «ergebnis» direkt nach «status», der Rest der Datei bleibt, wie er ist
    neu_d = {}
    for k, wert in d.items():
        if k == "ergebnis":
            continue
        neu_d[k] = wert
        if k == "status":
            neu_d["ergebnis"] = feld_ergebnis(erg)
    if "ergebnis" not in neu_d:
        neu_d["ergebnis"] = feld_ergebnis(erg)
    pfad.write_text(json.dumps(neu_d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"geschrieben: {ziel.relative_to(ROOT)}/ (voteinfo_roh.json, ergebnis.json"
          + (", gemeindegrenzen.geojson" if neu else "") + f") und {pfad.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Abgleich der Interessenbindungen mit dem Handelsregister
========================================================
Prüft die deklarierten Organisationen gegen das amtliche Handelsregister.
Quelle ist der offene Zefix-Datensatz des Bundesamts für Justiz, abgefragt
über den SPARQL-Endpunkt von LINDAS. Er enthält alle rund 790'000
eingetragenen Rechtseinheiten der Schweiz, das Handelsregister Schaffhausen
eingeschlossen.

Was das Skript kann und was nicht
---------------------------------
Es prüft, ob eine deklarierte Firma im Handelsregister existiert, und hält
Name, UID und Sitz fest. Damit lassen sich Deklarationen belegen und Einträge
finden, die sich nicht zuordnen lassen (Tippfehler, umbenannte oder
gelöschte Firmen).

Es kann NICHT den umgekehrten Weg gehen, also zu einer Person alle Mandate
suchen. Weder der offene Datensatz noch die Zefix-REST-API kennen Personen.
Die REST-API bietet laut ihrer eigenen Schnittstellenbeschreibung
(https://www.zefix.admin.ch/ZefixPublicREST/v3/api-docs) genau zehn Endpunkte,
und alle drehen sich um Rechtseinheiten, Publikationen und Gemeinden. Eine
Suche nach «alle Mandate von Person X» ist damit nicht möglich, und eine
frühere Fassung dieses Skripts, die einen Endpunkt /person/search aufrief, hat
ins Leere gegriffen. Wer Mandate einer Person sucht, muss die Firmen einzeln
aufrufen und die Publikationstexte lesen.

Was der REST-Zugang dafür bringt
--------------------------------
Liegen Zugangsdaten in data/zefix_zugang.json ({"user": "...", "pass": "..."}),
prüft das Skript jede deklarierte Firma zusätzlich am amtlichen Register selbst
und holt Angaben, die der offene Datensatz nicht enthält:

  · status und deletionDate: steht die Firma noch im Register oder ist sie
    gelöscht? Ein deklariertes Mandat bei einer gelöschten Firma ist ein
    Befund, keine Formalie.
  · oldNames: frühere Firmennamen. Damit lösen sich Fälle auf, die bisher als
    «nicht gefunden» galten, weil die Firma zwischenzeitlich umbenannt wurde.
    Genau das ist laut Register der häufigste Grund für Fehlanzeigen.
  · legalSeat, address, canton: der Sitz aus erster Hand, womit sich ein
    «möglicher» Treffer zu einem eindeutigen erhärten oder ausschliessen lässt.
  · purpose: der eingetragene Zweck, der zeigt, ob die gefundene Firma
    inhaltlich zur Deklaration passt.
  · zefixDetailWeb: der Link auf den amtlichen Eintrag, den das Dashboard
    direkt anbieten kann.

Der Zugang macht die Prüfung also nicht breiter, sondern belastbarer.

Alles, was dabei herauskommt, ist ein Prüfhinweis mit Quellenangabe, keine
Feststellung. Der Abgleich über den Namen ist nicht eindeutig: Namensgleiche
Personen und Firmen kommen vor.

Ausführen:
    python3 scripts/zefix.py            # Bericht
    python3 scripts/zefix.py --apply    # schreibt data/interessen_pruefung.json
"""
import json
import re
import sys
import time
import unicodedata
from datetime import date
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
NETZ = DATA / "interessen_netz.json"
ZIEL = DATA / "interessen_pruefung.json"
CACHE = DATA / "zefix_cache.json"
ZUGANG = DATA / "zefix_zugang.json"

SPARQL = "https://lindas.admin.ch/query"
ZEFIX_REST = "https://www.zefix.admin.ch/ZefixPublicREST/api/v1"
UA = {"User-Agent": "Mozilla/5.0 (kantonsrat-dashboard)"}
BUENDEL = 4          # Organisationen je Abfrage; mehr lässt der Endpunkt
                     # zeitlich nicht zu und liefert dann stillschweigend nichts

# Nur Namen, die nach einer eingetragenen Rechtseinheit aussehen. Vereine und
# Behörden stehen meist nicht im Handelsregister, ihr Fehlen sagt nichts aus.
REGISTERPFLICHTIG = re.compile(
    r"\b(AG|GmbH|SA|Sàrl|Genossenschaft|Stiftung|Holding|KlG|KmG)\b", re.I)


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s.lower()).strip()


def wortmenge(s):
    return {w for w in re.split(r"[^a-z0-9]+", norm(s)) if len(w) > 2
            and w not in {"der", "die", "das", "und", "ag", "gmbh", "sa"}}


def guete(deklariert, treffer, ort=None):
    """Wie gut passt ein Registereintrag zur Deklaration?

    Der Namensabgleich allein genügt nicht: «Stiftung betreutes Wohnen» trifft
    auch eine Genossenschaft in Appenzell. Darum zählen Wortüberschneidung und,
    falls bekannt, der Sitz."""
    a, b = wortmenge(deklariert), wortmenge(treffer.get("name", ""))
    if not a or not b:
        return ("kein", 0.0)
    anteil = len(a & b) / len(a)
    sitz_ok = None
    if ort:
        sitz_ok = norm(ort) in norm(treffer.get("ort", "")) or \
                  norm(treffer.get("ort", "")) in norm(ort)
    if anteil >= 0.6 and sitz_ok is not False:
        return ("eindeutig", anteil)
    if anteil >= 0.34:
        return ("moeglich", anteil)
    return ("kein", anteil)


def suchbegriff(name):
    """Aussagekräftigster Namensteil für die Suche im Register."""
    n = re.sub(r"\(.*?\)", " ", name)
    n = re.sub(r"\b(AG|GmbH|SA|Sàrl|Genossenschaft|Stiftung|Holding)\b", " ", n, flags=re.I)
    woerter = [w for w in re.split(r"[\s,]+", n) if len(w) > 3]
    return norm(woerter[0]) if woerter else norm(name)[:12]


def sparql_abfrage(begriffe):
    """Ein Bündel Suchbegriffe in einer Abfrage."""
    filt = " || ".join(f'CONTAINS(LCASE(?name), "{b}")' for b in begriffe)
    q = f"""
PREFIX schema: <http://schema.org/>
SELECT ?name ?ort ?uid WHERE {{
  ?s a <https://schema.ld.admin.ch/ZefixOrganisation> ; schema:legalName ?name .
  OPTIONAL {{ ?s schema:address ?a . ?a schema:addressLocality ?ort }}
  OPTIONAL {{ ?s schema:identifier ?i . ?i schema:value ?uid .
              FILTER(STRSTARTS(STR(?uid), "CHE")) }}
  FILTER({filt})
}} LIMIT 200
"""
    r = requests.post(SPARQL, data={"query": q},
                      headers={**UA, "Accept": "application/sparql-results+json"},
                      timeout=180)
    r.raise_for_status()
    return [{k: v["value"] for k, v in b.items()} for b in r.json()["results"]["bindings"]]


def register_pruefen(orgs):
    """Je Organisation die Treffer aus dem Handelsregister."""
    cache = json.load(open(CACHE, encoding="utf-8")) if CACHE.exists() else {}
    offen = [o for o in orgs if o["label"] not in cache]
    print(f"   {len(orgs)} Organisationen, {len(offen)} noch nicht abgefragt", flush=True)

    for i in range(0, len(offen), BUENDEL):
        teil = offen[i:i + BUENDEL]
        begriffe = {suchbegriff(o["label"]): o for o in teil}
        treffer = []
        for versuch in range(2):
            try:
                treffer = sparql_abfrage(list(begriffe))
                if treffer:
                    break
            except Exception as e:
                print(f"   ! Abfrage fehlgeschlagen: {e}", flush=True)
            time.sleep(2)
        if not treffer:
            # leeres Ergebnis für ein ganzes Bündel heisst meist Zeitüberschreitung,
            # nicht "gibt es nicht": dann lieber nichts merken und später erneut fragen
            print(f"   ! Bündel ohne Treffer, nicht gespeichert: {list(begriffe)}", flush=True)
            continue
        for begriff, o in begriffe.items():
            passend = [t for t in treffer if begriff in norm(t.get("name", ""))]
            cache[o["label"]] = passend[:5]
        print(f"   ... {min(i+BUENDEL, len(offen))}/{len(offen)}", flush=True)
        time.sleep(0.5)

    # Zweiter Durchgang einzeln: gebündelte Abfragen laufen gelegentlich in die
    # Zeitgrenze des Endpunkts und liefern dann für das ganze Bündel nichts.
    nachzuegler = [o for o in orgs if not cache.get(o["label"])]
    if nachzuegler:
        print(f"   {len(nachzuegler)} ohne Treffer, einzeln nachfragen", flush=True)
        for o in nachzuegler:
            b = suchbegriff(o["label"])
            try:
                treffer = sparql_abfrage([b])
            except Exception as e:
                print(f"   ! {o['label']}: {e}", flush=True)
                continue
            passend = [x for x in treffer if b in norm(x.get("name", ""))]
            if passend:
                cache[o["label"]] = passend[:5]
            time.sleep(0.4)

    json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return cache


def rest(pfad, zugang, methode="GET", rumpf=None):
    """Ein Aufruf an die Zefix-REST-API. Gibt (daten, fehlertext) zurück."""
    try:
        kopf = {**UA, "Accept": "application/json"}
        if methode == "POST":
            kopf["Content-Type"] = "application/json"
            r = requests.post(f"{ZEFIX_REST}{pfad}", json=rumpf,
                              auth=(zugang["user"], zugang["pass"]),
                              headers=kopf, timeout=60)
        else:
            r = requests.get(f"{ZEFIX_REST}{pfad}",
                             auth=(zugang["user"], zugang["pass"]),
                             headers=kopf, timeout=60)
        if r.status_code == 401:
            return None, "401 nicht angemeldet: Zugang falsch oder noch nicht freigeschaltet"
        if r.status_code == 404:
            return None, "404"
        if r.status_code != 200:
            return None, f"{r.status_code} {r.text[:120]}"
        return r.json(), None
    except Exception as e:
        return None, str(e)[:120]


def rest_anreichern(orgs, zugang):
    """Deklarierte Firmen am amtlichen Register prüfen.

    Sucht je Firma über /company/search, holt zum besten Treffer die
    Volldaten über /company/uid und behält Status, Sitz, Zweck, frühere Namen
    und den Link auf den Registereintrag. Findet die Namenssuche nichts, wird
    ein zweites Mal ohne Rechtsformzusatz gesucht.
    """
    raus, fehler = {}, []
    for i, o in enumerate(orgs, 1):
        gefunden = None
        for begriff in (o["label"], suchbegriff(o["label"])):
            kurz, f = rest("/company/search", zugang, "POST", {"name": begriff})
            if f:
                fehler.append(f"{o['label']}: {f}")
                break
            if kurz:
                # Bester Treffer nach Wortüberschneidung, aktive vor gelöschten
                bewertet = sorted(
                    kurz, key=lambda t: (-guete(o["label"], t, o.get("ort"))[1],
                                         0 if not t.get("deletionDate") else 1))
                gefunden = bewertet[0]
                break
            time.sleep(0.3)
        if not gefunden:
            continue
        voll = None
        if gefunden.get("uid"):
            voll, f = rest(f"/company/uid/{gefunden['uid']}", zugang)
            if isinstance(voll, list):
                voll = voll[0] if voll else None
        v = voll or gefunden
        adresse = v.get("address") or {}
        raus[o["label"]] = {
            "name": v.get("name"),
            "uid": v.get("uid"),
            "sitz": v.get("legalSeat"),
            "kanton": v.get("canton"),
            "ort": adresse.get("city") or v.get("legalSeat"),
            "rechtsform": deutsch((v.get("legalForm") or {}).get("name")),
            "status": STATUS.get(v.get("status"), v.get("status")),
            "geloescht_am": v.get("deletionDate"),
            "zweck": kuerzen(v.get("purpose")),
            "frueher": [n.get("name") for n in (v.get("oldNames") or []) if n.get("name")][:4],
            "url": deutsch(v.get("zefixDetailWeb")) or v.get("cantonalExcerptWeb"),
        }
        if i % 10 == 0:
            print(f"   ... {i}/{len(orgs)} am Register geprüft", flush=True)
        time.sleep(0.3)
    return raus, fehler


def kuerzen(s, n=240):
    s = re.sub(r"\s+", " ", s or "").strip()
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + " …"


def deutsch(feld):
    """Mehrsprachige Felder der API (DFIEString) auf Deutsch herunterbrechen.

    legalForm.name und zefixDetailWeb sind keine Zeichenketten, sondern Objekte
    mit den Schlüsseln de, fr, it und en. Wer sie direkt weitergibt, schreibt
    ein Objekt in die Seite.
    """
    if isinstance(feld, dict):
        for s in ("de", "fr", "it", "en"):
            if feld.get(s):
                return feld[s]
        return None
    return feld or None


# status ist laut Schnittstellenbeschreibung auf drei Werte festgelegt.
STATUS = {"ACTIVE": "aktiv",
          "CANCELLED": "gelöscht",
          "BEING_CANCELLED": "in Löschung"}


def main():
    netz = json.load(open(NETZ, encoding="utf-8"))
    orgs = [k for k in netz["knoten"] if k["typ"] == "organisation"]
    firmen = [o for o in orgs if REGISTERPFLICHTIG.search(o["label"])]
    print(f"{len(orgs)} deklarierte Organisationen, davon {len(firmen)} "
          f"mit Rechtsform im Namen (nur diese werden geprüft)")

    cache = register_pruefen(firmen)
    eindeutig, moeglich, offen = [], [], []
    for o in firmen:
        roh = cache.get(o["label"], [])
        bewertet = []
        for tr in roh:
            stufe, anteil = guete(o["label"], tr, o.get("ort"))
            if stufe != "kein":
                bewertet.append({**tr, "stufe": stufe, "uebereinstimmung": round(anteil, 2)})
        bewertet.sort(key=lambda x: (-{"eindeutig": 2, "moeglich": 1}[x["stufe"]],
                                     -x["uebereinstimmung"]))
        eintrag = {"organisation": o["label"], "branche": o["branche"],
                   "ort": o.get("ort"), "treffer": bewertet[:5],
                   "mitglieder": sorted({k["von"].replace("m:", "").replace("|", " ")
                                         for k in netz["kanten"]
                                         if k["nach"] == o["id"] and k.get("art") != "branche"})}
        if bewertet and bewertet[0]["stufe"] == "eindeutig":
            eindeutig.append(eintrag)
        elif bewertet:
            moeglich.append(eintrag)
        else:
            offen.append(eintrag)

    print(f"\n   eindeutig im Handelsregister: {len(eindeutig)}")
    for e in eindeutig[:6]:
        tr = e["treffer"][0]
        print(f"      · {e['organisation'][:40]:40} -> {tr['name'][:34]:34} {tr.get('uid','')}")
    print(f"   nur mögliche Treffer: {len(moeglich)}")
    for e in moeglich:
        tr = e["treffer"][0]
        print(f"      · {e['organisation'][:40]:40} -> {tr['name'][:38]:38} ({tr.get('ort','?')})")
    print(f"   kein Treffer: {len(offen)}")
    for e in offen:
        print(f"      · {e['organisation'][:52]:52} ({', '.join(e['mitglieder'])})")

    # Anreicherung am amtlichen Register, nur mit Zugangsdaten
    amtlich, rest_fehler, befunde = {}, [], []
    if ZUGANG.exists():
        zugang = json.load(open(ZUGANG, encoding="utf-8"))
        print(f"\n   Zefix-Zugang vorhanden, {len(firmen)} Firmen am Register prüfen")
        amtlich, rest_fehler = rest_anreichern(firmen, zugang)
        if rest_fehler:
            print(f"   ! {len(rest_fehler)} Aufrufe fehlgeschlagen, erster: {rest_fehler[0]}")
        if not amtlich and rest_fehler:
            print("   Die Anreicherung ist ausgefallen. Der Bericht beruht allein auf dem")
            print("   offenen Datensatz, also auf demselben Stand wie ohne Zugang.")

        # Die drei Befunde, die den Zugang überhaupt lohnen
        for e in eindeutig + moeglich + offen:
            a = amtlich.get(e["organisation"])
            if not a:
                continue
            e["amtlich"] = a
            if a.get("geloescht_am") or a.get("status") in ("gelöscht", "in Löschung"):
                wie = "in Löschung" if a.get("status") == "in Löschung" else "gelöscht"
                befunde.append({"art": "geloescht", "organisation": e["organisation"],
                                "mitglieder": e["mitglieder"],
                                "text": f"im Handelsregister {wie}"
                                        + (f", Datum {a['geloescht_am']}" if a.get("geloescht_am") else ""),
                                "url": a.get("url")})
            elif e in offen:
                treffer = a.get("frueher") and "früherer Name" or "Namensvariante"
                befunde.append({"art": "aufgeloest", "organisation": e["organisation"],
                                "mitglieder": e["mitglieder"],
                                "text": f"am Register doch gefunden als «{a['name']}» ({treffer})",
                                "url": a.get("url")})
        if befunde:
            print(f"\n   {len(befunde)} Befunde aus dem amtlichen Register:")
            for b in befunde:
                print(f"      · {b['organisation'][:46]:46} {b['text']}")
                print(f"        betrifft: {', '.join(b['mitglieder'])}")
        else:
            print("\n   Keine Auffälligkeiten am amtlichen Register.")
    else:
        print(f"\n   Keine Zefix-Zugangsdaten in {ZUGANG.name}: die Prüfung beruht allein")
        print("   auf dem offenen Datensatz. Status, frühere Namen und der Link auf den")
        print("   Registereintrag fehlen damit. Kostenlosen Zugang beantragen bei")
        print("   zefix@bj.admin.ch, dann {\"user\": \"...\", \"pass\": \"...\"} dort ablegen.")

    # Eine Personensuche gibt es in dieser API nicht, siehe Kopf der Datei.
    hinweise = []

    if "--apply" in sys.argv:
        json.dump({"stand": date.today().isoformat(),
                   "quelle": "Zefix (Bundesamt für Justiz) über lindas.admin.ch",
                   "hinweis": ("Namensabgleich, keine Feststellung. «Eindeutig» heisst, dass "
                               "Name und, soweit bekannt, Sitz übereinstimmen; «möglich» heisst, "
                               "dass nur ein Teil des Namens passt. Nicht gefunden heisst nicht, "
                               "dass es die Organisation nicht gibt: Schreibweise, Umbenennung "
                               "oder Löschung im Register sind häufige Gründe. Verbindlich sind "
                               "allein der beglaubigte Registerauszug und der Publikationstext "
                               "im SHAB."),
                   "eindeutig": eindeutig, "moeglich": moeglich, "nicht_gefunden": offen,
                   "befunde": befunde,
                   "amtlich_geprueft": len(amtlich),
                   "amtlich_fehler": rest_fehler[:10],
                   "personensuche": hinweise},
                  open(ZIEL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"\n{ZIEL.name} geschrieben.")
    else:
        print("\n(Probelauf, nichts geschrieben. Mit --apply schreiben.)")


if __name__ == "__main__":
    main()

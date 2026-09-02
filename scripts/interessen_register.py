#!/usr/bin/env python3
"""
Registerfunde für das Dashboard freigeben
=========================================
Nimmt die Ergebnisse der Personensuche im Handelsregister und macht daraus eine
Prüfliste. Nur was hier ausdrücklich freigegeben ist, erscheint im Dashboard.

Warum dieser Zwischenschritt
----------------------------
`hr_personen.py` sucht über den Nachnamen und prüft jeden Treffer am
Registerauszug gegen Vorname und Wohngemeinde. Das siebt Namensvettern aus,
aber es bleibt ein Namensabgleich:

  · Bei drei Ratsmitgliedern führt sh.ch keine Adresse. Dort ruht die Zuordnung
    allein auf dem Vornamen.
  · Das Register kennt mehrere Vornamen, die Deklaration nur den Rufnamen.
    «Di Ronco, Joel Christian, in Beringen» trifft auf «Christian Di Ronco» zu,
    ohne dieselbe Person zu sein.
  · Der Abgleich mit der Deklaration läuft über den Firmennamen. Eine anders
    umschriebene Bindung wird als fehlend gemeldet, obwohl sie deklariert ist.

Ein Dashboard, das öffentlich steht und Ratsmitglieder namentlich nennt, darf
solche Hinweise nicht als Tatsache zeigen. Darum entscheidet ein Mensch, Eintrag
für Eintrag, am Registerauszug. Das ist dasselbe Vorgehen wie bei den
Umkehrabstimmungen: Maschine engt ein, Mensch entscheidet.

Status je Eintrag
-----------------
    offen        noch nicht angesehen. Erscheint nicht im Dashboard.
    bestaetigt   am Auszug geprüft, es ist dieses Ratsmitglied, und in der
                 Selbstdeklaration fehlt die Bindung. Erscheint im Dashboard.
    deklariert   es ist dieses Ratsmitglied, aber die Bindung ist bereits
                 deklariert, nur anders umschrieben. Erscheint nicht gesondert.
    verworfen    Namensvetter, beendetes Mandat oder sonst nicht zutreffend.

Ausführen:
    python3 scripts/interessen_register.py           # Prüfliste nachführen
    python3 scripts/interessen_register.py --md      # Liste zum Abarbeiten
"""
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hr_personen as H
import interessen as I

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
QUELLE = DATA / "hr_personen.json"
ZIEL = DATA / "interessen_register.json"
VOLL = DATA / "interessen_register_voll.json"
LISTE = DATA / "interessen_register_pruefliste.md"

# Felder, die ein nicht freigegebener Eintrag in der veroeffentlichten Fassung
# behaelt. Alles andere bleibt in VOLL, das in .gitignore steht.
SCHLANK = ("kennung", "status", "geprueft", "nicht_mehr_gefunden")


def kennung(schluessel):
    """Wiedererkennungsmerkmal eines Eintrags, ohne die Zuordnung zu nennen.

    Der Schluessel lautet «Name|UID» und verbindet damit ein Ratsmitglied mit
    einer Firma. Bei einem verworfenen Fund ist genau diese Verbindung das,
    was nicht oeffentlich stehen soll: sie wurde geprueft und ausgeschieden.
    Der Hash haelt die Entscheidung ueber Laeufe hinweg fest, ohne sie zu
    verraten. Wer den Namen und die UID schon kennt, kann den Hash nachrechnen
    und bestaetigen; ableiten laesst sich aus ihm nichts.
    """
    return hashlib.sha256(schluessel.encode("utf-8")).hexdigest()[:16]


def schlank(e):
    """Ein Eintrag, wie er im oeffentlichen Repository steht."""
    if e.get("status") == "bestaetigt" and not e.get("nicht_mehr_gefunden"):
        return e                      # steht ohnehin im Dashboard
    d = {k: e[k] for k in SCHLANK if e.get(k)}
    d["kennung"] = e.get("kennung") or kennung(e["schluessel"])
    d["status"] = e.get("status", "offen")
    return d


def branche_von(firma, zweck):
    """Branche eines Registerfunds.

    Die Einteilung der deklarierten Organisationen läuft über den Namen
    (`interessen.branche`). Bei Registerfunden steht mehr zur Verfügung: der
    eingetragene Zweck. Er ist die bessere Grundlage, weil ein Firmenname oft
    nichts verrät. «SAH Services GmbH» ordnet sich über den Namen nirgends ein,
    über den Zweck («Förderung der sozialen Integration, Arbeitsintegration
    stellenloser Menschen») eindeutig.

    Der Name geht zuerst, damit die Einteilung mit den deklarierten
    Organisationen zusammenpasst; erst wenn er nichts hergibt, entscheidet der
    Zweck.
    """
    b = I.branche(firma)
    if b != "Übrige":
        return b
    if zweck:
        b = I.branche(zweck)
        if b != "Übrige":
            return b
    return "Übrige"


def vorbehalt(t, ort_bekannt):
    """Woran bei diesem Fund besonders zu denken ist.

    Aus der ersten Handprüfung am 2. September 2026: von fünf maschinell
    bestätigten Kandidaten hielt einer stand. Zwei der vier falschen betrafen
    Gesellschaften in Liquidation, bei denen der Auszug die Organe weiterhin
    ungestrichen führt, und einer eine Person mit abweichender Wohngemeinde.
    Beides steht seither als Vorbehalt an der Karte.
    """
    if t.get("urteil") == "bestaetigt_anderer_ort":
        return "Wohnort weicht ab, möglicherweise eine andere Person gleichen Namens"
    if not ort_bekannt:
        return "keine Adresse hinterlegt, die Zuordnung ruht allein auf dem Vornamen"
    if t.get("firma_besteht") is None:
        return ("nicht geprüft, ob die Firma noch besteht. "
                "python3 scripts/hr_personen.py --firmen-pruefen")
    if re.search(r"\bin Liquidation\b", t.get("firma") or "", re.I):
        return ("Gesellschaft in Liquidation. Der Auszug führt die Organe oft weiter, "
                "auch wenn das Mandat längst beendet ist")
    return None


def kandidaten():
    """Registerfunde, die auf das Ratsmitglied lauten und nicht deklariert sind."""
    if not QUELLE.exists():
        raise SystemExit(f"{QUELLE.name} fehlt. Zuerst hr_personen.py laufen lassen.")
    daten = json.loads(QUELLE.read_text(encoding="utf-8"))
    leute = {p["name"]: p for p in H.mitglieder()}

    raus = []
    # Dieselbe Rechtseinheit kann in der Trefferliste mehrfach stehen, wenn sie
    # den Sitz gewechselt hat: «Naturstein Schweiz GmbH» erscheint bei Jannik
    # Schraff dreimal, einmal mit Sitz Baar, zweimal mit Sitz Beringen, alle
    # drei unter derselben UID. Das ist ein Mandat und darf auch nur einmal in
    # der Prüfliste und im Dashboard stehen. Massgeblich ist die UID, nicht der
    # Firmenname mit Sitz.
    gesehen = set()
    for name, e in sorted(daten["personen"].items()):
        p = leute.get(name)
        if not p:
            continue
        dekl = H.deklarierte_firmen(p)
        ort_bekannt = bool(H.gemeinde(p.get("adresse"), name))
        # Eine Rechtseinheit kann in der Trefferliste unter mehreren Namen
        # stehen, weil das Register frühere Firmennamen mitführt. Jannik Schraff
        # hat «SMG bau gmbh» deklariert; unter derselben UID CHE-115.560.082
        # steht zusätzlich «Naturstein Schweiz GmbH». Wer nur den Namen
        # vergleicht, hält die Umfirmierung für ein zweites, undeklariertes
        # Mandat und legt einem Ratsmitglied etwas zur Last, das es deklariert
        # hat. Massgeblich ist darum die UID: passt irgendein Name dieser
        # Rechtseinheit zur Deklaration, gilt das Mandat als deklariert.
        deklarierte_uid = {t["uid"] for t in e["treffer"]
                           if H.firma_passt(t["firma"], H.alle_deklarationen(p))}
        for t in e["treffer"]:
            if not str(t.get("urteil", "")).startswith("bestaetigt"):
                continue
            if not t.get("aktuell"):
                continue                       # Personeneintrag gestrichen
            # Gelöschte Rechtseinheit: das Mandat kann nicht mehr bestehen. Diese
            # Firmen erscheinen nur, weil die Suche mit «auch gelöschte Firmen»
            # läuft; von Hand findet man sie nicht einmal. Von 170 gefundenen
            # Firmen waren 101 gelöscht, und drei der vier Fehlurteile der ersten
            # Handprüfung gingen darauf zurück.
            if t.get("firma_besteht") is False:
                continue
            if t.get("firma_geloescht"):
                continue
            if t["uid"] in deklarierte_uid:
                continue                       # bereits deklariert, siehe oben
            schluessel = f"{name}|{t['uid']}"
            if schluessel in gesehen:
                continue                       # dieselbe Firma, anderer Sitz
            gesehen.add(schluessel)
            person = t.get("person") or {}
            raus.append({
                "schluessel": schluessel,
                "mitglied": name,
                "fraktion": p.get("fraktion"),
                "firma": t["firma"],
                "uid": t["uid"],
                "sitz": t["sitz"],
                "rechtsform": t["rechtsform"],
                "funktion": person.get("funktion"),
                "zeichnung": person.get("zeichnung"),
                "eintrag": person.get("eintrag"),
                "auszug": f"{H.AUSZUG}?uid={t['uid']}",
                "zweck": H.kuerzen(t.get("zweck"), 400) or None,
                "branche": branche_von(t["firma"], t.get("zweck")),
                "vorbehalt": vorbehalt(t, ort_bekannt),
                "deklariert": H.alle_deklarationen(p),
            })
    return raus


def fruehere():
    """Die Urteile des letzten Laufs, nach Kennung.

    Zuerst aus VOLL, weil dort die Notizen stehen. Fehlt die Datei, tut es die
    veroeffentlichte Fassung: Status und Kennung stehen auch dort, und mehr
    braucht die Uebernahme nicht.
    """
    for datei in (VOLL, ZIEL):
        if not datei.exists():
            continue
        e = json.loads(datei.read_text(encoding="utf-8"))["eintraege"]
        return {x.get("kennung") or kennung(x["schluessel"]): x for x in e}
    return {}


def main():
    neu = kandidaten()
    for k in neu:
        k["kennung"] = kennung(k["schluessel"])
    alt = fruehere()

    eintraege = []
    for k in neu:
        vorher = alt.get(k["kennung"], {})
        k["status"] = vorher.get("status", "offen")
        k["notiz"] = vorher.get("notiz", "")
        if vorher.get("geprueft"):
            k["geprueft"] = vorher["geprueft"]
        eintraege.append(k)

    # Entscheide zu Einträgen, die nicht mehr auftauchen, bleiben erhalten:
    # sie können durch eine spätere Deklaration weggefallen sein.
    weg = [e for s, e in alt.items() if s not in {k["kennung"] for k in neu}]
    for e in weg:
        e["nicht_mehr_gefunden"] = True
        eintraege.append(e)

    kopf = {
        "stand": date.today().isoformat(),
        "hinweis": ("Prüfliste der Registerfunde. Nur Einträge mit status «bestaetigt» "
                    "erscheinen im Dashboard. Massgeblich ist der Registerauszug, "
                    "nicht dieser Namensabgleich."),
    }

    # Die Arbeitsfassung mit allen Feldern und Notizen. Sie steht in .gitignore:
    # ein verworfener Fund nennt ein Ratsmitglied neben einer Firma, die geprüft
    # und ausgeschieden wurde, und das gehört nicht in ein öffentliches
    # Repository.
    VOLL.write_text(json.dumps(dict(kopf, eintraege=eintraege),
                               ensure_ascii=False, indent=1), encoding="utf-8")

    # Die veröffentlichte Fassung. Freigegebene Funde vollständig, denn sie
    # stehen ohnehin im Dashboard; alle übrigen nur als Kennung und Status,
    # damit ein neuer Lauf ein einmal gefälltes Urteil wiederfindet.
    ZIEL.write_text(json.dumps(
        dict(kopf, hinweis=kopf["hinweis"] + " Nicht freigegebene Funde stehen "
             "hier nur als Kennung, die Arbeitsfassung bleibt lokal.",
             eintraege=[schlank(e) for e in eintraege]),
        ensure_ascii=False, indent=1), encoding="utf-8")

    z = {}
    for e in eintraege:
        z[e["status"]] = z.get(e["status"], 0) + 1
    print(f"{ZIEL.name}: {len(eintraege)} Einträge, " +
          ", ".join(f"{n}× {s}" for s, n in sorted(z.items())))

    if "--md" in sys.argv:
        zeilen = ["# Prüfliste: Registerfunde", "",
                  f"Stand {date.today().isoformat()}.", "",
                  "Für jeden Eintrag den Auszug öffnen und den Status setzen: "
                  "`bestaetigt`, `deklariert` oder `verworfen`. Nur `bestaetigt` "
                  "erscheint im Dashboard.", ""]
        for e in eintraege:
            if e["status"] != "offen":
                continue
            zeilen += [f"## {e['mitglied']} ({e.get('fraktion','')})", "",
                       f"**{e['firma']}**, {e['sitz']} ({e['rechtsform']}, {e['uid']})", "",
                       f"- eingetragen als: {e.get('eintrag')}",
                       f"- Funktion: {e.get('funktion')}, {e.get('zeichnung')}",
                       f"- deklariert sind: "
                       + (", ".join(e["deklariert"]) if e["deklariert"] else "keine Firma"),
                       f"- Auszug: {e['auszug']}"]
            if e.get("vorbehalt"):
                zeilen.append(f"- **Vorbehalt:** {e['vorbehalt']}")
            zeilen += ["", "Status: `offen`", "", "---", ""]
        LISTE.write_text("\n".join(zeilen), encoding="utf-8")
        print(f"{LISTE.name} geschrieben.")


if __name__ == "__main__":
    main()

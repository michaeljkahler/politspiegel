#!/usr/bin/env python3
"""
Interessenbindungen zerlegen und zu einem Netz verknüpfen
=========================================================
Die Deklarationen auf sh.ch sind Freitext in wechselnder Schreibweise:

    "Verwaltungsrat & Geschäftsleiter Bytix AG, Zürich"
    "- GLP Schaffhausen, Vorstandsmitglied"
    "Faccani Schuhe AG, Schaffhausen, VR-Präsident"
    "-Präsident Verwaltungskommission Alterszentrum ... Neuhausen am Rheinfall"

Dieses Skript trennt Rolle, Organisation und Ort, ordnet jeder Organisation
eine Branche zu und baut daraus ein Netz mit drei Knotenarten: Ratsmitglied,
Organisation, Branche. Zwei Ratsmitglieder sind verbunden, wenn sie dieselbe
Organisation nennen.

Ausführen:
    python3 scripts/interessen.py            # Bericht
    python3 scripts/interessen.py --apply    # schreibt data/interessen_netz.json
"""
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
QUELLE = DATA / "mitglieder.json"
ZIEL = DATA / "interessen_netz.json"

# Rollenbezeichnungen, längere zuerst, damit "Stiftungsratspräsident" nicht als
# "Präsident" endet
ROLLEN = [
    "Stiftungsratspräsidentin", "Stiftungsratspräsident", "Verwaltungsratspräsident",
    "Vizepräsidentin", "Vizepräsident", "VR-Präsidentin", "VR-Präsident",
    "Vorstandsmitglied", "Vorstandsmitglieder", "Geschäftsleiterin", "Geschäftsleiter",
    "Geschäftsleitung", "Geschäftsführerin", "Geschäftsführer",
    "Stiftungsrätin", "Stiftungsrates", "Stiftungsrat",
    "Verwaltungsrätin", "Verwaltungsrates", "Verwaltungsrat", "Verwaltungskommission",
    "Präsidentin", "Präsident", "Aktuarin", "Aktuar", "Kassierin", "Kassier",
    "Delegierte", "Delegierter", "Beisitzerin", "Beisitzer", "Revisorin", "Revisor",
    "Verwalterin", "Verwalter", "Vorstand", "Beirat", "Mitglied", "Co-Präsidium",
    "Präsidium", "Inhaberin", "Inhaber", "Partnerin", "Partner",
    # zusammengesetzte Ämter, sonst bliebe die Rolle im Organisationsnamen stecken
    "Gemeindepräsidentin", "Gemeindepräsident", "Stadtpräsidentin", "Stadtpräsident",
    "Zunftmeisterin", "Zunftmeister", "Kassiererin", "Kassierer",
    "Programmleitung", "Co-Leitung", "Leiterin", "Leiter", "Leitung",
    "Rechnungsprüferin", "Rechnungsprüfer", "Redaktorin", "Redaktor",
    "Kolumnistin", "Kolumnist", "Beraterin", "Berater", "Director", "Vorsitz",
]
ROLLEN_RE = re.compile(r"\b(" + "|".join(sorted(ROLLEN, key=len, reverse=True)) + r")\b", re.I)

# Branchen: Muster auf dem Organisationsnamen. Reihenfolge zählt.
BRANCHEN = [
    ("Parteien", r"\b(SP|SVP|FDP|GLP|EVP|EDU|CVP|Die Mitte|Grüne|GRÜNE|JUSO|JSVP|"
                 r"Junge Grüne|Jungfreisinn|Piraten)\b|partei"),
    ("Gemeinden und Behörden", r"gemeind|stadtrat|einwohnerrat|grosser stadtrat|"
                               r"schulbeh|zweckverband|abwasserverband|kirchgemeinde|"
                               r"b[üu]rgergemeinde|wahlb[üu]ro|gemeinderat|rechnungspr[üu]fung|"
                               r"ortsmarketing|st[äa]dtebund|metropolitankonferenz|"
                               r"steuergruppe|erziehungsrat|kantonsrat|regierungsrat|"
                               r"^(d[öo]rflingen|beringen|thayngen|neuhausen|hallau|"
                               r"schleitheim|wilchingen|stein am rhein|l[öo]hningen|"
                               r"buchberg|r[üu]dlingen|merishausen|bargen|trasadingen|"
                               r"osterfingen|guntmadingen|schaffhausen)$"),
    ("Gesundheit und Pflege", r"spital|spit[äa]ler|spitex|alterszentrum|pflegeheim|"
                              r"krebsliga|pro senectute|gesundheit|diabetes|lungenliga|"
                              r"rotes kreuz|samariter|psychiatr|arzt|[äa]rzte|apothek"),
    ("Soziales und Hilfswerke", r"sah\b|arbeitshilfswerk|caritas|heilsarmee|"
                                r"betreutes wohnen|sozial|gewaltbetroffen|frauenhaus|"
                                r"asyl|integration|witwen|waisen|kinderheim|behinder|"
                                r"\bsrk\b|rotkreuz|terre des femmes|brava|"
                                r"radikalisierung|\biiz\b|frau macht politik"),
    ("Energie und Umwelt", r"energie|\beks\b|axpo|strom|solar|wasserkraft|umwelt|"
                           r"naturschutz|forst|wald|klima|entsorgung|kehricht|"
                           r"greenpeace|\bwwf\b|vogelwarte|clean-?up|vernetzungsprojekt|"
                           r"lebensraum|gew[äa]sser|pro natura"),
    ("Landwirtschaft und Wein", r"bauernverband|landwirtschaft|rebbau|weinbau|winzer|"
                                r"genussregion|obstbau|tierhalt|z[üu]chter|"
                                r"g[üu]terkorporation|saatgut|traktoren|direktzahlung|"
                                r"quarter horse|\baqha\b|\bfeqha\b|pferde|n[äa]hrstoff"),
    ("Wohnen und Immobilien", r"hauseigent[üu]mer|\bhev\b|mieterverband|mieterinnen|"
                              r"immobilien|wohnbaugenossenschaft|liegenschaft|"
                              r"baugenossenschaft|holzbau|architekt"),
    ("Banken und Versicherungen", r"bank|versicherung|pensionskasse|vorsorge|"
                                  r"raiffeisen|kantonalbank|\bpk\b"),
    ("Verkehr", r"verkehrsbetrieb|\bvbsh\b|bahn|bus|transport|automobil|"
                r"schifffahrt|flugplatz|\bacs\b|\btcs\b|astag|pro velo|"
                r"\bmsc\b|\bmcs\b|strassen"),
    ("Bildung und Wissenschaft", r"schule|bildung|hochschul|universit|kindergarten|"
                                 r"berufsbildung|elternverein|stipendi|\bphsh\b|"
                                 r"jugendparlament|\bpex\b|lehrbetrieb|weiterbildung"),
    ("Kultur und Medien", r"museum|theater|galerie|kunst|musik|bibliothek|radio|"
                          r"zeitung|medien|kultur|chor|bl[äa]serverein|bote\b|ziiting|"
                          r"journalis|kolumn|redakt|herausgeber|bachgesellschaft|"
                          r"zunft|\bpreis\b|fasnacht"),
    ("Sport und Freizeit", r"sport|turnverein|handball|fussball|\bfc\b|schwing|"
                           r"sch[üu]tzen|pfadi|jugendverein|club\b|jodler|"
                           r"m[äa]nnerriege|\bslrg\b|wandern|ski|tennis"),
    ("Wirtschaft und Gewerbe", r"\bag\b|gmbh|genossenschaft|gewerbeverband|"
                               r"handelskammer|\bkmu\b|arbeitgeber|industrie|"
                               r"unternehmen|treuhand|wirtschaft"),
    ("Berufs- und Interessenverbände", r"verband|verein|gewerkschaft|syndicat|"
                                       r"kommission|stiftung|f[öo]rderverein"),
]

# Ortsnamen, die häufig hinten angehängt sind und nicht zur Organisation gehören
ORTE = {"schaffhausen", "neuhausen", "neuhausen am rheinfall", "stein am rhein",
        "thayngen", "beringen", "dörflingen", "wilchingen", "osterfingen",
        "trasadingen", "hallau", "oberhallau", "löhningen", "schleitheim",
        "merishausen", "bargen", "buchberg", "rüdlingen", "buch", "altdorf",
        "zürich", "bern", "winterthur", "basel", "st. gallen", "aargau",
        "kanton schaffhausen", "kanton sh", "sh", "region"}


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s.lower()).strip()


def zerlegen(text):
    """(rolle, organisation, ort) aus einer Zeile der Deklaration."""
    t = re.sub(r"^[\s\-–•*]+", "", text or "").strip().rstrip(".;,")
    t = re.sub(r"\(www\.[^)]+\)|\(https?://[^)]+\)", "", t).strip()
    if not t:
        return (None, None, None)

    rollen = [m.group(1) for m in ROLLEN_RE.finditer(t)]
    rest = ROLLEN_RE.sub(" ", t)
    rest = re.sub(r"\s*[&,/]\s*(und\s*)?$", "", rest)
    rest = re.sub(r"^[\s&,/-]+|[\s&,/-]+$", "", re.sub(r"\s{2,}", " ", rest)).strip()

    # Ort abtrennen: letztes Komma-Glied, wenn es ein bekannter Ort ist
    ort = None
    teile = [x.strip() for x in rest.split(",") if x.strip()]
    if len(teile) > 1 and norm(teile[-1]) in {norm(o) for o in ORTE}:
        ort = teile[-1]
        teile = teile[:-1]
    organisation = ", ".join(teile).strip(" ,-&/")
    organisation = re.sub(r"\s{2,}", " ", organisation)
    rolle = ", ".join(dict.fromkeys(r.strip() for r in rollen)) or None
    return (rolle, organisation or None, ort)


def branche(organisation):
    o = organisation or ""
    for name, muster in BRANCHEN:
        if re.search(muster, o, re.I):
            return name
    return "Übrige"


def schluessel(organisation):
    """Vereinheitlichter Schlüssel, damit Schreibvarianten zusammenfallen."""
    k = norm(organisation)
    k = re.sub(r"\b(ag|gmbh|verein|der|die|das|des|kanton|kt)\b", " ", k)
    return re.sub(r"[^a-z0-9]+", " ", k).strip()


def netz_bauen(mitglieder):
    knoten, kanten = {}, []
    org_mitglieder = defaultdict(list)

    for m in mitglieder:
        mid = f"m:{m['nachname']}|{m['vorname']}"
        knoten[mid] = {"id": mid, "typ": "mitglied", "label": m["name"],
                       "partei": m.get("partei", ""), "fraktion": m.get("fraktion", ""),
                       "bild": bool(m.get("bild")), "anzahl": 0}
        for eintrag in m.get("interessenbindungen", []):
            rolle, org, ort = zerlegen(eintrag)
            if not org or len(org) < 3:
                continue
            k = schluessel(org)
            if not k:
                continue
            oid = f"o:{k}"
            br = branche(org)
            if oid not in knoten:
                knoten[oid] = {"id": oid, "typ": "organisation", "label": org,
                               "branche": br, "ort": ort, "anzahl": 0}
            bid = f"b:{br}"
            if bid not in knoten:
                knoten[bid] = {"id": bid, "typ": "branche", "label": br, "anzahl": 0}
            kanten.append({"von": mid, "nach": oid, "rolle": rolle, "roh": eintrag})
            org_mitglieder[oid].append(mid)
            knoten[mid]["anzahl"] += 1
            knoten[oid]["anzahl"] += 1
            knoten[bid]["anzahl"] += 1

    # Organisation -> Branche als eigene Kante, damit sich Cluster bilden
    for n in list(knoten.values()):
        if n["typ"] == "organisation":
            kanten.append({"von": n["id"], "nach": f"b:{n['branche']}", "rolle": None,
                           "roh": None, "art": "branche"})

    geteilt = {oid: ms for oid, ms in org_mitglieder.items() if len(set(ms)) > 1}
    return list(knoten.values()), kanten, geteilt


def main():
    daten = json.load(open(QUELLE, encoding="utf-8"))
    mitglieder = daten["mitglieder"]
    knoten, kanten, geteilt = netz_bauen(mitglieder)

    orgs = [k for k in knoten if k["typ"] == "organisation"]
    print(f"{len(mitglieder)} Ratsmitglieder, "
          f"{sum(len(m['interessenbindungen']) for m in mitglieder)} Deklarationen")
    print(f"{len(orgs)} Organisationen, {len([k for k in kanten if k.get('art')!='branche'])} Mandate")
    print(f"{len(geteilt)} Organisationen mit mehr als einem Ratsmitglied\n")

    print("Branchen:")
    for b, n in Counter(o["branche"] for o in orgs).most_common():
        print(f"  {n:4}  {b}")

    print("\nOrganisationen mit mehreren Ratsmitgliedern:")
    nach_id = {k["id"]: k for k in knoten}
    for oid, ms in sorted(geteilt.items(), key=lambda x: -len(set(x[1])))[:14]:
        namen = ", ".join(sorted({nach_id[m]["label"] for m in ms}))
        print(f"  {len(set(ms))}  {nach_id[oid]['label'][:44]:44} | {namen[:70]}")

    print("\nStichprobe der Zerlegung:")
    for m in mitglieder[:4]:
        for e in m["interessenbindungen"][:2]:
            r, o, ort = zerlegen(e)
            print(f"  {m['name'][:18]:18} | Rolle: {str(r)[:26]:26} | Org: {str(o)[:34]:34} | {branche(o)}")

    if "--apply" in sys.argv:
        json.dump({"stand": daten.get("stand"), "quelle": daten.get("quelle"),
                   "knoten": knoten, "kanten": kanten},
                  open(ZIEL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"\n{ZIEL.name} geschrieben.")
    else:
        print("\n(Probelauf, nichts geschrieben. Mit --apply schreiben.)")


if __name__ == "__main__":
    main()

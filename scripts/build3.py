#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kantonsrat Schaffhausen · Kantonsratsspiegel — Generator
========================================================
Baut das vollständige Dashboard im Design vom 01.09.2026 (siehe
docs/DESIGN_entscheide.md): Seitenleiste, sieben Rubriken, Dunkelmodus,
neutrale Ja/Nein-Farben, richtungskorrigierte Quoten.

Gegenüber build2.py neu:
  · sieben statt fünf Rubriken, «Mitglied im Detail» geht in «Ratsmitglieder» auf
  · «Wer stimmt wie ich?» ist eingebaut, nicht mehr eine zweite Datei
  · CSS und JS liegen als eigene Dateien in scripts/assets und werden beim Bauen
    eingebettet. Das war bei build2.py die grösste Fehlerquelle: dort steckte
    alles in Python-Strings, in denen jede geschweifte Klammer verdoppelt werden
    musste.
  · kompakte Datenkodierung: Stimmen als Zeichenkette statt als Liste von
    Wörtern, das spart rund 70 % Dateigrösse
  · Bilddownload im Instagram-Hochformat für 16 Motive: Abstimmungen,
    alle neun Ranglisten, Fraktionsvergleich, Profilkarte und
    Interessenbindungen je Ratsmitglied, und das eigene Matching-Ergebnis

Ausführen:  python3 scripts/build3.py   ->  output/dashboard.html
"""

import collections
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ASSETS = pathlib.Path(__file__).resolve().parent / "assets"
OUT = ROOT / "output" / "dashboard.html"

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from prototyp import (betreff, flach, kuerze, ueberschrift,          # noqa: E402
                      sess_sort_key, de_datum, FRAK_KEY, PARTEI_KEY,
                      frak_key, partei_key, split_titel)

# Stimmen kompakt: ein Zeichen je Abstimmung
KODE = {"Ja": "J", "Nein": "N", "Enth": "E", "V/A/N": "A"}

# Rubriken der Seitenleiste
NAV = [
    ("neu",      "Zuletzt entschieden", "neu"),
    ("votes",    "Abstimmungen",        "vote"),
    ("members",  "Ratsmitglieder",      "people"),
    ("frak",     "Fraktionen",          "group"),
    ("themen",   "Themen",              "tag"),
    ("rang",     "Ranglisten",          "rank"),
    ("netz",     "Interessenbindungen", "netz"),
    ("match",    "Wer stimmt wie ich?", "match"),
]

# Matching: Auswahlregeln (vgl. docs/KONZEPT_waehler-matching.md)
# Drei Umfänge zur Wahl. Die Fragen sind in allen Modi nach Trennschärfe
# geordnet, der kurze Modus ist also der Anfang des langen.
MODI = [12, 36, 72]
MIN_BETEILIGUNG = 30
MIN_GEMEINSAM = 5
# Anteil, den die unterlegene Seite mindestens halten muss, damit eine
# Abstimmung als Frage taugt. Bei 15 Prozent fallen die praktisch einstimmigen
# Geschäftsberichts- und Kreditgenehmigungen weg, die den Rat nicht teilen.
MIN_MINDERHEIT = 0.15
# Nur Abstimmungen, deren Richtung belegt oder bewusst festgelegt ist
GEPRUEFTE_HERKUNFT = {"protokoll", "manuell", "konvention"}


# ─────────────────────────────────────────────────────────────────────────────
# Daten
# ─────────────────────────────────────────────────────────────────────────────

def umkehr_lesen():
    pfad = DATA / "umkehr_zuordnung.json"
    if not pfad.exists():
        return {}
    return {e["schluessel"]: e
            for e in json.loads(pfad.read_text(encoding="utf-8"))["zuordnung"]}


def zusatz(name, standard):
    """Zusatzdaten, die nicht in jedem Projektstand vorliegen müssen."""
    pfad = DATA / name
    if not pfad.exists():
        print(f"  Hinweis: {name} fehlt, der entsprechende Teil bleibt leer.")
        return standard
    return json.loads(pfad.read_text(encoding="utf-8"))


def netz_mit_register():
    """Beziehungsnetz aus der Selbstdeklaration, ergänzt um freigegebene
    Registerfunde.

    Jede Kante trägt neu ein Feld «q» für die Herkunft: «d» für die
    Selbstdeklaration auf sh.ch, «r» für eine Bindung, die nur im
    Handelsregister steht. Das Dashboard färbt danach ein, blau und gelb.

    Aufgenommen wird ausschliesslich, was in data/interessen_register.json den
    Status «bestaetigt» trägt, also von Hand am Registerauszug geprüft ist. Die
    Rohfunde der Personensuche sind Namensabgleiche und kommen hier nicht an.
    """
    netz = zusatz("interessen_netz.json", {"knoten": [], "kanten": []})
    for k in netz.get("kanten", []):
        if k.get("art") != "branche":
            k["q"] = "d"

    reg = zusatz("interessen_register.json", {"eintraege": []})
    frei = [e for e in reg.get("eintraege", [])
            if e.get("status") == "bestaetigt" and not e.get("nicht_mehr_gefunden")]
    if not frei:
        netz["reg_stand"] = reg.get("stand")
        return netz

    vorhanden = {n["id"] for n in netz["knoten"]}
    nach_name = {n["label"]: n["id"] for n in netz["knoten"] if n["typ"] == "mitglied"}
    neu_k = neu_o = neu_b = 0
    for e in frei:
        mid = nach_name.get(e["mitglied"])
        if not mid:
            continue
        oid = "o:reg:" + re.sub(r"\W+", "", norm_klein(e["firma"]))[:40]
        if oid not in vorhanden:
            netz["knoten"].append({"id": oid, "typ": "organisation",
                                   "label": e["firma"], "ort": e.get("sitz"),
                                   "branche": e.get("branche"),
                                   "q": "r", "uid": e.get("uid"),
                                   "url": e.get("auszug"), "anzahl": 0})
            vorhanden.add(oid)
            neu_o += 1
            # An die Branche hängen wie die deklarierten Organisationen auch,
            # sonst hinge der Registerfund allein am Ratsmitglied und fiele aus
            # der thematischen Ordnung des Netzes heraus. Die Branche stammt aus
            # dem Firmennamen und, wo der nichts hergibt, aus dem eingetragenen
            # Zweck.
            b = e.get("branche")
            if b:
                bid = f"b:{b}"
                if bid not in vorhanden:
                    netz["knoten"].append({"id": bid, "typ": "branche",
                                           "label": b, "anzahl": 0})
                    vorhanden.add(bid)
                    neu_b += 1
                netz["kanten"].append({"von": oid, "nach": bid, "rolle": None,
                                       "roh": None, "art": "branche"})
        netz["kanten"].append({"von": mid, "nach": oid, "q": "r",
                               "rolle": e.get("funktion") or "im Handelsregister eingetragen",
                               "roh": e.get("eintrag") or ""})
        neu_k += 1
    for n in netz["knoten"]:
        if n["typ"] == "organisation":
            n["anzahl"] = sum(1 for k in netz["kanten"] if k["nach"] == n["id"])
    netz["reg_stand"] = reg.get("stand")
    print(f"  Netz: {neu_k} Kanten und {neu_o} Organisationen aus dem "
          f"Handelsregister ergänzt, {neu_b} neue Branchen (freigegeben von "
          f"{len(reg.get('eintraege', []))} geprüften Funden)")
    return netz


def norm_klein(s):
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def ausgeschieden(d):
    """Wer in der laufenden Legislatur ausgeschieden ist.

    Massgeblich ist die Namensliste der jüngsten Sitzung. Sie führt den
    vollständigen Rat, Abwesende eingeschlossen: eine Abwesenheit steht als
    Stimme «A» und nicht als fehlender Name. Wer dort nicht mehr steht, aber
    früher in der Legislatur mitgestimmt hat, ist ausgeschieden.

    Nicht massgeblich ist der Abgleich mit mitglieder.json. Diese Datei entsteht
    aus den contentids in mitglieder_ids.json, und die Liste kann unvollständig
    sein: sie zählt derzeit 59 Einträge, der Rat hat 60 Sitze. Ein erster
    Versuch, das Ausscheiden über diese Differenz zu bestimmen, hat darum Lukas
    Bringolf als ausgeschieden markiert, obwohl er der Justizkommission
    vorsitzt und in der jüngsten Sitzung mitgestimmt hat. «Fehlt in unseren
    Stammdaten» und «nicht mehr im Rat» sind zwei verschiedene Dinge, und die
    Verwechslung stellt eine falsche Behauptung über eine namentlich genannte
    Person ins Netz.

    Zurückgegeben wird je Person die letzte Sitzung, an der sie teilgenommen
    hat. Mehr lässt sich nicht belegen, ein Rücktrittsdatum steht in keiner der
    Quellen.

    Nur für die laufende Legislatur sinnvoll: in abgeschlossenen sind alle
    ausgeschieden, dort wäre der Vermerk nichts als Lärm.
    """
    leg = d["aktuelle_legislatur"]
    S = sorted((s for s in d["sessions"] if s.get("legislatur") == leg),
               key=sess_sort_key)
    if len(S) < 2:
        return {}

    im_rat = {f"{p['nachname']}|{p['vorname']}" for p in S[-1]["members"]}
    letzte = {}
    for s in S:
        for p in s["members"]:
            letzte[f"{p['nachname']}|{p['vorname']}"] = s["sitzung"]

    raus = {k: v for k, v in letzte.items() if k not in im_rat}
    if raus:
        print(f"  Ausgeschieden in der laufenden Legislatur: {len(raus)} "
              f"({', '.join(sorted(k.replace('|', ' ') for k in raus))})")

    # Wer mitstimmt, aber kein Profil hat, ist eine Lücke in den Stammdaten und
    # kein Ausscheiden. Sie gehört gemeldet, damit die contentid nachgetragen
    # wird, sonst fehlen Bild und Interessenbindungen dieser Person.
    m = zusatz("mitglieder.json", {"mitglieder": []})
    profile = {p.get("name") or f"{p.get('vorname','')} {p.get('nachname','')}".strip()
               for p in m.get("mitglieder", [])}
    if profile:
        ohne = sorted(f"{k.split('|')[1]} {k.split('|')[0]}".strip()
                      for k in im_rat
                      if f"{k.split('|')[1]} {k.split('|')[0]}".strip() not in profile)
        if ohne:
            print(f"  ! Ohne Profil auf sh.ch, obwohl im Rat: {', '.join(ohne)}. "
                  f"Auf sh.ch fehlt der Personenkasten, darum gibt es keine contentid "
                  f"und damit kein Bild und keine Interessenbindungen.")
    return raus


def ohne_profil(d):
    """Wer im Rat sitzt, aber auf sh.ch keinen Personenkasten hat.

    Ohne Kasten gibt es keine contentid, ohne contentid kein Profil, also weder
    Porträt noch Interessenbindungen. Das ist eine Lücke auf sh.ch und keine
    Aussage über die Person. Das Dashboard sagt das im Profil, statt eine leere
    Seite zu zeigen, die nach Fehler aussieht.
    """
    leg = d["aktuelle_legislatur"]
    S = sorted((s for s in d["sessions"] if s.get("legislatur") == leg),
               key=sess_sort_key)
    if not S:
        return []
    m = zusatz("mitglieder.json", {"mitglieder": []})
    profile = {p.get("name") or f"{p.get('vorname','')} {p.get('nachname','')}".strip()
               for p in m.get("mitglieder", [])}
    if not profile:
        return []
    return sorted(f"{p['nachname']}|{p['vorname']}" for p in S[-1]["members"]
                  if f"{p['vorname']} {p['nachname']}".strip() not in profile)


def personen_payload():
    """Profile der Ratsmitglieder aus mitglieder.json, auf das Nötige gekürzt."""
    d = zusatz("mitglieder.json", {"mitglieder": [], "stand": None})
    # Freigegebene Registerfunde je Ratsmitglied, damit das Profil zeigt, was in
    # der Selbstdeklaration fehlt, ohne dass man ins Beziehungsnetz wechseln muss.
    reg = zusatz("interessen_register.json", {"eintraege": []})
    nach_person = {}
    for e in reg.get("eintraege", []):
        if e.get("status") != "bestaetigt" or e.get("nicht_mehr_gefunden"):
            continue
        nach_person.setdefault(e["mitglied"], []).append({
            "f": e["firma"], "o": e.get("sitz"), "r": e.get("funktion"),
            "u": e.get("uid"), "url": e.get("auszug")})

    raus = []
    for m in d.get("mitglieder", []):
        raus.append({
            "k": f"{m.get('nachname','')}|{m.get('vorname','')}",
            "n": m.get("name") or f"{m.get('vorname','')} {m.get('nachname','')}".strip(),
            "f": m.get("fraktion") or "",
            "p": m.get("partei") or "",
            "be": m.get("beruf") or "",
            "se": m.get("seit") or "",
            "ge": m.get("gemeinde") or m.get("wohnort") or "",
            # Die Quelle setzt teils Aufzählungszeichen davor, die hier stören
            "ib": [re.sub(r"^[\s\-–—•*]+", "", t).strip()
                   for t in (m.get("interessenbindungen") or []) if t and t.strip()],
            # Nur im Handelsregister gefunden, von Hand am Auszug bestätigt
            "hr": nach_person.get(
                m.get("name") or f"{m.get('vorname','')} {m.get('nachname','')}".strip(), []),
            "url": m.get("url") or "",
            # Porträt als base64-JPEG, im Schnitt 6 KB. Ohne Präfix gespeichert,
            # das setzt die Anzeige davor.
            "bi": m.get("bild") or "",
        })
    return {"stand": d.get("stand"), "quelle": d.get("quelle"), "liste": raus}


def sitzungen_lesen():
    d = json.loads((DATA / "all_sessions.json").read_text(encoding="utf-8"))
    d["sessions"].sort(key=sess_sort_key, reverse=True)      # neueste zuerst
    return d


def vote_payload(sess, v, umkehr):
    schluessel = f"{sess['sitzung']} #Nr{v['nr']}"
    u = umkehr.get(schluessel, {})
    titel_h, referenz = ueberschrift(v)
    inv = bool(v.get("richtung_invertiert"))
    p = {
        "nr": str(v.get("nr")),
        "t": titel_h,
        "tr": flach(v.get("titel")),                  # Originaltitel für Tooltip
        "d": flach(v.get("details")),
        "g": flach(v.get("geschaeft")),
        "b": betreff(v.get("geschaeft")),
        "ty": flach(v.get("typ")),
        "th": v.get("thema_name") or "",
        "tg": v.get("thema_gruppe"),
    }
    if referenz:
        p["rf"] = referenz
    # Schlagworte der dreistufigen Hierarchie und Abstimmungsform
    for feld, kurz_ in (("tags_form", "tf"), ("tags_ueberthema", "t1"),
                        ("tags_unterthema", "t2"), ("tags_detail", "t3")):
        werte = v.get(feld) or []
        if werte:
            p[kurz_] = werte
    if v.get("kontext"):
        p["kx"] = flach(v["kontext"])
        if v.get("kontext_quelle"):
            p["kq"] = v["kontext_quelle"]
    if v.get("stichworte"):
        p["sw"] = v["stichworte"]
    if inv:
        p["inv"] = 1
        p["iv"] = flach(v.get("inverted_note"))
        if u.get("herkunft"):
            p["hk"] = u["herkunft"]
        if u.get("protokoll_beleg"):
            p["bl"] = kuerze(u["protokoll_beleg"], 300)
    elif v.get("richtung_invertiert") is None and v.get("inverted_note"):
        p["inv"] = 0                                  # markiert, aber ungeklärt
        p["iv"] = flach(v.get("inverted_note"))
    return p


def sessions_payload(d, umkehr):
    raus = []
    for s in d["sessions"]:
        name, datum, zeit = split_titel(s["sitzung"])
        prot = (s.get("protokolle") or [{}])[0]
        raus.append({
            "s": s["sitzung"],
            "n": name,
            "dt": datum,
            "z": zeit,
            "leg": s.get("legislatur"),
            "q": s.get("quelle") or "",
            "pu": prot.get("url") or "",
            "v": [vote_payload(s, v, umkehr) for v in s["votes"]],
            "m": [{"n": f"{m['nachname']}|{m['vorname']}",
                   "f": m["fraktion"],
                   "p": (m["partei"] or "").strip(),
                   "v": "".join(KODE.get(x, "A") for x in m["votes"])}
                  for m in s["members"]],
        })
    return raus


# ─────────────────────────────────────────────────────────────────────────────
# Matching: Fragen wählen
# ─────────────────────────────────────────────────────────────────────────────

# Motionen und Postulate, über die der Rat direkt befindet, tragen keine
# Kommissionszuordnung und darum kein thema_gruppe. Sie sind aber die politisch
# aussagekräftigsten Abstimmungen überhaupt: 94 Stück allein in dieser
# Legislatur, darunter Tempo 30, Konversionsmassnahmen, E-Zigaretten. Sie nur
# wegen einer fehlenden Zuordnung wegzulassen, verarmt das Matching.
#
# Ersatzweise wird die Sachgruppe aus tags_ueberthema abgeleitet. Das Thema
# steuert allein die Streuung über die Sachgebiete und die Beschriftung der
# Karte. In die Richtungskorrektur und in die Übereinstimmungsrechnung geht es
# nicht ein, ein Fehlgriff kostet also Ausgewogenheit, nie Richtigkeit.
UEBERTHEMA_GRUPPE = {
    "Finanzen und Steuern": "6",
    "Staat und Politik": "1",
    "Sicherheit und Recht": "1",
    "Gesundheit und Soziales": "8",
    "Wirtschaft und Arbeit": "9",
    "Bildung, Kultur und Sport": "4",
    "Umwelt, Energie und Klima": "7",
    "Raum, Bau und Verkehr": "7",
}


def thema_ersatz(v, gruppen):
    """Sachgruppe und Name, notfalls aus dem Überthema abgeleitet."""
    if v.get("thema_gruppe"):
        return v["thema_gruppe"], v.get("thema_name"), False
    for t in (v.get("tags_ueberthema") or []):
        g = UEBERTHEMA_GRUPPE.get(flach(t))
        if g:
            return g, gruppen.get(g), True
    return None, None, False


def matching_payload(d, umkehr):
    """Trennschärfste Sachabstimmungen der laufenden Legislatur.

    Auswahlregeln:
      · nur die laufende Legislatur
      · nur Abstimmungen aus Sitzungen mit publiziertem Wortprotokoll
      · nur Abstimmungen mit geklärter Richtung; bei Umkehrabstimmungen muss
        die Richtung am Protokoll geprüft oder per Konvention festgelegt sein
      · geordnet nach Trennschärfe, also danach, wie stark die Abstimmung die
        Fraktionen geteilt hat
      · nur Abstimmungen, bei denen die unterlegene Seite mindestens
        MIN_MINDERHEIT des Ergebnisses hält. Eine Vorlage, die 57:0 durchgeht,
        ist keine Frage: sie ordnet niemanden zu und schiebt bei jedem Nutzer
        alle Übereinstimmungswerte gleichmässig nach oben.
      · je Geschäft zuerst die trennschärfste Abstimmung, danach im Ringverfahren
        die zweite, dritte und so weiter. Der Kurzmodus bleibt dadurch breit
        gestreut, die langen Modi gehen in dieselben Vorlagen in die Tiefe.

    Anders als scripts/matching.py wird die Richtung korrigiert: bei
    Umkehrabstimmungen zählt ein Nein im Rat als inhaltliche Zustimmung.
    Ausgeliefert wird die volle geordnete Liste; welchen Umfang der Nutzer
    beantwortet, entscheidet er im Dashboard (12, 36 oder 72 Fragen).
    """
    leg = d["aktuelle_legislatur"]
    S = [s for s in d["sessions"] if s.get("legislatur") == leg]
    if not S:
        return None
    tgruppen = d.get("themen_gruppen") or {}
    aktuell = S[0]["members"]
    fsize = collections.Counter(m["fraktion"] for m in aktuell)
    frak = [f for f, _ in fsize.most_common()]
    maxFragen = max(MODI)

    def wmean(ps, ws):
        return sum(p * w for p, w in zip(ps, ws)) / sum(ws) if ws else 0.0

    ohne_protokoll = 0
    kandidaten = []
    for si, s in enumerate(S):
        if not (s.get("protokolle") or []):
            ohne_protokoll += len(s["votes"])
            continue                                       # kein Wortprotokoll
        for i, v in enumerate(s["votes"]):
            tg, tname, geerbt = thema_ersatz(v, tgruppen)
            if not tg:
                continue
            if not ist_sachfrage(v):
                continue                                   # reine Verfahrensfrage
            if f"{s['sitzung']} #Nr{v['nr']}" in FRAGE_AUSSCHLUSS:
                continue                                   # Quellen widersprechen sich
            inv = v.get("richtung_invertiert")
            if inv is None:
                continue                                   # Richtung ungeklärt
            u = umkehr.get(f"{s['sitzung']} #Nr{v['nr']}")
            if inv and (not u or u.get("herkunft") not in GEPRUEFTE_HERKUNFT):
                continue                                   # Umkehr nicht geprüft
            fja = collections.Counter(); fnein = collections.Counter()
            ja = nein = 0
            for m in s["members"]:
                roh = m["votes"][i] if i < len(m["votes"]) else None
                if roh not in ("Ja", "Nein"):
                    continue
                # Richtungskorrektur: bei Umkehr ist ein Nein die Zustimmung
                dafuer = (roh == "Nein") if inv else (roh == "Ja")
                if dafuer:
                    ja += 1; fja[m["fraktion"]] += 1
                else:
                    nein += 1; fnein[m["fraktion"]] += 1
            if ja + nein < MIN_BETEILIGUNG:
                continue
            if min(ja, nein) / (ja + nein) < MIN_MINDERHEIT:
                continue                                   # praktisch einstimmig
            ps, ws = [], []
            for f in frak:
                t = fja[f] + fnein[f]
                if t >= 3:
                    ps.append(fja[f] / t); ws.append(fsize[f])
            if len(ps) < 3:
                continue
            mu = wmean(ps, ws)
            trenn = wmean([(p - mu) ** 2 for p in ps], ws) ** 0.5
            kandidaten.append({
                "si": si, "i": i, "trenn": trenn, "inv": bool(inv),
                "geschaeft": flach(v.get("geschaeft")),
                "gkey": gruppen_key(v, si, i),
                "wortlaut": flach(v.get("details")) or flach(v.get("titel")),
                "tg": tg, "thema": tname, "tgeerbt": geerbt,
                "kurz": frage_text(v),
            })

    # Ringverfahren: erst die beste Abstimmung jedes Geschäfts, dann die zweite
    # jedes Geschäfts und so fort. Innerhalb einer Runde entscheidet wieder die
    # Trennschärfe. Nur die beste je Geschäft zu nehmen, kostete zu viel: von
    # 253 Sachabstimmungen der Legislatur blieben so 58 Fragen übrig, von denen
    # bloss 23 den Rat überhaupt teilten.
    # Derselbe Antrag kommt zweimal vor die Abstimmung, wenn eine sofortige
    # zweite Lesung beschlossen wird: am 19.05.2025 stand der Antrag zur
    # Neunmonatsfrist des Obergerichts wörtlich gleich zweimal auf der Liste.
    # Zweimal dieselbe Frage zu stellen, hiesse dieselbe Haltung doppelt zu
    # gewichten. Es bleibt die trennschärfste der gleichlautenden Abstimmungen.
    gesehen = {}
    for c in sorted(kandidaten, key=lambda c: -c["trenn"]):
        k = (c["gkey"], re.sub(r"\W+", "", c["wortlaut"].lower())[:180])
        gesehen.setdefault(k, c)
    kandidaten = list(gesehen.values())

    gruppen = collections.defaultdict(list)
    for c in kandidaten:
        gruppen[c["gkey"]].append(c)
    for g in gruppen.values():
        g.sort(key=lambda c: -c["trenn"])
    reihe = []
    for runde in range(max(len(g) for g in gruppen.values()) if gruppen else 0):
        reihe += sorted((g[runde] for g in gruppen.values() if len(g) > runde),
                        key=lambda c: -c["trenn"])

    # Thematische Streuung, mitwachsend mit dem Umfang: bei 12 Fragen höchstens
    # drei je Themengruppe, bei 72 entsprechend mehr. Reicht der Vorrat nicht,
    # wird die Grenze aufgehoben, damit die langen Modi voll werden.
    n_themen = max(1, len(set(c["tg"] for c in reihe)))
    grenze = max(3, -(-maxFragen // n_themen))
    gewaehlt, pro_thema = [], collections.Counter()
    for c in reihe:
        if pro_thema[c["tg"]] >= grenze:
            continue
        gewaehlt.append(c); pro_thema[c["tg"]] += 1
        if len(gewaehlt) == maxFragen:
            break
    if len(gewaehlt) < maxFragen:
        drin = set(id(c) for c in gewaehlt)
        for c in reihe:
            if id(c) in drin:
                continue
            gewaehlt.append(c)
            if len(gewaehlt) == maxFragen:
                break

    # Von Hand geschriebene Fragetexte haben Vorrang. Sie benennen, worüber
    # wirklich abgestimmt wurde: bei einem Antrag innerhalb einer Vorlage ist
    # das nicht dasselbe wie das übergeordnete Geschäft.
    texte = {}
    tpfad = DATA / "frage_texte.json"
    if tpfad.exists():
        texte = {e["schluessel"]: e
                 for e in json.loads(tpfad.read_text(encoding="utf-8"))["fragen"]}

    kontext = {}
    kpfad = DATA / "frage_kontext.json"
    if kpfad.exists():
        kontext = json.loads(kpfad.read_text(encoding="utf-8"))

    def kontext_key(s, nr):
        halb = ("V" if "Vormittag" in s["sitzung"] else
                "N" if "Nachmittag" in s["sitzung"] else
                "A" if "Abend" in s["sitzung"] else "X")
        return f"{s.get('cid')}_{halb}_{nr}"

    fragen = []
    ohne_text = 0
    for c in gewaehlt:
        s = S[c["si"]]
        v = s["votes"][c["i"]]
        k = kontext.get(kontext_key(s, v["nr"]), {})
        hand = texte.get(f"{s['sitzung']}#{v['nr']}")
        if not hand:
            ohne_text += 1
        # Der frühere Rückfall auf v["kontext"] ist bewusst weg: dieses Feld
        # enthält durchgehend Resultatsätze aus dem Protokoll («wird mit 36:17
        # abgelehnt»), also das Ergebnis und keine Einordnung der Sache.
        fragen.append({
            "kurz": (hand or {}).get("frage") or c["kurz"],
            "kontext": (hand or {}).get("kontext") or c["geschaeft"],
            "zus": (hand or {}).get("zusammenfassung"),
            # Bei redigierten Fragen zählt allein, was dort steht. Ein leeres
            # Feld heisst «kein belegtes Argument», nicht «bitte auffüllen»:
            # die Texte in frage_kontext.json wurden für die alte, weiter
            # gefasste Fragestellung geschrieben und passen nicht mehr.
            #
            # Zitate erscheinen nur paarweise. Stünde nur eine Seite da, läse
            # sich die Karte einseitig, obwohl bloss das Gegenstück fehlt.
            "pro": paar(hand, k)[0],
            "contra": paar(hand, k)[1],
            "geprueft": bool(hand),
            "thema": c["thema"], "inv": c["inv"],
            "sitzung": s["sitzung"], "nr": str(v["nr"]),
            "trenn": round(c["trenn"], 3),
            # Worüber laut Excel abgestimmt wurde, zur Kontrolle auf der Karte
            "roh": kuerze(flach(v.get("details")) or flach(v.get("titel")), 260),
            "pu": ((s.get("protokolle") or [{}])[0]).get("url") or "",
        })
    if ohne_text:
        print(f"  Hinweis: {ohne_text} Fragen ohne handgeschriebenen Text, "
              "dort steht der Betreff des Geschäfts")

    def stimme(s, idx, nach, vor, inv):
        for m in s["members"]:
            if m["nachname"] == nach and m["vorname"] == vor:
                roh = m["votes"][idx] if idx < len(m["votes"]) else None
                if roh not in ("Ja", "Nein"):
                    return None
                dafuer = (roh == "Nein") if inv else (roh == "Ja")
                return "J" if dafuer else "N"
        return None

    mitglieder = []
    for m in aktuell:
        mitglieder.append({
            "n": f"{m['vorname']} {m['nachname']}".strip(),
            "f": m["fraktion"],
            "p": (m["partei"] or "").strip(),
            "s": [stimme(S[c["si"]], c["i"], m["nachname"], m["vorname"], c["inv"])
                  for c in gewaehlt],
        })
    # Die Modi richten sich nach dem, was wirklich da ist. Reicht der Vorrat für
    # den grössten Modus nicht, tritt an dessen Stelle die verfügbare Zahl.
    verfuegbar = len(gewaehlt)
    modi = sorted({m for m in MODI if m <= verfuegbar} |
                  ({verfuegbar} if verfuegbar < max(MODI) else set()))
    if not modi:
        modi = [verfuegbar]
    print(f"  Matching: {len(kandidaten)} taugliche Abstimmungen, {len(gruppen)} Geschäfte, "
          f"{verfuegbar} Fragen ({ohne_protokoll} ohne Protokoll übersprungen), "
          f"Modi {modi}")
    return {"fragen": fragen, "mitglieder": mitglieder, "fraktionen": frak,
            "min": MIN_GEMEINSAM, "leg": leg, "modi": modi}


# Formen, über die nicht in der Sache entschieden wird
FORM_VERFAHREN = {"Ordnungsantrag", "Traktandenliste", "Fristverlängerung",
                  "Rückkommen", "Rückweisung", "2. Lesung"}
# Formulierungen, die eine reine Verfahrensfrage verraten
VERFAHREN_TEXT = re.compile(
    r"\b(?:Beratung von|Reihenfolge|vorgezogen|Vorzug|vorziehen|Verschiebung|"
    r"sofortige\s+(?:zweite|2\.)\s+Lesung|Abbruch der Diskussion|"
    r"Unterbrechung|Sitzungsabbruch|Traktand|Wiederholung der Abstimmung|"
    r"Prüfungsantrag|redaktionelle|zur[üu]ckzuweisen|R[üu]ckweisung|"
    r"an die (?:vorberatende )?Kommission zur[üu]ck|geht .{0,40}zur[üu]ck an|"
    r"vertagt|Fristverk[üu]rzung|Fristverl[äa]ngerung|"
    r"Zuweisung .{0,160}? an (?:eine[rn]?|die) \d*er?\s?(?:SPK|Spezialkommission|Kommission)|"
    r"Aufteilung der Vorlage|"
    r"nach Abschluss \d\. Lesung|Vorbereitung \d\. Lesung)\b", re.I)


def ist_sachfrage(v):
    """Ob über eine Sache entschieden wurde und nicht über das Verfahren.

    Die Trennschärfe allein taugt nicht als Auswahlkriterium: Auch die Frage,
    ob Anhang 2 vor Anhang 1 beraten wird, spaltet den Rat zuverlässig, sagt
    aber nichts über politische Haltungen. Solche Abstimmungen gehören nicht
    in einen Fragebogen, der Positionen vergleichen will.
    """
    formen = set(v.get("tags_form") or [])
    if formen & FORM_VERFAHREN:
        return False
    text = " ".join([flach(v.get("titel")), flach(v.get("details"))])
    if VERFAHREN_TEXT.search(text):
        return False
    if re.search(r"[Uu]ng[üu]ltige Abstimmung", text):
        return False
    # Nach der Antwort auf eine Interpellation stimmt der Rat darüber ab, ob er
    # überhaupt darüber diskutieren will. Das ist eine Verfahrensfrage: sie sagt
    # nichts darüber, wie jemand zur Sache steht.
    if re.search(r"\bAntrag\s+Diskussion\b", text):
        return False
    if flach(v.get("typ")) == "Antrag" and re.match(r"^Interpellation\b", text):
        return False
    if flach(v.get("details")).lower() in ("diskussion", "diskussion.", ""):
        if re.match(r"^(?:Ordnungs)?[Aa]ntrag\b", flach(v.get("titel")) or ""):
            return False
    return True


# Ohne Geschäftsbezeichnung erhielte jeder Budgetantrag eine eigene Gruppe und
# alle kämen in der ersten Runde durch: der Kurzmodus wäre dann eine Reihe von
# Kontenkorrekturen. Budgetanträge derselben Vorlage werden darum zu einer
# Gruppe zusammengefasst, ebenso die mehrfachen Abstimmungen zum selben
# Vorstoss (Erheblicherklärung und anschliessende Abschreibung).
VORSTOSS = re.compile(r"\b((?:Volks)?(?:Motion|Postulat|Interpellation))\s*Nr\.\s*"
                      r"(\d{4}/\d+)", re.I)
BUDGETJAHR = re.compile(r"\bBudget\s*(20\d\d)")

# Einzelne Abstimmungen, die als Frage nicht taugen, mit Begründung.
# Beide Fälle stammen aus der Budgetsitzung vom 17.11.2025 (Abend): Das
# Protokoll hält fest, dem Gesamtbeitrag für das Energieförderprogramm sei mit
# 43:15 zugestimmt worden. Im Excel steht dieses Ergebnis jedoch bei der
# Äufnung des Energie- und Klimafonds, während beim Energieförderprogramm ein
# anderes Verhältnis eingetragen ist. Titel und Stimmen sind hier gegeneinander
# verschoben; welche Spalte zu welchem Beschluss gehört, lässt sich aus den
# Quellen nicht entscheiden. Eine Frage daraus zu bauen hiesse, Stimmen einem
# womöglich falschen Gegenstand zuzuordnen.
FRAGE_AUSSCHLUSS = {
    "22., 23. und 24. Sitzung 2025 · 17.11.2025 (Abend) #Nr10",
    "22., 23. und 24. Sitzung 2025 · 17.11.2025 (Abend) #Nr11",
}


def gruppen_key(v, si, i):
    if flach(v.get("geschaeft")):
        return flach(v["geschaeft"])
    text = " ".join([flach(v.get("titel")), flach(v.get("details"))])
    m = BUDGETJAHR.search(text)
    if m or "Oktoberbrief" in text:
        return f"Budget {m.group(1) if m else ''}".strip()
    m = VORSTOSS.search(text)
    if m:
        return f"{m.group(1)} {m.group(2)}"
    return f"{si}_{i}"


def paar(hand, kontext):
    """(dafür, dagegen) nur, wenn beide Seiten belegt sind, sonst (None, None).

    Ein einzelnes Zitat gäbe der Karte eine Schlagseite, die nicht in der
    Debatte lag, sondern daran, dass sich für die Gegenseite kein brauchbares
    Votum finden liess.
    """
    if hand:
        a, b = hand.get("dafuer"), hand.get("dagegen")
    else:
        a, b = kontext.get("pro"), kontext.get("contra")
    return (a, b) if (a and b) else (None, None)


def frage_text(v):
    """Sachliche, anonyme Kurzfassung: nie «Antrag <Name>»."""
    ge = flach(v.get("geschaeft"))
    b = betreff(ge)
    if b and len(b) > 12:
        return kuerze(b, 130)
    t, _ = ueberschrift(v)
    return kuerze(re.sub(r"^Antrag\s+[^:]+:\s*", "", t), 130)


# ─────────────────────────────────────────────────────────────────────────────
# Seite
# ─────────────────────────────────────────────────────────────────────────────

ICONS = {
    "neu": '<path d="M2.5 8.5l4 4 7-9" stroke="currentColor" stroke-width="1.7" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
    "vote": '<rect x="2.5" y="3" width="11" height="10" rx="1.6" stroke="currentColor" stroke-width="1.5" fill="none"/><path d="M5.4 8.3l1.8 1.8 3.4-3.9" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
    "people": '<circle cx="6.2" cy="6" r="2.4" stroke="currentColor" stroke-width="1.5" fill="none"/><path d="M2.2 14c0-2.2 1.8-3.7 4-3.7s4 1.5 4 3.7" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round"/><path d="M11.2 5.3a2.2 2.2 0 0 1 0 4.4M12.4 13.6c0-1.6-.6-2.7-1.4-3.3" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round"/>',
    "group": '<rect x="2" y="9" width="3.4" height="5" rx="1" stroke="currentColor" stroke-width="1.5" fill="none"/><rect x="6.3" y="5.4" width="3.4" height="8.6" rx="1" stroke="currentColor" stroke-width="1.5" fill="none"/><rect x="10.6" y="2.6" width="3.4" height="11.4" rx="1" stroke="currentColor" stroke-width="1.5" fill="none"/>',
    "tag": '<path d="M8.6 2H14v5.4l-6.3 6.3a1.4 1.4 0 0 1-2 0L2.3 10.3a1.4 1.4 0 0 1 0-2z" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linejoin="round"/><circle cx="11" cy="5" r="1" fill="currentColor"/>',
    "rank": '<path d="M2.6 13.4V9.2M8 13.4V3.2M13.4 13.4V6.6" stroke="currentColor" stroke-width="1.7" fill="none" stroke-linecap="round"/>',
    "match": '<path d="M8 13.6S2.2 10.2 2.2 6.3A3.1 3.1 0 0 1 8 4.6a3.1 3.1 0 0 1 5.8 1.7c0 3.9-5.8 7.3-5.8 7.3z" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linejoin="round"/>',
    "netz": '<circle cx="4" cy="4" r="2" stroke="currentColor" stroke-width="1.5" fill="none"/><circle cx="12.5" cy="6" r="2" stroke="currentColor" stroke-width="1.5" fill="none"/><circle cx="6.5" cy="12.5" r="2" stroke="currentColor" stroke-width="1.5" fill="none"/><path d="M5.7 5.2l5.2 .5M5.3 5.8l.6 4.8M11.4 7.6l-3.4 3.6" stroke="currentColor" stroke-width="1.3"/>',
}


def nav_html():
    teile = []
    for key, label, icon in NAV:
        teile.append(
            f'<button type="button" data-tab="{key}" title="{label}">'
            f'<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">{ICONS[icon]}</svg>'
            f'<span>{label}</span></button>')
    return "".join(teile)


def panels_html():
    """Leere Hüllen. Den Inhalt setzt dashboard.js beim Wechsel der Rubrik."""
    return "".join(f'<section class="panel" id="p-{key}"></section>' for key, _, _ in NAV)


def bauen():
    d = sitzungen_lesen()
    umkehr = umkehr_lesen()

    payload = {
        "sessions": sessions_payload(d, umkehr),
        "leg": d["legislaturen"],
        "aktLeg": d["aktuelle_legislatur"],
        "weg": ausgeschieden(d),
        "ohneProfil": ohne_profil(d),
        "themen": d["themen_gruppen"],
        "formen": d.get("tags_form_liste") or [],
        "hier": d.get("tags_hierarchie") or [],
        "personen": personen_payload(),
        "netz": netz_mit_register(),
        # Handelsregisterabgleich der Organisationen, Quelle Zefix über lindas.admin.ch
        "hreg": zusatz("interessen_pruefung.json",
                       {"eindeutig": [], "moeglich": [], "nicht_gefunden": []}),
        "match": matching_payload(d, umkehr),
    }
    daten = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    css = (ASSETS / "dashboard.css").read_text(encoding="utf-8")
    js = (ASSETS / "dashboard.js").read_text(encoding="utf-8")

    html = SEITE.replace("__CSS__", css) \
                .replace("__NAV__", nav_html()) \
                .replace("__PANELS__", panels_html()) \
                .replace("__DATEN__", daten) \
                .replace("__JS__", js)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    n_votes = sum(len(s["v"]) for s in payload["sessions"])
    n_fragen = len(payload["match"]["fragen"]) if payload["match"] else 0
    print(f"geschrieben: {OUT}")
    print(f"  {len(payload['sessions'])} Sitzungen, {n_votes} Abstimmungen, "
          f"{n_fragen} Matching-Fragen, {len(html)/1e6:.2f} MB")


SEITE = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kantonsrat Schaffhausen · Kantonsratsspiegel</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700&family=Public+Sans:wght@400;500;600;700&display=swap">
<style>
__CSS__
</style>
</head>
<body data-nav="closed">
<div class="scrim" id="scrim" hidden></div>
<div class="app">

  <aside class="side" id="side">
    <div class="brandrow">
      <div class="brand">Kantonsrat<br>Schaffhausen<span>Kantonsratsspiegel</span></div>
      <button class="navtoggle" id="navToggle" type="button"
              aria-label="Seitenleiste einklappen" aria-expanded="true">
        <svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true">
          <path d="M10 3L5 8l5 5" stroke="currentColor" stroke-width="1.8" fill="none"
                stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>
    <nav id="nav" aria-label="Rubriken">__NAV__</nav>
    <div class="sidefoot">
      <button class="themetoggle" id="themeToggle" type="button" aria-pressed="false">
        <svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true" id="themeIcon"></svg>
        <span id="themeLabel">Dunkelmodus</span>
      </button>
      <div class="stand" id="stand"></div>
    </div>
  </aside>

  <main class="main">
    <div class="topbar">
      <button class="burger" id="burger" type="button" aria-label="Menü öffnen" aria-expanded="false">
        <svg viewBox="0 0 16 16" width="17" height="17" aria-hidden="true">
          <path d="M2 4h12M2 8h12M2 12h12" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/>
        </svg>
      </button>
      <label class="search" for="suche">
        <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
          <circle cx="7" cy="7" r="5" stroke="currentColor" stroke-width="1.7" fill="none"/>
          <path d="M11 11l4 4" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/>
        </svg>
        <input id="suche" type="search" placeholder="Geschäft, Name oder Thema suchen …"
               autocomplete="off">
      </label>
      <select class="pick" id="scope" aria-label="Legislatur oder Sitzung"></select>
    </div>
    <div class="wrap" id="wrap">__PANELS__</div>
  </main>
</div>

<div class="bildmodal" id="bildModal" hidden>
  <div class="bildbox" role="dialog" aria-modal="true" aria-labelledby="bildTitel">
    <div class="bildkopf">
      <h2 id="bildTitel">Bild für Social Media</h2>
      <button type="button" class="bildzu" id="bildZu" aria-label="Schliessen">&times;</button>
    </div>
    <div class="bildbody">
      <div class="bildwahl">
        <label for="bildMotiv">Motiv</label>
        <select id="bildMotiv"></select>
        <div id="bildSubjektWrap" hidden>
          <label for="bildSubjekt" id="bildSubjektLabel">Ratsmitglied</label>
          <select id="bildSubjekt"></select>
        </div>
        <p class="bildnote">Hochformat 1080 × 1350, das Standardmass für Beiträge
        auf Instagram, LinkedIn und Facebook.</p>
        <button type="button" class="btn" id="bildLaden">Als PNG herunterladen</button>
      </div>
      <div class="bildvorschau"><canvas id="bildCanvas" width="1080" height="1350"></canvas></div>
    </div>
  </div>
</div>

<div class="beta" aria-hidden="true"><span>Betaversion</span></div>
<p class="beta-text">Diese Seite ist eine Betaversion: die Daten werden noch geprüft.</p>

<script id="daten" type="application/json">__DATEN__</script>
<script>
__JS__
</script>
</body>
</html>
"""


if __name__ == "__main__":
    bauen()

#!/usr/bin/env python3
"""
Notfall-Parser: Abstimmungsergebnisse aus dem PDF-Report
========================================================
sh.ch veröffentlicht die Abstimmungsergebnisse je Sitzungshälfte als xlsx UND
als PDF ("Definitiver Report"). Wenn der xlsx-Link ins Leere läuft (kommt vor:
Datei auf dem Server ersetzt, Link im CMS veraltet), liefert dieses Modul
dieselbe Datenstruktur wie scraper.parse_xlsx aus dem PDF.

Verwendung:
    from pdf_report import parse_pdf
    session = parse_pdf("pfad/report.pdf", "11. Sitzung 2026 · 24.08.2026 (Nachmittag)",
                        cid="23337193", roster=<members einer anderen Sitzungshälfte>)

Der optionale roster (Mitgliederliste einer bereits geparsten Sitzungshälfte
desselben Tages) macht die Trennung von Nach-/Vorname robust; ohne roster wird
heuristisch getrennt.
"""
import re
from pathlib import Path

import pdfplumber

STIMMEN = ("Ja", "Nein", "Enth", "V/A/N")
DETAIL_URL_TMPL = ("https://sh.ch/CMS/Webseite/Kanton-Schaffhausen/Beh-rde/"
                   "Parlament/Der-Kantonsrat-{cid}-DE.html")


def _zeilen(page, tol=4):
    """Wörter einer Seite nach Zeilen (y-Position) gruppieren.

    Geclustert statt gerundet: in den Reports weichen die y-Werte innerhalb
    einer Zeile um 1-2 Punkte ab, ein festes Raster würde solche Zeilen teilen.
    """
    worte = sorted(page.extract_words(), key=lambda w: w["top"])
    zeilen, aktuell, ref = [], [], None
    for w in worte:
        if ref is None or abs(w["top"] - ref) <= tol:
            aktuell.append(w)
            ref = w["top"] if ref is None else ref
        else:
            zeilen.append(sorted(aktuell, key=lambda x: x["x0"]))
            aktuell, ref = [w], w["top"]
    if aktuell:
        zeilen.append(sorted(aktuell, key=lambda x: x["x0"]))
    return zeilen


# ---------------------------------------------------------------------------
# Mitgliedertabelle (Seiten mit Kopfzeile "Nachnamen ... Abst. 1 ...")
# ---------------------------------------------------------------------------
def _parse_members(pdf, roster=None):
    n_votes = 0
    members = []
    lookup = {}
    if roster:
        for m in roster:
            lookup[f"{m['nachname']} {m['vorname']}"] = m

    for page in pdf.pages:
        zeilen = _zeilen(page)
        kopf = next((z for z in zeilen
                     if any(w["text"] == "Nachnamen" for w in z)), None)
        if kopf is None:
            continue
        # Anzahl Stimmspalten = Anzahl "Abst."-Marker in der Kopfzeile
        n_votes = max(n_votes, sum(1 for w in kopf if w["text"] == "Abst."))
        kopf_y = kopf[0]["top"]

        for z in zeilen:
            if z[0]["top"] <= kopf_y:
                continue
            texte = [w["text"] for w in z]
            # Stimmzellen sind die Tokens rechts der Parteispalte
            stimmen = [t for t in texte if t in STIMMEN]
            if not n_votes or len(stimmen) != n_votes:
                continue                      # Summenzeilen, Kopf-/Fusszeilen
            # Prefix = alles vor der ersten Stimmzelle
            i = next(i for i, t in enumerate(texte) if t in STIMMEN)
            prefix = " ".join(texte[:i])
            if not prefix or prefix.startswith(("Ja", "Nein", "Total", "Vakanz")):
                continue

            nachname = vorname = fraktion = partei = ""
            if lookup:
                treffer = next((k for k in lookup if prefix.startswith(k + " ")), None)
                if treffer:
                    # Fraktion und Partei aus dem roster übernehmen: beide
                    # können mehrteilig sein ("FDP-Die Mitte", "Junge Grüne"),
                    # eine Trennung nach Leerzeichen wäre unzuverlässig.
                    ref = lookup[treffer]
                    nachname, vorname = ref["nachname"], ref["vorname"]
                    fraktion, partei = ref["fraktion"], ref["partei"]
            if not nachname:                  # Fallback ohne roster
                teile = prefix.split()
                nachname, vorname = teile[0], (teile[1] if len(teile) > 1 else "")
                fraktion = " ".join(teile[2:-1])
                partei = teile[-1] if len(teile) > 3 else ""

            members.append({"nachname": nachname, "vorname": vorname,
                            "fraktion": fraktion, "partei": partei,
                            "votes": stimmen})
    return n_votes, members


# ---------------------------------------------------------------------------
# Metablock (Seiten mit Kopfzeile "Nr. | Traktandum | Betreff | Abstimmung")
# ---------------------------------------------------------------------------
def _parse_meta(pdf, n_votes):
    """Liest Geschäfte, Abstimmungstitel, Betreff (Typ) und 'Ja bedeutet'-Hinweise."""
    bloecke = []          # (nr, titel, typ, details[], inverted)
    geschaeft_map = {}
    aktuell = None
    geschaeft_buf = None
    x_traktandum = x_betreff = x_abst = None

    for page in pdf.pages:
        zeilen = _zeilen(page)
        kopf = next((z for z in zeilen
                     if any(w["text"] == "Traktandum" for w in z)
                     and any(w["text"] == "Betreff" for w in z)), None)
        if kopf is None:
            continue
        for w in kopf:
            if w["text"] == "Traktandum":
                x_traktandum = w["x0"]
            elif w["text"] == "Betreff":
                x_betreff = w["x0"]
            elif w["text"] == "Abstimmung":
                x_abst = w["x0"]
        kopf_y = kopf[0]["top"]

        for z in zeilen:
            if z[0]["top"] <= kopf_y:
                continue
            links = " ".join(w["text"] for w in z if w["x0"] < x_traktandum - 5)
            mitte = " ".join(w["text"] for w in z
                             if x_traktandum - 5 <= w["x0"] < x_betreff - 5)
            betreff = " ".join(w["text"] for w in z
                               if x_betreff - 5 <= w["x0"] < x_abst - 5)
            rechts = " ".join(w["text"] for w in z if w["x0"] >= x_abst - 5)

            # 1) Geschäfts-Vorspann (kann über mehrere Zeilen laufen)
            if mitte.startswith("Die Abstimmung"):
                geschaeft_buf = {"kopf": mitte, "text": [mitte]}
                continue
            if geschaeft_buf is not None:
                m_neu = re.match(r"Abstimmung\s+(\d+)", links)
                if not m_neu and mitte and not mitte.startswith("Die Abstimmung"):
                    geschaeft_buf["text"].append(mitte)
                    continue
                _flush_geschaeft(geschaeft_buf, geschaeft_map)
                geschaeft_buf = None

            # 2) neue Abstimmung
            m = re.match(r"Abstimmung\s+(\d+)$", links.strip())
            if m:
                aktuell = {"nr": int(m.group(1)), "titel": mitte, "typ": betreff,
                           "details": [], "inverted": None}
                bloecke.append(aktuell)
                continue

            if aktuell is None:
                continue
            # 3) Fortsetzungszeilen des laufenden Blocks
            if betreff and not aktuell["typ"]:
                aktuell["typ"] = betreff
            if rechts.startswith("Ja bedeutet"):
                aktuell["inverted"] = rechts.strip()
            if mitte and not mitte.startswith(("Ja bedeutet", "Nein bedeutet",
                                               "fakultatives", "obligatorisches")):
                aktuell["details"].append(mitte)

    if geschaeft_buf is not None:
        _flush_geschaeft(geschaeft_buf, geschaeft_map)

    votes = []
    for b in bloecke:
        votes.append({"nr": b["nr"], "titel": b["titel"].strip(),
                      "typ": b["typ"].strip(), "details": " ".join(b["details"]),
                      "inverted_note": b["inverted"],
                      "geschaeft": geschaeft_map.get(b["nr"], "")})
    votes.sort(key=lambda v: v["nr"])
    # Doppelt erfasste Nummern (Blockwiederholung über Seitenumbruch) entfernen
    gesehen, eindeutig = set(), []
    for v in votes:
        if v["nr"] in gesehen:
            continue
        gesehen.add(v["nr"])
        eindeutig.append(v)
    return eindeutig[:n_votes]


def _flush_geschaeft(buf, geschaeft_map):
    """Ordnet den gesammelten Geschäftstext den betroffenen Abstimmungsnummern zu.
    Unterstützt 'Nr. 1-2', 'Nr. 3' und 'Nr. 5-7 und 11-12'."""
    g = " ".join(buf["text"])
    g = re.sub(r"^Die Abstimmung(?:en)?\s+Nr\.\s*[\d\s\-und]+"
               r"bezieh(?:t|en)\s+sich\s+auf\s+folgendes\s+Geschäft:\s*", "", g).strip()
    kopf = buf["kopf"]
    bereich = re.search(r"Nr\.\s*([\d\s\-und]+?)\s*bezieh", kopf)
    if not bereich:
        return
    for teil in re.split(r"\s*und\s*|,", bereich.group(1)):
        m = re.match(r"\s*(\d+)\s*(?:-\s*(\d+))?\s*$", teil)
        if not m:
            continue
        a = int(m.group(1))
        b = int(m.group(2)) if m.group(2) else a
        for n in range(a, b + 1):
            geschaeft_map[n] = g


# ---------------------------------------------------------------------------
def parse_pdf(path, sitzung_label, cid=None, roster=None):
    with pdfplumber.open(path) as pdf:
        n_votes, members = _parse_members(pdf, roster)
        votes = _parse_meta(pdf, n_votes)
    return {"sitzung": sitzung_label, "n_votes": n_votes, "cid": cid,
            "url": DETAIL_URL_TMPL.format(cid=cid) if cid else None,
            "members": members, "votes": votes, "quelle": Path(path).name}


if __name__ == "__main__":
    import json, sys
    s = parse_pdf(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "?")
    print(json.dumps({"n_votes": s["n_votes"], "members": len(s["members"]),
                      "votes": [(v["nr"], v["typ"], v["titel"][:50]) for v in s["votes"]]},
                     ensure_ascii=False, indent=1))

#!/usr/bin/env python3
"""Liest die Detailzahlen aus Budget und Staatsrechnung des Kantons Schaffhausen (PDF).

    python3 budget_pdf.py budget2027_vorlage.pdf budget2027.csv

Schreibt zwei Dateien:
    budget2027.csv      Erfolgsrechnung, eine Zeile je Konto: Departement, Dienststelle,
                        Spezialfinanzierung, Konto, drei Wertspalten, Abweichung, Kommentar
    budget2027_ir.csv   Investitionsrechnung, eine Zeile je Konto und Vorhaben
                        (Verpflichtungs- oder Budgetkredit), Ausgaben und Einnahmen je Spalte

Wie es funktioniert: pdfplumber liefert je Wort seine x-Position. Das PDF ist eine
Tabelle mit fester Geometrie. Links bei x = 30 steht der Code, umgebrochene
Beschreibungen beginnen bei x = 84, die Zahlenspalten stehen rechtsbuendig, der
Kommentar steht rechts davon. Die rechten Kanten der Zahlenspalten stehen in der
Kopfzeile jeder Seite («2027 2026 2025 Betrag %» bzw. «Ausgaben Einnahmen ...»).

Sechs Fallen:
1. Kontonummern wie 3153.00 sehen aus wie Betraege. Als Betrag zaehlt nur, was
   rechts von x = 200 steht.
2. Die Kopfzeile jeder Seite lautet «2027 2026 2025 Betrag %», und die zweite Zeile
   einer umgebrochenen Beschreibung beginnt mitunter mit einer Jahreszahl. Beides
   sieht aus wie eine Dienststellennummer; die x-Grenze bei 60 faengt es ab.
3. Kapitel 6 enthaelt Erfolgs- und Investitionsrechnung. Die Kopfzeile der Seite
   («Erfolgsrechnung» bzw. «Investitionsrechnung») entscheidet, welcher Teil gilt.
4. Spezialfinanzierungen und Fonds (Code 2398.7214 u. ae.) stehen als eigene
   Bloecke innerhalb einer Dienststelle. Ohne eigene Erkennung landen ihre Konten
   bei der Dienststelle davor; in Spalten, in denen der Fonds nicht auf null
   abschliesst, stimmt deren Summe dann nicht mehr.
5. Eine Seite, auf der eine Spalte leer ist, verschiebt jede aus den Zahlen
   geschaetzte Spaltenlage. Budget 2027, Seite 155: Die Dienststelle 2276 Hoehere
   Fachschulen ist aufgehoben, die Spalte 2027 leer; aus den Zahlen geclustert
   rutschten Budget 2026 und Rechnung 2025 eine Spalte nach links. Die Kanten kommen
   deshalb aus der Kopfzeile; nur wenn sie fehlt, aus den Zahlen der Seite.
6. Die Investitionsrechnung gliedert im Budget Konto > Vorhaben, in der
   Staatsrechnung Vorhaben > Konto. Welche Ebene oben steht, zeigt die erste Zeile
   nach der Dienststelle; die Summen pruefen es.

Selbstpruefung: Das PDF druckt je Dienststelle, je Spezialfinanzierung und je
Departement eine Summe, in der Investitionsrechnung zusaetzlich je Konto bzw. je
Vorhaben. Das Skript rechnet die gelesenen Zeilen zusammen und vergleicht. Jede
Abweichung wird gemeldet.

Ergebnisse (Erfolgsrechnung, alle Blocksummen in allen drei Spalten exakt):
Budget 2026 (2'951 Kontozeilen), Staatsrechnung 2025 (3'034 Kontozeilen), Budget 2027
Vorlage (2'933 Kontozeilen, 126 Dienststellen). Investitionsrechnung: siehe Ausgabe.

Die Spaltenbezeichnungen unterscheiden sich zwischen Budget (Budget, Budget,
Rechnung) und Staatsrechnung (Rechnung, Budget, Rechnung). Sie werden aus der
Kopfzeile gelesen.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import pdfplumber

ZAHL = re.compile(r"^-?[\d’']+\.\d{2}$")
KONTO = re.compile(r"^\d{4}\.\d{2}$")        # 3010.00
DIENST = re.compile(r"^\d{4}$")              # 2380
SPEZ = re.compile(r"^\d{4}\.\d{4}$")         # 2398.7214, Spezialfinanzierung oder Fonds
DEPT = re.compile(r"^\d{2}$")                # 22
PROJEKT = re.compile(r"^[A-Z]{2,4}\d{3,5}(-\d{1,2})?$")   # IPR0326, ITP5016, ITP5019-1
SEITENZAHL = re.compile(r"^\d{1,4}$")
CODE_X = 60      # links davon steht der Code, rechts davon Beschreibung oder Kopfzeile
WERT_X = 200     # rechts davon stehen die Zahlenspalten
SPALTEN = ["budget", "budget_vorjahr", "rechnung", "abweichung", "prozent"]
JAHR = re.compile(r"^(19|20)\d{2}$")


def zu_zahl(s: str) -> float:
    return float(s.replace("’", "").replace("'", ""))


def zeilen(seite):
    gruppen = defaultdict(list)
    for w in seite.extract_words(use_text_flow=False):
        gruppen[round(w["top"] / 2)].append(w)
    for k in sorted(gruppen):
        yield sorted(gruppen[k], key=lambda w: w["x0"])


def kanten(alle_zeilen) -> list[float]:
    """Spaltenlage aus den Zahlen der Seite; nur Rueckfall, siehe Falle 5."""
    xs = sorted(
        w["x1"] for zl in alle_zeilen for w in zl
        if ZAHL.match(w["text"]) and w["x0"] > WERT_X
    )
    if not xs:
        return []
    gruppen, akt = [], [xs[0]]
    for x in xs[1:]:
        if x - akt[-1] <= 4:
            akt.append(x)
        else:
            gruppen.append(sum(akt) / len(akt))
            akt = [x]
    gruppen.append(sum(akt) / len(akt))
    return gruppen


def kanten_kopf(alle_zeilen) -> list[float]:
    """Rechte Kanten der Zahlenspalten aus der Kopfzeile der Erfolgsrechnung:
    «2027 2026 2025 Betrag %». Die Zahlen darunter sind rechtsbuendig daran."""
    for zl in alle_zeilen[:12]:
        rechts = [w for w in zl if w["x0"] > WERT_X]
        jahre = [w for w in rechts if JAHR.match(w["text"].strip("*"))]
        if len(jahre) >= 3:
            k = [w["x1"] for w in jahre] + [w["x1"] for w in rechts if w["text"] in ("Betrag", "%")]
            return sorted(k)
    return []


def spalte(x1: float, kant: list[float], toleranz: float = 5) -> int | None:
    for i, k in enumerate(kant):
        if abs(x1 - k) <= toleranz:
            return i
    return None


def spaltennamen(alle_zeilen, kant: list[float]) -> list[str]:
    """Spaltennamen aus der Kopfzeile lesen.

    Das Budget stellt «Budget 2026 | Budget 2025 | Rechnung 2024» nebeneinander,
    die Staatsrechnung «Rechnung 2025 | Budget 2025 | Rechnung 2024». Die Namen
    gehoeren deshalb aus dem Dokument gelesen und nicht angenommen.
    """
    art = {}
    jahr = {}
    for zl in alle_zeilen[:12]:
        for w in zl:
            if w["x0"] <= WERT_X:
                continue
            s = spalte(w["x1"], kant, toleranz=14)
            if s is None or s > 2:
                continue
            wort = w["text"].strip("*")
            if JAHR.match(wort):
                jahr.setdefault(s, wort)
            elif wort in ("Budget", "Rechnung"):
                art.setdefault(s, wort.lower())
    namen = []
    for i in range(len(kant)):
        if i in jahr:
            namen.append(f"{art.get(i, 'wert')}_{jahr[i]}")
        else:
            namen.append(SPALTEN[i] if i < len(SPALTEN) else f"spalte_{i}")
    return namen


def ist_seitenzahl(zl) -> bool:
    return all(SEITENZAHL.match(w["text"]) for w in zl) and zl[0]["x0"] > 700


# ─────────────────────────────────────────────────────────── Erfolgsrechnung

def lesen(pfad: str) -> tuple[list[dict], list[str]]:
    zeilenliste = []
    namen: list[str] = []
    with pdfplumber.open(pfad) as pdf:
        for nr, seite in enumerate(pdf.pages, start=1):
            alle = list(zeilen(seite))
            if not alle or "Erfolgsrechnung" not in " ".join(w["text"] for w in alle[0]):
                continue
            kant = kanten_kopf(alle) or kanten(alle)
            if len(kant) < 3:
                continue
            if not namen:
                namen = spaltennamen(alle, kant)
            letzte = None
            for zl in alle:
                erst = zl[0]["text"]
                if ist_seitenzahl(zl):
                    letzte = None
                    continue
                if zl[0]["x0"] > CODE_X:
                    # Umgebrochene Bezeichnung (links) oder Fortsetzung des Kommentars
                    # (rechts der Zahlen): gehoert zur Zeile davor, traegt keine Betraege.
                    hat_zahl = any(ZAHL.match(w["text"]) and WERT_X < w["x0"] < kant[-1] for w in zl)
                    if letzte is not None and not hat_zahl:
                        bez = [w["text"] for w in zl if w["x0"] < kant[-1] - 60]
                        kom = [w["text"] for w in zl if w["x0"] > kant[-1]]
                        if bez:
                            letzte["bezeichnung"] = (letzte["bezeichnung"] + " " + " ".join(bez)).strip()
                        if kom:
                            letzte["kommentar"] = (letzte["kommentar"] + " " + " ".join(kom)).strip()
                    else:
                        letzte = None
                    continue
                if not (KONTO.match(erst) or DIENST.match(erst)
                        or SPEZ.match(erst) or DEPT.match(erst)):
                    letzte = None
                    continue
                werte, text, kommentar = {}, [], []
                for w in zl[1:]:
                    if ZAHL.match(w["text"]) and w["x0"] > WERT_X and w["x0"] < kant[-1]:
                        s = spalte(w["x1"], kant)
                        if s is not None:
                            werte[s] = zu_zahl(w["text"])
                            continue
                    (kommentar if w["x0"] > kant[-1] else text).append(w["text"])
                letzte = {
                    "typ": ("departement" if DEPT.match(erst)
                            else "dienststelle" if DIENST.match(erst)
                            else "spezialfinanzierung" if SPEZ.match(erst)
                            else "konto"),
                    "code": erst,
                    "bezeichnung": " ".join(text),
                    "kommentar": " ".join(kommentar),
                    "werte": werte,
                    "seite": nr,
                }
                zeilenliste.append(letzte)
    return zeilenliste, namen


def pruefen(zeilenliste: list[dict], spalte_nr: int) -> tuple[int, list]:
    exakt, fehler = 0, []
    aktuell, summe = None, 0.0

    def abschluss():
        nonlocal exakt
        if aktuell is None:
            return
        soll = aktuell["werte"].get(spalte_nr, 0.0)
        if abs(summe - soll) < 0.5:
            exakt += 1
        else:
            fehler.append((aktuell["code"], aktuell["bezeichnung"], soll, summe, aktuell["seite"]))

    for z in zeilenliste:
        if z["typ"] in ("dienststelle", "spezialfinanzierung", "departement"):
            abschluss()
            aktuell = z if z["typ"] != "departement" else None
            summe = 0.0
        elif aktuell is not None and spalte_nr in z["werte"]:
            summe += z["werte"][spalte_nr]
    abschluss()
    return exakt, fehler


def pruefen_departemente(zeilenliste: list[dict], spalte_nr: int) -> tuple[int, list]:
    """Departementstotal gegen die Summe seiner Konten."""
    exakt, fehler = 0, []
    dep, summe = None, 0.0
    for z in zeilenliste + [{"typ": "departement", "code": "", "werte": {}, "bezeichnung": "", "seite": 0}]:
        if z["typ"] == "departement":
            if dep is not None:
                soll = dep["werte"].get(spalte_nr, 0.0)
                if abs(summe - soll) < 0.5:
                    exakt += 1
                else:
                    fehler.append((dep["code"], dep["bezeichnung"], soll, summe, dep["seite"]))
            dep, summe = z, 0.0
        elif z["typ"] == "konto":
            summe += z["werte"].get(spalte_nr, 0.0)
    return exakt, fehler


def schreiben(zeilenliste: list[dict], namen: list[str], ziel: str) -> int:
    dep = depname = dst = dstname = spz = spzname = ""
    n = 0
    with open(ziel, "w", newline="", encoding="utf-8") as f:
        s = csv.writer(f, delimiter=";")
        s.writerow(["departement", "departement_name", "dienststelle", "dienststelle_name",
                    "spezialfinanzierung", "spezialfinanzierung_name",
                    "konto", "bezeichnung", *namen, "kommentar", "seite"])
        for z in zeilenliste:
            if z["typ"] == "departement":
                dep, depname = z["code"], z["bezeichnung"]
                dst = dstname = spz = spzname = ""
                continue
            if z["typ"] == "dienststelle":
                dst, dstname = z["code"], z["bezeichnung"]
                spz = spzname = ""
                # Kommentar zur ganzen Dienststelle (z. B. Aufhebung) als eigene Zeile
                if z["kommentar"]:
                    s.writerow([dep, depname, dst, dstname, "", "", "", "", *[""] * len(namen),
                                z["kommentar"], z["seite"]])
                continue
            if z["typ"] == "spezialfinanzierung":
                spz, spzname = z["code"], z["bezeichnung"]
                # Fonds ohne eigene Dienststellen-Kopfzeile (z. B. 2198.7216): Die
                # Dienststellennummer steckt im Code, ein Name fehlt im PDF.
                if z["code"][:4] != dst:
                    dst, dstname = z["code"][:4], ""
                continue
            s.writerow([dep, depname, dst, dstname, spz, spzname, z["code"], z["bezeichnung"],
                        *[z["werte"].get(i, "") for i in range(len(namen))],
                        z["kommentar"], z["seite"]])
            n += 1
    return n


# ───────────────────────────────────────────────────── Investitionsrechnung

def kopf_ir(alle_zeilen) -> tuple[list[float], list[str]]:
    """Kanten und Namen der sechs Spalten: je Datensatz Ausgaben und Einnahmen.
    Kanten aus «Ausgaben Einnahmen ...», Namen aus «Budget 2027* Budget 2026* Rechnung 2025»."""
    kant, namen = [], []
    for i, zl in enumerate(alle_zeilen[:12]):
        woerter = [w for w in zl if w["x0"] > WERT_X]
        if sum(w["text"] in ("Ausgaben", "Einnahmen") for w in woerter) >= 4:
            # Die Wörter stehen nicht bündig mit den Zahlen (rund 14 Punkte links davon);
            # als Spaltenlage gilt deshalb ihre Mitte, jede Zahl gehört zur nächsten.
            kant = [(w["x0"] + w["x1"]) / 2 for w in woerter if w["text"] in ("Ausgaben", "Einnahmen")]
            titel = [w for z in alle_zeilen[max(0, i - 2):i] for w in z if w["x0"] > WERT_X]
            jahre = [w for w in titel if JAHR.match(w["text"].strip("*"))]
            arten = [w for w in titel if w["text"] in ("Budget", "Rechnung")]
            for j in sorted(jahre, key=lambda w: w["x0"]):
                vor = [a for a in arten if a["x1"] <= j["x0"] + 1]
                art = max(vor, key=lambda a: a["x1"])["text"].lower() if vor else "wert"
                jahr = j["text"].strip("*")
                namen += [f"{art}_{jahr}_ausgaben", f"{art}_{jahr}_einnahmen"]
            break
    return kant, namen


def lesen_ir(pfad: str) -> tuple[list[dict], list[str]]:
    zeilenliste = []
    namen: list[str] = []
    with pdfplumber.open(pfad) as pdf:
        for nr, seite in enumerate(pdf.pages, start=1):
            alle = list(zeilen(seite))
            if not alle or "Investitionsrechnung" not in " ".join(w["text"] for w in alle[0]):
                continue
            kant, nm = kopf_ir(alle)
            if len(kant) != 6:
                continue
            if not namen:
                namen = nm
            letzte = None
            for zl in alle:
                erst = zl[0]["text"]
                if ist_seitenzahl(zl):
                    letzte = None
                    continue
                zahlen = [w for w in zl if ZAHL.match(w["text"]) and w["x0"] > WERT_X]
                if zl[0]["x0"] > CODE_X:
                    if letzte is not None and not zahlen:
                        letzte["bezeichnung"] = (letzte["bezeichnung"] + " " + " ".join(w["text"] for w in zl)).strip()
                    else:
                        letzte = None   # Summenzeilen am Ende des Departements, «Nettoinvestition»
                    continue
                typ = ("departement" if DEPT.match(erst) else "dienststelle" if DIENST.match(erst)
                       else "spezialfinanzierung" if SPEZ.match(erst)
                       else "konto" if KONTO.match(erst) else "projekt" if PROJEKT.match(erst) else None)
                if typ is None:
                    letzte = None
                    continue
                werte = {}
                for w in zahlen:
                    mitte = (w["x0"] + w["x1"]) / 2
                    s = min(range(len(kant)), key=lambda i: abs(kant[i] - mitte))
                    if abs(kant[s] - mitte) <= 45:
                        werte[s] = zu_zahl(w["text"])
                text = [w["text"] for w in zl[1:] if not (ZAHL.match(w["text"]) and w["x0"] > WERT_X)]
                letzte = {"typ": typ, "code": erst, "bezeichnung": " ".join(text), "werte": werte, "seite": nr}
                zeilenliste.append(letzte)
    return zeilenliste, namen


def ir_blaetter(zeilenliste: list[dict]) -> tuple[list[dict], list, str]:
    """Blaetter (Konto und Vorhaben) mit Departement, Dienststelle und Fonds; Selbstpruefung.

    Bloecke sind Dienststellen und Fonds (2498.7004 Generationenfonds steht in der
    Investitionsrechnung als eigener Block, ohne Dienststelle 2498 davor). Innerhalb
    eines Blocks ist die erste Zeile die obere Ebene (Konto im Budget, Vorhaben in der
    Staatsrechnung); die Zeilen der anderen Art darunter sind ihre Teile. Ohne Teile
    ist die obere Zeile selbst ein Blatt.

    Geprueft wird je Spalte: obere Zeile = Summe ihrer Teile, Block = Summe seiner
    oberen Zeilen, Departement = Summe aller oberen Zeilen darin."""
    blaetter, fehler = [], []
    reihenfolge = {"konto": 0, "projekt": 0}
    dep = dst = spz = block = None
    oben_typ, oben, teile = None, None, []

    def summe(zs, i):
        return sum(z["werte"].get(i, 0.0) for z in zs)

    def vergleiche(art, z, ist_liste):
        for i in range(6):
            soll, ist = z["werte"].get(i, 0.0), summe(ist_liste, i)
            if abs(soll - ist) >= 0.5:
                fehler.append((art, z["code"], z["bezeichnung"], i, soll, ist, z["seite"]))

    def gruppe_abschliessen():
        nonlocal oben, teile
        if oben is None:
            return
        if teile:
            vergleiche("Teile", oben, teile)
            for t in teile:
                k, p = (oben, t) if oben["typ"] == "konto" else (t, oben)
                blaetter.append({"dep": dep, "dst": dst, "spz": spz, "konto": k, "projekt": p,
                                 "werte": t["werte"], "seite": t["seite"]})
        else:
            k, p = (oben, None) if oben["typ"] == "konto" else (None, oben)
            blaetter.append({"dep": dep, "dst": dst, "spz": spz, "konto": k, "projekt": p,
                             "werte": oben["werte"], "seite": oben["seite"]})
        block["_oben"].append(oben)
        dep["_oben"].append(oben)
        oben, teile = None, []

    for z in zeilenliste:
        if z["typ"] == "departement":
            gruppe_abschliessen()
            dep, dst, spz, block, oben_typ = z, None, None, None, None
            dep["_oben"] = []
        elif z["typ"] in ("dienststelle", "spezialfinanzierung"):
            gruppe_abschliessen()
            if z["typ"] == "dienststelle":
                dst, spz = z, None
            else:
                spz = z
                if dst is None or dst["code"] != z["code"][:4]:
                    dst = {"typ": "dienststelle", "code": z["code"][:4], "bezeichnung": "", "werte": {}, "seite": z["seite"]}
            block, oben_typ = z, None
            block["_oben"] = []
        else:
            if oben_typ is None:
                oben_typ = z["typ"]
                reihenfolge[z["typ"]] += 1
            if z["typ"] == oben_typ:
                gruppe_abschliessen()
                oben = z
            else:
                teile.append(z)
    gruppe_abschliessen()
    for z in zeilenliste:
        if z["typ"] in ("dienststelle", "spezialfinanzierung"):
            vergleiche("Block", z, z["_oben"])
        if z["typ"] == "departement":
            vergleiche("Departement", z, z["_oben"])
    oben = "Konto > Vorhaben" if reihenfolge["konto"] >= reihenfolge["projekt"] else "Vorhaben > Konto"
    return blaetter, fehler, oben


def schreiben_ir(blaetter: list[dict], namen: list[str], ziel: str) -> int:
    with open(ziel, "w", newline="", encoding="utf-8") as f:
        s = csv.writer(f, delimiter=";")
        s.writerow(["departement", "departement_name", "dienststelle", "dienststelle_name",
                    "spezialfinanzierung", "spezialfinanzierung_name",
                    "konto", "konto_name", "projekt", "projekt_name", *namen, "seite"])
        for b in blaetter:
            k, p, f = b["konto"], b["projekt"], b["spz"]
            s.writerow([b["dep"]["code"], b["dep"]["bezeichnung"], b["dst"]["code"], b["dst"]["bezeichnung"],
                        f["code"] if f else "", f["bezeichnung"] if f else "",
                        k["code"] if k else "", k["bezeichnung"] if k else "",
                        p["code"] if p else "", p["bezeichnung"] if p else "",
                        *[b["werte"].get(i, "") for i in range(len(namen))], b["seite"]])
    return len(blaetter)


def main() -> int:
    quelle = sys.argv[1] if len(sys.argv) > 1 else "budget2026.pdf"
    ziel = sys.argv[2] if len(sys.argv) > 2 else "budget2026.csv"
    protokoll = {"pdf": Path(quelle).name, "er": {}, "ir": {}}
    zeilenliste, namen = lesen(quelle)
    print(f"{quelle}: {sum(1 for z in zeilenliste if z['typ'] == 'konto')} Kontozeilen, "
          f"{sum(1 for z in zeilenliste if z['typ'] == 'dienststelle')} Dienststellen, "
          f"{sum(1 for z in zeilenliste if z['typ'] == 'spezialfinanzierung')} Spezialfinanzierungen, "
          f"{sum(1 for z in zeilenliste if z['typ'] == 'departement')} Departemente")
    print(f"  Spalten laut Kopfzeile: {', '.join(namen[:3])}")
    protokoll["er"] = {"konten": sum(1 for z in zeilenliste if z["typ"] == "konto"),
                       "dienststellen": sum(1 for z in zeilenliste if z["typ"] == "dienststelle"),
                       "fonds": sum(1 for z in zeilenliste if z["typ"] == "spezialfinanzierung"),
                       "spalten": namen[:3], "summen": 0, "abweichend": 0,
                       "kommentare": sum(1 for z in zeilenliste if z["kommentar"])}
    for i, name in enumerate(namen[:3]):
        exakt, fehler = pruefen(zeilenliste, i)
        dexakt, dfehler = pruefen_departemente(zeilenliste, i)
        protokoll["er"]["summen"] += exakt + dexakt
        protokoll["er"]["abweichend"] += len(fehler) + len(dfehler)
        print(f"  Selbstpruefung {name}: {exakt} Blocksummen exakt, {len(fehler)} abweichend; "
              f"Departemente {dexakt} exakt, {len(dfehler)} abweichend")
        for f in fehler + dfehler:
            print(f"    {f[0]} {f[1][:40]:<42} gedruckt {f[2]:>14,.2f}  gerechnet {f[3]:>14,.2f}  S.{f[4]}")
    n = schreiben(zeilenliste, namen, ziel)
    print(f"{ziel} geschrieben, {n} Zeilen, {sum(1 for z in zeilenliste if z['kommentar'])} mit Kommentar")

    ir, namen_ir = lesen_ir(quelle)
    if ir:
        blaetter, fehler, oben = ir_blaetter(ir)
        ziel_ir = str(Path(ziel).with_name(Path(ziel).stem + "_ir.csv"))
        print(f"Investitionsrechnung: {sum(1 for z in ir if z['typ'] == 'konto')} Kontozeilen, "
              f"{sum(1 for z in ir if z['typ'] == 'projekt')} Vorhaben, "
              f"{sum(1 for z in ir if z['typ'] == 'dienststelle')} Dienststellen, "
              f"{sum(1 for z in ir if z['typ'] == 'spezialfinanzierung')} Fonds; Gliederung {oben}")
        print(f"  Spalten laut Kopfzeile: {', '.join(namen_ir)}")
        gelesen = sum(1 for z in ir for v in z["werte"].values() if v)
        if not gelesen:
            fehler.append(("Werte", "-", "keine Betraege gelesen", 0, 0.0, 0.0, 0))
        print(f"  Selbstpruefung: {len(fehler)} Abweichungen (Teile, Bloecke, Departemente, je sechs Spalten); "
              f"{gelesen} Betraege gelesen")
        for f in fehler[:30]:
            print(f"    {f[0]} {f[1]} {f[2][:36]:<38} Spalte {f[3]} gedruckt {f[4]:>14,.2f} gerechnet {f[5]:>14,.2f} S.{f[6]}")
        m = schreiben_ir(blaetter, namen_ir, ziel_ir)
        print(f"{ziel_ir} geschrieben, {m} Zeilen")
        protokoll["ir"] = {"konten": sum(1 for z in ir if z["typ"] == "konto"),
                           "vorhaben": sum(1 for z in ir if z["typ"] == "projekt"),
                           "zeilen": m, "gliederung": oben, "spalten": namen_ir,
                           "summen": sum(1 for z in ir if z["typ"] in ("dienststelle", "spezialfinanzierung", "departement")) * 6
                           + sum(1 for z in ir if z["typ"] in ("konto", "projekt")) * 0,
                           "abweichend": len(fehler)}
    ziel_p = Path(ziel).with_name(Path(ziel).stem + "_pruefung.json")
    ziel_p.write_text(json.dumps(protokoll, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{ziel_p} geschrieben")
    return 0


if __name__ == "__main__":
    sys.exit(main())

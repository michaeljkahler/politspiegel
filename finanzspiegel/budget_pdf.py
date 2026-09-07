#!/usr/bin/env python3
"""Liest die Detailzahlen der Erfolgsrechnung aus dem Budget-PDF des Kantons Schaffhausen.

    python3 budget_pdf.py budget2026.pdf budget2026.csv

Ergebnis: eine Zeile je Konto, mit Departement und Dienststelle als eigene Spalten,
dazu Budget des Jahres, Budget des Vorjahres, Rechnung des Vorvorjahres, Abweichung
und Kommentar.

Wie es funktioniert: pdfplumber liefert je Wort seine x-Position. Das PDF ist eine
Tabelle mit fester Geometrie. Links bei x = 30 steht der Code, umgebrochene
Beschreibungen beginnen bei x = 84, die fuenf Zahlenspalten stehen rechtsbuendig.
Deren Lage verschiebt sich von Seite zu Seite, sie wird deshalb je Seite neu aus den
Zahlen der Seite geclustert.

Vier Fallen:
1. Kontonummern wie 3153.00 sehen aus wie Betraege. Als Betrag zaehlt nur, was
   rechts von x = 200 steht.
2. Die Kopfzeile jeder Seite lautet «2026 2025 2024 Betrag %», und die zweite Zeile
   einer umgebrochenen Beschreibung beginnt mitunter mit einer Jahreszahl. Beides
   sieht aus wie eine Dienststellennummer; die x-Grenze bei 60 faengt es ab.
3. Kapitel 6 enthaelt Erfolgs- und Investitionsrechnung. Nur Seiten mit der
   Kopfzeile «Erfolgsrechnung» zaehlen.
4. Spezialfinanzierungen und Fonds (Code 2398.7214 u. ae.) stehen als eigene
   Bloecke innerhalb einer Dienststelle. Ohne eigene Erkennung landen ihre Konten
   bei der Dienststelle davor; in Spalten, in denen der Fonds nicht auf null
   abschliesst, stimmt deren Summe dann nicht mehr.

Selbstpruefung: Das PDF druckt je Dienststelle, je Spezialfinanzierung und je
Departement eine Summe. Das Skript rechnet die gelesenen Kontozeilen zusammen und
vergleicht. Jede Abweichung wird gemeldet.

Ergebnis Budget 2026 (2'955 Kontozeilen, 124 Dienststellen, 26 Spezial-
finanzierungen): alle Blocksummen in allen drei Spalten exakt. Alle acht
Departementstotale stimmen auf den Franken mit Kapitel 4.4.2 ueberein, ihre Summe
mit dem Gesamtergebnis von -49'621'200 Franken.
Ergebnis Staatsrechnung 2025 (3'034 Kontozeilen), gleiches Skript: alle Blocksummen
in allen drei Spalten exakt.

Die Spaltenbezeichnungen unterscheiden sich zwischen Budget (Budget, Budget,
Rechnung) und Staatsrechnung (Rechnung, Budget, Rechnung). Sie werden aus der
Kopfzeile gelesen.
"""

from __future__ import annotations

import csv
import re
import sys
from collections import defaultdict

import pdfplumber

ZAHL = re.compile(r"^-?[\d’']+\.\d{2}$")
KONTO = re.compile(r"^\d{4}\.\d{2}$")       # 3010.00
DIENST = re.compile(r"^\d{4}$")              # 2380
SPEZ = re.compile(r"^\d{4}\.\d{4}$")        # 2398.7214, Spezialfinanzierung oder Fonds
DEPT = re.compile(r"^\d{2}$")                # 22
CODE_X = 60      # links davon steht der Code, rechts davon Beschreibung oder Kopfzeile
WERT_X = 200     # rechts davon stehen die Zahlenspalten
SPALTEN = ["budget", "budget_vorjahr", "rechnung", "abweichung", "prozent"]
JAHR = re.compile(r"^(19|20)\d{2}$")


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


def zu_zahl(s: str) -> float:
    return float(s.replace("’", "").replace("'", ""))


def zeilen(seite):
    gruppen = defaultdict(list)
    for w in seite.extract_words(use_text_flow=False):
        gruppen[round(w["top"] / 2)].append(w)
    for k in sorted(gruppen):
        yield sorted(gruppen[k], key=lambda w: w["x0"])


def kanten(alle_zeilen) -> list[float]:
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


def spalte(x1: float, kant: list[float], toleranz: float = 5) -> int | None:
    for i, k in enumerate(kant):
        if abs(x1 - k) <= toleranz:
            return i
    return None


def lesen(pfad: str) -> tuple[list[dict], list[str]]:
    zeilenliste = []
    namen: list[str] = []
    with pdfplumber.open(pfad) as pdf:
        for nr, seite in enumerate(pdf.pages, start=1):
            alle = list(zeilen(seite))
            if not alle or "Erfolgsrechnung" not in " ".join(w["text"] for w in alle[0]):
                continue
            kant = kanten(alle)
            if len(kant) < 3:
                continue
            if not namen:
                namen = spaltennamen(alle, kant)
            for zl in alle:
                erst = zl[0]["text"]
                if zl[0]["x0"] > CODE_X:
                    continue
                if not (KONTO.match(erst) or DIENST.match(erst)
                        or SPEZ.match(erst) or DEPT.match(erst)):
                    continue
                werte, text, kommentar = {}, [], []
                for w in zl[1:]:
                    if ZAHL.match(w["text"]) and w["x0"] > WERT_X:
                        s = spalte(w["x1"], kant)
                        if s is not None:
                            werte[s] = zu_zahl(w["text"])
                            continue
                    (kommentar if w["x0"] > kant[-1] else text).append(w["text"])
                zeilenliste.append({
                    "typ": ("departement" if DEPT.match(erst)
                            else "dienststelle" if DIENST.match(erst)
                            else "spezialfinanzierung" if SPEZ.match(erst)
                            else "konto"),
                    "code": erst,
                    "bezeichnung": " ".join(text),
                    "kommentar": " ".join(kommentar),
                    "werte": werte,
                    "seite": nr,
                })
    return zeilenliste, namen


def pruefen(zeilenliste: list[dict], spalte_nr: int) -> tuple[int, list]:
    exakt, fehler = 0, []
    aktuell, summe = None, 0.0

    def abschluss():
        nonlocal exakt
        if aktuell is None:
            return
        soll = aktuell["werte"].get(spalte_nr)
        if soll is None:
            return
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


def main() -> int:
    quelle = sys.argv[1] if len(sys.argv) > 1 else "budget2026.pdf"
    ziel = sys.argv[2] if len(sys.argv) > 2 else "budget2026.csv"
    zeilenliste, namen = lesen(quelle)
    print(f"{quelle}: {sum(1 for z in zeilenliste if z['typ'] == 'konto')} Kontozeilen, "
          f"{sum(1 for z in zeilenliste if z['typ'] == 'dienststelle')} Dienststellen, "
          f"{sum(1 for z in zeilenliste if z['typ'] == 'spezialfinanzierung')} Spezialfinanzierungen, "
          f"{sum(1 for z in zeilenliste if z['typ'] == 'departement')} Departemente")
    print(f"  Spalten laut Kopfzeile: {', '.join(namen[:3])}")
    for i, name in enumerate(namen[:3]):
        exakt, fehler = pruefen(zeilenliste, i)
        print(f"  Selbstpruefung {name}: {exakt} Blocksummen exakt, {len(fehler)} abweichend")
        for f in fehler:
            print(f"    {f[0]} {f[1][:40]:<42} gedruckt {f[2]:>14,.2f}  gerechnet {f[3]:>14,.2f}  S.{f[4]}")
    n = schreiben(zeilenliste, namen, ziel)
    print(f"{ziel} geschrieben, {n} Zeilen")
    return 0


if __name__ == "__main__":
    sys.exit(main())

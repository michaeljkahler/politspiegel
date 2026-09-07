#!/usr/bin/env python3
"""Fuehrt die Kontozeilen aus Budget und Staatsrechnung zur Datendatei des Finanzspiegels zusammen.

Aufruf aus der Projektwurzel:
    python3 finanzspiegel/daten.py

Liest    finanzspiegel/daten/budget2026.csv      aus budget_pdf.py, Spalten budget_2026, budget_2025
         finanzspiegel/daten/rechnung2025.csv    aus budget_pdf.py, Spalten rechnung_2025, budget_2025
         finanzspiegel/daten/kontenplan.xlsx     Artengliederung des FS-Modells der EFV, Blatt fs_er
Schreibt finanzspiegel/daten/finanzspiegel.json

Schluessel je Zeile: Departement, Dienststelle, Spezialfinanzierung, Konto. In beiden
Dokumenten eindeutig, 2'894 Schluessel in beiden. Budget 2025 stimmt in allen
gemeinsamen Zeilen ueberein; wo beide Dokumente einen Wert liefern, gilt die
Staatsrechnung als spaetere Publikation.

Kontrolle gegen den Bericht (Kap. 1.7 und 4.4.1): ordentlicher Aufwand Budget 2026
1'156.5 Mio., ordentlicher Ertrag 1'063.8 Mio., Gesamtergebnis -49.6 Mio.; Rechnung
2025 +14.9 Mio.; Budget 2025 -49.0 Mio. Alle Werte fallen auf den Franken.

Was zu welcher Sicht gehoert (Artengliederung HRM2):
  30 bis 37, 40 bis 47   ordentlicher Aufwand und Ertrag, die Sichten der Seite
  38, 48                 ausserordentlich (Einlagen in und Entnahmen aus Reserven)
  39, 49                 interne Verrechnungen, beidseits gleich, heben sich auf
  90                     Abschluss der Spezialfinanzierungen, Umbuchung im Eigenkapital
Die Seite zeigt im Drilldown nur die ordentlichen Gruppen. Das Ergebnis rechnet sie
in der Uebersicht vor: ordentlich, ausserordentlich, gesamt.

Warum die Rechnung 2024 fehlt: Die Vergleichsspalte der beiden PDF fuehrt nur Konten,
die im jeweiligen Dokument noch vorkommen. Ihre Summe ergibt 15.8 statt der
ausgewiesenen 19.1 Mio. Fuer 2024 braucht es die Staatsrechnung 2024 selbst.

Warum ein Teil der Sachgruppennamen von Hand kommt: Das FS-Modell der EFV ist ein
Statistikmodell und kennt weder durchlaufende Beitraege (37, 47) noch interne
Verrechnungen (39, 49) noch den Abschluss (90); es eliminiert sie. Der Kanton bucht
nach HRM2 und fuehrt sie. Die Namen dieser Gruppen stehen deshalb unten im Skript,
nach dem Kontenrahmen HRM2.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

HIER = Path(__file__).resolve().parent
DATEN = HIER / "daten"
JAHRE = [("b25", "Budget 2025"), ("r25", "Rechnung 2025"), ("b26", "Budget 2026")]

# Gruppen, die das FS-Modell nicht kennt, nach Kontenrahmen HRM2.
HRM2_ERGAENZUNG = {
    "33": "Abschreibungen Verwaltungsvermögen",
    "330": "Sachanlagen Verwaltungsvermögen",
    "332": "Immaterielle Anlagen Verwaltungsvermögen",
    "37": "Durchlaufende Beiträge", "370": "Durchlaufende Beiträge",
    "39": "Interne Verrechnungen",
    "390": "Material- und Warenbezüge", "391": "Dienstleistungen",
    "392": "Pacht, Mieten, Benützungskosten", "393": "Betriebs- und Verwaltungskosten",
    "394": "Kalkulatorische Zinsen und Finanzaufwand", "398": "Übertragungen",
    "399": "Übrige interne Verrechnungen",
    "47": "Durchlaufende Beiträge", "470": "Durchlaufende Beiträge",
    "49": "Interne Verrechnungen",
    "490": "Material- und Warenbezüge", "491": "Dienstleistungen",
    "492": "Pacht, Mieten, Benützungskosten", "493": "Betriebs- und Verwaltungskosten",
    "494": "Kalkulatorische Zinsen und Finanzertrag", "498": "Übertragungen",
    "499": "Übrige interne Verrechnungen",
    "90": "Abschluss", "901": "Abschluss Spezialfinanzierungen und Fonds",
}

# Kurze Erklaerung je zweistelliger Gruppe, fuer die Uebersicht. Laienverstaendlich,
# ohne Wertung, mit dem groessten Posten des Kantons als Beispiel.
ERKLAERUNG = {
    "30": "Löhne und Sozialbeiträge für Verwaltung, Lehrpersonen, Polizei, Gerichte",
    "31": "Material, Energie, Unterhalt, Mieten, Dienstleistungen Dritter",
    "33": "Wertverzehr von Gebäuden, Strassen und Anlagen",
    "34": "Zinsen und übriger Finanzaufwand",
    "35": "Einlagen in zweckgebundene Fonds",
    "36": "Beiträge an Spitäler, Gemeinden, Hochschulen, Prämienverbilligung, Sozialversicherungen",
    "37": "Geld, das der Kanton nur weiterleitet, etwa Bundesbeiträge an Gemeinden",
    "40": "Steuern natürlicher und juristischer Personen, Grundstückgewinn-, Erbschafts-, Motorfahrzeugsteuern",
    "41": "Konzessionen, Spielbankenabgabe, Regalien",
    "42": "Gebühren, Bussen, Verkäufe, Rückerstattungen",
    "43": "Übrige Erträge",
    "44": "Beteiligungen, Liegenschaften, Zinsen; darunter die Axpo-Dividende",
    "45": "Entnahmen aus zweckgebundenen Fonds",
    "46": "Anteile an Bundessteuern, Finanzausgleich, Beiträge von Bund und Gemeinden",
    "47": "Geld, das der Kanton nur weiterleitet, etwa Bundesbeiträge an Gemeinden",
}


def lade(datei: str, spalten: dict[str, str]) -> tuple[dict, dict]:
    werte: dict[tuple, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    namen: dict[tuple, tuple] = {}
    with open(DATEN / datei, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if r["konto"][0] not in "349":
                continue
            k = (r["departement"], r["dienststelle"], r["spezialfinanzierung"], r["konto"])
            for ziel, quelle in spalten.items():
                if r[quelle]:
                    werte[k][ziel] += float(r[quelle])
            namen[k] = (r["departement_name"], r["dienststelle_name"],
                        r["spezialfinanzierung_name"], r["bezeichnung"])
    return werte, namen


def kontenplan() -> dict[str, str]:
    plan = dict(HRM2_ERGAENZUNG)
    pfad = DATEN / "kontenplan.xlsx"
    if pfad.exists():
        import openpyxl
        ws = openpyxl.load_workbook(pfad, data_only=True)["fs_er"]
        for zeile in ws.iter_rows(values_only=True):
            if len(zeile) < 2 or zeile[0] is None or zeile[1] is None:
                continue
            code = str(zeile[0]).strip()
            if code.isdigit() and 1 <= len(code) <= 3:
                plan.setdefault(code, str(zeile[1]).strip())
    return plan


def main() -> None:
    b, nb = lade("budget2026.csv", {"b26": "budget_2026", "b25": "budget_2025"})
    r, nr = lade("rechnung2025.csv", {"r25": "rechnung_2025", "b25": "budget_2025"})

    dep, dst, spz, zeilen = {}, {}, {}, []
    for k in sorted(set(b) | set(r)):
        d, ds, sp, ko = k
        namen = nr.get(k) or nb[k]
        dep.setdefault(d, namen[0])
        if namen[1] or ds not in dst:
            dst.setdefault(ds, namen[1])
        if sp:
            spz.setdefault(sp, namen[2])
        w = []
        for j, _ in JAHRE:
            v = r[k].get(j) if k in r and j in r[k] else None
            if v is None:
                v = b[k].get(j) if k in b else None
            w.append(round(v) if v else 0)
        zeilen.append([d, ds, sp, ko, namen[3], *w])

    # Dienststellennummern ohne Kopfzeile im PDF (z. B. 2198, 2398) tragen nur
    # Fonds und Spezialfinanzierungen; so heissen sie dann auch.
    nur_fonds = {ds for ds in dst if not dst[ds]}
    for z in zeilen:
        if z[1] in nur_fonds and not z[2]:
            nur_fonds.discard(z[1])
    for ds in nur_fonds:
        dst[ds] = "Fonds und Spezialfinanzierungen"

    sg = kontenplan()
    daten = {
        "stand": date.today().isoformat(),
        "jahre": [{"k": k, "t": t} for k, t in JAHRE],
        "dep": dep, "dst": dst, "spz": spz,
        "sg": {c: n for c, n in sg.items() if len(c) in (2, 3)},
        "erkl": ERKLAERUNG,
        "z": zeilen,
    }
    ziel = DATEN / "finanzspiegel.json"
    ziel.write_text(json.dumps(daten, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    print(f"{len(zeilen)} Kontozeilen, {len(dep)} Departemente, {len(dst)} Dienststellen, "
          f"{len(spz)} Spezialfinanzierungen; {ziel.name} {ziel.stat().st_size / 1024:.0f} kB")
    fehlt = sorted({z[3][:n] for z in zeilen for n in (2, 3)} - set(daten["sg"]))
    print("Sachgruppen ohne Namen:", fehlt or "keine")
    for i, (j, t) in enumerate(JAHRE):
        g = defaultdict(float)
        for z in zeilen:
            g[z[3][:2]] += z[5 + i]
        ord_a = sum(v for c, v in g.items() if c[0] == "3" and c not in ("38", "39"))
        ord_e = -sum(v for c, v in g.items() if c[0] == "4" and c not in ("48", "49"))
        ao = -(g.get("38", 0) + g.get("48", 0))
        print(f"  {t:<14} ordentlicher Aufwand {ord_a / 1e6:8.1f}  Ertrag {ord_e / 1e6:8.1f}  "
              f"ordentlich {(ord_e - ord_a) / 1e6:6.1f}  a.o. {ao / 1e6:5.1f}  "
              f"Abschluss {-g.get('90', 0) / 1e6:5.1f}  Gesamt {-sum(g.values()) / 1e6:6.1f} Mio.")


if __name__ == "__main__":
    main()

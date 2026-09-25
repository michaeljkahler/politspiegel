#!/usr/bin/env python3
"""Führt Budget, Staatsrechnung und Finanzplan zur Datendatei des Finanzspiegels zusammen.

Aufruf aus der Projektwurzel:
    python3 finanzspiegel/daten.py

Liest    finanzspiegel/daten/budget2027.csv (+ _ir)   budget_pdf.py, Budget 2027, Vorlage des Regierungsrates
         finanzspiegel/daten/budget2026.csv (+ _ir)   budget_pdf.py, Budget 2026, vom Kantonsrat beschlossen
         finanzspiegel/daten/rechnung2025.csv (+ _ir) budget_pdf.py, Staatsrechnung 2025 und Budget 2025
         finanzspiegel/daten/finanzplan2027.json      finanzplan_pdf.py, Übersichten und Finanzplan 2028–2030
         finanzspiegel/daten/kontenplan.xlsx          Artengliederung des FS-Modells der EFV, Blatt fs_er
         finanzspiegel/daten/quellen.json             Titel, Fassung und Adresse der PDF
Schreibt finanzspiegel/daten/finanzspiegel.json

Datensätze
    Je Konto: b25 Budget 2025, r25 Rechnung 2025, b26 Budget 2026, b27 Budget 2027.
    Zusammengefasst: p28, p29, p30 Finanzplan; nur zweistellige Sachgruppen (Ziffer 2.1),
    Nettoinvestitionen (2.2), Bilanz (2.3) und Aufgabenfelder (Kapitel 7).
    Wo zwei Dokumente denselben Wert liefern, gilt das spätere: Budget 2025 aus der
    Staatsrechnung 2025, Rechnung 2025 aus der Staatsrechnung, Budget 2026 aus der vom
    Kantonsrat beschlossenen Fassung. Die Vergleichsspalten des Budgets 2027 dienen nur
    dem Abgleich (analyse.py).

Massgebend ist beim Budget die vom Kantonsrat beschlossene Fassung. Für 2027 liegt bis
zur Budgetdebatte nur die Vorlage des Regierungsrates vor; der Datensatz trägt das im
Titel und in «fassung». Nach dem Beschluss: PDF ersetzen, budget_pdf.py, daten.py.

Kontrollen (Ausgabe dieses Skripts): Summen je zweistellige Sachgruppe gegen Ziffer 2.1,
Nettoergebnis je Departement gegen Ziffer 4.4.2, Nettoinvestitionen gegen Ziffer 2.2,
jeweils Rechnung 2025, Budget 2026 und Budget 2027.

Was zu welcher Sicht gehört (Artengliederung HRM2):
  30 bis 37, 40 bis 47   ordentlicher Aufwand und Ertrag
  38, 48                 ausserordentlich (Einlagen in und Entnahmen aus Reserven)
  39, 49                 interne Verrechnungen, beidseits gleich, heben sich auf
  90                     Abschluss der Spezialfinanzierungen und Fonds im Eigenkapital

Warum ein Teil der Sachgruppennamen von Hand kommt: Das FS-Modell der EFV ist ein
Statistikmodell und kennt weder durchlaufende Beiträge (37, 47) noch interne
Verrechnungen (39, 49) noch den Abschluss (90); es eliminiert sie. Die Investitions-
rechnung gliedert es anders als HRM2 (56 und 57). Die Namen stehen deshalb unten,
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

# Datensätze je Konto, in dieser Reihenfolge in den Wertspalten
JAHRE = [
    {"k": "b25", "t": "Budget 2025", "a": "b", "j": 2025, "q": "rechnung2025",
     "fassung": "beschlossen vom Kantonsrat; Werte aus der Staatsrechnung 2025"},
    {"k": "r25", "t": "Rechnung 2025", "a": "r", "j": 2025, "q": "rechnung2025", "fassung": "Staatsrechnung 2025"},
    {"k": "b26", "t": "Budget 2026", "a": "b", "j": 2026, "q": "budget2026",
     "fassung": "beschlossen vom Kantonsrat am 17. November 2025"},
    {"k": "b27", "t": "Budget 2027", "a": "b", "j": 2027, "q": "budget2027",
     "fassung": "Vorlage des Regierungsrates vom 15. September 2026", "vorlage": 1},
]
PLAN = [{"k": f"p{j % 100}", "t": f"Finanzplan {j}", "a": "p", "j": j, "q": "budget2027",
         "fassung": "Finanzplan 2027–2030, Vorlage des Regierungsrates vom 15. September 2026"} for j in (2028, 2029, 2030)]

# Erfolgsrechnung: Datei, Spalte je Datensatz (die erste Datei, die einen Wert hat, gilt)
ER_QUELLEN = {
    "b25": [("rechnung2025.csv", "budget_2025"), ("budget2026.csv", "budget_2025")],
    "r25": [("rechnung2025.csv", "rechnung_2025")],
    "b26": [("budget2026.csv", "budget_2026")],
    "b27": [("budget2027.csv", "budget_2027")],
}
IR_QUELLEN = {
    "b25": [("rechnung2025_ir.csv", "budget_2025"), ("budget2026_ir.csv", "budget_2025")],
    "r25": [("rechnung2025_ir.csv", "rechnung_2025")],
    "b26": [("budget2026_ir.csv", "budget_2026")],
    "b27": [("budget2027_ir.csv", "budget_2027")],
}
# Kommentar der Dienststellen: je Datensatz das Dokument, das ihn begründet
KOMMENTAR = {"b27": "budget2027.csv", "r25": "rechnung2025.csv", "b26": "budget2026.csv"}
NAMEN_REIHENFOLGE = ["budget2027.csv", "rechnung2025.csv", "budget2026.csv"]   # jüngste Bezeichnung gilt

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
    "90": "Abschluss Spezialfinanzierungen und Fonds", "901": "Abschluss Spezialfinanzierungen und Fonds",
}
# Investitionsrechnung, Kontenrahmen HRM2, zweistellig
HRM2_IR = {
    "50": "Sachanlagen", "51": "Investitionen auf Rechnung Dritter", "52": "Immaterielle Anlagen",
    "54": "Darlehen", "55": "Beteiligungen und Grundkapitalien", "56": "Eigene Investitionsbeiträge",
    "57": "Durchlaufende Investitionsbeiträge", "58": "Ausserordentliche Investitionen",
    "60": "Übertragung von Sachanlagen in das Finanzvermögen", "61": "Rückerstattungen",
    "62": "Übertragung immaterieller Anlagen in das Finanzvermögen", "63": "Investitionsbeiträge für eigene Rechnung",
    "64": "Rückzahlung von Darlehen", "65": "Übertragung von Beteiligungen",
    "66": "Rückzahlung eigener Investitionsbeiträge", "67": "Durchlaufende Investitionsbeiträge",
    "68": "Ausserordentliche Investitionseinnahmen",
}

# Kurze Erklärung je zweistelliger Gruppe, für den Überblick. Laienverständlich,
# ohne Wertung, mit dem grössten Posten des Kantons als Beispiel.
ERKLAERUNG = {
    "30": "Löhne und Sozialbeiträge für Verwaltung, Lehrpersonen, Polizei, Gerichte",
    "31": "Material, Energie, Unterhalt, Mieten, Dienstleistungen Dritter",
    "33": "Wertverzehr von Gebäuden, Strassen und Anlagen",
    "34": "Zinsen und übriger Finanzaufwand",
    "35": "Einlagen in zweckgebundene Fonds",
    "36": "Beiträge an Spitäler, Gemeinden, Hochschulen, Prämienverbilligung, Sozialversicherungen, Finanzausgleich",
    "37": "Geld, das der Kanton nur weiterleitet, etwa Bundesbeiträge an Gemeinden",
    "40": "Steuern natürlicher und juristischer Personen, Grundstückgewinn-, Erbschafts-, Motorfahrzeugsteuern",
    "41": "Konzessionen, Spielbankenabgabe, Anteil am Gewinn der Nationalbank",
    "42": "Gebühren, Bussen, Verkäufe, Rückerstattungen",
    "43": "Aktivierte Eigenleistungen, Bestandesveränderungen, übrige betriebliche Erträge",
    "44": "Beteiligungen, Liegenschaften, Zinsen; darunter Kantonalbank und Axpo",
    "45": "Entnahmen aus zweckgebundenen Fonds",
    "46": "Anteile an Bundessteuern, Finanzausgleich, Beiträge von Bund und Gemeinden",
    "47": "Geld, das der Kanton nur weiterleitet, etwa Bundesbeiträge an Gemeinden",
}

ORD = lambda g: g[0] in "34" and g not in ("38", "39", "48", "49")


def lies(datei: str) -> list[dict]:
    with open(DATEN / datei, encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=";"))


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


def erfolgsrechnung():
    """Kontozeilen je Schlüssel (Departement, Dienststelle, Fonds, Konto) mit einem Wert je Datensatz."""
    werte: dict[tuple, dict[str, float]] = defaultdict(dict)
    namen: dict[tuple, tuple] = {}
    kommentare: dict[str, dict[str, str]] = {k: {} for k in KOMMENTAR}
    dateien = {d for q in ER_QUELLEN.values() for d, _ in q}
    zeilen = {d: lies(d) for d in dateien}
    for ds, quellen in ER_QUELLEN.items():
        # Summen je Schlüssel aus der ersten Datei, die den Schlüssel führt
        belegt = set()
        for datei, spalte in quellen:
            summe = defaultdict(float)
            for r in zeilen[datei]:
                if not r["konto"] or r["konto"][0] not in "349" or not r[spalte]:
                    continue
                k = (r["departement"], r["dienststelle"], r["spezialfinanzierung"], r["konto"])
                summe[k] += float(r[spalte])
            for k, v in summe.items():
                if k not in belegt:
                    werte[k][ds] = v
            belegt |= set(summe)
    for datei in reversed(NAMEN_REIHENFOLGE):
        for r in zeilen.get(datei) or lies(datei):
            if r["konto"]:
                k = (r["departement"], r["dienststelle"], r["spezialfinanzierung"], r["konto"])
                namen[k] = (r["departement_name"], r["dienststelle_name"], r["spezialfinanzierung_name"], r["bezeichnung"])
    for ds, datei in KOMMENTAR.items():
        for r in zeilen.get(datei) or lies(datei):
            t = (r.get("kommentar") or "").strip()
            if t:
                kommentare[ds][f"{r['dienststelle']}|{r['spezialfinanzierung']}|{r['konto']}"] = t
    return werte, namen, kommentare


def investitionsrechnung():
    werte: dict[tuple, dict[str, list[float]]] = defaultdict(dict)
    konten, projekte, namen = {}, {}, {}
    dateien = {d for q in IR_QUELLEN.values() for d, _ in q}
    zeilen = {d: lies(d) for d in dateien}
    for ds, quellen in IR_QUELLEN.items():
        belegt = set()
        for datei, spalte in quellen:
            summe = defaultdict(lambda: [0.0, 0.0])
            for r in zeilen[datei]:
                a, e = r[spalte + "_ausgaben"], r[spalte + "_einnahmen"]
                if not (a or e):
                    continue
                k = (r["departement"], r["dienststelle"], r["spezialfinanzierung"], r["konto"], r["projekt"])
                summe[k][0] += float(a or 0)
                summe[k][1] += float(e or 0)
            for k, v in summe.items():
                if k not in belegt:
                    werte[k][ds] = v
            belegt |= set(summe)
    for datei in ["budget2026_ir.csv", "rechnung2025_ir.csv", "budget2027_ir.csv"]:
        for r in zeilen[datei]:
            konten[r["konto"]] = r["konto_name"]
            projekte[r["projekt"]] = r["projekt_name"]
            namen[(r["departement"], r["dienststelle"], r["spezialfinanzierung"])] = (
                r["departement_name"], r["dienststelle_name"], r["spezialfinanzierung_name"])
    return werte, konten, projekte, namen


def kennzahlen_konten(z: list, i: int, ir: list, j: int) -> dict:
    """Kennzahlen eines Datensatzes aus den Kontozeilen (Franken)."""
    g = defaultdict(float)
    for row in z:
        g[row[3][:2]] += row[5 + i]
    auf = sum(v for c, v in g.items() if c[0] == "3" and ORD(c))
    ert = -sum(v for c, v in g.items() if c[0] == "4" and ORD(c))
    ao = -(g.get("38", 0) + g.get("48", 0))
    ek = -g.get("90", 0)
    inv_a = sum(r[5][2 * j] for r in ir)
    inv_e = sum(r[5][2 * j + 1] for r in ir)
    return {"ert": ert, "auf": auf, "ord": ert - auf, "ao": ao, "ek": ek, "gesamt": ert - auf + ao + ek,
            "fiskal": -g.get("40", 0), "transferE": -g.get("46", 0), "finanzE": -g.get("44", 0),
            "pers": g.get("30", 0), "sach": g.get("31", 0), "transfer": g.get("36", 0), "abschr": g.get("33", 0),
            "iv": g.get("39", 0), "invA": inv_a, "invE": inv_e, "netInv": inv_a - inv_e}


def kennzahlen_plan(fp: dict, s: int) -> dict:
    """Kennzahlen eines Planjahres aus Ziffer 2.1 und 2.2 (Tausend Franken -> Franken)."""
    e = {k: v[s] * 1000 for k, v in fp["erfolg"].items()}
    i = {k: v[s] * 1000 for k, v in fp["invest"].items()}
    ert = sum(e[c] for c in ("40", "41", "42", "43", "44", "45", "46", "47"))
    auf = -sum(e[c] for c in ("30", "31", "33", "34", "35", "36", "37"))
    ao = e["48"] + e["38"]
    return {"ert": ert, "auf": auf, "ord": ert - auf, "ao": ao, "ek": e["90"], "gesamt": e["gesamt"],
            "fiskal": e["40"], "transferE": e["46"], "finanzE": e["44"],
            "pers": -e["30"], "sach": -e["31"], "transfer": -e["36"], "abschr": -e["33"],
            "iv": 0, "invA": i["ausgaben"], "invE": i["einnahmen"], "netInv": i["netto"]}


def main() -> None:
    fp = json.loads((DATEN / "finanzplan2027.json").read_text(encoding="utf-8"))
    quellen = json.loads((DATEN / "quellen.json").read_text(encoding="utf-8"))
    er, er_namen, kommentare = erfolgsrechnung()
    ir, ir_konten, ir_projekte, ir_namen = investitionsrechnung()
    keys = [j["k"] for j in JAHRE]

    dep, dst, spz, zeilen = {}, {}, {}, []
    for k in sorted(er):
        d, ds, sp, ko = k
        n = er_namen[k]
        dep.setdefault(d, n[0])
        if n[1] and not dst.get(ds):
            dst[ds] = n[1]
        dst.setdefault(ds, n[1])
        if sp:
            spz.setdefault(sp, n[2])
        w = [round(er[k].get(j, 0.0)) for j in keys]
        if any(w):
            zeilen.append([d, ds, sp, ko, n[3], *w])
    # Dienststellennummern ohne Kopfzeile im PDF (z. B. 2198, 2398) tragen nur
    # Fonds und Spezialfinanzierungen; so heissen sie dann auch.
    nur_fonds = {ds for ds in dst if not dst[ds]}
    for z in zeilen:
        if z[1] in nur_fonds and not z[2]:
            nur_fonds.discard(z[1])
    for ds in nur_fonds:
        dst[ds] = "Fonds und Spezialfinanzierungen"

    ir_zeilen = []
    for k in sorted(ir):
        d, ds, sp, ko, pr = k
        n = ir_namen.get((d, ds, sp), ("", "", ""))
        dep.setdefault(d, n[0])
        if n[1] and not dst.get(ds):
            dst[ds] = n[1]
        dst.setdefault(ds, n[1] or "Fonds und Spezialfinanzierungen")
        if sp:
            spz.setdefault(sp, n[2])
        w = []
        for j in keys:
            a, e = ir[k].get(j, [0.0, 0.0])
            w += [round(a), round(e)]
        if any(w):
            ir_zeilen.append([d, ds, sp, ko, pr, w])

    sg = kontenplan()
    daten_kz = {}
    for i, j in enumerate(JAHRE):
        daten_kz[j["k"]] = kennzahlen_konten(zeilen, i, ir_zeilen, i)
    spalte = {(s["art"][0] if s["art"] != "finanzplan" else "p") + str(s["jahr"] % 100): n
              for n, s in enumerate(fp["spalten"])}
    for p in PLAN:
        daten_kz[p["k"]] = kennzahlen_plan(fp, spalte[p["k"]])
    # Bilanz, Nettoschuld und Steuerfuss: nur wo der Bericht sie führt (Budget 2026 aktualisiert)
    bilanz = {}
    for k, s in spalte.items():
        bilanz[k] = {"ek": fp["bilanz"]["ek"][s] * 1000, "fk": fp["bilanz"]["fk"][s] * 1000,
                     "fv": fp["bilanz"]["fv"][s] * 1000, "reserven": fp["bilanz"]["reserven"][s] * 1000,
                     "fluessig": fp["bilanz"]["fluessig"][s] * 1000,
                     "ns1": fp["nettoschuld1"][s] * 1000 if fp.get("nettoschuld1") else None}
        daten_kz.setdefault(k, {})
        daten_kz[k]["ekap"] = bilanz[k]["ek"]
        daten_kz[k]["sfnp"] = fp["steuerfuss"]["np"][s]
        daten_kz[k]["sfjp"] = fp["steuerfuss"]["jp"][s]
    # Steuerfuss 2025: dasselbe Steuerjahr, Budget und Rechnung
    daten_kz["b25"]["sfnp"], daten_kz["b25"]["sfjp"] = daten_kz["r25"]["sfnp"], daten_kz["r25"]["sfjp"]

    agg = {}
    for p in PLAN:
        s = spalte[p["k"]]
        agg[p["k"]] = {c: -fp["erfolg"][c][s] * 1000 for c in fp["erfolg"] if c.isdigit()}
    aggir = {p["k"]: [fp["invest"]["ausgaben"][spalte[p["k"]]] * 1000, fp["invest"]["einnahmen"][spalte[p["k"]]] * 1000]
             for p in PLAN}

    # Kommentare: nur zu Konten, die in den Daten stehen, und zu Dienststellen
    komm = {ds: {k: t for k, t in m.items()} for ds, m in kommentare.items()}

    # Namen der Sachgruppen: Erfolgsrechnung zwei- und dreistellig, Investitionsrechnung zweistellig
    sgn = {c: n for c, n in sg.items() if len(c) in (2, 3) and c[0] in "349"}
    sgn.update(HRM2_IR)

    daten = {
        "stand": date.today().isoformat(),
        "jahre": JAHRE, "plan": PLAN,
        "dep": dep, "dst": dst, "spz": spz, "sg": sgn, "erkl": ERKLAERUNG,
        "z": zeilen,
        "ir": ir_zeilen, "irk": {k: v for k, v in ir_konten.items() if k}, "irp": {k: v for k, v in ir_projekte.items() if k},
        "agg": agg, "aggir": aggir, "kz": daten_kz, "bilanz": bilanz,
        "felder": fp["felder"],
        "komm": komm,
        "quellen": quellen.get("verarbeitet", []),
    }
    ziel = DATEN / "finanzspiegel.json"
    ziel.write_text(json.dumps(daten, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    print(f"{len(zeilen)} Kontozeilen Erfolgsrechnung, {len(ir_zeilen)} Zeilen Investitionsrechnung, "
          f"{len(dep)} Departemente, {len(dst)} Dienststellen, {len(spz)} Fonds; "
          f"{sum(len(m) for m in komm.values())} Kommentare; {ziel.name} {ziel.stat().st_size / 1024:.0f} kB")
    fehlt = sorted({z[3][:n] for z in zeilen for n in (2, 3)} - set(sgn))
    print("Sachgruppen ohne Namen:", fehlt or "keine")

    # Kontrollen gegen den Bericht (Tausend Franken, Toleranz 1 für Rundung)
    abw = 0
    for k in ("r25", "b26", "b27"):
        i, s = keys.index(k), spalte[k]
        g = defaultdict(float)
        for z in zeilen:
            g[z[3][:2]] += z[5 + i]
        for c, v in fp["erfolg"].items():
            if c.isdigit() and c != "90" and abs(-g.get(c, 0) / 1000 - v[s]) > 1:
                abw += 1
                print(f"  Abweichung 2.1 {k} {c}: Daten {-g.get(c, 0) / 1000:,.0f} Bericht {v[s]:,}")
        if abs(-g.get("90", 0) / 1000 - fp["erfolg"]["90"][s]) > 1:
            abw += 1
        d = defaultdict(float)
        for z in zeilen:
            d[z[0]] += z[5 + i]
        for c, v in fp["departemente"].items():
            if c != "gesamt" and abs(-d.get(c, 0) / 1000 - v[s]) > 1:
                abw += 1
                print(f"  Abweichung 4.4.2 {k} Departement {c}: Daten {-d.get(c, 0) / 1000:,.0f} Bericht {v[s]:,}")
        net = daten_kz[k]["netInv"] / 1000
        if abs(net - fp["invest"]["netto"][s]) > 1:
            print(f"  Hinweis 2.2 {k}: Nettoinvestitionen Detailzahlen {net:,.1f}, Übersicht {fp['invest']['netto'][s]:,} (siehe analyse.py)")
    print(f"Kontrolle Ziffer 2.1 und 4.4.2 (Rechnung 2025, Budget 2026, Budget 2027): {abw} Abweichungen")
    for j in JAHRE + PLAN:
        K = daten_kz[j["k"]]
        print(f"  {j['t']:<16} Ertrag {K['ert'] / 1e6:8.1f}  Aufwand {K['auf'] / 1e6:8.1f}  operativ {K['ord'] / 1e6:7.1f}  "
              f"a.o. {K['ao'] / 1e6:5.1f}  EK {K['ek'] / 1e6:4.1f}  Gesamt {K['gesamt'] / 1e6:6.1f}  "
              f"Nettoinvestitionen {K['netInv'] / 1e6:6.1f} Mio.")


if __name__ == "__main__":
    main()

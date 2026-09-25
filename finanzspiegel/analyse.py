#!/usr/bin/env python3
"""Prüfhinweise für den Finanzspiegel: Stellen, an denen Zahlen sich stark verändern,
vom Budget abweichen oder zwischen Dokumenten nicht übereinstimmen.

Aufruf aus der Projektwurzel, nach daten.py:
    python3 finanzspiegel/analyse.py

Liest    finanzspiegel/daten/finanzspiegel.json      daten.py
         finanzspiegel/daten/budget2027.csv (+ _ir)  Vergleichsspalten Budget 2026 und Rechnung 2025
         finanzspiegel/daten/finanzplan2027.json     Ziffern 2.2 und 5.3 des Berichts
         finanzspiegel/daten/*_pruefung.json         Selbstprüfung von budget_pdf.py
Schreibt finanzspiegel/daten/finanzspiegel.json      ergänzt um «befunde», «regeln», «pruefung»

Die Hinweise sind Feststellungen mit Zahlen, keine Bewertung. Jeder nennt die Beträge,
die Kommentare der Dienststellen aus dem Budget oder der Staatsrechnung im Wortlaut und
den Ort im Vergleich. Regeln und Schwellen stehen in REGELN und erscheinen auf der Seite.
Nettoaufwand je Dienststelle wird über alle Konten gerechnet, wie die Summenzeilen in
Kapitel 6 der Dokumente.
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

HIER = Path(__file__).resolve().parent
DATEN = HIER / "daten"

SCHWELLEN = {
    "bb_chf": 1_000_000, "bb_pct": 0.10,     # Budget 2027 zu Budget 2026, je Dienststelle
    "br_chf": 2_000_000, "br_pct": 0.15,     # Budget 2027 zu Rechnung 2025, je Dienststelle
    "rb_chf": 1_000_000, "rb_pct": 0.10,     # Rechnung 2025 zu Budget 2025, je Dienststelle
    "neu_chf": 250_000,                      # Dienststelle oder Fonds neu oder ohne Beträge
    "ir_rb_chf": 1_000_000, "ir_rb_pct": 0.30,   # Investitionen, Rechnung 2025 zu Budget 2025, je Vorhaben
    "ir_bb_chf": 2_000_000,                  # Investitionen, Budget 2027 zu Budget 2026, je Vorhaben
    "konten": 3,                             # grösste Konten je Hinweis
}
SACHANLAGEN = {"500": "Grundstücke", "501": "Strassen/Verkehrswege", "502": "Wasserbau", "504": "Hochbauten",
               "506": "Mobilien", "509": "Übrige Sachanlagen"}
TYPEN = ["Dokumentenabgleich", "Budget zu Vorjahresbudget", "Budget zu letzter Rechnung",
         "Rechnung zu Budget", "Strukturänderung", "Investition Rechnung zu Budget", "Investition Budget zu Vorjahresbudget"]


def mio(v: float, st: int = 2) -> str:
    s = f"{abs(v) / 1e6:,.{st}f}".replace(",", "'")
    return ("−" if v < 0 else "") + s


def mio_vz(v: float, st: int = 2) -> str:
    return ("+" if v > 0 else "−" if v < 0 else "±") + f"{abs(v) / 1e6:,.{st}f}".replace(",", "'")


def fr(v: float) -> str:
    return ("−" if v < 0 else "") + f"{abs(round(v)):,}".replace(",", "'")


def pct(d: float, b: float) -> str:
    return f"{'+' if d >= 0 else '−'}{abs(100 * d / b):.1f} %" if abs(b) >= 1 else "neu"


def stufe(chf: float) -> int:
    return 1 if abs(chf) >= 5e6 else 2 if abs(chf) >= 1e6 else 3


def main() -> None:
    D = json.loads((DATEN / "finanzspiegel.json").read_text(encoding="utf-8"))
    fp = json.loads((DATEN / "finanzplan2027.json").read_text(encoding="utf-8"))
    keys = [j["k"] for j in D["jahre"]]
    titel = {j["k"]: j["t"] for j in D["jahre"]}
    I = {k: i for i, k in enumerate(keys)}
    S = SCHWELLEN
    befunde = []

    def dst_name(ds):
        return D["dst"].get(ds) or f"Dienststelle {ds}"

    # ── Nettoaufwand je Dienststelle, alle Konten; Aufwand und Ertrag getrennt
    netto = defaultdict(lambda: defaultdict(float))
    aufw = defaultdict(lambda: defaultdict(float))
    ertr = defaultdict(lambda: defaultdict(float))
    konto = defaultdict(lambda: defaultdict(float))   # (dst, spz, konto) -> ds -> Wert
    bez = {}
    dep_von = {}
    for z in D["z"]:
        d, ds, sp, ko, b = z[:5]
        dep_von[ds] = d
        bez[(ds, sp, ko)] = b
        for k in keys:
            v = z[5 + I[k]]
            netto[ds][k] += v
            if v > 0:
                aufw[ds][k] += v
            else:
                ertr[ds][k] -= v
            konto[(ds, sp, ko)][k] += v

    def komm_zu(ds_key, dst, konten_liste):
        """Kommentare der Dienststelle im Wortlaut: zuerst zur Dienststelle, dann zu den Konten."""
        m = D["komm"].get(ds_key, {})
        aus = []
        t = m.get(f"{dst}||")
        if t:
            aus.append([ds_key, f"{dst} {dst_name(dst)}", t])
        for (ds, sp, ko), _ in konten_liste:
            t = m.get(f"{ds}|{sp}|{ko}")
            if t:
                aus.append([ds_key, f"{ko} {bez.get((ds, sp, ko), '')}", t])
        return aus

    def groesste(dst, a, b):
        diffs = [((ds, sp, ko), w.get(b, 0) - w.get(a, 0)) for (ds, sp, ko), w in konto.items() if ds == dst]
        diffs = [x for x in diffs if abs(x[1]) >= 0.5]
        diffs.sort(key=lambda x: -abs(x[1]))
        return diffs[:S["konten"]]

    def veraenderung(typ, a, b, schw_chf, schw_pct, komm_ds, text_komm):
        for ds in sorted(netto):
            va, vb = netto[ds].get(a, 0.0), netto[ds].get(b, 0.0)
            d = vb - va
            if abs(d) < schw_chf or (abs(va) >= 1 and abs(d) / abs(va) < schw_pct):
                continue
            if abs(va) < 1 or abs(vb) < 1:
                continue   # neu oder aufgehoben: Strukturänderung
            top = groesste(ds, a, b)
            fakten = [
                f"{titel[a]}: Nettoaufwand {mio(va)} Mio. Franken (Aufwand {mio(aufw[ds][a])}, Ertrag {mio(ertr[ds][a])}).",
                f"{titel[b]}: Nettoaufwand {mio(vb)} Mio. Franken (Aufwand {mio(aufw[ds][b])}, Ertrag {mio(ertr[ds][b])}).",
                f"Veränderung: {mio_vz(d)} Mio. Franken ({pct(d, va)}).",
            ]
            andere = [k for k in ("r25", "b26", "b27", "b25") if k not in (a, b) and abs(netto[ds].get(k, 0)) >= 1][:1]
            for k in andere:
                fakten.append(f"Zum Vergleich {titel[k]}: Nettoaufwand {mio(netto[ds][k])} Mio. Franken.")
            if top:
                fakten.append("Grösste Veränderungen je Konto: " + "; ".join(
                    f"{ko} {bez.get((x, sp, ko), '')} {mio_vz(v)} Mio." for (x, sp, ko), v in top))
            befunde.append({
                "typ": typ, "titel": f"{ds} {dst_name(ds)}: Nettoaufwand {mio(va, 1)} → {mio(vb, 1)} Mio. Franken ({pct(d, va)})",
                "ds": [b, a], "chf": round(d), "fakten": fakten,
                "komm": komm_zu(komm_ds, ds, top), "komm_titel": text_komm,
                "rechnung": "er", "gl": "inst", "ansicht": "N", "umfang": "alle",
                "pfad": [f"d{dep_von[ds]}", f"s{ds}"],
            })

    veraenderung("Budget zu Vorjahresbudget", "b26", "b27", S["bb_chf"], S["bb_pct"], "b27",
                 "Kommentare im Budget 2027 zur Abweichung gegenüber dem Budget 2026")
    veraenderung("Budget zu letzter Rechnung", "r25", "b27", S["br_chf"], S["br_pct"], "b27",
                 "Kommentare im Budget 2027 (sie beziehen sich auf das Budget 2026)")
    veraenderung("Rechnung zu Budget", "b25", "r25", S["rb_chf"], S["rb_pct"], "r25",
                 "Kommentare in der Staatsrechnung 2025 zur Abweichung gegenüber dem Budget 2025")

    # ── Strukturänderung: Dienststelle mit Beträgen in einem Budget und keinen im anderen
    for ds in sorted(netto):
        a26 = aufw[ds].get("b26", 0) + ertr[ds].get("b26", 0)
        a27 = aufw[ds].get("b27", 0) + ertr[ds].get("b27", 0)
        if (a26 < 1 and a27 >= S["neu_chf"]) or (a27 < 1 and a26 >= S["neu_chf"]):
            neu = a26 < 1
            fakten = [f"Budget 2026: Aufwand {mio(aufw[ds].get('b26', 0))}, Ertrag {mio(ertr[ds].get('b26', 0))} Mio. Franken.",
                      f"Budget 2027: Aufwand {mio(aufw[ds].get('b27', 0))}, Ertrag {mio(ertr[ds].get('b27', 0))} Mio. Franken."]
            if abs(netto[ds].get("r25", 0)) >= 1:
                fakten.append(f"Rechnung 2025: Nettoaufwand {mio(netto[ds]['r25'])} Mio. Franken.")
            befunde.append({
                "typ": "Strukturänderung",
                "titel": f"{ds} {dst_name(ds)}: {'neu im Budget 2027' if neu else 'im Budget 2027 ohne Beträge'}",
                "ds": ["b27", "b26"], "chf": round(max(a26, a27)), "fakten": fakten,
                "komm": komm_zu("b27", ds, groesste(ds, "b26", "b27")), "komm_titel": "Kommentare im Budget 2027",
                "rechnung": "er", "gl": "inst", "ansicht": "N", "umfang": "alle",
                "pfad": [f"d{dep_von[ds]}", f"s{ds}"],
            })

    # ── Dokumentenabgleich Erfolgsrechnung: Vergleichsspalten im Budget 2027 gegen die Datensätze
    with open(DATEN / "budget2027.csv", encoding="utf-8") as f:
        b27_doc = list(csv.DictReader(f, delimiter=";"))
    for spalte, k, dok in (("budget_2026", "b26", "Budget 2026, beschlossene Fassung"),
                           ("rechnung_2025", "r25", "Staatsrechnung 2025")):
        vgl = defaultdict(float)
        for r in b27_doc:
            if r["konto"] and r[spalte]:
                vgl[(r["dienststelle"], r["spezialfinanzierung"], r["konto"])] += float(r[spalte])
        for key in sorted(set(vgl) | {x for x, w in konto.items() if abs(w.get(k, 0)) >= 0.5}):
            # Die Datensätze sind auf Franken gerundet, die Vergleichsspalte hat Rappen
            a, b = round(vgl.get(key, 0.0)), konto.get(key, {}).get(k, 0.0)
            if abs(a - b) < 1:
                continue
            ds, sp, ko = key
            ort = f"Fonds {sp} {D['spz'].get(sp, '')}" if sp else f"{ds} {dst_name(ds)}"
            fakten = [f"Dokument Budget 2027, Spalte {titel[k]}: {fr(a)} Franken.",
                      f"{dok}: {fr(b)} Franken.",
                      f"Differenz: {fr(a - b)} Franken."]
            # Folgen für Summen im Budget 2027: Ziffer 2.1 führt den Wert der beschlossenen Fassung
            if k == "b26":
                sg = ko[:2]
                s21 = fp["erfolg"].get(sg, [None] * 6)[1]
                if s21 is not None:
                    summe_doc = sum(float(r[spalte] or 0) for r in b27_doc if r["konto"][:2] == sg)
                    fakten.append(f"Sachgruppe {sg} im Dokument Budget 2027: Detailzahlen {mio(-summe_doc if sg[0] == '4' else summe_doc)} "
                                  f"Mio., Ziffer 2.1 {mio(abs(s21) * 1000)} Mio. Franken.")
            befunde.append({
                "typ": "Dokumentenabgleich",
                "titel": f"{ko} {bez.get(key, '')}, {ort}: {titel[k]} {fr(a)} statt {fr(b)} Franken",
                "ds": ["b27", k], "chf": round(a - b), "fakten": fakten,
                "komm": [x for x in komm_zu("b27", ds, [(key, 0)]) if x[1].startswith(ko)], "komm_titel": "Kommentar im Budget 2027",
                "rechnung": "er", "gl": "inst", "ansicht": "N", "umfang": "alle",
                "pfad": [f"d{dep_von[ds]}", f"s{ds}"] + ([f"f{sp}"] if sp else []), "markiert": f"k{ds}|{sp}|{ko}",
            })

    # ── Investitionsrechnung
    iw = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0]))   # Vorhaben -> ds -> [A, E]
    vorhaben_ort = {}
    for z in D["ir"]:
        d, ds, sp, ko, pr, w = z
        vorhaben_ort.setdefault(pr, (d, ds, sp))
        for k in keys:
            a, e = w[2 * I[k]], w[2 * I[k] + 1]
            iw[pr][k][0] += a
            iw[pr][k][1] += e
    netto_ir = lambda pr, k: iw[pr][k][0] - iw[pr][k][1]

    for pr in sorted(iw):
        d, ds, sp = vorhaben_ort[pr]
        name = D["irp"].get(pr, pr)
        rb, rr = netto_ir(pr, "b25"), netto_ir(pr, "r25")
        dd = rr - rb
        if abs(dd) >= S["ir_rb_chf"] and (abs(rb) < 1 or abs(dd) / abs(rb) >= S["ir_rb_pct"]):
            befunde.append({
                "typ": "Investition Rechnung zu Budget",
                "titel": f"{pr} {name}: Rechnung 2025 {mio(rr, 1)} Mio. bei Budget {mio(rb, 1)} Mio. Franken",
                "ds": ["r25", "b25"], "chf": round(dd),
                "fakten": [f"Budget 2025: Nettoinvestition {mio(rb)} Mio. Franken.",
                           f"Rechnung 2025: Nettoinvestition {mio(rr)} Mio. Franken.",
                           f"Differenz: {mio_vz(dd)} Mio. Franken ({pct(dd, rb)}).",
                           f"Dienststelle {ds} {dst_name(ds)}."]
                + ([f"Budget 2026: {mio(netto_ir(pr, 'b26'))} Mio., Budget 2027: {mio(netto_ir(pr, 'b27'))} Mio. Franken."]
                   if abs(netto_ir(pr, "b26")) + abs(netto_ir(pr, "b27")) >= 1 else []),
                "komm": [], "komm_titel": "",
                "rechnung": "ir", "gl": "inst", "ansicht": "N", "umfang": "alle",
                "pfad": [f"d{d}", f"s{ds}"] + ([f"f{sp}"] if sp else []), "markiert": f"v{ds}|{sp}|{pr}",
            })
        b6, b7 = netto_ir(pr, "b26"), netto_ir(pr, "b27")
        d2 = b7 - b6
        if abs(d2) >= S["ir_bb_chf"]:
            befunde.append({
                "typ": "Investition Budget zu Vorjahresbudget",
                "titel": f"{pr} {name}: Budget 2027 {mio(b7, 1)} Mio. nach {mio(b6, 1)} Mio. Franken im Budget 2026",
                "ds": ["b27", "b26"], "chf": round(d2),
                "fakten": [f"Budget 2026: Nettoinvestition {mio(b6)} Mio. Franken.",
                           f"Budget 2027: Nettoinvestition {mio(b7)} Mio. Franken.",
                           f"Veränderung: {mio_vz(d2)} Mio. Franken.",
                           f"Rechnung 2025: {mio(netto_ir(pr, 'r25'))} Mio. Franken.",
                           f"Dienststelle {ds} {dst_name(ds)}."],
                "komm": [], "komm_titel": "",
                "rechnung": "ir", "gl": "inst", "ansicht": "N", "umfang": "alle",
                "pfad": [f"d{d}", f"s{ds}"] + ([f"f{sp}"] if sp else []), "markiert": f"v{ds}|{sp}|{pr}",
            })

    # ── Dokumentenabgleich Investitionsrechnung: Detailzahlen gegen Ziffer 2.2 und 5.3.1
    s27 = [n for n, s in enumerate(fp["spalten"]) if s["art"] == "budget" and s["jahr"] == 2027][0]
    netz = {k: sum(z[5][2 * I[k]] - z[5][2 * I[k] + 1] for z in D["ir"]) for k in ("r25", "b26", "b27")}
    for k, s in (("r25", 0), ("b26", 1), ("b27", s27)):
        bericht = fp["invest"]["netto"][s] * 1000
        if abs(netz[k] - bericht) >= 1000:   # Bericht in Tausend Franken
            je_dep = defaultdict(float)
            for z in D["ir"]:
                je_dep[z[0]] += z[5][2 * I[k]] - z[5][2 * I[k] + 1]
            fakten = [f"Detailzahlen Investitionsrechnung (Kapitel 6): Nettoinvestitionen {mio(netz[k])} Mio. Franken.",
                      f"Übersicht (Ziffer 2.2): {mio(bericht)} Mio. Franken.",
                      f"Differenz: {mio_vz(netz[k] - bericht)} Mio. Franken."]
            markiert = None
            pfad = []
            for dep_code, v in sorted(je_dep.items()):
                name = D["dep"].get(dep_code, dep_code)
                bericht_dep = (fp.get("invest_dep") or {}).get(dep_code)
                if bericht_dep is not None and abs(v - bericht_dep[s] * 1000) >= 1000:
                    fakten.append(f"{name}: Detailzahlen {mio(v)} Mio., Ziffer 5.3.1 {mio(bericht_dep[s] * 1000)} Mio. Franken.")
                    pfad = [f"d{dep_code}"]
            je_gruppe = defaultdict(float)
            for z in D["ir"]:
                je_gruppe[z[3][:3]] += z[5][2 * I[k]] - z[5][2 * I[k] + 1]
            for sg, w in (fp.get("sachanlagen") or {}).items():
                if len(sg) == 3 and abs(je_gruppe.get(sg, 0) - w[s] * 1000) >= 1000:
                    fakten.append(f"{SACHANLAGEN.get(sg, 'Sachgruppe ' + sg)} (Sachgruppe {sg}): Detailzahlen {mio(je_gruppe.get(sg, 0))} Mio., "
                                  f"Ziffer 5.3.2 {mio(w[s] * 1000)} Mio. Franken.")
            # Verpflichtungskredite (VK) mit Betrag im Budget 2027, die in der Liste 5.3.10 fehlen.
            # Die Liste gehört zum Dokument Budget 2027, der Abgleich deshalb nur für b27.
            vk_liste = set(fp.get("vk_5310") or [])
            if k == "b27" and vk_liste:
                fehlend, ort = defaultdict(float), {}
                for z in D["ir"]:
                    if z[4] and z[4] not in vk_liste and D["irp"].get(z[4], "").startswith("VK"):
                        fehlend[z[4]] += z[5][2 * I[k]] - z[5][2 * I[k] + 1]
                        ort.setdefault(z[4], (z[0], z[1], z[2]))
                fehlend = {pr: v for pr, v in fehlend.items() if abs(v) >= 1}
                if fehlend:
                    teile = ", ".join(f"{pr} {D['irp'][pr]} {mio(v)} Mio." for pr, v in sorted(fehlend.items()))
                    fakten.append(f"Verpflichtungskredite mit Betrag in den Detailzahlen, die in der Liste der Ziffer 5.3.10 fehlen: "
                                  f"{teile}; zusammen {mio(sum(fehlend.values()))} Mio. Franken.")
                    # Liegen alle in einer Dienststelle, öffnet der Hinweis diese und markiert das erste Vorhaben
                    if len({ort[pr][:2] for pr in fehlend}) == 1:
                        pr = sorted(fehlend)[0]
                        d_, ds_, sp_ = ort[pr]
                        pfad = [f"d{d_}", f"s{ds_}"] + ([f"f{sp_}"] if sp_ else [])
                        markiert = f"v{ds_}|{sp_}|{pr}"
            befunde.append({
                "typ": "Dokumentenabgleich",
                "titel": f"Investitionsrechnung {titel[k]}: Detailzahlen {mio(netz[k], 1)} Mio., Übersicht {mio(bericht, 1)} Mio. Franken",
                "ds": [k], "chf": round(netz[k] - bericht), "fakten": fakten, "komm": [], "komm_titel": "",
                "rechnung": "ir", "gl": "inst", "ansicht": "N", "umfang": "alle", "pfad": pfad,
                **({"markiert": markiert} if markiert else {}),
            })

    # Reihenfolge: Art, dann Betrag
    befunde.sort(key=lambda b: (TYPEN.index(b["typ"]), -abs(b["chf"])))
    for n, b in enumerate(befunde, start=1):
        b["nr"] = n
        b["stufe"] = stufe(b["chf"])
    D["befunde"] = befunde
    D["regeln"] = S
    D["typen"] = TYPEN

    # Selbstprüfung der Leseprogramme für die Quellenangabe
    pruefung = {}
    for q in D["quellen"]:
        if not q.get("csv"):
            continue
        p = DATEN / (Path(q["csv"]).stem + "_pruefung.json")
        if p.exists():
            pruefung[q["k"]] = json.loads(p.read_text(encoding="utf-8"))
    pruefung["finanzplan"] = {"abweichend": len(fp.get("pruefung") or [])}
    D["pruefung"] = pruefung
    (DATEN / "finanzspiegel.json").write_text(json.dumps(D, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    zahl = defaultdict(int)
    for b in befunde:
        zahl[b["typ"]] += 1
    print(f"{len(befunde)} Prüfhinweise: " + ", ".join(f"{t} {zahl[t]}" for t in TYPEN if zahl[t]))
    for b in befunde:
        if b["typ"] in ("Dokumentenabgleich", "Strukturänderung"):
            print(f"  {b['nr']:>3}. {b['typ']}: {b['titel']}")


if __name__ == "__main__":
    main()

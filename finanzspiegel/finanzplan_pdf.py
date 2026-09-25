#!/usr/bin/env python3
"""Liest die Übersichtstabellen aus dem Bericht zu Budget und Finanzplan (PDF).

    python3 finanzplan_pdf.py daten/pdf/budget2027_vorlage.pdf daten/finanzplan2027.json

Der Finanzplan liegt nur zusammengefasst vor, nicht je Konto. Gelesen werden:
    2.1  Erfolgsrechnung, gestufter Erfolgsausweis   Rechnung, Budget, Budget, drei Planjahre
    2.2  Nettoinvestitionen                          dieselben sechs Spalten
    2.3  Bilanz                                      dieselben sechs Spalten
    2.5  Nettoschuld I                               dieselben sechs Spalten
    1.6  Eckwerte, Kennzahlen                        Nettoverschuldungsquotient, Selbstfinanzierungsgrad
    Steuerfuss natürliche und juristische Personen   dieselben sechs Spalten
    4.4.2 Nettoergebnis pro Departement              Rechnung, Budget, Budget
    4.4.3 Nettoergebnis nach Aufgabengebiet          Rechnung, Budget, Budget
    5.3.1 Nettoinvestitionen pro Departement,
    5.3.2 Sachanlagen                                Rechnung, Budget, Budget
    5.3.10 Verpflichtungskredite                     Nummern der Vorhaben (Abgleich mit Kapitel 6)
    7.x  Aufgabenfelder: Ertrag, Aufwand, netto      Budget und drei Planjahre

Beträge in 1'000 Franken wie im Bericht. Selbstprüfung: Jede Zwischensumme wird aus
ihren Teilen nachgerechnet (Toleranz 2, weil der Bericht gerundete Beträge summiert),
die Bilanz muss aufgehen, die Aufgabenfelder müssen das Gesamtergebnis ergeben.

Warum pdftotext: Die Tabellen haben feste Spalten und einzeilige Zahlenreihen;
mehrzeilige Bezeichnungen stehen über und unter der Zahlenzeile. Gelesen werden deshalb
die Zahlenzeilen in ihrer Reihenfolge, und die Bezeichnungen kommen aus der Liste
unten. Rutscht eine Zeile, schlägt die Summenprüfung an.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ZAHL = r"-?\d{1,3}(?:'\d{3})*|-"
REIHE = re.compile(rf"^(?P<text>.*?)\s+(?P<zahlen>(?:(?:{ZAHL})\s+){{2,}}(?:{ZAHL}))(?:\s+\d(?:\.\d)+)?\s*$")
PROZENT = re.compile(r"^(?P<text>.*?)\s+(?P<zahlen>(?:-?[\d.]+%\s+){5,}-?[\d.]+%)\s*$")

# Zeilen der Tabelle 2.1 in ihrer Reihenfolge; Schlüssel = HRM2-Sachgruppe, wo es eine ist
ERFOLG = [
    ("E", "Ertrag"), ("40", "Fiskalertrag"), ("41", "Regalien und Konzessionen"), ("42", "Entgelte"),
    ("43", "Verschiedene Erträge"), ("45", "Entnahmen aus Spezialfinanzierungen und Fonds Fremdkapital"),
    ("46", "Transferertrag"), ("47", "Durchlaufende Beiträge"),
    ("A", "Aufwand"), ("30", "Personalaufwand"), ("31", "Sachaufwand"), ("33", "Abschreibungen"),
    ("35", "Einlagen in Spezialfinanzierungen und Fonds Fremdkapital"), ("36", "Transferaufwand"),
    ("37", "Durchlaufende Beiträge"),
    ("betrieb", "Ergebnis aus betrieblicher Tätigkeit"), ("44", "Finanzertrag"), ("34", "Finanzaufwand"),
    ("finanz", "Ergebnis aus Finanzierung"), ("operativ", "Operatives Ergebnis"),
    ("48", "Ausserordentlicher Ertrag"), ("38", "Ausserordentlicher Aufwand"), ("ao", "Ausserordentliches Ergebnis"),
    ("zwischen", "Zwischenergebnis operativ und ausserordentlich"),
    ("ek_ent", "Entnahmen aus Spezialfinanzierungen und Fonds Eigenkapital"),
    ("ek_ein", "Einlagen in Spezialfinanzierungen und Fonds Eigenkapital"),
    ("90", "Netto Einlagen und Entnahmen Spezialfinanzierungen und Fonds Eigenkapital"),
    ("gesamt", "Gesamtergebnis"),
]
ERFOLG_SUMMEN = {
    "E": ["40", "41", "42", "43", "45", "46", "47"],
    "A": ["30", "31", "33", "35", "36", "37"],
    "betrieb": ["E", "A"], "finanz": ["44", "34"], "operativ": ["betrieb", "finanz"],
    "ao": ["48", "38"], "zwischen": ["operativ", "ao"], "90": ["ek_ent", "ek_ein"],
    "gesamt": ["zwischen", "90"],
}
BILANZ = [
    ("fluessig", "Flüssige Mittel und kurzfristige Geldanlagen"), ("finanzanlagen", "Finanzanlagen"),
    ("uebriges_fv", "Übriges Finanzvermögen"), ("fv", "Total Finanzvermögen"),
    ("sachanlagen", "Sachanlagen Verwaltungsvermögen"), ("beteiligungen", "Beteiligungen, Grundkapitalien"),
    ("investitionsbeitraege", "Investitionsbeiträge"), ("uebriges_vv", "Übriges Verwaltungsvermögen"),
    ("vv", "Total Verwaltungsvermögen"), ("aktiven", "Total Aktiven"),
    ("lang_fv", "Langfristige Finanzverbindlichkeiten"), ("uebriges_fk", "Übriges Fremdkapital"),
    ("fk", "Total Fremdkapital"), ("sf_ek", "Spezialfinanzierungen im Eigenkapital"), ("fonds_ek", "Fonds im Eigenkapital"),
    ("vorfinanzierungen", "Vorfinanzierungen"), ("reserven", "Finanzpolitische Reserven"),
    ("aufwertung", "Aufwertungsreserve"), ("neubewertung", "Neubewertungsreserve Finanzvermögen"),
    ("bilanzueberschuss", "Bilanzüberschuss/-fehlbetrag"), ("ek", "Total Eigenkapital"), ("passiven", "Total Passiven"),
]
BILANZ_SUMMEN = {
    "fv": ["fluessig", "finanzanlagen", "uebriges_fv"],
    "vv": ["sachanlagen", "beteiligungen", "investitionsbeitraege", "uebriges_vv"],
    "aktiven": ["fv", "vv"], "fk": ["lang_fv", "uebriges_fk"],
    "ek": ["sf_ek", "fonds_ek", "vorfinanzierungen", "reserven", "aufwertung", "neubewertung", "bilanzueberschuss"],
    "passiven": ["fk", "ek"],
}
DEPARTEMENTE = [("gesamt", "Gesamtergebnis"), ("10", "Kantonsrat"), ("20", "Regierungsrat/Staatskanzlei"),
                ("21", "Departement des Innern"), ("22", "Erziehungsdepartement"), ("23", "Baudepartement"),
                ("24", "Volkswirtschaftsdepartement"), ("25", "Finanzdepartement"), ("30", "Gerichte")]
FUNKTIONEN_NAMEN = {  # oberste Ebene der funktionalen Gliederung HRM2
    "0": "Allgemeine Verwaltung", "1": "Öffentliche Ordnung und Sicherheit, Verteidigung", "2": "Bildung",
    "3": "Kultur, Sport und Freizeit, Kirche", "4": "Gesundheit", "5": "Soziale Sicherheit",
    "6": "Verkehr und Nachrichtenübermittlung", "7": "Umweltschutz und Raumordnung", "8": "Volkswirtschaft",
    "9": "Finanzen und Steuern"}


def zahl(t: str) -> int:
    return 0 if t == "-" else int(t.replace("'", ""))


def seiten(pdf: str) -> list[str]:
    try:
        text = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, check=True).stdout
    except FileNotFoundError:
        raise SystemExit("pdftotext fehlt (poppler-utils).")
    return text.decode("utf-8", "replace").replace("’", "'").split("\f")


def finde(seitenliste: list[str], titel: str, start: int = 0) -> int:
    """Seite mit dem Titel; Zeilen des Inhaltsverzeichnisses (Titel ... Seitenzahl) zählen nicht."""
    muster = re.compile(titel)
    for i in range(start, len(seitenliste)):
        for z in seitenliste[i].splitlines():
            if muster.match(z.strip()) and not re.search(r"\s{3,}\d{1,3}\s*$", z):
                return i
    raise SystemExit(f"Abschnitt nicht gefunden: {titel}")


def zahlenzeilen(text: str, n: int) -> list[tuple[str, list[int]]]:
    """Zeilen mit genau n Zahlen am Ende, in ihrer Reihenfolge."""
    aus = []
    for z in text.splitlines():
        m = REIHE.match(z.rstrip())
        if not m:
            continue
        werte = re.findall(ZAHL, m.group("zahlen"))
        if len(werte) == n:
            aus.append((m.group("text").strip(), [zahl(w) for w in werte]))
    return aus


def nach_ueberschrift(text: str, titel: str, bis: str | None = None) -> str:
    """Text ab der Zeile mit dem Titel bis vor die Zeile mit bis."""
    zeilen = text.splitlines()
    for i, z in enumerate(zeilen):
        if re.match(titel, z.strip()) and not re.search(r"\s{3,}\d{1,3}\s*$", z):
            rest = zeilen[i + 1:]
            if bis:
                for j, y in enumerate(rest):
                    if re.match(bis, y.strip()):
                        rest = rest[:j]
                        break
            return "\n".join(rest)
    raise SystemExit(f"Überschrift nicht gefunden: {titel}")


def pruefe(werte: dict, summen: dict, spalten: int, name: str, fehler: list) -> None:
    """Zwischensummen nachrechnen. Der Bericht summiert ungerundete Beträge und druckt
    gerundete; je Summand kann die Summe deshalb um einen halben Tausender abweichen."""
    for ziel, teile in summen.items():
        toleranz = max(1, (len(teile) + 1) // 2)
        for s in range(spalten):
            soll = werte[ziel][s]
            ist = sum(werte[t][s] for t in teile)
            if abs(soll - ist) > toleranz:
                fehler.append(f"{name}: {ziel} Spalte {s + 1} gedruckt {soll} nachgerechnet {ist}")


def main() -> int:
    quelle = sys.argv[1] if len(sys.argv) > 1 else "daten/pdf/budget2027_vorlage.pdf"
    ziel = Path(sys.argv[2] if len(sys.argv) > 2 else "daten/finanzplan2027.json")
    S = seiten(quelle)
    fehler: list[str] = []

    # Kopf: Spalten der Übersichtstabellen, aus 2.1 gelesen
    i21 = finde(S, r"2\.1 Erfolgsrechnung")
    kopf = nach_ueberschrift(S[i21], r"2\.1 Erfolgsrechnung")
    arten = re.findall(r"(Rechnung|Budget|Finanzplan)", kopf.split("Ertrag")[0])
    jahre = re.findall(r"\b(20\d\d)\b", kopf.split("Ertrag")[0])
    spalten = [{"art": a.lower(), "jahr": int(j)} for a, j in zip(arten[:6], jahre[:6])]
    if len(spalten) != 6:
        raise SystemExit(f"Kopf von 2.1 nicht erkannt: {arten} {jahre}")

    # 2.1 gestufter Erfolgsausweis
    reihen = zahlenzeilen(nach_ueberschrift(S[i21], r"2\.1 Erfolgsrechnung"), 6)
    if len(reihen) != len(ERFOLG):
        raise SystemExit(f"2.1: {len(reihen)} Zahlenzeilen statt {len(ERFOLG)}")
    erfolg = {k: w for (k, _), (_, w) in zip(ERFOLG, reihen)}
    pruefe(erfolg, ERFOLG_SUMMEN, 6, "2.1", fehler)

    # 2.2 Nettoinvestitionen
    i22 = finde(S, r"2\.2 Nettoinvestitionen")
    r22 = zahlenzeilen(nach_ueberschrift(S[i22], r"2\.2 Nettoinvestitionen"), 6)[:3]
    invest = {"netto": r22[0][1], "ausgaben": r22[1][1], "einnahmen": r22[2][1]}
    pruefe(invest, {"netto": ["ausgaben"]}, 6, "2.2", [])  # Vorzeichen: netto = Ausgaben - Einnahmen
    for s in range(6):
        if abs(invest["netto"][s] - (invest["ausgaben"][s] - invest["einnahmen"][s])) > 2:
            fehler.append(f"2.2 Spalte {s + 1}: netto {invest['netto'][s]} ≠ Ausgaben - Einnahmen")

    # 2.3 Bilanz
    i23 = finde(S, r"2\.3 Bilanz")
    r23 = zahlenzeilen(nach_ueberschrift(S[i23], r"2\.3 Bilanz"), 6)
    if len(r23) != len(BILANZ):
        raise SystemExit(f"2.3: {len(r23)} Zahlenzeilen statt {len(BILANZ)}")
    bilanz = {k: w for (k, _), (_, w) in zip(BILANZ, r23)}
    pruefe(bilanz, BILANZ_SUMMEN, 6, "2.3", fehler)
    for s in range(6):
        if abs(bilanz["aktiven"][s] - bilanz["passiven"][s]) > 2:
            fehler.append(f"2.3 Spalte {s + 1}: Aktiven ≠ Passiven")

    # 2.5 Nettoschuld I
    i25 = finde(S, r"2\.5 Finanzierungsrechnung")
    ns = [w for t, w in zahlenzeilen(S[i25], 6) if t.startswith("Nettoschuld I ")]
    nettoschuld = ns[0] if ns else None

    # 1.6 Eckwerte: Kennzahlen in Prozent, Steuerfuss
    i16 = finde(S, r"1\.6 Budget")
    prozent = {}
    for z in S[i16].splitlines():
        m = PROZENT.match(z.strip())
        if m:
            prozent[m.group("text").strip()] = [float(x.rstrip("%")) for x in m.group("zahlen").split()]
    isf = finde(S, r"Steuerfuss und Lohnentwicklung", i21)
    steuerfuss = {}
    for z in S[isf].splitlines():
        m = re.match(r"^\s*Steuerfuss (natürliche|juristische) Personen\s+((?:\d+%\s*){6})", z)
        if m:
            steuerfuss["np" if m.group(1) == "natürliche" else "jp"] = [int(x) for x in re.findall(r"(\d+)%", m.group(2))]

    # 4.4.2 Departemente, 4.4.3 Funktionen: Rechnung, Budget, Budget, Abweichung absolut, in %
    i442 = finde(S, r"4\.4\.2\s+Nettoergebnis pro Departement")
    t442 = nach_ueberschrift(S[i442], r"4\.4\.2\s+Nettoergebnis pro Departement")
    dep = {}
    for (k, name), (text, w) in zip(DEPARTEMENTE, [r for r in zahlenzeilen_mit_prozent(t442)]):
        if not text.startswith(name[:12]):
            fehler.append(f"4.4.2: erwartet {name}, gelesen {text}")
        dep[k] = w[:3]
    for s in range(3):
        if abs(sum(v[s] for k, v in dep.items() if k != "gesamt") - dep["gesamt"][s]) > 2:
            fehler.append(f"4.4.2 Spalte {s + 1}: Departemente ergeben nicht das Gesamtergebnis")
    i443 = finde(S, r"4\.4\.3\s+Nettoergebnis nach Aufgabengebiet", i442)
    t443 = nach_ueberschrift(S[i443], r"4\.4\.3\s+Nettoergebnis nach Aufgabengebiet", r"4\.4\.4")
    funk_namen = {}
    funktionen = {}
    for z in t443.splitlines():
        m = re.match(rf"^\s*(?:(\d)\s+)?(.*?)\s+((?:(?:{ZAHL})\s+){{4}})(-?[\d.]+|-)\s*$", z)
        if m and m.group(1) is not None:
            funktionen[m.group(1)] = [zahl(x) for x in re.findall(ZAHL, m.group(3))][:3]
            funk_namen[m.group(1)] = m.group(2).strip()
        elif m and m.group(2).startswith("Total"):
            funktionen["total"] = [zahl(x) for x in re.findall(ZAHL, m.group(3))][:3]
    # Mehrzeilige Namen (1 Öffentliche Ordnung und Sicherheit, Verteidigung) stehen neben
    # der Zahlenzeile nicht vollständig; es gelten die Namen des Kontenrahmens.
    for nr in funktionen:
        if nr != "total":
            funk_namen[nr] = FUNKTIONEN_NAMEN[nr]
    if len([k for k in funktionen if k != "total"]) != 10 or "total" not in funktionen:
        fehler.append(f"4.4.3: {len(funktionen)} Zeilen gelesen")
    else:
        for s in range(3):
            if abs(sum(funktionen[str(i)][s] for i in range(10)) - funktionen["total"][s]) > 5:
                fehler.append(f"4.4.3 Spalte {s + 1}: Funktionen ergeben nicht das Total")

    # 5.3.1 Nettoinvestitionen pro Departement, 5.3.2 Sachanlagen: Rechnung, Budget, Budget
    i531 = finde(S, r"5\.3\.1\s+Nettoinvestitionen pro Departement")
    t531 = nach_ueberschrift(S[i531], r"5\.3\.1\s+Nettoinvestitionen pro Departement", r"5\.3\.2")
    namen_dep = {name: k for k, name in DEPARTEMENTE if k != "gesamt"}
    invest_dep = {}
    for text, w in zahlenzeilen_mit_prozent(t531):
        if text in namen_dep:
            invest_dep[namen_dep[text]] = w[:3]
        elif text.startswith("Total"):
            invest_dep["total"] = w[:3]
    for text in namen_dep:   # Zeilen ohne Beträge («Kantonsrat - - -»)
        invest_dep.setdefault(namen_dep[text], [0, 0, 0])
    if "total" in invest_dep:
        for s_ in range(3):
            if abs(sum(v[s_] for k, v in invest_dep.items() if k != "total") - invest_dep["total"][s_]) > 5:
                fehler.append(f"5.3.1 Spalte {s_ + 1}: Departemente ergeben nicht das Total")
            if abs(invest_dep["total"][s_] - invest["netto"][s_]) > 1:
                fehler.append(f"5.3.1 Spalte {s_ + 1}: Total ≠ Ziffer 2.2")
    else:
        fehler.append("5.3.1: Total nicht gelesen")
    t532 = nach_ueberschrift(S[i531], r"5\.3\.2\s+Sachanlagen")
    gruppen_532 = {"Grundstücke": "500", "Strassen/Verkehrswege": "501", "Wasserbau": "502", "Hochbauten": "504",
                   "Mobilien": "506", "Übrige Sachanlagen": "509", "Sachanlagen": "50"}
    sachanlagen = {}
    for text, w in zahlenzeilen_mit_prozent(t532):
        if text in gruppen_532:
            sachanlagen[gruppen_532[text]] = w[:3]
    if "50" in sachanlagen:
        for s_ in range(3):
            if abs(sum(v[s_] for k, v in sachanlagen.items() if k != "50") - sachanlagen["50"][s_]) > 4:
                fehler.append(f"5.3.2 Spalte {s_ + 1}: Gruppen ergeben nicht die Sachanlagen")

    # 5.3.10 Verpflichtungskredite: Nummern der Vorhaben, für den Abgleich mit den Detailzahlen
    # (analyse.py). Die Liste endet mit der Zeile «Total Anträge zum Kreditbeschluss».
    vk_5310 = []
    for i in range(finde(S, r"5\.3\.10\s+Verpflichtungskredite"), len(S)):
        ende = False
        for z in S[i].splitlines():
            if "Total Anträge zum Kreditbeschluss" in z:
                ende = True
                break
            m = re.match(r"^([A-Z]{2,4}\d{3,5}(?:-\d{1,2})?)\s", z)
            if m and m.group(1) not in vk_5310:
                vk_5310.append(m.group(1))
        if ende:
            break
    if not vk_5310:
        fehler.append("5.3.10: keine Vorhaben gelesen")

    # 7.x Aufgabenfelder
    felder = []
    i7 = finde(S, r"7\.1\s+Volkswirtschaft")
    for i in range(i7, len(S)):
        for z in S[i].splitlines():
            m = re.match(r"^\s*7\.(\d+)\s+(.+?)\s*$", z)
            if not m:
                continue
            reihen7 = zahlenzeilen(nach_ueberschrift(S[i], re.escape(z.strip())), 5)[:3]
            wert = {t.split()[0]: w for t, w in reihen7}
            ertrag, aufwand = wert.get("Ertrag"), wert.get("Aufwand")
            netto = wert.get("Nettoaufwand") or wert.get("Nettoertrag")
            if not (ertrag and aufwand and netto):
                fehler.append(f"7.{m.group(1)}: Tabelle nicht gelesen")
                continue
            vz = 1 if "Nettoaufwand" in wert else -1
            for s in range(5):
                if abs(vz * netto[s] - (aufwand[s] - ertrag[s])) > 2:
                    fehler.append(f"7.{m.group(1)} Spalte {s + 1}: netto ≠ Aufwand - Ertrag")
            felder.append({"nr": int(m.group(1)), "name": m.group(2), "ertrag": ertrag[:4], "aufwand": aufwand[:4],
                           "netto": [vz * v for v in netto[:4]], "kumuliert": vz * netto[4]})
    felder.sort(key=lambda f: f["nr"])
    if len(felder) != 10:
        fehler.append(f"Kapitel 7: {len(felder)} Aufgabenfelder statt 10")
    # Aufgabenfelder zusammen = Gesamtergebnis (Budget und Planjahre, Spalten 3 bis 6 von 2.1)
    for s in range(4):
        summe = sum(f["netto"][s] for f in felder)
        if abs(summe + erfolg["gesamt"][2 + s]) > 5:
            fehler.append(f"Kapitel 7 Spalte {s + 1}: Nettoaufwand {summe} ≠ -Gesamtergebnis {erfolg['gesamt'][2 + s]}")

    titelseite = re.sub(r"\s+", " ", S[0] + S[1])
    m = re.search(r"(VORLAGE DES REGIERUNGSRATES VOM|BESCHLOSSEN VOM KANTONSRAT AM) (\d{1,2}\. \w+ \d{4})", titelseite, re.I)
    fassung = (m.group(1).capitalize().replace("regierungsrates", "Regierungsrates").replace("kantonsrat", "Kantonsrat")
               + " " + m.group(2).title().replace(". ", ". ")) if m else ""
    daten = {
        "quelle": Path(quelle).name, "fassung": fassung.strip(), "einheit": "1000 Franken",
        "spalten": spalten, "erfolg": erfolg, "erfolg_namen": dict(ERFOLG), "invest": invest,
        "bilanz": bilanz, "bilanz_namen": dict(BILANZ), "nettoschuld1": nettoschuld,
        "kennzahlen": prozent, "steuerfuss": steuerfuss,
        "departemente": dep, "funktionen": funktionen, "funktionen_namen": funk_namen,
        "invest_dep": invest_dep, "sachanlagen": sachanlagen, "vk_5310": vk_5310,
        "felder": felder, "pruefung": fehler,
    }
    ziel.write_text(json.dumps(daten, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{quelle}: {fassung}")
    print(f"  Spalten: {', '.join(s['art'] + ' ' + str(s['jahr']) for s in spalten)}")
    print(f"  Gesamtergebnis: {erfolg['gesamt']}")
    print(f"  Nettoinvestitionen: {invest['netto']}; Eigenkapital: {bilanz['ek']}")
    print(f"  Aufgabenfelder: {len(felder)}; Funktionen: {len(funktionen)}; Departemente: {len(dep)}; "
          f"Vorhaben in 5.3.10: {len(vk_5310)}")
    print(f"  Selbstprüfung: {len(fehler)} Abweichungen")
    for f in fehler:
        print("   ", f)
    print(f"{ziel} geschrieben")
    return 1 if fehler else 0


def zahlenzeilen_mit_prozent(text: str) -> list[tuple[str, list[int]]]:
    """Zeilen «Name  R  B  B  Abw.  %»: vier Beträge und eine Prozentzahl."""
    aus = []
    for z in text.splitlines():
        m = re.match(rf"^\s*(.*?)\s+((?:(?:{ZAHL})\s+){{4}})(-?[\d.]+|-)\s*$", z)
        if m and m.group(1):
            aus.append((m.group(1).strip(), [zahl(x) for x in re.findall(ZAHL, m.group(2))]))
    return aus


if __name__ == "__main__":
    sys.exit(main())

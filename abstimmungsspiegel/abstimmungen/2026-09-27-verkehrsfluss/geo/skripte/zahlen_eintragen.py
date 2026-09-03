#!/usr/bin/env python3
"""Traegt die gerechneten Geozahlen in vorlage.json ein.

Aufruf aus der Projektwurzel:
    python3 abstimmungsspiegel/abstimmungen/2026-09-27-verkehrsfluss/geo/skripte/zahlen_eintragen.py

Liest  geo/02_aufbereitet/geltungsbereich.json   (geltungsbereich.py)
       geo/02_aufbereitet/haushalte.json         (haushalte.py)
Schreibt in vorlage.json:
       textkritik.stellen[1]  Tabellenfuss und Folge (Schnittmenge der beiden Netze)
       karte.anwohner         Tabelle Anwohner und Laermfassaden je Vorlage
       argumente contra-4     Punkte 1 und 2 von «fehlt», Kommentar der ersten kritischen Frage

Warum ein Skript: Die Zahlen aendern sich mit jedem Lauf der Geoskripte
(neuer Fahrplan, neuer Laermkataster). Von Hand nachgetragen veralten sie
unbemerkt; hier stehen die Saetze einmal, die Zahlen kommen aus den Dateien.
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

VORLAGE = Path(__file__).resolve().parent.parent.parent
FERTIG = VORLAGE / "geo" / "02_aufbereitet"
DATEI = VORLAGE / "vorlage.json"


def km(v) -> str:
    return f"{v:.1f}".replace(".", ",") + " km"


def z(n) -> str:
    return f"{int(n):,}".replace(",", " ")


def main() -> int:
    kz = json.loads((FERTIG / "geltungsbereich.json").read_text(encoding="utf-8"))
    hh = json.loads((FERTIG / "haushalte.json").read_text(encoding="utf-8"))
    i, g, e = hh["vorlagen"]["initiative"], hh["vorlagen"]["gegenvorschlag"], hh["vorlagen"]["eine"]
    d = json.loads(DATEI.read_text(encoding="utf-8"), object_pairs_hook=collections.OrderedDict)

    # ---- Textkritik, Stelle 2: die beiden Netze
    st = d["textkritik"]["stellen"][1]
    st["tabelle"]["fuss"] = (
        "Der Gegenvorschlag greift auf der ersten Zeile. Das Netz der Initiative, Kantonsstrassen "
        f"innerorts mit Busbetrieb, ist eine andere Menge: {km(kz['initiative_km'])}, davon "
        f"{km(kz['beide_km'])} auch im Gegenvorschlag, {km(kz['nur_initiative_km'])} nur in der Initiative "
        f"(siedlungsorientierte Strassen mit Bus). Umgekehrt erfasst der Gegenvorschlag "
        f"{km(kz['nur_gegenvorschlag_km'])} ohne Buslinie, die die Initiative nicht erfasst. "
        "Rechnung in der Karte «Selber nachschauen».")
    st["folge"] = (
        "1. Die beiden Vorlagen regeln nicht dasselbe Strassennetz.\n"
        f"2. Beide erfassen {km(kz['beide_km'])}; nur die Initiative {km(kz['nur_initiative_km'])}, "
        f"nur der Gegenvorschlag {km(kz['nur_gegenvorschlag_km'])}.\n"
        "3. Wer beide annimmt, entscheidet mit der Stichfrage auch darüber, welche Abgrenzung gilt.\n"
        "4. Keines der beiden Argumentarien erwähnt das.")

    # ---- Textkritik, Stelle 1: Umkreise aus karte.total (gemeindekarten.py)
    tot = d["karte"].get("total") or {}
    if tot.get("p100") is not None:
        st1 = d["textkritik"]["stellen"][0]
        zeilen = st1["folge"].split("\n")
        zeilen = [zl for zl in zeilen if not zl.startswith("2. ")]
        zeilen.insert(1, f"2. {tot['p100']:.0f} Prozent der betroffenen Strassen liegen innerhalb von 100 Metern "
                         f"einer Schule, eines Kindergartens oder eines Heims, {tot['p300']:.0f} Prozent innerhalb "
                         f"von 300 Metern, {tot['p500']:.0f} Prozent innerhalb von 500 Metern "
                         f"({d['karte'].get('anlagen_total', '')}).")
        st1["folge"] = "\n".join(zeilen)

    # ---- Karte: Anwohner je Vorlage
    def zeile(name, v):
        return collections.OrderedDict([
            ("vorlage", name), ("km", v["strassen_km"]), ("anwohner", v["anwohner"]),
            ("haushalte", v["haushalte"]), ("gebaeude_65", v["gebaeude_ueber_65"]),
            ("gebaeude_60", v["gebaeude_ueber_60"]), ("anwohner_65", v["anwohner_an_fassaden_ueber_65"])])
    d["karte"]["anwohner"] = collections.OrderedDict([
        ("einleitung", "Wer an den betroffenen Strassen wohnt, aus dem Hektarraster der "
                       "Bevölkerungsstatistik und dem Lärmkataster."),
        ("zeilen", [zeile("Initiative", i), zeile("Gegenvorschlag", g), zeile("mindestens eine", e)]),
        ("quelle", f"BFS STATPOP {hh['statpop_jahr']} (Einwohner je Hektare, Hektaren an einer betroffenen "
                   "Strasse); Lärmkataster Kanton Schaffhausen, Fassadenpunkte Tag, "
                   f"{hh['fassade_fang_m']:.0f} m; Grenzwerte LSV Anhang 3 (65 dB(A) ES III, 60 dB(A) ES II); "
                   f"{str(hh['personen_je_haushalt']).replace('.', ',')} Personen je Haushalt"),
    ])

    # ---- contra-4: die Zahl hinter «Tausende»
    a = next(x for x in d["argumente"] if x["id"] == "contra-4")
    rest = a["fehlt"].split("\n")
    rest = [r for r in rest if r.startswith("3. ")] or [
        "3. Die Reihenfolge der Massnahmen: Der Kanton setzt an verkehrsorientierten Strassen zuerst "
        "lärmarme Beläge ein. Sie bringen neu 6 bis 8 Dezibel, am Lebensende noch rund 3. Eine "
        "Temporeduktion bringt rund 3 Dezibel und kommt erst, wenn die Grenzwerte trotz Belag "
        "überschritten bleiben."]
    a["fehlt"] = (
        f"1. Die Zahl hinter «Tausende»: An den von der Initiative erfassten Strassen ({km(i['strassen_km'])}) "
        f"liegen nach dem kantonalen Lärmkataster {z(i['punkte_ueber_65'])} Fassadenpunkte an "
        f"{z(i['gebaeude_ueber_65'])} Gebäuden über 65 dB(A) am Tag, dem Immissionsgrenzwert der "
        f"Empfindlichkeitsstufe III; mit dem Grenzwert für reine Wohnzonen (60 dB(A), ES II) sind es "
        f"{z(i['gebaeude_ueber_60'])} Gebäude. Beim Gegenvorschlag ({km(g['strassen_km'])}): "
        f"{z(g['gebaeude_ueber_65'])} Gebäude über 65 dB(A), {z(g['gebaeude_ueber_60'])} über 60 dB(A).\n"
        f"2. Personen: In den Hektaren an den von der Initiative erfassten Strassen wohnen "
        f"{z(i['anwohner'])} Personen (STATPOP {hh['statpop_jahr']}), davon "
        f"{z(i['anwohner_an_fassaden_ueber_65'])} in Hektaren mit mindestens einer Fassade über 65 dB(A). "
        "Die Hektare zählt ganz, die Zahl ist darum eine Obergrenze. «Tausende» trifft damit für "
        "Fassaden und Personen zu.\n" + "\n".join(rest))
    a["kritische_fragen"][0]["kommentar"] = (
        f"«Tausende» ohne Zahl; eigene Rechnung: {z(i['gebaeude_ueber_65'])} Gebäude über 65 dB(A), "
        f"{z(i['anwohner_an_fassaden_ueber_65'])} Anwohner in diesen Hektaren")

    DATEI.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"eingetragen: Initiative {km(kz['initiative_km'])}, Gegenvorschlag {km(kz['gegenvorschlag_km'])}, "
          f"beide {km(kz['beide_km'])}; Anwohner {z(i['anwohner'])} / {z(g['anwohner'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Faerbt die Grafiken der Geoanalyse auf das Farbsystem des Dashboards um.

Aufruf aus der Projektwurzel:
    python3 scripts/grafiken_umfaerben.py

Liest  geo/00_uebergabe_michael/grafiken/*.svg  und  .../karten_gemeinden/*.svg
Schreibt nach  grafiken/  und  grafiken/gemeinden/
Die Originale bleiben unveraendert.

Warum ueberhaupt: docs/DESIGN_entscheide.md, Abschnitt 1. Gruen ist die SVP, Rot die SP.
Eine Ampelskala in einer neutralen Abstimmungshilfe faerbt zudem eine Wertung ein
("rot = schlimm"), die dort nicht hingehoert. Rangfolgen werden deshalb zu einer
Graustufenrampe; die Zahl steht in diesen Grafiken ohnehin am Balken, es geht also
keine Information verloren.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent

# ------------------------------------------------------------------ Zuordnung
# Belegt durch eine Auszaehlung aller Hexwerte in den 17 Grafiken.

NEUTRAL = {
    "#f5f4f1": "#f7f8fa",   # Blattgrund      -> --flaeche
    "#f4f3ef": "#f7f8fa",   # Blattgrund Variante
    "#0b0b0b": "#12161c",   # Titel           -> --text
    "#2b2b2b": "#12161c",
    "#52514e": "#5a626d",   # Fliesstext      -> --text-leise
    "#8a8881": "#8b93a1",   # leise
    "#9a988f": "#8b93a1",
    "#e1e0d9": "#e2e6eb",   # Haarlinie       -> --linie
    "#e7e5df": "#e2e6eb",
    "#c9c8c2": "#d5dae1",
    "#c9c7c0": "#d5dae1",
}

# Der blaue Akzent der Kopfleiste. Die Oberflaeche hat laut Design-Entscheiden
# keine eigene Akzentfarbe, aktive Zustaende laufen ueber Tiefe und Schriftfarbe.
AKZENT = {
    "#2a78d6": "#3c4652",
    "#1c5cab": "#2b3440",
    "#dfeaf7": "#e2e6eb",
}

# Ampel: hoch / mittel / gering -> Graustufenrampe, dunkel = viel.
AMPEL = {
    "#d03b3b": "#1f2833",   # rot    -> sehr dunkel
    "#c0392b": "#1f2833",
    "#eb6834": "#4a5563",   # orange -> mittel
    "#c9871c": "#6e7783",
    "#b84a20": "#4a5563",
    "#0ca30c": "#a9b1be",   # gruen  -> hell
    "#158a66": "#8b93a1",
    "#fdf3c9": "#eceff3",
    "#dce9dc": "#eceff3",
    "#d6efe6": "#eceff3",
    "#dbe9fb": "#e2e6eb",
    "#eef1f5": "#f7f8fa",
    "#4a3aa7": "#5a626d",
}

# Sequenzielle Gruenskala in G12, G16, G17 -> Graphitrampe, gleiche Reihenfolge.
SKALA = {
    "#08492f": "#1f2833",
    "#0f7a54": "#3c4652",
    "#2f9e75": "#5a626d",
    "#63c39b": "#8b93a1",
    "#9cbcae": "#b9c2ce",
    "#d2e2da": "#dfe3e8",
    "#cddfd7": "#e2e6eb",
}

# Flaechen der beiden Uebersichtskarten. Bleiben neutral, nur leicht angeglichen.
KARTE = {
    "#c2c1b9": "#d5dae1",
    "#c7c6bf": "#dfe3e8",
    "#c3cdc6": "#d5dae1",
    "#dedcd4": "#e8ebef",
    "#ece9e2": "#f2f4f7",
    "#eceae3": "#f2f4f7",
    "#0c6f4a": "#2b3440",
    "#46a37c": "#6e7783",
    "#a4c3b4": "#b9c2ce",
    "#e0a92a": "#8b93a1",
}

ZUORDNUNG: dict[str, str] = {**NEUTRAL, **AKZENT, **AMPEL, **SKALA, **KARTE}

# Kategoriale Farben der Gemeindekarten. Vier Nutzungsgruppen, die sich
# unterscheiden muessen. Offen, siehe Hinweis am Ende des Laufs.
KATEGORIAL = {
    "#1b9e77", "#2166ac", "#6a51a3", "#d95f0e", "#e6194b", "#f4a6ae",
}


def faerben(text: str) -> tuple[str, dict[str, int]]:
    zaehler: dict[str, int] = {}

    def ersetz(m):
        alt = m.group(0).lower()
        neu = ZUORDNUNG.get(alt)
        if neu is None:
            return m.group(0)
        zaehler[alt] = zaehler.get(alt, 0) + 1
        return neu

    return re.sub(r"#[0-9a-fA-F]{6}", ersetz, text), zaehler


def lauf(quelle: Path, ziel: Path) -> tuple[int, set[str]]:
    ziel.mkdir(parents=True, exist_ok=True)
    offen: set[str] = set()
    n = 0
    for f in sorted(quelle.glob("*.svg")):
        text = f.read_text(encoding="utf-8")
        neu, _ = faerben(text)
        (ziel / f.name).write_text(neu, encoding="utf-8")
        for c in set(re.findall(r"#[0-9a-fA-F]{6}", neu)):
            c = c.lower()
            if c in KATEGORIAL or c in ZUORDNUNG:
                if c in KATEGORIAL:
                    offen.add(c)
        n += 1
    # PNG-Fassungen unveraendert mitkopieren, damit der Ordner vollstaendig ist
    for f in quelle.glob("*.png"):
        shutil.copy2(f, ziel / f.name)
    return n, offen


def main() -> None:
    a, offen_a = lauf(WURZEL / "geo" / "00_uebergabe_michael" / "grafiken", WURZEL / "grafiken")
    b, offen_b = lauf(WURZEL / "geo" / "00_uebergabe_michael" / "grafiken" / "gemeinden",
                      WURZEL / "grafiken" / "gemeinden")
    c, offen_c = lauf(WURZEL / "geo" / "00_uebergabe_michael" / "karten_gemeinden",
                      WURZEL / "grafiken" / "gemeinden")
    print(f"umgefaerbt: {a} Grafiken, {b} Gemeindegrafiken, {c} Gemeindekarten")
    offen = offen_a | offen_b | offen_c
    if offen:
        print("\nNoch offen, kategoriale Farben ohne Entsprechung im Farbsystem:")
        for c in sorted(offen):
            print(f"  {c}")
        print("Diese kodieren die vier Nutzungsgruppen der Gemeindekarten "
              "(Schule, Kindergarten, Heim, weitere) und brauchen einen Entscheid.")


if __name__ == "__main__":
    main()

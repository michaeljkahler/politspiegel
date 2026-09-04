"""Testphasen-Band, einmal fuer alle Seiten des Politspiegels.

Ein diagonales Band in einer Ecke, auf jeder Seite sichtbar, solange in
politspiegel/politspiegel.json «testphase» auf true steht. Uebersicht,
Abstimmungsliste, Abstimmungsseiten und Kantonsratsspiegel binden denselben
Block ein; die Ecke ist je Seite waehlbar, damit das Band keinen Knopf
verdeckt (Abstimmungsseiten haben unten links den Knopf fuer Social Media).

Geometrie: der Mittelpunkt des Bandes liegt auf der Winkelhalbierenden der
Ecke, --tp-mitte Pixel vom Eck entfernt. Sichtbar ist die Sehne zwischen den
beiden Bildraendern, doppelt so lang wie --tp-mitte; darum muss --tp-mitte gut
die halbe Textbreite betragen. Der Kasten (--tp-eck) ist groesser als die
Sehne, damit das Band erst am Bildrand endet. Fuer Bildschirmleser bleibt das
Band verborgen und wird in ganzen Worten angesagt.
"""

from __future__ import annotations

import json
from pathlib import Path

QUELLE = Path(__file__).resolve().parent / "politspiegel.json"


def aktiv() -> bool:
    try:
        return bool(json.loads(QUELLE.read_text(encoding="utf-8")).get("testphase"))
    except Exception:
        return False


def testphase_html(ecke: str = "oben-rechts") -> str:
    """ecke: «oben-rechts» oder «unten-links»."""
    if not aktiv():
        return ""
    return (f'<div class="testphase tp-{ecke}" aria-hidden="true"><span>Testphase</span></div>'
            '<p class="testphase-text">Diese Seite ist in der Testphase: die Daten werden noch geprüft. '
            'Fehler bitte an die Adresse im Impressum.</p>')


TESTPHASE_CSS = """
:root{--tp-eck:168px;--tp-mitte:62px}
.testphase{position:fixed;z-index:900;width:var(--tp-eck);height:var(--tp-eck);overflow:hidden;pointer-events:none}
.testphase span{position:absolute;display:block;width:300px;padding:5px 0;background:#C62828;color:#FFFFFF;
  font-family:Archivo,"Public Sans","Helvetica Neue",Arial,sans-serif;font-size:12.5px;font-weight:650;
  letter-spacing:.09em;text-transform:uppercase;text-align:center;box-shadow:0 1px 10px rgba(17,24,32,.28);
  transform-origin:center}
.tp-unten-links{bottom:0;left:0}
.tp-unten-links span{left:0;bottom:0;transform:translate(calc(-50% + var(--tp-mitte)),calc(50% - var(--tp-mitte))) rotate(45deg)}
.tp-oben-rechts{top:0;right:0}
.tp-oben-rechts span{right:0;top:0;transform:translate(calc(50% - var(--tp-mitte)),calc(-50% + var(--tp-mitte))) rotate(45deg)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .testphase span{background:#E04B4B;color:#1A0808}}
:root[data-theme="dark"] .testphase span{background:#E04B4B;color:#1A0808}
@media (max-width:640px){:root{--tp-eck:108px;--tp-mitte:40px}.testphase span{font-size:9px;padding:3px 0;letter-spacing:.04em}}
.testphase-text{position:absolute;width:1px;height:1px;margin:-1px;padding:0;border:0;overflow:hidden;white-space:nowrap;clip:rect(0 0 0 0);clip-path:inset(50%)}
@media print{.testphase{display:none}}
"""

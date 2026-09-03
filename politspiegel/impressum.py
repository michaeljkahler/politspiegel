"""Impressum, einmal fuer alle Seiten des Politspiegels.

Gelesen aus politspiegel/politspiegel.json («impressum»). Uebersicht,
Abstimmungsliste und jede Abstimmungsseite binden denselben Block ein; der
Kantonsratsspiegel traegt dieselben Angaben in seinem Fuss (dashboard.js).

Die Mailadresse steht nicht im Klartext im HTML, sondern wird von einem
Dreizeiler zusammengesetzt; wer ohne Skript liest, sieht sie mit «(at)».
"""

from __future__ import annotations

import html
import json
from pathlib import Path

QUELLE = Path(__file__).resolve().parent / "politspiegel.json"


def impressum_html() -> str:
    d = json.loads(QUELLE.read_text(encoding="utf-8")).get("impressum") or {}
    if not d:
        return ""
    e = lambda s: html.escape(str(s), quote=True)
    u, dom = (d.get("mail") or ["", ""])[:2]
    mail = (f'<span class="imp-mail" data-u="{e(u)}" data-d="{e(dom)}">{e(u)} (at) {e(dom)}</span>'
            if u and dom else "")
    return (f'<div class="impressum" id="impressum">'
            f'<p><b>Impressum.</b> Verantwortlich für den Inhalt: {e(d.get("verantwortlich", ""))}'
            f'{", " + mail if mail else ""}. {e(d.get("text", ""))}</p>'
            + (f'<p><b>Datenschutz.</b> {e(d.get("datenschutz", ""))}</p>' if d.get("datenschutz") else "")
            + '</div>'
            '<script>document.querySelectorAll(".imp-mail").forEach(function(s){'
            'var a=s.dataset.u+"@"+s.dataset.d;s.innerHTML=\'<a href="mailto:\'+a+\'">\'+a+"</a>";});</script>')


IMPRESSUM_CSS = """
.impressum{margin-top:18px;padding-top:16px;border-top:1px solid var(--linie);font-size:13px;color:var(--text-leise)}
.impressum p{margin:0 0 8px} .impressum p:last-child{margin:0}
.impressum b{color:var(--text)} .impressum a{color:inherit}
"""

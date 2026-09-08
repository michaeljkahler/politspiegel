"""Verweise auf die eigenen Social-Media-Konten, einmal für alle Seiten.

Gelesen aus politspiegel/politspiegel.json («social»). Übersicht,
Abstimmungsliste und jede Abstimmungsseite binden denselben Block ein; der
Kantonsratsspiegel trägt dieselbe Reihe in seinem Fuss (dashboard.js, Funktion
sozialHtml).

Die Zeichen sind als SVG in die Seite geschrieben, nicht von einem fremden
Server geladen. Sonst würde beim Aufruf der Seite eine Verbindung zu Meta,
Google oder ByteDance aufgebaut, und die Zusage «diese Seite sendet nichts»
wäre hinfällig. Aus demselben Grund sind es Verweise und keine eingebetteten
Feeds.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

QUELLE = Path(__file__).resolve().parent / "politspiegel.json"

# Wortmarken als Pfad in einem 24er-Raster, einfarbig (currentColor).
ZEICHEN = {
    "instagram": ('<rect x="2.6" y="2.6" width="18.8" height="18.8" rx="5.4" fill="none" '
                  'stroke="currentColor" stroke-width="1.9"/>'
                  '<circle cx="12" cy="12" r="4.3" fill="none" stroke="currentColor" stroke-width="1.9"/>'
                  '<circle cx="17.3" cy="6.7" r="1.3" fill="currentColor"/>'),
    "facebook": ('<path d="M13.6 21.5v-8.2h2.8l.42-3.2h-3.22V8.03c0-.93.26-1.56 1.6-1.56h1.7V3.6'
                 'a22 22 0 0 0-2.5-.13c-2.47 0-4.16 1.5-4.16 4.27v2.38H7.4v3.2h2.84v8.2z" '
                 'fill="currentColor"/>'),
    "youtube": ('<rect x="1.6" y="4.9" width="20.8" height="14.2" rx="4.6" fill="none" stroke="currentColor" stroke-width="1.9"/><path d="M10.2 8.9 15.9 12l-5.7 3.1z" fill="currentColor"/>'),
    "tiktok": ('<path d="M16.1 2.6h-3.2v13.05a2.62 2.62 0 1 1-2.05-2.56v-3.24a5.83 5.83 0 1 0 5.25 5.8V8.9'
               'a6.5 6.5 0 0 0 3.9 1.27V6.95a3.34 3.34 0 0 1-2.5-1.05 3.4 3.4 0 0 1-1.4-2.6z" '
               'fill="currentColor"/>'),
}


def social_html(ueberschrift: str = "Politspiegel folgen") -> str:
    d = json.loads(QUELLE.read_text(encoding="utf-8")).get("social") or {}
    kanaele = d.get("kanaele") or []
    if not kanaele:
        return ""
    e = lambda s: html.escape(str(s), quote=True)
    links = "".join(
        f'<a class="soz-link" href="{e(k["url"])}" target="_blank" rel="noopener me" '
        f'title="{e(k["name"])}" aria-label="{e(k["name"])}">'
        f'<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" focusable="false">'
        f'{ZEICHEN.get(k["kanal"], "")}</svg>'
        f'<span>{e(k["label"])}</span></a>'
        for k in kanaele if k.get("kanal") in ZEICHEN and k.get("url")
    )
    handle = e(d.get("handle", ""))
    return (f'<div class="soz">'
            f'<p class="soz-titel">{e(ueberschrift)}'
            + (f' <span class="soz-handle">{handle}</span>' if handle else "")
            + f'</p><div class="soz-reihe">{links}</div></div>')


SOCIAL_CSS = """
.soz{margin-top:18px;padding-top:16px;border-top:1px solid var(--linie)}
.soz-titel{margin:0 0 10px;font-size:13px;color:var(--text-leise)}
.soz-handle{color:var(--text);font-weight:600}
.soz-reihe{display:flex;flex-wrap:wrap;gap:8px}
.soz .soz-link{display:inline-flex;align-items:center;gap:8px;padding:7px 13px 7px 11px;
  border:1px solid var(--linie);border-radius:999px;font-size:13.5px;font-weight:600;
  color:var(--text);text-decoration:none;line-height:1}
.soz-link:hover{border-color:var(--text);background:var(--flaeche)}
.soz-link svg{flex:none;color:var(--text-leise)}
.soz-link:hover svg{color:var(--text)}
@media (max-width:520px){.soz-link span{display:none}.soz-link{padding:9px}}
"""

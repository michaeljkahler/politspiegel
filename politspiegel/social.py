"""Verweise auf die eigenen Social-Media-Konten, einmal für alle Seiten.

Gelesen aus politspiegel/politspiegel.json («social»). Übersicht,
Abstimmungsliste und jede Abstimmungsseite binden denselben Block ein; der
Kantonsratsspiegel trägt dieselbe Reihe in seiner Kopfleiste (build3.py).

Die Leiste liegt fest oben links über dem Inhalt und bleibt beim Blättern
stehen. Links, weil oben rechts das Testphasen-Band sitzt. Sie ist schmal
gehalten und weicht auf kleinen Bildschirmen auf die blossen Zeichen zurück,
damit sie den Seitentitel nicht verdeckt.

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


def social_html(ueberschrift: str = "Folgen") -> str:
    """Feste Leiste oben links, auf jeder Seite gleich."""
    d = json.loads(QUELLE.read_text(encoding="utf-8")).get("social") or {}
    kanaele = d.get("kanaele") or []
    if not kanaele:
        return ""
    e = lambda s: html.escape(str(s), quote=True)
    links = "".join(
        f'<a class="soz-link" href="{e(k["url"])}" target="_blank" rel="noopener me" '
        f'title="{e(k["name"])}" aria-label="{e(k["name"])}">'
        f'<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" focusable="false">'
        f'{ZEICHEN.get(k["kanal"], "")}</svg>'
        f'<span>{e(k["label"])}</span></a>'
        for k in kanaele if k.get("kanal") in ZEICHEN and k.get("url")
    )
    return (f'<nav class="soz" aria-label="Politspiegel auf Social Media">'
            f'<span class="soz-titel">{e(ueberschrift)}</span>{links}</nav>')


SOCIAL_CSS = """
.soz{position:fixed;z-index:880;top:12px;left:12px;display:flex;align-items:center;gap:6px;
  padding:6px 10px 6px 12px;border:1px solid var(--linie);border-radius:999px;
  background:color-mix(in srgb, var(--grund) 88%, transparent);backdrop-filter:blur(10px);
  box-shadow:0 2px 12px rgba(17,24,32,.10)}
.soz-titel{font-size:12.5px;font-weight:600;color:var(--text-leise);letter-spacing:.02em;padding-right:2px}
.soz .soz-link{display:inline-flex;align-items:center;gap:7px;padding:6px 11px 6px 9px;
  border:1px solid transparent;border-radius:999px;font-size:13px;font-weight:600;
  color:var(--text);text-decoration:none;line-height:1}
.soz .soz-link:hover,.soz .soz-link:focus-visible{border-color:var(--linie);background:var(--flaeche)}
.soz-link svg{flex:none;color:var(--text-leise)}
.soz-link:hover svg,.soz-link:focus-visible svg{color:var(--text)}
/* Die Leiste liegt ueber dem Seitenkopf: der Kopf rueckt darunter weg. */
.soz ~ .rahmen .kopf,.soz ~ .wrap .kopf{padding-top:8px}
@media (max-width:1100px){.soz-titel{display:none}.soz .soz-link span{display:none}
  .soz .soz-link{padding:8px}.soz{padding:5px 6px;gap:2px}}
@media (max-width:640px){.soz{top:8px;left:8px}}
@media print{.soz{display:none}}
"""

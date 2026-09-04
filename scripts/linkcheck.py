#!/usr/bin/env python3
"""Alle Verweise des Politspiegels pruefen.

Aufruf aus der Projektwurzel:
    python3 scripts/linkcheck.py            # pruefen, Bericht, data/link_status.json schreiben
    python3 scripts/linkcheck.py --offline  # nur die Verweise innerhalb von site/ pruefen

Geprueft wird
1. jede Protokolladresse (pu) und Sitzungsseite in data/all_sessions.json und
   jede Profiladresse in data/mitglieder.json, per HEAD (bei 405/403 per GET),
2. jeder relative Verweis in site/ (href ohne http/mailto) auf eine vorhandene Datei,
3. jeder Sprung aus dem Abstimmungsspiegel in den Kantonsratsspiegel
   (kantonsrat/#s=<Sitzung>&nr=<Nr>) auf eine vorhandene Abstimmung.

Ergebnis: data/link_status.json mit {url: {"status": 200, "typ": "application/pdf",
"geprueft": "2026-09-04"}}. build3.py liest die Datei und ersetzt Protokollverweise,
die nicht mehr erreichbar sind, durch die Sitzungsseite auf sh.ch (Feld pf=1).
Der Abbruchcode ist 1, sobald ein Verweis fehlt; so laesst sich das Skript
vor jedem Veroeffentlichen laufen lassen.
"""

from __future__ import annotations

import concurrent.futures
import datetime as dt
import glob
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITE = ROOT / "site"
STATUS = DATA / "link_status.json"
UA = {"User-Agent": "Mozilla/5.0 (Politspiegel Linkpruefung)"}


def pruefen(url: str) -> dict:
    for methode in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=methode, headers=UA)
            with urllib.request.urlopen(req, timeout=25) as r:
                return {"status": r.status, "typ": r.headers.get("Content-Type", "").split(";")[0]}
        except urllib.error.HTTPError as e:
            if methode == "HEAD" and e.code in (403, 405):
                continue
            return {"status": e.code, "typ": ""}
        except Exception as e:  # Netz, Zeitueberschreitung
            return {"status": 0, "typ": type(e).__name__}
    return {"status": 0, "typ": ""}


def externe_adressen() -> dict[str, list[str]]:
    urls: dict[str, list[str]] = {}
    d = json.loads((DATA / "all_sessions.json").read_text(encoding="utf-8"))
    for s in d["sessions"]:
        for p in s.get("protokolle") or []:
            urls.setdefault(p["url"], []).append("Protokoll " + s["sitzung"])
        if s.get("url"):
            urls.setdefault(s["url"], []).append("Sitzungsseite " + s["sitzung"])
    mp = DATA / "mitglieder.json"
    if mp.exists():
        m = json.loads(mp.read_text(encoding="utf-8"))
        liste = m if isinstance(m, list) else m.get("mitglieder") or m.get("liste") or []
        for x in liste:
            u = x.get("url") or x.get("profil")
            if u:
                urls.setdefault(u, []).append("Profil " + (x.get("nachname") or x.get("name") or ""))
    return urls


def relative_verweise() -> list[str]:
    fehler = []
    for f in glob.glob(str(SITE / "**" / "*.html"), recursive=True):
        t = Path(f).read_text(encoding="utf-8")
        # Nur echtes HTML, keine JS-Vorlagen ("' + esc(" ...)
        for href in set(re.findall(r'href="([^"#\']+)"', t)):
            if href.startswith(("http", "mailto", "data:", "javascript")):
                continue
            ziel = os.path.normpath(os.path.join(os.path.dirname(f), urllib.parse.unquote(href)))
            if os.path.isdir(ziel):
                ziel = os.path.join(ziel, "index.html")
            if not os.path.exists(ziel):
                fehler.append(f"{os.path.relpath(f, ROOT)}: {href}")
    return fehler


def ratssprünge() -> list[str]:
    fehler = []
    kr = SITE / "kantonsrat" / "index.html"
    if not kr.exists():
        return ["site/kantonsrat/index.html fehlt"]
    m = re.search(r'<script id="daten" type="application/json">(.*?)</script>', kr.read_text(encoding="utf-8"), re.S)
    D = json.loads(m.group(1))
    paare = {(s["s"], str(v["nr"])) for s in D["sessions"] for v in s["v"]}
    for f in glob.glob(str(SITE / "abstimmung" / "*" / "index.html")):
        t = Path(f).read_text(encoding="utf-8")
        for s, nr in re.findall(r'href="[^"]*kantonsrat/#s=([^&"]+)&(?:amp;)?nr=([^"]+)"', t):
            paar = (urllib.parse.unquote(html.unescape(s)), html.unescape(nr))
            if paar not in paare:
                fehler.append(f"{os.path.relpath(f, ROOT)}: Sitzung «{paar[0]}» Nr. {paar[1]} nicht im Kantonsratsspiegel")
    return fehler


def main() -> int:
    offline = "--offline" in sys.argv
    fehler = 0
    rel = relative_verweise()
    print(f"Relative Verweise in site/: {len(rel)} fehlend")
    for x in rel:
        print("  ", x)
    fehler += len(rel)
    spr = ratssprünge()
    print(f"Sprünge Abstimmungsspiegel → Kantonsratsspiegel: {len(spr)} ohne Ziel")
    for x in spr:
        print("  ", x)
    fehler += len(spr)
    if offline:
        return 1 if fehler else 0

    urls = externe_adressen()
    print(f"Externe Adressen: {len(urls)}")
    with concurrent.futures.ThreadPoolExecutor(16) as ex:
        ergebnisse = dict(zip(urls, ex.map(pruefen, urls)))
    heute = dt.date.today().isoformat()
    status = {}
    if STATUS.exists():
        status = json.loads(STATUS.read_text(encoding="utf-8"))
    for u, r in ergebnisse.items():
        status[u] = {**r, "geprueft": heute}
        if r["status"] != 200:
            fehler += 1
            print(f"  {r['status']:>4} {u}  ({'; '.join(urls[u][:2])})")
    STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    gut = sum(1 for r in ergebnisse.values() if r["status"] == 200)
    print(f"geschrieben: {STATUS.relative_to(ROOT)}; {gut} erreichbar, {len(ergebnisse) - gut} nicht")
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())

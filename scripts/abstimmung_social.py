#!/usr/bin/env python3
"""
Social-Media-Bilder des Abstimmungsspiegels als PNG
===================================================
Die Motive (Vorlage, Gegenüberstellung, Aussagenpaare, Kantonsrat, Karussell
je Argument) zeichnet die Seite selbst im Browser auf eine Leinwand
(abstimmungsspiegel/bausteine/teilen.py). Dieses Skript öffnet die gebaute
Seite in einem unsichtbaren Chromium, lässt jedes Motiv zeichnen und speichert
die Leinwand als PNG. So gibt es genau ein Zeichenprogramm, und Bild und Seite
bleiben deckungsgleich.

Ausgabe: site/social/abstimmung/<slug>/
    vorlage.png, gegen.png, paar-1.png …, kantonsrat.png,
    karussell-<argument-id>-folie-N.png, posts.json (Serie mit Texten)

Ausführen:
    bash scripts/browser_einrichten.sh              # einmal je Sandbox
    python3 scripts/abstimmung_social.py 2026-09-27-verkehrsfluss
    python3 scripts/abstimmung_social.py 2026-09-27-verkehrsfluss --nur vorlage,kantonsrat,gegen,paar
"""
import argparse
import base64
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
BASIS_URL = "https://michaeljkahler.github.io/politspiegel/"
MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
          "September", "Oktober", "November", "Dezember"]


def datum_lang(iso):
    j, m, t = iso.split("-")
    return f"{int(t)}. {MONATE[int(m) - 1]} {j}"


def browser_umgebung():
    libs = Path.home() / "libs"
    if libs.exists():
        pfade = [str(libs / "usr/lib/x86_64-linux-gnu"), str(libs / "lib/x86_64-linux-gnu")]
        os.environ["LD_LIBRARY_PATH"] = ":".join(pfade + [os.environ.get("LD_LIBRARY_PATH", "")])


def rendern(slug, nur, ordner):
    from playwright.sync_api import sync_playwright
    seite = SITE / "abstimmung" / slug / "index.html"
    if not seite.exists():
        raise SystemExit(f"{seite} fehlt. Zuerst die Abstimmungsseite bauen.")
    ordner.mkdir(parents=True, exist_ok=True)
    bilder = []
    # Die Seite kommt von einem lokalen Webserver, nicht per file://: sonst
    # gelten die eingebundenen SVG-Grafiken als fremde Herkunft, und der
    # Browser verweigert das Auslesen der Leinwand («tainted canvas»).
    import http.server, socketserver, threading, functools
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(SITE))
    handler.log_message = lambda *a, **k: None
    srv = socketserver.TCPServer(("127.0.0.1", 0), handler)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1400, "height": 1000}, color_scheme="light")
        pg.goto(f"http://127.0.0.1:{port}/abstimmung/{slug}/index.html")
        pg.wait_for_load_state("networkidle")
        pg.evaluate("document.fonts.ready")
        pg.click("#bildStart")
        pg.wait_for_selector("#bildCanvas")
        motive = pg.evaluate("Array.from(document.querySelectorAll('#bildMotiv option')).map(o => o.value)")

        def zeichnen_und_speichern(name):
            pg.wait_for_function("window.bildStufe !== undefined", timeout=20000)
            pg.wait_for_timeout(150)
            daten = pg.evaluate("document.querySelector('#bildCanvas').toDataURL('image/png')")
            stufe = pg.evaluate("window.bildStufe")
            ueberlauf = pg.evaluate("window.bildUeberlauf")
            pfad = ordner / f"{name}.png"
            pfad.write_bytes(base64.b64decode(daten.split(",", 1)[1]))
            bilder.append({"datei": pfad.name, "motiv": name, "stufe": stufe, "ueberlauf": bool(ueberlauf)})
            print(f"  {pfad.name}  Massstab {stufe}" + ("  ÜBERLAUF" if ueberlauf else ""))

        for k in motive:
            art = k.split(":")[0]
            if nur and art not in nur:
                continue
            pg.evaluate("window.bildStufe = undefined")
            pg.select_option("#bildMotiv", k)
            name = k.replace(":", "-")
            if art == "karussell":
                n = pg.evaluate("document.querySelectorAll('#bildFolie option').length")
                for i in range(n):
                    pg.evaluate("window.bildStufe = undefined")
                    pg.select_option("#bildFolie", str(i))
                    zeichnen_und_speichern(f"{name}-folie-{i + 1}")
            else:
                zeichnen_und_speichern(name)
        b.close()
    srv.shutdown()
    return bilder


def serie(slug, daten, bilder, ordner):
    """Plan der Beiträge bis zum Abstimmungssonntag, mit Texten in Listenform."""
    v = daten["vorlage"]
    url = BASIS_URL + "abstimmung/" + slug + "/"
    url_ordner = BASIS_URL + "social/abstimmung/" + slug + "/"
    datum = datum_lang(v["abstimmung"])
    tag = date.fromisoformat(v["abstimmung"])
    heute = date.today()
    vorhanden = {b["motiv"] for b in bilder}
    name = {s: v["seiten"][s].get("komitee", v["seiten"][s]["name"]) for s in ("pro", "contra")}
    hashtag = "#" + "".join(ch for ch in v["titel"] if ch.isalnum())
    fuss = f"\n\nAlle Argumente und die Prüfung: {url}\n\n#Schaffhausen #Abstimmung {hashtag} #Politspiegel"
    args = daten["argumente"]
    pro = [a for a in args if a["seite"] == "pro"]
    con = [a for a in args if a["seite"] == "contra"]
    posts = []

    def post(motive, text, wann, art="karussell"):
        medien = [url_ordner + m + ".png" for m in motive if m in vorhanden]
        if not medien:
            return
        posts.append({"art": art, "termin": wann.isoformat() + "T12:00", "text": text,
                      "media": medien, "providers": ["instagram", "facebook", "tiktok"],
                      "instagram": {"type": "POST"}, "facebook": {"type": "POST"},
                      "tiktok": {"privacyOption": "PUBLIC_TO_EVERYONE", "photoCoverIndex": 0}})

    # Termine rückwärts vom Abstimmungssonntag, frühestens morgen.
    def t(tage_vorher):
        return max(tag - timedelta(days=tage_vorher), heute + timedelta(days=1))

    post(["vorlage"],
         f"{v['ebene']}, Abstimmung vom {datum}: {v['titel']}.\n\n"
         f"1. Worum es geht: {v['worum_geht_es']}\n"
         f"2. Bei einem Ja: {v['bei_ja']}\n"
         f"3. Bei einem Nein: {v['bei_nein']}" + fuss, t(22))
    kr = daten.get("kantonsrat") or {}
    if "kantonsrat" in vorhanden:
        import re
        zeilen = [f"{i}. {(a.get('details') or a.get('titel', '')).rstrip('.')}: {a.get('ja')} Ja, {a.get('nein')} Nein"
                  for i, a in enumerate(kr.get("abstimmungen", []), 1)]
        m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", kr.get("sitzung") or "")
        wann = f", Sitzung vom {datum_lang(f'{m.group(3)}-{m.group(2)}-{m.group(1)}')}" if m else ""
        post(["kantonsrat"],
             f"{v['titel']}: Wie der Kantonsrat Schaffhausen gestimmt hat{wann}. "
             "Namentliche Abstimmungen, gezählt aus dem Wortprotokoll.\n\n"
             + "\n".join(zeilen) + fuss, t(19))
    def punkte(a):
        if a.get("typ") == "wertung":
            return "Werturteil, ohne Note"
        pr = a.get("pruefung") or {}
        werte = [x for x in pr.values() if x is not None]
        return f"{sum(werte)} von {4 * len(werte)} Punkten für den Beleg"

    n_paare = min(len(pro), len(con))
    for i in range(n_paare):
        a, c = pro[i], con[i]
        post([f"paar-{i}"],
             f"{v['titel']}, Aussagenpaar {i + 1} von {n_paare}.\n\n"
             f"1. {name['pro']}: «{a['aussage']}» ({punkte(a)})\n"
             f"2. {name['contra']}: «{c['aussage']}» ({punkte(c)})\n\n"
             "Geprüft wird der Beleg jeder Aussage nach fünf Achsen (Quellenlage, Zahlenfestigkeit, "
             "Ursachennachweis, Reichweite, Übertragbarkeit), nicht ob sie richtig ist. "
             "Begründung je Achse auf der Seite." + fuss, t(16 - 2 * i))
    post(["gegen"],
         f"{v['titel']}: Wie gut sind die Argumente belegt?\n\n"
         "1. Mittelwert je Achse über die geprüften Aussagen, 0 bis 4 Punkte.\n"
         "2. Gemessen wird der Beleg, nicht die Richtigkeit.\n"
         "3. Werturteile sind ausgenommen." + fuss, t(6))
    # Karussells zu Argumenten mit eigener Auswertung, eines je Seite
    for seite, liste in (("pro", pro), ("contra", con)):
        mit = [a for a in liste if any(g.get("quelle", "").lower().startswith("eigene")
                                       for g in (a.get("grafiken") or ([a["grafik"]] if a.get("grafik") else [])))]
        if not mit:
            continue
        a = mit[0]
        folien = sorted(b["motiv"] for b in bilder if b["motiv"].startswith(f"karussell-{a['id']}-folie-"))
        folien.sort(key=lambda s: int(s.rsplit("-", 1)[1]))
        post(folien[:10],
             f"{v['titel']}: eine Aussage von {name[seite]} im Detail.\n\n"
             f"«{a['aussage']}»\n\n"
             "1. Was zutrifft und was fehlt, mit eigener Auswertung.\n"
             "2. Die letzte Folie zeigt die Aussage der Gegenseite mit gleicher Nummer." + fuss,
             t(4 if seite == "pro" else 3))
    post(["vorlage"],
         f"Am Sonntag, {datum}: {v['titel']}.\n\n"
         "1. Alle Argumente beider Seiten, geprüft nach fünf Achsen.\n"
         "2. Wie der Kantonsrat gestimmt hat.\n"
         "3. Eigene Auswertungen und Karten." + fuss, t(2))

    (ordner / "posts.json").write_text(json.dumps({
        "slug": slug, "vorlage": v["titel"], "abstimmung": v["abstimmung"], "status": "entwurf",
        "bilder": bilder, "posts": posts}, ensure_ascii=False, indent=1), encoding="utf-8")
    return posts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--nur", help="Motivarten, kommagetrennt: vorlage,gegen,paar,kantonsrat,karussell")
    a = ap.parse_args()
    browser_umgebung()
    ordner = SITE / "social" / "abstimmung" / a.slug
    nur = set(a.nur.split(",")) if a.nur else None
    print(f"{a.slug}: Motive zeichnen …")
    bilder = rendern(a.slug, nur, ordner)
    # Bei --nur bleiben die übrigen Motive aus einem früheren Lauf im Plan.
    neu = {b["motiv"] for b in bilder}
    for pfad in sorted(ordner.glob("*.png")):
        if pfad.stem not in neu:
            bilder.append({"datei": pfad.name, "motiv": pfad.stem, "stufe": None, "ueberlauf": False})
    daten = json.loads((ROOT / "abstimmungsspiegel" / "abstimmungen" / a.slug / "vorlage.json")
                       .read_text(encoding="utf-8"))
    # Kantonsratsdaten liegen in den Bilddaten der Seite, nicht in vorlage.json
    seite = (SITE / "abstimmung" / a.slug / "index.html").read_text(encoding="utf-8")
    m = seite.find('id="bild-daten"')
    if m > 0:
        s = seite.find(">", m) + 1
        e = seite.find("</script>", s)
        daten["kantonsrat"] = json.loads(seite[s:e].replace("<\\/", "</")).get("kantonsrat")
    posts = serie(a.slug, daten, bilder, ordner)
    print(f"  {len(bilder)} Bilder, {len(posts)} Beiträge geplant, Ordner {ordner.relative_to(ROOT)}")
    for p in posts:
        print(f"  {p['termin'][:10]}  {len(p['media'])} Bild(er)  {p['text'][:70]}…")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Social-Media-Serie des Finanzspiegels als PNG
=============================================
Die Motive zeichnet die Seite selbst im Browser (Kuchen, Balkenliste, Überblick,
finanzspiegel/bauen.py). Dieses Skript öffnet die gebaute Seite in einem
unsichtbaren Chromium, stellt je Beitrag Jahr, Ansicht und Ebene ein wie ein
Besucher, lässt das Motiv zeichnen und speichert die Leinwand als PNG. Ein
Zeichenprogramm, deckungsgleich mit der Seite.

Ausgabe: site/social/finanzen/<serie>/
    01-ueberblick.png … 07-rechnung.png, posts.json (Serie mit Texten und Terminen)

Ausführen:
    bash scripts/browser_einrichten.sh                 # einmal je Sandbox
    python3 scripts/finanzen_social.py                 # Serie «start», Beginn nächster Montag
    python3 scripts/finanzen_social.py --serie 2026-09-start --start 2026-09-28
    python3 scripts/finanzen_social.py --jahr b27      # nach dem Budget 2027

Texte nach den Regeln des Politspiegels: nummerierte Listen, nur Zahlen, keine
Wertung, keine Erwähnungen. Ein Beitrag je Tag um 09:00, Instagram und Facebook;
TikTok nimmt über Metricool keine Fotos.
"""
import argparse
import base64
import functools
import http.server
import json
import os
import socketserver
import sys
import threading
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
DATEN = ROOT / "finanzspiegel" / "daten" / "finanzspiegel.json"
BASIS_URL = "https://michaeljkahler.github.io/politspiegel/"
SEITE_URL = BASIS_URL + "finanzen/"
HASHTAGS = "#Schaffhausen #Kantonsfinanzen #Politspiegel"
ORDENTLICH = lambda g: g[0] in "34" and g not in ("38", "39", "48", "49")


def mio(v):
    return f"{v / 1e6:,.1f}".replace(",", "'")


def vz(v):
    return ("−" if v < 0 else "+") + mio(abs(v))


def browser_umgebung():
    libs = Path.home() / "libs"
    if libs.exists():
        pfade = [str(libs / "usr/lib/x86_64-linux-gnu"), str(libs / "lib/x86_64-linux-gnu")]
        os.environ["LD_LIBRARY_PATH"] = ":".join(pfade + [os.environ.get("LD_LIBRARY_PATH", "")])


# ---------------------------------------------------------------- Zahlen

def zahlen(d, jahr):
    """Dieselben Summen wie die Seite: ordentlich, Ertrag positiv gedreht."""
    i = 5 + [j["k"] for j in d["jahre"]].index(jahr)
    g, dep, sg, dst = {}, {}, {}, {}
    for z in d["z"]:
        konto = z[3]
        k2 = konto[:2]
        w = z[i]
        g[k2] = g.get(k2, 0) + w
        if not ORDENTLICH(k2) or not w:
            continue
        seite = konto[0]
        v = -w if seite == "4" else w
        dep.setdefault(seite, {}); dep[seite][z[0]] = dep[seite].get(z[0], 0) + v
        sg.setdefault(seite, {}); sg[seite][k2] = sg[seite].get(k2, 0) + v
        dst.setdefault(seite, {}).setdefault(z[0], {})
        dst[seite][z[0]][z[1]] = dst[seite][z[0]].get(z[1], 0) + v
    auf = sum(v for c, v in g.items() if c[0] == "3" and ORDENTLICH(c))
    ert = -sum(v for c, v in g.items() if c[0] == "4" and ORDENTLICH(c))
    ao = -(g.get("38", 0) + g.get("48", 0))
    ab = -g.get("90", 0)
    return {"auf": auf, "ert": ert, "ord": ert - auf, "ao": ao, "ab": ab,
            "gesamt": ert - auf + ao + ab, "dep": dep, "sg": sg, "dst": dst}


def top(d, mapping, namen, n, total):
    reihen = sorted(mapping.items(), key=lambda x: -x[1])[:n]
    return "\n".join(f"{i + 1}. {namen(k)}: {mio(v)} Mio. ({100 * v / total:.1f} %)"
                     for i, (k, v) in enumerate(reihen))


# ---------------------------------------------------------------- Motive

def motive(jahr, jahrzahl, art):
    """Je Beitrag: Dateiname, Schritte im Browser, Motiv der Leinwand."""
    grund = [("jahrzahl", str(jahrzahl)), ("art", art)]
    return [
        {"datei": "01-ueberblick", "schritte": grund, "motiv": "ueberblick"},
        {"datei": "02-aufwand-departemente", "schritte": grund + [("seite", "3"), ("gliederung", "inst")], "motiv": "kuchen"},
        {"datei": "03-ertrag-sachgruppen", "schritte": grund + [("seite", "4"), ("gliederung", "art")], "motiv": "kuchen"},
        {"datei": "04-aufwand-sachgruppen", "schritte": grund + [("seite", "3"), ("gliederung", "art")], "motiv": "kuchen"},
        {"datei": "05-erziehungsdepartement", "schritte": grund + [("seite", "3"), ("gliederung", "inst"), ("suche", "Erziehungsdepartement")], "motiv": "kuchen"},
        {"datei": "06-departement-innern", "schritte": grund + [("seite", "3"), ("gliederung", "inst"), ("suche", "Departement des Innern")], "motiv": "kuchen"},
        {"datei": "07-rechnung", "schritte": [("jahrzahl", str(jahrzahl - 1)), ("art", "r")], "motiv": "ueberblick"},
    ]


def rendern(liste, ordner):
    from playwright.sync_api import sync_playwright
    seite = SITE / "finanzen" / "index.html"
    if not seite.exists():
        raise SystemExit(f"{seite} fehlt. Zuerst finanzspiegel/bauen.py laufen lassen.")
    ordner.mkdir(parents=True, exist_ok=True)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(SITE))
    handler.log_message = lambda *a, **k: None
    srv = socketserver.TCPServer(("127.0.0.1", 0), handler)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    fertig = []
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"])
        pg = b.new_page(viewport={"width": 1400, "height": 1000}, color_scheme="light")
        # Schriften kommen von Google; ohne Netz faellt der Browser auf Systemschriften
        # zurueck, das Bild bleibt vollstaendig.
        pg.goto(f"http://127.0.0.1:{port}/finanzen/index.html")
        pg.wait_for_load_state("networkidle")
        pg.evaluate("document.fonts.ready")
        for m in liste:
            for feld, wert in m["schritte"]:
                if feld == "suche":
                    pg.fill("#sucheFeld", wert); pg.wait_for_timeout(150); pg.keyboard.press("Enter")
                else:
                    knopf = f'.chips button[data-feld="{feld}"][data-wert="{wert}"]'
                    if pg.locator(knopf).count() and not pg.locator(knopf).is_disabled():
                        pg.click(knopf)
                pg.wait_for_timeout(120)
            pg.click("#bildAuf"); pg.wait_for_timeout(150)
            pg.select_option("#bildMotiv", m["motiv"]); pg.wait_for_timeout(300)
            daten = pg.evaluate("document.querySelector('#bildCanvas').toDataURL('image/png')")
            pfad = ordner / f"{m['datei']}.png"
            pfad.write_bytes(base64.b64decode(daten.split(",", 1)[1]))
            pg.click("#bildZu"); pg.wait_for_timeout(100)
            fertig.append(pfad.name)
            print(f"  {pfad.name}")
        b.close()
    srv.shutdown()
    return fertig


# ---------------------------------------------------------------- Texte

def serie(d, jahr, start, serienname, bilder):
    jahrzahl = 2000 + int(jahr[1:])
    titel = next(j["t"] for j in d["jahre"] if j["k"] == jahr)
    K = zahlen(d, jahr)
    # Vergleich Budget gegen Rechnung des letzten abgeschlossenen Jahres
    rk = "r" + str(jahrzahl - 1)[2:]
    bk = "b" + str(jahrzahl - 1)[2:]
    url_ordner = BASIS_URL + "social/finanzen/" + serienname + "/"
    fuss = f"\n\nAlle Zahlen, jeder Klick eine Stufe tiefer: {SEITE_URL}\n\n{HASHTAGS}"
    quelle = f"Quelle: Kanton Schaffhausen, {titel}, Detailzahlen der Erfolgsrechnung. Ordentlicher Aufwand und Ertrag."
    ndep = lambda k: d["dep"].get(k, k)
    nsg = lambda k: d["sg"].get(k, k)
    posts = []

    def post(datei, text, tag):
        if f"{datei}.png" not in bilder:
            return
        posts.append({"art": "bild", "termin": tag.isoformat() + "T09:00", "text": text,
                      "media": [url_ordner + datei + ".png"], "providers": ["instagram", "facebook"],
                      "instagram": {"type": "POST"}, "facebook": {"type": "POST"}})

    t = lambda n: start + timedelta(days=n)

    ao = (f" Dazu kommen {mio(K['ao'])} Mio. ausserordentlicher Ertrag, vor allem Entnahmen aus Reserven."
          if K["ao"] > 0 else f" Davon gehen {mio(-K['ao'])} Mio. ausserordentlicher Aufwand ab." if K["ao"] < 0 else "")
    post("01-ueberblick",
         f"Neu im Politspiegel: der Finanzspiegel. Budget und Staatsrechnung des Kantons Schaffhausen, "
         f"vom Gesamtbild bis zum einzelnen Konto.\n\n{titel}:\n"
         f"1. Ordentlicher Ertrag {mio(K['ert'])} Mio. Franken.\n"
         f"2. Ordentlicher Aufwand {mio(K['auf'])} Mio. Franken.\n"
         f"3. Ordentliches Ergebnis {vz(K['ord'])} Mio.{ao} Gesamtergebnis {vz(K['gesamt'])} Mio. Franken.\n\n{quelle}{fuss}",
         t(0))

    dep3 = K["dep"]["3"]
    post("02-aufwand-departemente",
         f"Wohin das Geld geht: Aufwand nach Departement, {titel}, total {mio(K['auf'])} Mio. Franken.\n\n"
         + top(d, dep3, ndep, 6, K["auf"]) + f"\n\n{quelle}{fuss}", t(1))

    post("03-ertrag-sachgruppen",
         f"Woher das Geld kommt: Ertrag nach Art, {titel}, total {mio(K['ert'])} Mio. Franken.\n\n"
         + top(d, K["sg"]["4"], nsg, 6, K["ert"])
         + "\n\nFiskalertrag sind Steuern, Transferertrag Anteile an Bundessteuern, Finanzausgleich und Beiträge von Bund und Gemeinden."
         + f"\n\n{quelle}{fuss}", t(2))

    post("04-aufwand-sachgruppen",
         f"Wohin das Geld geht: Aufwand nach Art, {titel}, total {mio(K['auf'])} Mio. Franken.\n\n"
         + top(d, K["sg"]["3"], nsg, 6, K["auf"])
         + "\n\nTransferaufwand sind Beiträge an Spitäler, Gemeinden, Hochschulen, Prämienverbilligung und Sozialversicherungen."
         + f"\n\n{quelle}{fuss}", t(3))

    for datei, code, tag in (("05-erziehungsdepartement", "22", t(4)), ("06-departement-innern", "21", t(5))):
        ds = K["dst"]["3"].get(code, {})
        total = sum(ds.values())
        post(datei,
             f"{ndep(code)}, Aufwand nach Dienststelle, {titel}, total {mio(total)} Mio. Franken, "
             f"{100 * total / K['auf']:.1f} % des Aufwands des Kantons.\n\n"
             + top(d, ds, lambda k: d["dst"].get(k) or f"Dienststelle {k}", 6, total) + f"\n\n{quelle}{fuss}", tag)

    if rk in [j["k"] for j in d["jahre"]] and bk in [j["k"] for j in d["jahre"]]:
        R, B = zahlen(d, rk), zahlen(d, bk)
        tr = next(j["t"] for j in d["jahre"] if j["k"] == rk)
        post("07-rechnung",
             f"Budget und Rechnung im Vergleich, {jahrzahl - 1}.\n\n"
             f"1. Ertrag: Budget {mio(B['ert'])} Mio., Rechnung {mio(R['ert'])} Mio. ({vz(R['ert'] - B['ert'])}).\n"
             f"2. Aufwand: Budget {mio(B['auf'])} Mio., Rechnung {mio(R['auf'])} Mio. ({vz(R['auf'] - B['auf'])}).\n"
             f"3. Gesamtergebnis: Budget {vz(B['gesamt'])} Mio., Rechnung {vz(R['gesamt'])} Mio.\n\n"
             f"Quelle: Kanton Schaffhausen, Budget {jahrzahl - 1} und {tr}, Detailzahlen der Erfolgsrechnung.{fuss}",
             t(6))
    return posts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--serie", default=None, help="Ordnername unter site/social/finanzen/")
    ap.add_argument("--start", default=None, help="erster Sendetag, ISO-Datum; Standard: nächster Montag")
    ap.add_argument("--jahr", default=None, help="Datensatz, z. B. b26; Standard: jüngstes Budget")
    ap.add_argument("--nur-texte", action="store_true", help="Bilder nicht neu zeichnen")
    a = ap.parse_args()

    d = json.loads(DATEN.read_text(encoding="utf-8"))
    jahr = a.jahr or [j["k"] for j in d["jahre"] if j["k"].startswith("b")][-1]
    jahrzahl = 2000 + int(jahr[1:])
    heute = date.today()
    start = date.fromisoformat(a.start) if a.start else heute + timedelta(days=(7 - heute.weekday()) % 7 or 7)
    serienname = a.serie or f"{start.isoformat()[:7]}-start"
    ordner = SITE / "social" / "finanzen" / serienname

    browser_umgebung()
    if a.nur_texte:
        bilder = [p.name for p in ordner.glob("*.png")]
    else:
        print(f"Zeichne Motive für {jahr} nach {ordner.relative_to(ROOT)}")
        bilder = rendern(motive(jahr, jahrzahl, jahr[0]), ordner)
    posts = serie(d, jahr, start, serienname, bilder)
    alt = {}
    pj = ordner / "posts.json"
    if pj.exists():
        alt = json.loads(pj.read_text(encoding="utf-8"))
    daten = {"serie": serienname, "jahr": jahr, "start": start.isoformat(),
             "status": alt.get("status", "entwurf"), "bilder": bilder, "posts": posts}
    # Metricool-IDs aus einem frueheren Lauf behalten
    for p in posts:
        for q in alt.get("posts", []):
            if q.get("media") == p["media"] and q.get("metricool"):
                p["metricool"] = q["metricool"]
    pj.write_text(json.dumps(daten, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(posts)} Beiträge, {start} bis {start + timedelta(days=len(posts) - 1)}, {pj.relative_to(ROOT)}")


if __name__ == "__main__":
    sys.exit(main())

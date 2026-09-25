#!/usr/bin/env python3
"""
Social-Media-Serie des Finanzspiegels als PNG
=============================================
Die Motive zeichnet die Seite selbst im Browser (Dialog «Grafik», finanzspiegel/grafik.js,
Format Social Media 4:5). Dieses Skript öffnet die gebaute Seite in einem unsichtbaren
Chromium, stellt je Beitrag die Ansicht über die Adresse ein (#d=b27&g=inst&p=d22, wie
beim Teilen einer Ansicht), lässt das Motiv zeichnen und speichert die Leinwand als PNG.
Ein Zeichenprogramm, deckungsgleich mit der Seite.

Ausgabe: site/social/finanzen/<serie>/
    01-ueberblick.png … 07-finanzplan.png (oder 07-rechnung.png), posts.json (Serie mit Texten und Terminen)

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
    ek_entnahme = fipol = 0   # Entnahmen aus dem Eigenkapital (489), davon finanzpolitische Reserve (4894)
    for z in d["z"]:
        konto = z[3]
        k2 = konto[:2]
        w = z[i]
        g[k2] = g.get(k2, 0) + w
        if konto.startswith("489"):
            ek_entnahme -= w
        if konto.startswith("4894"):
            fipol -= w
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
    return {"auf": auf, "ert": ert, "ord": ert - auf, "ao": ao, "ab": ab, "ek_entnahme": ek_entnahme, "fipol": fipol,
            "gesamt": ert - auf + ao + ab, "dep": dep, "sg": sg, "dst": dst}


def top(d, mapping, namen, n, total):
    reihen = sorted(mapping.items(), key=lambda x: -x[1])[:n]
    return "\n".join(f"{i + 1}. {namen(k)}: {mio(v)} Mio. ({100 * v / total:.1f} %)"
                     for i, (k, v) in enumerate(reihen))


# ---------------------------------------------------------------- Motive

def motive(jahr, jahrzahl, art, rechnung=None, plan=False):
    """Je Beitrag: Dateiname, Ansicht der Seite (Adresse nach #, wie beim Teilen einer
    Ansicht) und Motiv der Grafik. Format immer Social Media 4:5 (1080 x 1350)."""
    grund = f"d={jahr}&r=er&u=ord"
    liste = [
        {"datei": "01-ueberblick", "ansicht": grund + "&g=inst&a=A", "motiv": "ueberblick"},
        {"datei": "02-aufwand-departemente", "ansicht": grund + "&g=inst&a=A", "motiv": "kuchen"},
        {"datei": "03-ertrag-sachgruppen", "ansicht": grund + "&g=art&a=E", "motiv": "kuchen"},
        {"datei": "04-aufwand-sachgruppen", "ansicht": grund + "&g=art&a=A", "motiv": "kuchen"},
        {"datei": "05-erziehungsdepartement", "ansicht": grund + "&g=inst&a=A&p=d22", "motiv": "kuchen"},
        {"datei": "06-departement-innern", "ansicht": grund + "&g=inst&a=A&p=d21", "motiv": "kuchen"},
    ]
    if plan:
        # Entwicklung 2025 bis 2030; die Seite zeigt dort als Vorgabe das Gesamtergebnis
        liste.append({"datei": "07-finanzplan", "ansicht": grund + "&g=inst&a=A", "motiv": "entwicklung"})
    if rechnung:
        liste.append({"datei": ("08" if plan else "07") + "-rechnung",
                      "ansicht": f"d={rechnung}&r=er&u=ord&g=inst&a=A", "motiv": "ueberblick"})
    return liste


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
        b = p.chromium.launch(args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", "--no-proxy-server"])
        pg = b.new_page(viewport={"width": 1400, "height": 1000}, color_scheme="light")
        # Schriften kommen von Google; ohne Netz faellt der Browser auf Systemschriften
        # zurueck, das Bild bleibt vollstaendig.
        for m in liste:
            # Die Ansicht steht in der Adresse; neu laden, damit die Seite sie liest
            pg.goto(f"http://127.0.0.1:{port}/finanzen/index.html#{m['ansicht']}")
            pg.reload()
            pg.wait_for_load_state("networkidle")
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(300)
            pg.click("#grafikAuf"); pg.wait_for_timeout(150)
            pg.select_option("#grafikMotiv", m["motiv"])
            pg.select_option("#grafikFormat", "hoch"); pg.wait_for_timeout(300)
            daten = pg.evaluate("document.querySelector('#grafikCanvas').toDataURL('image/png')")
            pfad = ordner / f"{m['datei']}.png"
            pfad.write_bytes(base64.b64decode(daten.split(",", 1)[1]))
            pg.keyboard.press("Escape"); pg.wait_for_timeout(100)
            fertig.append(pfad.name)
            print(f"  {pfad.name}")
        b.close()
    srv.shutdown()
    return fertig


# ---------------------------------------------------------------- Texte

def serie(d, jahr, start, serienname, bilder):
    jahrzahl = 2000 + int(jahr[1:])
    eintrag = next(j for j in d["jahre"] if j["k"] == jahr)
    titel = eintrag["t"] + (" (Vorlage des Regierungsrates)" if eintrag.get("vorlage") else "")
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

    # Vom ordentlichen Ergebnis zum Gesamtergebnis: ausserordentlich (38, 48) und Fonds im Eigenkapital (90)
    if K["ao"] > 0:
        herkunft = ("Entnahmen aus dem Eigenkapital" if abs(K["ao"] - K["ek_entnahme"]) < 1
                    else "ausserordentlicher Ertrag, vor allem Entnahmen aus dem Eigenkapital" if K["ek_entnahme"] > K["ao"] / 2
                    else "ausserordentlicher Ertrag")
        teile = [f"{mio(K['ao'])} Mio. {herkunft}"
                 + (f", davon {mio(K['fipol'])} Mio. aus der finanzpolitischen Reserve," if K["fipol"] >= 50_000 else "")]
    elif K["ao"] < 0:
        teile = [f"minus {mio(-K['ao'])} Mio. ausserordentlicher Aufwand"]
    else:
        teile = []
    if abs(K["ab"]) >= 50_000:
        teile.append(f"netto {mio(K['ab'])} Mio. aus Spezialfinanzierungen und Fonds" if K["ab"] > 0
                     else f"netto minus {mio(-K['ab'])} Mio. an Spezialfinanzierungen und Fonds")
    ao = f" Dazu kommen {' und '.join(teile)}." if teile else ""
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

    plan = [p for p in d.get("plan") or [] if p["j"] > jahrzahl]
    if plan:
        kz = d["kz"]
        rechnungen = [j for j in d["jahre"] if j["a"] == "r"]
        reihe = rechnungen[-1:] + [j for j in d["jahre"] if j["a"] == "b" and rechnungen and j["j"] > rechnungen[-1]["j"]] + plan
        name = lambda j: j["t"] + (" (Vorlage)" if j.get("vorlage") else "")
        zeilen = "\n".join(f"{n + 1}. {name(j)}: {vz(kz[j['k']]['gesamt'])} Mio." for n, j in enumerate(reihe))
        summe = sum(kz[j["k"]]["gesamt"] for j in [eintrag] + plan)
        ek_von, ek_bis = kz[reihe[0]["k"]].get("ekap"), kz[plan[-1]["k"]].get("ekap")
        ek = (f" Eigenkapital Ende {reihe[0]['j']}: {mio(ek_von)} Mio., Ende {plan[-1]['j']}: {mio(ek_bis)} Mio. Franken."
              if ek_von and ek_bis else "")
        post("07-finanzplan",
             f"Finanzplan bis {plan[-1]['j']}: Gesamtergebnis der Erfolgsrechnung in Millionen Franken.\n\n{zeilen}\n\n"
             f"Von {jahrzahl} bis {plan[-1]['j']} zusammen {vz(summe)} Mio. Franken.{ek}\n\n"
             f"Quelle: Kanton Schaffhausen, {titel.replace(eintrag['t'], eintrag['t'] + ' und Finanzplan ' + str(jahrzahl) + '–' + str(plan[-1]['j']))}, "
             f"Ziffern 2.1 und 2.3; Staatsrechnung {reihe[0]['j']}.{fuss}",
             t(6))

    if rk in [j["k"] for j in d["jahre"]] and bk in [j["k"] for j in d["jahre"]]:
        R, B = zahlen(d, rk), zahlen(d, bk)
        tr = next(j["t"] for j in d["jahre"] if j["k"] == rk)
        post("08-rechnung" if plan else "07-rechnung",
             f"Budget und Rechnung im Vergleich, {jahrzahl - 1}.\n\n"
             f"1. Ertrag: Budget {mio(B['ert'])} Mio., Rechnung {mio(R['ert'])} Mio. ({vz(R['ert'] - B['ert'])}).\n"
             f"2. Aufwand: Budget {mio(B['auf'])} Mio., Rechnung {mio(R['auf'])} Mio. ({vz(R['auf'] - B['auf'])}).\n"
             f"3. Gesamtergebnis: Budget {vz(B['gesamt'])} Mio., Rechnung {vz(R['gesamt'])} Mio.\n\n"
             f"Quelle: Kanton Schaffhausen, Budget {jahrzahl - 1} und {tr}, Detailzahlen der Erfolgsrechnung.{fuss}",
             t(7) if plan else t(6))
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
        rechnungen = [j["k"] for j in d["jahre"] if j["k"] == "r" + str(jahrzahl - 1)[2:]]
        plan = any(p["j"] > jahrzahl for p in d.get("plan") or [])
        bilder = rendern(motive(jahr, jahrzahl, jahr[0], rechnungen[0] if rechnungen else None, plan), ordner)
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

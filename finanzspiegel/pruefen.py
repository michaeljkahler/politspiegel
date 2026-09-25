#!/usr/bin/env python3
"""Prüft die gebaute Seite des Finanzspiegels im Browser.

Aufruf aus der Projektwurzel, nach bauen.py:
    python3 finanzspiegel/pruefen.py [Zielordner für Testbilder]

Braucht Playwright mit Chromium (in der Sandbox: bash scripts/browser_einrichten.sh).
Die Seite läuft über einen lokalen HTTP-Server; für die Prüfung wird eine Kopie mit
einem Zugang zu den inneren Funktionen angelegt (site/finanzen/_test.html) und am Ende
gelöscht. Geprüft wird:

1. Zahlen: Wurzel des Baums gegen die Kennzahlen je Datensatz (Aufwand, Ertrag,
   Gesamtergebnis, Nettoinvestitionen), Kinder gegen Eltern auf allen Ebenen,
   in allen Gliederungen und für jedes Jahr.
2. Grafiken: jedes Motiv in jedem Format für drei Auswahlen, als PNG; Ringdiagramm
   (Flächen gegen positive Einträge, Tabelle gegen Total der Ebene), Ebenenwahl
   («alle Konten» und übersprungene Ebenen behalten das Total).
3. Bedienung: Klick in Icicle und Tabelle, Suche, Prüfhinweis im Vergleich, Adresse
   (Hash), Finanzplan in der Auswahl, Investitionsrechnung bis zum Vorhaben.
4. Darstellung: keine Fehler in der Konsole, auf 390 px kein waagrechtes Scrollen,
   Bildschirmfotos hell, dunkel und mobil.
Ausgabe: Zusammenfassung; Rückgabewert 1 bei einer Abweichung.
"""
from __future__ import annotations

import asyncio
import base64
import functools
import http.server
import json
import os
import socketserver
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
SEITE = SITE / "finanzen" / "index.html"
TEST = SITE / "finanzen" / "_test.html"
ENDE = "if(document.fonts && document.fonts.ready) document.fonts.ready.then(init); else init();\n})();"
HAKEN = ("window.__t = {D, DS, KZ, BF, st, G, baum, BAUM: () => BAUM, KNOTEN: () => KNOTEN, wert, sichtbar, kinderSortiert, "
         "aktuellerKnoten, setzePfad, gRingDaten, gZielKnoten, gEbene, gZeichnen, neu, zeichneDrill, suche, springeZu, "
         "zeigeImVergleich, kzWert, gesperrt, hashLesen, hashSchreiben, gruppenVon};\n")


def browser_umgebung():
    libs = Path.home() / "libs"
    if libs.exists():
        pfade = [str(libs / "usr/lib/x86_64-linux-gnu"), str(libs / "lib/x86_64-linux-gnu")]
        os.environ["LD_LIBRARY_PATH"] = ":".join(pfade + [os.environ.get("LD_LIBRARY_PATH", "")])


PRUEF_ZAHLEN = r"""
() => {
  const T = window.__t, {D, DS, KZ, st} = T, out = {faelle: 0, abw: []};
  const nah = (a, b, tol) => Math.abs(a - b) <= (tol || 1);
  const pruefeBaum = (n, s, pfad) => {
    if(!n.kinder.size) return;
    for(const i of [0, 1]){
      const summe = [...n.kinder.values()].reduce((a, c) => a + c.v[s][i], 0);
      out.faelle++;
      if(!nah(summe, n.v[s][i], 2)) out.abw.push(['Kinder', pfad, n.id, s, i, Math.round(summe), Math.round(n.v[s][i])]);
    }
    n.kinder.forEach(c => pruefeBaum(c, s, pfad));
  };
  for(const d of DS){
    const k = d.k, plan = d.a === 'p';
    for(const [r, gl, u] of [['er', 'inst', 'ord'], ['er', 'art', 'ord'], ['er', 'inst', 'alle'], ['er', 'art', 'alle'], ['ir', 'inst', 'alle'], ['ir', 'art', 'alle']]){
      if(plan && r === 'er' && gl === 'inst') continue;
      st.sel = [k]; st.rechnung = r; st.gl = gl; st.umfang = u; st.pfad = []; T.baum();
      const w = T.BAUM(), K = KZ[k], pfad = `${k} ${r} ${gl} ${u}`;
      const tol = plan ? 10000 : 1;   // Finanzplan: gedruckte Tausender, einzeln gerundet
      out.faelle++;
      if(r === 'er' && u === 'ord'){
        if(!nah(w.v[0][0], K.auf, tol) || !nah(w.v[0][1], K.ert, tol)) out.abw.push(['Wurzel ordentlich', pfad, Math.round(w.v[0][0]), Math.round(K.auf), Math.round(w.v[0][1]), Math.round(K.ert)]);
      } else if(r === 'er'){
        if(!nah(w.v[0][0] - w.v[0][1], -K.gesamt, tol)) out.abw.push(['Wurzel alle', pfad, Math.round(w.v[0][0] - w.v[0][1]), Math.round(-K.gesamt)]);
      } else {
        if(!nah(w.v[0][0] - w.v[0][1], K.netInv, tol) || !nah(w.v[0][0], K.invA, tol)) out.abw.push(['Wurzel IR', pfad, Math.round(w.v[0][0] - w.v[0][1]), Math.round(K.netInv)]);
      }
      pruefeBaum(w, 0, pfad);
    }
  }
  // Drei Jahre zugleich: jede Spalte wie das Jahr allein
  st.sel = ['b27', 'b26', 'r25']; st.rechnung = 'er'; st.gl = 'inst'; st.umfang = 'ord'; st.pfad = []; T.baum();
  st.sel.forEach((k, s) => { out.faelle++; if(!nah(T.BAUM().v[s][0], KZ[k].auf)) out.abw.push(['Auswahl drei', k]); pruefeBaum(T.BAUM(), s, 'drei ' + k); });
  // Ringdiagramm: Flächen = positive Einträge; Tabelle + nicht gezeigte = Total der Ebene
  out.ringe = {faelle: 0, abw: []};
  const auswahlen = [['b27', 'b26', 'r25'], ['b25', 'r25'], ['b27', 'p28', 'p30'], ['r25'], ['p29']];
  for(const sel of auswahlen) for(const r of ['er', 'ir']) for(const gl of ['inst', 'art']) for(const u of (r === 'er' ? ['ord', 'alle'] : ['alle'])){
    st.sel = sel; st.rechnung = r; st.gl = gl; st.umfang = u; st.pfad = []; T.baum();
    const wurzel = T.BAUM(), knoten = [wurzel];
    const k1 = [...wurzel.kinder.values()].sort((a, b) => Math.abs(b.v[0][0]) - Math.abs(a.v[0][0]))[0];
    if(k1 && !T.gesperrt()){ knoten.push(k1); const k2 = [...k1.kinder.values()].sort((a, b) => Math.abs(b.v[0][0]) - Math.abs(a.v[0][0]))[0]; if(k2 && k2.kinder.size) knoten.push(k2); }
    for(const ansicht of ['A', 'E', 'N']){
      st.ansicht = ansicht;
      for(const n of knoten) for(const maxE of [7, 5]){
        const d = T.gRingDaten(n, maxE), gezeigt = new Set(d.plus);
        sel.forEach((k, s) => {
          out.ringe.faelle++;
          const posi = [...n.kinder.values()].reduce((a, c) => a + Math.max(0, T.wert(c, s)), 0);
          const tab = d.teile.reduce((a, t) => a + (t.v[s] === null ? 0 : t.v[s]), 0) + [...n.kinder.values()].filter(c => !gezeigt.has(c)).reduce((a, c) => a + T.wert(c, s), 0);
          // Finanzplan in der Investitionsrechnung: nur ein Total, keine Einträge (die Grafik nennt es)
          const ohneTeile = ![...n.kinder.values()].some(c => Math.abs(T.wert(c, s)) >= .5);
          const a1 = Math.abs(d.summe[s] - posi), a2 = n.kinder.size && !ohneTeile ? Math.abs(tab - T.wert(n, s)) : 0;
          if(a1 > .05 || a2 > .05) out.ringe.abw.push([sel.join('-'), r, gl, u, ansicht, n.id, k, a1, a2]);
        });
      }
    }
  }
  st.ansicht = 'A';
  // Ebenenwahl: «alle Konten» und übersprungene Ebenen behalten das Total
  out.ebene = {faelle: 0, abw: []};
  for(const sel of [['b27', 'b26', 'r25'], ['r25']]) for(const r of ['er', 'ir']) for(const gl of ['inst', 'art']){
    st.sel = sel; st.rechnung = r; st.gl = gl; st.umfang = r === 'er' ? 'ord' : 'alle'; st.pfad = []; T.baum();
    const knoten = [T.BAUM()], lauf = (n, t) => { if(t > 3) return; n.kinder.forEach(c => { if(!c.blatt && c.kinder.size){ knoten.push(c); lauf(c, t + 1); } }); };
    lauf(T.BAUM(), 1);
    for(const n of knoten.slice(0, 400)) for(const tiefe of ['naechste', 'konten']){
      T.setzePfad(n); T.G.ebene = null; T.G.tiefe = tiefe;
      const z = T.gZielKnoten();
      out.ebene.faelle++;
      sel.forEach((k, s) => { for(const i of [0, 1]){ const summe = [...z.kinder.values()].reduce((a, c) => a + c.v[s][i], 0); if(Math.abs(summe - n.v[s][i]) > 1) out.ebene.abw.push([sel.join('-'), r, gl, n.id, tiefe, k, i, summe, n.v[s][i]]); } });
    }
  }
  T.G.tiefe = 'naechste';
  return out;
}
"""


async def main() -> int:
    from playwright.async_api import async_playwright
    ziel = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/finanzspiegel-test")
    ziel.mkdir(parents=True, exist_ok=True)
    html = SEITE.read_text(encoding="utf-8")
    if ENDE not in html:
        print("Ende des Skripts nicht gefunden; bauen.py geändert?")
        return 1
    TEST.write_text(html.replace(ENDE, ENDE[:-len("})();")] + HAKEN + "})();"), encoding="utf-8")
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(SITE))
    handler.log_message = lambda *a, **k: None
    srv = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}/finanzen/"
    fehler = 0
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(args=["--no-proxy-server", "--no-sandbox", "--disable-dev-shm-usage"])
            ctx = await b.new_context(viewport={"width": 1400, "height": 1000}, accept_downloads=True)
            pg = await ctx.new_page()
            meldungen = []
            pg.on("console", lambda m: meldungen.append(f"{m.type}: {m.text}") if m.type == "error" else None)
            pg.on("pageerror", lambda e: meldungen.append(f"Seitenfehler: {e}"))
            await pg.goto(url + "_test.html")
            await pg.wait_for_timeout(2000)
            await pg.wait_for_function("window.__t !== undefined")

            # 1. Zahlen
            r = await pg.evaluate(PRUEF_ZAHLEN)
            print(f"Zahlen: {r['faelle']} Fälle, {len(r['abw'])} Abweichungen")
            print(f"Ringdiagramm: {r['ringe']['faelle']} Fälle, {len(r['ringe']['abw'])} Abweichungen")
            print(f"Ebenenwahl: {r['ebene']['faelle']} Fälle, {len(r['ebene']['abw'])} Abweichungen")
            for a in (r["abw"] + r["ringe"]["abw"] + r["ebene"]["abw"])[:12]:
                print("   ", a)
            fehler += len(r["abw"]) + len(r["ringe"]["abw"]) + len(r["ebene"]["abw"])
            await pg.goto(url + "_test.html#")
            await pg.reload()
            await pg.wait_for_timeout(1500)

            # 2. Grafiken: jedes Motiv in jedem Format, drei Auswahlen
            async def canvas(name):
                daten = await pg.evaluate("document.getElementById('grafikCanvas').toDataURL('image/png')")
                (ziel / f"{name}.png").write_bytes(base64.b64decode(daten.split(",", 1)[1]))
                leer = await pg.evaluate("""() => { const c = document.getElementById('grafikCanvas'), x = c.getContext('2d');
                  const d = x.getImageData(0, 0, c.width, c.height).data; let n = 0; for(let i = 0; i < d.length; i += 4000) if(d[i] < 200) n++; return n; }""")
                return leer
            bilder = 0
            for praefix, auswahl in (("a", "b27,b26,r25"), ("b", "b27,p28,p30"), ("c", "r25")):
                await pg.evaluate(f"() => {{ window.__t.st.sel = '{auswahl}'.split(','); window.__t.st.pfad = []; window.__t.neu(); }}")
                await pg.click("#grafikAuf"); await pg.wait_for_timeout(300)
                for m in ["kuchen", "balken", "ringe", "ueberblick", "entwicklung", "kennzahlen"]:
                    await pg.select_option("#grafikMotiv", m)
                    for f in ["hoch", "folie", "bericht"]:
                        await pg.select_option("#grafikFormat", f)
                        await pg.wait_for_timeout(60)
                        if await canvas(f"{praefix}_{m}_{f}") < 20:
                            print(f"    Grafik fast leer: {praefix} {m} {f}"); fehler += 1
                        bilder += 1
                await pg.keyboard.press("Escape"); await pg.wait_for_timeout(100)
            # Ringe mit gemeinsamer Skala, Ebene tiefer, alle Konten, transparenter Grund
            await pg.evaluate("() => { const T = window.__t; T.st.sel = ['b27','b26','r25']; T.st.rechnung = 'er'; T.st.gl = 'inst'; T.st.pfad = ['d21']; T.neu(true); }")
            await pg.click("#grafikAuf"); await pg.wait_for_timeout(200)
            await pg.select_option("#grafikMotiv", "ringe"); await pg.select_option("#grafikSkala", "betrag")
            await pg.select_option("#grafikFormat", "folie"); await canvas("d_ringe_skala_folie")
            await pg.select_option("#grafikTiefe", "konten"); await canvas("d_ringe_konten_folie")
            await pg.check('input[name="grafikHg"][value="transparent"]'); await canvas("d_ringe_transparent")
            await pg.fill("#grafikTitel", "Departement des Innern: Aufwand im Budget 2027, 2026 und in der Rechnung 2025"); await pg.wait_for_timeout(250)
            await canvas("d_titel")
            async with pg.expect_download() as dl:
                await pg.click("#grafikLaden")
            print(f"Grafiken: {bilder + 4} Bilder, Download {(await dl.value).suggested_filename}")
            await pg.keyboard.press("Escape")

            # 3. Bedienung
            await pg.evaluate("() => { const T = window.__t; T.st.sel = ['b27','b26','r25']; T.st.rechnung = 'er'; T.st.gl = 'inst'; T.st.umfang = 'ord'; T.st.ansicht = 'A'; T.st.pfad = []; T.neu(); }")
            await pg.click("#icicles rect.seg"); await pg.wait_for_timeout(150)
            krume = await pg.text_content("#krume")
            await pg.click("#tabelle tr.klick"); await pg.wait_for_timeout(150)
            krume2 = await pg.text_content("#krume")
            print(f"Klick Icicle: {krume.strip()} · Klick Tabelle: {krume2.strip()}")
            await pg.fill("#sucheFeld", "Spitalversorgung"); await pg.wait_for_timeout(200)
            await pg.keyboard.press("Enter"); await pg.wait_for_timeout(300)
            print(f"Suche «Spitalversorgung»: {(await pg.text_content('#krume')).strip()} · markiert {await pg.evaluate('window.__t.st.markiert')}")
            await pg.evaluate("() => { const T = window.__t; T.st.rechnung = 'ir'; T.st.gl = 'inst'; T.st.pfad = ['d23', 's2332']; T.baum(); T.zeichneDrill(); }")
            zeilen_ir = await pg.locator("#tabelle tbody tr").count()
            print(f"Investitionsrechnung, 2332: {zeilen_ir - 1} Vorhaben; {(await pg.text_content('#krume')).strip()}")
            await pg.evaluate("() => { const T = window.__t; T.st.sel = ['b27','p28']; T.st.rechnung = 'er'; T.st.gl = 'inst'; T.neu(); }")
            gl = await pg.evaluate("window.__t.st.gl")
            hinweis = await pg.is_visible("#planhinweis")
            print(f"Finanzplan in der Auswahl: Gliederung {gl}, Hinweis sichtbar {hinweis}")
            if gl != "art" or not hinweis:
                fehler += 1
            # Prüfhinweis im Vergleich
            await pg.evaluate("() => { const T = window.__t; T.st.sel = ['b27','b26','r25']; T.neu(); }")
            await pg.click("#bfListe li .bf-kopf"); await pg.wait_for_timeout(100)
            await pg.click("#bfListe li.offen button.knopf"); await pg.wait_for_timeout(300)
            print(f"Prüfhinweis 1 im Vergleich: {(await pg.text_content('#krume')).strip()} · {await pg.evaluate('window.__t.st.rechnung')}")
            # Adresse
            h = await pg.evaluate("location.hash")
            await pg.goto(url + "_test.html" + h); await pg.wait_for_timeout(1200)
            h2 = await pg.evaluate("location.hash")
            print(f"Adresse: {h} {'gleich' if h == h2 else 'anders: ' + h2}")
            if h != h2:
                fehler += 1
            await pg.screenshot(path=str(ziel / "seite_desktop.png"), full_page=False)

            # 4. Darstellung
            for name, vp, schema in (("mobil", {"width": 390, "height": 844}, "light"), ("dunkel", {"width": 1400, "height": 1000}, "dark")):
                c2 = await b.new_context(viewport=vp, color_scheme=schema)
                p2 = await c2.new_page()
                p2.on("console", lambda m: meldungen.append(f"{m.type}: {m.text}") if m.type == "error" else None)
                p2.on("pageerror", lambda e: meldungen.append(f"Seitenfehler: {e}"))
                await p2.goto(url); await p2.wait_for_timeout(1500)
                sw = await p2.evaluate("[document.scrollingElement.scrollWidth, window.innerWidth]")
                await p2.screenshot(path=str(ziel / f"seite_{name}.png"), full_page=True)
                if sw[0] > sw[1]:
                    print(f"{name}: waagrechtes Scrollen {sw}"); fehler += 1
                if name == "mobil":
                    await p2.click("#grafikAuf"); await p2.wait_for_timeout(300)
                    sw2 = await p2.evaluate("[document.scrollingElement.scrollWidth, window.innerWidth]")
                    await p2.screenshot(path=str(ziel / "dialog_mobil.png"))
                    print(f"mobil 390 px: Seite {sw}, mit Dialog {sw2}")
                await c2.close()
            print(f"Konsole: {len(meldungen)} Fehler" + (": " + "; ".join(meldungen[:5]) if meldungen else ""))
            fehler += len(meldungen)
            await b.close()
    finally:
        srv.shutdown()
        TEST.unlink(missing_ok=True)
    print(f"Ergebnis: {'keine Abweichung' if not fehler else f'{fehler} Abweichungen'}; Bilder in {ziel}")
    return 1 if fehler else 0


if __name__ == "__main__":
    browser_umgebung()
    sys.exit(asyncio.run(main()))

#!/usr/bin/env python3
"""Baut den Finanzspiegel, die vierte Ebene des Politspiegels.

Aufruf aus der Projektwurzel:
    python3 finanzspiegel/bauen.py

Liest    finanzspiegel/daten/finanzspiegel.json   aus daten.py
         politspiegel/politspiegel.json           Impressum, Testphase, Meldewerkzeug
Schreibt site/finanzen/index.html                 eine Datei, alles inline

Drei Teile, von grob nach fein:

1. Ueberblick «Woher, wohin». Zwei Balken auf derselben Skala, oben der Ertrag nach
   Ertragsart, unten der Aufwand nach Aufwandart. Der Unterschied der Laengen ist
   das ordentliche Ergebnis; ein Kaestchen rechnet vor, wie daraus mit dem
   ausserordentlichen Ergebnis das Gesamtergebnis wird. Das ist die Antwort auf die
   Frage «wohin fliesst das Geld» fuer jemanden, der zehn Sekunden hat.

2. Drilldown. Icicle: je Ebene ein Band, Breite gleich Betrag, Klick geht eine Stufe
   tiefer, Brotkrumen zurueck. Zwei Gliederungen: nach Dienststelle (Departement,
   Dienststelle, Fonds, Konto; kreditrechtlich verbindlich) und nach Sachgruppe
   (Artengliederung HRM2, zwei- und dreistellig, Konto). Darunter die Kinder als
   Tabelle mit Betrag, Anteil und Vergleichsjahr.

3. Bild fuer Social Media, 1080 x 1350, im Browser gezeichnet wie im
   Kantonsratsspiegel. Zwei Motive: der Ueberblick und die gerade gezeigte Ebene.

Warum Icicle und nicht Mindmap: Ein Knotendiagramm zeigt Struktur, nicht Groesse.
Bildung mit 178 Mio. und Kultur mit 7 Mio. saehen als Knoten gleich aus. Und Ebene
drei hat 129 Dienststellen; radial ist das auf dem Telefon nicht lesbar.

Warum Aufwand und Ertrag getrennt: Flaechen koennen nicht negativ sein, und 14 der
129 Dienststellen schliessen mit Ertragsueberschuss.

Warum nur ordentlich im Drilldown: Interne Verrechnungen (39, 49) stehen beidseits
gleich und blaehen beide Seiten um 47 Mio. auf; Ausserordentliches (38, 48) sind
Reservebewegungen. Mit ihnen stimmte kein Total mit dem Bericht ueberein, ohne sie
stimmen alle: 1'156.5 und 1'063.8 Mio. im Budget 2026, wie in Kapitel 1.7.
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
ROOT = HIER.parent
sys.path.insert(0, str(ROOT / "politspiegel"))
from impressum import IMPRESSUM_CSS, impressum_html  # noqa: E402
from melden import MELDEN_CSS, melden_html, melden_knopf_html  # noqa: E402
from testphase import TESTPHASE_CSS, testphase_html  # noqa: E402

e = lambda s: html.escape(str(s), quote=True)

CSS = """
:root{
  --pro:#0F766E; --pro-text:#0C6A62; --contra:#8E44AD; --contra-text:#7E3C9A;
  --grund:#FFFFFF; --flaeche:#F7F8FA; --karte:#FFFFFF;
  --text:#12161C; --text-leise:#5A626D; --linie:#E2E6EB; --hover:#F2F7F6;
  --auf:#0F766E,#1E9189,#3FB3A8,#7ACBC3,#A9DDD8,#CDEBE8,#E2F3F1;
  --ert:#7E3C9A,#9553AE,#AE78C4,#C4A0D6,#D8BEE4,#E8D8F0,#F1E8F6;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --pro:#3FB3A8; --pro-text:#3FB3A8; --contra:#C08AD8; --contra-text:#C08AD8;
    --grund:#12161C; --flaeche:#171C24; --karte:#1B212B;
    --text:#EEF1F5; --text-leise:#9AA3AF; --linie:#2C3440; --hover:#1F2731;
  }
}
:root[data-theme="dark"]{
  --pro:#3FB3A8; --pro-text:#3FB3A8; --contra:#C08AD8; --contra-text:#C08AD8;
  --grund:#12161C; --flaeche:#171C24; --karte:#1B212B;
  --text:#EEF1F5; --text-leise:#9AA3AF; --linie:#2C3440; --hover:#1F2731;
}
*{box-sizing:border-box}
body{margin:0;background:var(--grund);color:var(--text);
  font-family:"Public Sans","Helvetica Neue",Arial,sans-serif;font-size:16px;line-height:1.55}
h1,h2,h3{font-family:Archivo,"Helvetica Neue",Arial,sans-serif;font-weight:600}
a{color:inherit}
button{font:inherit}
.wrap{max-width:1000px;margin:0 auto;padding:0 24px 80px}
.kopf{border-bottom:1px solid var(--linie);padding:28px 0 26px;margin-bottom:26px}
.zurueck{display:inline-flex;align-items:center;gap:6px;font-family:Archivo,sans-serif;font-size:13px;font-weight:600;
  letter-spacing:.08em;text-transform:uppercase;color:var(--text-leise);text-decoration:none;margin-bottom:14px}
.zurueck:hover{color:var(--text)}
.marke{font-size:13px;letter-spacing:.10em;text-transform:uppercase;color:var(--pro-text);
  font-family:Archivo,sans-serif;font-weight:600}
h1{font-size:clamp(28px,4.6vw,42px);line-height:1.1;margin:10px 0 10px;letter-spacing:-.015em;text-wrap:balance}
.lead{margin:0;font-size:17px;color:var(--text-leise);max-width:64ch}

.steuer{display:flex;flex-wrap:wrap;gap:14px 22px;margin:0 0 22px}
.grp{display:flex;flex-direction:column;gap:6px}
.grp b{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--text-leise);font-weight:600;font-family:Archivo,sans-serif}
.chips{display:inline-flex;border:1px solid var(--linie);border-radius:8px;overflow:hidden;background:var(--karte)}
.chips button{appearance:none;border:0;background:transparent;color:var(--text);padding:7px 13px;
  font-size:14px;cursor:pointer;border-right:1px solid var(--linie)}
.chips button:last-child{border-right:0}
.chips button[aria-pressed="true"]{background:var(--pro);color:#fff;font-weight:600}
#drill.ertrag .chips button[aria-pressed="true"]{background:var(--contra)}
.chips button:focus-visible{outline:2px solid var(--text);outline-offset:-2px}
.chips button[disabled]{color:var(--text-leise);opacity:.45;cursor:not-allowed}

h2{font-size:15px;letter-spacing:.06em;text-transform:uppercase;color:var(--text-leise);margin:34px 0 12px}
h2 small{text-transform:none;letter-spacing:0;font-weight:400;font-family:"Public Sans",sans-serif;color:var(--text-leise)}
.karte{background:var(--karte);border:1px solid var(--linie);border-radius:14px;padding:18px 20px;margin-bottom:14px}

.kacheln{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:14px}
.kachel{background:var(--karte);border:1px solid var(--linie);border-radius:14px;padding:14px 16px}
.kachel .z{font-family:Archivo,sans-serif;font-size:clamp(20px,3vw,27px);font-weight:600;letter-spacing:-.02em;line-height:1.1;font-variant-numeric:tabular-nums}
.kachel .l{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--text-leise);margin-top:6px;font-family:Archivo,sans-serif;font-weight:600}
.kachel .s{font-size:13px;color:var(--text-leise);margin-top:6px;line-height:1.35}
.kachel.ert .z{color:var(--contra-text)} .kachel.auf .z{color:var(--pro-text)}

.ww svg{display:block;width:100%;height:auto}
.ww .beschr{font-family:Archivo,sans-serif;font-size:12px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;fill:var(--text-leise)}
.ww .seg{stroke:var(--karte);stroke-width:1.5;cursor:pointer}
.ww .seg:hover{opacity:.85}
.ww .in{font-size:11.5px;font-weight:600;pointer-events:none}
.ww .diff{font-size:12px;fill:var(--text-leise)}
.ww .diffz{font-family:Archivo,sans-serif;font-size:13px;font-weight:600;fill:var(--text)}
.legenden{display:grid;grid-template-columns:1fr 1fr;gap:6px 26px;margin-top:14px}
.legende h3{margin:0 0 6px;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--text-leise)}
.legende ol{list-style:none;margin:0;padding:0}
.legende li{display:grid;grid-template-columns:12px 1fr auto;gap:8px;align-items:baseline;padding:5px 0;border-top:1px solid var(--linie);font-size:14px;cursor:pointer}
.legende li:hover{background:var(--hover)}
.legende li i{display:inline-block;width:12px;height:12px;border-radius:3px;transform:translateY(1px)}
.legende li small{display:block;color:var(--text-leise);font-size:12.5px;line-height:1.35}
.legende li b{font-weight:600;font-variant-numeric:tabular-nums;white-space:nowrap}
.legende li b em{font-style:normal;color:var(--text-leise);font-weight:400;margin-left:6px}
.ergebnis{margin-top:14px;padding-top:12px;border-top:1px solid var(--linie);font-size:14px;color:var(--text-leise);line-height:1.5}
.ergebnis b{color:var(--text);font-variant-numeric:tabular-nums}

.steuer-oben{align-items:flex-end}
.suche{flex:1 1 280px;min-width:240px}
.suche label b{display:block}
.suchbox{position:relative}
#sucheFeld{width:100%;padding:8px 14px;border:1px solid var(--linie);border-radius:8px;background:var(--karte);color:var(--text);font:inherit;font-size:14.5px;height:38px}
#sucheFeld:focus{outline:2px solid var(--pro);outline-offset:-1px}
#sucheListe{position:absolute;left:0;right:0;top:calc(100% + 4px);z-index:860;margin:0;padding:4px;list-style:none;background:var(--karte);
  border:1px solid var(--linie);border-radius:10px;box-shadow:0 8px 28px rgba(0,0,0,.14);max-height:360px;overflow:auto}
#sucheListe li{display:grid;grid-template-columns:1fr auto;gap:2px 12px;padding:8px 10px;border-radius:7px;cursor:pointer;font-size:14px}
#sucheListe li:hover,#sucheListe li[aria-selected="true"]{background:var(--hover)}
#sucheListe li .art{grid-column:1/-1;font-size:12px;color:var(--text-leise)}
#sucheListe li .art em{font-style:normal;padding:1px 6px;border-radius:4px;background:var(--flaeche);border:1px solid var(--linie);margin-right:6px;font-size:11px;text-transform:uppercase;letter-spacing:.04em}
#sucheListe li b{font-weight:600;font-variant-numeric:tabular-nums;white-space:nowrap;color:var(--text-leise)}
#sucheListe li.leer{color:var(--text-leise);cursor:default}

.krume{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:0 0 10px;font-size:14px}
.krume button{appearance:none;border:0;background:none;color:var(--pro-text);padding:0;
  cursor:pointer;text-decoration:underline;text-underline-offset:2px}
.krume span{color:var(--text-leise)} .krume .jetzt{color:var(--text);font-weight:600}
.dkopf{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:baseline;gap:8px;margin-bottom:12px}
.dkopf .betrag{font-family:Archivo,sans-serif;font-size:26px;font-weight:600;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.dkopf .neben{color:var(--text-leise);font-size:13.5px}
#icicle{display:block;width:100%;height:auto;overflow:visible}
#icicle rect{cursor:pointer}
#icicle text{pointer-events:none;font-size:11px}
.leer{color:var(--text-leise);font-size:14px;padding:8px 0}
table{width:100%;border-collapse:collapse;font-size:14px}
th{text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--text-leise);
  border-bottom:1px solid var(--text);padding:6px 8px 6px 0;font-weight:600;white-space:nowrap;font-family:Archivo,sans-serif}
th.r,td.r{text-align:right;padding-right:0;padding-left:12px;font-variant-numeric:tabular-nums;white-space:nowrap}
td{border-bottom:1px solid var(--linie);padding:8px 8px 8px 0;vertical-align:top}
tr.klick{cursor:pointer} tr.klick:hover td{background:var(--hover)}
td .nr{color:var(--text-leise);font-variant-numeric:tabular-nums;margin-right:7px;font-size:13px}
td.plus,td.minus{color:var(--text-leise)}
.balken{display:block;height:4px;background:var(--pro);border-radius:2px;margin-top:6px;max-width:320px}
.ertrag .balken{background:var(--contra)}

.bildknopf{position:fixed;right:18px;bottom:18px;z-index:800;display:inline-flex;align-items:center;gap:8px;
  background:var(--text);color:var(--grund);border:0;border-radius:999px;padding:11px 16px;font-weight:600;
  font-size:14px;cursor:pointer;box-shadow:0 4px 18px rgba(0,0,0,.18)}
.bildknopf svg{width:16px;height:16px}
.bildlage{position:fixed;inset:0;z-index:950;background:rgba(10,14,20,.55);display:none;align-items:flex-start;justify-content:center;padding:30px 14px;overflow:auto}
.bildlage.offen{display:flex}
.bildbox{background:var(--karte);color:var(--text);border-radius:16px;max-width:920px;width:100%;padding:18px 20px 22px;border:1px solid var(--linie)}
.bildkopf{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
.bildkopf h2{margin:0;font-size:18px;text-transform:none;letter-spacing:0;color:var(--text)}
.bildzu{appearance:none;border:0;background:none;color:var(--text-leise);font-size:26px;cursor:pointer;line-height:1}
.bildbody{display:grid;grid-template-columns:260px 1fr;gap:18px}
.bildwahl label{display:block;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--text-leise);margin:8px 0 4px;font-family:Archivo,sans-serif;font-weight:600}
.bildwahl select{width:100%;padding:8px;border:1px solid var(--linie);border-radius:8px;background:var(--grund);color:var(--text);font:inherit}
.bildnote{font-size:13px;color:var(--text-leise);margin:12px 0}
.btn{appearance:none;border:0;background:var(--pro);color:#fff;border-radius:8px;padding:10px 14px;font-weight:600;cursor:pointer}
.bildvorschau canvas{width:100%;height:auto;border:1px solid var(--linie);border-radius:8px;background:#fff}

.fuss{margin-top:44px;padding-top:20px;border-top:1px solid var(--linie);font-size:13.5px;color:var(--text-leise);line-height:1.55}
.fuss b{color:var(--text)} .fuss p{margin:0 0 10px}
.melden-inline{display:inline-flex;align-items:center;gap:6px;margin-left:10px;appearance:none;border:1px solid var(--linie);
  background:var(--karte);color:var(--text);border-radius:999px;padding:4px 11px;font-size:13px;cursor:pointer}
.melden-inline svg{width:14px;height:14px}

@media (max-width:720px){
  .wrap{padding:0 14px 70px}
  .kacheln{grid-template-columns:1fr 1fr 1fr;gap:8px} .kachel{padding:11px 12px}
  .kachel .s{display:none}
  .legenden{grid-template-columns:1fr}
  th.h,td.h{display:none}
  .bildbody{grid-template-columns:1fr}
  .bildknopf span{display:none} .bildknopf{padding:12px}
  #icicle text{font-size:10px}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
""" + IMPRESSUM_CSS + TESTPHASE_CSS + MELDEN_CSS

JS = r"""
(function(){
"use strict";
const D = JSON.parse(document.getElementById('daten').textContent);
const F = new Intl.NumberFormat('de-CH');
const JAHRE = D.jahre.map(j => j.k);
const titel = k => D.jahre.find(j => j.k === k).t;
const $ = s => document.querySelector(s);
const esc = t => String(t).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const kurz = (t, n) => t.length <= n ? t : t.slice(0, Math.max(n-1,1)).trimEnd() + '…';
const mio = v => (v/1e6).toLocaleString('de-CH', {minimumFractionDigits:1, maximumFractionDigits:1});
const fr  = v => F.format(Math.round(v));
const vz  = v => (v < 0 ? '−' : '+') + mio(Math.abs(v));
const farbe = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const rampe = n => farbe(n).split(',').map(s => s.trim());

/* Ein Datensatz heisst b26 (Budget 2026) oder r25 (Rechnung 2025). Oben waehlt man
   Jahr und Art getrennt, damit die Liste nicht mit jedem Jahr um zwei Eintraege
   waechst; unten den Vergleich, weil er nur dort wirkt. */
const artVon = k => k[0], jahrVon = k => 2000 + +k.slice(1);
const key = (art, jahr) => art + String(jahr).slice(2);
const JAHRZAHLEN = [...new Set(JAHRE.map(jahrVon))].sort();
function standardVergleich(k){
  const a = artVon(k), j = jahrVon(k);
  const kand = a === 'r' ? [key('b', j), key('r', j-1), key('b', j-1)]
                         : [key('r', j-1), key('b', j-1), key('r', j)];
  return kand.find(x => JAHRE.includes(x)) || JAHRE.find(x => x !== k);
}
let st = {jahr:'b26', vergleich:'r25', seite:'3', gliederung:'inst', pfad:[]};
st.vergleich = standardVergleich(st.jahr);

const ORDENTLICH = g => (g[0] === '3' || g[0] === '4') && !['38','39','48','49'].includes(g);
const nameSg = c => D.sg[c] ? c + ' ' + D.sg[c] : c;

/* ── Summen je zweistelliger Sachgruppe ─────────────────────────────────── */
function gruppen(k){
  const i = 5 + JAHRE.indexOf(k), g = {};
  for(const z of D.z){ const c = z[3].slice(0,2); g[c] = (g[c] || 0) + z[i]; }
  return g;
}
function kennzahlen(k){
  const g = gruppen(k);
  const auf = Object.entries(g).filter(([c]) => c[0]==='3' && ORDENTLICH(c)).reduce((s,[,v]) => s+v, 0);
  const ert = -Object.entries(g).filter(([c]) => c[0]==='4' && ORDENTLICH(c)).reduce((s,[,v]) => s+v, 0);
  const ao  = -((g['38']||0) + (g['48']||0));
  const ab  = -(g['90']||0);
  return {g, auf, ert, ord: ert - auf, ao, ab, gesamt: ert - auf + ao + ab};
}

/* ── Ueberblick: Woher, wohin ────────────────────────────────────────────── */
function zeichneUeberblick(){
  const K = kennzahlen(st.jahr), V = kennzahlen(st.vergleich);
  const tJ = titel(st.jahr), tV = titel(st.vergleich);
  $('#wwTitel').textContent = `· ${tJ}, ordentlicher Ertrag und Aufwand`;
  $('#kacheln').innerHTML =
    `<div class="kachel ert"><div class="z">${mio(K.ert)} Mio.</div><div class="l">Ertrag ${esc(tJ)}</div>
       <div class="s">${esc(tV)}: ${mio(V.ert)} Mio., also ${vz(K.ert - V.ert)}</div></div>
     <div class="kachel auf"><div class="z">${mio(K.auf)} Mio.</div><div class="l">Aufwand ${esc(tJ)}</div>
       <div class="s">${esc(tV)}: ${mio(V.auf)} Mio., also ${vz(K.auf - V.auf)}</div></div>
     <div class="kachel"><div class="z">${vz(K.gesamt)} Mio.</div><div class="l">${K.gesamt < 0 ? 'Defizit' : 'Überschuss'} ${esc(tJ)}</div>
       <div class="s">${esc(tV)}: ${vz(V.gesamt)} Mio.</div></div>`;

  const RA = rampe('--auf'), RE = rampe('--ert');
  const reihe = (praefix, ramp) => Object.entries(K.g)
    .filter(([c,v]) => c[0] === praefix && ORDENTLICH(c) && Math.abs(v) > 0)
    .map(([c,v]) => ({c, v:Math.abs(v)})).sort((a,b) => b.v - a.v)
    .map((x,i) => ({...x, f: ramp[Math.min(i, ramp.length-1)], hell: i >= 3}));
  const E = reihe('4', RE), A = reihe('3', RA);
  const skala = Math.max(K.auf, K.ert);
  const W = Math.max(300, Math.round($('#ww').clientWidth || 1000)), L = 0, R = W;
  const schmal = W < 640, H = schmal ? 40 : 44, Y1 = 22, Y2 = schmal ? 132 : 108;
  const bar = (liste, y, total) => {
    let x = L, s = '';
    for(const seg of liste){
      const b = (R-L) * seg.v / skala;
      const tx = seg.hell ? '#12161C' : '#FFFFFF';
      s += `<rect class="seg" x="${x.toFixed(1)}" y="${y}" width="${b.toFixed(1)}" height="${H}" fill="${seg.f}" rx="3" data-sg="${seg.c}"><title>${esc(nameSg(seg.c))}: ${mio(seg.v)} Mio. Fr., ${(100*seg.v/total).toFixed(1)} %</title></rect>`;
      if(b > 64){
        s += `<text class="in" x="${(x+7).toFixed(1)}" y="${y+17}" fill="${tx}">${esc(kurz(D.sg[seg.c]||seg.c, Math.floor(b/7)))}</text>`;
        s += `<text class="in" x="${(x+7).toFixed(1)}" y="${y+H-9}" fill="${tx}" opacity=".8" style="font-weight:400">${(100*seg.v/total).toFixed(0)} %</text>`;
      } else if(b > 28){
        s += `<text class="in" x="${(x+6).toFixed(1)}" y="${y+H/2+4}" fill="${tx}" opacity=".9" style="font-weight:400">${(100*seg.v/total).toFixed(0)} %</text>`;
      }
      x += b;
    }
    return s;
  };
  const xE = (R-L) * K.ert / skala, xA = (R-L) * K.auf / skala;
  const diff = K.ert - K.auf;
  const dx = Math.min(xE, xA), dw = Math.abs(xE - xA);
  let s = `<svg viewBox="0 0 ${W} ${Y2+H+6}" width="${W}" role="img" aria-label="Ertrag und Aufwand ${esc(tJ)} im Vergleich">`;
  s += `<text class="beschr" x="0" y="13">Woher · Ertrag ${mio(K.ert)} Mio.</text>` + bar(E, Y1, K.ert);
  s += `<text class="beschr" x="0" y="${Y2-9}">Wohin · Aufwand ${mio(K.auf)} Mio.</text>` + bar(A, Y2, K.auf);
  if(dw > 2){
    const lab = (diff < 0 ? `Ordentliches Defizit ${mio(-diff)}` : `Ordentlicher Überschuss ${mio(diff)}`) + ' Mio.';
    if(schmal){
      // Auf dem Telefon eine eigene Zeile zwischen den Balken, rechtsbuendig
      const yb = Y1 + H + 4, hb = 18;
      s += `<rect x="${dx.toFixed(1)}" y="${yb}" width="${dw.toFixed(1)}" height="${hb}" fill="none" stroke="${farbe('--text-leise')}" stroke-dasharray="3 3"/>`;
      s += `<text class="diffz" x="${R - 4}" y="${yb + hb + 20}" text-anchor="end">${lab}</text>`;
    } else {
      const yb = Y1 + H + 6, hb = Y2 - 14 - yb;
      s += `<rect x="${dx.toFixed(1)}" y="${yb}" width="${dw.toFixed(1)}" height="${hb}" fill="none" stroke="${farbe('--text-leise')}" stroke-dasharray="3 3"/>`;
      const breit = dw > 190, tx = breit ? dx + dw/2 : Math.max(dx - 6, 0);
      s += `<text class="diffz" x="${tx.toFixed(1)}" y="${yb + hb/2 + 5}" text-anchor="${breit ? 'middle' : 'end'}">${lab}</text>`;
    }
  }
  s += '</svg>';
  $('#ww').innerHTML = s;
  $('#ww').querySelectorAll('rect.seg').forEach(r => r.addEventListener('click', () => springe(r.dataset.sg)));

  const leg = (liste, total, klasse) => `<ol>` + liste.map(x =>
    `<li data-sg="${x.c}"><i style="background:${x.f}"></i>
       <span>${esc(D.sg[x.c]||x.c)}${D.erkl[x.c] ? `<small>${esc(D.erkl[x.c])}</small>` : ''}</span>
       <b>${mio(x.v)}<em>${(100*x.v/total).toFixed(1)} %</em></b></li>`).join('') + `</ol>`;
  $('#legenden').innerHTML =
    `<div class="legende"><h3>Woher das Geld kommt</h3>${leg(E, K.ert)}</div>
     <div class="legende"><h3>Wohin es geht</h3>${leg(A, K.auf)}</div>`;
  $('#legenden').querySelectorAll('li').forEach(li => li.addEventListener('click', () => springe(li.dataset.sg)));

  const aoText = K.ao ? ` ${K.ao > 0 ? 'Dazu kommen' : 'Davon gehen ab'} ${mio(Math.abs(K.ao))} Mio. ${K.ao > 0 ? 'ausserordentlicher Ertrag, vor allem Entnahmen aus Reserven' : 'ausserordentlicher Aufwand, vor allem Einlagen in Reserven'}.` : '';
  const abText = K.ab ? ` Fondsabschlüsse ${vz(K.ab)} Mio.` : '';
  $('#ergebnis').innerHTML =
    `Ordentlicher Ertrag <b>${mio(K.ert)}</b> minus ordentlicher Aufwand <b>${mio(K.auf)}</b> ergibt <b>${vz(K.ord)} Mio.</b>${esc(aoText)}${esc(abText)}
     Gesamtergebnis <b>${vz(K.gesamt)} Mio. Franken</b>${K.gesamt < 0 ? ', ein Aufwandüberschuss' : ', ein Ertragsüberschuss'}.
     Interne Verrechnungen (${mio(Math.abs(K.g['39']||0))} Mio.) stehen auf beiden Seiten gleich und sind hier weggelassen.`;
}

/* Aus der Uebersicht in den Drilldown der Sachgruppe springen */
function springe(sg){
  st.seite = sg[0]; st.gliederung = 'art'; st.pfad = ['a' + sg];
  chipsSetzen();
  zeichneDrill();
  $('#drill').scrollIntoView({behavior:'smooth', block:'start'});
}

/* ── Drilldown ───────────────────────────────────────────────────────────── */
function baum(){
  const i = 5 + JAHRE.indexOf(st.jahr), iv = 5 + JAHRE.indexOf(st.vergleich);
  const wurzel = {id:'', name: st.seite === '3' ? 'Gesamter Aufwand' : 'Gesamter Ertrag', wert:0, vgl:0, kinder:new Map()};
  for(const z of D.z){
    const [dep, dst, spz, konto, bez] = z;
    if(konto[0] !== st.seite || !ORDENTLICH(konto.slice(0,2))) continue;
    const vzf = st.seite === '4' ? -1 : 1;           // Ertrag steht in den Daten negativ
    const w = vzf * z[i], v = vzf * z[iv];
    if(!w && !v) continue;
    const pfad = st.gliederung === 'inst'
      ? [['d'+dep, D.dep[dep]||dep], ['s'+dst, D.dst[dst] || ('Dienststelle ' + dst)]]
          .concat(spz ? [['f'+spz, D.spz[spz]||spz]] : []).concat([['k'+konto, bez]])
      : [['a'+konto.slice(0,2), nameSg(konto.slice(0,2))], ['b'+konto.slice(0,3), nameSg(konto.slice(0,3))], ['k'+konto, bez]];
    let n = wurzel; n.wert += w; n.vgl += v;
    for(const [id, name] of pfad){
      if(!n.kinder.has(id)) n.kinder.set(id, {id, name, wert:0, vgl:0, kinder:new Map()});
      n = n.kinder.get(id); n.wert += w; n.vgl += v;
    }
  }
  const sortiere = n => { n.kinder = [...n.kinder.values()].sort((a,b) => b.wert - a.wert); n.kinder.forEach(sortiere); return n; };
  return sortiere(wurzel);
}
/* Fuer Flaechen zaehlen nur positive Betraege; Minusposten (Rueckerstattungen auf der
   Aufwandseite, Ertragsminderungen auf der Ertragsseite) stehen in der Tabelle mit
   Vorzeichen und ohne Balken. Die Summen bleiben die gedruckten. */
const pos = v => Math.max(0, v);
function kette(wurzel){
  let n = wurzel, k = [n];
  for(const id of st.pfad){ const c = n.kinder.find(x => x.id === id); if(!c) break; n = c; k.push(n); }
  st.pfad = k.slice(1).map(x => x.id);
  return k;
}
function zeichneIcicle(k){
  const W = Math.max(300, Math.round(($('#icicle').parentElement.clientWidth || 1000))), H = 32, G = 3, start = k[k.length-1];
  const ramp = st.seite === '3' ? rampe('--auf') : rampe('--ert');
  let ebenen = [[{n:start, x0:0, x1:W}]], reihe = ebenen[0];
  for(let t = 0; t < 2; t++){
    const nx = [];
    for(const {n, x0, x1} of reihe){
      const summe = n.kinder.reduce((s,c) => s + pos(c.wert), 0); if(!summe) continue;
      let x = x0;
      for(const c of n.kinder){ const b = (x1-x0) * pos(c.wert) / summe; if(b > 0.4) nx.push({n:c, x0:x, x1:x+b}); x += b; }
    }
    if(!nx.length) break; ebenen.push(nx); reihe = nx;
  }
  const hoehe = ebenen.length * (H+G) - G;
  let s = `<svg id="icicle" viewBox="0 0 ${W} ${hoehe}" width="${W}" height="${hoehe}" role="img" aria-label="Aufteilung nach Ebenen">`;
  ebenen.forEach((reihe, i) => {
    const y = i * (H+G);
    reihe.forEach(seg => {
      const b = seg.x1 - seg.x0;
      const f = i === 0 ? farbe('--text') : ramp[i === 1 ? 0 : 2];
      const tx = i === 0 ? farbe('--grund') : '#FFFFFF';
      s += `<rect x="${seg.x0.toFixed(2)}" y="${y}" width="${Math.max(b-0.6,0.4).toFixed(2)}" height="${H}" fill="${f}" rx="2" data-tiefe="${st.pfad.length + i}" data-id="${seg.n.id}"><title>${esc(seg.n.name)}: ${mio(seg.n.wert)} Mio. Fr.</title></rect>`;
      if(b > 62){
        s += `<text x="${(seg.x0+6).toFixed(2)}" y="${y+12.5}" fill="${tx}" font-weight="600">${esc(kurz(seg.n.name, Math.floor(b/6.2)))}</text>`;
        if(b > 110) s += `<text x="${(seg.x0+6).toFixed(2)}" y="${y+24}" fill="${tx}" opacity=".78">${mio(seg.n.wert)} Mio.</text>`;
      }
    });
  });
  $('#icicle').outerHTML = s + '</svg>';
  document.querySelectorAll('#icicle rect').forEach(r => r.addEventListener('click', () => {
    const t = +r.dataset.tiefe; if(t === st.pfad.length) return;
    st.pfad = st.pfad.slice(0, t).concat(r.dataset.id); zeichneDrill();
  }));
}
function zeichneDrill(){
  const wurzel = baum(), k = kette(wurzel), jetzt = k[k.length-1];
  const tJ = titel(st.jahr), tV = titel(st.vergleich);
  $('#drill').classList.toggle('ertrag', st.seite === '4');
  $('#krume').innerHTML = k.map((n,i) => i === k.length-1
    ? `<span class="jetzt">${esc(n.name)}</span>`
    : `<button data-i="${i}">${esc(n.name)}</button><span>›</span>`).join('');
  $('#krume').querySelectorAll('button').forEach(b => b.addEventListener('click', () => { st.pfad = st.pfad.slice(0, +b.dataset.i); zeichneDrill(); }));
  const anteil = wurzel.wert ? 100*jetzt.wert/wurzel.wert : 0, d = jetzt.wert - jetzt.vgl;
  $('#dkopf').innerHTML =
    `<div><div class="betrag">${mio(jetzt.wert)} Mio. Fr.</div><div class="neben">${esc(tJ)}${k.length > 1 ? `, ${anteil.toFixed(1)} % des ${st.seite==='3'?'Aufwands':'Ertrags'}` : ''}</div></div>
     <div class="neben">${esc(tV)}: ${mio(jetzt.vgl)} Mio.${jetzt.vgl ? ` (${vz(d)} Mio., ${d>=0?'+':'−'}${Math.abs(100*d/jetzt.vgl).toFixed(1)} %)` : ''}</div>`;
  zeichneIcicle(k);
  const t = $('#tabelle');
  if(!jetzt.kinder.length){ t.innerHTML = `<div class="leer">Unterste Ebene: Konto ${esc(jetzt.id.slice(1))}.</div>`; return; }
  const kopf = k.length === 1 ? (st.gliederung === 'inst' ? 'Departement' : 'Sachgruppe')
             : st.gliederung === 'inst' ? (jetzt.id[0] === 'd' ? 'Dienststelle' : jetzt.id[0] === 's' && jetzt.kinder[0].id[0] === 'f' ? 'Fonds / Konto' : 'Konto')
             : (jetzt.id[0] === 'a' ? 'Sachgruppe' : 'Konto');
  const max = Math.max(1, ...jetzt.kinder.map(c => pos(c.wert)));
  t.innerHTML = `<table><thead><tr><th>${kopf}</th><th class="r">${esc(tJ)}</th><th class="r">Anteil</th><th class="r h">${esc(tV)}</th><th class="r h">Differenz</th></tr></thead><tbody>`
    + jetzt.kinder.map(c => {
        const dd = c.wert - c.vgl, kl = dd > 0 ? 'plus' : dd < 0 ? 'minus' : '';
        return `<tr class="${c.kinder.length ? 'klick' : ''}" data-id="${c.id}">
          <td>${c.id[0] === 'k' ? `<span class="nr">${esc(c.id.slice(1))}</span>` : ''}${esc(c.name)}${c.wert > 0 ? `<span class="balken" style="width:${(100*c.wert/max).toFixed(1)}%"></span>` : ''}</td>
          <td class="r">${fr(c.wert)}</td><td class="r">${(jetzt.wert ? 100*c.wert/jetzt.wert : 0).toFixed(1)} %</td>
          <td class="r h">${fr(c.vgl)}</td><td class="r h ${kl}">${dd ? (dd>0?'+':'−') + fr(Math.abs(dd)) : '–'}</td></tr>`;
      }).join('') + '</tbody></table>';
  t.querySelectorAll('tr.klick').forEach(tr => tr.addEventListener('click', () => { st.pfad = st.pfad.concat(tr.dataset.id); zeichneDrill(); }));
}

/* ── Steuerung ───────────────────────────────────────────────────────────── */
function chipsSetzen(){
  const a = artVon(st.jahr), j = jahrVon(st.jahr);
  $('#jahrChips').innerHTML = JAHRZAHLEN.map(y => {
    const da = JAHRE.includes(key(a, y)) || JAHRE.includes(key(a === 'b' ? 'r' : 'b', y));
    return `<button type="button" data-feld="jahrzahl" data-wert="${y}" aria-pressed="${y === j}" ${da ? '' : 'disabled'}>${y}</button>`;
  }).join('');
  $('#artChips').innerHTML = [['b','Budget'],['r','Rechnung']].map(([k,t]) => {
    const da = JAHRE.includes(key(k, j));
    return `<button type="button" data-feld="art" data-wert="${k}" aria-pressed="${k === a}" ${da ? '' : 'disabled'} title="${da ? '' : t + ' ' + j + ' liegt noch nicht vor'}">${t}</button>`;
  }).join('');
  $('#vglChips').innerHTML = JAHRE.filter(k => k !== st.jahr).map(k =>
    `<button type="button" data-feld="vergleich" data-wert="${k}" aria-pressed="${k === st.vergleich}">${esc(titel(k))}</button>`).join('');
  document.querySelectorAll('.chips button[data-feld="seite"],.chips button[data-feld="gliederung"]')
    .forEach(b => b.setAttribute('aria-pressed', st[b.dataset.feld] === b.dataset.wert));
}
document.addEventListener('click', ev => {
  const b = ev.target.closest('.chips button'); if(!b || b.disabled) return;
  const f = b.dataset.feld, w = b.dataset.wert;
  if(f === 'jahrzahl'){
    const a = artVon(st.jahr), neu = JAHRE.includes(key(a, w)) ? key(a, w) : key(a === 'b' ? 'r' : 'b', w);
    if(neu === st.jahr) return; st.jahr = neu; st.vergleich = standardVergleich(neu);
  } else if(f === 'art'){
    const neu = key(w, jahrVon(st.jahr)); if(neu === st.jahr || !JAHRE.includes(neu)) return;
    st.jahr = neu; st.vergleich = standardVergleich(neu);
  } else {
    if(st[f] === w) return; st[f] = w;
    if(f === 'seite' || f === 'gliederung') st.pfad = [];
  }
  chipsSetzen(); zeichneUeberblick(); zeichneDrill();
});

/* ── Suche ───────────────────────────────────────────────────────────────── */
/* Ein Treffer ist ein Knoten des Drilldowns: Departement, Dienststelle, Fonds,
   Sachgruppe oder Konto. Anwaehlen setzt Ansicht, Gliederung und Pfad und springt
   hin. Gesucht wird in Namen und Kontonummern; Umlaute und Gross-/Kleinschreibung
   sind egal. Gewicht: erst die Ebene (grob vor fein), dann Wortanfang, dann Betrag. */
const SYNONYME = [['Lehrer', 'Lehrpersonen'], ['Schule', 'Schul'], ['Spital', 'Spitalversorgung'],
  ['Polizei', 'Polizei'], ['Steuern', 'Steuer'], ['Axpo', 'Beteiligungen'], ['Krankenkasse', 'Prämienverbilligung'],
  ['Flüchtlinge', 'Flüchtling'], ['Gefängnis', 'Justizvollzug'], ['Bahn', 'Öffentlicher Verkehr'], ['Kindergarten', 'Kindergärten']];
const norm = t => String(t).toLowerCase().replace(/ä/g,'ae').replace(/ö/g,'oe').replace(/ü/g,'ue').replace(/ß/g,'ss');
let sucheIndex = null, sucheJahr = null;
function baueSucheIndex(){
  const i = 5 + JAHRE.indexOf(st.jahr), m = new Map();
  const add = (schl, o, w) => { const e = m.get(schl); if(e) e.wert += w; else m.set(schl, {...o, wert:w}); };
  for(const z of D.z){
    const [dep, dst, spz, konto, bez] = z;
    const seite = konto[0]; if(!'34'.includes(seite) || !ORDENTLICH(konto.slice(0,2))) continue;
    const w = (seite === '4' ? -1 : 1) * z[i]; if(!w) continue;
    const dn = D.dep[dep] || dep, sn = D.dst[dst] || ('Dienststelle ' + dst);
    add(`${seite}|d${dep}`, {typ:'Departement', name:dn, kontext:'', seite, gl:'inst', pfad:['d'+dep]}, w);
    add(`${seite}|s${dst}`, {typ:'Dienststelle', name:sn, kontext:dn, seite, gl:'inst', pfad:['d'+dep,'s'+dst]}, w);
    if(spz) add(`${seite}|f${spz}`, {typ:'Fonds', name:D.spz[spz]||spz, kontext:`${dn} › ${sn}`, seite, gl:'inst', pfad:['d'+dep,'s'+dst,'f'+spz]}, w);
    const kp = ['d'+dep,'s'+dst].concat(spz ? ['f'+spz] : []).concat(['k'+konto]);
    add(`${seite}|${kp.join('/')}`, {typ:'Konto', name:`${konto} ${bez}`, kontext:(spz ? D.spz[spz] : sn), seite, gl:'inst', pfad:kp}, w);
    const a = konto.slice(0,2), b = konto.slice(0,3);
    add(`${seite}|a${a}`, {typ:'Sachgruppe', name:nameSg(a), kontext:seite === '3' ? 'Aufwand' : 'Ertrag', seite, gl:'art', pfad:['a'+a]}, w);
    add(`${seite}|b${b}`, {typ:'Sachgruppe', name:nameSg(b), kontext:nameSg(a), seite, gl:'art', pfad:['a'+a,'b'+b]}, w);
  }
  const GEW = {Departement:0, Dienststelle:1, Fonds:1, Sachgruppe:2, Konto:3};
  // Durchsucht wird der Name, bei zweistelligen Sachgruppen auch die Erklaerung
  // («Axpo» findet so den Finanzertrag), und Umgangsbegriffe aus der Liste SYNONYME.
  sucheIndex = [...m.values()].map(o => {
    let n = norm(o.name);
    if(o.typ === 'Sachgruppe' && o.pfad.length === 1) n += ' ' + norm(D.erkl[o.pfad[0].slice(1)] || '');
    for(const [von, zu] of SYNONYME) if(n.includes(norm(zu))) n += ' ' + norm(von);
    return {...o, n, gew: GEW[o.typ]};
  });
  sucheJahr = st.jahr;
}
function suche(text){
  if(sucheJahr !== st.jahr || !sucheIndex) baueSucheIndex();
  const q = norm(text.trim()); if(q.length < 2) return [];
  const woerter = q.split(/\s+/);
  return sucheIndex
    .filter(o => woerter.every(w => o.n.includes(w)))
    .map(o => ({o, anfang: o.n.startsWith(q) || o.n.includes(' ' + q) ? 0 : 1}))
    .sort((x,y) => x.o.gew - y.o.gew || x.anfang - y.anfang || Math.abs(y.o.wert) - Math.abs(x.o.wert))
    .slice(0, 12).map(x => x.o);
}
function zeigeSuche(){
  const liste = $('#sucheListe'), text = $('#sucheFeld').value;
  const tr = suche(text);
  if(text.trim().length < 2){ liste.hidden = true; liste.innerHTML = ''; return; }
  liste.hidden = false;
  liste.innerHTML = tr.length ? tr.map((o,i) =>
    `<li role="option" data-i="${i}" aria-selected="${i === 0}"><span>${esc(o.name)}</span><b>${mio(o.wert)} Mio.</b>
      <span class="art"><em>${esc(o.typ)}</em>${o.seite === '3' ? 'Aufwand' : 'Ertrag'}${o.kontext ? ' · ' + esc(o.kontext) : ''}</span></li>`).join('')
    : `<li class="leer">Nichts gefunden. Gesucht wird in Bezeichnungen und Kontonummern des gewählten Jahres.</li>`;
  liste.querySelectorAll('li[data-i]').forEach(li => li.addEventListener('mousedown', ev => { ev.preventDefault(); waehle(tr[+li.dataset.i]); }));
  liste._treffer = tr;
}
function waehle(o){
  if(!o) return;
  st.seite = o.seite; st.gliederung = o.gl; st.pfad = o.pfad.slice();
  $('#sucheListe').hidden = true; $('#sucheFeld').value = o.name; $('#sucheFeld').blur();
  chipsSetzen(); zeichneDrill();
  $('#drill-titel').scrollIntoView({behavior:'smooth', block:'start'});
}
$('#sucheFeld').addEventListener('input', zeigeSuche);

$('#sucheFeld').addEventListener('focus', zeigeSuche);
$('#sucheFeld').addEventListener('blur', () => setTimeout(() => { $('#sucheListe').hidden = true; }, 150));
$('#sucheFeld').addEventListener('keydown', ev => {
  const liste = $('#sucheListe'), tr = liste._treffer || [];
  const akt = [...liste.querySelectorAll('li[data-i]')].findIndex(li => li.getAttribute('aria-selected') === 'true');
  if(ev.key === 'ArrowDown' || ev.key === 'ArrowUp'){
    ev.preventDefault(); if(!tr.length) return;
    const neu = (akt + (ev.key === 'ArrowDown' ? 1 : -1) + tr.length) % tr.length;
    liste.querySelectorAll('li[data-i]').forEach((li,i) => li.setAttribute('aria-selected', i === neu));
    liste.querySelectorAll('li[data-i]')[neu].scrollIntoView({block:'nearest'});
  } else if(ev.key === 'Enter'){ ev.preventDefault(); waehle(tr[Math.max(akt,0)]); }
  else if(ev.key === 'Escape'){ liste.hidden = true; }
});

/* ── Bild fuer Social Media ──────────────────────────────────────────────── */
const BW = 1080, BH = 1350;
function bildRahmen(x, ink, ink3, line){
  x.fillStyle = ink; x.font = "700 30px Archivo, sans-serif"; x.fillText("KANTON SCHAFFHAUSEN", 72, 96);
  x.fillStyle = ink3; x.font = "600 21px 'Public Sans', sans-serif"; x.fillText("FINANZSPIEGEL", 72, 130);
  x.strokeStyle = ink; x.lineWidth = 3; x.beginPath(); x.moveTo(72, 156); x.lineTo(BW-72, 156); x.stroke();
  x.strokeStyle = line; x.lineWidth = 1; x.beginPath(); x.moveTo(72, BH-132); x.lineTo(BW-72, BH-132); x.stroke();
  x.fillStyle = ink; x.font = "700 22px 'Public Sans', sans-serif"; x.fillText("Politspiegel Schaffhausen · Finanzspiegel", 72, BH-92);
  x.fillStyle = ink3; x.font = "400 18px 'Public Sans', sans-serif"; x.fillText("Daten: Budget und Staatsrechnung, Finanzverwaltung Kanton Schaffhausen", 72, BH-62);
}
function bildBalken(x, y, name, wert, max, f, ink, ink3, sub){
  x.fillStyle = ink; x.font = "600 24px 'Public Sans', sans-serif"; x.fillText(kurz(name, 46), 72, y);
  x.fillStyle = ink3; x.font = "400 20px 'Public Sans', sans-serif"; x.textAlign = "right"; x.fillText(sub, BW-72, y); x.textAlign = "left";
  const b = Math.max(6, (BW-144) * wert / max);
  x.fillStyle = f; x.fillRect(72, y+12, b, 14);
}
function malen(motiv){
  const c = $('#bildCanvas'), x = c.getContext('2d');
  const bg = farbe('--karte'), ink = farbe('--text'), ink3 = farbe('--text-leise'), line = farbe('--linie');
  x.fillStyle = bg; x.fillRect(0, 0, BW, BH);
  bildRahmen(x, ink, ink3, line);
  const tJ = titel(st.jahr);
  if(motiv === 'ueberblick'){
    const K = kennzahlen(st.jahr);
    x.fillStyle = ink; x.font = "700 44px Archivo, sans-serif"; x.fillText("Wohin das Geld des Kantons fliesst", 72, 236);
    x.fillStyle = ink3; x.font = "400 24px 'Public Sans', sans-serif"; x.fillText(`${tJ}, ordentlicher Ertrag und Aufwand`, 72, 276);
    const RA = rampe('--auf'), RE = rampe('--ert');
    const reihe = (p, ramp) => Object.entries(K.g).filter(([c,v]) => c[0]===p && ORDENTLICH(c) && Math.abs(v) > 0)
      .map(([c,v]) => ({c, v:Math.abs(v)})).sort((a,b) => b.v-a.v).map((s,i) => ({...s, f: ramp[Math.min(i, ramp.length-1)]}));
    const skala = Math.max(K.auf, K.ert);
    const streifen = (liste, y, total, label) => {
      x.fillStyle = ink3; x.font = "600 19px Archivo, sans-serif"; x.fillText(label.toUpperCase(), 72, y-12);
      let px = 72;
      for(const s of liste){ const b = (BW-144) * s.v / skala; x.fillStyle = s.f; x.fillRect(px, y, Math.max(b-2,1), 54); px += b; }
      let yy = y + 90;
      for(const s of liste.slice(0,6)){
        x.fillStyle = s.f; x.fillRect(72, yy-18, 20, 20);
        x.fillStyle = ink; x.font = "500 24px 'Public Sans', sans-serif"; x.fillText(kurz(D.sg[s.c]||s.c, 32), 106, yy);
        x.font = "600 24px 'Public Sans', sans-serif"; x.textAlign = "right"; x.fillText(`${mio(s.v)} Mio.  ${(100*s.v/total).toFixed(0)} %`, BW-72, yy); x.textAlign = "left";
        yy += 40;
      }
      return yy;
    };
    let y = streifen(reihe('4', RE), 340, K.ert, `Woher · Ertrag ${mio(K.ert)} Mio.`);
    y = streifen(reihe('3', RA), y + 44, K.auf, `Wohin · Aufwand ${mio(K.auf)} Mio.`);
    y = Math.min(y + 30, BH - 200);
    x.fillStyle = ink; x.font = "700 36px Archivo, sans-serif";
    x.fillText(`${K.gesamt < 0 ? 'Defizit' : 'Überschuss'} ${mio(Math.abs(K.gesamt))} Mio. Franken`, 72, y);
    x.fillStyle = ink3; x.font = "400 21px 'Public Sans', sans-serif";
    x.fillText(`Ordentlich ${vz(K.ord)} Mio.${K.ao ? `, ausserordentlich ${vz(K.ao)} Mio.` : ''}${K.ab ? `, Fondsabschlüsse ${vz(K.ab)} Mio.` : ''}`, 72, y + 34);
  } else if(motiv === 'kuchen'){
    bildKuchen(x, ink, ink3, line, tJ);
  } else {
    const wurzel = baum(), k = kette(wurzel), jetzt = k[k.length-1];
    const ramp = st.seite === '3' ? rampe('--auf') : rampe('--ert');
    const pfadText = k.slice(0, -1).map(n => n.name).join(' › ');
    x.fillStyle = ink3; x.font = "400 22px 'Public Sans', sans-serif"; if(pfadText) x.fillText(kurz(pfadText, 70), 72, 214);
    x.fillStyle = ink; x.font = "700 42px Archivo, sans-serif";
    const zeilen = umbruch(x, jetzt.name, BW-144); let y = 262;
    for(const z of zeilen.slice(0,2)){ x.fillText(z, 72, y); y += 48; }
    x.fillStyle = ramp[0]; x.font = "700 40px Archivo, sans-serif"; x.fillText(`${mio(jetzt.wert)} Mio. Franken`, 72, y + 6);
    x.fillStyle = ink3; x.font = "400 22px 'Public Sans', sans-serif"; x.fillText(`${tJ}, ${st.seite === '3' ? 'Aufwand' : 'Ertrag'}${k.length > 1 ? `, ${(100*jetzt.wert/wurzel.wert).toFixed(1)} % des Totals` : ''}`, 72, y + 42);
    y += 100;
    const kinder = jetzt.kinder.slice(0, 11); const rest = jetzt.kinder.slice(11).reduce((s,c) => s + c.wert, 0);
    const max = kinder.length ? kinder[0].wert : 1;
    for(const c of kinder){ bildBalken(x, y, c.name, c.wert, max, ramp[0], ink, ink3, `${mio(c.wert)} Mio.  ${(100*c.wert/jetzt.wert).toFixed(1)} %`); y += 58; }
    if(rest > 0) bildBalken(x, y, `Übrige ${jetzt.kinder.length - 11}`, rest, max, ramp[3], ink, ink3, `${mio(rest)} Mio.  ${(100*rest/jetzt.wert).toFixed(1)} %`);
  }
}
/* Kuchen: die Kinder der geoeffneten Ebene als Ring, die sieben groessten einzeln,
   der Rest als «Uebrige». Prozent im Ring ab 6 %, Legende darunter mit Betrag.
   Steht man auf einem Konto, gibt es keine Kinder; dann zeigt der Kuchen die
   Ebene darueber. */
function bildKuchen(x, ink, ink3, line, tJ){
  const wurzel = baum(), k = kette(wurzel);
  let jetzt = k[k.length-1], eltern = k.length > 1 ? k[k.length-2] : null;
  if(!jetzt.kinder.length && eltern){ jetzt = eltern; }
  const ramp = st.seite === '3' ? rampe('--auf') : rampe('--ert');
  const FARBEN = st.seite === '3'
    ? ['#0F766E','#3FB3A8','#1E5F7A','#6FB8D9','#2C3440','#8FD4B8','#0C4A44']
    : ['#7E3C9A','#C08AD8','#B44A6E','#E0A0B8','#2C3440','#D9B8E8','#4E2461'];
  const GRAU = farbe('--linie');
  const kinder = jetzt.kinder.filter(c => c.wert > 0);
  const total = kinder.reduce((s,c) => s + c.wert, 0);
  // Sieben einzeln, der Rest gesammelt; ein einzelner Rest wird selbst gezeigt.
  const n = kinder.length <= 8 ? kinder.length : 7;
  const top = kinder.slice(0, n), rest = kinder.slice(n).reduce((s,c) => s + c.wert, 0);
  const teile = top.map((c,i) => ({name:c.name, wert:c.wert, f:FARBEN[i % FARBEN.length]}));
  if(rest > 0) teile.push({name:`Übrige ${kinder.length - n}`, wert:rest, f:GRAU, grau:true});

  // Titel
  const pfadText = k.slice(0, -1).filter(n => n !== jetzt).map(n => n.name).join(' › ');
  x.fillStyle = ink3; x.font = "400 22px 'Public Sans', sans-serif";
  if(pfadText) x.fillText(kurz(pfadText, 70), 72, 214);
  x.fillStyle = ink; x.font = "700 40px Archivo, sans-serif";
  const titelZ = umbruch(x, k.length === 1 ? (st.seite === '3' ? 'Wohin das Geld geht' : 'Woher das Geld kommt') : jetzt.name, BW-144);
  let y = 262; for(const z of titelZ.slice(0,2)){ x.fillText(z, 72, y); y += 46; }
  x.fillStyle = ink3; x.font = "400 22px 'Public Sans', sans-serif";
  x.fillText(`${tJ}, ${st.seite === '3' ? 'Aufwand' : 'Ertrag'}, ${mio(total)} Mio. Franken`, 72, y + 4);

  // Ring
  const cx = BW/2, cy = y + 300, R = 250, r = 150;
  let a = -Math.PI/2;
  for(const t of teile){
    const w = 2*Math.PI * t.wert / total;
    x.beginPath(); x.arc(cx, cy, R, a, a+w); x.arc(cx, cy, r, a+w, a, true); x.closePath();
    x.fillStyle = t.f; x.fill();
    x.strokeStyle = farbe('--karte'); x.lineWidth = 3; x.stroke();
    if(t.wert / total >= 0.06){
      const m = a + w/2, rx = cx + Math.cos(m) * (R+r)/2, ry = cy + Math.sin(m) * (R+r)/2;
      x.fillStyle = t.grau ? ink : '#FFFFFF'; x.font = "700 24px 'Public Sans', sans-serif";
      x.textAlign = "center"; x.textBaseline = "middle";
      x.fillText(`${(100*t.wert/total).toFixed(0)} %`, rx, ry);
      x.textAlign = "left"; x.textBaseline = "alphabetic";
    }
    a += w;
  }
  x.fillStyle = ink; x.font = "700 40px Archivo, sans-serif"; x.textAlign = "center";
  x.fillText(`${mio(total)}`, cx, cy + 4);
  x.fillStyle = ink3; x.font = "400 20px 'Public Sans', sans-serif"; x.fillText("Mio. Franken", cx, cy + 34);
  x.textAlign = "left";

  // Legende, zwei Spalten
  let ly = cy + R + 56; const spalte = (BW - 144) / 2;
  teile.forEach((t, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const lx = 72 + col * spalte, yy = ly + row * 52;
    x.fillStyle = t.f; x.fillRect(lx, yy - 18, 20, 20);
    if(t.grau){ x.strokeStyle = ink3; x.lineWidth = 1; x.strokeRect(lx, yy - 18, 20, 20); }
    x.fillStyle = ink; x.font = "600 20px 'Public Sans', sans-serif"; x.fillText(kurz(t.name, 34), lx + 32, yy);
    x.fillStyle = ink3; x.font = "400 19px 'Public Sans', sans-serif";
    x.fillText(`${mio(t.wert)} Mio. · ${(100*t.wert/total).toFixed(1)} %`, lx + 32, yy + 24);
  });
}
function umbruch(x, text, breite){
  const w = text.split(' '), out = []; let z = '';
  for(const t of w){ const p = z ? z + ' ' + t : t; if(x.measureText(p).width > breite && z){ out.push(z); z = t; } else z = p; }
  if(z) out.push(z); return out;
}
$('#bildAuf').addEventListener('click', () => { $('#bildLage').classList.add('offen'); malen($('#bildMotiv').value); });
$('#bildZu').addEventListener('click', () => $('#bildLage').classList.remove('offen'));
$('#bildLage').addEventListener('click', ev => { if(ev.target === $('#bildLage')) $('#bildLage').classList.remove('offen'); });
$('#bildMotiv').addEventListener('change', () => malen($('#bildMotiv').value));
$('#bildLaden').addEventListener('click', () => {
  const a = document.createElement('a');
  a.download = `finanzspiegel-${st.jahr}-${$('#bildMotiv').value}.png`;
  a.href = $('#bildCanvas').toDataURL('image/png'); a.click();
});
document.fonts && document.fonts.ready.then(() => { if($('#bildLage').classList.contains('offen')) malen($('#bildMotiv').value); });

chipsSetzen(); zeichneUeberblick(); zeichneDrill();
let rz; window.addEventListener('resize', () => { clearTimeout(rz); rz = setTimeout(() => { zeichneUeberblick(); zeichneDrill(); }, 150); });
})();
"""


def chips(feld: str, eintraege: list[tuple[str, str]], aktiv: str, klasse: str = "") -> str:
    return f'<div class="chips {klasse}">' + "".join(
        f'<button type="button" data-feld="{feld}" data-wert="{e(k)}" aria-pressed="{str(k == aktiv).lower()}">{e(t)}</button>'
        for k, t in eintraege) + "</div>"


def seite(daten: dict) -> str:
    jahre = [(j["k"], j["t"]) for j in daten["jahre"]]
    daten_json = json.dumps(daten, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    return f"""<!DOCTYPE html>
<html lang="de-CH">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Finanzspiegel Schaffhausen</title>
<meta name="description" content="Budget und Staatsrechnung des Kantons Schaffhausen: woher das Geld kommt, wohin es geht, bis zum einzelnen Konto.">
<link rel="icon" href="../favicon.svg" type="image/svg+xml">
<link rel="icon" href="../favicon.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="../apple-touch-icon.png">
<meta name="theme-color" content="#0B0F14">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700&family=Public+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
{testphase_html("oben-rechts")}
<div class="wrap">
<header class="kopf">
  <a class="zurueck" href="../">&larr; Politspiegel Schaffhausen</a>
  <div class="marke">Finanzspiegel</div>
  <h1>Wohin das Geld des Kantons fliesst</h1>
  <p class="lead">Budget und Staatsrechnung des Kantons Schaffhausen, vom Gesamtbild bis zum einzelnen Konto.
  Zwei Balken zeigen, woher das Geld kommt und wohin es geht; darunter geht jeder Klick eine Stufe tiefer.</p>
</header>

<div class="steuer steuer-oben">
  <div class="grp"><b>Jahr</b><div class="chips" id="jahrChips"></div></div>
  <div class="grp"><b>Budget oder Rechnung</b><div class="chips" id="artChips"></div></div>
  <div class="grp suche"><label for="sucheFeld"><b>Suche</b></label>
    <div class="suchbox">
      <input id="sucheFeld" type="search" autocomplete="off" spellcheck="false"
        placeholder="Dienststelle, Konto, Sachgruppe oder Fonds">
      <ul id="sucheListe" role="listbox" hidden></ul>
    </div>
  </div>
</div>

<h2>Woher, wohin <small id="wwTitel"></small></h2>
<div class="kacheln" id="kacheln"></div>
<div class="karte ww">
  <div id="ww"></div>
  <div class="legenden" id="legenden"></div>
  <p class="ergebnis" id="ergebnis"></p>
</div>

<h2 id="drill-titel">Im Detail <small>· Klick auf ein Feld oder eine Zeile geht eine Stufe tiefer</small></h2>
<div id="drill">
<div class="steuer">
  <div class="grp"><b>Ansicht</b>{chips("seite", [("3", "Aufwand"), ("4", "Ertrag")], "3")}</div>
  <div class="grp"><b>Gliederung</b>{chips("gliederung", [("inst", "Dienststelle"), ("art", "Sachgruppe")], "inst")}</div>
  <div class="grp"><b>Vergleich mit</b><div class="chips" id="vglChips"></div></div>
</div>
<div class="krume" id="krume"></div>
<div class="karte">
  <div class="dkopf" id="dkopf"></div>
  <svg id="icicle"></svg>
</div>
<div class="karte" id="tabelle"></div>
</div>

<footer class="fuss">
<p><b>Quellen.</b> Kanton Schaffhausen, Bericht und Antrag des Regierungsrates zum Budget 2026 vom 26. August 2025
und Staatsrechnung 2025, je Kapitel 6 Detailzahlen, Erfolgsrechnung. Die Zahlen sind aus den PDF ausgelesen. Die Summen
je Dienststelle, Fonds und Departement stimmen mit den gedruckten überein, die Totale mit Kapitel 1.7 des Berichts
(ordentlicher Aufwand 1'156.5, ordentlicher Ertrag 1'063.8 Mio.) und die Ergebnisse mit den ausgewiesenen:
Budget 2025 −49.0, Rechnung 2025 +14.9, Budget 2026 −49.6 Mio. Franken.</p>
<p><b>Lesehilfe.</b> Aufwand und Ertrag stehen getrennt, weil Flächen nicht negativ sein können. Gezeigt ist das
Ordentliche; ausserordentliche Reservebewegungen und Fondsabschlüsse rechnet der Überblick vor, interne
Verrechnungen stehen auf beiden Seiten gleich und sind weggelassen. Die Sachgruppen folgen dem Kontenrahmen HRM2.
Kreditrechtlich verbindlich ist die Gliederung nach Dienststelle.</p>
<p><b>Stand</b> {e(daten["stand"])}. Aufbereitung ohne Gewähr. {melden_knopf_html("melden-inline")}</p>
{impressum_html()}
</footer>
</div>

<button type="button" class="bildknopf" id="bildAuf" title="Bild für Social Media erzeugen">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-8 8"/></svg><span>Bild teilen</span></button>
<div class="bildlage" id="bildLage" role="dialog" aria-modal="true" aria-labelledby="bildTitel">
  <div class="bildbox">
    <div class="bildkopf"><h2 id="bildTitel">Bild für Social Media</h2>
      <button type="button" class="bildzu" id="bildZu" aria-label="Schliessen">&times;</button></div>
    <div class="bildbody">
      <div class="bildwahl">
        <label for="bildMotiv">Motiv</label>
        <select id="bildMotiv">
          <option value="kuchen">Kuchendiagramm der aktuellen Ansicht</option>
          <option value="ebene">Balkenliste der aktuellen Ansicht</option>
          <option value="ueberblick">Woher, wohin: Überblick</option>
        </select>
        <p class="bildnote">Hochformat 1080 × 1350, das Standardmass für Beiträge auf Instagram, LinkedIn und Facebook.
        «Aktuelle Ansicht» ist die Ebene, die im Detail gerade geöffnet ist: Kuchen und Balken zeigen ihre Aufteilung.</p>
        <button type="button" class="btn" id="bildLaden">Als PNG herunterladen</button>
      </div>
      <div class="bildvorschau"><canvas id="bildCanvas" width="1080" height="1350"></canvas></div>
    </div>
  </div>
</div>
{melden_html("Finanzspiegel", schwebend=False)}
<script id="daten" type="application/json">{daten_json}</script>
<script>{JS}</script>
</body>
</html>
"""


def main() -> None:
    daten = json.loads((HIER / "daten" / "finanzspiegel.json").read_text(encoding="utf-8"))
    ziel = ROOT / "site" / "finanzen" / "index.html"
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(seite(daten), encoding="utf-8")
    print(f"{ziel.relative_to(ROOT)}: {ziel.stat().st_size / 1024:.0f} kB, {len(daten['z'])} Kontozeilen")


if __name__ == "__main__":
    main()

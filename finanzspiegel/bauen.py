#!/usr/bin/env python3
"""Baut den Finanzspiegel, die vierte Ebene des Politspiegels.

Aufruf aus der Projektwurzel (nach daten.py und analyse.py):
    python3 finanzspiegel/bauen.py

Liest    finanzspiegel/daten/finanzspiegel.json   daten.py, analyse.py
         finanzspiegel/grafik.js                  Grafiken für Präsentation und Social Media
         politspiegel/politspiegel.json           Impressum, Testphase, Meldewerkzeug
Schreibt site/finanzen/index.html                 eine Datei, alles inline

Aufbau, von grob nach fein:
  1. Auswahl: bis zu drei Datensätze A, B, C im Raster Rechnung, Budget, Finanzplan 2025 bis 2030.
     A ist der Bezug für alle Differenzen.
  2. Woher, wohin: ordentlicher Ertrag und Aufwand von A als zwei Balken auf derselben Skala.
  3. Entwicklung 2025 bis 2030: Kennzahl im Zeitverlauf, Rechnung, Budget und Finanzplan;
     Nettoaufwand je Departement und je Aufgabenfeld des Finanzplans.
  4. Vergleich: Kennzahlen, Icicle je Datensatz auf gemeinsamer Skala, Tabelle mit Differenzen
     und den Kommentaren der Dienststellen; Erfolgs- und Investitionsrechnung, Gliederung nach
     Dienststelle oder Sachgruppe, Suche, CSV.
  5. Prüfhinweise aus analyse.py, mit Filter und Sprung in den Vergleich.
  6. Methode und Quellen.
  Dazu: Grafik für Präsentation und Social Media (grafik.js), Knopf unten rechts.

Warum Icicle und nicht Mindmap: Ein Knotendiagramm zeigt Struktur, nicht Grösse. Bildung mit
178 Mio. und Kultur mit 7 Mio. sähen als Knoten gleich aus.

Warum Aufwand und Ertrag getrennt: Flächen können nicht negativ sein, und ein Teil der
Dienststellen schliesst mit Ertragsüberschuss. Die Ansicht «netto» steht in der Tabelle.

Warum ordentlich als Vorgabe: Interne Verrechnungen (39, 49) stehen beidseits gleich,
Ausserordentliches (38, 48) sind Reservebewegungen. Ohne sie stimmen die Totale mit Ziffer 2.1
des Berichts. «Alle Konten» zeigt die Dienststellen so, wie Kapitel 6 sie summiert.
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
from social import kanal_html  # noqa: E402  Verweis auf den WhatsApp-Kanal
from testphase import TESTPHASE_CSS, testphase_html  # noqa: E402

GRAFIK = HIER / "grafik.js"
e = lambda s: html.escape(str(s), quote=True)

CSS = r"""
:root{
  color-scheme: light;
  --grund:#FFFFFF; --flaeche:#F7F8FA; --karte:#FFFFFF;
  --text:#12161C; --text-2:#3F4752; --text-leise:#5A626D; --linie:#E2E6EB; --linie-2:#C9CFD6; --hover:#F2F4F7; --markiert:#FFF4D6;
  --pro:#0F766E; --pro-text:#0C6A62; --contra:#8E44AD; --contra-text:#7E3C9A;
  --auf:#0F766E,#1E9189,#3FB3A8,#7ACBC3,#A9DDD8,#CDEBE8,#E2F3F1;
  --ert:#7E3C9A,#9553AE,#AE78C4,#C4A0D6,#D8BEE4,#E8D8F0,#F1E8F6;
  --s1:#2a78d6; --s2:#eb6834; --s3:#1baf7a;
  --s1-hell:#A6C6EE; --s2-hell:#F7C0AA; --s3-hell:#9FDDC7;
  --linie-r:#2C3440; --linie-b:#7B8494;
  --schatten:0 8px 30px rgba(17,24,32,.14);
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    color-scheme: dark;
    --grund:#12161C; --flaeche:#171C24; --karte:#1B212B;
    --text:#EEF1F5; --text-2:#C3CAD3; --text-leise:#9AA3AF; --linie:#2C3440; --linie-2:#3C4655; --hover:#1F2731; --markiert:#3B3317;
    --pro:#3FB3A8; --pro-text:#3FB3A8; --contra:#C08AD8; --contra-text:#C08AD8;
    --s1:#3987e5; --s2:#d95926; --s3:#199e70;
    --s1-hell:#2A5488; --s2-hell:#7A3D28; --s3-hell:#1A604E;
    --linie-r:#D5DBE3; --linie-b:#8E97A5;
    --schatten:0 8px 30px rgba(0,0,0,.5);
  }
}
:root[data-theme="dark"]{
  color-scheme: dark;
  --grund:#12161C; --flaeche:#171C24; --karte:#1B212B;
  --text:#EEF1F5; --text-2:#C3CAD3; --text-leise:#9AA3AF; --linie:#2C3440; --linie-2:#3C4655; --hover:#1F2731; --markiert:#3B3317;
  --pro:#3FB3A8; --pro-text:#3FB3A8; --contra:#C08AD8; --contra-text:#C08AD8;
  --s1:#3987e5; --s2:#d95926; --s3:#199e70;
  --s1-hell:#2A5488; --s2-hell:#7A3D28; --s3-hell:#1A604E;
  --linie-r:#D5DBE3; --linie-b:#8E97A5;
  --schatten:0 8px 30px rgba(0,0,0,.5);
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--grund);color:var(--text);
  font-family:"Public Sans","Helvetica Neue",Arial,sans-serif;font-size:16px;line-height:1.55}
h1,h2,h3{font-family:Archivo,"Helvetica Neue",Arial,sans-serif;font-weight:600}
a{color:inherit}
button{font:inherit;color:inherit}
.wrap{max-width:1080px;margin:0 auto;padding:0 24px 80px}
.kopf{border-bottom:1px solid var(--linie);padding:28px 0 22px;margin-bottom:14px}
.zurueck{display:inline-flex;align-items:center;gap:6px;font-family:Archivo,sans-serif;font-size:13px;font-weight:600;
  letter-spacing:.08em;text-transform:uppercase;color:var(--text-leise);text-decoration:none;margin-bottom:14px}
.zurueck:hover{color:var(--text)}
.marke{font-size:13px;letter-spacing:.10em;text-transform:uppercase;color:var(--text-leise);font-family:Archivo,sans-serif;font-weight:600}
h1{font-size:clamp(28px,4.6vw,42px);line-height:1.1;margin:10px 0 10px;letter-spacing:-.015em;text-wrap:balance}
.lead{margin:0;font-size:17px;color:var(--text-leise);max-width:66ch}
.stand{font-size:13px;color:var(--text-leise);margin:0 0 8px}

h2{font-size:15px;letter-spacing:.06em;text-transform:uppercase;color:var(--text-leise);margin:40px 0 6px}
h2 small{text-transform:none;letter-spacing:0;font-weight:400;font-family:"Public Sans",sans-serif}
.unter{margin:0 0 14px;color:var(--text-leise);max-width:76ch;font-size:15px}
h3{font-size:16px;margin:24px 0 8px}
.karte{background:var(--karte);border:1px solid var(--linie);border-radius:14px;padding:16px 18px;margin-bottom:14px}
.leise{color:var(--text-leise)} .klein{font-size:13px}
.nur-sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}

/* Auswahl */
.wahl-kopf{display:flex;flex-wrap:wrap;gap:10px 18px;align-items:flex-start;justify-content:space-between}
.auswahl{display:flex;flex-wrap:wrap;gap:8px;align-items:center;min-height:36px}
.chip{display:inline-flex;align-items:center;gap:7px;border:1px solid var(--linie-2);background:var(--karte);border-radius:999px;padding:4px 6px 4px 10px;font-size:14px;cursor:pointer}
.chip:hover{background:var(--hover)}
.chip i{display:inline-block;width:12px;height:12px;border-radius:3px}
.chip b{font-family:Archivo,sans-serif}
.chip .weg{appearance:none;border:0;background:none;cursor:pointer;color:var(--text-leise);font-size:17px;line-height:1;padding:0 4px}
.chip .weg:hover{color:var(--text)}
.chip.bezug{border-color:var(--text-2)}
.marke-vorlage{display:inline-block;border:1px solid var(--linie-2);border-radius:4px;padding:0 5px;font-size:11px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;color:var(--text-leise);line-height:1.5;vertical-align:1px}
.schnell{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.schnell b{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--text-leise);margin-right:4px;font-family:Archivo,sans-serif}
.schnell button{appearance:none;border:1px solid var(--linie);background:var(--flaeche);border-radius:6px;padding:4px 9px;font-size:13px;cursor:pointer}
.schnell button:hover{border-color:var(--linie-2);background:var(--hover)}
.raster{overflow-x:auto;margin-top:12px;-webkit-overflow-scrolling:touch}
.raster table{border-collapse:separate;border-spacing:4px;min-width:296px;width:100%;table-layout:fixed}
.raster col.kopfspalte{width:96px}
.raster th{font-size:12px;font-weight:600;color:var(--text-leise);text-align:center;padding:0 0 2px;font-family:Archivo,sans-serif}
.raster th.zeile{text-align:left;padding-right:6px;white-space:nowrap;font-size:13px;color:var(--text-2)}
.raster td{padding:0}
.zelle{appearance:none;width:100%;height:40px;border:1px solid var(--linie);background:var(--flaeche);border-radius:7px;cursor:pointer;position:relative;font-size:12.5px;color:var(--text-leise);padding:0;line-height:1.15}
.zelle:hover{border-color:var(--linie-2);background:var(--hover)}
.zelle:focus-visible{outline:2px solid var(--text);outline-offset:1px}
.zelle .erg{font-variant-numeric:tabular-nums;display:block}
.zelle .vl{display:block;font-size:10px;letter-spacing:.04em;text-transform:uppercase;opacity:.85}
.zelle[aria-pressed="true"]{border-color:transparent;font-weight:700}
.zelle .bst{display:none;font-family:Archivo,sans-serif;font-size:17px}
.zelle[aria-pressed="true"] .erg,.zelle[aria-pressed="true"] .vl{display:none}
.zelle[aria-pressed="true"] .bst{display:inline}
.hinweis{border-left:3px solid var(--linie-2);background:var(--flaeche);padding:10px 14px;border-radius:0 8px 8px 0;margin:12px 0 0;font-size:14.5px}
.raster-legende{font-size:12.5px;color:var(--text-leise);margin:8px 0 0}

/* Steuerelemente */
.steuer{display:flex;flex-wrap:wrap;gap:12px 20px;margin:0 0 14px;align-items:flex-end}
.grp{display:flex;flex-direction:column;gap:5px}
.grp > b{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--text-leise);font-weight:600;font-family:Archivo,sans-serif}
.chips{display:inline-flex;flex-wrap:wrap;border:1px solid var(--linie-2);border-radius:8px;overflow:hidden;background:var(--karte)}
.chips button{appearance:none;border:0;background:transparent;color:var(--text);padding:6px 12px;font-size:14px;cursor:pointer;border-right:1px solid var(--linie)}
.chips button:last-child{border-right:0}
.chips button[aria-pressed="true"]{background:var(--text);color:var(--grund);font-weight:600}
.chips button:focus-visible{outline:2px solid var(--text);outline-offset:-2px}
.chips button[disabled]{opacity:.4;cursor:not-allowed}
select{font:inherit;font-size:14px;padding:6px 8px;border:1px solid var(--linie-2);border-radius:8px;background:var(--karte);color:var(--text);max-width:100%}

/* Woher, wohin */
.kacheln{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:14px}
.kachel{background:var(--karte);border:1px solid var(--linie);border-radius:14px;padding:14px 16px}
.kachel .z{font-family:Archivo,sans-serif;font-size:clamp(20px,3vw,27px);font-weight:600;letter-spacing:-.02em;line-height:1.1}
.kachel .l{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--text-leise);margin-top:6px;font-family:Archivo,sans-serif;font-weight:600}
.kachel .s{font-size:13px;color:var(--text-leise);margin-top:6px;line-height:1.35}
.kachel.ert .z{color:var(--contra-text)} .kachel.auf .z{color:var(--pro-text)}
.ww svg{display:block;width:100%;height:auto}
.ww .beschr{font-family:Archivo,sans-serif;font-size:12px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;fill:var(--text-leise)}
.ww .seg{stroke:var(--karte);stroke-width:2;cursor:pointer}
.ww .seg:hover{opacity:.85}
.ww .in{font-size:11.5px;font-weight:600;pointer-events:none}
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

/* Entwicklung */
.verlauf svg{display:block;width:100%;height:auto;overflow:visible}
.verlauf .achse text{font-size:11.5px;fill:var(--text-leise);font-variant-numeric:tabular-nums}
.verlauf .gitter line{stroke:var(--linie);stroke-width:1}
.verlauf .bruch line{stroke:var(--linie-2);stroke-width:1}
.verlauf .bruch text{font-size:11px;fill:var(--text-leise)}
.legende-zeile{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:13px;color:var(--text-2);margin:8px 0 0}
.legende-zeile span{display:inline-flex;align-items:center;gap:6px}
.legende-zeile svg{width:26px;height:12px}
.tip{position:fixed;z-index:900;pointer-events:none;background:var(--karte);color:var(--text);border:1px solid var(--linie-2);border-radius:8px;box-shadow:var(--schatten);padding:8px 10px;font-size:13px;max-width:360px;display:none}
.tip .t{font-weight:700;margin-bottom:4px}
.tip .z{display:grid;grid-template-columns:14px 1fr auto;gap:4px 8px;align-items:center}
.tip .z i{display:inline-block;width:12px;height:2px;border-radius:1px}
.tip .z i.k{height:10px;border-radius:2px}
.tip .z b{font-variant-numeric:tabular-nums;text-align:right}
.tip .z span{color:var(--text-2)}
.tip .d{margin-top:4px;color:var(--text-2);font-size:12.5px}
.spark{display:block;width:120px;height:28px}
details.tabelle{margin-top:8px}
details.tabelle summary{cursor:pointer;font-size:13.5px;color:var(--text-2)}
details.tabelle .inner{overflow-x:auto}

/* Tabellen */
table.tab{width:100%;border-collapse:collapse;font-size:14px}
table.tab th{text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--text-leise);border-bottom:1px solid var(--text-2);padding:6px 8px 6px 0;font-weight:600;font-family:Archivo,sans-serif;white-space:nowrap;vertical-align:bottom}
table.tab td{border-bottom:1px solid var(--linie);padding:7px 8px 7px 0;vertical-align:middle}
table.tab th.r,table.tab td.r{text-align:right;padding-left:10px;padding-right:0;font-variant-numeric:tabular-nums;white-space:nowrap}
table.tab tr.klick{cursor:pointer}
table.tab tr.klick:hover td{background:var(--hover)}
table.tab tr.aktiv td{background:var(--hover)}
table.tab tr.markiert td{background:var(--markiert)}
table.tab tr.summe td{font-weight:600}
th .schl{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px;vertical-align:-1px}
.kz-tab td .dd{display:block;font-size:12px;color:var(--text-leise)}
.kz-tab td small{color:var(--text-leise)}
td .code{color:var(--text-leise);font-variant-numeric:tabular-nums;margin-right:6px;font-size:13px}

/* Vergleich */
.krume{display:flex;flex-wrap:wrap;align-items:center;gap:4px 6px;margin:4px 0 10px;font-size:14px}
.krume button{appearance:none;border:0;background:none;color:var(--text);cursor:pointer;padding:0;text-decoration:underline;text-underline-offset:2px}
.krume span.sep{color:var(--text-leise)}
.krume .jetzt{font-weight:700}
.icicles .ic{margin:0 0 12px}
.icicles .ic-kopf{display:flex;flex-wrap:wrap;justify-content:space-between;gap:2px 12px;align-items:baseline;margin:0 0 4px;font-size:14px}
.icicles .ic-kopf b{font-family:Archivo,sans-serif;font-size:15px}
.icicles .ic-kopf .wert{font-variant-numeric:tabular-nums;font-weight:600}
.icicles svg{display:block;width:100%;height:auto;overflow:visible}
.icicles rect.seg{cursor:pointer}
.icicles text{pointer-events:none;font-size:11.5px}
.icicles .leerband{fill:var(--flaeche)}
.icicles .keine{font-size:13px;color:var(--text-leise);padding:6px 0}
.balk{display:flex;flex-direction:column;gap:1px;margin-top:4px;max-width:320px}
.balk span{display:block;height:3px;border-radius:0 2px 2px 0}
.mk{appearance:none;border:1px solid var(--text-2);background:var(--karte);color:var(--text);border-radius:999px;font-size:11.5px;font-weight:700;padding:0 7px;line-height:18px;cursor:pointer;white-space:nowrap;margin-left:4px}
.mk.indirekt{border-style:dashed;color:var(--text-leise);font-weight:500;border-color:var(--linie-2)}
.mk.komm{border-color:var(--linie-2);font-weight:600;color:var(--text-2)}
.mk:hover{background:var(--hover)}
.werkzeug{display:flex;flex-wrap:wrap;justify-content:space-between;gap:8px;align-items:center;margin:0 0 8px}
.knopf{appearance:none;border:1px solid var(--linie-2);background:var(--karte);border-radius:6px;padding:5px 10px;font-size:13.5px;cursor:pointer}
.knopf:hover{background:var(--hover)}
.knoepfe{display:flex;flex-wrap:wrap;gap:8px}
.suche{position:relative;flex:1 1 260px;max-width:440px}
.suche input{width:100%;height:36px;padding:6px 12px;border:1px solid var(--linie-2);border-radius:8px;background:var(--karte);color:var(--text);font:inherit;font-size:14.5px}
.suche input:focus{outline:2px solid var(--text);outline-offset:-1px}
.suche ul{position:absolute;left:0;right:0;top:calc(100% + 4px);z-index:850;list-style:none;margin:0;padding:4px;background:var(--karte);border:1px solid var(--linie-2);border-radius:10px;box-shadow:var(--schatten);max-height:360px;overflow:auto}
.suche li{padding:7px 9px;border-radius:6px;cursor:pointer;font-size:14px;display:grid;grid-template-columns:1fr auto;gap:0 10px}
.suche li small{grid-column:1/-1;color:var(--text-leise);font-size:12px}
.suche li:hover,.suche li[aria-selected="true"]{background:var(--hover)}
.pop{position:absolute;z-index:880;background:var(--karte);border:1px solid var(--linie-2);border-radius:10px;box-shadow:var(--schatten);padding:10px 12px;max-width:440px;font-size:14px;display:none}
.pop .kopf-pop{font-family:Archivo,sans-serif;font-weight:600;margin-bottom:6px}
.pop ol{margin:4px 0 0;padding-left:20px}
.pop li{margin:0 0 6px}
.pop p{margin:0 0 8px}
.pop q{quotes:"«" "»"}
.pop button{appearance:none;border:0;background:none;color:var(--text);text-decoration:underline;cursor:pointer;padding:0;text-align:left;font-size:14px}

/* Prüfhinweise */
.bf-filter{display:flex;flex-wrap:wrap;gap:10px 16px;align-items:flex-end;margin:0 0 12px}
.bf-typen{display:flex;flex-wrap:wrap;gap:6px}
.bf-typen button{appearance:none;border:1px solid var(--linie-2);background:var(--karte);border-radius:999px;padding:4px 10px;font-size:13px;cursor:pointer}
.bf-typen button[aria-pressed="true"]{background:var(--text);color:var(--grund);border-color:var(--text)}
.bf-typen button em{font-style:normal;color:var(--text-leise);margin-left:4px}
.bf-typen button[aria-pressed="true"] em{color:inherit;opacity:.8}
.bf-liste{list-style:none;margin:0;padding:0}
.bf{border:1px solid var(--linie);border-radius:10px;background:var(--karte);margin:0 0 8px}
.bf > button.bf-kopf{appearance:none;width:100%;border:0;background:none;text-align:left;cursor:pointer;padding:11px 14px;display:grid;grid-template-columns:auto 1fr auto;gap:2px 12px;align-items:baseline}
.bf-kopf .nr{font-family:Archivo,sans-serif;color:var(--text-leise);font-variant-numeric:tabular-nums;min-width:2.2em}
.bf-kopf .titel{font-weight:600}
.bf-kopf .betr{font-variant-numeric:tabular-nums;color:var(--text-2);white-space:nowrap;font-size:14px}
.bf-kopf .meta{grid-column:2/-1;font-size:12.5px;color:var(--text-leise)}
.bf-kopf .typ{display:inline-block;border:1px solid var(--linie-2);border-radius:4px;padding:0 5px;margin-right:6px;font-size:11.5px;color:var(--text-2)}
.bf-body{padding:0 14px 12px 14px;display:none}
.bf.offen .bf-body{display:block}
.bf-body ol{margin:0 0 10px;padding-left:22px}
.bf-body li{margin:0 0 3px}
.bf-body .komm-titel{font-size:13px;color:var(--text-leise);margin:6px 0 4px}
.bf-body blockquote{margin:0 0 6px;padding:0 0 0 12px;border-left:2px solid var(--linie-2);font-size:14px;color:var(--text-2)}
.bf.markiert{outline:2px solid var(--text);outline-offset:1px}
.mehr{margin:10px 0 0}

/* Methode */
.methode ol{padding-left:22px}
.methode li{margin:0 0 6px}
.quellen td{font-size:13.5px}

/* Grafik: Knopf unten rechts, Dialog mit Vorschau */
.grafikknopf{position:fixed;right:18px;bottom:18px;z-index:800;display:inline-flex;align-items:center;gap:8px;appearance:none;background:var(--text);color:var(--grund);border:0;border-radius:999px;padding:11px 16px;font-weight:600;font-size:14px;cursor:pointer;box-shadow:0 4px 18px rgba(0,0,0,.18)}
.grafikknopf svg{width:17px;height:17px;flex:none}
.grafikknopf:focus-visible{outline:2px solid var(--text);outline-offset:3px}
.grafiklage{position:fixed;inset:0;z-index:950;background:rgba(10,14,20,.55);display:none;align-items:flex-start;justify-content:center;padding:30px 14px;overflow:auto}
.grafiklage.offen{display:flex}
.grafikbox{background:var(--karte);color:var(--text);border-radius:14px;max-width:1120px;width:100%;padding:18px 20px 22px;border:1px solid var(--linie);box-shadow:var(--schatten)}
.grafikkopf{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.grafikkopf h2{margin:0;font-size:19px;text-transform:none;letter-spacing:0;color:var(--text)}
.grafikzu{appearance:none;border:0;background:none;color:var(--text-leise);font-size:28px;cursor:pointer;line-height:1;padding:0 6px}
.grafikzu:hover{color:var(--text)}
.grafikbody{display:grid;grid-template-columns:280px 1fr;gap:20px;align-items:start}
.grafikwahl .feld{display:block;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--text-leise);margin:12px 0 5px;font-family:Archivo,sans-serif;font-weight:600}
.grafikwahl .feld:first-child{margin-top:2px}
.grafikwahl select,.grafikwahl input[type="text"]{width:100%;padding:8px;border:1px solid var(--linie-2);border-radius:8px;background:var(--grund);color:var(--text);font:inherit;font-size:14px}
.grafikwahl input[type="text"]:focus{outline:2px solid var(--text);outline-offset:-1px}
.grafikwahl .radio{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:14px}
.grafikwahl .radio label{display:inline-flex;gap:6px;align-items:center;cursor:pointer}
.grafiknote{font-size:13px;color:var(--text-2);margin:14px 0 0}
.grafikhinweis{font-size:12.5px;color:var(--text-leise);margin:6px 0 0}
.grafikknoepfe{display:flex;flex-direction:column;gap:8px;margin-top:14px}
.btn{appearance:none;border:1px solid transparent;background:var(--text);color:var(--grund);border-radius:8px;padding:10px 14px;font-weight:700;font-size:14.5px;cursor:pointer}
.btn.zweit{background:transparent;color:var(--text);border-color:var(--linie-2);font-weight:500}
.btn.zweit:hover{background:var(--hover)}
.btn:focus-visible{outline:2px solid var(--text);outline-offset:2px}
.grafikmeldung{font-size:13px;color:var(--text-2);min-height:1.5em;margin:8px 0 0}
.grafikvorschau{min-width:0}
.grafikvorschau canvas{display:block;width:auto;height:auto;max-width:100%;max-height:calc(100vh - 150px);margin:0 auto;border:1px solid var(--linie);border-radius:8px;background:#fff}
body.grafik-offen .grafikknopf{display:none}
.grafikvorschau.transparent canvas{background:repeating-conic-gradient(#E6E8EC 0 25%, #FFFFFF 0 50%) 0 0/22px 22px}
.grafikvorschau p{font-size:12.5px;color:var(--text-leise);margin:6px 0 0}

.fuss{margin-top:48px;padding-top:20px;border-top:1px solid var(--linie);font-size:13.5px;color:var(--text-leise);line-height:1.55}
.fuss b{color:var(--text)} .fuss p{margin:0 0 10px}
.fuss-kanal a{color:var(--text);font-weight:600;text-decoration:none}
.fuss-kanal a:hover{text-decoration:underline}
.melden-inline{display:inline-flex;align-items:center;gap:6px;margin-left:10px;appearance:none;border:1px solid var(--linie);
  background:var(--karte);color:var(--text);border-radius:999px;padding:4px 11px;font-size:13px;cursor:pointer}
.melden-inline svg{width:14px;height:14px}

@media (max-width:760px){
  .wrap{padding:0 16px 70px}
  .kacheln{grid-template-columns:1fr 1fr 1fr;gap:8px} .kachel{padding:11px 12px} .kachel .s{display:none}
  .legenden{grid-template-columns:1fr}
  .h-m{display:none}
  table.tab{font-size:13.5px}
  .bf > button.bf-kopf{grid-template-columns:auto 1fr}
  .bf-kopf .betr{grid-column:2}
  .grafikbody{grid-template-columns:1fr}
  .grafikvorschau{order:-1}
  .grafikknopf span{display:none}
  .grafikknopf{padding:13px}
  .grafiklage{padding:12px 8px}
  .grafikbox{padding:14px 14px 18px}
  .spark{width:80px}
}
@media (max-width:520px){ .h-s{display:none} .raster col.kopfspalte{width:62px} .raster table{border-spacing:2px} .raster th.zeile{font-size:11.5px;padding-right:2px} .zelle{font-size:10.5px;height:36px} .zelle .vl{display:none} .karte{padding:14px 14px} }
@media print{ .schnell,.raster,.steuer,.werkzeug,.bf-filter,.grafikknopf,.grafiklage,[data-grafik]{display:none!important} .bf-body{display:block} }
@media (prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}
""" + IMPRESSUM_CSS + TESTPHASE_CSS + MELDEN_CSS

JS = r"""
(function(){
"use strict";
const D = JSON.parse(document.getElementById('daten').textContent);
const DS = D.jahre.concat(D.plan), IDX = Object.fromEntries(DS.map((d, i) => [d.k, i]));
const JI = Object.fromEntries(D.jahre.map((d, i) => [d.k, i]));   // Spalte in den Kontozeilen
const KZ = D.kz, BF = D.befunde || [];
const $ = (s, e) => (e || document).querySelector(s);
const $$ = (s, e) => [...(e || document).querySelectorAll(s)];
const esc = t => String(t).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const farbe = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const rampe = n => farbe(n).split(',').map(s => s.trim());
const tausender = s => { const [g, d] = String(s).split('.'); return g.replace(/\B(?=(\d{3})+(?!\d))/g, "'") + (d !== undefined ? '.' + d : ''); };
const fr = v => { const r = Math.round(v); return (r < 0 ? '−' : '') + tausender(Math.abs(r)); };
const frS = v => { const r = Math.round(v); return (r > 0 ? '+' : r < 0 ? '−' : '±') + tausender(Math.abs(r)); };
const mio = (v, s) => (v < 0 ? '−' : '') + tausender((Math.abs(v) / 1e6).toFixed(s === undefined ? 1 : s));
const mioVz = (v, s) => { const t = (Math.abs(v) / 1e6).toFixed(s === undefined ? 1 : s); return (+t === 0 ? '±' : v > 0 ? '+' : '−') + tausender(t); };
const pct = (d, b) => Math.abs(b) >= 1 ? ((d >= 0 ? '+' : '−') + Math.abs(100 * d / Math.abs(b)).toFixed(1) + ' %') : '';
const kurz = (t, n) => t.length <= n ? t : t.slice(0, Math.max(n - 1, 1)).trimEnd() + '…';
const standText = () => D.stand.split('-').reverse().join('.');
const SLOT = ['A', 'B', 'C'];
const slotFarbe = s => farbe(['--s1', '--s2', '--s3'][s]);
const slotHell = s => farbe(['--s1-hell', '--s2-hell', '--s3-hell'][s]);
function lum(hex){ const h = hex.replace('#', ''); const c = [0, 2, 4].map(i => parseInt(h.substr(i, 2), 16) / 255).map(v => v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4)); return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]; }
const textAuf = hex => { const L = lum(hex); return (1.05 / (L + .05)) >= ((L + .05) / (lum('#12161C') + .05)) ? '#FFFFFF' : '#12161C'; };
function el(tag, attrs, kids){ const n = document.createElement(tag); if(attrs) for(const [k, v] of Object.entries(attrs)){ if(v === null || v === undefined) continue; if(k === 'text') n.textContent = v; else if(k === 'class') n.className = v; else n.setAttribute(k, v); } (kids || []).forEach(c => c && n.append(c)); return n; }
const ORDENTLICH = g => (g[0] === '3' || g[0] === '4') && !['38', '39', '48', '49'].includes(g);

/* ── Datensätze ──────────────────────────────────────────────────────── */
const dsT = k => DS[IDX[k]].t;
const dsLang = k => DS[IDX[k]].t + (DS[IDX[k]].vorlage ? ' (Vorlage)' : '');
const istPlan = k => DS[IDX[k]].a === 'p';
const J_MIN = 2025, J_MAX = 2030;
const st = {sel: ['b27', 'b26', 'r25'], rechnung: 'er', gl: 'inst', ansicht: 'A', umfang: 'ord', pfad: [], markiert: null,
            kz: 'gesamt', bereich: null, bf: {typ: 'alle', ds: 'alle', min: 0, nurAuswahl: false, q: ''}, bfOffen: new Set(), bfZahl: 30};
// Finanzplan: nur zweistellige Sachgruppen und Totale; mit ihm bleibt der Vergleich auf der obersten Ebene
const gesperrt = () => st.sel.some(istPlan);

/* Summen je zweistelliger Sachgruppe und Kennzahlen eines Datensatzes */
const GRUPPEN = {};
function gruppenVon(k){
  if(GRUPPEN[k]) return GRUPPEN[k];
  const g = {};
  if(istPlan(k)){ Object.assign(g, D.agg[k]); }
  else { const i = 5 + JI[k]; for(const z of D.z){ const c = z[3].slice(0, 2); g[c] = (g[c] || 0) + z[i]; } }
  return GRUPPEN[k] = g;
}
const kennzahlenVon = k => KZ[k];

/* ── Baum für die gewählten Datensätze ───────────────────────────────── */
let BAUM = null, KNOTEN = null;
function seiten(konto, v){ const c = konto[0]; return c === '3' || c === '5' ? [v, 0] : c === '4' || c === '6' ? [0, -v] : v >= 0 ? [v, 0] : [0, -v]; }
function neuerKnoten(id, name, code, eltern, blatt){ return {id, name, code, v: st.sel.map(() => [0, 0]), kinder: new Map(), eltern, tiefe: eltern ? eltern.tiefe + 1 : 0, blatt: !!blatt}; }
function einhaengen(pfad, s, a, e){
  let n = BAUM; n.v[s][0] += a; n.v[s][1] += e;
  for(const [id, name, code, blatt, komm] of pfad){
    let c = n.kinder.get(id);
    if(!c){ c = neuerKnoten(id, name, code, n, blatt); if(komm) c.komm = komm; n.kinder.set(id, c); KNOTEN.set(id, c); n.blatt = false; }
    c.v[s][0] += a; c.v[s][1] += e; n = c;
  }
}
function pfadER(z){
  const [dep, dst, spz, konto, bez] = z;
  if(st.gl === 'inst'){
    const p = [['d' + dep, D.dep[dep] || dep, '', false], ['s' + dst, D.dst[dst] || ('Dienststelle ' + dst), dst, false, `${dst}||`]];
    if(spz) p.push(['f' + spz, D.spz[spz] || spz, spz, false]);
    p.push([`k${dst}|${spz}|${konto}`, bez, konto, true, `${dst}|${spz}|${konto}`]);
    return p;
  }
  const a = konto.slice(0, 2), b = konto.slice(0, 3);
  return [['a' + a, D.sg[a] || ('Sachgruppe ' + a), a, false], ['b' + b, D.sg[b] || ('Sachgruppe ' + b), b, false], ['k' + konto, bez, konto, true]];
}
function pfadIR(z){
  const [dep, dst, spz, konto, pr] = z;
  const kn = D.irk[konto] || konto, pn = D.irp[pr] || pr;
  if(st.gl === 'inst'){
    const p = [['d' + dep, D.dep[dep] || dep, '', false], ['s' + dst, D.dst[dst] || ('Dienststelle ' + dst), dst, false]];
    if(spz) p.push(['f' + spz, D.spz[spz] || spz, spz, false]);
    p.push([`v${dst}|${spz}|${pr}`, pn, pr, false], [`k${dst}|${spz}|${pr}|${konto}`, kn, konto, true]);
    return p;
  }
  const a = konto.slice(0, 2);
  return [['a' + a, D.sg[a] || ('Sachgruppe ' + a), a, false], ['k' + konto, kn, konto, false], [`v${konto}|${pr}`, pn, pr, true]];
}
function baum(){
  const ir = st.rechnung === 'ir';
  if(gesperrt() && !ir) st.gl = 'art';
  BAUM = neuerKnoten('root', ir ? 'Investitionsrechnung' : 'Erfolgsrechnung', '', null, false);
  KNOTEN = new Map([['root', BAUM]]);
  st.sel.forEach((k, s) => {
    if(!ir){
      if(istPlan(k)){
        for(const [sg, v] of Object.entries(D.agg[k])){
          if(!v || (st.umfang === 'ord' && !ORDENTLICH(sg))) continue;
          const [a, e] = seiten(sg, v);
          einhaengen([['a' + sg, D.sg[sg] || sg, sg, false]], s, a, e);
        }
        return;
      }
      const i = 5 + JI[k];
      for(const z of D.z){
        const v = z[i]; if(!v) continue;
        if(st.umfang === 'ord' && !ORDENTLICH(z[3].slice(0, 2))) continue;
        const [a, e] = seiten(z[3], v);
        einhaengen(pfadER(z), s, a, e);
      }
    } else {
      if(istPlan(k)){ const [a, e] = D.aggir[k]; BAUM.v[s][0] += a; BAUM.v[s][1] += e; return; }
      const j = JI[k];
      for(const z of D.ir){
        const a = z[5][2 * j], e = z[5][2 * j + 1]; if(!a && !e) continue;
        einhaengen(pfadIR(z), s, a, e);
      }
    }
  });
}
const wert = (n, s) => { const v = n.v[s]; return st.ansicht === 'A' ? v[0] : st.ansicht === 'E' ? v[1] : v[0] - v[1]; };
const sichtbar = (c, s) => st.ansicht === 'A' ? Math.abs(c.v[s][0]) > .004 : st.ansicht === 'E' ? Math.abs(c.v[s][1]) > .004 : Math.abs(c.v[s][0]) + Math.abs(c.v[s][1]) > .004;
const pos = v => Math.max(0, v);
function kinderSortiert(n){
  const arr = [...n.kinder.values()];
  arr.sort((a, b) => { const ma = Math.max(...st.sel.map((_, s) => wert(a, s))), mb = Math.max(...st.sel.map((_, s) => wert(b, s))); return mb - ma || a.id.localeCompare(b.id); });
  return arr;
}
function aktuellerKnoten(){
  let n = BAUM; const weg = [n], pf = [];
  for(const id of st.pfad){ const c = n.kinder.get(id); if(!c) break; n = c; weg.push(n); pf.push(id); }
  st.pfad = pf;
  return weg;
}
function setzePfad(n){ const p = []; let x = n; while(x && x.id !== 'root'){ p.unshift(x.id); x = x.eltern; } st.pfad = p; }
const ansichtName = () => st.rechnung === 'ir' ? {A:'Ausgaben', E:'Einnahmen', N:'Nettoinvestitionen'}[st.ansicht] : {A:'Aufwand', E:'Ertrag', N:'Nettoaufwand'}[st.ansicht];
const knotenName = n => (n.code ? n.code + ' ' : '') + n.name;

/* ── Prüfhinweise: Index nach Knoten ─────────────────────────────────── */
const BF_DIREKT = new Map(), BF_INDIREKT = new Map();
BF.forEach((b, i) => {
  const ziel = b.markiert || b.pfad[b.pfad.length - 1];
  const kette = [ziel, ...b.pfad.filter(p => p !== ziel).reverse()];
  for(const ds of b.ds) kette.forEach((id, t) => {
    const key = ds + '|' + b.rechnung + '|' + id, map = t === 0 ? BF_DIREKT : BF_INDIREKT;
    if(!map.has(key)) map.set(key, new Set());
    map.get(key).add(i);
  });
});
function befundeFuer(id){
  const d = new Set(), ind = new Set();
  if(st.gl !== 'inst') return {d: [], i: []};
  for(const k of st.sel){
    const key = k + '|' + st.rechnung + '|' + id;
    (BF_DIREKT.get(key) || []).forEach(i => d.add(i));
    (BF_INDIREKT.get(key) || []).forEach(i => ind.add(i));
  }
  d.forEach(i => ind.delete(i));
  return {d: [...d], i: [...ind]};
}
/* Kommentare der Dienststellen zu einem Knoten, je gewähltem Datensatz */
function kommentareFuer(n){
  if(!n.komm || st.rechnung !== 'er') return [];
  return st.sel.map((k, s) => [k, s, (D.komm[k] || {})[n.komm]]).filter(x => x[2]);
}

/* ── Auswahl ─────────────────────────────────────────────────────────── */
function zeichneRaster(){
  const jahre = []; for(let j = J_MIN; j <= J_MAX; j++) jahre.push(j);
  const tb = $('#raster'); tb.innerHTML = '';
  const zelle = k => {
    const d = DS[IDX[k]], s = st.sel.indexOf(k), erg = KZ[k].gesamt;
    const b = el('button', {type: 'button', class: 'zelle', 'data-k': k, 'aria-pressed': s >= 0 ? 'true' : 'false',
      title: `${dsLang(k)}: Gesamtergebnis ${mioVz(erg)} Mio. Franken` + (s >= 0 ? `, gewählt als ${SLOT[s]}` : '')});
    b.append(el('span', {class: 'erg', text: mioVz(erg)}));
    if(d.vorlage) b.append(el('span', {class: 'vl', text: 'Vorlage'}));
    b.append(el('span', {class: 'bst', text: s >= 0 ? SLOT[s] : ''}));
    if(s >= 0){ b.style.background = slotFarbe(s); b.style.color = textAuf(slotFarbe(s)); }
    return b;
  };
  const reihe = (titel, art) => el('tr', null, [el('th', {class: 'zeile', text: titel}), ...jahre.map(j => {
    const td = el('td'), k = art + String(j).slice(2);
    if(IDX[k] !== undefined) td.append(zelle(k));
    return td;
  })]);
  tb.append(el('colgroup', null, [el('col', {class: 'kopfspalte'}), ...jahre.map(() => el('col'))]),
            el('thead', null, [el('tr', null, [el('th', {class: 'zeile'}), ...jahre.map(j => el('th', {text: String(j)}))])]),
            el('tbody', null, [reihe('Rechnung', 'r'), reihe('Budget', 'b'), reihe('Finanzplan', 'p')]));
  $$('.zelle', tb).forEach(b => b.addEventListener('click', () => waehle(b.dataset.k)));
  const aw = $('#auswahl'); aw.innerHTML = '';
  st.sel.forEach((k, s) => {
    const c = el('span', {class: 'chip' + (s === 0 ? ' bezug' : ''), role: 'button', tabindex: '0', title: s === 0 ? 'Bezug für die Differenzen' : 'Als Bezug (A) setzen'});
    const sw = el('i'); sw.style.background = slotFarbe(s);
    const weg = el('button', {type: 'button', class: 'weg', 'aria-label': dsT(k) + ' entfernen', text: '×'});
    weg.addEventListener('click', ev => { ev.stopPropagation(); if(st.sel.length > 1){ st.sel = st.sel.filter(x => x !== k); neu(); } });
    c.append(sw, el('b', {text: SLOT[s]}), document.createTextNode(dsT(k)));
    if(DS[IDX[k]].vorlage) c.append(el('span', {class: 'marke-vorlage', text: 'Vorlage', title: DS[IDX[k]].fassung}));
    c.append(weg);
    const bezug = () => { if(s > 0){ st.sel = [k, ...st.sel.filter(x => x !== k)]; neu(); } };
    c.addEventListener('click', bezug); c.addEventListener('keydown', ev => { if(ev.key === 'Enter' || ev.key === ' '){ ev.preventDefault(); bezug(); } });
    aw.append(c);
  });
  if(st.sel.length > 1) aw.append(el('span', {class: 'leise klein', text: 'Differenzen gegenüber A. Klick auf einen Eintrag macht ihn zu A.'}));
}
function waehle(k){
  const i = st.sel.indexOf(k);
  if(i >= 0){ if(st.sel.length > 1) st.sel.splice(i, 1); }
  else if(st.sel.length < 3) st.sel.push(k);
  else st.sel[2] = k;
  neu();
}
function neu(pfadBehalten){
  if(!pfadBehalten && gesperrt()) st.pfad = [];
  baum();
  zeichneRaster(); zeichneHinweis(); zeichneUeberblick(); zeichneKennzahlen(); zeichneVerlauf(); zeichneDrill(); zeichneBefunde(); hashSchreiben();
}
function zeichneHinweis(){
  const h = $('#planhinweis');
  h.hidden = !gesperrt();
  h.textContent = gesperrt() ? 'Der Finanzplan 2028 bis 2030 liegt nur nach Sachgruppen vor (Ziffer 2.1 des Berichts), die Investitionen nur als Total. Mit einem Finanzplanjahr in der Auswahl zeigt der Vergleich deshalb die Sachgruppen; tiefer geht es mit Budget und Rechnung.' : '';
}

/* ── Woher, wohin: Datensatz A ───────────────────────────────────────── */
function zeichneUeberblick(){
  const kA = st.sel[0], kB = st.sel[1] || null;
  const K = KZ[kA], V = kB ? KZ[kB] : null, g = gruppenVon(kA);
  const tJ = dsLang(kA), tV = kB ? dsLang(kB) : '';
  $('#wwTitel').textContent = `· ${tJ}, ordentlicher Ertrag und Aufwand`;
  const vgl = (v, w) => V ? `<div class="s">${esc(tV)}: ${mio(w)} Mio., also ${mioVz(v - w)}</div>` : '';
  $('#kacheln').innerHTML =
    `<div class="kachel ert"><div class="z">${mio(K.ert)} Mio.</div><div class="l">Ertrag ${esc(tJ)}</div>${vgl(K.ert, V && V.ert)}</div>
     <div class="kachel auf"><div class="z">${mio(K.auf)} Mio.</div><div class="l">Aufwand ${esc(tJ)}</div>${vgl(K.auf, V && V.auf)}</div>
     <div class="kachel"><div class="z">${mioVz(K.gesamt)} Mio.</div><div class="l">${K.gesamt < 0 ? 'Defizit' : 'Überschuss'} ${esc(tJ)}</div>${V ? `<div class="s">${esc(tV)}: ${mioVz(V.gesamt)} Mio.</div>` : ''}</div>`;
  const RA = rampe('--auf'), RE = rampe('--ert');
  const reihe = (p, ramp) => Object.entries(g).filter(([c, v]) => c[0] === p && ORDENTLICH(c) && Math.abs(v) > 0)
    .map(([c, v]) => ({c, v: Math.abs(v)})).sort((a, b) => b.v - a.v)
    .map((x, i) => ({...x, f: ramp[Math.min(i, ramp.length - 1)], hell: i >= 3}));
  const E = reihe('4', RE), A = reihe('3', RA);
  const skala = Math.max(K.auf, K.ert);
  const W = Math.max(300, Math.round($('#ww').clientWidth || 1000)), R = W;
  const schmal = W < 640, H = schmal ? 40 : 44, Y1 = 22, Y2 = schmal ? 132 : 108;
  const bar = (liste, y, total) => {
    let x = 0, s = '';
    for(const seg of liste){
      const b = R * seg.v / skala;
      const tx = seg.hell ? '#12161C' : '#FFFFFF';
      s += `<rect class="seg" x="${x.toFixed(1)}" y="${y}" width="${Math.max(b - 2, .5).toFixed(1)}" height="${H}" fill="${seg.f}" rx="3" data-sg="${seg.c}" tabindex="0" role="button" aria-label="${esc((D.sg[seg.c] || seg.c) + ': ' + mio(seg.v) + ' Mio. Franken')}"><title>${esc((seg.c + ' ' + (D.sg[seg.c] || '')).trim())}: ${mio(seg.v)} Mio. Fr., ${(100 * seg.v / total).toFixed(1)} %</title></rect>`;
      if(b > 64){
        s += `<text class="in" x="${(x + 7).toFixed(1)}" y="${y + 17}" fill="${tx}">${esc(kurz(D.sg[seg.c] || seg.c, Math.floor(b / 7)))}</text>`;
        s += `<text class="in" x="${(x + 7).toFixed(1)}" y="${y + H - 9}" fill="${tx}" opacity=".8" style="font-weight:400">${(100 * seg.v / total).toFixed(0)} %</text>`;
      } else if(b > 28){
        s += `<text class="in" x="${(x + 6).toFixed(1)}" y="${y + H / 2 + 4}" fill="${tx}" opacity=".9" style="font-weight:400">${(100 * seg.v / total).toFixed(0)} %</text>`;
      }
      x += b;
    }
    return s;
  };
  const xE = R * K.ert / skala, xA = R * K.auf / skala, diff = K.ert - K.auf;
  const dx = Math.min(xE, xA), dw = Math.abs(xE - xA);
  let s = `<svg viewBox="0 0 ${W} ${Y2 + H + 6}" width="${W}" role="img" aria-label="Ertrag und Aufwand ${esc(tJ)}">`;
  s += `<text class="beschr" x="0" y="13">Woher · Ertrag ${mio(K.ert)} Mio.</text>` + bar(E, Y1, K.ert);
  s += `<text class="beschr" x="0" y="${Y2 - 9}">Wohin · Aufwand ${mio(K.auf)} Mio.</text>` + bar(A, Y2, K.auf);
  if(dw > 2){
    const lab = (diff < 0 ? `Operatives Defizit ${mio(-diff)}` : `Operativer Überschuss ${mio(diff)}`) + ' Mio.';
    if(schmal){
      const yb = Y1 + H + 4, hb = 18;
      s += `<rect x="${dx.toFixed(1)}" y="${yb}" width="${dw.toFixed(1)}" height="${hb}" fill="none" stroke="${farbe('--text-leise')}" stroke-dasharray="3 3"/>`;
      s += `<text class="diffz" x="${R - 4}" y="${yb + hb + 20}" text-anchor="end">${lab}</text>`;
    } else {
      const yb = Y1 + H + 6, hb = Y2 - 14 - yb;
      s += `<rect x="${dx.toFixed(1)}" y="${yb}" width="${dw.toFixed(1)}" height="${hb}" fill="none" stroke="${farbe('--text-leise')}" stroke-dasharray="3 3"/>`;
      const breit = dw > 190, tx = breit ? dx + dw / 2 : Math.max(dx - 6, 0);
      s += `<text class="diffz" x="${tx.toFixed(1)}" y="${yb + hb / 2 + 5}" text-anchor="${breit ? 'middle' : 'end'}">${lab}</text>`;
    }
  }
  $('#ww').innerHTML = s + '</svg>';
  $$('#ww rect.seg').forEach(r => { r.addEventListener('click', () => springeSachgruppe(r.dataset.sg)); r.addEventListener('keydown', ev => { if(ev.key === 'Enter') springeSachgruppe(r.dataset.sg); }); });
  const leg = (liste, total) => `<ol>` + liste.map(x =>
    `<li data-sg="${x.c}"><i style="background:${x.f}"></i>
       <span>${esc(D.sg[x.c] || x.c)}${D.erkl[x.c] ? `<small>${esc(D.erkl[x.c])}</small>` : ''}</span>
       <b>${mio(x.v)}<em>${(100 * x.v / total).toFixed(1)} %</em></b></li>`).join('') + `</ol>`;
  $('#legenden').innerHTML = `<div class="legende"><h3>Woher das Geld kommt</h3>${leg(E, K.ert)}</div><div class="legende"><h3>Wohin es geht</h3>${leg(A, K.auf)}</div>`;
  $$('#legenden li').forEach(li => li.addEventListener('click', () => springeSachgruppe(li.dataset.sg)));
  const teile = [];
  if(Math.abs(K.ao) >= 5e4) teile.push(`${K.ao > 0 ? 'Dazu kommen' : 'Davon gehen ab'} ${mio(Math.abs(K.ao))} Mio. ausserordentliches Ergebnis${K.ao > 0 ? ', vor allem Entnahmen aus finanzpolitischen Reserven' : ', vor allem Einlagen in Reserven'}.`);
  if(Math.abs(K.ek) >= 5e4) teile.push(`Fonds und Spezialfinanzierungen im Eigenkapital ${mioVz(K.ek)} Mio.`);
  $('#ergebnis').innerHTML = `Ordentlicher Ertrag <b>${mio(K.ert)}</b> minus ordentlicher Aufwand <b>${mio(K.auf)}</b> ergibt das operative Ergebnis von <b>${mioVz(K.ord)} Mio.</b> ${esc(teile.join(' '))}
    Gesamtergebnis <b>${mioVz(K.gesamt)} Mio. Franken</b>${K.gesamt < 0 ? ', ein Aufwandüberschuss' : ', ein Ertragsüberschuss'}.` + (K.iv ? ` Interne Verrechnungen (${mio(Math.abs(K.iv))} Mio.) stehen auf beiden Seiten gleich und sind weggelassen.` : '');
}
function springeSachgruppe(sg){
  st.rechnung = 'er'; st.gl = 'art'; st.umfang = 'ord'; st.ansicht = sg[0] === '4' ? 'E' : 'A';
  baum();
  const n = KNOTEN.get('a' + sg);
  if(n && !gesperrt() && n.kinder.size){ setzePfad(n); st.markiert = null; } else { st.pfad = []; st.markiert = 'a' + sg; }
  zeichneDrill(); hashSchreiben();
  $('#vergleichTitel').scrollIntoView({behavior: 'smooth', block: 'start'});
}

/* ── Kennzahlen im Vergleich ─────────────────────────────────────────── */
const KENNZAHLEN = [
  ['ert', 'Ordentlicher Ertrag', 'Sachgruppen 40 bis 47'],
  ['auf', 'Ordentlicher Aufwand', 'Sachgruppen 30 bis 37'],
  ['ord', 'Operatives Ergebnis', 'ordentlicher Ertrag minus Aufwand'],
  ['ao', 'Ausserordentliches Ergebnis', 'Sachgruppen 48 minus 38, vor allem Reserven'],
  ['gesamt', 'Gesamtergebnis', 'mit Fonds und Spezialfinanzierungen im Eigenkapital'],
  ['fiskal', 'Fiskalertrag (Steuern)', 'Sachgruppe 40'],
  ['transferE', 'Transferertrag', 'Sachgruppe 46: Bundessteueranteile, Finanzausgleich, Beiträge'],
  ['pers', 'Personalaufwand', 'Sachgruppe 30'],
  ['sach', 'Sach- und Betriebsaufwand', 'Sachgruppe 31'],
  ['transfer', 'Transferaufwand', 'Sachgruppe 36'],
  ['netInv', 'Nettoinvestitionen', 'Ausgaben minus Einnahmen der Investitionsrechnung'],
  ['ekap', 'Eigenkapital am Jahresende', 'Bilanz, Ziffer 2.3; Budget 2026 aktualisiert'],
  ['sfnp', 'Steuerfuss natürliche Personen', 'Prozent der einfachen Staatssteuer'],
];
const kzRoh = (k, key) => { const K = KZ[k]; return !K || K[key] === undefined || K[key] === null ? null : K[key]; };
const kzFormat = (key, v) => key === 'sfnp' ? v + ' %' : ['ord', 'ao', 'gesamt'].includes(key) ? mioVz(v) : mio(v);
const kzDiff = (key, d, b) => key === 'sfnp' ? (d > 0 ? '+' : d < 0 ? '−' : '±') + Math.abs(d) + ' Prozentpunkte' : mioVz(d) + (['ord', 'ao', 'gesamt'].includes(key) || !pct(d, b) ? '' : ` (${pct(d, b)})`);
function zeichneKennzahlen(){
  const t = $('#kz'); t.innerHTML = '';
  const kopf = el('tr', null, [el('th', {text: 'Kennzahl, Mio. Franken'}), ...st.sel.map((k, s) => { const th = el('th', {class: 'r'}); const sw = el('span', {class: 'schl'}); sw.style.background = slotFarbe(s); th.append(sw, document.createTextNode(SLOT[s] + ' · ' + dsLang(k))); return th; })]);
  const body = el('tbody');
  for(const [key, name, erkl] of KENNZAHLEN){
    if(!st.sel.some(k => kzRoh(k, key) !== null)) continue;
    const tr = el('tr');
    const td0 = el('td'); td0.append(el('span', {text: name})); if(erkl) td0.append(el('small', {class: 'h-m', text: ' · ' + erkl}));
    tr.append(td0);
    st.sel.forEach((k, s) => {
      const v = kzRoh(k, key), td = el('td', {class: 'r'});
      if(v === null){ td.append(el('span', {class: 'leise', text: '·', title: 'Für diesen Datensatz nicht ausgewiesen'})); tr.append(td); return; }
      td.append(el('b', {text: kzFormat(key, v)}));
      const b = kzRoh(st.sel[0], key);
      if(s > 0 && b !== null) td.append(el('span', {class: 'dd', text: kzDiff(key, v - b, b)}));
      tr.append(td);
    });
    body.append(tr);
  }
  t.append(el('thead', null, [kopf]), body);
}

/* ── Entwicklung 2025 bis 2030 ───────────────────────────────────────── */
const KZ_WAHL = [['gesamt', 'Gesamtergebnis'], ['ord', 'Operatives Ergebnis'], ['ert', 'Ertrag'], ['auf', 'Aufwand'], ['fiskal', 'Steuern'],
  ['transfer', 'Transferaufwand'], ['pers', 'Personalaufwand'], ['netInv', 'Nettoinvestitionen'], ['ekap', 'Eigenkapital']];
const KZ_TITEL = {gesamt: 'Gesamtergebnis der Erfolgsrechnung', ord: 'Operatives Ergebnis (ordentlicher Ertrag minus Aufwand)', ert: 'Ordentlicher Ertrag', auf: 'Ordentlicher Aufwand',
  fiskal: 'Fiskalertrag (Steuern)', transfer: 'Transferaufwand', pers: 'Personalaufwand', netInv: 'Nettoinvestitionen', ekap: 'Eigenkapital am Jahresende'};
const DEP_NETTO = {};
function depNetto(k){
  if(DEP_NETTO[k]) return DEP_NETTO[k];
  const i = 5 + JI[k], m = {};
  for(const z of D.z) m[z[0]] = (m[z[0]] || 0) + z[i];
  return DEP_NETTO[k] = m;
}
const FELD_IDX = {b27: 0, p28: 1, p29: 2, p30: 3};
function kzWert(k){
  if(st.bereich === null) return kzRoh(k, st.kz);
  if(st.bereich[0] === 'd'){ if(istPlan(k)) return null; const v = depNetto(k)[st.bereich.slice(1)]; return v === undefined ? null : v; }
  const f = D.felder.find(x => 'f' + x.nr === st.bereich), i = FELD_IDX[k];
  return !f || i === undefined ? null : f.netto[i] * 1000;
}
function kzTitel(){
  if(st.bereich === null) return KZ_TITEL[st.kz];
  if(st.bereich[0] === 'd') return `Nettoaufwand ${D.dep[st.bereich.slice(1)]}`;
  const f = D.felder.find(x => 'f' + x.nr === st.bereich);
  return `Nettoaufwand Aufgabenfeld ${f.name}`;
}
const kzUeber = () => st.bereich !== null ? (st.bereich[0] === 'd' ? 'Erfolgsrechnung, alle Konten des Departements' : 'Finanzplan, Kapitel 7') : st.kz === 'netInv' ? 'Investitionsrechnung' : st.kz === 'ekap' ? 'Bilanz' : 'Erfolgsrechnung';
function serienVerlauf(){
  const p = (k, j) => [j, IDX[k] === undefined ? null : kzWert(k), k];
  return {
    r: [p('r25', 2025)],
    b: [p('b25', 2025), p('b26', 2026), p('b27', 2027)],
    p: [p('b27', 2027), p('p28', 2028), p('p29', 2029), p('p30', 2030)],
  };
}
function zeichneVerlauf(){
  const box = $('#verlauf');
  const chips = $('#kzChips'); chips.innerHTML = '';
  KZ_WAHL.forEach(([k, t]) => { const b = el('button', {type: 'button', 'aria-pressed': String(st.bereich === null && st.kz === k), text: t}); b.addEventListener('click', () => { st.kz = k; st.bereich = null; zeichneVerlauf(); zeichneBereiche(); }); chips.append(b); });
  $('#kzBereich').value = st.bereich === null ? '' : st.bereich;
  $('#verlaufTitel').textContent = kzTitel();
  const S = serienVerlauf(), da = v => v !== null && v !== undefined;
  const W = Math.max(320, box.clientWidth || 900), schmal = W < 560;
  const H = schmal ? 250 : 300, L = schmal ? 46 : 60, R = schmal ? 16 : 24, T = 40, B = 30;
  const x = j => L + (W - L - R) * (j - J_MIN) / (J_MAX - J_MIN);
  const alle = [...S.r, ...S.b, ...S.p].map(q => q[1]).filter(da);
  let lo = Math.min(...alle), hi = Math.max(...alle);
  if(!alle.length){ lo = 0; hi = 1; }
  if(lo < 0 || hi <= 0){ lo = Math.min(lo, 0); hi = Math.max(hi, 0); } else { lo = Math.max(0, lo - (hi - lo) * 0.3); }
  const spanne = hi - lo || 1;
  const schritt = (() => { const roh = spanne / 5, p = Math.pow(10, Math.floor(Math.log10(roh))); return [1, 2, 2.5, 5, 10].map(f => f * p).find(s => s >= roh); })();
  lo = Math.floor(lo / schritt) * schritt; hi = Math.ceil(hi / schritt) * schritt;
  const y = v => T + (H - T - B) * (1 - (v - lo) / ((hi - lo) || 1));
  const dunkel = farbe('--linie-r'), grau = farbe('--linie-b'), fl = farbe('--karte');
  let s = `<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-label="${esc(kzTitel())}, ${J_MIN} bis ${J_MAX}">`;
  s += '<g class="gitter">';
  for(let v = lo; v <= hi + 1e-6; v += schritt) s += `<line x1="${L}" x2="${W - R}" y1="${y(v).toFixed(1)}" y2="${y(v).toFixed(1)}"${Math.abs(v) < 1e-6 ? ' style="stroke:var(--linie-2)"' : ''}/>`;
  s += '</g><g class="achse">';
  for(let v = lo; v <= hi + 1e-6; v += schritt) s += `<text x="${L - 8}" y="${(y(v) + 4).toFixed(1)}" text-anchor="end">${mio(v, schritt < 1e6 ? 1 : 0)}</text>`;
  for(let j = J_MIN; j <= J_MAX; j++) s += `<text x="${x(j).toFixed(1)}" y="${H - 8}" text-anchor="middle">${schmal ? "’" + String(j).slice(2) : j}</text>`;
  s += `<text x="${L - 8}" y="${T - 12}" text-anchor="end">Mio. Fr.</text></g>`;
  const xb = (x(2027) + x(2028)) / 2;
  s += `<g class="bruch"><line x1="${xb}" x2="${xb}" y1="${T - 14}" y2="${H - B}"/><text x="${xb - 5}" y="${T - 6}" text-anchor="end">Budget</text><text x="${xb + 5}" y="${T - 6}">Finanzplan</text></g>`;
  const pfad = (pts, stil) => { const p = pts.filter(q => da(q[1])); if(p.length < 2) return ''; return `<path d="${p.map((q, i) => (i ? 'L' : 'M') + x(q[0]).toFixed(1) + ',' + y(q[1]).toFixed(1)).join('')}" fill="none" ${stil}/>`; };
  s += pfad(S.b, `stroke="${grau}" stroke-width="2" stroke-dasharray="5 4"`);
  s += pfad(S.p, `stroke="${grau}" stroke-width="2" stroke-dasharray="1.5 3.5" stroke-linecap="round"`);
  s += pfad(S.r, `stroke="${dunkel}" stroke-width="2"`);
  const gewaehlt = st.sel.map((k, sidx) => ({k, sidx, j: DS[IDX[k]].j, v: kzWert(k)})).filter(g => da(g.v));
  const labelUnten = new Set();
  gewaehlt.forEach(g => { if(gewaehlt.some(h => h !== g && h.j === g.j && (h.v > g.v || (h.v === g.v && h.sidx < g.sidx)))) labelUnten.add(g.k); });
  const punkt = (j, v, k, art) => {
    if(!da(v)) return '';
    const sidx = st.sel.indexOf(k); let o = '';
    if(sidx >= 0){ o += `<circle cx="${x(j).toFixed(1)}" cy="${y(v).toFixed(1)}" r="10" fill="none" stroke="${slotFarbe(sidx)}" stroke-width="3"/>`; o += `<text x="${x(j).toFixed(1)}" y="${(labelUnten.has(k) ? y(v) + 27 : y(v) - 15).toFixed(1)}" text-anchor="middle" style="font-size:12px;font-weight:700;fill:var(--text)">${SLOT[sidx]}</text>`; }
    if(art === 'r') o += `<circle cx="${x(j).toFixed(1)}" cy="${y(v).toFixed(1)}" r="4.5" fill="${dunkel}" stroke="${fl}" stroke-width="2"/>`;
    else if(art === 'p') o += `<path d="M${x(j).toFixed(1)},${(y(v) - 5.5).toFixed(1)}l5.5,5.5l-5.5,5.5l-5.5,-5.5z" fill="${fl}" stroke="${grau}" stroke-width="2"/>`;
    else o += `<circle cx="${x(j).toFixed(1)}" cy="${y(v).toFixed(1)}" r="4.5" fill="${fl}" stroke="${grau}" stroke-width="2"/>`;
    return o;
  };
  for(const [j, v, k] of S.b) s += punkt(j, v, k, 'b');
  for(const [j, v, k] of S.p) if(j > 2027) s += punkt(j, v, k, 'p');
  for(const [j, v, k] of S.r) s += punkt(j, v, k, 'r');
  s += `<line id="vlKreuz" x1="0" x2="0" y1="${T}" y2="${H - B}" stroke="${farbe('--text-leise')}" stroke-width="1" style="display:none"/>`;
  s += `<rect x="${L}" y="${T}" width="${W - L - R}" height="${H - T - B}" fill="transparent" id="vlFlaeche"/></svg>`;
  box.innerHTML = s;
  const flaeche = $('#vlFlaeche'), kreuz = $('#vlKreuz'), tip = $('#tip');
  const jahrVon = ev => { const r = box.querySelector('svg').getBoundingClientRect(); return Math.max(J_MIN, Math.min(J_MAX, Math.round(J_MIN + ((ev.clientX - r.left) * W / r.width - L) / (W - L - R) * (J_MAX - J_MIN)))); };
  flaeche.addEventListener('pointermove', ev => {
    const j = jahrVon(ev);
    kreuz.setAttribute('x1', x(j)); kreuz.setAttribute('x2', x(j)); kreuz.style.display = '';
    tip.innerHTML = ''; tip.append(el('div', {class: 't', text: `${j} · ${kzTitel()}`}));
    const z = el('div', {class: 'z'});
    const zeile = (k, name, stil) => { if(IDX[k] === undefined) return; const v = kzWert(k); if(!da(v)) return; const i = el('i'); i.style.background = stil; z.append(i, el('span', {text: name}), el('b', {text: mio(v) + ' Mio.'})); };
    const jj = String(j).slice(2);
    zeile('r' + jj, 'Rechnung', dunkel); zeile('b' + jj, 'Budget' + (DS[IDX['b' + jj]] && DS[IDX['b' + jj]].vorlage ? ' (Vorlage)' : ''), grau); zeile('p' + jj, 'Finanzplan', grau);
    tip.append(z);
    if(st.kz === 'ekap' && st.bereich === null && j === 2026) tip.append(el('div', {class: 'd', text: 'Budget 2026 aktualisiert mit dem Abschluss 2025 (Ziffer 2.3).'}));
    const r = kzWert('r' + jj), b = kzWert('b' + jj);
    if(IDX['r' + jj] !== undefined && da(r) && da(b)) tip.append(el('div', {class: 'd', text: `Rechnung minus Budget: ${mioVz(r - b)} Mio. ${pct(r - b, b)}`}));
    tip.append(el('div', {class: 'd', text: 'Klick wählt den Datensatz dieses Jahres für den Vergleich.'}));
    platziereTip(ev);
  });
  flaeche.addEventListener('pointerleave', () => { kreuz.style.display = 'none'; tip.style.display = 'none'; });
  flaeche.addEventListener('click', ev => {
    const jj = String(jahrVon(ev)).slice(2);
    const k = ['r' + jj, 'b' + jj, 'p' + jj].find(q => IDX[q] !== undefined);
    if(k && !st.sel.includes(k)) waehle(k);
  });
  zeichneVerlaufTabelle(S);
}
function zeichneVerlaufTabelle(S){
  const t = $('#verlaufTab'); t.innerHTML = '';
  const kopf = el('tr', null, [el('th', {text: 'Jahr'}), el('th', {class: 'r', text: 'Rechnung'}), el('th', {class: 'r', text: 'Budget'}), el('th', {class: 'r', text: 'Finanzplan'})]);
  const body = el('tbody');
  const w = k => { if(IDX[k] === undefined) return '·'; const v = kzWert(k); return v === null || v === undefined ? '·' : mio(v) + ' Mio.'; };
  for(let j = J_MIN; j <= J_MAX; j++){ const jj = String(j).slice(2); body.append(el('tr', null, [el('td', {text: String(j)}), el('td', {class: 'r', text: w('r' + jj)}), el('td', {class: 'r', text: w('b' + jj) + (jj === '27' ? ' (Vorlage)' : '')}), el('td', {class: 'r', text: w('p' + jj)})])); }
  t.append(el('thead', null, [kopf]), body);
}
function platziereTip(ev){
  const tip = $('#tip'); tip.style.display = 'block';
  const w = tip.offsetWidth, h = tip.offsetHeight;
  let lx = ev.clientX + 14, ly = ev.clientY + 14;
  if(lx + w > window.innerWidth - 8) lx = ev.clientX - w - 14;
  if(ly + h > window.innerHeight - 8) ly = ev.clientY - h - 14;
  tip.style.left = Math.max(8, lx) + 'px'; tip.style.top = Math.max(8, ly) + 'px';
}

/* ── Departemente und Aufgabenfelder ─────────────────────────────────── */
function spark(werte, w, h){
  // Skala aus den eigenen Werten: gezeigt wird der Verlauf, die Beträge stehen daneben
  const v = werte.filter(q => q !== null);
  if(v.length < 2) return '';
  let lo = Math.min(...v), hi = Math.max(...v);
  const rand = Math.max((hi - lo) * 0.15, Math.abs(hi) * 0.02, 1); lo -= rand; hi += rand;
  const xs = i => 3 + (w - 6) * i / (werte.length - 1), ys = q => 3 + (h - 6) * (1 - (q - lo) / ((hi - lo) || 1));
  let s = `<svg class="spark" viewBox="0 0 ${w} ${h}" aria-hidden="true">`;
  const pts = werte.map((q, i) => q === null ? null : [xs(i), ys(q)]).filter(Boolean);
  s += `<path d="${pts.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ',' + p[1].toFixed(1)).join('')}" fill="none" stroke="${farbe('--linie-r')}" stroke-width="1.6"/>`;
  const l = pts[pts.length - 1];
  return s + `<circle cx="${l[0]}" cy="${l[1]}" r="2.6" fill="${farbe('--text')}"/></svg>`;
}
function zeichneBereiche(){
  // Departemente: Nettoaufwand über alle Konten, wie Ziffer 4.4.2 des Berichts
  const t = $('#departemente'); t.innerHTML = '';
  const ks = ['b25', 'r25', 'b26', 'b27'];
  t.append(el('thead', null, [el('tr', null, [el('th', {text: 'Departement'}), ...ks.map(k => el('th', {class: 'r' + (k === 'b25' ? ' h-m' : ''), text: dsT(k).replace('Budget', 'B').replace('Rechnung', 'R') + (DS[IDX[k]].vorlage ? ' Vorlage' : '')})), el('th', {class: 'r h-s', text: 'B 2027 − B 2026'})])]));
  const body = el('tbody');
  const summe = {};
  for(const dep of Object.keys(D.dep)){
    const tr = el('tr', {class: 'klick' + (st.bereich === 'd' + dep ? ' aktiv' : ''), tabindex: '0'});
    tr.append(el('td', {text: D.dep[dep]}));
    ks.forEach(k => { const v = depNetto(k)[dep] || 0; summe[k] = (summe[k] || 0) + v; tr.append(el('td', {class: 'r' + (k === 'b25' ? ' h-m' : ''), text: mio(v)})); });
    const d = (depNetto('b27')[dep] || 0) - (depNetto('b26')[dep] || 0);
    tr.append(el('td', {class: 'r h-s', text: `${mioVz(d, Math.abs(d) < 1e5 ? 2 : 1)} ${pct(d, depNetto('b26')[dep] || 0)}`}));
    const wahl = () => { st.bereich = 'd' + dep; zeichneVerlauf(); zeichneBereiche(); $('#entwicklung').scrollIntoView({behavior: 'smooth', block: 'start'}); };
    tr.addEventListener('click', wahl); tr.addEventListener('keydown', ev => { if(ev.key === 'Enter') wahl(); });
    body.append(tr);
  }
  const tr = el('tr', {class: 'summe'}); tr.append(el('td', {text: 'Total: Aufwand minus Ertrag'}));
  ks.forEach(k => tr.append(el('td', {class: 'r' + (k === 'b25' ? ' h-m' : ''), text: mio(summe[k])})));
  tr.append(el('td', {class: 'r h-s', text: mioVz(summe.b27 - summe.b26)}));
  body.append(tr); t.append(body);
  // Aufgabenfelder des Finanzplans
  const f = $('#felder'); f.innerHTML = '';
  f.append(el('thead', null, [el('tr', null, [el('th', {text: 'Aufgabenfeld'}), el('th', {class: 'h-s', text: '2027 bis 2030'}), el('th', {class: 'r', text: 'B 2027'}), el('th', {class: 'r h-m', text: 'FP 2028'}), el('th', {class: 'r h-m', text: 'FP 2029'}), el('th', {class: 'r', text: 'FP 2030'}), el('th', {class: 'r h-s', text: '2030 − 2027'}), el('th', {class: 'r h-m', text: 'Summe 2027–2030'})])]));
  const fb = el('tbody'), fs = [0, 0, 0, 0];
  for(const x of D.felder){
    const tr = el('tr', {class: 'klick' + (st.bereich === 'f' + x.nr ? ' aktiv' : ''), tabindex: '0'});
    const w = x.netto.map(v => v * 1000); w.forEach((v, i) => fs[i] += v);
    const tdS = el('td', {class: 'h-s'}); tdS.innerHTML = spark(w, 120, 28);
    tr.append(el('td', {text: x.name + (x.netto[0] < 0 ? ' (Nettoertrag)' : '')}), tdS, el('td', {class: 'r', text: mio(w[0])}), el('td', {class: 'r h-m', text: mio(w[1])}), el('td', {class: 'r h-m', text: mio(w[2])}), el('td', {class: 'r', text: mio(w[3])}),
      el('td', {class: 'r h-s', text: `${mioVz(w[3] - w[0])} ${pct(w[3] - w[0], w[0])}`}), el('td', {class: 'r h-m', text: mio(x.kumuliert * 1000)}));
    const wahl = () => { st.bereich = 'f' + x.nr; zeichneVerlauf(); zeichneBereiche(); $('#entwicklung').scrollIntoView({behavior: 'smooth', block: 'start'}); };
    tr.addEventListener('click', wahl); tr.addEventListener('keydown', ev => { if(ev.key === 'Enter') wahl(); });
    fb.append(tr);
  }
  const ts = el('tr', {class: 'summe'});
  ts.append(el('td', {text: 'Total: Aufwandüberschuss'}), el('td', {class: 'h-s'}), el('td', {class: 'r', text: mio(fs[0])}), el('td', {class: 'r h-m', text: mio(fs[1])}), el('td', {class: 'r h-m', text: mio(fs[2])}), el('td', {class: 'r', text: mio(fs[3])}), el('td', {class: 'r h-s', text: mioVz(fs[3] - fs[0])}), el('td', {class: 'r h-m', text: mio(D.felder.reduce((a, x) => a + x.kumuliert * 1000, 0))}));
  fb.append(ts); f.append(fb);
}

/* ── Vergleich: Icicles und Tabelle ──────────────────────────────────── */
function zeichneDrill(){
  const ir = st.rechnung === 'ir';
  $$('#drillSteuer .chips button').forEach(b => {
    const f = b.dataset.feld, w = b.dataset.wert;
    b.setAttribute('aria-pressed', String(String(st[f]) === w));
    if(f === 'gl' && w === 'inst') { b.disabled = gesperrt() && !ir; b.title = b.disabled ? 'Der Finanzplan liegt nur nach Sachgruppen vor.' : ''; }
    if(f === 'umfang') b.disabled = ir;
  });
  $('#ansA').textContent = ir ? 'Ausgaben' : 'Aufwand';
  $('#ansE').textContent = ir ? 'Einnahmen' : 'Ertrag';
  $('#ansN').textContent = ir ? 'Netto' : 'Netto';
  const weg = aktuellerKnoten(), jetzt = weg[weg.length - 1];
  const kr = $('#krume'); kr.innerHTML = '';
  weg.forEach((n, i) => {
    if(i === weg.length - 1) kr.append(el('span', {class: 'jetzt', text: knotenName(n)}));
    else { const b = el('button', {type: 'button', text: knotenName(n)}); b.addEventListener('click', () => { st.pfad = st.pfad.slice(0, i); st.markiert = null; zeichneDrill(); hashSchreiben(); }); kr.append(b, el('span', {class: 'sep', text: '›'})); }
  });
  zeichneIcicles(jetzt);
  zeichneTabelle(jetzt);
}
function zeichneIcicles(jetzt){
  const box = $('#icicles'); box.innerHTML = '';
  const W = Math.max(300, box.clientWidth || 900), H1 = 38, H2 = 24, G = 3;
  const kinder = kinderSortiert(jetzt);
  const summen = st.sel.map((_, s) => kinder.reduce((a, c) => a + pos(wert(c, s)), 0));
  const maxT = Math.max(1, ...summen);
  st.sel.forEach((k, s) => {
    const wrap = el('div', {class: 'ic'}), kopf = el('div', {class: 'ic-kopf'});
    const sw = el('span'); sw.style.cssText = `display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:6px;vertical-align:-1px;background:${slotFarbe(s)}`;
    const l = el('span'); l.append(sw, el('b', {text: `${SLOT[s]} · ${dsLang(k)}`}));
    const v = wert(jetzt, s);
    const dv = v - wert(jetzt, 0), st2 = Math.abs(v) < 1e7 ? 2 : 1;
    kopf.append(l, el('span', {class: 'wert', text: `${ansichtName()} ${mio(v, st2)} Mio. Fr.` + (s > 0 ? ` (${mioVz(dv, st2)} Mio.${pct(dv, wert(jetzt, 0)) ? ', ' + pct(dv, wert(jetzt, 0)) : ''})` : '')}));
    wrap.append(kopf);
    if(!kinder.some(c => pos(wert(c, s)) > 0)){
      const leer = istPlan(k) && jetzt.id === 'root' && st.rechnung === 'ir' ? 'Der Finanzplan führt die Investitionen nur als Total.'
        : istPlan(k) && jetzt.id !== 'root' ? 'Der Finanzplan liegt nur nach Sachgruppen vor.'
        : jetzt.v[s][0] || jetzt.v[s][1] ? `Keine positiven Beträge in der Ansicht ${ansichtName()}.` : `${dsT(k)}: keine Beträge auf dieser Ebene.`;
      wrap.append(el('div', {class: 'keine', text: leer})); box.append(wrap); return;
    }
    const hoehe = H1 + G + H2, fS = slotFarbe(s), fH = slotHell(s), tS = textAuf(fS), tH = textAuf(fH);
    let svg = `<svg viewBox="0 0 ${W} ${hoehe}" width="${W}" height="${hoehe}" role="img" aria-label="${esc(dsT(k))}: Aufteilung ${esc(jetzt.name)}">`;
    svg += `<rect class="leerband" x="0" y="0" width="${W}" height="${H1}" rx="3"/>`;
    let x = 0;
    for(const c of kinder){
      const w = W * pos(wert(c, s)) / maxT; if(w <= 0) continue;
      const bf = befundeFuer(c.id), mark = bf.d.length ? '▲ ' : '';
      svg += `<rect class="seg" data-id="${esc(c.id)}" x="${(x + 1).toFixed(2)}" y="0" width="${Math.max(w - 2, .6).toFixed(2)}" height="${H1}" rx="3" fill="${fS}"/>`;
      if(w > 58){ svg += `<text x="${(x + 7).toFixed(1)}" y="15" fill="${tS}" font-weight="700">${esc(kurz(mark + knotenName(c), Math.floor((w - 10) / 6.3)))}</text>`; if(w > 100) svg += `<text x="${(x + 7).toFixed(1)}" y="30" fill="${tS}">${mio(wert(c, s))} Mio.</text>`; }
      const enkel = [...c.kinder.values()].map(g => [g, pos(wert(g, s))]).filter(q => q[1] > 0).sort((a, b) => b[1] - a[1]);
      const es = enkel.reduce((a, q) => a + q[1], 0);
      let x2 = x;
      for(const [g, gv] of enkel){
        const w2 = w * gv / es;
        if(w2 > .8) svg += `<rect class="seg" data-id="${esc(g.id)}" x="${(x2 + 1).toFixed(2)}" y="${H1 + G}" width="${Math.max(w2 - 2, .6).toFixed(2)}" height="${H2}" rx="2" fill="${fH}"/>`;
        if(w2 > 70) svg += `<text x="${(x2 + 6).toFixed(1)}" y="${H1 + G + 16}" fill="${tH}">${esc(kurz(knotenName(g), Math.floor((w2 - 10) / 6)))}</text>`;
        x2 += w2;
      }
      x += w;
    }
    const div = el('div'); div.innerHTML = svg + '</svg>'; wrap.append(div); box.append(wrap);
  });
  const tip = $('#tip');
  $$('rect.seg', box).forEach(r => {
    const n = KNOTEN.get(r.dataset.id);
    r.addEventListener('pointermove', ev => {
      tip.innerHTML = ''; tip.append(el('div', {class: 't', text: knotenName(n)}));
      const z = el('div', {class: 'z'});
      st.sel.forEach((k, s) => { const i = el('i', {class: 'k'}); i.style.background = slotFarbe(s); z.append(i, el('span', {text: SLOT[s] + ' · ' + dsLang(k)}), el('b', {text: fr(wert(n, s))})); });
      tip.append(z);
      if(st.sel.length > 1) tip.append(el('div', {class: 'd', text: st.sel.slice(1).map((k, i) => `${SLOT[i + 1]} minus A: ${frS(wert(n, i + 1) - wert(n, 0))} ${pct(wert(n, i + 1) - wert(n, 0), wert(n, 0))}`).join(' · ')}));
      const bf = befundeFuer(n.id);
      if(bf.d.length) tip.append(el('div', {class: 'd', text: `▲ ${bf.d.length} Prüfhinweis${bf.d.length > 1 ? 'e' : ''} zu diesem Eintrag`}));
      platziereTip(ev);
    });
    r.addEventListener('pointerleave', () => { tip.style.display = 'none'; });
    r.addEventListener('click', () => {
      tip.style.display = 'none';
      if(gesperrt()){ $('#planhinweis').scrollIntoView({behavior: 'smooth', block: 'center'}); return; }
      if(n.blatt){ setzePfad(n.eltern); st.markiert = n.id; } else setzePfad(n);
      zeichneDrill(); hashSchreiben();
    });
  });
}
function zeichneTabelle(jetzt){
  const t = $('#tabelle'); t.innerHTML = '';
  const kinder = kinderSortiert(jetzt).filter(c => st.sel.some((_, s) => sichtbar(c, s)));
  if(!kinder.length){ t.append(el('div', {class: 'leise', text: jetzt.kinder.size ? `Keine Einträge mit ${ansichtName()} auf dieser Ebene.` : 'Unterste Ebene erreicht.'})); return; }
  const k0 = kinder[0].id[0];
  const kopfName = {d: 'Departement', s: 'Dienststelle', f: 'Fonds', v: 'Vorhaben', k: 'Konto', a: 'Sachgruppe', b: 'Sachgruppe'}[k0] || 'Eintrag';
  const kopf = el('tr', null, [el('th', {text: kopfName + ' · ' + ansichtName() + ', Franken'})]);
  st.sel.forEach((k, s) => { const th = el('th', {class: 'r' + (s === 2 ? ' h-m' : '')}); const sw = el('span', {class: 'schl'}); sw.style.background = slotFarbe(s); th.append(sw, document.createTextNode(SLOT[s])); th.title = dsLang(k); kopf.append(th); });
  st.sel.slice(1).forEach((k, i) => kopf.append(el('th', {class: 'r' + (i === 1 ? ' h-m' : ' h-s'), text: `${SLOT[i + 1]} minus A`})));
  kopf.append(el('th', {class: 'r', text: ''}));
  const body = el('tbody');
  const max = Math.max(1, ...kinder.flatMap(c => st.sel.map((_, s) => Math.abs(wert(c, s)))));
  const zu = gesperrt();
  for(const c of kinder){
    const klickbar = !c.blatt && !zu && c.kinder.size;
    const tr = el('tr', {class: (klickbar ? 'klick' : '') + (st.markiert === c.id ? ' markiert' : ''), 'data-id': c.id, tabindex: klickbar ? '0' : null});
    const td0 = el('td');
    td0.append(el('span', {class: 'code', text: c.code}), document.createTextNode(c.name));
    const balk = el('div', {class: 'balk'});
    st.sel.forEach((_, s) => { const b = el('span'); b.style.width = (100 * Math.abs(wert(c, s)) / max).toFixed(1) + '%'; b.style.background = slotFarbe(s); if(wert(c, s) < 0) b.style.opacity = '.45'; balk.append(b); });
    td0.append(balk); tr.append(td0);
    st.sel.forEach((_, s) => tr.append(el('td', {class: 'r' + (s === 2 ? ' h-m' : ''), text: sichtbar(c, s) ? fr(wert(c, s)) : '·'})));
    st.sel.slice(1).forEach((_, i) => { const d = wert(c, i + 1) - wert(c, 0); const td = el('td', {class: 'r' + (i === 1 ? ' h-m' : ' h-s')}); td.append(el('div', {text: d ? frS(d) : '·'})); if(d && Math.abs(wert(c, 0)) >= 1) td.append(el('div', {class: 'leise klein', text: pct(d, wert(c, 0))})); tr.append(td); });
    const tdm = el('td', {class: 'r'});
    const km = kommentareFuer(c);
    if(km.length){ const b = el('button', {type: 'button', class: 'mk komm', title: 'Kommentar der Dienststelle', 'aria-label': 'Kommentar der Dienststelle', text: 'Kommentar'}); b.addEventListener('click', ev => { ev.stopPropagation(); zeigeKommentar(b, c, km); }); tdm.append(b); }
    const bf = befundeFuer(c.id);
    if(bf.d.length){ const b = el('button', {type: 'button', class: 'mk', title: 'Prüfhinweise zu diesem Eintrag', text: '▲ ' + bf.d.length}); b.addEventListener('click', ev => { ev.stopPropagation(); zeigePop(b, bf.d, c); }); tdm.append(b); }
    else if(bf.i.length){ const b = el('button', {type: 'button', class: 'mk indirekt', title: 'Prüfhinweise in tieferen Ebenen', text: bf.i.length + ' darunter'}); b.addEventListener('click', ev => { ev.stopPropagation(); zeigePop(b, bf.i, c); }); tdm.append(b); }
    tr.append(tdm);
    if(klickbar){ const go = () => { setzePfad(c); st.markiert = null; zeichneDrill(); hashSchreiben(); }; tr.addEventListener('click', go); tr.addEventListener('keydown', ev => { if(ev.key === 'Enter') go(); }); }
    body.append(tr);
  }
  const sum = el('tr', {class: 'summe'});
  sum.append(el('td', {text: 'Total ' + (jetzt.id === 'root' ? jetzt.name : knotenName(jetzt))}));
  st.sel.forEach((_, s) => sum.append(el('td', {class: 'r' + (s === 2 ? ' h-m' : ''), text: fr(wert(jetzt, s))})));
  st.sel.slice(1).forEach((_, i) => sum.append(el('td', {class: 'r' + (i === 1 ? ' h-m' : ' h-s'), text: frS(wert(jetzt, i + 1) - wert(jetzt, 0))})));
  const tdk = el('td', {class: 'r'}), kj = kommentareFuer(jetzt);
  if(kj.length){ const b = el('button', {type: 'button', class: 'mk komm', text: 'Kommentar'}); b.addEventListener('click', ev => { ev.stopPropagation(); zeigeKommentar(b, jetzt, kj); }); tdk.append(b); }
  sum.append(tdk);
  body.append(sum);
  t.append(el('table', {class: 'tab'}, [el('thead', null, [kopf]), body]));
  if(st.markiert){ const m = $(`tr[data-id="${CSS.escape(st.markiert)}"]`, t); if(m) setTimeout(() => m.scrollIntoView({behavior: 'smooth', block: 'center'}), 60); }
}
function popZeigen(anker){
  const pop = $('#pop'), r = anker.getBoundingClientRect();
  pop.style.display = 'block';
  const w = pop.offsetWidth;
  pop.style.left = Math.max(8, Math.min(window.scrollX + r.right - w, window.scrollX + window.innerWidth - w - 8)) + 'px';
  pop.style.top = (window.scrollY + r.bottom + 6) + 'px';
}
function zeigePop(anker, liste, knoten){
  const pop = $('#pop'); pop.innerHTML = '';
  pop.append(el('div', {class: 'kopf-pop', text: `${liste.length} Prüfhinweis${liste.length > 1 ? 'e' : ''}: ${knotenName(knoten)}`}));
  const ol = el('ol');
  liste.slice(0, 12).forEach(i => { const b = BF[i]; const li = el('li'); const bt = el('button', {type: 'button', text: `${b.nr}. ${b.titel}`}); bt.addEventListener('click', () => { pop.style.display = 'none'; oeffneBefund(i); }); li.append(bt); ol.append(li); });
  pop.append(ol);
  if(liste.length > 12) pop.append(el('div', {class: 'leise klein', text: `und ${liste.length - 12} weitere in der Liste der Prüfhinweise`}));
  popZeigen(anker);
}
function zeigeKommentar(anker, knoten, liste){
  const pop = $('#pop'); pop.innerHTML = '';
  pop.append(el('div', {class: 'kopf-pop', text: knotenName(knoten)}));
  liste.forEach(([k, s, t]) => { const p = el('p'); p.append(el('b', {text: `${SLOT[s]} · ${k === 'r25' ? 'Staatsrechnung 2025' : dsLang(k)}: `}), el('q', {text: t})); pop.append(p); });
  pop.append(el('div', {class: 'leise klein', text: 'Kommentar der Organisationseinheit im Dokument, im Wortlaut. Er begründet die Abweichung zum Vorjahresbudget, in der Staatsrechnung die Abweichung zum Budget.'}));
  popZeigen(anker);
}
document.addEventListener('click', ev => { const pop = $('#pop'); if(pop.style.display === 'block' && !pop.contains(ev.target) && !ev.target.classList.contains('mk')) pop.style.display = 'none'; });

/* ── Suche im Vergleich ──────────────────────────────────────────────── */
const SYNONYME = [['Lehrer', 'Lehrpersonen'], ['Schule', 'Schul'], ['Spital', 'Spital'], ['Polizei', 'Polizei'], ['Steuern', 'Steuer'], ['Axpo', 'Beteiligungen'],
  ['Krankenkasse', 'Prämienverbilligung'], ['Flüchtlinge', 'Flüchtling'], ['Gefängnis', 'Justizvollzug'], ['Bahn', 'Öffentlicher Verkehr'], ['Nationalbank', 'Nationalbank'],
  ['Finanzausgleich', 'NFA'], ['Sicherheitszentrum', 'PSZ']];
const norm = t => String(t).toLowerCase().replace(/ä/g, 'ae').replace(/ö/g, 'oe').replace(/ü/g, 'ue').replace(/ß/g, 'ss');
function suche(q){
  q = norm(q.trim()); if(q.length < 2) return [];
  const woerter = q.split(/\s+/), out = [];
  for(const n of KNOTEN.values()){
    if(n.id === 'root') continue;
    let txt = norm((n.code || '') + ' ' + n.name);
    for(const [von, zu] of SYNONYME) if(txt.includes(norm(zu))) txt += ' ' + norm(von);
    if(!woerter.every(w => txt.includes(w))) continue;
    const g = Math.max(...st.sel.map((_, s) => Math.abs(n.v[s][0]) + Math.abs(n.v[s][1])));
    out.push([n, n.blatt ? 2 : n.tiefe === 1 ? 0 : 1, txt.startsWith(q) || txt.includes(' ' + q) ? 0 : 1, g]);
  }
  out.sort((a, b) => a[1] - b[1] || a[2] - b[2] || b[3] - a[3]);
  return out.slice(0, 14).map(x => x[0]);
}
function zeigeSuche(){
  const inp = $('#sucheFeld'), ul = $('#sucheListe');
  const tr = suche(inp.value);
  ul.innerHTML = '';
  if(inp.value.trim().length < 2){ ul.hidden = true; return; }
  ul.hidden = false;
  if(!tr.length){ ul.append(el('li', {text: 'Nichts gefunden in der gewählten Rechnung und Gliederung.'})); return; }
  tr.forEach((n, i) => {
    const eltern = []; let x = n.eltern; while(x && x.id !== 'root'){ eltern.unshift(knotenName(x)); x = x.eltern; }
    const li = el('li', {role: 'option', 'aria-selected': String(i === 0)});
    const g = n.v[0][0] || n.v[0][1] ? fr(Math.abs(n.v[0][0]) >= Math.abs(n.v[0][1]) ? n.v[0][0] : n.v[0][1]) : '';
    li.append(el('span', {text: knotenName(n)}), el('b', {class: 'leise', text: g}), el('small', {text: (n.blatt ? (n.id[0] === 'v' ? 'Vorhaben' : 'Konto') : n.tiefe === 1 ? 'Ebene 1' : 'Gruppe') + (eltern.length ? ' · ' + eltern.join(' › ') : '')}));
    li.addEventListener('mousedown', ev => { ev.preventDefault(); springeZu(n); });
    ul.append(li);
  });
  ul._treffer = tr;
}
function springeZu(n){
  $('#sucheListe').hidden = true;
  if(gesperrt() && n.tiefe > 1){ $('#planhinweis').scrollIntoView({behavior: 'smooth', block: 'center'}); return; }
  // Hat der Treffer in der Ansicht keinen Betrag, auf die Seite wechseln, auf der er einen hat
  if(!st.sel.some((_, s) => sichtbar(n, s))) st.ansicht = st.sel.some((_, s) => Math.abs(n.v[s][0]) > .004) ? 'A' : 'E';
  if(n.blatt || !n.kinder.size){ setzePfad(n.eltern); st.markiert = n.id; } else { setzePfad(n.eltern && n.eltern.id !== 'root' ? n.eltern : BAUM); st.markiert = n.id; }
  zeichneDrill(); hashSchreiben();
  $('#vergleichTitel').scrollIntoView({behavior: 'smooth', block: 'start'});
}

/* ── CSV der aktuellen Tabelle ───────────────────────────────────────── */
function csv(){
  const weg = aktuellerKnoten(), jetzt = weg[weg.length - 1];
  const zeilen = [['Ebene', 'Code', 'Bezeichnung', ...st.sel.map(k => dsLang(k) + ' ' + ansichtName())]];
  for(const c of kinderSortiert(jetzt)) zeilen.push([weg.map(n => n.name).join(' > '), c.code, c.name, ...st.sel.map((_, s) => wert(c, s).toFixed(0))]);
  const text = '﻿' + zeilen.map(z => z.map(v => /[;"\n]/.test(v) ? '"' + String(v).replace(/"/g, '""') + '"' : v).join(';')).join('\n');
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([text], {type: 'text/csv;charset=utf-8'}));
  a.download = 'finanzspiegel-' + st.rechnung + '-' + st.sel.join('-') + '-' + (jetzt.code || 'total').replace(/[^\w.]+/g, '') + '.csv';
  document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}

/* ── Prüfhinweise ────────────────────────────────────────────────────── */
const TYPEN = D.typen || [];
function bfGefiltert(){
  const f = st.bf, q = norm(f.q.trim());
  return BF.map((b, i) => [b, i]).filter(([b]) =>
    (f.typ === 'alle' || b.typ === f.typ) && (f.ds === 'alle' || b.ds.includes(f.ds)) &&
    (f.min === 0 || b.stufe <= f.min) && (!f.nurAuswahl || b.ds.some(k => st.sel.includes(k))) &&
    (!q || norm(b.titel + ' ' + b.fakten.join(' ') + ' ' + b.komm.map(x => x[1] + ' ' + x[2]).join(' ')).includes(q)));
}
function zeichneBefunde(){
  const typen = $('#bfTypen'); typen.innerHTML = '';
  const f = st.bf;
  const basis = BF.filter(b => (f.ds === 'alle' || b.ds.includes(f.ds)) && (f.min === 0 || b.stufe <= f.min) && (!f.nurAuswahl || b.ds.some(k => st.sel.includes(k))));
  [['alle', 'Alle'], ...TYPEN.map(t => [t, t])].forEach(([k, t]) => {
    if(k !== 'alle' && !BF.some(b => b.typ === k)) return;
    const n = k === 'alle' ? basis.length : basis.filter(b => b.typ === k).length;
    const b = el('button', {type: 'button', 'aria-pressed': String(f.typ === k)}); b.append(document.createTextNode(t), el('em', {text: String(n)}));
    b.addEventListener('click', () => { st.bf.typ = k; st.bfZahl = 30; zeichneBefunde(); });
    typen.append(b);
  });
  const liste = $('#bfListe'); liste.innerHTML = '';
  const g = bfGefiltert();
  $('#bfZahl').textContent = `${g.length} von ${BF.length} Prüfhinweisen`;
  g.slice(0, st.bfZahl).forEach(([b, i]) => {
    const li = el('li', {class: 'bf' + (st.bfOffen.has(i) ? ' offen' : ''), id: 'bf-' + b.nr});
    const kopf = el('button', {type: 'button', class: 'bf-kopf', 'aria-expanded': String(st.bfOffen.has(i))});
    const meta = el('span', {class: 'meta'}); meta.append(el('span', {class: 'typ', text: b.typ}), document.createTextNode(b.ds.map(dsLang).join(', ') + (b.rechnung === 'ir' ? ' · Investitionsrechnung' : '')));
    kopf.append(el('span', {class: 'nr', text: b.nr + '.'}), el('span', {class: 'titel', text: b.titel}), el('span', {class: 'betr', text: mioVz(b.chf, 2) + ' Mio.'}), meta);
    kopf.addEventListener('click', () => { if(st.bfOffen.has(i)) st.bfOffen.delete(i); else st.bfOffen.add(i); li.classList.toggle('offen'); kopf.setAttribute('aria-expanded', String(st.bfOffen.has(i))); });
    const body = el('div', {class: 'bf-body'});
    body.append(el('ol', null, b.fakten.map(x => el('li', {text: x}))));
    if(b.komm && b.komm.length){
      body.append(el('div', {class: 'komm-titel', text: b.komm_titel + ':'}));
      b.komm.forEach(([k, wo, t]) => { const q = el('blockquote'); q.append(el('b', {text: wo + ': '}), document.createTextNode('«' + t + '»')); body.append(q); });
    }
    const zeig = el('button', {type: 'button', class: 'knopf', text: 'Im Vergleich zeigen'});
    zeig.addEventListener('click', () => zeigeImVergleich(b));
    body.append(zeig);
    li.append(kopf, body); liste.append(li);
  });
  const mehr = $('#bfMehr'); mehr.innerHTML = '';
  if(g.length > st.bfZahl){ const b = el('button', {type: 'button', class: 'knopf', text: `Weitere ${Math.min(30, g.length - st.bfZahl)} anzeigen`}); b.addEventListener('click', () => { st.bfZahl += 30; zeichneBefunde(); }); mehr.append(b); }
}
function zeigeImVergleich(b){
  st.sel = b.ds.filter(k => IDX[k] !== undefined).slice(0, 3);
  st.rechnung = b.rechnung || 'er'; st.gl = b.gl || 'inst'; st.ansicht = b.ansicht || 'N'; st.umfang = b.umfang || 'alle';
  baum();
  st.pfad = b.pfad.slice(); st.markiert = b.markiert || null;
  neu(true);
  $('#vergleichTitel').scrollIntoView({behavior: 'smooth', block: 'start'});
}
function oeffneBefund(i){
  const b = BF[i];
  st.bf = {typ: 'alle', ds: 'alle', min: 0, nurAuswahl: false, q: ''};
  $('#bfDs').value = 'alle'; $('#bfMin').value = '0'; $('#bfNur').checked = false; $('#bfSuche').value = '';
  const p = bfGefiltert().findIndex(([, j]) => j === i);
  st.bfZahl = Math.max(30, p + 10);
  st.bfOffen.add(i);
  zeichneBefunde();
  const li = document.getElementById('bf-' + b.nr);
  if(li){ li.classList.add('markiert'); li.scrollIntoView({behavior: 'smooth', block: 'center'}); setTimeout(() => li.classList.remove('markiert'), 2500); }
}

/* ── Adresse (Hash) für geteilte Ansichten ───────────────────────────── */
function hashSchreiben(){
  const h = new URLSearchParams({d: st.sel.join(','), r: st.rechnung, g: st.gl, a: st.ansicht, u: st.umfang, p: st.pfad.join('/')});
  history.replaceState(null, '', '#' + h.toString());
}
function hashLesen(){
  try{
    const h = new URLSearchParams(location.hash.slice(1));
    const d = (h.get('d') || '').split(',').filter(k => IDX[k] !== undefined).slice(0, 3);
    if(d.length) st.sel = d;
    if(['er', 'ir'].includes(h.get('r'))) st.rechnung = h.get('r');
    if(['inst', 'art'].includes(h.get('g'))) st.gl = h.get('g');
    if(['A', 'E', 'N'].includes(h.get('a'))) st.ansicht = h.get('a');
    if(['ord', 'alle'].includes(h.get('u'))) st.umfang = h.get('u');
    if(h.get('p')) st.pfad = h.get('p').split('/').filter(Boolean);
  }catch(e){}
}

/*__GRAFIK__*/

/* ── Start ───────────────────────────────────────────────────────────── */
function init(){
  hashLesen();
  $$('#drillSteuer .chips button').forEach(b => b.addEventListener('click', () => {
    if(b.disabled) return;
    const f = b.dataset.feld, w = b.dataset.wert;
    if(st[f] === w) return;
    st[f] = w;
    if(f === 'rechnung' || f === 'gl' || f === 'umfang'){ st.pfad = []; st.markiert = null; baum(); }
    zeichneDrill(); hashSchreiben();
  }));
  $$('#schnell button').forEach(b => b.addEventListener('click', () => { st.sel = b.dataset.sel.split(','); st.pfad = []; st.markiert = null; neu(); }));
  const selB = $('#kzBereich');
  const og1 = el('optgroup', {label: 'Departement, Budget und Rechnung 2025 bis 2027'});
  Object.entries(D.dep).forEach(([c, t]) => og1.append(el('option', {value: 'd' + c, text: t})));
  const og2 = el('optgroup', {label: 'Aufgabenfeld, Budget 2027 und Finanzplan'});
  D.felder.forEach(x => og2.append(el('option', {value: 'f' + x.nr, text: x.name})));
  selB.append(og1, og2);
  selB.addEventListener('change', () => { st.bereich = selB.value === '' ? null : selB.value; zeichneVerlauf(); zeichneBereiche(); });
  $('#sucheFeld').addEventListener('input', zeigeSuche);
  $('#sucheFeld').addEventListener('focus', zeigeSuche);
  $('#sucheFeld').addEventListener('blur', () => setTimeout(() => { $('#sucheListe').hidden = true; }, 150));
  $('#sucheFeld').addEventListener('keydown', ev => {
    const ul = $('#sucheListe'), tr = ul._treffer || [], items = $$('li[role="option"]', ul);
    const akt = items.findIndex(li => li.getAttribute('aria-selected') === 'true');
    if(ev.key === 'ArrowDown' || ev.key === 'ArrowUp'){ ev.preventDefault(); if(!items.length) return; const n = (akt + (ev.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length; items.forEach((li, i) => li.setAttribute('aria-selected', String(i === n))); items[n].scrollIntoView({block: 'nearest'}); }
    else if(ev.key === 'Enter'){ ev.preventDefault(); if(tr.length) springeZu(tr[Math.max(akt, 0)]); }
    else if(ev.key === 'Escape'){ ul.hidden = true; }
  });
  $('#csvKnopf').addEventListener('click', csv);
  ['b27', 'b26', 'r25', 'b25'].forEach(k => $('#bfDs').append(el('option', {value: k, text: dsLang(k)})));
  $('#bfDs').addEventListener('change', ev => { st.bf.ds = ev.target.value; st.bfZahl = 30; zeichneBefunde(); });
  $('#bfMin').addEventListener('change', ev => { st.bf.min = +ev.target.value; st.bfZahl = 30; zeichneBefunde(); });
  $('#bfNur').addEventListener('change', ev => { st.bf.nurAuswahl = ev.target.checked; st.bfZahl = 30; zeichneBefunde(); });
  $('#bfSuche').addEventListener('input', ev => { st.bf.q = ev.target.value; st.bfZahl = 30; zeichneBefunde(); });
  neu(true);
  zeichneBereiche();
  grafikInit();
  let rz; window.addEventListener('resize', () => { clearTimeout(rz); rz = setTimeout(() => { zeichneUeberblick(); zeichneVerlauf(); zeichneDrill(); zeichneBereiche(); }, 150); });
  if(window.matchMedia) window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => { zeichneRaster(); zeichneUeberblick(); zeichneKennzahlen(); zeichneVerlauf(); zeichneDrill(); zeichneBereiche(); });
}
if(document.fonts && document.fonts.ready) document.fonts.ready.then(init); else init();
})();
"""


def chips(feld: str, eintraege: list[tuple[str, str]], ids: list[str] | None = None) -> str:
    out = '<div class="chips">'
    for i, (w, t) in enumerate(eintraege):
        idattr = f' id="{ids[i]}"' if ids and ids[i] else ""
        out += f'<button type="button" data-feld="{feld}" data-wert="{e(w)}"{idattr}>{e(t)}</button>'
    return out + "</div>"


def mio(v: float, st: int = 1) -> str:
    return ("−" if v < 0 else "") + f"{abs(v) / 1e6:,.{st}f}".replace(",", "'")


def seite(D: dict) -> str:
    daten = json.dumps(D, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    pr = D.get("pruefung", {})
    q = {x.get("k"): x for x in D["quellen"] if x.get("k")}
    stand = ".".join(reversed(D["stand"].split("-")))
    b27 = next(j for j in D["jahre"] if j["k"] == "b27")
    er_summen = sum(v.get("er", {}).get("summen", 0) for k, v in pr.items() if k != "finanzplan")
    er_abw = sum(v.get("er", {}).get("abweichend", 0) for k, v in pr.items() if k != "finanzplan")
    ir_abw = sum(v.get("ir", {}).get("abweichend", 0) for k, v in pr.items() if k != "finanzplan")
    n_bf = len(D.get("befunde", []))
    S = D.get("regeln", {})
    chf = lambda v: f"{v:,.0f}".replace(",", "'")
    K = D["kz"]
    # Budget 2027: Vorlage bis zum Beschluss des Kantonsrates (Kennzeichen in daten.py, JAHRE)
    monate = ("Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
              "September", "Oktober", "November", "Dezember")
    pub = (q.get("budget2027") or {}).get("publiziert", "")
    pub27 = (f", publiziert am {int(pub[8:10])}. {monate[int(pub[5:7]) - 1]} {pub[:4]}"
             if len(pub) == 10 else "")
    vorlage27 = (" Bis der Kantonsrat das Budget beschlossen hat, ist dies die Vorlage; "
                 "die beschlossene Fassung ersetzt sie." if b27.get("vorlage") else "")
    fp_teil = "Teil der Vorlage zum Budget 2027" if b27.get("vorlage") else "Teil des Budgets 2027"

    quellen_zeilen = ""
    for k in ("budget2027", "budget2026", "rechnung2025"):
        x = q.get(k)
        if not x:
            continue
        p = pr.get(k, {})
        er, ir = p.get("er", {}), p.get("ir", {})
        pruef = ("keine Abweichung" if not er.get("abweichend") and not ir.get("abweichend")
                 else f"{er.get('abweichend', 0) + ir.get('abweichend', 0)} Abweichungen")
        quellen_zeilen += (
            f'<tr><td><a href="{e(x["url"])}" rel="noopener">{e(x["titel"])}</a><br><span class="leise klein">{e(x["datei"])}</span></td>'
            f'<td class="h-m">{e(x.get("fassung", ""))}</td><td class="h-s">{e(x.get("verwendet", ""))}</td>'
            f'<td class="r">{chf(er.get("konten", 0))} / {chf(ir.get("zeilen", 0))}</td><td class="r h-s">{pruef}</td></tr>')

    return f"""<!DOCTYPE html>
<html lang="de-CH">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Finanzspiegel Schaffhausen</title>
<meta name="description" content="Budget 2027, Finanzplan bis 2030, Budget 2026 und Staatsrechnung 2025 des Kantons Schaffhausen: bis zu drei Jahre im Vergleich, bis zum einzelnen Konto und Investitionsvorhaben.">
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
  <p class="lead">Budget 2027 mit Finanzplan bis 2030, Budget 2026 und Staatsrechnung 2025 des Kantons Schaffhausen.
  Bis zu drei Jahre nebeneinander, vom Gesamtbild bis zum einzelnen Konto und Investitionsvorhaben.</p>
</header>
<p class="stand">Stand der Daten {stand} · Budget 2027 und Finanzplan: {e(b27["fassung"])}; massgebend wird die Fassung, die der Kantonsrat beschliesst.</p>

<section aria-labelledby="wahlTitel">
<h2 id="wahlTitel">Jahre wählen <small>· bis zu drei, A ist der Bezug für alle Differenzen</small></h2>
<div class="karte">
  <div class="wahl-kopf">
    <div class="auswahl" id="auswahl" aria-live="polite"></div>
    <div class="schnell" id="schnell"><b>Schnellwahl</b>
      <button type="button" data-sel="b27,b26,r25">Budget 2027 und 2026, Rechnung 2025</button>
      <button type="button" data-sel="b25,r25">Budget und Rechnung 2025</button>
      <button type="button" data-sel="b27,p28,p30">Budget 2027, Finanzplan 2028 und 2030</button>
    </div>
  </div>
  <div class="raster"><table id="raster"></table></div>
  <p class="raster-legende">Zahl im Feld: Gesamtergebnis in Millionen Franken (Ertragsüberschuss +, Aufwandüberschuss −). Klick wählt ein Jahr oder nimmt es heraus.</p>
  <div class="hinweis" id="planhinweis" hidden></div>
</div>
</section>

<section aria-labelledby="wwTitelH">
<h2 id="wwTitelH">Woher, wohin <small id="wwTitel"></small></h2>
<div class="kacheln" id="kacheln"></div>
<div class="karte ww">
  <div id="ww"></div>
  <div class="legenden" id="legenden"></div>
  <p class="ergebnis" id="ergebnis"></p>
</div>
</section>

<section aria-labelledby="entwicklung">
<h2 id="entwicklung">Entwicklung 2025 bis 2030 <small>· Rechnung, Budget und Finanzplan</small></h2>
<p class="unter">Der Finanzplan 2028 bis 2030 ist {fp_teil}. Er liegt nur zusammengefasst vor: nach Sachgruppen, Aufgabenfeldern und als Bilanz.</p>
<div class="steuer">
  <div class="grp"><b>Kennzahl</b><div class="chips" id="kzChips"></div></div>
  <div class="grp"><b>Bereich, netto</b><select id="kzBereich"><option value="">nicht gewählt</option></select></div>
</div>
<div class="karte">
  <div class="werkzeug"><h3 id="verlaufTitel" style="margin:0"></h3><button type="button" class="knopf" data-grafik="entwicklung">Als Grafik</button></div>
  <div class="verlauf" id="verlauf"></div>
  <div class="legende-zeile">
    <span><svg viewBox="0 0 26 12"><line x1="0" x2="26" y1="6" y2="6" stroke="var(--linie-r)" stroke-width="2"/><circle cx="13" cy="6" r="3.5" fill="var(--linie-r)"/></svg>Rechnung</span>
    <span><svg viewBox="0 0 26 12"><line x1="0" x2="26" y1="6" y2="6" stroke="var(--linie-b)" stroke-width="2" stroke-dasharray="5 4"/><circle cx="13" cy="6" r="3.5" fill="var(--karte)" stroke="var(--linie-b)" stroke-width="2"/></svg>Budget</span>
    <span><svg viewBox="0 0 26 12"><line x1="0" x2="26" y1="6" y2="6" stroke="var(--linie-b)" stroke-width="2" stroke-dasharray="1.5 3.5" stroke-linecap="round"/><path d="M13,1.5l4.5,4.5l-4.5,4.5l-4.5,-4.5z" fill="var(--karte)" stroke="var(--linie-b)" stroke-width="1.8"/></svg>Finanzplan</span>
    <span><svg viewBox="0 0 26 12"><circle cx="13" cy="6" r="4.5" fill="none" stroke="var(--s1)" stroke-width="2.5"/></svg>gewählte Jahre A, B, C</span>
  </div>
  <details class="tabelle"><summary>Werte als Tabelle</summary><div class="inner"><table class="tab" id="verlaufTab"></table></div></details>
</div>
<h3>Nettoaufwand je Departement</h3>
<p class="unter klein">Aufwand minus Ertrag über alle Konten, wie Ziffer 4.4.2 des Berichts; negativ: Ertragsüberschuss (Finanzdepartement mit den Steuern). Millionen Franken. Klick zeigt das Departement im Zeitverlauf oben.</p>
<div class="karte" style="overflow-x:auto"><table class="tab" id="departemente"></table></div>
<h3>Finanzplan je Aufgabenfeld</h3>
<p class="unter klein">Nettoaufwand je Aufgabenfeld, Budget 2027 und Finanzplan 2028 bis 2030 (Kapitel 7 des Berichts), Millionen Franken. «Finanzen und Steuern» ist ein Nettoertrag. Klick zeigt das Aufgabenfeld im Zeitverlauf oben.</p>
<div class="karte" style="overflow-x:auto"><table class="tab" id="felder"></table></div>
</section>

<section aria-labelledby="vergleichTitel">
<h2 id="vergleichTitel">Vergleich <small>· Klick auf ein Feld oder eine Zeile geht eine Stufe tiefer</small></h2>
<p class="unter">Kennzahlen der gewählten Jahre, darunter die Aufteilung als Icicle: je Jahr ein Band auf derselben Skala, die Breite entspricht dem Betrag. Die obere Reihe zeigt die Einträge der geöffneten Ebene, die untere deren Unterteilung.</p>
<div class="karte" style="overflow-x:auto"><table class="tab kz-tab" id="kz"></table></div>
<div class="steuer" id="drillSteuer">
  <div class="grp"><b>Rechnung</b>{chips("rechnung", [("er", "Erfolgsrechnung"), ("ir", "Investitionsrechnung")])}</div>
  <div class="grp"><b>Gliederung</b>{chips("gl", [("inst", "Dienststelle"), ("art", "Sachgruppe")])}</div>
  <div class="grp"><b>Ansicht</b>{chips("ansicht", [("A", "Aufwand"), ("E", "Ertrag"), ("N", "Netto")], ["ansA", "ansE", "ansN"])}</div>
  <div class="grp"><b>Konten</b>{chips("umfang", [("ord", "ordentliche"), ("alle", "alle")])}</div>
</div>
<div class="werkzeug">
  <div class="suche"><label class="nur-sr" for="sucheFeld">Suche</label>
    <input id="sucheFeld" type="search" autocomplete="off" spellcheck="false" placeholder="Suche: Dienststelle, Konto oder Vorhaben">
    <ul id="sucheListe" role="listbox" hidden></ul>
  </div>
  <div class="knoepfe"><button type="button" class="knopf" data-grafik="kuchen">Als Grafik</button><button type="button" class="knopf" data-grafik="ringe">Ringe</button><button type="button" class="knopf" id="csvKnopf">Tabelle als CSV</button></div>
</div>
<nav class="krume" id="krume" aria-label="Ebenen"></nav>
<div class="karte"><div class="icicles" id="icicles"></div></div>
<div class="karte" id="tabelle" style="overflow-x:auto"></div>
</section>

<section aria-labelledby="pruefTitel">
<h2 id="pruefTitel">Prüfhinweise <small>· {n_bf} Stellen mit grossen Veränderungen oder Abweichungen</small></h2>
<p class="unter">Stellen, an denen Beträge sich gegenüber dem Vorjahr stark verändern, vom Budget abweichen oder zwischen Dokumenten nicht übereinstimmen. Jeder Hinweis nennt die Zahlen und die Kommentare der Dienststellen im Wortlaut und springt in den Vergleich. Die Hinweise sind Feststellungen, keine Bewertung; die Regeln stehen unter «Methode».</p>
<div class="bf-filter"><div class="grp"><b>Art des Hinweises</b><div class="bf-typen" id="bfTypen"></div></div></div>
<div class="bf-filter">
  <div class="grp"><b>Jahr</b><select id="bfDs"><option value="alle">alle</option></select></div>
  <div class="grp"><b>Betrag</b><select id="bfMin"><option value="0">alle</option><option value="2">ab 1 Mio. Franken</option><option value="1">ab 5 Mio. Franken</option></select></div>
  <div class="grp"><b>Suche</b><input id="bfSuche" type="search" placeholder="Wort oder Konto" style="height:34px;padding:4px 10px;border:1px solid var(--linie-2);border-radius:8px;background:var(--karte);color:var(--text);font:inherit;font-size:14px"></div>
  <label class="klein" style="display:flex;gap:6px;align-items:center;margin-bottom:6px"><input type="checkbox" id="bfNur"> nur zu den gewählten Jahren</label>
</div>
<p class="leise klein" id="bfZahl"></p>
<ul class="bf-liste" id="bfListe"></ul>
<div class="mehr" id="bfMehr"></div>
</section>

<section aria-labelledby="methodeTitel" class="methode">
<h2 id="methodeTitel">Methode und Quellen</h2>
<h3>Datengrundlage</h3>
<ol>
  <li>Budget 2027 inklusive Detailzahlen und Finanzplan 2027–2030, {e(b27["fassung"])}{pub27}.{vorlage27}</li>
  <li>Budget 2026 in der vom Kantonsrat am 17. November 2025 beschlossenen Fassung; Staatsrechnung 2025. Das Budget 2025 stammt aus der Vergleichsspalte der Staatsrechnung 2025.</li>
  <li>Gelesen sind je Dokument die Detailzahlen (Kapitel 6): Erfolgsrechnung je Konto mit den Kommentaren der Organisationseinheiten, Investitionsrechnung je Konto und Vorhaben. Der Finanzplan 2028–2030 liegt nur zusammengefasst vor: Sachgruppen (Ziffer 2.1), Nettoinvestitionen (2.2), Bilanz (2.3) und Aufgabenfelder (Kapitel 7).</li>
  <li>Selbstprüfung beim Lesen: Je Dokument und Spalte ist die Summe der Konten gleich der gedruckten Summe je Dienststelle, Fonds und Departement, in der Investitionsrechnung zusätzlich je Konto und Vorhaben. Erfolgsrechnung {chf(er_summen)} Summen, {er_abw} Abweichungen; Investitionsrechnung {ir_abw} Abweichungen. Die Summen je Sachgruppe und je Departement stimmen für Rechnung 2025, Budget 2026 und Budget 2027 mit den Ziffern 2.1 und 4.4.2 überein. Die Übersichtstabellen des Finanzplans sind nachgerechnet: {pr.get("finanzplan", {}).get("abweichend", 0)} Abweichungen.</li>
  <li>Wo Dokumente voneinander abweichen, gilt die spätere Publikation; die Abweichungen stehen unter den Prüfhinweisen (Dokumentenabgleich). Die Nettoinvestitionen des Budgets 2027 sind aus den Detailzahlen gerechnet ({mio(K["b27"]["netInv"])} Mio. Franken); die Übersicht des Berichts nennt 110.1 Mio.</li>
</ol>
<h3>Lesehilfe</h3>
<ol>
  <li>Konten «ordentliche»: Sachgruppen 30 bis 37 und 40 bis 47. Ihre Totale sind der ordentliche Aufwand und Ertrag des Berichts. «Alle» nimmt Ausserordentliches (38, 48, vor allem finanzpolitische Reserven), interne Verrechnungen (39, 49) und den Abschluss der Fonds im Eigenkapital (90) dazu; so summiert Kapitel 6 die Dienststellen.</li>
  <li>Netto: Aufwand minus Ertrag, in der Investitionsrechnung Ausgaben minus Einnahmen. Negativ heisst Ertragsüberschuss.</li>
  <li>Gliederung nach Dienststelle: Departement, Dienststelle, Fonds, Konto; kreditrechtlich verbindlich. Nach Sachgruppe: Artengliederung HRM2, zwei- und dreistellig, dann das Konto über alle Dienststellen.</li>
  <li>Investitionsrechnung: Vorhaben sind Verpflichtungskredite (VK) oder Budgetkredite. Das Budget gliedert Konto vor Vorhaben, die Staatsrechnung Vorhaben vor Konto; hier einheitlich Dienststelle, Vorhaben, Konto.</li>
  <li>Icicle: Flächen können nicht negativ sein. Einträge mit negativem Betrag, etwa Rückerstattungen, stehen nur in der Tabelle.</li>
  <li>Kommentar: Begründung der Dienststelle im Dokument, im Wortlaut. Im Budget bezieht er sich auf das Vorjahresbudget, in der Staatsrechnung auf das Budget desselben Jahres.</li>
  <li>Grafik (Knopf unten rechts, «Als Grafik» bei Entwicklung und Vergleich): PNG für Social Media (4:5), Präsentationen (16:9) oder Berichte (3:2), mit Quelle und Datenstand. Motive: Kuchen, Balkenliste, Ringdiagramm mit bis zu drei Jahren (A aussen), Woher und wohin, Entwicklung, Kennzahlen.</li>
</ol>
<h3>Regeln der Prüfhinweise</h3>
<ol>
  <li>Budget zu Vorjahresbudget: Nettoaufwand einer Dienststelle (alle Konten) im Budget 2027 um mindestens {chf(S.get("bb_chf", 0))} Franken und {int(S.get("bb_pct", 0) * 100)} % anders als im Budget 2026.</li>
  <li>Budget zu letzter Rechnung: dasselbe gegenüber der Rechnung 2025, ab {chf(S.get("br_chf", 0))} Franken und {int(S.get("br_pct", 0) * 100)} %.</li>
  <li>Rechnung zu Budget: Nettoaufwand einer Dienststelle in der Rechnung 2025 um mindestens {chf(S.get("rb_chf", 0))} Franken und {int(S.get("rb_pct", 0) * 100)} % anders als im Budget 2025.</li>
  <li>Strukturänderung: Dienststelle mit Beträgen ab {chf(S.get("neu_chf", 0))} Franken in einem der Budgets 2026 und 2027 und keinen im anderen.</li>
  <li>Investition Rechnung zu Budget: Nettoinvestition eines Vorhabens in der Rechnung 2025 um mindestens {chf(S.get("ir_rb_chf", 0))} Franken und {int(S.get("ir_rb_pct", 0) * 100)} % anders als im Budget 2025. Investition Budget zu Vorjahresbudget: Veränderung ab {chf(S.get("ir_bb_chf", 0))} Franken.</li>
  <li>Dokumentenabgleich: Vergleichsspalten im Dokument Budget 2027 gegen die Datensätze aus den früheren Dokumenten; Detailzahlen gegen die Übersichten des Berichts.</li>
  <li>Je Hinweis die {S.get("konten", 3)} Konten mit der grössten Veränderung und ihre Kommentare. Betrag in der Liste: Veränderung in Millionen Franken, Grundlage der Sortierung.</li>
</ol>
<h3>Quellen</h3>
<div style="overflow-x:auto"><table class="tab quellen">
<thead><tr><th>Dokument</th><th class="h-m">Fassung</th><th class="h-s">Verwendet für</th><th class="r">Konten ER / Zeilen IR</th><th class="r h-s">Selbstprüfung</th></tr></thead>
<tbody>{quellen_zeilen}</tbody></table></div>
</section>

<footer class="fuss">
<p><b>Stand</b> {stand}. Aufbereitung der publizierten Zahlen ohne Gewähr; massgebend sind die Dokumente des Kantons. {melden_knopf_html("melden-inline")}</p>
{kanal_html("Politspiegel folgen: der WhatsApp-Kanal meldet jede neue Auswertung", "fuss-kanal")}
{impressum_html()}
</footer>
</div>
<div class="tip" id="tip" role="tooltip"></div>
<button type="button" class="grafikknopf" id="grafikAuf" title="Grafik für Social Media, Präsentation oder Bericht erzeugen" aria-label="Grafik erzeugen" aria-haspopup="dialog">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-8 8"/></svg><span>Grafik</span></button>
<div class="grafiklage" id="grafikLage">
  <div class="grafikbox" role="dialog" aria-modal="true" aria-labelledby="grafikKopfTitel">
    <div class="grafikkopf"><h2 id="grafikKopfTitel">Grafik für Social Media, Präsentation oder Bericht</h2>
      <button type="button" class="grafikzu" id="grafikZu" aria-label="Schliessen">&times;</button></div>
    <div class="grafikbody">
      <div class="grafikwahl">
        <label class="feld" for="grafikMotiv">Motiv</label>
        <select id="grafikMotiv"></select>
        <div id="grafikEbeneZeile"><label class="feld" for="grafikEbene">Ebene</label><select id="grafikEbene"></select>
          <p class="grafikhinweis" id="grafikEbeneStand" hidden></p><p class="grafikhinweis" id="grafikEbeneHinweis" hidden></p></div>
        <div id="grafikTiefeZeile" hidden><label class="feld" for="grafikTiefe">Unterteilung</label><select id="grafikTiefe"><option value="naechste">nächste Ebene</option><option value="konten">alle Konten darunter</option></select></div>
        <div id="grafikSlotZeile" hidden><label class="feld" for="grafikSlot">Jahr</label><select id="grafikSlot"></select></div>
        <div id="grafikSkalaZeile" hidden><label class="feld" for="grafikSkala">Ringe</label><select id="grafikSkala"><option value="anteil">Anteile, jeder Ring 100 %</option><option value="betrag">Beträge, gemeinsame Skala</option></select></div>
        <label class="feld" for="grafikFormat">Format</label>
        <select id="grafikFormat"></select>
        <span class="feld" id="grafikHgName">Hintergrund</span>
        <div class="radio" role="radiogroup" aria-labelledby="grafikHgName"><label><input type="radio" name="grafikHg" value="weiss" checked> weiss</label><label><input type="radio" name="grafikHg" value="transparent"> transparent</label></div>
        <label class="feld" for="grafikTitel">Titel</label>
        <input type="text" id="grafikTitel" maxlength="140" autocomplete="off">
        <p class="grafiknote" id="grafikNote"></p>
        <div class="grafikknoepfe">
          <button type="button" class="btn" id="grafikLaden">Als PNG herunterladen</button>
          <button type="button" class="btn zweit" id="grafikKopie">In die Zwischenablage kopieren</button>
        </div>
        <p class="grafikmeldung" id="grafikMeldung" role="status" aria-live="polite"></p>
      </div>
      <div class="grafikvorschau" id="grafikVorschau"><canvas id="grafikCanvas" width="1080" height="1350" role="img" aria-label="Vorschau der Grafik"></canvas><p id="grafikMass"></p></div>
    </div>
  </div>
</div>
<div class="pop" id="pop"></div>
{melden_html("Finanzspiegel", schwebend=False)}
<script id="daten" type="application/json">{daten}</script>
<script>{JS.replace("/*__GRAFIK__*/", GRAFIK.read_text(encoding="utf-8"))}</script>
</body>
</html>
"""


def main() -> None:
    daten = json.loads((HIER / "daten" / "finanzspiegel.json").read_text(encoding="utf-8"))
    ziel = ROOT / "site" / "finanzen" / "index.html"
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(seite(daten), encoding="utf-8")
    print(f"{ziel.relative_to(ROOT)}: {ziel.stat().st_size / 1024:.0f} kB, {len(daten['z'])} Kontozeilen, "
          f"{len(daten['ir'])} Zeilen Investitionsrechnung, {len(daten.get('befunde', []))} Prüfhinweise")


if __name__ == "__main__":
    main()

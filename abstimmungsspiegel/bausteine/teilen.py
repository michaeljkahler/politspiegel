"""Bilder fuer Social Media, gezeichnet im Browser.

Wird von argumente.py eingebunden. Liefert drei Dinge: die Daten, die die
Seite als JSON mitnimmt (bild_daten), den Kasten mit Motivwahl und Vorschau
(HTML, CSS) und die Zeichenlogik (JS) fuer die Leinwand 1080 x 1350, das
Standardmass fuer Beitraege auf Instagram, LinkedIn und Facebook.

Warum im Browser und nicht beim Bauen: Es ist derselbe Weg wie im
Kantonsratsspiegel, und das Bild folgt so dem gewaehlten Hell- oder
Dunkelmodus. Der Preis: Es gibt kein fertiges PNG im Ordner, das als
Linkvorschau dienen koennte; dafuer steht weiterhin das Vorschaubild des
Politspiegels.

Motive:
  vorlage        Titel, Termin, worum es geht, bei Ja / bei Nein
  gegen          Gegenueberstellung: die Netzgrafik beider Seiten
  paar:<n>       das n-te Aussagenpaar, Pro und Contra untereinander
  kantonsrat     wie die Fraktionen abgestimmt haben
  karussell:<id> je Argument eine Folge von Folien mit allen Inhalten der Karte

Eine Regel zur Neutralitaet: Das Karussell zeigt eine Seite. Damit kein
Karussell ohne Gegenseite in Umlauf kommt, zeigt die letzte Folie immer die
Aussage der anderen Seite mit gleicher Nummer und deren Belegwert.
"""

from __future__ import annotations

import json


MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
          "September", "Oktober", "November", "Dezember"]


def datum_lang(iso: str) -> str:
    j, m, t = iso.split("-")
    return f"{int(t)}. {MONATE[int(m) - 1]} {j}"


def bild_daten(daten: dict, achsen: list, args: list, kr: dict | None,
               url: str, punkte, mittelwerte, seite_komitee: dict,
               seite_name: dict, typ_name: dict) -> str:
    """Was die Zeichenlogik braucht, als JSON-Text. Nur Text und Zahlen, keine
    Adressen ausser der eigenen: Das Bild soll fuer sich stehen."""
    v = daten["vorlage"]
    mp, _ = mittelwerte(args, achsen, "pro")
    mc, _ = mittelwerte(args, achsen, "contra")

    def summe(seite):
        sel = [a for a in args if a["seite"] == seite and a.get("typ") != "wertung"]
        return [sum(punkte(a, achsen)[0] for a in sel), sum(punkte(a, achsen)[1] for a in sel)]

    argumente = []
    for a in args:
        f = a.get("fundstelle") or {}
        grafiken = a.get("grafiken") or ([a["grafik"]] if a.get("grafik") else [])
        er, mo = punkte(a, achsen)
        argumente.append({
            "id": a["id"], "seite": a["seite"],
            "aussage": a["aussage"], "traeger": a.get("traeger", ""),
            "typ": a.get("typ", "tatsache"),
            "typ_name": typ_name.get(a.get("typ", "tatsache"), a.get("typ", "")),
            "schema": a.get("schema", ""),
            "offen": a.get("stand") == "fundstelle_offen",
            "fundstelle": {"titel": f.get("titel", ""), "datum": f.get("datum", "")} if f else None,
            "pruefung": a.get("pruefung") or {},
            "erreicht": er, "moeglich": mo,
            "trifft_zu": a.get("trifft_zu", ""), "fehlt": a.get("fehlt", ""),
            "zahlhinweis": a.get("zahlhinweis", ""),
            "kritische_fragen": [{"frage": k["frage"], "status": k["status"],
                                  "kommentar": k.get("kommentar", "")}
                                 for k in a.get("kritische_fragen", [])],
            "belege": [{"titel": b["titel"], "art": b.get("art", "")} for b in a.get("belege", [])],
            "grafiken": [{"datei": g["datei"], "titel": g["titel"],
                          "hinweis": g.get("hinweis", ""), "quelle": g["quelle"],
                          "eigen": g["quelle"].lower().startswith("eigene")} for g in grafiken],
        })

    d = {
        "url": url,
        "vorlage": {
            "titel": v["titel"], "untertitel": v.get("untertitel", ""),
            "ebene": v.get("ebene", ""), "datum": datum_lang(v["abstimmung"]),
            "worum": v.get("worum_geht_es", ""),
            "bei_ja": v.get("bei_ja", ""), "bei_nein": v.get("bei_nein", ""),
        },
        "seiten": {s: {"name": seite_name[s], "komitee": seite_komitee[s]} for s in ("pro", "contra")},
        "achsen": [{"id": a["id"], "kurz": a["kurz"]} for a in achsen],
        "mittel": {"pro": mp, "contra": mc},
        "summe": {"pro": summe("pro"), "contra": summe("contra")},
        "argumente": argumente,
        "kantonsrat": kr,
        "stand": daten.get("stand", ""),
    }
    # «</script>» darf im eingebetteten JSON nicht vorkommen.
    return json.dumps(d, ensure_ascii=False).replace("</", "<\\/")


CSS = r"""
.bildstart{position:fixed;left:18px;bottom:18px;z-index:30;display:flex;align-items:center;gap:8px;
  border:1px solid var(--linie);background:var(--karte);color:var(--text);border-radius:999px;
  padding:9px 16px;font-size:13.5px;cursor:pointer;font-family:Archivo,sans-serif;font-weight:600;
  box-shadow:0 2px 10px rgba(16,24,40,.10)}
.bildmodal{position:fixed;inset:0;z-index:80;background:rgba(8,12,16,.55);display:flex;
  align-items:center;justify-content:center;padding:22px}
.bildmodal[hidden]{display:none}
.bildbox{background:var(--grund);border:1px solid var(--linie);border-radius:16px;
  width:min(980px,100%);max-height:92vh;overflow:auto;box-shadow:0 24px 60px rgba(0,0,0,.3)}
.bildkopf{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:18px 22px;
  border-bottom:1px solid var(--linie);position:sticky;top:0;background:var(--grund);z-index:2}
.bildkopf h2{margin:0;font-size:19px}
.bildzu{background:none;border:0;font-size:26px;line-height:1;color:var(--text-leise);cursor:pointer;padding:0 4px}
.bildbody{display:grid;grid-template-columns:300px 1fr;gap:24px;padding:22px}
.bildwahl label{display:block;font-size:11px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;
  color:var(--text-leise);margin:14px 0 7px}
.bildwahl label:first-child{margin-top:0}
.bildwahl select{width:100%;background:var(--flaeche);border:1px solid var(--linie);border-radius:8px;
  padding:10px 12px;font-size:13.5px;color:var(--text)}
.bildnote{font-size:12.5px;color:var(--text-leise);line-height:1.5;margin:14px 0 14px}
.bildwahl .bildknopf{display:block;width:100%;margin-top:8px;border:1px solid var(--text);background:var(--text);
  color:var(--grund);border-radius:8px;padding:10px 12px;font-size:13.5px;font-family:Archivo,sans-serif;
  font-weight:600;cursor:pointer}
.bildwahl .bildknopf.leise{background:transparent;color:var(--text);border-color:var(--linie)}
.bildwahl .bildknopf[hidden]{display:none}
.bildregel{font-size:12px;color:var(--text-leise);line-height:1.5;margin:16px 0 0;padding-top:12px;
  border-top:1px solid var(--linie)}
.bildvorschau{display:flex;justify-content:center;align-items:flex-start}
.bildvorschau canvas{width:100%;max-width:340px;height:auto;border-radius:10px;border:1px solid var(--linie);
  box-shadow:0 8px 24px rgba(16,24,40,.12)}
@media (max-width:900px){.bildbody{grid-template-columns:1fr}.bildstart{left:14px;bottom:14px}}
@media print{.bildstart,.bildmodal{display:none}}
"""


HTML = """
<div class="bildmodal" id="bildModal" hidden>
  <div class="bildbox" role="dialog" aria-modal="true" aria-labelledby="bildTitel">
    <div class="bildkopf">
      <h2 id="bildTitel">Bild für Social Media</h2>
      <button type="button" class="bildzu" id="bildZu" aria-label="Schliessen">&times;</button>
    </div>
    <div class="bildbody">
      <div class="bildwahl">
        <label for="bildMotiv">Motiv</label>
        <select id="bildMotiv"></select>
        <div id="bildFolieWrap" hidden>
          <label for="bildFolie">Folie</label>
          <select id="bildFolie"></select>
        </div>
        <p class="bildnote">Hochformat 1080 × 1350, das Standardmass für Beiträge auf
        Instagram, LinkedIn und Facebook. Die Farben folgen dem gewählten Hell- oder
        Dunkelmodus der Seite.</p>
        <button type="button" class="bildknopf" id="bildLaden">Als PNG herunterladen</button>
        <button type="button" class="bildknopf leise" id="bildAlle" hidden>Alle Folien herunterladen</button>
        <p class="bildregel">Das Karussell zeigt die Karte einer Seite, Folie für Folie. Die letzte
        Folie zeigt immer die Aussage der Gegenseite mit gleicher Nummer, damit kein Bild ohne
        Gegenseite in Umlauf kommt. Bewertet wird der Beleg, nicht das Argument.</p>
      </div>
      <div class="bildvorschau"><canvas id="bildCanvas" width="1080" height="1350"></canvas></div>
    </div>
  </div>
</div>
<button type="button" class="bildstart" id="bildStart">
  <svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true">
    <rect x="2" y="3" width="12" height="10" rx="2" stroke="currentColor" stroke-width="1.6" fill="none"/>
    <circle cx="6" cy="7" r="1.4" fill="currentColor"/>
    <path d="M3 12l3.5-3.5 2.5 2.5 2-2L13 12" stroke="currentColor" stroke-width="1.6" fill="none" stroke-linejoin="round"/>
  </svg>Bild für Social Media</button>
"""


JS = r"""
(function(){
  var D = JSON.parse(document.getElementById('bild-daten').textContent);
  var W = 1080, H = 1350, M = 72, INNEN = W - 2*M;
  var $ = function(s){ return document.querySelector(s); };
  var FUSS = H - 132;          // oberhalb liegt der Inhalt, darunter das Wasserzeichen
  var BILDER = {};             // geladene Grafiken, Schluessel: Datei

  function farbe(n){ return getComputedStyle(document.documentElement).getPropertyValue(n).trim() || '#888'; }
  function palette(){
    return { bg: farbe('--grund'), karte: farbe('--karte'), flaeche: farbe('--flaeche'),
             ink: farbe('--text'), leise: farbe('--text-leise'), linie: farbe('--linie'),
             pro: farbe('--pro'), contra: farbe('--contra'),
             segVoll: farbe('--seg-voll'), segLeer: farbe('--seg-leer') };
  }
  function seitenFarbe(p, s){ return s === 'pro' ? p.pro : p.contra; }
  function gegen(s){ return s === 'pro' ? 'contra' : 'pro'; }
  function ARCH(px, w){ return (w || 600) + ' ' + px + 'px Archivo, "Helvetica Neue", Arial, sans-serif'; }
  function SANS(px, w){ return (w || 400) + ' ' + px + 'px "Public Sans", "Helvetica Neue", Arial, sans-serif'; }

  /* ---- Text ------------------------------------------------------------ */
  function zeilen(x, str, maxW){
    var out = [];
    String(str || '').split(/\n\s*\n/).forEach(function(abs, i){
      if (i) out.push('');
      var z = '';
      abs.replace(/\s+/g, ' ').trim().split(' ').forEach(function(wd){
        var t = z ? z + ' ' + wd : wd;
        if (x.measureText(t).width > maxW && z) { out.push(z); z = wd; } else z = t;
      });
      if (z) out.push(z);
    });
    return out;
  }
  /* Zeichnet einen Text mit Umbruch und gibt die naechste freie Zeile zurueck.
     Ueberzaehlige Zeilen fallen weg; die letzte bekommt eine Auslassung, damit
     ein Schnitt als Schnitt erkennbar ist und nicht als Ende des Satzes. */
  function text(x, str, px, y, maxW, lh, maxLines){
    var zs = zeilen(x, str, maxW);
    if (maxLines && zs.length > maxLines) {
      zs = zs.slice(0, maxLines);
      var l = zs[maxLines-1];
      while (l.length && x.measureText(l + ' …').width > maxW) l = l.replace(/\s*\S+$/, '');
      zs[maxLines-1] = l + ' …';
    }
    zs.forEach(function(z){ if (z) x.fillText(z, px, y); y += z ? lh : lh * 0.55; });
    return y;
  }
  function hoehe(x, str, maxW, lh, maxLines){
    var zs = zeilen(x, str, maxW);
    if (maxLines && zs.length > maxLines) zs = zs.slice(0, maxLines);
    var h = 0; zs.forEach(function(z){ h += z ? lh : lh * 0.55; }); return h;
  }
  /* Fliesstext, der den Platz nutzt: die groesste Schrift aus der Reihe, bei
     der der ganze Text in die freie Hoehe passt. Passt er auch in der
     kleinsten nicht, wird dort gekuerzt. So bleibt eine kurze Antwort gross
     und eine lange lesbar, statt beide gleich klein zu setzen. */
  function fliess(x, str, px, y, maxW, frei, groessen){
    groessen = groessen || [34, 30, 27, 24];
    for (var i = 0; i < groessen.length; i++){
      var g = groessen[i], lh = Math.round(g * 1.45);
      x.font = SANS(g, 400);
      if (hoehe(x, str, maxW, lh) <= frei || i === groessen.length - 1)
        return text(x, str, px, y, maxW, lh, Math.floor(frei / lh));
    }
  }
  function linie(x, x1, y1, x2, y2, f, b){
    x.strokeStyle = f; x.lineWidth = b || 1; x.beginPath(); x.moveTo(x1, y1); x.lineTo(x2, y2); x.stroke();
  }
  function rundrect(x, px, py, w, h, r){
    x.beginPath(); x.moveTo(px + r, py); x.arcTo(px + w, py, px + w, py + h, r);
    x.arcTo(px + w, py + h, px, py + h, r); x.arcTo(px, py + h, px, py, r); x.arcTo(px, py, px + w, py, r); x.closePath();
  }
  /* Marke: Umriss-Pille mit Versalien, wie auf der Seite. Gibt die Breite zurueck. */
  function marke(x, str, px, py, f){
    x.font = ARCH(17, 600); var s = str.toUpperCase(); var w = x.measureText(s).width + 30;
    x.strokeStyle = f; x.lineWidth = 2; rundrect(x, px, py - 24, w, 36, 18); x.stroke();
    x.fillStyle = f; x.fillText(s, px + 15, py + 1);
    return w;
  }
  function pille(x, str, px, py, fg, bg){
    x.font = ARCH(15, 600); var w = x.measureText(str).width + 24;
    x.fillStyle = bg; rundrect(x, px, py - 20, w, 30, 15); x.fill();
    x.fillStyle = fg; x.fillText(str, px + 12, py + 1);
    return w;
  }

  /* ---- Rahmen ---------------------------------------------------------- */
  function kopf(x, p){
    x.fillStyle = p.bg; x.fillRect(0, 0, W, H);
    x.textBaseline = 'alphabetic';
    x.fillStyle = p.ink; x.font = ARCH(28, 700); x.fillText('ABSTIMMUNGSSPIEGEL', M, 92);
    x.fillStyle = p.leise; x.font = SANS(19, 600);
    x.fillText((D.vorlage.ebene + ' · Abstimmung vom ' + D.vorlage.datum).toUpperCase(), M, 126);
    linie(x, M, 152, W - M, 152, p.ink, 3);
    return 226;
  }
  function fuss(x, p, rechts){
    linie(x, M, FUSS, W - M, FUSS, p.linie, 1);
    x.fillStyle = p.ink; x.font = SANS(22, 700);
    x.fillText('Politspiegel Schaffhausen · Abstimmungsspiegel', M, FUSS + 40);
    x.fillStyle = p.leise; x.font = SANS(18, 400);
    x.fillText(D.url ? D.url.replace(/^https?:\/\//, '') : 'Bewertet wird der Beleg einer Aussage, nicht die Aussage.', M, FUSS + 70);
    if (rechts) { x.textAlign = 'right'; x.font = SANS(18, 600); x.fillText(rechts, W - M, FUSS + 70); x.textAlign = 'left'; }
  }
  function titel(x, p, str, y, px){
    x.fillStyle = p.ink; x.font = ARCH(px || 40, 600);
    return text(x, str, M, y, INNEN, (px || 40) * 1.18, 3) + 10;
  }

  /* ---- Netz ------------------------------------------------------------ */
  function netz(x, p, cx, cy, r, reihen, beschriftet, pruefung){
    var n = D.achsen.length;
    function pol(i, f){ var w = -Math.PI/2 + i*2*Math.PI/n; return [cx + r*f*Math.cos(w), cy + r*f*Math.sin(w)]; }
    x.strokeStyle = p.linie; x.lineWidth = 1.5;
    [1,2,3,4].forEach(function(st){
      x.beginPath(); for (var i = 0; i < n; i++){ var q = pol(i, st/4); i ? x.lineTo(q[0], q[1]) : x.moveTo(q[0], q[1]); }
      x.closePath(); x.stroke();
    });
    for (var i = 0; i < n; i++){
      var q = pol(i, 1); var na = pruefung && pruefung[D.achsen[i].id] == null;
      x.setLineDash(na ? [6, 6] : []); linie(x, cx, cy, q[0], q[1], p.linie, 1.5); x.setLineDash([]);
    }
    reihen.forEach(function(rw){
      var pts = [];
      for (var i = 0; i < n; i++){ var v = rw.werte[D.achsen[i].id]; if (v == null) continue; pts.push(pol(i, v/4)); }
      if (pts.length >= 3){
        x.beginPath(); pts.forEach(function(q, k){ k ? x.lineTo(q[0], q[1]) : x.moveTo(q[0], q[1]); }); x.closePath();
        x.globalAlpha = 0.18; x.fillStyle = rw.farbe; x.fill(); x.globalAlpha = 1;
        x.strokeStyle = rw.farbe; x.lineWidth = 3.5; x.stroke();
      }
      pts.forEach(function(q){ x.beginPath(); x.arc(q[0], q[1], 6, 0, 2*Math.PI); x.fillStyle = rw.farbe; x.fill(); });
    });
    if (beschriftet){
      for (var i = 0; i < n; i++){
        var q = pol(i, 1.24); var a = D.achsen[i];
        x.textAlign = Math.abs(q[0] - cx) <= 10 ? 'center' : (q[0] < cx ? 'right' : 'left');
        x.fillStyle = p.ink; x.font = ARCH(21, 600); x.fillText(a.kurz, q[0], q[1] + 7);
        if (reihen.length === 2){
          x.fillStyle = p.leise; x.font = SANS(18, 400);
          x.fillText(f1(reihen[0].werte[a.id]) + ' zu ' + f1(reihen[1].werte[a.id]), q[0], q[1] + 32);
        } else if (pruefung){
          x.fillStyle = p.leise; x.font = SANS(18, 400);
          x.fillText(pruefung[a.id] == null ? 'nicht anwendbar' : pruefung[a.id] + ' von 4', q[0], q[1] + 32);
        }
      }
      x.textAlign = 'left';
    }
  }
  function f1(v){ return (Math.round(v*10)/10).toFixed(1).replace('.', ','); }

  /* Fuenf Balken, einer je Achse, wie auf der Karte. */
  function balken(x, p, y, pruefung, f){
    D.achsen.forEach(function(a){
      var v = pruefung[a.id];
      x.fillStyle = p.ink; x.font = SANS(22, 600); x.fillText(a.kurz, M, y + 8);
      var bx = M + 250, bw = 120, gap = 12;
      if (v == null){
        x.fillStyle = p.leise; x.font = SANS(19, 400); x.fillText('nicht anwendbar', bx, y + 8);
      } else {
        for (var k = 0; k < 4; k++){ x.fillStyle = k < v ? f : p.segLeer; rundrect(x, bx + k*(bw+gap), y - 10, bw, 22, 5); x.fill(); }
        x.fillStyle = p.ink; x.font = SANS(22, 700); x.textAlign = 'right'; x.fillText(String(v), W - M, y + 8); x.textAlign = 'left';
      }
      y += 48;
    });
    return y;
  }

  /* ---- Motive ---------------------------------------------------------- */
  function mVorlage(x, p, y){
    var v = D.vorlage;
    y = titel(x, p, v.titel, y + 30, 50);
    x.fillStyle = p.leise; x.font = SANS(25, 400);
    y = text(x, v.untertitel, M, y, INNEN, 34, 3) + 26;
    x.fillStyle = p.leise; x.font = ARCH(17, 600); x.fillText('WORUM ES GEHT', M, y); y += 34;
    x.fillStyle = p.ink; x.font = SANS(24, 400);
    y = text(x, v.worum, M, y, INNEN, 34, 8) + 22;
    var kasten = [['Bei einem Ja', v.bei_ja], ['Bei einem Nein', v.bei_nein]];
    var frei = FUSS - 20 - y, kh = Math.floor((frei - 16) / 2);
    kasten.forEach(function(k){
      x.fillStyle = p.flaeche; rundrect(x, M, y, INNEN, kh, 14); x.fill();
      x.fillStyle = p.ink; x.font = ARCH(22, 600); x.fillText(k[0], M + 26, y + 40);
      x.fillStyle = p.ink; x.font = SANS(20, 400);
      text(x, k[1], M + 26, y + 74, INNEN - 52, 28, Math.floor((kh - 90) / 28));
      y += kh + 16;
    });
  }

  function mGegen(x, p, y){
    y = titel(x, p, 'Wie gut sind die Argumente belegt?', y + 24, 40);
    x.fillStyle = p.leise; x.font = SANS(22, 400);
    y = text(x, 'Mittelwert je Achse über die geprüften Aussagen, 0 bis 4 Punkte. ' +
             'Gemessen wird der Beleg, nicht die Richtigkeit.', M, y, INNEN, 31, 3);
    netz(x, p, W/2, y + 330, 230,
         [{ werte: D.mittel.pro, farbe: p.pro }, { werte: D.mittel.contra, farbe: p.contra }], true);
    y += 690;
    ['pro', 'contra'].forEach(function(s){
      var f = seitenFarbe(p, s), su = D.summe[s];
      x.fillStyle = f; rundrect(x, M, y - 14, 22, 22, 5); x.fill();
      x.fillStyle = p.ink; x.font = ARCH(24, 600); x.fillText(D.seiten[s].komitee, M + 38, y + 6);
      x.fillStyle = p.leise; x.font = SANS(21, 400); x.textAlign = 'right';
      x.fillText(su[0] + ' von ' + su[1] + ' Punkten, Werturteile ausgenommen', W - M, y + 6); x.textAlign = 'left';
      y += 48;
    });
    x.fillStyle = p.leise; x.font = SANS(19, 400);
    text(x, 'Ein guter Beleg macht eine Aussage nicht richtig, und eine unbelegte Aussage nicht falsch. ' +
         'Ob Reisezeit oder Wohnruhe schwerer wiegt, messen diese Achsen nicht.', M, y + 10, INNEN, 27, 3);
  }

  function argHalb(x, p, a, y, hh){
    var f = seitenFarbe(p, a.seite), ende = y + hh;
    var mw = marke(x, D.seiten[a.seite].komitee, M, y, f);
    x.fillStyle = p.leise; x.font = SANS(17, 400); x.fillText(a.typ_name, M + mw + 16, y);
    y += 44;
    x.fillStyle = p.ink; x.font = ARCH(27, 600);
    y = text(x, '«' + a.aussage + '»', M, y, INNEN, 36, 5) + 6;
    x.fillStyle = p.leise; x.font = SANS(18, 400);
    y = text(x, a.traeger, M, y, INNEN, 24, 1) + 18;
    if (a.typ === 'wertung'){
      x.fillStyle = p.leise; x.font = SANS(20, 400);
      text(x, 'Werturteil. Steht ohne Note, weil sich kein Beleg dafür prüfen lässt.', M, y + 8, INNEN, 28, 2);
      return ende;
    }
    var r = Math.min(70, (ende - y - 10) / 2);
    netz(x, p, M + r + 10, y + r + 4, r, [{ werte: a.pruefung, farbe: f }], false, a.pruefung);
    x.fillStyle = p.ink; x.font = ARCH(36, 700); x.fillText(a.erreicht + ' von ' + a.moeglich, M + 2*r + 50, y + r - 4);
    x.fillStyle = p.leise; x.font = SANS(18, 400); x.fillText('Punkten für den Beleg', M + 2*r + 50, y + r + 24);
    var tx = M + 2*r + 50, ty = y + r + 58; x.font = SANS(17, 400);
    var teile = D.achsen.map(function(ax){ var v = a.pruefung[ax.id]; return ax.kurz + ' ' + (v == null ? '–' : v); });
    text(x, teile.join('  ·  '), tx, ty, W - M - tx, 24, 2);
    return ende;
  }

  function mPaar(x, p, y, n){
    var pro = D.argumente.filter(function(a){ return a.seite === 'pro'; })[n],
        con = D.argumente.filter(function(a){ return a.seite === 'contra'; })[n];
    x.fillStyle = p.leise; x.font = ARCH(17, 600); x.fillText(('Aussagenpaar ' + (n+1)).toUpperCase(), M, y);
    y += 40;
    var hh = (FUSS - 40 - y) / 2;
    if (pro) argHalb(x, p, pro, y + 26, hh - 30);
    linie(x, M, y + hh, W - M, y + hh, p.linie, 1.5);
    if (con) argHalb(x, p, con, y + hh + 40, hh - 30);
  }

  function mKantonsrat(x, p, y){
    var kr = D.kantonsrat;
    y = titel(x, p, 'Wie der Kantonsrat gestimmt hat', y + 24, 40);
    x.fillStyle = p.leise; x.font = SANS(21, 400);
    y = text(x, 'Dieselbe Vorlage im Rat: namentliche Abstimmungen am ' + kr.sitzung +
             ', gezählt aus dem Wortprotokoll.', M, y, INNEN, 30, 2) + 14;
    var n = kr.abstimmungen.length, eh = Math.min(170, Math.floor((FUSS - 36 - y) / Math.max(n, 1)));
    kr.abstimmungen.forEach(function(v){
      var top = y;
      x.fillStyle = p.leise; x.font = ARCH(15, 600);
      x.fillText(('Abstimmung ' + v.nr + ' · ' + v.titel).toUpperCase(), M, y + 2);
      x.fillStyle = p.ink; x.font = SANS(22, 600); x.textAlign = 'right';
      x.fillText(v.ja + ' Ja : ' + v.nein + ' Nein', W - M, y + 2); x.textAlign = 'left';
      y += 30;
      x.fillStyle = p.ink; x.font = ARCH(21, 600);
      y = text(x, v.details || v.titel, M, y, INNEN, 27, eh > 150 ? 2 : 1) + 6;
      /* Ja dunkel, Nein hell. Die Seitenfarben waeren hier irrefuehrend: Wer fuer
         die Initiative ist, stimmt beim Gegenvorschlag mit Nein. */
      var s = Math.max(v.ja + v.nein, 1), bw = INNEN;
      x.fillStyle = p.linie; rundrect(x, M, y, bw, 18, 4); x.fill();
      x.fillStyle = p.ink; rundrect(x, M, y, bw * v.ja / s, 18, 4); x.fill();
      y += 34;
      x.fillStyle = p.leise; x.font = SANS(16, 400);
      var fr = v.fraktionen.map(function(f){ return f.name + ' ' + f.ja + ':' + f.nein; }).join('  ·  ');
      text(x, fr + (v.enth ? '  ·  ' + v.enth + ' Enth.' : ''), M, y, INNEN, 22, 1);
      y = top + eh;
    });
    x.fillStyle = p.leise; x.font = SANS(15, 400);
    x.fillText('Balken: Anteil Ja dunkel, Anteil Nein hell. Je Fraktion Ja:Nein.', M, FUSS - 14);
  }

  /* ---- Karussell ------------------------------------------------------- */
  /* Ein langer Text wird auf mehrere Folien verteilt statt abgeschnitten.
     Gemessen wird in der kleinsten Schrift, die fliess() noch waehlt; was
     dort nicht auf eine Folie passt, bekommt eine zweite. Absatzgrenzen
     bleiben erhalten, damit kein Satz ueber den Folienrand springt. */
  var MX = document.createElement('canvas').getContext('2d');
  function seiten(str, frei){
    MX.font = SANS(24, 400);
    var lh = Math.round(24 * 1.45), maxL = Math.floor(frei / lh);
    var out = [], akt = [], n = 0;
    String(str || '').split(/\n\s*\n/).forEach(function(abs){
      var zs = zeilen(MX, abs, INNEN);
      /* Ein Absatz wechselt lieber ganz auf die naechste Folie, als dass er
         mitten im Satz bricht; nur ein Absatz laenger als eine Folie wird geteilt. */
      if (akt.length && n + 0.55 + zs.length > maxL && zs.length <= maxL){ out.push(akt); akt = []; n = 0; }
      if (akt.length){ n += 0.55; }
      zs.forEach(function(z){
        if (n + 1 > maxL){ out.push(akt); akt = []; n = 0; }
        akt.push(z); n += 1;
      });
      akt.push('');   /* Absatzende, wird beim Zusammensetzen zur Leerzeile */
    });
    if (akt.length) out.push(akt);
    return out.map(function(seite){
      var abs = [], z = [];
      seite.forEach(function(l){ if (l === ''){ if (z.length) abs.push(z.join(' ')); z = []; } else z.push(l); });
      if (z.length) abs.push(z.join(' '));
      return abs.join('\n\n');
    }).filter(function(s){ return s; });
  }
  function textFolien(f, name, str, extra){
    var frei = FUSS - 30 - (226 + 20 + 52 + 8) - (extra ? 130 : 0);
    var st = seiten(str, frei);
    st.forEach(function(teil, i){
      var nm = name + (st.length > 1 ? ' (' + (i+1) + '/' + st.length + ')' : '');
      f.push({ name: nm, z: function(x, p, y){
        y = titel(x, p, nm, y + 20, 36);
        var res = (extra && i === st.length - 1) ? 130 : 0;
        x.fillStyle = p.ink; y = fliess(x, teil, M, y + 8, INNEN, FUSS - 30 - res - y);
        if (extra && i === st.length - 1){ x.fillStyle = p.leise; x.font = SANS(19, 400); text(x, extra, M, y + 14, INNEN, 26, 4); }
      }});
    });
  }
  function folien(a){
    var f = [], w = a.typ === 'wertung';
    f.push({ name: 'Aussage', z: function(x, p, y){
      var fb = seitenFarbe(p, a.seite);
      var mw = marke(x, D.seiten[a.seite].komitee, M, y + 10, fb);
      x.fillStyle = p.leise; x.font = SANS(18, 400); x.fillText(a.typ_name, M + mw + 16, y + 10);
      y += 76;
      x.fillStyle = p.ink;
      var gr = [54, 48, 42, 36], k;
      for (k = 0; k < gr.length; k++){ x.font = ARCH(gr[k], 600);
        if (hoehe(x, '«' + a.aussage + '»', INNEN, gr[k]*1.25) <= 620 || k === gr.length-1) break; }
      y = text(x, '«' + a.aussage + '»', M, y, INNEN, gr[k]*1.25, Math.floor(620 / (gr[k]*1.25))) + 18;
      x.fillStyle = p.leise; x.font = SANS(22, 400);
      y = text(x, a.traeger, M, y, INNEN, 30, 2) + 12;
      if (a.fundstelle){ x.font = SANS(19, 400);
        text(x, 'Fundstelle: ' + a.fundstelle.titel + (a.fundstelle.datum ? ' · ' + a.fundstelle.datum : ''), M, y, INNEN, 26, 2); }
      else if (a.offen){ x.font = SANS(19, 400); text(x, 'Fundstelle offen: noch nicht mit Urheber und Datum belegt.', M, y, INNEN, 26, 2); }
    }});
    f.push({ name: w ? 'Ohne Note' : 'Belegprüfung', z: function(x, p, y){
      var fb = seitenFarbe(p, a.seite);
      y = titel(x, p, w ? 'Warum diese Aussage ohne Note steht' : 'Wie gut ist die Aussage belegt?', y + 20, 36);
      x.fillStyle = p.leise; x.font = SANS(22, 400);
      y = text(x, '«' + a.aussage + '»', M, y, INNEN, 30, 3) + 20;
      if (w){
        x.fillStyle = p.ink; x.font = SANS(28, 400);
        text(x, 'Werturteil. Es ist weder wahr noch falsch, und es lässt sich kein Beleg dafür prüfen. ' +
             'Es wird dargestellt, aber nicht benotet, und geht nicht in die Netzgrafik ein.', M, y + 10, INNEN, 38, 8);
        return;
      }
      x.fillStyle = p.ink; x.font = ARCH(56, 700); x.fillText(a.erreicht + ' von ' + a.moeglich, M, y + 46);
      x.fillStyle = p.leise; x.font = SANS(22, 400); x.fillText('Punkten, 4 je anwendbare Achse', M + 30 + x.measureText('').width + (function(){ x.font = ARCH(56, 700); var w = x.measureText(a.erreicht + ' von ' + a.moeglich).width; x.font = SANS(22, 400); return w; })(), y + 46);
      netz(x, p, W/2, y + 290, 150, [{ werte: a.pruefung, farbe: fb }], true, a.pruefung);
      y += 520;
      balken(x, p, y, a.pruefung, fb);
    }});
    textFolien(f, w ? 'Was daran stimmt' : 'Was zutrifft', a.trifft_zu, '');
    textFolien(f, w ? 'Warum ohne Note' : 'Was fehlt', a.fehlt, a.zahlhinweis || '');
    a.grafiken.forEach(function(g){
      f.push({ name: 'Grafik: ' + g.titel, bild: g.datei, z: function(x, p, y){
        pille(x, g.eigen ? 'Eigene Auswertung' : 'Fremde Quelle', M, y + 6, g.eigen ? p.bg : p.ink, g.eigen ? p.ink : p.flaeche);
        y += 66;
        x.fillStyle = p.ink; x.font = ARCH(30, 600); y = text(x, g.titel, M, y, INNEN, 38, 2) + 10;
        var im = BILDER[g.datei], boxH = FUSS - 130 - y;
        if (im && im.complete && im.naturalWidth){
          var sc = Math.min(INNEN / im.naturalWidth, boxH / im.naturalHeight);
          var iw = im.naturalWidth * sc, ih = im.naturalHeight * sc;
          x.fillStyle = '#FFFFFF'; rundrect(x, M, y, INNEN, ih + 24, 12); x.fill();
          x.drawImage(im, M + (INNEN - iw)/2, y + 12, iw, ih); y += ih + 40;
        } else {
          x.fillStyle = p.flaeche; rundrect(x, M, y, INNEN, boxH, 12); x.fill();
          x.fillStyle = p.leise; x.font = SANS(20, 400); x.fillText('Grafik konnte nicht geladen werden.', M + 24, y + 44); y += boxH + 16;
        }
        x.fillStyle = p.leise; x.font = SANS(19, 400);
        y = text(x, g.hinweis, M, y, INNEN, 26, 3); text(x, g.quelle, M, y + 4, INNEN, 24, 2);
      }});
    });
    if (a.kritische_fragen.length) f.push({ name: 'Kritische Fragen', z: function(x, p, y){
      y = titel(x, p, 'Kritische Fragen', y + 20, 36);
      x.fillStyle = p.leise; x.font = SANS(20, 400);
      y = text(x, 'Die Prüffragen zum Argumenttyp' + (a.schema ? ' «' + a.schema + '»' : '') + '.', M, y, INNEN, 28, 2) + 14;
      var frei = FUSS - 20 - y, je = Math.min(190, Math.floor(frei / a.kritische_fragen.length));
      a.kritische_fragen.forEach(function(k){
        var top = y, st = k.status === 'beantwortet' ? 'beantwortet' : (k.status === 'offen' ? 'offen' : 'nicht erfüllt');
        pille(x, st, M, y + 14, k.status === 'beantwortet' ? p.bg : p.ink, k.status === 'beantwortet' ? p.ink : p.flaeche);
        y += 46;
        x.fillStyle = p.ink; x.font = ARCH(22, 600); y = text(x, k.frage, M, y, INNEN, 29, 2) + 2;
        x.fillStyle = p.leise; x.font = SANS(19, 400); text(x, k.kommentar, M, y, INNEN, 26, Math.max(1, Math.floor((top + je - y - 10) / 26)));
        y = top + je;
      });
    }});
    f.push({ name: 'Grundlagen', z: function(x, p, y){
      y = titel(x, p, 'Grundlagen der Prüfung', y + 20, 36);
      if (a.fundstelle){
        x.fillStyle = p.leise; x.font = ARCH(17, 600); x.fillText('FUNDSTELLE DER AUSSAGE', M, y); y += 34;
        x.fillStyle = p.ink; x.font = SANS(23, 400);
        y = text(x, a.fundstelle.titel + (a.fundstelle.datum ? ' · ' + a.fundstelle.datum : ''), M, y, INNEN, 32, 3) + 24;
      }
      x.fillStyle = p.leise; x.font = ARCH(17, 600); x.fillText('QUELLEN DER PRÜFUNG', M, y); y += 34;
      if (!a.belege.length){ x.fillStyle = p.ink; x.font = SANS(23, 400); x.fillText('Keine weiteren Quellen herangezogen.', M, y); return; }
      a.belege.forEach(function(b){
        if (y > FUSS - 60) return;
        var art = { amtlich: 'amtlich', wissenschaft: 'Wissenschaft', medien: 'Medien', interessengruppe: 'Interessengruppe', komitee: 'Komitee' }[b.art] || b.art;
        var pw = art ? pille(x, art, M, y + 4, p.ink, p.flaeche) + 14 : 0;
        x.fillStyle = p.ink; x.font = SANS(22, 400); y = text(x, b.titel, M + pw, y + 8, INNEN - pw, 30, 2) + 14;
      });
    }});
    var g = gegenstueck(a);
    f.push({ name: 'Die andere Seite', z: function(x, p, y){
      y = titel(x, p, 'Die andere Seite', y + 20, 36);
      x.fillStyle = p.leise; x.font = SANS(21, 400);
      y = text(x, 'Zu jeder Aussage steht eine der Gegenseite. Beide sind nach denselben fünf Achsen geprüft.', M, y, INNEN, 29, 2) + 30;
      if (g) argHalb(x, p, g, y + 10, FUSS - 60 - y);
      else { x.fillStyle = p.ink; x.font = SANS(24, 400); x.fillText('Für diese Aussage steht kein Gegenstück bereit.', M, y + 20); }
    }});
    return f;
  }
  function gegenstueck(a){
    var eig = D.argumente.filter(function(b){ return b.seite === a.seite; }),
        and = D.argumente.filter(function(b){ return b.seite !== a.seite; });
    return and[eig.indexOf(a)] || null;
  }

  /* ---- Motivliste ------------------------------------------------------ */
  var MOTIVE = [{ k: 'vorlage', g: 'Vorlage', l: 'Die Vorlage' },
                { k: 'gegen', g: 'Vorlage', l: 'Gegenüberstellung der Belegqualität' }];
  var nPaare = Math.min(D.argumente.filter(function(a){ return a.seite === 'pro'; }).length,
                        D.argumente.filter(function(a){ return a.seite === 'contra'; }).length);
  for (var i = 0; i < nPaare; i++) MOTIVE.push({ k: 'paar:' + i, g: 'Aussagenpaare', l: 'Aussagenpaar ' + (i+1) });
  if (D.kantonsrat && D.kantonsrat.abstimmungen.length) MOTIVE.push({ k: 'kantonsrat', g: 'Kantonsrat', l: 'Wie der Kantonsrat gestimmt hat' });
  D.argumente.forEach(function(a, i){
    var nr = D.argumente.filter(function(b){ return b.seite === a.seite; }).indexOf(a) + 1;
    MOTIVE.push({ k: 'karussell:' + a.id, g: 'Karussell ' + D.seiten[a.seite].komitee, l: nr + '. ' + kurz(a.aussage, 60), arg: a });
  });
  function kurz(s, n){ return s.length <= n ? s : s.slice(0, n).replace(/\s*\S*$/, '') + ' …'; }
  function motivVon(k){ for (var i = 0; i < MOTIVE.length; i++) if (MOTIVE[i].k === k) return MOTIVE[i]; return MOTIVE[0]; }

  /* ---- Bilder laden ---------------------------------------------------- */
  function ladeBild(datei){
    return new Promise(function(res){
      if (BILDER[datei]) return res();
      var im = new Image(); im.onload = function(){ BILDER[datei] = im; res(); }; im.onerror = function(){ res(); };
      im.src = 'grafiken/' + datei + '.svg';
    });
  }

  /* ---- Zeichnen -------------------------------------------------------- */
  function zeichne(k, folie){
    var c = $('#bildCanvas'), x = c.getContext('2d'), p = palette(), m = motivVon(k);
    var warten = [document.fonts ? document.fonts.ready : Promise.resolve()];
    if (m.arg){ var f = folien(m.arg)[folie || 0]; if (f && f.bild) warten.push(ladeBild(f.bild)); }
    return Promise.all(warten).then(function(){
      var y = kopf(x, p), rechts = '';
      if (k === 'vorlage') mVorlage(x, p, y);
      else if (k === 'gegen') mGegen(x, p, y);
      else if (k === 'kantonsrat') mKantonsrat(x, p, y);
      else if (k.indexOf('paar:') === 0) mPaar(x, p, y, +k.slice(5));
      else if (m.arg){
        var fs = folien(m.arg), n = (folie || 0);
        fs[n].z(x, p, y);
        rechts = (n + 1) + ' von ' + fs.length;
      }
      fuss(x, p, rechts);
    });
  }

  /* ---- Bedienung ------------------------------------------------------- */
  var sel = $('#bildMotiv'), selF = $('#bildFolie');
  var gruppen = {};
  MOTIVE.forEach(function(m){
    if (!gruppen[m.g]){ gruppen[m.g] = document.createElement('optgroup'); gruppen[m.g].label = m.g; sel.appendChild(gruppen[m.g]); }
    var o = document.createElement('option'); o.value = m.k; o.textContent = m.l; gruppen[m.g].appendChild(o);
  });
  function folienListe(){
    var m = motivVon(sel.value); selF.innerHTML = '';
    $('#bildFolieWrap').hidden = !m.arg; $('#bildAlle').hidden = !m.arg;
    if (!m.arg) return;
    folien(m.arg).forEach(function(f, i){
      var o = document.createElement('option'); o.value = i; o.textContent = (i+1) + ' · ' + f.name; selF.appendChild(o);
    });
  }
  function dateiname(k, folie){
    var slug = (location.pathname.match(/abstimmung\/([^\/]+)/) || [0, 'vorlage'])[1];
    var teil = k.replace(/:/g, '-');
    return 'abstimmungsspiegel-' + slug + '-' + teil + (folie != null ? '-folie-' + (folie+1) : '') + '.png';
  }
  function neu(){ zeichne(sel.value, +selF.value || 0); }
  sel.addEventListener('change', function(){ folienListe(); neu(); });
  selF.addEventListener('change', neu);
  $('#bildLaden').addEventListener('click', function(){
    var m = motivVon(sel.value), fo = m.arg ? (+selF.value || 0) : null;
    zeichne(sel.value, fo).then(function(){
      var a = document.createElement('a'); a.download = dateiname(sel.value, fo);
      a.href = $('#bildCanvas').toDataURL('image/png'); a.click();
    });
  });
  $('#bildAlle').addEventListener('click', function(){
    var m = motivVon(sel.value); if (!m.arg) return;
    var n = folien(m.arg).length, i = 0;
    (function schritt(){
      if (i >= n){ neu(); return; }
      zeichne(sel.value, i).then(function(){
        var a = document.createElement('a'); a.download = dateiname(sel.value, i);
        a.href = $('#bildCanvas').toDataURL('image/png'); a.click();
        i++; setTimeout(schritt, 400);
      });
    })();
  });
  function modal(auf){
    $('#bildModal').hidden = !auf;
    document.body.style.overflow = auf ? 'hidden' : '';
    if (auf){ folienListe(); neu(); }
  }
  $('#bildStart').addEventListener('click', function(){ modal(true); });
  $('#bildZu').addEventListener('click', function(){ modal(false); });
  $('#bildModal').addEventListener('click', function(e){ if (e.target === $('#bildModal')) modal(false); });
  document.addEventListener('keydown', function(e){ if (e.key === 'Escape' && !$('#bildModal').hidden) modal(false); });
  /* Wechselt das Farbschema, wird das Bild neu gezeichnet. */
  new MutationObserver(function(){ if (!$('#bildModal').hidden) neu(); })
    .observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
})();
"""

/* ── Grafiken für Präsentation und Social Media ───────────────────────────
   Knopf unten rechts, Dialog mit Motiv, Ebene, Format, Hintergrund und Titel,
   Vorschau im Canvas, Download als PNG oder Kopie in die Zwischenablage.
   Formate: Präsentation 16:9, Bericht 3:2, Social Media 4:5 (1080 × 1350).
   Die Grafiken sind immer hell. Grundlage ist die Ansicht, die auf der Seite
   gewählt ist; keine eigene Rechnung. Farben der Datensätze A, B, C wie auf der
   Seite; Flächen in Kuchen und Ringen nach Rang aus einer Reihe von sieben Farben,
   geprüft für benachbarte Flächen, Rest grau. */
const G_FORMATE = {
  hoch:    {w:1080, h:1350, t:'Social Media 4:5', m:'1080 × 1350 Pixel'},
  folie:   {w:1920, h:1080, t:'Präsentation 16:9', m:'1920 × 1080 Pixel'},
  bericht: {w:1800, h:1200, t:'Bericht 3:2', m:'1800 × 1200 Pixel'},
};
const G_MOTIVE = [
  ['kuchen', 'Kuchendiagramm der gewählten Ebene'],
  ['balken', 'Balkenliste der gewählten Ebene, bis drei Datensätze'],
  ['ringe', 'Ringdiagramm, A aussen, B und C innen'],
  ['ueberblick', 'Woher, wohin: Ertrag und Aufwand nach Sachgruppen'],
  ['entwicklung', 'Entwicklung der gewählten Kennzahl'],
  ['kennzahlen', 'Kennzahlen im Vergleich'],
];
const G_NOTIZ = {
  balken: 'Einträge der gewählten Ebene mit den Einstellungen des Vergleichs (Rechnung, Gliederung, Ansicht, Konten), für alle gewählten Datensätze. Einträge ohne Platz sind als «Übrige» zusammengefasst.',
  kuchen: 'Einträge der gewählten Ebene für einen Datensatz. Die sieben grössten einzeln, der Rest als «Übrige». Negative Beträge haben keine Fläche und stehen unter der Legende.',
  ringe: 'Einträge der gewählten Ebene als Ringe: A aussen, B und C nach innen. Gleiche Farbe heisst gleicher Eintrag. Skala «Anteile»: jeder Ring ergibt den vollen Kreis. Skala «Beträge»: das grösste Total ergibt den vollen Kreis, kleinere Totale bleiben offen.',
  ueberblick: 'Ordentlicher Ertrag und Aufwand eines Datensatzes nach Sachgruppen auf derselben Skala, mit der Rechnung vom operativen Ergebnis zum Gesamtergebnis.',
  entwicklung: 'Die unter «Entwicklung» gewählte Kennzahl oder der gewählte Bereich: Rechnung, Budget und Finanzplan 2025 bis 2030.',
  kennzahlen: 'Die Kennzahlen aus dem Vergleich mit den Differenzen gegenüber Datensatz A.',
};
const G = {motiv:'kuchen', format:'hoch', hg:'weiss', slot:0, skala:'anteil', ebene:null, tiefe:'naechste', titel:'', autoTitel:'', opener:null};
const G_MIT_EBENE = ['balken', 'kuchen', 'ringe'];
const G_TINTE = '#12161C', G_TINTE2 = '#3F4752', G_TINTE3 = '#5A626D', G_LINIE = '#E2E6EB', G_LINIE2 = '#C9CFD6';
const G_SLOT = ['#2a78d6', '#eb6834', '#1baf7a'];
// Kategoriale Reihe, geprüft für benachbarte Flächen in genau dieser Reihenfolge: Farben nur nach Rang vergeben
const G_KAT = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7'];
const G_GRAU = '#B9BEC6', G_RECHNUNG = '#2C3440', G_BUDGET = '#7B8494', G_PLAN = '#7B8494';
const G_AUF = ['#0F766E','#1E9189','#3FB3A8','#7ACBC3','#A9DDD8','#CDEBE8','#E2F3F1'];
const G_ERT = ['#7E3C9A','#9553AE','#AE78C4','#C4A0D6','#D8BEE4','#E8D8F0','#F1E8F6'];
const G_TF = 'Archivo, "Helvetica Neue", Arial, sans-serif', G_F = '"Public Sans", "Helvetica Neue", Arial, sans-serif';

/* Hilfen für Text und Formen */
function gSchrift(x, gewicht, px, fam){ x.font = `${gewicht} ${Math.round(px * 10) / 10}px ${fam || G_F}`; }
function gSpacing(x, px){ if('letterSpacing' in x) x.letterSpacing = px + 'px'; }
function gKuerzen(x, t, breite){
  t = String(t);
  if(x.measureText(t).width <= breite) return t;
  let lo = 0, hi = t.length;
  while(lo < hi){ const m = Math.ceil((lo + hi) / 2); if(x.measureText(t.slice(0, m).trimEnd() + '…').width <= breite) lo = m; else hi = m - 1; }
  return t.slice(0, lo).trimEnd() + '…';
}
function gUmbruch(x, text, breite){
  const w = String(text).split(/\s+/).filter(Boolean), out = []; let z = '';
  for(const t of w){ const p = z ? z + ' ' + t : t; if(x.measureText(p).width > breite && z){ out.push(z); z = t; } else z = p; }
  if(z) out.push(z); return out;
}
function gZeilen(x, text, breite, n){
  const z = gUmbruch(x, text, breite);
  if(z.length <= n) return z.map(t => gKuerzen(x, t, breite));
  const out = z.slice(0, n - 1).map(t => gKuerzen(x, t, breite)); out.push(gKuerzen(x, z.slice(n - 1).join(' '), breite)); return out;
}
function gText(x, t, px, py, o){
  o = o || {};
  gSchrift(x, o.w || 400, o.s || 20, o.f);
  x.fillStyle = o.c || G_TINTE; x.textAlign = o.a || 'left'; x.textBaseline = o.b || 'alphabetic';
  const txt = o.max ? gKuerzen(x, String(t), o.max) : String(t);
  x.fillText(txt, px, py);
  const breite = x.measureText(txt).width;
  x.textAlign = 'left'; x.textBaseline = 'alphabetic';
  return breite;
}
function gRundBalken(x, x0, y, x1, h, r, farbe){
  // abgerundet am Datenende, gerade an der Nulllinie
  const l = Math.min(x0, x1), w = Math.abs(x1 - x0); if(w < .5) return;
  const rr = Math.max(0, Math.min(r, w / 2, h / 2));
  x.fillStyle = farbe; x.beginPath();
  if(x1 >= x0){ x.moveTo(l, y); x.lineTo(l + w - rr, y); x.quadraticCurveTo(l + w, y, l + w, y + rr); x.lineTo(l + w, y + h - rr); x.quadraticCurveTo(l + w, y + h, l + w - rr, y + h); x.lineTo(l, y + h); }
  else { x.moveTo(l + w, y); x.lineTo(l + rr, y); x.quadraticCurveTo(l, y, l, y + rr); x.lineTo(l, y + h - rr); x.quadraticCurveTo(l, y + h, l + rr, y + h); x.lineTo(l + w, y + h); }
  x.closePath(); x.fill();
}
const gDs = k => dsLang(k);
const gName = n => knotenName(n);
const gRechnungWort = () => st.rechnung === 'ir' ? 'Investitionsrechnung' : 'Erfolgsrechnung';
const gGliederungWort = () => st.gl === 'art' ? 'Sachgruppen' : 'Departementen';
const gUmfangText = () => st.rechnung === 'er' ? (st.umfang === 'ord' ? ' · ordentlicher Aufwand und Ertrag' : ' · alle Konten') : '';

/* Einheit einer Grafik: nach dem grössten Betrag */
function gEinheit(werte){
  const m = Math.max(0, ...werte.filter(v => v !== null && v !== undefined).map(Math.abs));
  if(m >= 1e7) return {f: v => mioG(v, 1), t: 'Millionen Franken', k: 'Mio.'};
  if(m >= 1e6) return {f: v => mioG(v, 2), t: 'Millionen Franken', k: 'Mio.'};
  if(m >= 1e4) return {f: v => tsd(v), t: 'Tausend Franken', k: 'Tsd.'};
  return {f: v => fr(v), t: 'Franken', k: 'Fr.'};
}
const mioG = (v, s) => (v < 0 ? '−' : '') + tausender((Math.abs(v) / 1e6).toFixed(s));
const tsd = v => (v < 0 ? '−' : '') + tausender(Math.round(Math.abs(v) / 1000));

/* Quelle: die Dokumente der gezeigten Datensätze. «Vorlage» steht, solange ein
   Datensatz des Dokuments das Kennzeichen trägt (daten.py, JAHRE). */
function gQuelle(ks){
  const s = new Set(ks.map(k => DS[IDX[k]].q));
  const vl = q => DS.some(d => d.q === q && d.vorlage) ? ' (Vorlage des Regierungsrates)' : '';
  const teile = [];
  if(s.has('budget2027')) teile.push((ks.some(k => DS[IDX[k]].a === 'p') ? 'Budget 2027 und Finanzplan 2027–2030' : 'Budget 2027') + vl('budget2027'));
  if(s.has('budget2026')) teile.push('Budget 2026');
  if(s.has('rechnung2025')) teile.push(ks.includes('b25') ? 'Staatsrechnung 2025 mit Budget 2025' : 'Staatsrechnung 2025');
  return teile;
}

/* Rahmen: Marke oben, Titel, Quelle und Stand unten.
   o: titel, unter (Untertitel), legende ([{f, t}]), ueber (Zeile über dem Titel), fuss (Einheit rechts unten), ds (gezeigte Datensätze) */
function gRahmen(x, W, H, o){
  const u = Math.min(W, H) / 1080, M = Math.round(64 * u), breit = W - 2 * M;
  x.setLineDash([]); x.globalAlpha = 1; x.globalCompositeOperation = 'source-over'; gSpacing(x, 0);
  if(G.hg === 'weiss'){ x.fillStyle = '#FFFFFF'; x.fillRect(0, 0, W, H); } else x.clearRect(0, 0, W, H);
  gSpacing(x, 1.2 * u); gText(x, 'KANTON SCHAFFHAUSEN', M, M + 24 * u, {w:700, s:27 * u, f:G_TF});
  gSpacing(x, 2 * u); gText(x, 'FINANZSPIEGEL', M, M + 54 * u, {w:600, s:18 * u, c:G_TINTE3});
  gSpacing(x, 0);
  x.fillStyle = G_TINTE; x.fillRect(M, M + 74 * u, breit, Math.max(1, 3 * u));
  let y = M + 74 * u + 58 * u;
  if(o.ueber){ gText(x, o.ueber, M, y, {s:20 * u, c:G_TINTE3, max: breit}); y += 56 * u; }
  else y += 12 * u;
  G.autoTitel = o.titel;
  const titelText = G.titel.trim() || o.titel;
  let ts = 46 * u;
  for(const g of [46, 40, 34]){ ts = g * u; gSchrift(x, 700, ts, G_TF); if(gUmbruch(x, titelText, breit).length <= 2) break; }
  gZeilen(x, titelText, breit, 2).forEach(z => { gText(x, z, M, y, {w:700, s:ts, f:G_TF, max: breit}); y += ts * 1.15; });
  y += (52 * u - ts * 1.15);
  let unten = y - 30 * u;
  if(o.unter){
    gSchrift(x, 400, 22 * u);
    const uz = gZeilen(x, o.unter, breit, 2);
    uz.forEach((z, i) => gText(x, z, M, y - 8 * u + i * 29 * u, {s:22 * u, c:G_TINTE2, max: breit}));
    unten = y - 8 * u + (uz.length - 1) * 29 * u;
    y = unten + 38 * u;
  }
  if(o.legende && o.legende.length){
    let lx = M, ly = y + (o.unter ? 2 : 0) * u;
    gSchrift(x, 500, 21 * u);
    o.legende.forEach(e => {
      const tw = Math.min(x.measureText(e.t).width, breit - 30 * u);
      if(lx > M && lx + 30 * u + tw > W - M){ lx = M; ly += 32 * u; }
      x.fillStyle = e.f; x.fillRect(lx, ly - 17 * u, 20 * u, 20 * u);
      gText(x, e.t, lx + 30 * u, ly, {w:500, s:21 * u, max: breit - 30 * u});
      lx += 30 * u + tw + 40 * u;
    });
    unten = ly;
  }
  // Fuss: Marke und Einheit, darunter die Quelle
  const yf = H - M;
  x.fillStyle = G_LINIE; x.fillRect(M, yf - 58 * u, breit, Math.max(1, 1.5 * u));
  const rechts = o.fuss || 'Beträge in Franken';
  gText(x, 'Politspiegel Schaffhausen · Finanzspiegel', M, yf - 30 * u, {w:700, s:18 * u});
  gText(x, rechts, W - M, yf - 30 * u, {s:16 * u, c:G_TINTE3, a:'right'});
  gSchrift(x, 400, 15 * u);
  const teile = gQuelle(o.ds || st.sel);
  const stand = ` · Stand ${standText()}`;
  // Von lang nach kurz; die erste, die in die Zeile passt. «Vorlage» bleibt bis zur kürzesten Form stehen.
  const kurz = t => t.replace(' (Vorlage des Regierungsrates)', ' (Vorlage)');
  const knapp = t => kurz(t).replace(/ \d{4}–\d{4}/, '').replace(/ mit Budget \d{4}/, '');
  const quellen = [`Quelle: Kanton Schaffhausen, ${teile.join(', ')}${stand}`, `Quelle: Kanton Schaffhausen, ${teile.map(kurz).join(', ')}${stand}`,
    `Quelle: Kanton Schaffhausen, ${teile.map(knapp).join(', ')}${stand}`, `Quelle: Kanton Schaffhausen, Budget und Staatsrechnung${stand}`];
  const quelle = quellen.find(t => x.measureText(t).width <= breit) || quellen[quellen.length - 1];
  gText(x, quelle, M, yf - 4 * u, {s:15 * u, c:G_TINTE3, max: breit});
  return {x0: M, x1: W - M, y0: unten + 48 * u, y1: yf - 84 * u, u, W, H, M};
}

/* Ebene der Grafik: Vorgabe ist die im Vergleich geöffnete Ebene oder der dort
   markierte Suchtreffer; im Dialog wählbar. Ebenen mit nur einem Untereintrag
   werden übersprungen. Mit Unterteilung «Konten» zeigt die Grafik alle Konten
   unterhalb der Ebene. */
function gKnotenVon(id){
  const weg = aktuellerKnoten(), jetzt = weg[weg.length - 1];
  return weg.find(n => n.id === id) || jetzt.kinder.get(id) || null;
}
function gZielKnoten(){
  const weg = aktuellerKnoten();
  let n = weg[weg.length - 1];
  const gewaehlt = G.ebene && gKnotenVon(G.ebene);
  if(gewaehlt) n = gewaehlt;
  if(gesperrt()) return n;
  while(n.kinder.size === 1){ const c = n.kinder.values().next().value; if(c.blatt || !c.kinder.size) break; n = c; }
  if(G.tiefe === 'konten' && [...n.kinder.values()].some(c => !c.blatt)){
    const konten = new Map();
    const sammeln = k => k.kinder.forEach(c => { if(c.blatt) konten.set(c.id, c); else sammeln(c); });
    sammeln(n);
    return Object.assign({}, n, {kinder: konten, alleKonten: true});
  }
  return n;
}
function gEbene(){
  const jetzt = gZielKnoten();
  const kinder = kinderSortiert(jetzt).filter(c => st.sel.some((_, s) => sichtbar(c, s)));
  return {jetzt, kinder};
}
function gUeberEbene(n){
  if(n.id === 'root') return gRechnungWort() + gUmfangText();
  const p = []; let e = n.eltern; while(e){ p.unshift(e.id === 'root' ? gRechnungWort() : gName(e)); e = e.eltern; }
  return p.join(' › ') + gUmfangText();
}
const gTitelEbene = n => n.alleKonten ? (n.id === 'root' ? `${ansichtName()} nach Konten` : `${gName(n)}: ${ansichtName()} nach Konten`)
  : n.id === 'root' ? `${ansichtName()} nach ${gGliederungWort()}` : `${gName(n)}: ${ansichtName()}`;

/* 1. Balkenliste der gewählten Ebene, bis drei Datensätze, Beträge am Balkenende */
function gBalken(x, W, H){
  const E = gEbene(), S = st.sel.length, n0 = E.jetzt;
  const alleW = E.kinder.flatMap(c => st.sel.map((_, s) => wert(c, s)));
  const ein = gEinheit(alleW.concat(st.sel.map((_, s) => wert(n0, s))));
  const B = gRahmen(x, W, H, {titel: gTitelEbene(n0), ueber: gUeberEbene(n0),
    unter: S === 1 ? `${gDs(st.sel[0])}, ${ansichtName()} in ${ein.t}` : `${ansichtName()} in ${ein.t}`,
    legende: S > 1 ? st.sel.map((k, s) => ({f: G_SLOT[s], t: `${SLOT[s]} · ${gDs(k)}`})) : null, fuss: `Beträge in ${ein.t}`});
  const u = B.u, quer = W > H, breite = B.x1 - B.x0;
  let y = B.y0;
  if(!E.kinder.length){ gText(x, `Keine Einträge mit ${ansichtName()} auf dieser Ebene.`, B.x0, y + 20 * u, {s:24 * u, c:G_TINTE3}); return; }
  gSchrift(x, 500, 22 * u);
  const namen = E.kinder.map(gName);
  const labelMax = quer ? Math.min(0.36 * breite, 640 * u) : 0;
  const zweizeilig = quer && namen.some(t => x.measureText(t).width > labelMax);
  const labelW = quer ? Math.min(labelMax, Math.max(x.measureText('Übrige (00)').width, ...namen.map(t => x.measureText(t).width)) + 4 * u) : 0;
  const gap = (S > 1 ? 3 : 0) * u, labelH = quer ? 0 : 31 * u, labelMin = quer ? (zweizeilig ? 50 : 26) * u : 0;
  const maxBar = (S === 1 ? 40 : S === 2 ? 26 : 20) * u, minBar = (S === 1 ? 12 : 9) * u;
  const gruppe = bh => S * bh + (S - 1) * gap;
  const zeileVon = bh => Math.max(labelMin, gruppe(bh)) + labelH + Math.max(14 * u, (S === 1 ? 0.6 : 0.32) * gruppe(bh));
  const platz = B.y1 - y - 40 * u;
  let zeilen = E.kinder.map((c, i) => ({name: namen[i], v: st.sel.map((_, s) => sichtbar(c, s) ? wert(c, s) : null)}));
  const nMax = Math.max(2, Math.floor(platz / zeileVon(minBar)));
  if(zeilen.length > nMax){
    const rest = zeilen.slice(nMax - 1);
    zeilen = zeilen.slice(0, nMax - 1);
    zeilen.push({name: `Übrige (${rest.length})`, uebrig: true, v: st.sel.map((_, s) => { const w = rest.map(r => r.v[s]).filter(v => v !== null); return w.length ? w.reduce((a, b) => a + b, 0) : null; })});
  }
  let barH = maxBar;
  while(barH > minBar && zeilen.length * zeileVon(barH) > platz) barH -= .5 * u;
  const zeileH = zeileVon(barH), gh = gruppe(barH), blockH = Math.max(gh, labelMin);
  const vs = Math.max(15 * u, Math.min(22 * u, (barH + gap) * (S === 1 ? 0.75 : 1)));
  gSchrift(x, 500, vs);
  const tw = v => x.measureText(ein.f(v)).width, abst = 10 * u;
  const alle = zeilen.flatMap(r => r.v.filter(v => v !== null));
  const posV = alle.filter(v => v > 0), negV = alle.filter(v => v < 0);
  const bx0 = B.x0 + labelW + (quer ? 24 * u : 0), bx1 = B.x1;
  const hi = Math.max(0, ...alle), lo = Math.min(0, ...alle);
  const maxTw = Math.max(0, ...alle.map(tw));
  let k = (bx1 - bx0 - (negV.length ? 2 : 1) * (abst + maxTw)) / Math.max(1, hi - lo);
  const xNull = bx0 + (negV.length ? Math.max(...negV.map(v => -v * k + abst + tw(v))) : 0);
  posV.forEach(v => { k = Math.min(k, (bx1 - xNull - abst - tw(v)) / v); });
  negV.forEach(v => { k = Math.min(k, (xNull - bx0 - abst - tw(v)) / -v); });
  k = Math.max(k, 0);
  const yStart = y;
  zeilen.forEach(r => {
    const tinte = r.uebrig ? G_TINTE2 : G_TINTE, gewicht = r.uebrig ? 400 : 500;
    if(quer){
      gSchrift(x, gewicht, 22 * u);
      const zl = gZeilen(x, r.name, labelW, 2), mitte = y + blockH / 2;
      const b0 = zl.length === 1 ? mitte + 8 * u : mitte - 4.5 * u;
      zl.forEach((z, i) => gText(x, z, B.x0, b0 + i * 25 * u, {w:gewicht, s:22 * u, c:tinte, max: labelW}));
    } else {
      gText(x, r.name, B.x0, y + 22 * u, {w:gewicht, s:22 * u, c:tinte, max: breite});
    }
    let by = y + labelH + (blockH - gh) / 2;
    r.v.forEach((v, s) => {
      const ym = by + barH / 2 + .5 * u;
      if(v === null){ gText(x, 'kein Betrag', xNull + abst, ym, {s:vs * .85, b:'middle', c:G_TINTE3}); }
      else {
        const xe = xNull + v * k;
        gRundBalken(x, xNull, by, xe, barH, Math.min(4 * u, barH / 2), G_SLOT[s]);
        if(v >= 0) gText(x, ein.f(v), xe + abst, ym, {w:500, s:vs, b:'middle'});
        else gText(x, ein.f(v), xe - abst, ym, {w:500, s:vs, b:'middle', a:'right'});
      }
      by += barH + gap;
    });
    y += zeileH;
  });
  if(negV.length){ x.fillStyle = G_LINIE2; x.fillRect(xNull - .75 * u, yStart - 6 * u, Math.max(1, 1.5 * u), y - yStart - (zeileH - blockH - labelH) + 12 * u); }
  const tot = st.sel.map((_, s) => wert(n0, s));
  const totText = S === 1 ? ein.f(tot[0]) : st.sel.map((kk, s) => `${SLOT[s]} ${ein.f(tot[s])}`).join(' · ');
  gText(x, `Total ${n0.id === 'root' ? gRechnungWort() : gName(n0)}: ${totText} ${ein.k}`, B.x0, y + 16 * u, {w:500, s:20 * u, c:G_TINTE2, max: breite});
}

/* 2. Kuchendiagramm der gewählten Ebene, ein Datensatz. Auf der untersten
   Ebene zeigt es die Ebene darüber. */
function gKuchen(x, W, H){
  const s = Math.min(G.slot, st.sel.length - 1), k = st.sel[s];
  let knoten = gEbene().jetzt;
  if(!knoten.kinder.size && knoten.eltern) knoten = knoten.eltern;
  const kinder = [...knoten.kinder.values()].map(c => [c, wert(c, s)]);
  const plus = kinder.filter(q => q[1] >= .5).sort((a, b) => b[1] - a[1] || a[0].id.localeCompare(b[0].id));
  const minus = kinder.filter(q => q[1] <= -.5);
  const summe = plus.reduce((a, q) => a + q[1], 0), total = wert(knoten, s);
  const ein = gEinheit(plus.map(q => q[1]).concat([summe]));
  const einzeln = plus.length <= 8 ? plus.length : 7;
  const teile = plus.slice(0, einzeln).map((q, i) => ({name: gName(q[0]), wert: q[1], f: i < 7 ? G_KAT[i] : G_GRAU}));
  if(plus.length > einzeln) teile.push({name: `Übrige (${plus.length - einzeln})`, wert: plus.slice(einzeln).reduce((a, q) => a + q[1], 0), f: G_GRAU, uebrig: true});
  const B = gRahmen(x, W, H, {titel: gTitelEbene(knoten), unter: `${gDs(k)}, ${ansichtName()} in ${ein.t}`, ueber: gUeberEbene(knoten), ds: [k], fuss: `Beträge in ${ein.t}`});
  const u = B.u, quer = W > H, breite = B.x1 - B.x0;
  if(!teile.length){ gText(x, `Keine positiven Beträge in der Ansicht ${ansichtName()}.`, B.x0, B.y0 + 30 * u, {s:24 * u, c:G_TINTE3}); return; }
  const hinweis = minus.length ? `Nicht dargestellt: ${minus.length} ${minus.length === 1 ? 'Eintrag' : 'Einträge'} mit negativem Betrag, zusammen ${ein.f(minus.reduce((a, q) => a + q[1], 0))} ${ein.k}. Total der Ebene: ${ein.f(total)} ${ein.k}` : '';
  const hoehe = B.y1 - B.y0;
  const legZeilen = quer ? teile.length : Math.ceil(teile.length / 2);
  let cx, cy, R;
  if(quer){ R = Math.min(hoehe * 0.46, breite * 0.2); cx = B.x0 + R + 10 * u; cy = B.y0 + hoehe / 2; }
  else { R = Math.min(breite * 0.3, (hoehe - legZeilen * 64 * u - 70 * u - (hinweis ? 60 * u : 0)) / 2); cx = W / 2; cy = B.y0 + R + 6 * u; }
  const r = R * 0.6;
  let a = -Math.PI / 2;
  teile.forEach(t => {
    t.a = a; t.w = 2 * Math.PI * t.wert / summe;
    x.beginPath(); x.arc(cx, cy, R, a, a + t.w); x.arc(cx, cy, r, a + t.w, a, true); x.closePath();
    x.fillStyle = t.f; x.fill();
    a += t.w;
  });
  if(teile.length > 1){
    x.save();
    if(G.hg === 'weiss') x.strokeStyle = '#FFFFFF'; else { x.globalCompositeOperation = 'destination-out'; x.strokeStyle = '#000000'; }
    x.lineWidth = 4 * u;
    teile.forEach(t => { x.beginPath(); x.moveTo(cx + Math.cos(t.a) * (r - 2 * u), cy + Math.sin(t.a) * (r - 2 * u)); x.lineTo(cx + Math.cos(t.a) * (R + 2 * u), cy + Math.sin(t.a) * (R + 2 * u)); x.stroke(); });
    x.restore();
  }
  teile.forEach(t => {
    if(t.wert / summe < 0.06) return;
    const m = t.a + t.w / 2, rx = cx + Math.cos(m) * (R + r) / 2, ry = cy + Math.sin(m) * (R + r) / 2;
    gText(x, `${Math.round(100 * t.wert / summe)} %`, rx, ry + u, {w:700, s:22 * u, a:'center', b:'middle', c: textAuf(t.f)});
  });
  gSchrift(x, 700, 40 * u, G_TF);
  const zs = Math.min(40 * u, 40 * u * (r * 1.6) / Math.max(1, x.measureText(ein.f(summe)).width));
  gText(x, ein.f(summe), cx, cy + 6 * u, {w:700, s:zs, f:G_TF, a:'center'});
  gText(x, ein.t.replace('Franken', 'Fr.'), cx, cy + 36 * u, {s:19 * u, c:G_TINTE3, a:'center'});
  const eintrag = (t, lx, ly, bw) => {
    x.fillStyle = t.f; x.fillRect(lx, ly - 19 * u, 22 * u, 22 * u);
    gText(x, t.name, lx + 34 * u, ly, {w:500, s:22 * u, max: bw - 34 * u, c: t.uebrig ? G_TINTE2 : G_TINTE});
    gText(x, `${ein.f(t.wert)} ${ein.k} · ${(100 * t.wert / summe).toFixed(1)} %`, lx + 34 * u, ly + 27 * u, {s:19 * u, c:G_TINTE3, max: bw - 34 * u});
  };
  if(quer){
    const lx = cx + R + 80 * u, bw = Math.min(B.x1 - lx, 900 * u);
    const zeile = Math.min(70 * u, (hoehe - (hinweis ? 70 * u : 0)) / teile.length);
    let ly = cy - (teile.length * zeile + (hinweis ? 70 * u : 0)) / 2 + 24 * u;
    teile.forEach(t => { eintrag(t, lx, ly, bw); ly += zeile; });
    if(hinweis){ gSchrift(x, 400, 18 * u); gZeilen(x, hinweis, bw, 2).forEach((z, i) => gText(x, z, lx, ly + 4 * u + i * 24 * u, {s:18 * u, c:G_TINTE3})); }
  } else {
    const sp = breite / 2;
    let ly = cy + R + 58 * u;
    teile.forEach((t, i) => eintrag(t, B.x0 + (i % 2) * sp, ly + Math.floor(i / 2) * 64 * u, sp - 18 * u));
    ly += legZeilen * 64 * u;
    if(hinweis){ gSchrift(x, 400, 18 * u); gZeilen(x, hinweis, breite, 2).forEach((z, i) => gText(x, z, B.x0, ly + i * 24 * u, {s:18 * u, c:G_TINTE3})); }
  }
}

/* Ringdiagramm im Vergleich: ein Ring je Datensatz, A aussen, B und C nach innen.
   Gleiche Einträge in allen Ringen in derselben Reihenfolge und Farbe. Skala
   «anteil»: jeder Ring ergibt den vollen Kreis; «betrag»: das grösste Total
   ergibt den vollen Kreis, kleinere Totale bleiben offen. */
function gRingDaten(knoten, maxEinzeln){
  const kinder = [...knoten.kinder.values()];
  const rang = c => Math.max(...st.sel.map((_, s) => Math.max(0, wert(c, s))));
  const plus = kinder.filter(c => rang(c) >= .5).sort((a, b) => rang(b) - rang(a) || a.id.localeCompare(b.id));
  const einzeln = plus.length <= maxEinzeln + 1 ? plus.length : maxEinzeln;
  const teile = plus.slice(0, einzeln).map((c, i) => ({name: gName(c), f: i < 7 ? G_KAT[i] : G_GRAU,
    v: st.sel.map((_, s) => sichtbar(c, s) ? wert(c, s) : null), fl: st.sel.map((_, s) => Math.max(0, wert(c, s)))}));
  if(plus.length > einzeln){
    const rest = plus.slice(einzeln);
    teile.push({name: `Übrige (${rest.length})`, f: G_GRAU, uebrig: true,
      v: st.sel.map((_, s) => { const w = rest.filter(c => sichtbar(c, s)).map(c => wert(c, s)); return w.length ? w.reduce((a, b) => a + b, 0) : null; }),
      fl: st.sel.map((_, s) => rest.reduce((a, c) => a + Math.max(0, wert(c, s)), 0))});
  }
  const summe = st.sel.map((_, s) => teile.reduce((a, t) => a + t.fl[s], 0));
  return {kinder, plus, teile, summe};
}
function gRinge(x, W, H){
  const S = st.sel.length, E = gEbene(), quer = W > H;
  let knoten = E.jetzt;
  if(!knoten.kinder.size && knoten.eltern) knoten = knoten.eltern;
  const modus = S > 1 ? G.skala : 'anteil';
  const {kinder, teile, summe} = gRingDaten(knoten, quer ? 7 : 5);
  const maxSumme = Math.max(...summe, 1);
  const ein = gEinheit(teile.flatMap(t => t.v).concat(st.sel.map((_, s) => wert(knoten, s))));
  const negNamen = new Map();
  kinder.forEach(c => st.sel.forEach((_, s) => { const v = wert(c, s); if(v <= -.5){ const n = gName(c); if(!negNamen.has(n)) negNamen.set(n, []); negNamen.get(n).push(`${SLOT[s]} ${ein.f(v)}`); } }));
  const negListe = [...negNamen.entries()];
  const negSumme = st.sel.map((_, s) => kinder.reduce((a, c) => a + Math.min(0, wert(c, s)), 0));
  const ohneTeile = st.sel.map((k, s) => Math.abs(wert(knoten, s)) >= .5 && !kinder.some(c => Math.abs(wert(c, s)) >= .5) ? `${SLOT[s]} ${gDs(k)}: nur als Total (${ein.f(wert(knoten, s))} ${ein.k})` : '').filter(Boolean);
  const hinweis = (ohneTeile.length ? ohneTeile.join('; ') + '. ' : '') + (negListe.length === 0 ? '' : negListe.length <= 2
    ? `Ohne Fläche, weil negativ: ${negListe.map(([n, w]) => `${n} (${S > 1 ? w.join(', ') : w.join(', ').slice(2)})`).join('; ')} ${ein.k}. Anteile bezogen auf die Summe der positiven Einträge.`
    : `Ohne Fläche: ${negListe.length} Einträge mit negativem Betrag, zusammen ${st.sel.map((k, s) => (S > 1 ? SLOT[s] + ' ' : '') + ein.f(negSumme[s])).join(', ')} ${ein.k}. Anteile bezogen auf die Summe der positiven Einträge.`);
  const ringName = s => s === 0 ? 'aussen' : s === S - 1 ? 'innen' : 'Mitte';
  const kopfText = (k, s) => S === 1 ? gDs(k) : `${SLOT[s]} · ${ringName(s)}`;
  const unter = S === 1 ? `${gDs(st.sel[0])}, ${ansichtName()} in ${ein.t}`
    : `Von aussen nach innen: ${st.sel.map((k, s) => `${SLOT[s]} ${gDs(k)}`).join(', ')}. ` + (modus === 'betrag' ? 'Gemeinsame Skala: das grösste Total ergibt den vollen Kreis.' : 'Jeder Ring zeigt die Anteile an seinem Total.');
  const B = gRahmen(x, W, H, {titel: gTitelEbene(knoten), unter, ueber: gUeberEbene(knoten), fuss: `Beträge in ${ein.t}`});
  const u = B.u, breite = B.x1 - B.x0, hoehe = B.y1 - B.y0;
  if(!teile.length){ gText(x, `Keine positiven Beträge in der Ansicht ${ansichtName()}.`, B.x0, B.y0 + 30 * u, {s:24 * u, c:G_TINTE3}); return; }
  const zeilenN = teile.length + 1;
  const hinweisH = hinweis ? 58 * u : 0;
  let cx, cy, R, tx0, tx1, ty0, zeileH;
  if(quer){ R = Math.min(hoehe * 0.47, breite * 0.18); cx = B.x0 + R + 6 * u; cy = B.y0 + hoehe / 2; tx0 = cx + R + 80 * u; }
  else tx0 = B.x0;
  tx1 = B.x1;
  gSchrift(x, 500, 20 * u);
  const wertW = Math.max(...teile.flatMap(t => t.v.filter(v => v !== null).map(v => x.measureText(ein.f(v)).width)), ...st.sel.map((_, s) => x.measureText(ein.f(wert(knoten, s))).width));
  gSchrift(x, 700, 19 * u, G_TF);
  const kopfW = S === 1 ? 0 : Math.max(...st.sel.map((k, s) => x.measureText(kopfText(k, s)).width));
  const colW = Math.min(Math.max(wertW, kopfW, 110 * u) + 40 * u, (tx1 - tx0) * (S === 1 ? 0.4 : 0.62) / S);
  gSchrift(x, 400, 17 * u);
  const kopfH = S === 1 ? 44 * u : 30 * u + Math.max(...st.sel.map(k => gZeilen(x, gDs(k), colW - 12 * u, 2).length)) * 21 * u + 12 * u;
  if(quer){
    zeileH = Math.min(62 * u, (hoehe - kopfH - hinweisH) / zeilenN);
    const tabH = kopfH + zeilenN * zeileH + hinweisH;
    ty0 = B.y0 + Math.max(0, (hoehe - tabH) / 2);
  } else {
    zeileH = 44 * u;
    const tabH = kopfH + zeilenN * zeileH + hinweisH;
    R = Math.max(90 * u, Math.min(breite * 0.36, (hoehe - tabH - 44 * u) / 2));
    cx = W / 2; cy = B.y0 + R;
    ty0 = cy + R + 44 * u;
  }
  const nameW = tx1 - tx0 - S * colW;
  const r0 = S === 1 ? R * 0.6 : S === 2 ? R * 0.44 : R * 0.36;
  const rg = S > 1 ? 9 * u : 0;
  const dicke = (R - r0 - (S - 1) * rg) / S;
  const voll = 2 * Math.PI, start = -Math.PI / 2;
  const bogen = (ra, ri, a0, a1, farbe) => { x.beginPath(); x.arc(cx, cy, ra, a0, a1); x.arc(cx, cy, ri, a1, a0, true); x.closePath(); x.fillStyle = farbe; x.fill(); };
  const fuge = (ra, ri, a) => {
    x.save();
    if(G.hg === 'weiss') x.strokeStyle = '#FFFFFF'; else { x.globalCompositeOperation = 'destination-out'; x.strokeStyle = '#000000'; }
    x.lineWidth = 3.5 * u; x.beginPath();
    x.moveTo(cx + Math.cos(a) * (ri - 1 * u), cy + Math.sin(a) * (ri - 1 * u)); x.lineTo(cx + Math.cos(a) * (ra + 1 * u), cy + Math.sin(a) * (ra + 1 * u)); x.stroke();
    x.restore();
  };
  const segmente = [];
  st.sel.forEach((k, s) => {
    const ra = R - s * (dicke + rg), ri = ra - dicke;
    const bezug = modus === 'betrag' ? maxSumme : summe[s];
    if(modus === 'betrag' || summe[s] <= 0) bogen(ra, ri, 0, voll, '#EEF0F3');
    let a = start;
    const grenzen = [];
    teile.forEach(t => {
      if(t.fl[s] <= 0 || bezug <= 0) return;
      const w = voll * t.fl[s] / bezug;
      bogen(ra, ri, a, a + w, t.f);
      grenzen.push(a);
      segmente.push({t, s, a, w, ra, ri});
      a += w;
    });
    const zu = Math.abs(a - start - voll) < 1e-6;
    if(grenzen.length > 1 || !zu) grenzen.forEach(g => fuge(ra, ri, g));
    if(!zu && grenzen.length) fuge(ra, ri, a);
  });
  const ps = Math.min(20 * u, dicke * 0.42);
  segmente.forEach(g => {
    const anteil = g.t.fl[g.s] / summe[g.s];
    const rm = (g.ra + g.ri) / 2, txt = `${Math.round(100 * anteil)} %`;
    gSchrift(x, 700, ps);
    const tw = x.measureText(txt).width;
    if(anteil < 0.05 || dicke < 34 * u || g.w * rm < tw + 16 * u) return;
    const m = g.a + g.w / 2;
    if(S > 1 && Math.abs(Math.atan2(Math.sin(m - start), Math.cos(m - start))) < (26 * u) / rm) return;
    gText(x, txt, cx + Math.cos(m) * rm, cy + Math.sin(m) * rm + .5 * u, {w:700, s:ps, a:'center', b:'middle', c: textAuf(g.t.f)});
  });
  if(S > 1){
    st.sel.forEach((k, s) => {
      const ra = R - s * (dicke + rg), rm = ra - dicke / 2;
      const ph = Math.min(dicke - 8 * u, 30 * u), pw = 30 * u, px = cx - pw / 2, py = cy - rm - ph / 2;
      x.fillStyle = G_RECHNUNG; x.beginPath();
      if(x.roundRect) x.roundRect(px, py, pw, ph, 6 * u); else x.rect(px, py, pw, ph);
      x.fill();
      gText(x, SLOT[s], cx, cy - rm + 1 * u, {w:700, s:Math.min(18 * u, ph * 0.7), a:'center', b:'middle', c:'#FFFFFF', f:G_TF});
    });
  } else {
    gSchrift(x, 700, 40 * u, G_TF);
    const zs = Math.min(40 * u, 40 * u * (r0 * 1.6) / Math.max(1, x.measureText(ein.f(summe[0])).width));
    gText(x, ein.f(summe[0]), cx, cy + 6 * u, {w:700, s:zs, f:G_TF, a:'center'});
    gText(x, ein.t.replace('Franken', 'Fr.'), cx, cy + 36 * u, {s:19 * u, c:G_TINTE3, a:'center'});
  }
  const colR = s => tx0 + nameW + (s + 1) * colW;
  let ty = ty0 + 22 * u;
  st.sel.forEach((k, s) => {
    gText(x, kopfText(k, s), colR(s), ty, {w:700, s:19 * u, a:'right', f:G_TF, max: colW - 12 * u});
    if(S === 1) return;
    gSchrift(x, 400, 17 * u);
    gZeilen(x, gDs(k), colW - 12 * u, 2).forEach((z, i) => gText(x, z, colR(s), ty + 23 * u + i * 21 * u, {s:17 * u, c:G_TINTE2, a:'right'}));
  });
  ty = ty0 + kopfH;
  x.fillStyle = G_TINTE2; x.fillRect(tx0, ty - 2 * u, tx1 - tx0, Math.max(1, 2 * u));
  const zweizeilig = zeileH >= 42 * u;
  teile.forEach(t => {
    const ym = ty + zeileH / 2;
    x.fillStyle = t.f; x.fillRect(tx0, ym - 11 * u, 22 * u, 22 * u);
    gText(x, t.name, tx0 + 34 * u, ym + 7 * u, {w: t.uebrig ? 400 : 500, s:21 * u, c: t.uebrig ? G_TINTE2 : G_TINTE, max: nameW - 50 * u});
    st.sel.forEach((_, s) => {
      const v = t.v[s];
      if(v === null){ gText(x, '·', colR(s), ym + 7 * u, {s:20 * u, c:G_TINTE3, a:'right'}); return; }
      const anteil = t.fl[s] > 0 && summe[s] > 0 ? `${(100 * t.fl[s] / summe[s]).toFixed(1)} %` : (v < 0 ? 'negativ' : '0.0 %');
      if(zweizeilig){
        gText(x, ein.f(v), colR(s), ym - 2 * u, {w:500, s:20 * u, a:'right'});
        gText(x, anteil, colR(s), ym + 16 * u, {s:16 * u, c:G_TINTE3, a:'right'});
      } else {
        gText(x, `${ein.f(v)} · ${anteil}`, colR(s), ym + 6 * u, {s:17 * u, a:'right', max: colW - 8 * u});
      }
    });
    x.fillStyle = G_LINIE; x.fillRect(tx0, ty + zeileH - .75 * u, tx1 - tx0, Math.max(1, 1.5 * u));
    ty += zeileH;
  });
  const ymT = ty + zeileH / 2;
  gText(x, `Total ${knoten.id === 'root' ? gRechnungWort() : gName(knoten)}`, tx0, ymT + 7 * u, {w:700, s:21 * u, max: nameW - 12 * u});
  st.sel.forEach((_, s) => gText(x, ein.f(wert(knoten, s)), colR(s), ymT + 7 * u, {w:700, s:20 * u, a:'right'}));
  ty += zeileH;
  if(hinweis){ gSchrift(x, 400, 16 * u); gZeilen(x, hinweis, tx1 - tx0, 2).forEach((z, i) => gText(x, z, tx0, ty + 22 * u + i * 22 * u, {s:16 * u, c:G_TINTE3})); }
}

/* 3. Woher, wohin: ordentlicher Ertrag und Aufwand nach Sachgruppen, ein Datensatz */
function gUeberblick(x, W, H){
  const s = Math.min(G.slot, st.sel.length - 1), k = st.sel[s];
  const K = kennzahlenVon(k), g = gruppenVon(k);
  const reihe = (p, ramp) => Object.entries(g).filter(([c, v]) => c[0] === p && ORDENTLICH(c) && Math.abs(v) >= .5)
    .map(([c, v]) => ({c, name: D.sg[c] || c, wert: p === '4' ? -v : v})).filter(t => t.wert > 0).sort((a, b) => b.wert - a.wert)
    .map((t, i) => Object.assign(t, {f: ramp[Math.min(i, ramp.length - 1)]}));
  const ert = reihe('4', G_ERT), auf = reihe('3', G_AUF);
  const B = gRahmen(x, W, H, {titel: 'Woher das Geld kommt, wohin es geht', unter: `${gDs(k)}, ordentlicher Ertrag und Aufwand nach Sachgruppen, Millionen Franken`, ueber: 'Erfolgsrechnung', ds: [k], fuss: 'Beträge in Millionen Franken'});
  const u = B.u, quer = W > H, spalten = quer ? 3 : 2, breite = B.x1 - B.x0;
  const skala = Math.max(K.ert, K.auf, 1);
  let y = B.y0 + 4 * u;
  const block = (liste, total, label) => {
    gSpacing(x, 1.4 * u); gText(x, label.toUpperCase(), B.x0, y, {w:700, s:19 * u, c:G_TINTE3, f:G_TF}); gSpacing(x, 0);
    y += 14 * u;
    const bh = (quer ? 50 : 60) * u;
    let px = B.x0;
    for(const t of liste){
      const w = breite * t.wert / skala;
      if(w > 0){
        x.fillStyle = t.f; x.fillRect(px, y, Math.max(w - 3 * u, .5), bh);
        gSchrift(x, 700, 21 * u);
        const txt = `${Math.round(100 * t.wert / total)} %`;
        if(w - 3 * u > x.measureText(txt).width + 18 * u) gText(x, txt, px + 10 * u, y + bh / 2 + u, {w:700, s:21 * u, b:'middle', c: textAuf(t.f)});
      }
      px += w;
    }
    y += bh + 44 * u;
    const sp = breite / spalten, zh = (quer ? 50 : 58) * u;
    const zeigen = liste.slice(0, quer ? 6 : 6);
    zeigen.forEach((t, i) => {
      const lx = B.x0 + (i % spalten) * sp, ly = y + Math.floor(i / spalten) * zh;
      x.fillStyle = t.f; x.fillRect(lx, ly - 19 * u, 20 * u, 20 * u);
      gText(x, t.name, lx + 30 * u, ly, {w:500, s:21 * u, max: sp - 46 * u});
      gText(x, `${mioG(t.wert, 1)} Mio. · ${(100 * t.wert / total).toFixed(1)} %`, lx + 30 * u, ly + 25 * u, {s:18 * u, c:G_TINTE3, max: sp - 46 * u});
    });
    y += (Math.ceil(zeigen.length / spalten) - 1) * zh + 26 * u + (quer ? 40 : 50) * u;
  };
  block(ert, K.ert, `Woher · Ertrag ${mioG(K.ert, 1)} Mio.`);
  block(auf, K.auf, `Wohin · Aufwand ${mioG(K.auf, 1)} Mio.`);
  const wort = Math.round(K.gesamt) === 0 ? 'ausgeglichen' : K.gesamt < 0 ? 'Aufwandüberschuss' : 'Ertragsüberschuss';
  const teile = [`Operatives Ergebnis ${mioVz(K.ord)} Mio.`];
  if(Math.abs(K.ao) >= 5e4) teile.push(`ausserordentliches Ergebnis ${mioVz(K.ao)} Mio.`);
  if(Math.abs(K.ek) >= 5e4) teile.push(`Fonds im Eigenkapital ${mioVz(K.ek)} Mio.`);
  gSchrift(x, 400, 19 * u);
  const uz = gZeilen(x, `Überleitung: ${teile.join(' · ')}`, breite, 2);
  const yE = Math.min(y - 4 * u, B.y1 - 20 * u - (uz.length - 1) * 25 * u);
  gText(x, `Gesamtergebnis: ${mioVz(K.gesamt)} Mio. Franken (${wort})`, B.x0, yE, {w:700, s:27 * u, f:G_TF, max: breite});
  uz.forEach((z, i) => gText(x, z, B.x0, yE + 34 * u + i * 25 * u, {s:19 * u, c:G_TINTE2}));
}

/* 4. Entwicklung der gewählten Kennzahl, 2025 bis 2030 */
function gEntwicklung(x, W, H){
  const S = serienVerlauf();
  const alleK = [...S.r, ...S.b, ...S.p].filter(p => p[1] !== null).map(p => p[2]);
  const B = gRahmen(x, W, H, {titel: kzTitel(), unter: `Rechnung, Budget und Finanzplan ${J_MIN} bis ${J_MAX}, Millionen Franken.` + (st.kz === 'ekap' && st.bereich === null ? ' Budget 2026 aktualisiert mit dem Abschluss 2025.' : ''), ueber: kzUeber(), ds: alleK.length ? [...new Set(alleK)] : st.sel, fuss: 'Beträge in Millionen Franken'});
  const u = B.u;
  const da = v => v !== null && v !== undefined;
  const alle = [...S.r, ...S.b, ...S.p].map(p => p[1]).filter(da);
  if(!alle.length){ gText(x, 'Für diese Auswahl liegen keine Werte vor.', B.x0, B.y0 + 30 * u, {s:24 * u, c:G_TINTE3}); return; }
  let lo = Math.min(...alle), hi = Math.max(...alle);
  if(lo < 0 || hi <= 0){ lo = Math.min(lo, 0); hi = Math.max(hi, 0); }
  else { lo = Math.max(0, lo - (hi - lo) * 0.3); }
  const schritt = (() => { const roh = (hi - lo || 1) / 5, p = Math.pow(10, Math.floor(Math.log10(roh))); return [1, 2, 2.5, 5, 10].map(f => f * p).find(q => q >= roh); })();
  lo = Math.floor(lo / schritt) * schritt; hi = Math.ceil(hi / schritt) * schritt;
  const legTexte = ['Rechnung', 'Budget', 'Finanzplan'];
  const L = B.x0 + 90 * u, R = B.x1 - 250 * u, T = B.y0 + 34 * u, BU = B.y1 - 96 * u;
  const xj = j => L + (R - L) * (j - J_MIN) / (J_MAX - J_MIN);
  const yv = v => T + (BU - T) * (1 - (v - lo) / ((hi - lo) || 1));
  for(let v = lo; v <= hi + 1e-6; v += schritt){
    x.fillStyle = Math.abs(v) < 1e-6 ? G_LINIE2 : G_LINIE; x.fillRect(L, yv(v) - .75 * u, R - L, Math.max(1, 1.5 * u));
    gText(x, mioG(v, schritt < 1e6 ? 1 : 0), L - 16 * u, yv(v) + 6 * u, {s:18 * u, c:G_TINTE3, a:'right'});
  }
  for(let j = J_MIN; j <= J_MAX; j++) gText(x, String(j), xj(j), BU + 34 * u, {s:18 * u, c:G_TINTE3, a:'center'});
  const xb = (xj(2027) + xj(2028)) / 2;
  x.fillStyle = G_LINIE2; x.fillRect(xb - .75 * u, T - 26 * u, Math.max(1, 1.5 * u), BU - T + 26 * u);
  gText(x, 'Budget', xb - 10 * u, T - 10 * u, {s:16 * u, c:G_TINTE3, a:'right'});
  gText(x, 'Finanzplan', xb + 10 * u, T - 10 * u, {s:16 * u, c:G_TINTE3});
  const strich = art => art === 'strich' ? [12 * u, 9 * u] : art === 'punkt' ? [1 * u, 9 * u] : [];
  const linie = (pts, farbe, art) => {
    const p = pts.filter(q => da(q[1])); if(p.length < 2) return;
    x.save(); x.strokeStyle = farbe; x.lineWidth = 3.5 * u; x.lineJoin = 'round'; x.lineCap = art === 'punkt' ? 'round' : 'butt';
    x.setLineDash(strich(art));
    x.beginPath(); p.forEach((q, i) => i ? x.lineTo(xj(q[0]), yv(q[1])) : x.moveTo(xj(q[0]), yv(q[1]))); x.stroke(); x.restore();
  };
  linie(S.b, G_BUDGET, 'strich'); linie(S.p, G_PLAN, 'punkt'); linie(S.r, G_RECHNUNG);
  const punkte = (pts, art) => pts.forEach(([j, v]) => {
    if(!da(v)) return;
    x.save(); x.beginPath();
    if(art === 'p'){ const r = 6.5 * u; x.moveTo(xj(j), yv(v) - r); x.lineTo(xj(j) + r, yv(v)); x.lineTo(xj(j), yv(v) + r); x.lineTo(xj(j) - r, yv(v)); x.closePath(); }
    else x.arc(xj(j), yv(v), 6.5 * u, 0, 2 * Math.PI);
    x.fillStyle = art === 'r' ? G_RECHNUNG : '#FFFFFF'; x.fill(); x.lineWidth = 3 * u; x.strokeStyle = art === 'r' ? '#FFFFFF' : art === 'p' ? G_PLAN : G_BUDGET; x.stroke(); x.restore();
  });
  punkte(S.b, 'b'); punkte(S.p.filter(q => q[0] > 2027), 'p'); punkte(S.r, 'r');
  // Endwerte rechts: letzter Planwert, sonst letztes Budget
  const lx = xj(J_MAX) + 30 * u;
  const ende = [...S.p].reverse().find(q => da(q[1])) || [...S.b].reverse().find(q => da(q[1]));
  if(ende){
    gText(x, ende[0] > 2027 ? `Finanzplan ${ende[0]}` : `Budget ${ende[0]}`, lx, yv(ende[1]) - 8 * u, {s:17 * u, c:G_TINTE3});
    gText(x, `${mioG(ende[1], 1)} Mio.`, lx, yv(ende[1]) + 18 * u, {w:700, s:25 * u, f:G_TF});
  }
  const rEnde = [...S.r].reverse().find(q => da(q[1]));
  if(rEnde){
    const yr = Math.max(T + 20 * u, Math.min(BU, yv(rEnde[1])));
    gText(x, `${mioG(rEnde[1], 1)}`, xj(rEnde[0]) + 14 * u, yr - 14 * u, {w:700, s:20 * u, f:G_TF, c:G_RECHNUNG});
  }
  let gx = L, gy = B.y1 - 12 * u;
  const leg = (farbe, art, voll, text, raute) => {
    x.save(); x.strokeStyle = farbe; x.lineWidth = 3.5 * u; x.setLineDash(strich(art)); x.lineCap = art === 'punkt' ? 'round' : 'butt';
    x.beginPath(); x.moveTo(gx, gy - 7 * u); x.lineTo(gx + 44 * u, gy - 7 * u); x.stroke(); x.restore();
    x.beginPath();
    if(raute){ const r = 6 * u, cx = gx + 22 * u, cy = gy - 7 * u; x.moveTo(cx, cy - r); x.lineTo(cx + r, cy); x.lineTo(cx, cy + r); x.lineTo(cx - r, cy); x.closePath(); }
    else x.arc(gx + 22 * u, gy - 7 * u, 6 * u, 0, 2 * Math.PI);
    x.fillStyle = voll ? farbe : '#FFFFFF'; x.fill(); x.lineWidth = 3 * u; x.strokeStyle = voll ? '#FFFFFF' : farbe; x.stroke();
    gx += 56 * u; gx += gText(x, text, gx, gy, {s:19 * u, c:G_TINTE2}) + 38 * u;
  };
  leg(G_RECHNUNG, null, true, legTexte[0]); leg(G_BUDGET, 'strich', false, legTexte[1]); leg(G_PLAN, 'punkt', false, legTexte[2], true);
}

/* 5. Kennzahlen im Vergleich */
function gKennzahlen(x, W, H){
  const S = st.sel.length;
  const B = gRahmen(x, W, H, {titel: 'Kennzahlen im Vergleich', unter: S === 1 ? `${gDs(st.sel[0])}, Millionen Franken` : `Millionen Franken, Differenzen gegenüber ${SLOT[0]} (${gDs(st.sel[0])})`, ueber: 'Erfolgsrechnung, Investitionsrechnung, Bilanz', fuss: 'Beträge in Millionen Franken'});
  const u = B.u, quer = W > H, breite = B.x1 - B.x0;
  const nameW = breite * (quer ? (S === 1 ? 0.55 : 0.4) : 0.38);
  const spW = (breite - nameW) / S;
  let y = B.y0 + 2 * u;
  let kopfZeilen = 1;
  st.sel.forEach((k, s) => {
    const xr = B.x0 + nameW + spW * (s + 1) - (s < S - 1 ? 28 * u : 0);
    gSchrift(x, 400, 19 * u);
    const tz = gZeilen(x, gDs(k), spW - 40 * u, 2);
    kopfZeilen = Math.max(kopfZeilen, tz.length);
    const tw = gText(x, SLOT[s], xr, y, {w:700, s:22 * u, f:G_TF, a:'right'});
    x.fillStyle = G_SLOT[s]; x.fillRect(xr - tw - 30 * u, y - 18 * u, 20 * u, 20 * u);
    tz.forEach((z, i) => gText(x, z, xr, y + 28 * u + i * 24 * u, {s:19 * u, c:G_TINTE2, a:'right'}));
  });
  y += 28 * u + (kopfZeilen - 1) * 24 * u + 16 * u;
  x.fillStyle = G_TINTE2; x.fillRect(B.x0, y, breite, Math.max(1, 2 * u));
  const liste = KENNZAHLEN.filter(([key]) => st.sel.some(k => kzRoh(k, key) !== null));
  const zeileH = Math.min(84 * u, (B.y1 - y) / liste.length);
  liste.forEach(([key, name, erkl], i) => {
    const yz = y + (i + 1) * zeileH, mitte = yz - zeileH / 2;
    gSchrift(x, 500, 23 * u);
    const nz = quer ? [gKuerzen(x, name, nameW - 24 * u)] : gZeilen(x, name, nameW - 24 * u, 2);
    const mitErkl = quer && erkl && zeileH >= 60 * u;
    const nb = mitErkl ? mitte - 3 * u : mitte + 8 * u - (nz.length - 1) * 13 * u;
    nz.forEach((z, j) => gText(x, z, B.x0, nb + j * 27 * u, {w:500, s:23 * u}));
    if(mitErkl) gText(x, erkl, B.x0, mitte + 23 * u, {s:16 * u, c:G_TINTE3, max: nameW - 24 * u});
    st.sel.forEach((k, s) => {
      const v = kzRoh(k, key), xr = B.x0 + nameW + spW * (s + 1) - (s < S - 1 ? 28 * u : 0);
      if(v === null){ gText(x, '·', xr, mitte + 9 * u, {s:25 * u, a:'right', c:G_TINTE3}); return; }
      const txt = kzFormat(key, v);
      if(s === 0){ gText(x, txt, xr, mitte + 9 * u, {w:500, s:25 * u, a:'right'}); return; }
      gText(x, txt, xr, mitte - 1 * u, {w:500, s:25 * u, a:'right'});
      const b = kzRoh(st.sel[0], key);
      if(b === null) return;
      const d = v - b;
      gText(x, kzDiff(key, d, b), xr, mitte + 24 * u, {s:17 * u, c:G_TINTE3, a:'right', max: spW - 16 * u});
    });
    x.fillStyle = G_LINIE; x.fillRect(B.x0, yz - .75 * u, breite, Math.max(1, 1.5 * u));
  });
}

/* Dialog */
const G_ZEICHNER = {balken: gBalken, kuchen: gKuchen, ringe: gRinge, ueberblick: gUeberblick, entwicklung: gEntwicklung, kennzahlen: gKennzahlen};
function gEbenenFuellen(){
  const sel = $('#grafikEbene'); sel.innerHTML = '';
  const weg = aktuellerKnoten(), jetzt = weg[weg.length - 1], zu = gesperrt();
  const oben = el('optgroup', {label: 'Geöffnete Ebene und darüber'});
  weg.forEach((n, i) => oben.append(el('option', {value: n.id, text: (n.id === 'root' ? `${gRechnungWort()}, oberste Ebene` : gName(n)) + (i === weg.length - 1 && i > 0 ? ' (geöffnet)' : '')})));
  sel.append(oben);
  const unter = zu ? [] : kinderSortiert(jetzt).filter(c => !c.blatt && c.kinder.size);
  if(unter.length){
    const og = el('optgroup', {label: 'Eine Ebene tiefer'});
    unter.forEach(c => og.append(el('option', {value: c.id, text: gName(c) + (st.markiert === c.id ? ' (Suchtreffer)' : '')})));
    sel.append(og);
  }
  sel.value = G.ebene && [...sel.options].some(o => o.value === G.ebene) ? G.ebene : jetzt.id;
  const h = $('#grafikEbeneHinweis');
  h.hidden = !zu;
  h.textContent = zu ? 'Der Finanzplan liegt nur nach Sachgruppen vor: Grafik für die oberste Ebene.' : '';
}
function gZeichnen(){
  const f = G_FORMATE[G.format], c = $('#grafikCanvas');
  if(c.width !== f.w) c.width = f.w;
  if(c.height !== f.h) c.height = f.h;
  const x = c.getContext('2d');
  x.setTransform(1, 0, 0, 1, 0, 0);
  G_ZEICHNER[G.motiv](x, f.w, f.h);
  const mitEbene = G_MIT_EBENE.includes(G.motiv);
  $('#grafikEbeneZeile').hidden = !mitEbene;
  if(!mitEbene) $('#grafikTiefeZeile').hidden = true;
  if(mitEbene){
    const z = gZielKnoten();
    $('#grafikTiefeZeile').hidden = gesperrt() || !(z.alleKonten || [...z.kinder.values()].some(k => !k.blatt));
    $('#grafikTiefe').value = G.tiefe;
    const e = $('#grafikEbeneStand');
    const gewaehlt = (G.ebene && gKnotenVon(G.ebene)) || aktuellerKnoten().slice(-1)[0];
    e.hidden = !(z.id !== gewaehlt.id || z.alleKonten);
    e.textContent = z.alleKonten ? `Gezeigt: alle Konten unter ${z.id === 'root' ? gRechnungWort() : gName(z)} (${z.kinder.size}).` : `Gezeigt: ${gName(z)}, weil ${gName(gewaehlt)} nur diesen Untereintrag hat.`;
  }
  const mitSlot = ['kuchen', 'ueberblick'].includes(G.motiv) && st.sel.length > 1;
  $('#grafikSlotZeile').hidden = !mitSlot;
  $('#grafikSkalaZeile').hidden = !(G.motiv === 'ringe' && st.sel.length > 1);
  $('#grafikSkala').value = G.skala;
  const sl = $('#grafikSlot');
  sl.innerHTML = '';
  st.sel.forEach((k, s) => sl.append(el('option', {value: String(s), text: `${SLOT[s]} · ${gDs(k)}`})));
  sl.value = String(Math.min(G.slot, st.sel.length - 1));
  $('#grafikNote').textContent = G_NOTIZ[G.motiv];
  $('#grafikTitel').placeholder = G.autoTitel;
  $('#grafikMass').textContent = `${f.m}, PNG. Quelle und Datenstand stehen in der Grafik.`;
  $('#grafikVorschau').classList.toggle('transparent', G.hg !== 'weiss');
  c.setAttribute('aria-label', `Vorschau: ${G.titel.trim() || G.autoTitel}`);
}
function gDateiname(){
  const E = gEbene();
  const knoten = ['kuchen', 'ringe'].includes(G.motiv) && !E.jetzt.kinder.size && E.jetzt.eltern ? E.jetzt.eltern : E.jetzt;
  const teil = G_MIT_EBENE.includes(G.motiv) ? '-' + st.rechnung + '-' + (knoten.code || (knoten.id === 'root' ? 'total' : knoten.id)).replace(/[^\w.]+/g, '') + (knoten.alleKonten ? '-konten' : '') + (G.motiv === 'ringe' && st.sel.length > 1 ? (G.skala === 'betrag' ? '-skala' : '-anteile') : '')
    : G.motiv === 'entwicklung' ? '-' + (st.bereich !== null ? st.bereich : st.kz) : '';
  const ds = G.motiv === 'entwicklung' ? J_MIN + '-' + J_MAX : ['kuchen', 'ueberblick'].includes(G.motiv) ? st.sel[Math.min(G.slot, st.sel.length - 1)] : st.sel.join('-');
  return `finanzspiegel-${G.motiv}-${ds}${teil}-${G.format}.png`;
}
function gMeldung(t){ const m = $('#grafikMeldung'); m.textContent = t; clearTimeout(m._t); m._t = setTimeout(() => { m.textContent = ''; }, 6000); }
function oeffneGrafik(motiv, opener){
  if(motiv) G.motiv = motiv;
  G.opener = opener || document.activeElement;
  G.titel = ''; G.slot = Math.min(G.slot, st.sel.length - 1);
  const jetzt = aktuellerKnoten().slice(-1)[0], mk = st.markiert && jetzt.kinder.get(st.markiert);
  G.ebene = mk && !mk.blatt && mk.kinder.size && !gesperrt() ? mk.id : null;
  gEbenenFuellen();
  $('#grafikMotiv').value = G.motiv; $('#grafikFormat').value = G.format; $('#grafikTitel').value = ''; $('#grafikMeldung').textContent = '';
  $$('input[name="grafikHg"]').forEach(r => { r.checked = r.value === G.hg; });
  $('#grafikLage').classList.add('offen');
  document.body.classList.add('grafik-offen');
  document.body.style.overflow = 'hidden';
  gZeichnen();
  if(document.fonts && document.fonts.load){
    Promise.all([`700 48px ${G_TF}`, `600 20px ${G_F}`, `400 20px ${G_F}`, `500 20px ${G_F}`, `700 20px ${G_F}`].map(f => document.fonts.load(f))).then(() => { if($('#grafikLage').classList.contains('offen')) gZeichnen(); }).catch(() => {});
  }
  setTimeout(() => $('#grafikMotiv').focus(), 30);
}
function schliesseGrafik(){
  $('#grafikLage').classList.remove('offen');
  document.body.classList.remove('grafik-offen');
  document.body.style.overflow = '';
  if(G.opener && G.opener.focus) G.opener.focus();
}
function grafikInit(){
  const mot = $('#grafikMotiv'), fmt = $('#grafikFormat'), lage = $('#grafikLage');
  G_MOTIVE.forEach(([k, t]) => mot.append(el('option', {value:k, text:t})));
  Object.entries(G_FORMATE).forEach(([k, f]) => fmt.append(el('option', {value:k, text:`${f.t} (${f.m.replace(' Pixel', '')})`})));
  $('#grafikAuf').addEventListener('click', ev => oeffneGrafik(null, ev.currentTarget));
  $$('[data-grafik]').forEach(b => b.addEventListener('click', ev => oeffneGrafik(b.dataset.grafik, ev.currentTarget)));
  $('#grafikZu').addEventListener('click', schliesseGrafik);
  lage.addEventListener('click', ev => { if(ev.target === lage) schliesseGrafik(); });
  document.addEventListener('keydown', ev => { if(ev.key === 'Escape' && lage.classList.contains('offen')){ ev.preventDefault(); schliesseGrafik(); } });
  lage.addEventListener('keydown', ev => {
    if(ev.key !== 'Tab') return;
    const f = $$('button, select, input', lage).filter(e => !e.disabled && e.offsetParent !== null && !(e.type === 'radio' && !e.checked));
    if(!f.length) return;
    const i = f.indexOf(document.activeElement);
    if(ev.shiftKey && i <= 0){ ev.preventDefault(); f[f.length - 1].focus(); }
    else if(!ev.shiftKey && i === f.length - 1){ ev.preventDefault(); f[0].focus(); }
  });
  mot.addEventListener('change', () => { G.motiv = mot.value; gZeichnen(); });
  fmt.addEventListener('change', () => { G.format = fmt.value; gZeichnen(); });
  $('#grafikSlot').addEventListener('change', ev => { G.slot = +ev.target.value; gZeichnen(); });
  $('#grafikSkala').addEventListener('change', ev => { G.skala = ev.target.value; gZeichnen(); });
  $('#grafikEbene').addEventListener('change', ev => { G.ebene = ev.target.value; gZeichnen(); });
  $('#grafikTiefe').addEventListener('change', ev => { G.tiefe = ev.target.value; gZeichnen(); });
  $$('input[name="grafikHg"]').forEach(r => r.addEventListener('change', () => { if(r.checked){ G.hg = r.value; gZeichnen(); } }));
  let tt; $('#grafikTitel').addEventListener('input', ev => { G.titel = ev.target.value; clearTimeout(tt); tt = setTimeout(gZeichnen, 150); });
  $('#grafikLaden').addEventListener('click', () => {
    gZeichnen();
    const a = document.createElement('a');
    a.download = gDateiname();
    a.href = $('#grafikCanvas').toDataURL('image/png');
    document.body.append(a); a.click(); a.remove();
    gMeldung('Heruntergeladen: ' + a.download);
  });
  $('#grafikKopie').addEventListener('click', async () => {
    gZeichnen();
    const c = $('#grafikCanvas');
    const bild = new Promise((ok, fehler) => c.toBlob(b => b ? ok(b) : fehler(new Error('leer')), 'image/png'));
    try{
      if(!navigator.clipboard || !navigator.clipboard.write || typeof ClipboardItem === 'undefined') throw new Error('keine Zwischenablage');
      try{ await navigator.clipboard.write([new ClipboardItem({'image/png': bild})]); }
      catch(e){ await navigator.clipboard.write([new ClipboardItem({'image/png': await bild})]); }
      gMeldung('Grafik in der Zwischenablage. In Word oder PowerPoint mit Einfügen übernehmen.');
    }catch(e){ gMeldung('Kopieren ist in diesem Browser nicht möglich. Bitte als PNG herunterladen.'); }
  });
}

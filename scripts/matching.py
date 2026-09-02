#!/usr/bin/env python3
"""
Wähler-Matching: Prototyp
=========================
Baut aus all_sessions.json einen interaktiven Fragebogen. Wählt automatisch die
trennschärfsten Sachabstimmungen der laufenden Legislatur (die die Fraktionen am
stärksten teilen), thematisch gestreut und je Geschäft nur einmal, und erzeugt
eine standalone HTML-Demo. Der Nutzer beantwortet die Fragen mit Ja oder Nein,
die Übereinstimmung mit Ratsmitgliedern und Fraktionen wird nach dem
Proximity-Modell berechnet.

Grundsätze (siehe docs/KONZEPT_waehler-matching.md):
- nur Abstimmungen mit geprüftem Thema und geklärter Richtung (keine offenen
  Umkehrfälle),
- keine politische Wertung: die Richtung bewertet der Nutzer selbst,
- Rohstimmen werden nie verändert; Enthaltung und Abwesenheit zählen nicht.

Ausführen: python3 scripts/matching.py  ->  output/matching-prototyp.html
"""
import json, re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUTPUT = ROOT / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

N_FRAGEN = 12
MIN_BETEILIGUNG = 30      # Mindestzahl Ja+Nein, damit eine Abstimmung zählt
MAX_PRO_THEMA = 3         # thematische Streuung
MIN_GEMEINSAM = 5         # Mindestzahl beantworteter Fragen für eine Wertung

PARTEI_FARBE = {"SVP": "svp", "SP": "sp", "GLP": "glp", "FDP": "fdp"}


def kurz(geschaeft, titel):
    """Lesbare, anonyme Kurzfassung des Geschäfts. Bevorzugt den Titel in
    Anführungszeichen ('mit dem Titel «...»') oder den Teil nach 'betreffend',
    fällt auf den Geschäftstext zurück, nie auf 'Antrag <Name>'."""
    g = (geschaeft or "").strip()
    m = (re.search(r"mit dem Titel\s+[«\"]([^»\"]+)[»\"]", g)
         or re.search(r"betreffend\s+(.*)", g))
    s = m.group(1) if m else g
    s = re.sub(r"\s+", " ", s).strip(" «».")
    s = s.replace(" - ", ", ")           # Gedankenstrich vermeiden
    return s[:110] if s else "Abstimmung"


def waehle_fragen(sessions, leg):
    S = [s for s in sessions if s["legislatur"] == leg]
    # Nur Sitzungen mit publiziertem Wortprotokoll zulassen (Whitelist aus
    # protokoll_urls.json). Fragen ohne verfügbares Protokoll fallen weg.
    pfile = DATA / "protokoll_urls.json"
    mit_protokoll = set(json.load(open(pfile)).keys()) if pfile.exists() else None
    # Fraktionsgrössen aus der neuesten Sitzung
    fsize = defaultdict(int)
    for m in S[0]["members"]:
        fsize[m["fraktion"]] += 1
    frak = [f for f, _ in sorted(fsize.items(), key=lambda x: -x[1])]

    def wmean(ps, ws):
        return sum(p * w for p, w in zip(ps, ws)) / sum(ws)

    cands = []
    for si, s in enumerate(S):
        for i, v in enumerate(s["votes"]):
            if not v.get("thema_gruppe"):
                continue
            if v.get("richtung_invertiert") is None:      # offene Umkehr ausschliessen
                continue
            if mit_protokoll is not None and str(s.get("cid")) not in mit_protokoll:
                continue                                   # kein publiziertes Protokoll
            fja = defaultdict(int); fnein = defaultdict(int); ja = nein = 0
            for m in s["members"]:
                vv = m["votes"][i] if i < len(m["votes"]) else None
                if vv == "Ja":
                    ja += 1; fja[m["fraktion"]] += 1
                elif vv == "Nein":
                    nein += 1; fnein[m["fraktion"]] += 1
            if ja + nein < MIN_BETEILIGUNG:
                continue
            ps = []; ws = []
            for f in frak:
                t = fja[f] + fnein[f]
                if t >= 3:
                    ps.append(fja[f] / t); ws.append(fsize[f])
            if len(ps) < 3:
                continue
            mu = wmean(ps, ws)
            trenn = wmean([(p - mu) ** 2 for p in ps], ws) ** 0.5
            cands.append({
                "si": si, "i": i, "trenn": trenn,
                "knapp": min(ja, nein) / (ja + nein),
                "geschaeft": v.get("geschaeft") or "",
                "thema": v.get("thema_name"), "tg": v["thema_gruppe"],
                "kurz": kurz(v.get("geschaeft"), v.get("titel")),
            })
    # je Geschäft nur die trennschärfste Abstimmung
    best = {}
    for c in cands:
        k = c["geschaeft"]
        if k not in best or c["trenn"] > best[k]["trenn"]:
            best[k] = c
    uniq = sorted(best.values(), key=lambda c: -c["trenn"])
    # thematische Streuung
    sel = []; per = defaultdict(int)
    for c in uniq:
        if per[c["tg"]] >= MAX_PRO_THEMA:
            continue
        sel.append(c); per[c["tg"]] += 1
        if len(sel) == N_FRAGEN:
            break
    return S, frak, sel


def frage_key(session, nr):
    """Eindeutiger Schlüssel je Abstimmung. Vormittag und Nachmittag teilen sich
    dieselbe cid und nummerieren beide ab 1, darum gehört die Tageshälfte in den
    Schlüssel."""
    lab = session["sitzung"]
    halb = ("V" if "Vormittag" in lab else "N" if "Nachmittag" in lab
            else "A" if "Abend" in lab else "X")
    return f"{session.get('cid')}_{halb}_{nr}"


def baue_daten(sessions, leg):
    S, frak, sel = waehle_fragen(sessions, leg)
    aktuell = S[0]["members"]        # amtierende Mitglieder = neueste Sitzung

    kontext = {}
    kfile = DATA / "frage_kontext.json"
    if kfile.exists():
        kontext = json.load(open(kfile))

    fragen = []
    for c in sel:
        s = S[c["si"]]
        nr = s["votes"][c["i"]]["nr"]
        k = kontext.get(frage_key(s, nr), {})
        fragen.append({"kurz": c["kurz"], "thema": c["thema"],
                       "geschaeft": c["geschaeft"], "trenn": round(c["trenn"], 2),
                       "kontext": k.get("kontext"), "pro": k.get("pro"), "contra": k.get("contra")})

    def stimme_in(session, idx, nach, vor):
        for m in session["members"]:
            if m["nachname"] == nach and m["vorname"] == vor:
                vv = m["votes"][idx] if idx < len(m["votes"]) else None
                return vv if vv in ("Ja", "Nein") else None
        return None

    mitglieder = []
    for m in aktuell:
        stimmen = [stimme_in(S[c["si"]], c["i"], m["nachname"], m["vorname"]) for c in sel]
        mitglieder.append({
            "name": f"{m['vorname']} {m['nachname']}".strip(),
            "fraktion": m["fraktion"],
            "partei": m["partei"],
            "farbe": PARTEI_FARBE.get(m["partei"], "muted"),
            "stimmen": stimmen,
        })

    return {"fragen": fragen, "mitglieder": mitglieder, "fraktionen": frak,
            "min_gemeinsam": MIN_GEMEINSAM, "legislatur": leg}


# ---------------------------------------------------------------------------
CSS = """
:root{--ink:#1a1a1a;--paper:#faf9f6;--line:#e2ddd3;--muted:#6b6459;
--svp:#3a7d3a;--sp:#c1272d;--glp:#e0a800;--fdp:#2b5c8a;--accent:#8a1a1a}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:"Source Sans 3",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
background:var(--paper);color:var(--ink);line-height:1.5;font-size:16px}
.wrap{max-width:820px;margin:0 auto;padding:0 20px 60px}
header{border-bottom:3px solid var(--ink);padding:30px 0 18px;margin-bottom:8px}
.eyebrow{font-size:12px;letter-spacing:.18em;text-transform:uppercase;color:var(--muted);font-weight:600;margin-bottom:6px}
h1{font-family:Georgia,serif;font-size:clamp(24px,4vw,34px);line-height:1.08}
.sub{margin-top:10px;color:var(--muted);font-size:15px;max-width:62ch}
.proto{display:inline-block;margin-top:12px;background:#f3ede0;border:1px solid var(--line);
border-radius:4px;padding:6px 12px;font-size:13px;color:#7a5c00}
h2.sec{font-family:Georgia,serif;font-size:20px;margin:34px 0 4px}
.note{color:var(--muted);font-size:14px;margin-bottom:18px;max-width:66ch}
.frage{border:1px solid var(--line);border-radius:8px;padding:16px 18px;margin-bottom:14px;background:#fff}
.frage .thema{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);font-weight:700}
.frage .txt{font-size:16px;font-weight:600;margin:6px 0 12px}
.frage details{margin:4px 0 12px}
.frage summary{font-size:13px;color:var(--accent);cursor:pointer}
.frage details p{font-size:13px;color:var(--muted);margin-top:6px}
.frage .kontext{font-size:14px;color:#3a352c;margin:2px 0 12px;line-height:1.55}
.zitate{display:grid;gap:8px;margin:0 0 14px}
.z{font-size:13.5px;line-height:1.5;padding:9px 12px;border-radius:6px;border-left:3px solid;background:#faf8f3}
.z .zl{display:block;font-size:10px;letter-spacing:.1em;text-transform:uppercase;font-weight:700;color:var(--muted);margin-bottom:3px}
.z.za{border-left-color:#7f8a93}
.z.zb{border-left-color:#b3a684}
.opts{display:flex;gap:8px;flex-wrap:wrap}
.opts button{font:inherit;font-weight:600;font-size:14px;padding:8px 18px;border:1px solid var(--line);
background:#fff;border-radius:20px;cursor:pointer;color:var(--ink)}
.opts button:hover{border-color:var(--muted)}
.opts button.ja.on{background:#2f6b2f;border-color:#2f6b2f;color:#fff}
.opts button.nein.on{background:var(--accent);border-color:var(--accent);color:#fff}
.opts button.skip.on{background:var(--muted);border-color:var(--muted);color:#fff}
.bar{position:sticky;bottom:0;background:linear-gradient(transparent,var(--paper) 24%);
padding:20px 0 8px;margin-top:10px;display:flex;gap:14px;align-items:center;flex-wrap:wrap}
.bar button{font:inherit;font-weight:700;font-size:16px;padding:12px 26px;border:none;border-radius:6px;
background:var(--accent);color:#fff;cursor:pointer}
.bar button:disabled{background:#c9c2b6;cursor:not-allowed}
.bar .cnt{color:var(--muted);font-size:14px}
#ergebnis{margin-top:20px}
.rang{display:flex;align-items:center;gap:12px;padding:9px 0;border-bottom:1px solid var(--line)}
.rang .pos{width:26px;color:var(--muted);font-weight:700;text-align:right}
.rang .nm{flex:1;font-weight:600}
.rang .fr{font-size:12px;color:var(--muted)}
.rang .pct{font-variant-numeric:tabular-nums;font-weight:700;width:64px;text-align:right}
.meter{height:8px;border-radius:5px;background:#eee;width:120px;overflow:hidden}
.meter>span{display:block;height:100%}
.tag{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:2px}
.svp{background:var(--svp)}.sp{background:var(--sp)}.glp{background:var(--glp)}.fdp{background:var(--fdp)}
.muted{background:var(--muted)}
.frakcard{display:flex;align-items:center;gap:12px;padding:12px 14px;border:1px solid var(--line);
border-radius:8px;margin-bottom:8px;background:#fff}
.frakcard .nm{flex:1;font-weight:700}
.frakcard .pct{font-weight:800;font-size:18px;font-variant-numeric:tabular-nums}
.subtabs{display:flex;gap:0;border-bottom:1px solid var(--line);margin:26px 0 16px}
.subtabs button{background:none;border:none;font:inherit;font-weight:600;font-size:14px;padding:10px 14px;
color:var(--muted);border-bottom:3px solid transparent;margin-bottom:-1px;cursor:pointer}
.subtabs button.on{color:var(--ink);border-bottom-color:var(--accent)}
"""

JS = """
const D = __DATA__;
const answers = new Array(D.fragen.length).fill(null);

function render(){
  const box = document.getElementById('fragen');
  box.innerHTML = D.fragen.map((f,idx)=>{
    const zitate = (f.pro && f.contra) ? `
      <div class="zitate">
        <div class="z za"><span class="zl">Aus der Debatte, dafür</span>«${f.pro}»</div>
        <div class="z zb"><span class="zl">Aus der Debatte, dagegen</span>«${f.contra}»</div>
      </div>` : '';
    return `
    <div class="frage">
      <div class="thema">${f.thema||''}</div>
      <div class="txt">${idx+1}. ${f.kurz}</div>
      ${f.kontext ? `<p class="kontext">${f.kontext}</p>` : ''}
      ${zitate}
      <details><summary>Vollständiger Geschäftstext und Quelle</summary><p>${f.geschaeft||''}</p></details>
      <div class="opts" data-q="${idx}">
        <button class="ja" onclick="pick(${idx},'Ja',this)">Ja, dafür</button>
        <button class="nein" onclick="pick(${idx},'Nein',this)">Nein, dagegen</button>
        <button class="skip" onclick="pick(${idx},'skip',this)">Keine Meinung</button>
      </div>
    </div>`;}).join('');
}
function pick(q,val,btn){
  answers[q] = (val==='skip') ? 'skip' : val;
  const wrap = btn.parentElement;
  [...wrap.children].forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');
  const done = answers.filter(a=>a!==null).length;
  document.getElementById('cnt').textContent = done+' / '+D.fragen.length+' beantwortet';
  document.getElementById('go').disabled = answers.filter(a=>a==='Ja'||a==='Nein').length < 1;
}
function matchOf(stimmen){
  let gem=0, ueb=0;
  for(let k=0;k<answers.length;k++){
    const a=answers[k], s=stimmen[k];
    if((a==='Ja'||a==='Nein') && (s==='Ja'||s==='Nein')){ gem++; if(a===s) ueb++; }
  }
  return {gem, score: gem>0 ? ueb/gem : null};
}
function auswerten(){
  // Mitglieder
  const rows = D.mitglieder.map(m=>{
    const r=matchOf(m.stimmen); return {...m, ...r};
  }).filter(m=>m.gem>=D.min_gemeinsam && m.score!==null)
    .sort((a,b)=> b.score-a.score || b.gem-a.gem);
  // Fraktionen: Mittel der Mitglieder-Scores
  const byF={};
  rows.forEach(m=>{(byF[m.fraktion]=byF[m.fraktion]||[]).push(m.score);});
  const fr=Object.entries(byF).map(([f,arr])=>({f,score:arr.reduce((x,y)=>x+y,0)/arr.length,n:arr.length}))
    .sort((a,b)=>b.score-a.score);

  const pct=x=>Math.round(x*100)+'%';
  const farbe=fr=>{const s=fr.toUpperCase();return s.includes('SVP')?'svp':s.includes('SP-')?'sp':s.includes('FDP')?'fdp':s.includes('GLP')?'glp':'muted';};

  let html = '<h2 class="sec">Grösste Übereinstimmung</h2>';
  html += '<div class="subtabs"><button class="on" onclick="tab(0,this)">Fraktionen</button>'
        + '<button onclick="tab(1,this)">Ratsmitglieder</button></div>';
  html += '<div id="t0">'+ fr.map(x=>`
    <div class="frakcard"><span class="tag ${farbe(x.f)}"></span>
      <span class="nm">${x.f}</span>
      <div class="meter"><span class="${farbe(x.f)}" style="width:${pct(x.score)}"></span></div>
      <span class="pct">${pct(x.score)}</span></div>`).join('') + '</div>';
  html += '<div id="t1" style="display:none">'+ rows.slice(0,20).map((m,i)=>`
    <div class="rang"><span class="pos">${i+1}</span>
      <span class="tag ${m.farbe}"></span>
      <span class="nm">${m.name} <span class="fr">${m.fraktion}</span></span>
      <div class="meter"><span class="${m.farbe}" style="width:${pct(m.score)}"></span></div>
      <span class="pct">${pct(m.score)}</span></div>`).join('')
    + `<p class="note" style="margin-top:14px">Gezeigt werden amtierende Mitglieder mit mindestens ${D.min_gemeinsam} gemeinsam beantworteten Fragen. Prozent = Anteil übereinstimmender Stimmen.</p></div>`;
  const out=document.getElementById('ergebnis');
  out.innerHTML=html; out.scrollIntoView({behavior:'smooth'});
}
function tab(n,btn){
  document.getElementById('t0').style.display = n===0?'block':'none';
  document.getElementById('t1').style.display = n===1?'block':'none';
  [...btn.parentElement.children].forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');
}
render();
"""

HTML = """<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kantonsrat Schaffhausen · Wähler-Matching (Prototyp)</title>
<style>__CSS__</style></head>
<body><div class="wrap">
<header>
<div class="eyebrow">Kantonsrat Schaffhausen · Prototyp</div>
<h1>Welche Fraktion stimmt wie Sie?</h1>
<p class="sub">Beantworten Sie die folgenden Sachfragen, über die der Kantonsrat in der laufenden Legislatur tatsächlich abgestimmt hat. Danach sehen Sie, welche Fraktionen und Mitglieder am häufigsten gleich gestimmt haben wie Sie.</p>
<div class="proto">Prototyp: Fragen automatisch nach Trennschärfe gewählt, Texte noch Rohfassungen aus den Geschäftstiteln.</div>
</header>
<h2 class="sec">Die Fragen</h2>
<p class="note">Ein Ja bedeutet Zustimmung zum jeweiligen Geschäft, ein Nein Ablehnung. Über den aufklappbaren Text sehen Sie den genauen Wortlaut.</p>
<div id="fragen"></div>
<div class="bar">
<button id="go" disabled onclick="auswerten()">Auswerten</button>
<span class="cnt" id="cnt">0 / 0 beantwortet</span>
</div>
<div id="ergebnis"></div>
</div>
<script>__JS__</script>
</body></html>"""


def main():
    d = json.load(open(DATA / "all_sessions.json"))
    daten = baue_daten(d["sessions"], d["aktuelle_legislatur"])
    out = (HTML.replace("__CSS__", CSS)
               .replace("__JS__", JS.replace("__DATA__", json.dumps(daten, ensure_ascii=False))))
    ziel = OUTPUT / "matching-prototyp.html"
    ziel.write_text(out, encoding="utf-8")
    print(f"{ziel.name}: {len(daten['fragen'])} Fragen, "
          f"{len(daten['mitglieder'])} Mitglieder, {len(out)} Zeichen.")


if __name__ == "__main__":
    main()

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent    # Projektwurzel (scripts/ liegt darunter)
DATA = ROOT / "data"
OUTPUT = ROOT / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

data = json.load(open(DATA / 'all_sessions.json'))
data_str = json.dumps(data, ensure_ascii=False)

def _lade(name, standard):
    """Zusatzdaten, die nicht in jedem Projektstand vorliegen müssen."""
    pfad = DATA / name
    if not pfad.exists():
        print(f"     Hinweis: {name} fehlt, entsprechender Teil bleibt leer.")
        return standard
    return json.load(open(pfad, encoding="utf-8"))

mitglieder = _lade("mitglieder.json", {"mitglieder": [], "stand": None})
netz = _lade("interessen_netz.json", {"knoten": [], "kanten": []})
pruefung = _lade("interessen_pruefung.json", {"eindeutig": [], "moeglich": [], "nicht_gefunden": []})
mitglieder_str = json.dumps(mitglieder, ensure_ascii=False)
netz_str = json.dumps(netz, ensure_ascii=False)
pruefung_str = json.dumps(pruefung, ensure_ascii=False)

CSS = '''
:root{
  --ink:#1a1a1a; --paper:#faf9f6; --line:#e2ddd3; --muted:#6b6459;
  --svp:#3a7d3a; --sp:#c1272d; --glp:#e0a800; --fdp:#2b5c8a; --accent:#8a1a1a;
}
*{box-sizing:border-box;margin:0;padding:0}
html{-webkit-text-size-adjust:100%}
body{font-family:"Source Sans 3",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  background:var(--paper); color:var(--ink); line-height:1.5; font-size:16px}
.wrap{max-width:1100px; margin:0 auto; padding:0 20px}
header.masthead{border-bottom:3px solid var(--ink); padding:32px 0 20px}
.masthead .eyebrow{font-size:12px; letter-spacing:.18em; text-transform:uppercase; color:var(--muted); font-weight:600; margin-bottom:8px}
.masthead h1{font-family:Georgia,"Times New Roman",serif; font-weight:700; font-size:clamp(26px,4.5vw,40px); line-height:1.05; letter-spacing:-.01em}
.masthead .sub{margin-top:10px; color:var(--muted); font-size:15px; max-width:60ch}
.sess-bar{display:flex; gap:8px; align-items:center; margin:0 0 26px; flex-wrap:wrap}
.sess-bar label{font-size:12px; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); font-weight:600}
.sess-bar select{font:inherit; font-size:15px; padding:8px 14px; border:1px solid var(--line); border-radius:3px; background:#fff; color:var(--ink); font-weight:600; max-width:100%}
#sessSelWrap{display:inline-flex; gap:8px; align-items:center}
.modus-schalter{display:inline-flex; align-items:center; gap:8px; cursor:pointer; padding:7px 13px;
  border:1px solid var(--line); border-radius:99px; background:#fff; text-transform:none;
  letter-spacing:0; font-size:13.5px; font-weight:600; color:var(--muted); margin-right:6px}
.modus-schalter:hover{border-color:var(--accent); color:var(--accent)}
.modus-schalter input{accent-color:var(--accent); width:15px; height:15px; cursor:pointer}
.modus-schalter.an{background:var(--ink); border-color:var(--ink); color:#fff}
@media(max-width:720px){
  .sess-bar{display:grid; grid-template-columns:1fr; gap:3px}
  .sess-bar select{width:100%}
  .sess-bar label{margin-top:6px}
  .modus-schalter{margin:0 0 6px; justify-content:center}
  #sessSelWrap{display:grid; grid-template-columns:1fr; gap:3px}
}
nav.tabs{display:flex; gap:0; border-bottom:1px solid var(--line); margin:22px 0 22px; flex-wrap:wrap}
nav.tabs button{background:none; border:none; cursor:pointer; font:inherit; padding:12px 16px; font-size:14px; font-weight:600; color:var(--muted); border-bottom:3px solid transparent; margin-bottom:-1px; white-space:nowrap}
nav.tabs button:hover{color:var(--ink)}
nav.tabs button.active{color:var(--ink); border-bottom-color:var(--accent)}
/* Dropdown-Navigation (mobil) */
.nav-select-wrap{display:none; margin:22px 0 26px; position:relative}
.nav-select-wrap::after{content:"▾"; position:absolute; right:18px; top:50%; transform:translateY(-50%); pointer-events:none; color:var(--muted); font-size:14px}
.nav-select{width:100%; font:inherit; font-size:16px; font-weight:600; color:var(--ink); background:#fff; border:1px solid var(--line); border-radius:6px; padding:14px 40px 14px 16px; appearance:none; -webkit-appearance:none; cursor:pointer}
.nav-select:focus{outline:none; border-color:var(--accent)}
/* Umschalten: schmale Screens Dropdown, breite Tab-Leiste */
@media(max-width:720px){
  nav.tabs{display:none}
  .nav-select-wrap{display:block}
}
.panel{display:none; animation:fade .3s ease}
.panel.active{display:block}
@keyframes fade{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
h2.section{font-family:Georgia,serif; font-size:22px; font-weight:700; margin:8px 0 4px}
.section-note{color:var(--muted); font-size:14px; margin-bottom:22px; max-width:70ch}
.vote-card{border:1px solid var(--line); border-left:4px solid var(--ink); background:#fff; padding:18px 20px; margin-bottom:14px; border-radius:2px}
.vote-card .vhead{display:flex; justify-content:space-between; gap:16px; align-items:baseline; flex-wrap:wrap}
.vote-card .vnr{font-size:12px; letter-spacing:.1em; text-transform:uppercase; color:var(--accent); font-weight:700}
.vote-card .vtype{font-size:11px; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); background:var(--paper); padding:3px 8px; border:1px solid var(--line); border-radius:99px}
.vote-card h3{font-size:17px; margin:4px 0 6px; font-weight:600}
.vote-card .vdet{font-size:13.5px; color:var(--muted); margin-bottom:12px}
.vote-card .vgesch{font-size:12px; color:var(--muted); font-style:italic; margin-bottom:12px; padding-left:10px; border-left:2px solid var(--line)}
.tally{display:flex; height:26px; border-radius:3px; overflow:hidden; border:1px solid var(--line); font-size:12px; font-weight:700}
.tally span{display:flex; align-items:center; justify-content:center; color:#fff; min-width:22px}
.tally .ja{background:var(--svp)} .tally .nein{background:var(--sp)} .tally .enth{background:#b0a89a} .tally .van{background:#d8d2c6; color:var(--muted)}
.tally-legend{display:flex; gap:16px; margin-top:8px; font-size:12px; color:var(--muted); flex-wrap:wrap}
.tally-legend b{color:var(--ink)}
.invnote{margin-top:10px; font-size:12px; background:#fff8e6; border:1px solid #e8d9a0; padding:6px 10px; border-radius:3px; color:#7a5c00}
.frak-grid{display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:16px}
.frak-card{border:1px solid var(--line); background:#fff; padding:18px; border-radius:3px; border-top:4px solid var(--ink)}
.frak-card h3{font-size:16px; margin-bottom:2px}
.frak-card .fseats{font-size:13px; color:var(--muted); margin-bottom:14px}
.stat-row{display:flex; justify-content:space-between; font-size:13px; padding:6px 0; border-bottom:1px solid var(--paper)}
.stat-row b{font-variant-numeric:tabular-nums}
.disc-bar{height:6px; background:var(--line); border-radius:99px; margin-top:4px; overflow:hidden}
.disc-bar i{display:block; height:100%; border-radius:99px}
.filter-bar{display:flex; gap:10px; flex-wrap:wrap; margin-bottom:16px; align-items:center}
.filter-bar select,.filter-bar input{font:inherit; font-size:14px; padding:8px 12px; border:1px solid var(--line); border-radius:3px; background:#fff; color:var(--ink)}
.member-table{width:100%; border-collapse:collapse; font-size:14px; background:#fff; border:1px solid var(--line)}
.member-table th{text-align:left; padding:10px 12px; border-bottom:2px solid var(--ink); font-size:12px; letter-spacing:.05em; text-transform:uppercase; color:var(--muted); cursor:pointer; user-select:none}
.member-table th:hover{color:var(--ink)}
.member-table td{padding:9px 12px; border-bottom:1px solid var(--paper)}
.member-table tr:hover td{background:#fbfaf7}
.pill{display:inline-block; width:10px; height:10px; border-radius:99px; margin-right:6px; vertical-align:middle}
.vote-dots{display:flex; gap:3px; flex-wrap:wrap}
.vote-dots i,.vote-dots a{width:14px; height:14px; border-radius:2px; display:inline-block}
.vd-ja{background:var(--svp)} .vd-nein{background:var(--sp)} .vd-enth{background:#b0a89a} .vd-van{background:#e2ddd3}
.legend-dots{display:flex; gap:16px; font-size:12px; color:var(--muted); margin:14px 0; flex-wrap:wrap}
.legend-dots span{display:flex; align-items:center; gap:5px}
.legend-dots i{width:12px;height:12px;border-radius:2px;display:inline-block}
.spider-wrap{display:flex; gap:30px; flex-wrap:wrap; align-items:flex-start}
.spider-wrap svg{overflow:visible}
.spider-controls{flex:1; min-width:240px}
.frak-toggle{display:flex; align-items:center; gap:8px; padding:8px 10px; border:1px solid var(--line); border-radius:3px; margin-bottom:8px; cursor:pointer; font-size:14px; background:#fff}
.frak-toggle input{accent-color:var(--accent)}
.frak-toggle .swatch{width:14px;height:14px;border-radius:3px}
.axis-caption{font-size:12px; color:var(--muted); margin-top:16px; max-width:40ch; line-height:1.5}
.disclaimer{background:#fff8e6; border:1px solid #e8d9a0; padding:12px 16px; border-radius:3px; font-size:13px; color:#6b5518; margin:0 0 20px}
/* Ranglisten */
.rank-intro{display:flex; gap:10px; flex-wrap:wrap; margin-bottom:20px}
.rank-scope{font:inherit; font-size:14px; padding:8px 12px; border:1px solid var(--line); border-radius:3px; background:#fff; font-weight:600}
.rank-grid{display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:20px}
.rank-box{border:1px solid var(--line); background:#fff; border-radius:3px; overflow:hidden}
.rank-box h3{font-size:14px; padding:14px 16px; border-bottom:2px solid var(--ink); display:flex; align-items:center; gap:8px}
.rank-box h3 .ico{width:22px;height:22px;border-radius:5px;display:inline-flex;align-items:center;justify-content:center;color:#fff;font-size:13px;font-weight:700}
.rank-list{list-style:none}
.rank-list li{display:flex; align-items:center; gap:10px; padding:9px 16px; border-bottom:1px solid var(--paper); font-size:14px}
.rank-list li:last-child{border:none}
.rank-num{width:22px; font-weight:700; color:var(--muted); font-variant-numeric:tabular-nums; text-align:right}
.rank-name{flex:1}
.rank-name small{color:var(--muted); font-weight:400}
.rank-val{font-weight:700; font-variant-numeric:tabular-nums; text-align:right; white-space:nowrap}
.rank-val small{display:block; font-weight:400; color:var(--muted); font-size:11.5px; margin-top:1px}
.rank-bar{height:5px;border-radius:99px;background:var(--line);margin-top:3px;overflow:hidden;max-width:120px}
.rank-bar i{display:block;height:100%;border-radius:99px}
.rank-cell{display:flex;flex-direction:column;flex:1;min-width:0}
.top1{color:var(--accent)}
footer.foot{border-top:1px solid var(--line); margin-top:50px; padding:24px 0 40px; font-size:12.5px; color:var(--muted); line-height:1.6}
footer.foot b{color:var(--ink)}
/* Überblick */
.ub-hero{margin-bottom:26px}
.ub-h2{font-family:Georgia,serif; font-size:clamp(22px,3.5vw,30px); font-weight:700; line-height:1.1; margin-bottom:10px}
.ub-lead{font-size:16px; color:var(--muted); max-width:64ch; line-height:1.55}
.ub-big{display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr)); gap:14px; margin-bottom:38px}
.ub-bignum{background:#fff; border:1px solid var(--line); border-top:4px solid var(--accent); border-radius:3px; padding:22px 16px; text-align:center}
.ub-bignum .n{font-size:38px; font-weight:700; font-variant-numeric:tabular-nums; line-height:1; color:var(--ink)}
.ub-bignum .l{font-size:13px; color:var(--muted); margin-top:8px; letter-spacing:.03em}
.ub-sec{font-family:Georgia,serif; font-size:20px; font-weight:700; margin:8px 0 4px}
.ub-secnote{font-size:14px; color:var(--muted); margin-bottom:18px; max-width:66ch}
.ub-teasers{display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:16px; margin-bottom:40px}
.ub-teaser{background:#fff; border:1px solid var(--line); border-radius:3px; padding:18px; transition:box-shadow .15s, transform .15s}
.ub-teaser:hover{box-shadow:0 4px 16px rgba(0,0,0,.07); transform:translateY(-2px)}
.ub-thead{display:flex; align-items:center; gap:9px; font-size:15px; font-weight:700; margin-bottom:4px}
.ub-tico{width:24px;height:24px;border-radius:6px;display:inline-flex;align-items:center;justify-content:center;color:#fff;font-size:13px;font-weight:700;flex:0 0 auto}
.ub-texpl{font-size:12.5px; color:var(--muted); margin-bottom:12px; line-height:1.4; min-height:34px}
.ub-tlist{list-style:none; margin-bottom:12px}
.ub-tlist li{display:flex; align-items:center; gap:8px; padding:6px 0; border-bottom:1px solid var(--paper); font-size:14px}
.ub-tlist li:last-child{border:none}
.ub-rank{width:16px; font-weight:700; color:var(--muted); font-variant-numeric:tabular-nums}
.ub-dot{width:9px;height:9px;border-radius:99px;flex:0 0 auto}
.ub-tname{flex:1; min-width:0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis}
.ub-tval{font-weight:700; font-variant-numeric:tabular-nums; font-size:13px; text-align:right; white-space:nowrap}
.ub-tval small{display:block; font-weight:400; color:var(--muted); font-size:11px}
.ub-more{font-size:13px; color:var(--accent); font-weight:600}
.ub-nav{display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:14px}
.ub-navcard{background:var(--paper); border:1px solid var(--line); border-left:4px solid var(--ink); border-radius:3px; padding:16px 18px; transition:background .15s}
.ub-navcard:hover{background:#fff}
.ub-navcard b{display:block; font-size:15px; margin-bottom:4px}
.ub-navcard span{font-size:13px; color:var(--muted); line-height:1.4}
/* Themen-Tab */
.themen-chips{display:flex; flex-wrap:wrap; gap:8px; margin-bottom:24px}
.themen-chip{background:#fff; border:1px solid var(--line); border-radius:99px; padding:8px 14px; font:inherit; font-size:13.5px; cursor:pointer; color:var(--ink); display:flex; align-items:center; gap:7px; transition:all .12s}
.themen-chip:hover{border-color:var(--muted)}
.themen-chip.active{background:var(--ink); color:#fff; border-color:var(--ink)}
.tc-count{font-size:11px; background:var(--paper); color:var(--muted); border-radius:99px; padding:1px 7px; font-variant-numeric:tabular-nums}
.themen-chip.active .tc-count{background:rgba(255,255,255,.2); color:#fff}
.themen-head{margin-bottom:18px}
.themen-h3{font-family:Georgia,serif; font-size:22px; font-weight:700}
.themen-sub{font-size:13px; color:var(--muted); margin-top:2px}
.themen-sec{font-family:Georgia,serif; font-size:17px; font-weight:700; margin:26px 0 12px; padding-bottom:6px; border-bottom:1px solid var(--line)}
.themen-parteien{display:flex; flex-direction:column; gap:9px; margin-bottom:8px}
.tp-row{display:flex; align-items:center; gap:12px}
.tp-name{flex:0 0 150px; font-size:13px; font-weight:600; border-left:3px solid; padding-left:9px; line-height:1.2}
.tp-name small{color:var(--muted); font-weight:400; font-size:11px}
.tp-bar{flex:1; display:flex; height:16px; border-radius:3px; overflow:hidden; background:#eee9df}
.tp-bar span{display:block;height:100%}
.tp-val{flex:0 0 auto; font-size:12px; color:var(--muted); font-variant-numeric:tabular-nums; width:88px; text-align:right}
.themen-votes{display:flex; flex-direction:column}
.tv-row{display:flex; justify-content:space-between; gap:14px; padding:11px 4px; border-bottom:1px solid var(--paper); align-items:flex-start}
.tv-titel{font-size:14px; font-weight:600; line-height:1.3}
.tv-meta{font-size:12px; color:var(--muted); margin-top:2px}
.tv-tally{flex:0 0 auto; font-size:12px; color:var(--muted); text-align:right; white-space:nowrap; font-variant-numeric:tabular-nums}
@media(max-width:600px){.tp-name{flex-basis:100px} .tv-tally{display:none}}
/* Themen im Mitglied-Detail */
.m-themen-titel{font-family:Georgia,serif; font-size:18px; font-weight:700; margin:8px 0 4px}
.m-themen-note{font-size:12.5px; color:var(--muted); margin-bottom:16px; max-width:66ch; line-height:1.45}
.m-themen{display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:14px; margin-bottom:28px}
.m-thema{background:#fff; border:1px solid var(--line); border-radius:3px; padding:13px 15px}
.m-thema-head{display:flex; justify-content:space-between; align-items:baseline; margin-bottom:8px; gap:8px}
.m-thema-name{font-size:13.5px; font-weight:600; line-height:1.25}
.m-thema-count{font-size:11px; color:var(--muted); white-space:nowrap; font-variant-numeric:tabular-nums}
.m-thema-bar{display:flex; height:12px; border-radius:3px; overflow:hidden; background:#eee9df; margin-bottom:7px}
.m-thema-bar span{display:block; height:100%}
.mt-ja{background:var(--svp)} .mt-nein{background:var(--sp)} .mt-enth{background:#9a8f7d}
.m-thema-legend{font-size:11.5px; color:var(--muted); font-variant-numeric:tabular-nums}
/* Themen im Mitglied-Detail Ende */
/* Mitglied im Detail */
.m-head{display:flex; align-items:center; gap:14px; padding:18px 20px; background:#fff; border:1px solid var(--line); border-left:5px solid var(--ink); border-radius:3px; margin-bottom:18px; flex-wrap:wrap}
.m-head .m-name{font-family:Georgia,serif; font-size:22px; font-weight:700}
.m-head .m-frak{font-size:13px; color:var(--muted)}
.m-stats{display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); gap:12px; margin-bottom:24px}
.m-stat{background:#fff; border:1px solid var(--line); border-radius:3px; padding:14px 16px; text-align:center}
.m-stat .num{font-size:26px; font-weight:700; font-variant-numeric:tabular-nums; line-height:1}
.m-stat .lbl{font-size:12px; color:var(--muted); margin-top:6px; letter-spacing:.03em}
.m-stat .sub{font-size:11px; color:var(--muted); margin-top:2px}
.m-stat.ja .num{color:var(--svp)} .m-stat.nein .num{color:var(--sp)}
.m-stat.enth .num{color:#9a8f7d} .m-stat.van .num{color:#b0a89a}
.m-sess-group{margin-bottom:20px}
.m-sess-title{font-size:13px; font-weight:700; color:var(--ink); padding:8px 0 8px; border-bottom:2px solid var(--ink); margin-bottom:2px; display:flex; justify-content:space-between; align-items:baseline}
.m-sess-title small{font-weight:400; color:var(--muted)}
.m-vote{display:flex; align-items:flex-start; gap:12px; padding:11px 4px; border-bottom:1px solid var(--paper)}
.m-vote-badge{flex:0 0 auto; width:64px; text-align:center; font-size:11px; font-weight:700; letter-spacing:.04em; text-transform:uppercase; padding:5px 0; border-radius:3px; color:#fff}
.mb-ja{background:var(--svp)} .mb-nein{background:var(--sp)} .mb-enth{background:#9a8f7d} .mb-van{background:#d0c8ba; color:var(--muted)}
.m-vote-body{flex:1; min-width:0}
.m-vote-body .mv-titel{font-size:14px; font-weight:600; line-height:1.35}
.m-vote-body .mv-gesch{font-size:12px; color:var(--muted); margin-top:2px; font-style:italic}
.mv-link{color:var(--ink); text-decoration:none; border-bottom:1px solid var(--line)}
.mv-link:hover{color:var(--accent); border-bottom-color:var(--accent)}
.m-sess-link{color:var(--ink); text-decoration:none; border-bottom:2px solid transparent}
.m-sess-link:hover{color:var(--accent)}
.m-vote-body .mv-meta{font-size:12px; color:var(--muted); margin-top:2px}
.m-vote-body .mv-inv{font-size:11px; color:#7a5c00; background:#fff8e6; border:1px solid #e8d9a0; padding:2px 7px; border-radius:3px; display:inline-block; margin-top:4px}
.m-vote-result{flex:0 0 auto; font-size:11px; color:var(--muted); text-align:right; padding-top:3px; font-variant-numeric:tabular-nums}
@media(max-width:600px){.m-vote-result{display:none}}
@media(max-width:600px){.member-table .hide-sm{display:none} body{font-size:15px}}
/* Untermenü in der Tab-Leiste (Kantonsratssitzungen) */
.tabs-dd{position:relative; display:inline-flex}
.tabs-dd>button{display:inline-flex; align-items:center; gap:7px}
.tabs-dd>button .caret{font-size:10px; color:var(--muted); transition:transform .15s}
.tabs-dd.open>button .caret{transform:rotate(180deg)}
.dd-menu{position:absolute; top:100%; left:0; min-width:230px; background:#fff; border:1px solid var(--line);
  border-radius:4px; box-shadow:0 8px 24px rgba(0,0,0,.11); padding:6px; z-index:40; display:none}
.tabs-dd.open .dd-menu{display:block}
.dd-menu button{display:block; width:100%; text-align:left; padding:10px 12px; font-size:14px; font-weight:600;
  color:var(--muted); border:none; background:none; cursor:pointer; border-radius:3px; margin:0; white-space:nowrap}
.dd-menu button:hover{background:var(--paper); color:var(--ink)}
.dd-menu button.active{color:var(--accent); background:var(--paper)}
.dd-menu small{display:block; font-weight:400; font-size:11.5px; color:var(--muted); margin-top:2px}
/* Namensliste je Abstimmung */
.vn-toggle{margin-top:13px; background:none; border:1px solid var(--line); border-radius:3px; font:inherit;
  font-size:13px; font-weight:600; color:var(--ink); padding:7px 13px; cursor:pointer; display:inline-flex; align-items:center; gap:8px}
.vn-toggle:hover{border-color:var(--accent); color:var(--accent)}
.vn-toggle .caret{font-size:10px; color:var(--muted); transition:transform .15s}
.vn-toggle[aria-expanded="true"] .caret{transform:rotate(180deg)}
.vn-box{display:none; margin-top:15px; border-top:1px solid var(--line); padding-top:15px}
.vn-box.open{display:block}
/* Präsent ist die längste Spalte und bekommt darum mehr Breite (dort zweispaltig) */
.vn-cols{display:grid; grid-template-columns:1fr 1fr .75fr 1.65fr; gap:18px}
@media(max-width:860px){.vn-cols{grid-template-columns:repeat(2,1fr)}}
@media(max-width:470px){.vn-cols{grid-template-columns:1fr}}
.vn-col h4{font-size:11.5px; letter-spacing:.07em; text-transform:uppercase; font-weight:700; padding-bottom:6px;
  border-bottom:2px solid; margin-bottom:8px; display:flex; justify-content:space-between; align-items:baseline; gap:8px}
.vn-col h4 span{font-variant-numeric:tabular-nums; font-size:13px}
.vn-col.c-ja h4{color:var(--svp); border-color:var(--svp)}
.vn-col.c-nein h4{color:var(--sp); border-color:var(--sp)}
.vn-col.c-enth h4{color:#8a8070; border-color:#b0a89a}
.vn-col.c-pres h4{color:var(--muted); border-color:var(--line)}
.vn-list{list-style:none; display:flex; flex-direction:column; gap:1px}
.vn-list li{font-size:13px; line-height:1.35}
/* Die Präsent-Spalte ist die längste: zweispaltig, damit die Karte nicht ausufert */
.vn-col.c-pres .vn-list{display:block; columns:2; column-gap:14px}
.vn-col.c-pres .vn-list li{break-inside:avoid}
@media(max-width:860px){.vn-col.c-pres .vn-list{columns:1}}
.vn-name{display:flex; align-items:center; gap:7px; color:var(--ink); text-decoration:none; padding:2px 5px;
  border-radius:3px; cursor:pointer}
.vn-name:hover{background:var(--paper); color:var(--accent)}
.vn-dot{flex:0 0 auto; width:9px; height:9px; border-radius:99px}
.vn-empty{font-size:13px; color:var(--muted); font-style:italic; padding:2px 5px}
.vn-abw{margin-top:18px; border-top:1px dashed var(--line); padding-top:13px}
.vn-abw h4{font-size:11.5px; letter-spacing:.07em; text-transform:uppercase; font-weight:700; color:var(--muted); margin-bottom:9px}
.vn-inline{display:flex; flex-wrap:wrap; gap:2px 18px}
.vn-inline .vn-name{padding:2px 4px}
.vn-hint{font-size:11.5px; color:var(--muted); margin-top:12px}
/* Abstimmungskarte hervorheben, wenn aus der Mitgliedertabelle angesprungen */
.vote-card.flash{border-left-color:var(--accent); box-shadow:0 0 0 3px rgba(138,26,26,.13)}
/* Stimmpunkte in der Mitgliedertabelle: anklickbar mit Tooltip */
.vote-dots a{display:inline-block; cursor:pointer; border-radius:2px}
.vote-dots a:hover{outline:2px solid var(--ink); outline-offset:1px}
.vd-tip{position:fixed; z-index:60; max-width:330px; background:var(--ink); color:#fff; font-size:12.5px;
  line-height:1.42; padding:10px 13px; border-radius:4px; box-shadow:0 10px 28px rgba(0,0,0,.24); pointer-events:none; display:none}
.vd-tip b.tip-nr{display:block; font-size:10.5px; letter-spacing:.09em; text-transform:uppercase; color:#cfc7b8; margin-bottom:4px; font-weight:700}
.vd-tip .tip-res{margin-top:6px; padding-top:6px; border-top:1px solid #4a463f; color:#cfc7b8; font-size:11.5px}
.vd-tip .tip-eig{font-weight:700; color:#fff}
/* Filterleiste im Reiter Abstimmungen */
.vfilter{background:#fff; border:1px solid var(--line); border-radius:4px; padding:16px 18px; margin-bottom:22px}
.vfilter-row{display:flex; gap:10px; flex-wrap:wrap; align-items:center; margin-bottom:12px}
.vfilter-row:last-child{margin-bottom:0}
.vfilter label{font-size:11.5px; letter-spacing:.07em; text-transform:uppercase; color:var(--muted); font-weight:700; flex:0 0 auto}
.vfilter input[type=text]{flex:1; min-width:220px; font:inherit; font-size:15px; padding:9px 13px;
  border:1px solid var(--line); border-radius:3px; background:var(--paper); color:var(--ink)}
.vfilter input[type=text]:focus{outline:none; border-color:var(--accent); background:#fff}
.vfilter select{font:inherit; font-size:14px; padding:8px 12px; border:1px solid var(--line);
  border-radius:3px; background:#fff; color:var(--ink); font-weight:600}
.vf-reset{font:inherit; font-size:13px; padding:8px 13px; border:1px solid var(--line); background:none;
  border-radius:3px; cursor:pointer; color:var(--muted)}
.vf-reset:hover{border-color:var(--accent); color:var(--accent)}
.vf-treffer{font-size:13px; color:var(--muted); margin-left:auto}
.vf-treffer b{color:var(--ink)}
/* Tag-Ebenen */
.tagzeile{display:flex; gap:7px; flex-wrap:wrap; align-items:center}
.tagzeile.ebene2{padding-left:14px; border-left:2px solid var(--line)}
.tagzeile.ebene3{padding-left:28px; border-left:2px solid var(--line)}
.tagchip{font:inherit; font-size:12.5px; padding:5px 11px; border:1px solid var(--line); background:var(--paper);
  border-radius:99px; cursor:pointer; color:var(--ink); display:inline-flex; align-items:center; gap:6px}
.tagchip:hover{border-color:var(--accent); color:var(--accent)}
.tagchip small{color:var(--muted); font-variant-numeric:tabular-nums; font-size:11px}
.tagchip.aktiv{background:var(--ink); color:#fff; border-color:var(--ink)}
.tagchip.aktiv small{color:#cfc7b8}
.tagchip.ebene2.aktiv{background:var(--accent); border-color:var(--accent)}
.tagchip.ebene3.aktiv{background:var(--svp); border-color:var(--svp)}
.tag-hinweis{font-size:12px; color:var(--muted); font-style:italic}
/* Sitzungsüberschrift, wenn über mehrere Sitzungen gesucht wird */
.v-sessgroup{font-family:Georgia,serif; font-size:17px; font-weight:700; margin:26px 0 10px;
  padding-bottom:6px; border-bottom:2px solid var(--ink)}
.v-sessgroup:first-child{margin-top:0}
.v-sessgroup small{font-family:inherit; font-weight:400; font-size:13px; color:var(--muted); margin-left:8px}
.v-leer{padding:26px; text-align:center; color:var(--muted); background:#fff; border:1px solid var(--line); border-radius:3px}
/* Tags auf der Abstimmungskarte */
.v-tags{display:flex; gap:6px; flex-wrap:wrap; margin-top:10px}
.v-tag{font-size:11px; padding:3px 9px; border-radius:99px; background:var(--paper); border:1px solid var(--line); color:var(--muted)}
.v-tag.form{background:#efece4; color:var(--ink); font-weight:600}
.v-tag.detail{cursor:pointer}
.v-tag.detail:hover{border-color:var(--accent); color:var(--accent)}
.v-kontext{font-size:12.5px; color:var(--muted); margin-top:10px; padding-left:10px; border-left:2px solid var(--line)}
.v-kontext b{color:var(--ink); font-weight:600}
.v-stich{font-size:11.5px; color:var(--muted); margin-top:7px}
.v-stich b{color:var(--ink); font-weight:600; letter-spacing:.04em; text-transform:uppercase; font-size:10.5px}
mark{background:#fff2a8; color:inherit; padding:0 2px; border-radius:2px}
/* Porträt und Interessenbindungen im Mitglied-Detail */
.m-portrait{width:82px; height:82px; border-radius:4px; object-fit:cover; flex:0 0 auto; border:1px solid var(--line)}
.m-portrait.leer{display:flex; align-items:center; justify-content:center; background:var(--paper);
  color:var(--muted); font-family:Georgia,serif; font-size:26px; font-weight:700}
.m-stamm{font-size:12.5px; color:var(--muted); margin-top:3px}
.m-int{background:#fff; border:1px solid var(--line); border-radius:3px; padding:16px 18px; margin-bottom:20px}
.m-int.leer{font-size:13px; color:var(--muted)}
.m-int-titel{font-family:Georgia,serif; font-size:17px; font-weight:700; margin-bottom:10px}
.m-int-titel small{font-family:inherit; font-weight:400; font-size:12.5px; color:var(--muted); margin-left:8px}
.m-int-liste{list-style:none; display:flex; flex-direction:column; gap:7px}
.m-int-liste li{display:flex; align-items:baseline; gap:9px; font-size:13.5px; flex-wrap:wrap}
.m-int-branche{flex:0 0 auto; font-size:11px; padding:2px 9px; border-radius:99px;
  background:var(--paper); border:1px solid var(--line); color:var(--muted); cursor:pointer}
.m-int-branche:hover{border-color:var(--accent); color:var(--accent)}
.m-int-org{font-weight:600}
.m-int-liste small{color:var(--muted)}
.m-int-fuss{font-size:11.5px; color:var(--muted); margin-top:12px; font-style:italic}
/* Netz der Interessenbindungen */
.netz-leiste{display:flex; gap:10px; flex-wrap:wrap; align-items:center; margin-bottom:16px}
.netz-leiste select,.netz-leiste input{font:inherit; font-size:14px; padding:8px 12px;
  border:1px solid var(--line); border-radius:3px; background:#fff; color:var(--ink)}
.netz-leiste input{min-width:210px}
.netz-wrap{position:relative; background:#fff; border:1px solid var(--line); border-radius:4px; overflow:hidden}
#netz{display:block; width:100%; height:820px; cursor:grab}
#netz:active{cursor:grabbing}
.netz-info{position:absolute; right:14px; top:14px; width:290px; max-height:560px; overflow:auto;
  background:rgba(255,255,255,.97); border:1px solid var(--line); border-radius:4px; padding:14px 16px;
  font-size:13px; box-shadow:0 6px 20px rgba(0,0,0,.08)}
.netz-info h4{font-family:Georgia,serif; font-size:16px; margin-bottom:4px}
.netz-info .ni-typ{font-size:11px; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); font-weight:700}
.netz-info ul{list-style:none; margin-top:9px; display:flex; flex-direction:column; gap:5px}
.netz-info li{font-size:12.5px; line-height:1.35}
.netz-info small{color:var(--muted)}
.netz-legende{display:flex; gap:14px; flex-wrap:wrap; margin-top:12px; font-size:12px; color:var(--muted)}
.netz-legende span{display:inline-flex; align-items:center; gap:6px}
.netz-legende i{width:11px; height:11px; border-radius:99px; display:inline-block}
.ni-hreg{font-size:12px; line-height:1.4; margin:9px 0; padding:8px 10px; border-radius:3px;
  background:var(--paper); border-left:3px solid var(--line)}
.ni-hreg.eindeutig{border-left-color:var(--svp)}
.ni-hreg.moeglich{border-left-color:var(--glp)}
.ni-hreg.offen{border-left-color:#b0a89a}
.ni-hreg b{display:block; font-size:10.5px; letter-spacing:.08em; text-transform:uppercase; color:var(--muted)}
.ni-hreg small{display:block; color:var(--muted); font-size:11px; margin-top:4px}
.netz-zoom{display:inline-flex; gap:0; border:1px solid var(--line); border-radius:3px; overflow:hidden; background:#fff}
.netz-zoom button{font:inherit; font-size:13px; padding:8px 12px; border:none; background:none; cursor:pointer; color:var(--ink)}
.netz-zoom button:hover{background:var(--paper); color:var(--accent)}
.netz-zoom button+button{border-left:1px solid var(--line)}
.netz-regler{display:flex; gap:18px; flex-wrap:wrap; align-items:center; margin-bottom:16px;
  background:var(--paper); border:1px solid var(--line); border-radius:4px; padding:12px 16px}
.netz-regler label{display:inline-flex; align-items:center; gap:8px; font-size:12.5px; color:var(--muted); font-weight:600}
.netz-regler input[type=range]{width:120px; accent-color:var(--accent); cursor:pointer}
.netz-regler output{font-size:12px; color:var(--ink); font-variant-numeric:tabular-nums; min-width:56px}
@media(max-width:720px){ .netz-regler label{width:100%} .netz-regler input[type=range]{flex:1} }
@media(max-width:720px){ #netz{height:560px} .netz-info{position:static; width:auto; margin:12px} }
'''

JS = r'''
const DATA = __DATA__;
const PERSONEN = __MITGLIEDER__;
const NETZ = __NETZ__;
const HREG = __PRUEFUNG__;
// Fraktionen wechseln über die Legislaturen hinweg Namen und Zuschnitt,
// darum sind auch die früheren Bezeichnungen hinterlegt.
const FRAK_COLORS = {
  "SVP-EDU":"#3a7d3a",
  "SP-JUSO-GRÜNE-Junge Grüne":"#c1272d", "SP-JUSO":"#c1272d", "SP":"#c1272d",
  "GLP-EVP":"#e0a800",
  "FDP-Die Mitte":"#2b5c8a", "FDP-Die Mitte-JF":"#2b5c8a",
  "FDP-CVP":"#2b5c8a", "FDP-CVP-JF":"#2b5c8a",
  "AL-Grüne":"#7a9a2b", "AL-GRÜNE-Junge Grüne":"#7a9a2b", "AL-GRÜNE-JUNGE GRÜNE":"#7a9a2b",
  "GRÜNE-Junge Grüne":"#6aa832"
};
const FRAK_SHORT = {
  "SVP-EDU":"SVP-EDU",
  "SP-JUSO-GRÜNE-Junge Grüne":"SP-JUSO-GRÜNE", "SP-JUSO":"SP-JUSO", "SP":"SP",
  "GLP-EVP":"GLP-EVP",
  "FDP-Die Mitte":"FDP-Mitte", "FDP-Die Mitte-JF":"FDP-Mitte-JF",
  "FDP-CVP":"FDP-CVP", "FDP-CVP-JF":"FDP-CVP-JF",
  "AL-Grüne":"AL-Grüne", "AL-GRÜNE-Junge Grüne":"AL-GRÜNE", "AL-GRÜNE-JUNGE GRÜNE":"AL-GRÜNE",
  "GRÜNE-Junge Grüne":"GRÜNE"
};
const NV = v => v==="Ja"?"ja": v==="Nein"?"nein": (v==="Enth"||v==="Enthaltung")?"enth":"van";
// Parteifarben für die Namenspunkte. Fällt auf die Fraktionsfarbe zurück,
// wenn eine Partei hier (noch) nicht hinterlegt ist.
const PARTEI_COLORS = {
  "svp":"#3a7d3a", "jsvp":"#6ba85f", "svp senioren":"#588f52",
  "svp agro":"#4e8f46", "svp kmu":"#63a05a", "edu":"#8a6b2f",
  "parteilos":"#8a8070",
  "sp":"#c1272d", "juso":"#e2564f",
  "grüne":"#7ab648", "junge grüne":"#a3cc4a", "al":"#8e2f6e", "al-grüne":"#8e2f6e",
  "glp":"#c9c02f", "evp":"#e0a800",
  "fdp":"#2b5c8a", "jf":"#5b86ad", "jfdp":"#5b86ad",
  "die mitte":"#e08a1e", "cvp":"#e08a1e"
};
// Schreibweisen wechseln über die Jahre ("GRÜNE", "Grüne", "JUNGE GRÜNE"),
// darum wird kleingeschrieben nachgeschlagen.
const parteiColor = m =>
  PARTEI_COLORS[(m.partei||"").trim().toLowerCase()] || FRAK_COLORS[m.fraktion] || "#8a8070";
const esc = s => String(s==null?"":s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const memKey = m => m.nachname+"|"+m.vorname;
let curSession = 0;

/* ===== Auswahl: eine Sitzung oder über alle Sitzungen suchen =====
   Zwei Betriebsarten. Ohne Haken zeigt der Reiter eine einzelne Sitzung, der
   Wortfilter wirkt dann innerhalb dieser Sitzung. Mit Haken fällt die
   Sitzungswahl weg und gesucht wird über die gewählte Legislatur oder über
   alle Jahre. Ohne diese Trennung stünden 202 Sitzungen in einer Liste. */
let sessLegNr = DATA.aktuelle_legislatur;   // Zahl oder "alle"
let sucheModus = false;

const sessSel=document.getElementById("sessSel");
const sessLegSel=document.getElementById("sessLeg");
const modusBox=document.getElementById("modusSuche");

function sitzungenDerLeg(leg){
  const alle=DATA.sessions.map((s,i)=>({s,i}));
  return leg==="alle" ? alle : alle.filter(x=>x.s.legislatur===leg);
}
function fuelleLegislaturen(){
  sessLegSel.innerHTML="";
  const alle=document.createElement("option");
  alle.value="alle"; alle.textContent=`Alle Legislaturen · ${DATA.sessions.length} Sitzungen`;
  sessLegSel.appendChild(alle);
  Object.values(DATA.legislaturen).sort((a,b)=>b.nummer-a.nummer).forEach(L=>{
    const o=document.createElement("option");
    o.value=L.nummer;
    o.textContent=L.label+(L.nummer===DATA.aktuelle_legislatur?" (aktuell)":"")+` · ${L.n_sitzungen} Sitzungen`;
    sessLegSel.appendChild(o);
  });
  sessLegSel.value=String(sessLegNr);
  sessLegSel.onchange=()=>{
    sessLegNr = sessLegSel.value==="alle" ? "alle" : +sessLegSel.value;
    fuelleSitzungen();
    const liste=sitzungenDerLeg(sessLegNr);
    if(liste.length){ curSession=liste[0].i; sessSel.value=String(curSession); }
    renderSession();
  };
}
function fuelleSitzungen(){
  const liste=sitzungenDerLeg(sessLegNr);
  sessSel.innerHTML="";
  liste.forEach(({s,i})=>{
    const o=document.createElement("option"); o.value=i; o.textContent=s.sitzung; sessSel.appendChild(o);
  });
  if(!liste.some(x=>x.i===curSession) && liste.length) curSession=liste[0].i;
  sessSel.value=String(curSession);
  document.getElementById("sessSelWrap").style.display = sucheModus ? "none" : "inline-flex";
}
sessSel.onchange=()=>{ curSession=+sessSel.value; renderSession(); };

modusBox.onchange=()=>{
  sucheModus=modusBox.checked;
  document.getElementById("modusWrap").classList.toggle("an", sucheModus);
  // beim Umschalten auf Suche über alle Jahre voreinstellen
  if(sucheModus && sessLegNr!=="alle"){ /* gewählte Legislatur beibehalten */ }
  fuelleSitzungen();
  renderSession();
  const feld=document.getElementById("vSuche");
  if(sucheModus && feld) feld.focus();
};

/* Tabs */
// Reiter, die unter "Kantonsratssitzungen" hängen und die Sitzungsauswahl nutzen
const SESSION_TABS = ["votes","profile"];
function activateTab(tab){
  document.querySelectorAll("nav.tabs button").forEach(x=>x.classList.remove("active"));
  document.querySelectorAll(".panel").forEach(x=>x.classList.remove("active"));
  const btn=document.querySelector(`nav.tabs button[data-tab="${tab}"]`);
  if(btn) btn.classList.add("active");
  const panel=document.getElementById("tab-"+tab);
  if(panel) panel.classList.add("active");
  // Untermenü "Kantonsratssitzungen" mitführen
  const dd=document.getElementById("sessDd");
  if(dd){
    const drin=SESSION_TABS.includes(tab);
    dd.classList.remove("open");
    dd.querySelector("#sessDdBtn").classList.toggle("active", drin);
    dd.querySelector("#sessDdBtn").setAttribute("aria-expanded","false");
    const lbl=dd.querySelector("#sessDdLabel");
    if(lbl) lbl.textContent = drin
      ? "Kantonsratssitzungen: " + (tab==="votes"?"Abstimmungen":"Ratsmitglieder")
      : "Kantonsratssitzungen";
  }
  // Dropdown synchron halten
  const navSel=document.getElementById("navSelect");
  if(navSel && navSel.value!==tab) navSel.value=tab;
  if(tab==="fraktionen") renderFrakTab();
  if(tab==="interessen"){ netzMalen(); netzHeizen(0.4); }
  if(tab==="ueberblick") renderUeberblick();
  if(tab==="themen") renderThemen();
  document.getElementById("sessScope").style.display =
    SESSION_TABS.includes(tab) ? "flex" : "none";
  // nach oben scrollen, damit der neue Reiter von oben beginnt (mobil wichtig)
  window.scrollTo({top:0, behavior:"instant"});
}
document.querySelectorAll("nav.tabs button[data-tab]").forEach(b=>{
  b.onclick=()=>activateTab(b.dataset.tab);
});
// Untermenü auf-/zuklappen
const sessDdBtn=document.getElementById("sessDdBtn");
if(sessDdBtn){
  sessDdBtn.onclick=(e)=>{
    e.stopPropagation();
    const dd=document.getElementById("sessDd");
    const auf=dd.classList.toggle("open");
    sessDdBtn.setAttribute("aria-expanded", auf?"true":"false");
  };
  document.addEventListener("click", e=>{
    const dd=document.getElementById("sessDd");
    if(dd && !dd.contains(e.target)) dd.classList.remove("open");
  });
  document.addEventListener("keydown", e=>{
    if(e.key==="Escape") document.getElementById("sessDd").classList.remove("open");
  });
}
document.getElementById("navSelect").onchange=(e)=>activateTab(e.target.value);

function S(){ return DATA.sessions[curSession]; }
function fraktionen(s){ return [...new Set(s.members.map(m=>m.fraktion))]; }
function parteien(s){ return [...new Set(s.members.map(m=>m.partei))].filter(Boolean); }

/* ===== Abstimmungen ===== */
function tallyFor(s,idx){const t={ja:0,nein:0,enth:0,van:0};s.members.forEach(m=>t[NV(m.votes[idx])]++);return t;}

/* --- Namenslisten je Abstimmung ------------------------------------------
   Vier Spalten (Ja, Nein, Enthaltung, Präsent) plus eine Zeile mit den
   Abwesenden. Jeder Name ist ein Link auf "Mitglied im Detail". Der Punkt
   davor trägt die Parteifarbe. */
function memberSort(a,b){
  return (a.nachname+" "+a.vorname).localeCompare(b.nachname+" "+b.vorname,"de");
}
function nameItem(m){
  return `<li><a class="vn-name" data-member="${esc(memKey(m))}" title="${esc(m.partei||m.fraktion)}">`+
         `<span class="vn-dot" style="background:${parteiColor(m)}"></span>${esc(m.nachname)} ${esc(m.vorname)}</a></li>`;
}
function nameColumn(cls,label,list){
  const inner = list.length
    ? `<ul class="vn-list">${list.slice().sort(memberSort).map(nameItem).join("")}</ul>`
    : `<div class="vn-empty">niemand</div>`;
  return `<div class="vn-col ${cls}"><h4>${label}<span>${list.length}</span></h4>${inner}</div>`;
}
function namenBox(s,idx){
  const g={ja:[],nein:[],enth:[],van:[]};
  s.members.forEach(m=>g[NV(m.votes[idx])].push(m));
  const praesent=[...g.ja,...g.nein,...g.enth];
  const abw = g.van.length
    ? `<div class="vn-inline">${g.van.slice().sort(memberSort).map(m=>nameItem(m).replace(/^<li>|<\/li>$/g,"")).join("")}</div>`
    : `<div class="vn-empty">niemand, der Rat war vollzählig</div>`;
  return `<div class="vn-cols">
      ${nameColumn("c-ja","Ja",g.ja)}
      ${nameColumn("c-nein","Nein",g.nein)}
      ${nameColumn("c-enth","Enthaltung",g.enth)}
      ${nameColumn("c-pres","Präsent",praesent)}
    </div>
    <div class="vn-abw"><h4>Abwesend oder nicht teilgenommen · ${g.van.length}</h4>${abw}</div>
    <div class="vn-hint">Punkt = Partei. Klick auf einen Namen öffnet das Mitglied im Detail.</div>`;
}

/* --- Filterzustand ------------------------------------------------------- */
let vSuche = "";
let vForm  = "";
let tagOber = null, tagUnter = null, tagDetail = [];

function abstimmungenImScope(){
  /* Alle Abstimmungen der gewählten Sitzung bzw. der ganzen Legislatur,
     jeweils mit ihrer Sitzung und dem Spaltenindex. */
  const quellen = sucheModus ? sitzungenDerLeg(sessLegNr)
                             : [{s:DATA.sessions[curSession], i:curSession}];
  const out=[];
  quellen.forEach(({s,i})=>s.votes.forEach((v,vi)=>out.push({s, sIdx:i, v, vIdx:vi})));
  return out;
}

function suchtext(v){
  return [v.titel, v.details, v.geschaeft, v.typ, v.kontext,
          (v.stichworte||[]).join(" "), (v.tags_detail||[]).join(" "),
          (v.tags_unterthema||[]).join(" "), (v.tags_ueberthema||[]).join(" "),
          v.thema_name].filter(Boolean).join(" ").toLowerCase();
}

function passt(e){
  const v=e.v;
  if(vForm && !(v.tags_form||[]).includes(vForm)) return false;
  if(tagDetail.length){
    if(!tagDetail.some(t=>(v.tags_detail||[]).includes(t))) return false;
  } else if(tagUnter){
    if(!(v.tags_unterthema||[]).includes(tagUnter)) return false;
  } else if(tagOber){
    if(!(v.tags_ueberthema||[]).includes(tagOber)) return false;
  }
  if(vSuche){
    const txt=suchtext(v);
    // alle Suchwörter müssen vorkommen, Reihenfolge egal
    if(!vSuche.split(/\s+/).filter(Boolean).every(w=>txt.includes(w))) return false;
  }
  return true;
}

function hervorheben(text){
  if(!vSuche || !text) return esc(text);
  let out=esc(text);
  vSuche.split(/\s+/).filter(w=>w.length>2).forEach(w=>{
    out=out.replace(new RegExp("("+w.replace(/[.*+?^${}()|[\]\\]/g,"\\$&")+")","gi"),"<mark>$1</mark>");
  });
  return out;
}

function voteCard(e){
  const {s, sIdx, v, vIdx}=e;
  const t=tallyFor(s,vIdx);
  const seg=(n,cls,lbl)=> n>0?`<span class="${cls}" style="flex:${n}" title="${lbl}: ${n}">${n>2?n:""}</span>`:"";
  const card=document.createElement("div"); card.className="vote-card"; card.id=`vote-${sIdx}-${vIdx}`;
  card.style.borderLeftColor=t.ja>t.nein?"var(--svp)":(t.nein>t.ja?"var(--sp)":"var(--ink)");
  const titelText = v.titel||"(ohne Titel)";
  const titelHtml = s.url ? `<a class="mv-link" href="${s.url}" target="_blank" rel="noopener">${hervorheben(titelText)}</a>` : hervorheben(titelText);
  const tags = [...(v.tags_form||[]).map(x=>`<span class="v-tag form">${esc(x)}</span>`),
                ...(v.tags_detail||[]).map(x=>`<span class="v-tag detail" data-tag="${esc(x)}">${esc(x)}</span>`)].join("");
  const uid=`${sIdx}-${vIdx}`;
  card.innerHTML=`<div class="vhead"><span class="vnr">Abstimmung ${v.nr}</span>${v.typ?`<span class="vtype">${esc(v.typ)}</span>`:""}</div>
    <h3>${titelHtml}</h3>
    ${v.details?`<div class="vdet">${hervorheben(v.details)}</div>`:""}
    ${v.geschaeft?`<div class="vgesch">${hervorheben(v.geschaeft)}</div>`:""}
    <div class="tally">${seg(t.ja,"ja","Ja")}${seg(t.nein,"nein","Nein")}${seg(t.enth,"enth","Enthaltung")}${seg(t.van,"van","abwesend")}</div>
    <div class="tally-legend"><span><b>${t.ja}</b> Ja</span><span><b>${t.nein}</b> Nein</span><span><b>${t.enth}</b> Enthaltung</span><span><b>${t.van}</b> abwesend</span></div>
    ${v.inverted_note?`<div class="invnote"><b>Achtung Umkehrlogik:</b> ${esc(v.inverted_note)}</div>`:""}
    ${v.kontext?`<div class="v-kontext"><b>Protokoll:</b> ${hervorheben(v.kontext)}</div>`:""}
    ${(v.stichworte||[]).length?`<div class="v-stich"><b>Debatte:</b> ${hervorheben((v.stichworte||[]).join(", "))}</div>`:""}
    ${tags?`<div class="v-tags">${tags}</div>`:""}
    <button class="vn-toggle" type="button" aria-expanded="false" aria-controls="vn-${uid}">Wer hat wie gestimmt? <span class="caret">▾</span></button>
    <div class="vn-box" id="vn-${uid}"></div>`;
  const btn=card.querySelector(".vn-toggle"), box=card.querySelector(".vn-box");
  btn.onclick=()=>{
    const auf=box.classList.toggle("open");
    btn.setAttribute("aria-expanded", auf?"true":"false");
    if(auf && !box.dataset.gefuellt){ box.innerHTML=namenBox(s,vIdx); box.dataset.gefuellt="1"; }
  };
  card.querySelectorAll(".v-tag.detail").forEach(el=>{
    el.onclick=()=>{ tagAusKarte(el.dataset.tag); };
  });
  return card;
}

function renderVotes(){
  const liste=abstimmungenImScope();
  const treffer=liste.filter(passt);
  const box=document.getElementById("voteList"); box.innerHTML="";

  const info=document.getElementById("vTreffer");
  if(info) info.innerHTML = `<b>${treffer.length}</b> von ${liste.length} Abstimmungen`;
  const h=document.getElementById("votesTitel");
  if(h){
    const L=DATA.legislaturen[String(sessLegNr)];
    h.textContent = !sucheModus ? "Alle Abstimmungen dieser Sitzung"
      : (sessLegNr==="alle" ? "Suche über alle Sitzungen seit 2018"
                            : `Suche über die ${L?L.label:"Legislatur"}`);
  }

  if(!treffer.length){
    const aktiv=[vSuche?`Suchwort «${esc(vSuche)}»`:null, vForm?`Form «${esc(vForm)}»`:null,
                 tagDetail.length?`Tag «${esc(tagDetail.join(", "))}»`:(tagUnter?`Thema «${esc(tagUnter)}»`:(tagOber?`Thema «${esc(tagOber)}»`:null))]
                .filter(Boolean);
    box.innerHTML=`<div class="v-leer">Keine Abstimmung passt${aktiv.length?" zu "+aktiv.join(" und "):""}.
      ${sucheModus?"":"<br>Der Haken oben schaltet die Suche auf alle Sitzungen um."}
      <br><button class="vf-reset" type="button" id="vResetLeer" style="margin-top:12px">Filter zurücksetzen</button></div>`;
    const b=document.getElementById("vResetLeer");
    if(b) b.onclick=()=>document.getElementById("vReset").click();
    renderTagZeilen(liste);
    return;
  }
  let letzteSitzung=null;
  treffer.forEach(e=>{
    if(sucheModus && e.sIdx!==letzteSitzung){
      letzteSitzung=e.sIdx;
      const anzahl=treffer.filter(x=>x.sIdx===e.sIdx).length;
      const h=document.createElement("div"); h.className="v-sessgroup";
      h.innerHTML=`${esc(e.s.sitzung)}<small>${anzahl} Treffer</small>`;
      box.appendChild(h);
    }
    box.appendChild(voteCard(e));
  });
  renderTagZeilen(liste);
}

/* --- Tag-Ebenen ---------------------------------------------------------- */
function zaehleTags(liste, feld){
  const c={};
  liste.forEach(e=>(e.v[feld]||[]).forEach(t=>c[t]=(c[t]||0)+1));
  return c;
}
function chip(text, anzahl, aktiv, ebene, onclick){
  const b=document.createElement("button");
  b.type="button";
  b.className=`tagchip ebene${ebene}${aktiv?" aktiv":""}`;
  b.innerHTML=`${esc(text)}${anzahl!=null?`<small>${anzahl}</small>`:""}`;
  b.onclick=onclick;
  return b;
}
function renderTagZeilen(liste){
  const H=DATA.tags_hierarchie||[];
  const oberZ=zaehleTags(liste,"tags_ueberthema");
  const zeile1=document.getElementById("tagOber"); zeile1.innerHTML="";
  [...new Set(H.map(x=>x.ueberthema))].forEach(o=>{
    if(!oberZ[o] && tagOber!==o) return;
    zeile1.appendChild(chip(o, oberZ[o]||0, tagOber===o, 1, ()=>{
      tagOber = (tagOber===o? null : o); tagUnter=null; tagDetail=[]; renderVotes();
    }));
  });
  if(!zeile1.children.length){
    const leer=document.createElement("span"); leer.className="tag-hinweis";
    leer.textContent="Für diese Auswahl sind keine Themen erfasst.";
    zeile1.appendChild(leer);
  }

  const rowU=document.getElementById("tagUnterRow"), zeile2=document.getElementById("tagUnter");
  const rowD=document.getElementById("tagDetailRow"), zeile3=document.getElementById("tagDetail");
  rowU.style.display = tagOber ? "flex" : "none";
  rowD.style.display = tagUnter ? "flex" : "none";
  if(!tagOber) return;

  // Ebene 2 im gewählten Überthema
  const inOber=liste.filter(e=>(e.v.tags_ueberthema||[]).includes(tagOber));
  const unterZ=zaehleTags(inOber,"tags_unterthema");
  zeile2.innerHTML="";
  [...new Set(H.filter(x=>x.ueberthema===tagOber).map(x=>x.unterthema))].forEach(u=>{
    if(!unterZ[u] && tagUnter!==u) return;
    zeile2.appendChild(chip(u, unterZ[u]||0, tagUnter===u, 2, ()=>{
      tagUnter = (tagUnter===u? null : u); tagDetail=[]; renderVotes();
    }));
  });
  if(!tagUnter) return;

  // Ebene 3 im gewählten Unterthema, mehrfach wählbar
  const inUnter=inOber.filter(e=>(e.v.tags_unterthema||[]).includes(tagUnter));
  const detZ=zaehleTags(inUnter,"tags_detail");
  zeile3.innerHTML="";
  H.filter(x=>x.unterthema===tagUnter && x.ueberthema===tagOber).forEach(x=>{
    if(!detZ[x.tag] && !tagDetail.includes(x.tag)) return;
    zeile3.appendChild(chip(x.tag, detZ[x.tag]||0, tagDetail.includes(x.tag), 3, ()=>{
      tagDetail = tagDetail.includes(x.tag) ? tagDetail.filter(y=>y!==x.tag)
                                            : [...tagDetail, x.tag];
      renderVotes();
    }));
  });
}

/* Klick auf einen Tag an der Abstimmungskarte setzt den Filter */
function tagAusKarte(tag){
  const eintrag=(DATA.tags_hierarchie||[]).find(x=>x.tag===tag);
  if(!eintrag) return;
  tagOber=eintrag.ueberthema; tagUnter=eintrag.unterthema; tagDetail=[tag];
  renderVotes();
  window.scrollTo({top:0, behavior:"smooth"});
}

/* --- Suchfeld, Formfilter, Zurücksetzen ---------------------------------- */
function initVoteFilter(){
  const feld=document.getElementById("vSuche");
  let timer=null;
  feld.oninput=()=>{
    clearTimeout(timer);
    timer=setTimeout(()=>{ vSuche=feld.value.trim().toLowerCase(); renderVotes(); }, 220);
  };
  const formSel=document.getElementById("vForm");
  formSel.innerHTML='<option value="">Alle Formen</option>';
  (DATA.tags_form_liste||[]).forEach(f=>{
    const o=document.createElement("option"); o.value=f; o.textContent=f; formSel.appendChild(o);
  });
  formSel.onchange=()=>{ vForm=formSel.value; renderVotes(); };
  document.getElementById("vReset").onclick=()=>{
    vSuche=""; vForm=""; tagOber=null; tagUnter=null; tagDetail=[];
    feld.value=""; formSel.value="";
    renderVotes();
  };
}
/* Namen in den Abstimmungslisten -> Mitglied im Detail */
document.addEventListener("click", e=>{
  const a=e.target.closest(".vn-name");
  if(a) goToMember(a.dataset.member);
});
/* Öffnet eine Abstimmung der aktuellen Sitzung, aufgeklappt und hervorgehoben */
function goToVote(idx){
  // Filter lösen, damit die gesuchte Abstimmung sicher in der Liste steht
  sucheModus=false; modusBox.checked=false;
  document.getElementById("modusWrap").classList.remove("an");
  vSuche=""; vForm=""; tagOber=null; tagUnter=null; tagDetail=[];
  if(DATA.sessions[curSession]){
    sessLegNr=DATA.sessions[curSession].legislatur;
    sessLegSel.value=String(sessLegNr);
    fuelleSitzungen();
  }
  const feld=document.getElementById("vSuche"); if(feld) feld.value="";
  const fs=document.getElementById("vForm"); if(fs) fs.value="";
  sessSel.value=String(curSession);
  renderVotes();
  activateTab("votes");
  const card=document.getElementById(`vote-${curSession}-${idx}`);
  if(!card) return;
  const btn=card.querySelector(".vn-toggle"), box=card.querySelector(".vn-box");
  if(btn && box && !box.classList.contains("open")) btn.click();
  if(card.scrollIntoView) card.scrollIntoView({behavior:"smooth", block:"center"});
  card.classList.add("flash");
  setTimeout(()=>card.classList.remove("flash"), 2200);
}
/* Öffnet ein Ratsmitglied im Reiter "Mitglied im Detail" */
function goToMember(key){
  if(!key) return;
  const legSel=document.getElementById("mLeg"), sel=document.getElementById("mMember");
  // Legislatur suchen, in der die Person geführt ist: zuerst die der aktuellen
  // Sitzung, sonst die neueste, in der sie vorkommt.
  const kandidaten=[S().legislatur, ...Object.values(DATA.legislaturen).sort((a,b)=>b.nummer-a.nummer).map(L=>L.nummer)];
  const leg=kandidaten.find(L=>membersOfLeg(L).some(m=>m.key===key));
  if(leg===undefined){
    document.getElementById("mProfile").innerHTML =
      `<div class="section-note">Für ${esc(key.replace("|"," "))} liegt in den erfassten Legislaturen kein Profil vor.</div>`;
    activateTab("mitglied");
    return;
  }
  if(+legSel.value!==leg){ mLeg=leg; legSel.value=String(leg); fillMemberSelect(); }
  if([...sel.options].some(o=>o.value===key)) sel.value=key;
  renderMitglied();
  activateTab("mitglied");
}

/* ===== Fraktionsstatistik ===== */
function fraktStats(s,f){
  const mem=s.members.filter(m=>m.fraktion===f);
  let ja=0,nein=0,enth=0,van=0,discSum=0,valid=0;
  for(let i=0;i<s.votes.length;i++){
    const c={ja:0,nein:0,enth:0,van:0}; mem.forEach(m=>c[NV(m.votes[i])]++);
    ja+=c.ja;nein+=c.nein;enth+=c.enth;van+=c.van;
    const pres=c.ja+c.nein+c.enth;
    if(pres>0){discSum+=Math.max(c.ja,c.nein,c.enth)/pres;valid++;}
  }
  const tot=ja+nein+enth+van;
  return {seats:mem.length,ja,nein,enth,van,
    jaQuote:(ja/(ja+nein+enth||1))*100, enthQuote:(enth/(ja+nein+enth||1))*100,
    disziplin:valid?(discSum/valid)*100:0, praesenz:tot?((tot-van)/tot)*100:0};
}
// Aggregiert die Fraktionsstatistik über mehrere Sitzungen (z.B. eine Legislatur).
function fraktStatsMulti(sessions,f){
  let ja=0,nein=0,enth=0,van=0,discSum=0,valid=0,seats=0;
  sessions.forEach(s=>{
    const mem=s.members.filter(m=>m.fraktion===f);
    seats=Math.max(seats,mem.length);
    for(let i=0;i<s.votes.length;i++){
      const c={ja:0,nein:0,enth:0,van:0}; mem.forEach(m=>c[NV(m.votes[i])]++);
      ja+=c.ja;nein+=c.nein;enth+=c.enth;van+=c.van;
      const pres=c.ja+c.nein+c.enth;
      if(pres>0){discSum+=Math.max(c.ja,c.nein,c.enth)/pres;valid++;}
    }
  });
  const tot=ja+nein+enth+van;
  return {seats,ja,nein,enth,van,
    jaQuote:(ja/(ja+nein+enth||1))*100, enthQuote:(enth/(ja+nein+enth||1))*100,
    disziplin:valid?(discSum/valid)*100:0, praesenz:tot?((tot-van)/tot)*100:0};
}
function renderFrak(){
  const grid=document.getElementById("frakGrid"); grid.innerHTML="";
  const sess=spiderSessions(), meta=document.getElementById("frakScopeMeta");
  if(meta) meta.textContent = spiderScope.startsWith("leg:")
    ? `Gemittelt über ${sess.length} Sitzungen dieser Legislatur, ${sess.reduce((a,s)=>a+s.votes.length,0)} Abstimmungen.`
    : `Einzelne Sitzung mit ${sess[0].votes.length} Abstimmungen.`;
  spiderFraktionen().forEach(f=>{
    const st=statsForScope(f), col=FRAK_COLORS[f]||"#333";
    const card=document.createElement("div"); card.className="frak-card"; card.style.borderTopColor=col;
    card.innerHTML=`<h3 style="color:${col}">${FRAK_SHORT[f]||f}</h3><div class="fseats">${st.seats} Sitze</div>
      <div class="stat-row"><span>Ja-Quote</span><b>${st.jaQuote.toFixed(0)}%</b></div>
      <div class="stat-row"><span>Enthaltungen</span><b>${st.enthQuote.toFixed(0)}%</b></div>
      <div class="stat-row"><span>Präsenz</span><b>${st.praesenz.toFixed(0)}%</b></div>
      <div class="stat-row" style="border:none"><span>Geschlossenheit</span><b>${st.disziplin.toFixed(0)}%</b></div>
      <div class="disc-bar"><i style="width:${st.disziplin}%;background:${col}"></i></div>`;
    grid.appendChild(card);
  });
}

/* ===== Mitglieder ===== */
let sortKey="name",sortDir=1;
function memberJa(m){let ja=0,val=0;m.votes.forEach(v=>{const n=NV(v);if(n!=="van"){val++;if(n==="ja")ja++;}});return val?ja/val*100:0;}
function renderMembers(){
  const s=S(), ff=document.getElementById("fFrak"), fs=document.getElementById("fSearch"), body=document.getElementById("memberBody");
  let rows=s.members.slice();
  if(ff.value) rows=rows.filter(m=>m.fraktion===ff.value);
  if(fs.value) rows=rows.filter(m=>(m.nachname+" "+m.vorname).toLowerCase().includes(fs.value.toLowerCase()));
  rows.sort((a,b)=>{let A,B;
    if(sortKey==="name"){A=a.nachname;B=b.nachname;}
    else if(sortKey==="fraktion"){A=a.fraktion;B=b.fraktion;}
    else {A=memberJa(a);B=memberJa(b);}
    return (A<B?-1:A>B?1:0)*sortDir;});
  body.innerHTML=rows.map(m=>{
    const col=FRAK_COLORS[m.fraktion]||"#333";
    // Jeder Punkt verlinkt auf die zugehörige Abstimmung; die Frage erscheint beim Darüberfahren.
    const dots=m.votes.map((v,i)=>
      `<a class="vd-${NV(v)}" data-vote="${i}" data-mem="${esc(memKey(m))}" role="button" tabindex="0"></a>`).join("");
    return `<tr><td><a class="vn-name" style="display:inline-flex" data-member="${esc(memKey(m))}"><span class="pill" style="background:${col};margin-right:0"></span>${esc(m.nachname)} ${esc(m.vorname)}</a></td>
      <td class="hide-sm">${FRAK_SHORT[m.fraktion]||m.fraktion}</td>
      <td><b>${memberJa(m).toFixed(0)}%</b></td>
      <td class="hide-sm"><div class="vote-dots">${dots}</div></td></tr>`;
  }).join("");
}
/* --- Tooltip über den Stimmpunkten der Mitgliedertabelle ----------------- */
let vdTip=null;
function ensureTip(){
  if(!vdTip){ vdTip=document.createElement("div"); vdTip.className="vd-tip"; document.body.appendChild(vdTip); }
  return vdTip;
}
function tipHtml(idx, key){
  const s=S(), v=s.votes[idx];
  if(!v) return "";
  const m=s.members.find(x=>memKey(x)===key), t=tallyFor(s,idx);
  const eigen=m?{ja:"Ja",nein:"Nein",enth:"Enthaltung",van:"abwesend"}[NV(m.votes[idx])]:"";
  const g=v.geschaeft||"";
  return `<b class="tip-nr">Abstimmung ${v.nr}${v.typ?" · "+esc(v.typ):""}</b>`+
    esc(v.titel||"(ohne Titel)")+
    (g?`<div style="color:#cfc7b8;font-style:italic;margin-top:4px">${esc(g.slice(0,130))}${g.length>130?"…":""}</div>`:"")+
    (v.inverted_note?`<div style="color:#f0d9a0;margin-top:4px">Umkehrlogik: ${esc(v.inverted_note)}</div>`:"")+
    `<div class="tip-res">${m?`<span class="tip-eig">${esc(m.nachname)} ${esc(m.vorname)}: ${eigen}</span> · `:""}`+
    `Rat: ${t.ja} Ja, ${t.nein} Nein, ${t.enth} Enth., ${t.van} abw.</div>`;
}
function positionTip(e){
  const tip=ensureTip(), pad=15, r=tip.getBoundingClientRect();
  let x=e.clientX+pad, y=e.clientY+pad;
  if(x+r.width > window.innerWidth-10) x=e.clientX-r.width-pad;
  if(y+r.height > window.innerHeight-10) y=e.clientY-r.height-pad;
  tip.style.left=Math.max(8,x)+"px"; tip.style.top=Math.max(8,y)+"px";
}
function hideTip(){ if(vdTip) vdTip.style.display="none"; }
document.addEventListener("mouseover", e=>{
  const a=e.target.closest(".vote-dots a"); if(!a) return;
  const tip=ensureTip();
  tip.innerHTML=tipHtml(+a.dataset.vote, a.dataset.mem);
  tip.style.display="block";
  positionTip(e);
});
document.addEventListener("mousemove", e=>{
  if(vdTip && vdTip.style.display==="block" && e.target.closest(".vote-dots a")) positionTip(e);
});
document.addEventListener("mouseout", e=>{ if(e.target.closest(".vote-dots a")) hideTip(); });
document.addEventListener("click", e=>{
  const a=e.target.closest(".vote-dots a"); if(!a) return;
  hideTip(); goToVote(+a.dataset.vote);
});
document.addEventListener("keydown", e=>{
  if(e.key!=="Enter" && e.key!==" ") return;
  const a=document.activeElement && document.activeElement.closest && document.activeElement.closest(".vote-dots a");
  if(a){ e.preventDefault(); goToVote(+a.dataset.vote); }
});

function initMemberControls(){
  const ff=document.getElementById("fFrak");
  ff.innerHTML='<option value="">Alle Fraktionen</option>';
  fraktionen(S()).forEach(f=>{const o=document.createElement("option");o.value=f;o.textContent=FRAK_SHORT[f]||f;ff.appendChild(o);});
  ff.onchange=renderMembers; document.getElementById("fSearch").oninput=renderMembers;
  document.querySelectorAll(".member-table th").forEach(th=>{th.onclick=()=>{const k=th.dataset.sort;if(k===sortKey)sortDir*=-1;else{sortKey=k;sortDir=1;}renderMembers();};});
}

/* ===== Fraktionen: Kennzahlen + Profil (gemeinsamer Reiter) ===== */
const AXES=[{key:"jaQuote",label:"Zustimmung"},{key:"disziplin",label:"Geschlossenheit"},{key:"praesenz",label:"Präsenz"},{key:"enthQuote",label:"Enthaltung"},{key:"aktivNein",label:"Opposition"}];
// Scope: "leg:N" (ganze Legislatur) oder Sitzungsindex als String
let spiderScope = "leg:" + DATA.aktuelle_legislatur;
function renderFrakTab(){ renderFrak(); initSpiderToggles(); drawSpider(); }

function spiderSessions(){
  if(spiderScope.startsWith("leg:")){
    const L=+spiderScope.slice(4);
    return DATA.sessions.filter(s=>s.legislatur===L);
  }
  return [DATA.sessions[+spiderScope]];
}
function spiderFraktionen(){
  // alle Fraktionen, die im Scope vorkommen
  const set=new Set();
  spiderSessions().forEach(s=>s.members.forEach(m=>set.add(m.fraktion)));
  return [...set];
}
function statsForScope(f){
  const sess=spiderSessions();
  return sess.length>1 ? fraktStatsMulti(sess,f) : fraktStats(sess[0],f);
}
function axisValsScope(f){
  const st=statsForScope(f);
  return {jaQuote:st.jaQuote,disziplin:st.disziplin,praesenz:st.praesenz,
    enthQuote:Math.min(st.enthQuote*4,100),
    aktivNein:Math.min((st.nein/(st.ja+st.nein+st.enth||1))*100*2,100)};
}
let spiderState={};
function initSpiderScope(){
  const sel=document.getElementById("frakScopeSel");
  if(!sel) return;
  sel.innerHTML="";
  Object.values(DATA.legislaturen).sort((a,b)=>b.nummer-a.nummer).forEach(L=>{
    const o=document.createElement("option"); o.value="leg:"+L.nummer;
    o.textContent=L.label+(L.nummer===DATA.aktuelle_legislatur?" (aktuell)":"")+` · ${L.n_sitzungen} Sitzungen`;
    sel.appendChild(o);
  });
  const og=document.createElement("optgroup"); og.label="Einzelne Sitzungen";
  DATA.sessions.forEach((s,i)=>{const o=document.createElement("option");o.value=String(i);o.textContent=s.sitzung;og.appendChild(o);});
  sel.appendChild(og);
  sel.value=spiderScope;
  sel.onchange=()=>{ spiderScope=sel.value; renderFrakTab(); };
}
function initSpiderToggles(){
  const box=document.getElementById("spiderToggles"); box.innerHTML="";
  const fr=spiderFraktionen();
  // bestehende Auswahl bewahren, neue standardmässig an
  const prev={...spiderState}; spiderState={};
  fr.forEach(f=>spiderState[f]=(f in prev)?prev[f]:true);
  fr.forEach(f=>{
    const col=FRAK_COLORS[f]||"#777", lab=document.createElement("label"); lab.className="frak-toggle";
    lab.innerHTML=`<input type="checkbox" ${spiderState[f]?"checked":""}><span class="swatch" style="background:${col}"></span><span>${FRAK_SHORT[f]||f}</span>`;
    lab.querySelector("input").onchange=e=>{spiderState[f]=e.target.checked;drawSpider();};
    box.appendChild(lab);
  });
  const sess=spiderSessions();
  const scopeLabel = spiderScope.startsWith("leg:")
    ? `Gemittelt über ${sess.length} Sitzungen dieser Legislatur.`
    : `Einzelne Sitzung.`;
  const cap=document.createElement("div"); cap.className="axis-caption";
  cap.innerHTML=`<b>${scopeLabel}</b><br><b>Achsen:</b> Zustimmung = Ja-Anteil. Geschlossenheit = wie einheitlich die Fraktion stimmt. Präsenz = Teilnahme. Enthaltung &amp; Opposition sind zur Sichtbarkeit skaliert.`;
  box.appendChild(cap);
}
function drawSpider(){
  const svg=document.getElementById("spider"); if(!svg)return;
  const CX=190,CY=195,R=130,N=AXES.length; let g=`<g stroke="#e2ddd3" fill="none">`;
  for(let ring=1;ring<=4;ring++){const r=R*ring/4;let pts="";for(let i=0;i<N;i++){const a=Math.PI*2*i/N-Math.PI/2;pts+=`${CX+r*Math.cos(a)},${CY+r*Math.sin(a)} `;}g+=`<polygon points="${pts}"/>`;}
  for(let i=0;i<N;i++){const a=Math.PI*2*i/N-Math.PI/2;g+=`<line x1="${CX}" y1="${CY}" x2="${CX+R*Math.cos(a)}" y2="${CY+R*Math.sin(a)}"/>`;}
  g+=`</g><g font-size="11" fill="#6b6459" font-weight="600">`;
  AXES.forEach((ax,i)=>{const a=Math.PI*2*i/N-Math.PI/2,lr=R+22;let x=CX+lr*Math.cos(a),y=CY+lr*Math.sin(a);let anch=Math.abs(Math.cos(a))<0.3?"middle":(Math.cos(a)>0?"start":"end");g+=`<text x="${x}" y="${y+3}" text-anchor="${anch}">${ax.label}</text>`;});
  g+=`</g>`;
  spiderFraktionen().forEach(f=>{
    if(!spiderState[f])return; const vals=axisValsScope(f),col=FRAK_COLORS[f]||"#777";let pts="";
    AXES.forEach((ax,i)=>{const a=Math.PI*2*i/N-Math.PI/2,r=R*(vals[ax.key]/100);pts+=`${CX+r*Math.cos(a)},${CY+r*Math.sin(a)} `;});
    g+=`<polygon points="${pts}" fill="${col}" fill-opacity="0.12" stroke="${col}" stroke-width="2"/>`;
    AXES.forEach((ax,i)=>{const a=Math.PI*2*i/N-Math.PI/2,r=R*(vals[ax.key]/100);g+=`<circle cx="${CX+r*Math.cos(a)}" cy="${CY+r*Math.sin(a)}" r="3" fill="${col}"/>`;});
  });
  svg.innerHTML=g;
}

/* ===== Ranglisten ===== */
// Scope: "leg:N" (ganze Legislatur) oder Sitzungsindex als String
let rankScope = "leg:" + DATA.aktuelle_legislatur;

function sessionsInScope(){
  if(rankScope.startsWith("leg:")){
    const L = +rankScope.slice(4);
    return DATA.sessions.filter(s => s.legislatur === L);
  }
  return [DATA.sessions[+rankScope]];
}
function legOfScope(){
  if(rankScope.startsWith("leg:")) return +rankScope.slice(4);
  return DATA.sessions[+rankScope].legislatur;
}
// aktive Mitglieder der betreffenden Legislatur (Key "nachname|vorname")
function activeMembersOf(leg){
  const meta = DATA.legislaturen[String(leg)];
  return new Set(meta ? meta.aktive_mitglieder : []);
}

function collectMemberStats(){
  const sess = sessionsInScope();
  const active = activeMembersOf(legOfScope());
  const key = m => m.nachname + "|" + m.vorname;
  const acc = {};
  sess.forEach(s => {
    s.members.forEach(m => {
      const k = key(m);
      if(!active.has(k)) return;              // nur aktuelle Ratsmitglieder
      if(!acc[k]) acc[k] = {nachname:m.nachname,vorname:m.vorname,fraktion:m.fraktion,
                            partei:m.partei,ja:0,nein:0,enth:0,van:0,total:0,sitzungen:0};
      acc[k].sitzungen++;
      m.votes.forEach(v => {const n=NV(v); acc[k][n]++; acc[k].total++;});
    });
  });
  // total ist bereits relativ: nur Abstimmungen aus Sitzungen, in denen die
  // Person geführt wurde. Präsenz = (total - van) / total.
  return Object.values(acc);
}
function collectPartyStats(){
  const sess = sessionsInScope();
  const active = activeMembersOf(legOfScope());
  const key = m => m.nachname + "|" + m.vorname;
  const acc = {};
  sess.forEach(s => {
    s.members.forEach(m => {
      if(!active.has(key(m))) return;         // nur aktuelle Ratsmitglieder
      const p = m.partei || "?";
      if(!acc[p]) acc[p] = {partei:p,fraktion:m.fraktion,ja:0,nein:0,enth:0,van:0,total:0,members:new Set()};
      acc[p].members.add(key(m));
      m.votes.forEach(v => {const n=NV(v); acc[p][n]++; acc[p].total++;});
    });
  });
  return Object.values(acc).map(p => ({...p, nMembers:p.members.size}));
}
function rankBox(title,icoColor,icoChar,items,valFn,subFn,fmt){
  const max=Math.max(...items.map(valFn),1);
  const top=items.slice().sort((a,b)=>valFn(b)-valFn(a)).slice(0,8);
  let html=`<div class="rank-box"><h3><span class="ico" style="background:${icoColor}">${icoChar}</span>${title}</h3><ul class="rank-list">`;
  top.forEach((it,i)=>{
    const v=valFn(it), pct=(v/max)*100;
    html+=`<li><span class="rank-num ${i===0?'top1':''}">${i+1}</span>
      <div class="rank-cell"><span class="rank-name ${i===0?'top1':''}">${subFn(it)}</span>
      <div class="rank-bar"><i style="width:${pct}%;background:${icoColor}"></i></div></div>
      <span class="rank-val">${fmt(it,v)}</span></li>`;
  });
  return html+`</ul></div>`;
}
// Prozentwert mit der zugrunde liegenden Rechnung darunter, z.B. "82%" / "(49/60)"
const bruch = (v, zaehler, nenner) =>
  `${v.toFixed(0)}%<small>${zaehler} von ${nenner}</small>`;

function renderRang(){
  const mem = collectMemberStats();
  const par = collectPartyStats();
  const subM = it => `${it.nachname} ${it.vorname} <small>${FRAK_SHORT[it.fraktion]||it.partei}</small>`;
  const abgegeben = it => it.total - it.van;

  document.getElementById("rankMembers").innerHTML =
    rankBox("Fleissigste (höchste Präsenz)","#2b5c8a","P",mem,it=>abgegeben(it)/(it.total||1)*100,subM,
            (it,v)=>bruch(v, abgegeben(it), it.total))+
    rankBox("Abwesenheitskönige","#9a8f7d","A",mem,it=>it.van/(it.total||1)*100,subM,
            (it,v)=>bruch(v, it.van, it.total))+
    rankBox("Ja-Sager","#3a7d3a","J",mem,it=>it.ja/(abgegeben(it)||1)*100,subM,
            (it,v)=>bruch(v, it.ja, abgegeben(it)))+
    rankBox("Nein-Sager","#c1272d","N",mem,it=>it.nein/(abgegeben(it)||1)*100,subM,
            (it,v)=>bruch(v, it.nein, abgegeben(it)))+
    rankBox("Enthalter","#b0a89a","E",mem,it=>it.enth/(abgegeben(it)||1)*100,subM,
            (it,v)=>bruch(v, it.enth, abgegeben(it)));

  const subP = it => `${it.partei} <small>${it.nMembers} Mitgl.</small>`;
  document.getElementById("rankParties").innerHTML =
    rankBox("Präsenz nach Partei","#2b5c8a","P",par,it=>(it.total-it.van)/(it.total||1)*100,subP,
            (it,v)=>bruch(v, it.total-it.van, it.total))+
    rankBox("Abwesenheit nach Partei","#9a8f7d","A",par,it=>it.van/(it.total||1)*100,subP,
            (it,v)=>bruch(v, it.van, it.total))+
    rankBox("Ja-Quote nach Partei","#3a7d3a","J",par,it=>it.ja/((it.total-it.van)||1)*100,subP,
            (it,v)=>bruch(v, it.ja, it.total-it.van))+
    rankBox("Nein-Quote nach Partei","#c1272d","N",par,it=>it.nein/((it.total-it.van)||1)*100,subP,
            (it,v)=>bruch(v, it.nein, it.total-it.van))+
    rankBox("Enthaltungs-Quote nach Partei","#b0a89a","E",par,it=>it.enth/((it.total-it.van)||1)*100,subP,
            (it,v)=>bruch(v, it.enth, it.total-it.van));

  const sess = sessionsInScope();
  const legMeta = DATA.legislaturen[String(legOfScope())];
  if(rankScope.startsWith("leg:")){
    const istAktuell = legOfScope() === DATA.aktuelle_legislatur;
    const wer = istAktuell ? "aktuelle Ratsmitglieder" : "Ratsmitglieder dieser Legislatur";
    document.getElementById("rankMeta").textContent =
      `${mem.length} ${wer} · ${legMeta ? legMeta.label : "Legislatur"} · ${sess.length} Sitzungen. `+
      `Präsenz und Quoten je Person relativ zu ihren eigenen Sitzungen (ab Amtsantritt).`;
  } else {
    document.getElementById("rankMeta").textContent =
      `${mem.length} Ratsmitglieder · Einzelsitzung mit ${sess[0].n_votes} Abstimmungen.`;
  }
}
function initRankScope(){
  const sel = document.getElementById("rankScopeSel");
  sel.innerHTML = "";
  // Legislatur-Optionen (neueste zuerst)
  Object.values(DATA.legislaturen)
    .sort((a,b)=>b.nummer-a.nummer)
    .forEach(L=>{
      const o=document.createElement("option");
      o.value="leg:"+L.nummer;
      o.textContent=L.label + (L.nummer===DATA.aktuelle_legislatur?" (aktuell)":"") + ` · ${L.n_sitzungen} Sitzungen`;
      sel.appendChild(o);
    });
  // Trenner + Einzelsitzungen
  const og=document.createElement("optgroup"); og.label="Einzelne Sitzungen";
  DATA.sessions.forEach((s,i)=>{const o=document.createElement("option");o.value=String(i);o.textContent=s.sitzung;og.appendChild(o);});
  sel.appendChild(og);
  sel.value = "leg:" + DATA.aktuelle_legislatur;
  sel.onchange = () => { rankScope = sel.value; renderRang(); };
}

/* ===== Mitglied im Detail ===== */
let mLeg = DATA.aktuelle_legislatur;

function sessionsOfLeg(leg){
  // chronologisch (älteste zuerst) für die Timeline
  const s = DATA.sessions.filter(x => x.legislatur === leg).slice();
  s.sort((a,b)=>{
    const pa = a.sitzung.match(/(\d{2})\.(\d{2})\.(\d{4})/);
    const pb = b.sitzung.match(/(\d{2})\.(\d{2})\.(\d{4})/);
    const da = pa ? +(pa[3]+pa[2]+pa[1]) : 0;
    const db = pb ? +(pb[3]+pb[2]+pb[1]) : 0;
    if(da!==db) return da-db;
    const ha = a.sitzung.includes("Vormittag")?0:a.sitzung.includes("Abend")?2:1;
    const hb = b.sitzung.includes("Vormittag")?0:b.sitzung.includes("Abend")?2:1;
    return ha-hb;
  });
  return s;
}
function membersOfLeg(leg){
  const meta = DATA.legislaturen[String(leg)];
  const active = new Set(meta ? meta.aktive_mitglieder : []);
  // Namen + Fraktion aus der neuesten Sitzung dieser Legislatur
  const sess = sessionsOfLeg(leg);
  const newest = sess[sess.length-1];
  const list = [];
  newest.members.forEach(m=>{
    const k=m.nachname+"|"+m.vorname;
    if(active.has(k)) list.push({key:k, nachname:m.nachname, vorname:m.vorname, fraktion:m.fraktion, partei:m.partei});
  });
  list.sort((a,b)=> (a.nachname+a.vorname).localeCompare(b.nachname+b.vorname, "de"));
  return list;
}
function initMitglied(){
  const legSel=document.getElementById("mLeg");
  legSel.innerHTML="";
  Object.values(DATA.legislaturen).sort((a,b)=>b.nummer-a.nummer).forEach(L=>{
    const o=document.createElement("option"); o.value=L.nummer;
    o.textContent=L.label+(L.nummer===DATA.aktuelle_legislatur?" (aktuell)":"");
    legSel.appendChild(o);
  });
  legSel.value=mLeg;
  legSel.onchange=()=>{ mLeg=+legSel.value; fillMemberSelect(); renderMitglied(); };
  fillMemberSelect();
  document.getElementById("mMember").onchange=renderMitglied;
  renderMitglied();
}
function fillMemberSelect(){
  const sel=document.getElementById("mMember");
  const prev=sel.value;
  sel.innerHTML="";
  membersOfLeg(mLeg).forEach(m=>{
    const o=document.createElement("option"); o.value=m.key;
    o.textContent=`${m.nachname} ${m.vorname} (${FRAK_SHORT[m.fraktion]||m.partei})`;
    sel.appendChild(o);
  });
  // vorherige Auswahl beibehalten falls noch vorhanden
  if(prev && [...sel.options].some(o=>o.value===prev)) sel.value=prev;
}
/* ===== Personenprofile von sh.ch: Porträt und Interessenbindungen ===== */
const PERSON_INDEX = {};
(PERSONEN.mitglieder||[]).forEach(p=>{
  PERSON_INDEX[norm2(p.nachname)+"|"+norm2(p.vorname)] = p;
});
function norm2(s){
  return (s||"").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g,"").replace(/[^a-z]/g,"");
}
function personProfil(nachname, vorname){
  return PERSON_INDEX[norm2(nachname)+"|"+norm2(vorname)] || null;
}
/* Mandate einer Person aus dem Netz, mit Rolle und Branche */
function mandateVon(p){
  if(!p) return [];
  const mid="m:"+p.nachname+"|"+p.vorname;
  const orgs={}; (NETZ.knoten||[]).forEach(k=>orgs[k.id]=k);
  return (NETZ.kanten||[]).filter(k=>k.von===mid && k.art!=="branche").map(k=>({
    roh:k.roh, rolle:k.rolle, org:orgs[k.nach]||{label:"", branche:""}
  }));
}
function interessenBlock(p){
  if(!p) return `<div class="m-int leer">Für dieses Ratsmitglied liegt auf sh.ch kein Profil vor.</div>`;
  const m=mandateVon(p);
  if(!m.length) return `<div class="m-int leer"><b>Interessenbindungen:</b> auf sh.ch keine deklariert.</div>`;
  const zeilen=m.map(x=>`<li><span class="m-int-branche" data-branche="${esc(x.org.branche||"")}">${esc(x.org.branche||"–")}</span>
      <span class="m-int-org">${esc(x.org.label)}</span>
      ${x.rolle?`<small>${esc(x.rolle)}</small>`:""}</li>`).join("");
  return `<div class="m-int"><h3 class="m-int-titel">Interessenbindungen <small>${m.length}, deklariert auf sh.ch</small></h3>
    <ul class="m-int-liste">${zeilen}</ul>
    <div class="m-int-fuss">Stand ${esc(PERSONEN.stand||"?")}. Selbstdeklaration der Ratsmitglieder,
      im Reiter «Interessenbindungen» als Netz dargestellt.</div></div>`;
}

function renderMitglied(){
  const key=document.getElementById("mMember").value;
  const box=document.getElementById("mProfile");
  if(!key){ box.innerHTML=""; return; }
  const sess=sessionsOfLeg(mLeg);
  let ja=0,nein=0,enth=0,van=0,tot=0, sitzTeil=0;
  const groups=[];
  let frakInfo=null;
  sess.forEach(s=>{
    const m=s.members.find(x=>x.nachname+"|"+x.vorname===key);
    if(!m) return;
    sitzTeil++;
    if(!frakInfo) frakInfo={fraktion:m.fraktion, partei:m.partei, nachname:m.nachname, vorname:m.vorname};
    const rows=[];
    s.votes.forEach((v,i)=>{
      const stimme=m.votes[i];
      const n=NV(stimme);
      if(n==="ja") ja++; else if(n==="nein") nein++; else if(n==="enth") enth++; else van++;
      tot++;
      rows.push({v, n, stimme});
    });
    groups.push({s, rows});
  });
  const abg=tot-van;
  const pct=(x,base)=> base>0 ? (x/base*100).toFixed(0)+"%" : "–";
  const col=FRAK_COLORS[frakInfo.fraktion]||"#333";

  // Themen-Aufschlüsselung: wie stimmt die Person je Themengruppe?
  const themen={};
  groups.forEach(g=>{
    g.rows.forEach(r=>{
      const tn=r.v.thema_name;
      if(!tn) return;
      if(!themen[tn]) themen[tn]={name:tn, gruppe:r.v.thema_gruppe, ja:0,nein:0,enth:0,van:0,tot:0};
      const t=themen[tn]; t[r.n]++; t.tot++;
    });
  });
  const themenArr=Object.values(themen).sort((a,b)=>b.tot-a.tot);

  const P = personProfil(frakInfo.nachname, frakInfo.vorname);
  const bild = P && P.bild
    ? `<img class="m-portrait" src="data:image/jpeg;base64,${P.bild}" alt="${esc(frakInfo.nachname)} ${esc(frakInfo.vorname)}">`
    : `<div class="m-portrait leer">${esc((frakInfo.vorname[0]||"")+(frakInfo.nachname[0]||""))}</div>`;
  const stamm = P ? [P.beruf?`${esc(P.beruf)}`:null, P.geburtsdatum?`Jahrgang ${esc((P.geburtsdatum.match(/\d{4}/)||[""])[0])}`:null,
                     P.seit?`im Rat seit ${esc(P.seit)}`:null].filter(Boolean).join(" · ") : "";

  let html=`<div class="m-head" style="border-left-color:${col}">
    ${bild}
    <div><div class="m-name">${frakInfo.nachname} ${frakInfo.vorname}</div>
    <div class="m-frak">${frakInfo.fraktion} · ${frakInfo.partei} · ${sitzTeil} von ${sess.length} Sitzungen dieser Legislatur</div>
    ${stamm?`<div class="m-stamm">${stamm}</div>`:""}
    ${P&&P.url?`<div class="m-stamm"><a class="mv-link" href="${P.url}" target="_blank" rel="noopener">Profil auf sh.ch</a></div>`:""}</div>
  </div>
  ${interessenBlock(P)}
  <div class="m-stats">
    <div class="m-stat"><div class="num">${tot}</div><div class="lbl">Abstimmungen</div></div>
    <div class="m-stat ja"><div class="num">${ja}</div><div class="lbl">Ja</div><div class="sub">${pct(ja,abg)} der abgegebenen</div></div>
    <div class="m-stat nein"><div class="num">${nein}</div><div class="lbl">Nein</div><div class="sub">${pct(nein,abg)} der abgegebenen</div></div>
    <div class="m-stat enth"><div class="num">${enth}</div><div class="lbl">Enthaltung</div><div class="sub">${pct(enth,abg)} der abgegebenen</div></div>
    <div class="m-stat van"><div class="num">${van}</div><div class="lbl">Abwesend</div><div class="sub">${pct(van,tot)} aller Vorlagen</div></div>
  </div>`;

  // Themen-Block
  if(themenArr.length){
    html+=`<h3 class="m-themen-titel">Abstimmungsverhalten nach Thema</h3>
      <p class="m-themen-note">Themen orientieren sich an der Systematik der Schaffhauser Rechtssammlung (9 Hauptgruppen). Anteile beziehen sich auf die abgegebenen Stimmen zu diesem Thema.</p>
      <div class="m-themen">`;
    themenArr.forEach(t=>{
      const tabg=t.ja+t.nein+t.enth;
      const jaW=tabg?t.ja/tabg*100:0, neinW=tabg?t.nein/tabg*100:0, enthW=tabg?t.enth/tabg*100:0;
      html+=`<div class="m-thema">
        <div class="m-thema-head"><span class="m-thema-name">${t.name}</span><span class="m-thema-count">${t.tot} Abst.</span></div>
        <div class="m-thema-bar">
          <span style="width:${jaW}%" class="mt-ja" title="Ja: ${t.ja}"></span>
          <span style="width:${neinW}%" class="mt-nein" title="Nein: ${t.nein}"></span>
          <span style="width:${enthW}%" class="mt-enth" title="Enthaltung: ${t.enth}"></span>
        </div>
        <div class="m-thema-legend"><b style="color:var(--svp)">${t.ja} Ja</b> · <b style="color:var(--sp)">${t.nein} Nein</b> · ${t.enth} Enth. · ${t.van} abw.</div>
      </div>`;
    });
    html+=`</div>`;
  }

  // gruppiert nach Sitzung, neueste zuerst in der Anzeige
  groups.slice().reverse().forEach(g=>{
    const t=tallyFor(g.s, 0); // nur für kontext nicht nötig
    const sessLink = g.s.url
      ? `<a class="m-sess-link" href="${g.s.url}" target="_blank" rel="noopener">${g.s.sitzung}</a>`
      : g.s.sitzung;
    html+=`<div class="m-sess-group"><div class="m-sess-title">${sessLink}<small>${g.rows.length} Abstimmungen</small></div>`;
    g.rows.forEach(r=>{
      const badge={ja:"mb-ja",nein:"mb-nein",enth:"mb-enth",van:"mb-van"}[r.n];
      const label={ja:"Ja",nein:"Nein",enth:"Enth.",van:"abw."}[r.n];
      const tly=tallyForVote(g.s, r.v.nr-1);
      // aussagekräftiger Titel: eigener Titel, ergänzt um Geschäftskontext
      const titelText = r.v.titel || "(ohne Titel)";
      const titelHtml = g.s.url
        ? `<a class="mv-link" href="${g.s.url}" target="_blank" rel="noopener">${titelText}</a>`
        : titelText;
      const kontext = r.v.geschaeft
        ? `<div class="mv-gesch">${r.v.geschaeft}</div>` : "";
      html+=`<div class="m-vote">
        <span class="m-vote-badge ${badge}">${label}</span>
        <div class="m-vote-body">
          <div class="mv-titel">${titelHtml}</div>
          <div class="mv-meta">${r.v.typ?r.v.typ+" · ":""}Abstimmung ${r.v.nr}</div>
          ${kontext}
          ${r.v.inverted_note?`<span class="mv-inv">Umkehrlogik: ${r.v.inverted_note}</span>`:""}
        </div>
        <div class="m-vote-result">Rat gesamt:<br>${tly.ja} J · ${tly.nein} N · ${tly.enth} E</div>
      </div>`;
    });
    html+=`</div>`;
  });
  box.innerHTML=html;
}
function tallyForVote(s, idx){
  const t={ja:0,nein:0,enth:0,van:0};
  s.members.forEach(m=>t[NV(m.votes[idx])]++);
  return t;
}

/* ===== Themen ===== */
let tLeg = DATA.aktuelle_legislatur;
let tThema = null; // gewählte Gruppennummer

function themenInLeg(leg){
  // welche Themen kommen in dieser Legislatur vor, mit Anzahl
  const c={};
  DATA.sessions.filter(s=>s.legislatur===leg).forEach(s=>{
    s.votes.forEach(v=>{ if(v.thema_gruppe){ c[v.thema_gruppe]=(c[v.thema_gruppe]||0)+1; } });
  });
  return c;
}
function initThemen(){
  const legSel=document.getElementById("tLeg");
  legSel.innerHTML="";
  Object.values(DATA.legislaturen).sort((a,b)=>b.nummer-a.nummer).forEach(L=>{
    const o=document.createElement("option"); o.value=L.nummer;
    o.textContent=L.label+(L.nummer===DATA.aktuelle_legislatur?" (aktuell)":"");
    legSel.appendChild(o);
  });
  legSel.value=tLeg;
  legSel.onchange=()=>{ tLeg=+legSel.value; tThema=null; renderThemenChips(); renderThemen(); };
  renderThemenChips();
  renderThemen();
}
function renderThemenChips(){
  const counts=themenInLeg(tLeg);
  const box=document.getElementById("themenChips");
  const gruppen=DATA.themen_gruppen||{};
  // nach Anzahl sortiert
  const sorted=Object.keys(counts).sort((a,b)=>counts[b]-counts[a]);
  if(tThema===null && sorted.length) tThema=sorted[0];
  box.innerHTML=sorted.map(g=>{
    const active=g===tThema?" active":"";
    return `<button class="themen-chip${active}" data-g="${g}">${gruppen[g]||("Gruppe "+g)} <span class="tc-count">${counts[g]}</span></button>`;
  }).join("");
  box.querySelectorAll(".themen-chip").forEach(btn=>{
    btn.onclick=()=>{ tThema=btn.dataset.g; renderThemenChips(); renderThemen(); };
  });
}
function renderThemen(){
  const box=document.getElementById("themenInhalt");
  if(tThema===null){ box.innerHTML="<p class='section-note'>Kein Thema verfügbar.</p>"; return; }
  const gruppen=DATA.themen_gruppen||{};
  const sess=DATA.sessions.filter(s=>s.legislatur===tLeg);
  const active=new Set((DATA.legislaturen[String(tLeg)]||{}).aktive_mitglieder||[]);

  // 1. alle Abstimmungen dieses Themas sammeln (chronologisch)
  const votesOfTheme=[]; // {s, idx, v}
  sess.forEach(s=>{
    s.votes.forEach((v,i)=>{ if(v.thema_gruppe===tThema) votesOfTheme.push({s, idx:i, v}); });
  });

  // 2. pro Mitglied: Ja/Nein/Enth/van zu diesem Thema
  const acc={};
  sess.forEach(s=>{
    s.members.forEach(m=>{
      const k=m.nachname+"|"+m.vorname;
      if(!active.has(k)) return;
      s.votes.forEach((v,i)=>{
        if(v.thema_gruppe!==tThema) return;
        if(!acc[k]) acc[k]={nachname:m.nachname,vorname:m.vorname,fraktion:m.fraktion,partei:m.partei,ja:0,nein:0,enth:0,van:0,tot:0};
        const n=NV(m.votes[i]); acc[k][n]++; acc[k].tot++;
      });
    });
  });
  const mem=Object.values(acc);

  // 3. pro Partei aggregieren
  const par={};
  mem.forEach(m=>{
    const p=m.partei||"?";
    if(!par[p]) par[p]={partei:p, fraktion:m.fraktion, ja:0,nein:0,enth:0,van:0,tot:0, n:0};
    ["ja","nein","enth","van","tot"].forEach(k=>par[p][k]+=m[k]); par[p].n++;
  });

  const abg=x=>x.ja+x.nein+x.enth;
  // Header + Fraktions-/Partei-Übersicht
  let html=`<div class="themen-head">
    <h3 class="themen-h3">${gruppen[tThema]||("Gruppe "+tThema)}</h3>
    <div class="themen-sub">${votesOfTheme.length} Abstimmungen in dieser Legislatur</div>
  </div>`;

  // Parteien: Ja/Nein-Balken
  html+=`<h4 class="themen-sec">Wie stimmen die Parteien zu diesem Thema?</h4><div class="themen-parteien">`;
  Object.values(par).sort((a,b)=> (b.ja/(abg(b)||1)) - (a.ja/(abg(a)||1))).forEach(p=>{
    const a=abg(p); const jw=a?p.ja/a*100:0, nw=a?p.nein/a*100:0, ew=a?p.enth/a*100:0;
    const col=FRAK_COLORS[p.fraktion]||"#777";
    html+=`<div class="tp-row">
      <div class="tp-name" style="border-color:${col}">${p.partei} <small>${p.n} Mitgl.</small></div>
      <div class="tp-bar"><span class="mt-ja" style="width:${jw}%"></span><span class="mt-nein" style="width:${nw}%"></span><span class="mt-enth" style="width:${ew}%"></span></div>
      <div class="tp-val">${p.ja}J · ${p.nein}N</div>
    </div>`;
  });
  html+=`</div>`;

  // Mitglieder-Rangliste: höchste Ja-Quote zu diesem Thema
  html+=`<h4 class="themen-sec">Ratsmitglieder: Zustimmung zu diesem Thema</h4>
    <p class="ub-secnote">Ja-Anteil an den abgegebenen Stimmen zu «${gruppen[tThema]}». Sortierbar. Nur Mitglieder mit mindestens einer Stimme zum Thema.</p>
    <table class="member-table"><thead><tr>
      <th>Name</th><th class="hide-sm">Fraktion</th><th>Ja</th><th>Nein</th><th>Enth.</th><th>Ja-Quote</th>
    </tr></thead><tbody>`;
  mem.sort((a,b)=> (b.ja/(abg(b)||1)) - (a.ja/(abg(a)||1)));
  mem.forEach(m=>{
    const a=abg(m); const q=a?(m.ja/a*100):0; const col=FRAK_COLORS[m.fraktion]||"#333";
    html+=`<tr><td><span class="pill" style="background:${col}"></span>${m.nachname} ${m.vorname}</td>
      <td class="hide-sm">${FRAK_SHORT[m.fraktion]||m.fraktion}</td>
      <td>${m.ja}</td><td>${m.nein}</td><td>${m.enth}</td><td><b>${q.toFixed(0)}%</b></td></tr>`;
  });
  html+=`</tbody></table>`;

  // Liste der Abstimmungen zu diesem Thema
  html+=`<h4 class="themen-sec">Die Abstimmungen zu diesem Thema</h4><div class="themen-votes">`;
  votesOfTheme.slice().reverse().forEach(({s,idx,v})=>{
    const t=tallyForVote(s,idx);
    const titelHtml=s.url?`<a class="mv-link" href="${s.url}" target="_blank" rel="noopener">${v.titel||"(ohne Titel)"}</a>`:(v.titel||"(ohne Titel)");
    html+=`<div class="tv-row">
      <div class="tv-body"><div class="tv-titel">${titelHtml}</div>
        <div class="tv-meta">${s.sitzung} · ${v.typ||"Abstimmung "+v.nr}</div></div>
      <div class="tv-tally">${t.ja} Ja · ${t.nein} Nein · ${t.enth} Enth.</div>
    </div>`;
  });
  html+=`</div>`;
  box.innerHTML=html;
}

/* ===== Überblick (Startseite) ===== */
function ueberblickStats(){
  const leg = DATA.aktuelle_legislatur;
  const meta = DATA.legislaturen[String(leg)];
  const sess = DATA.sessions.filter(s => s.legislatur === leg);
  const active = new Set(meta ? meta.aktive_mitglieder : []);
  const totVotes = sess.reduce((a,s)=>a+s.n_votes,0);
  const acc={};
  sess.forEach(s=>s.members.forEach(m=>{
    const k=m.nachname+"|"+m.vorname;
    if(!active.has(k)) return;
    if(!acc[k]) acc[k]={nachname:m.nachname,vorname:m.vorname,fraktion:m.fraktion,partei:m.partei,ja:0,nein:0,enth:0,van:0,total:0};
    m.votes.forEach(v=>{const n=NV(v);acc[k][n]++;acc[k].total++;});
  }));
  return {leg, meta, sess, totVotes, mem:Object.values(acc), nMem:Object.keys(acc).length};
}
function topOf(mem, valFn, n){ return mem.slice().sort((a,b)=>valFn(b)-valFn(a)).slice(0,n); }
function renderUeberblick(){
  const {meta, sess, totVotes, mem, nMem} = ueberblickStats();
  const box=document.getElementById("ueberblickInhalt");
  const abg=it=>it.total-it.van;
  const fleissig = topOf(mem, it=>abg(it)/(it.total||1), 3);
  const jaSager  = topOf(mem, it=>it.ja/(abg(it)||1), 3);
  const abwesend = topOf(mem, it=>it.van/(it.total||1), 3);
  const teaserList = (items, fmt) => items.map((it,i)=>{
    const col=FRAK_COLORS[it.fraktion]||"#333";
    return `<li><span class="ub-rank">${i+1}</span><span class="ub-dot" style="background:${col}"></span>`+
      `<span class="ub-tname">${it.nachname} ${it.vorname}</span><span class="ub-tval">${fmt(it)}</span></li>`;
  }).join("");
  box.innerHTML=`
    <div class="ub-hero">
      <h2 class="ub-h2">Der Kantonsrat Schaffhausen in Zahlen</h2>
      <p class="ub-lead">Wie stimmen unsere 60 Ratsmitglieder ab? Diese Seite wertet alle namentlichen Abstimmungen der laufenden Amtszeit (${meta?meta.label.replace("Legislatur ab ","seit "):""}) aus, transparent und für alle nachvollziehbar.</p>
    </div>
    <div class="ub-big">
      <div class="ub-bignum"><div class="n">${nMem}</div><div class="l">Ratsmitglieder</div></div>
      <div class="ub-bignum"><div class="n">${sess.length}</div><div class="l">Sitzungen</div></div>
      <div class="ub-bignum"><div class="n">${totVotes}</div><div class="l">Abstimmungen</div></div>
      <div class="ub-bignum"><div class="n">4</div><div class="l">Fraktionen</div></div>
    </div>
    <h3 class="ub-sec">Auffälligkeiten der laufenden Amtszeit</h3>
    <p class="ub-secnote">Die drei Spitzenreiter je Kategorie. Für die vollständigen Listen zum Tab «Ranglisten» wechseln.</p>
    <div class="ub-teasers">
      <div class="ub-teaser" data-goto="rang">
        <div class="ub-thead"><span class="ub-tico" style="background:#2b5c8a">P</span>Am fleissigsten</div>
        <div class="ub-texpl">Wer war bei den meisten Abstimmungen anwesend?</div>
        <ul class="ub-tlist">${teaserList(fleissig, it=>`${(abg(it)/(it.total||1)*100).toFixed(0)}% <small>${abg(it)}/${it.total}</small>`)}</ul>
        <div class="ub-more">Ganze Rangliste ansehen →</div>
      </div>
      <div class="ub-teaser" data-goto="rang">
        <div class="ub-thead"><span class="ub-tico" style="background:#3a7d3a">J</span>Häufigste Ja-Stimmen</div>
        <div class="ub-texpl">Wer stimmt am öftesten mit «Ja»? Anteil der abgegebenen Stimmen.</div>
        <ul class="ub-tlist">${teaserList(jaSager, it=>`${(it.ja/(abg(it)||1)*100).toFixed(0)}% <small>${it.ja}/${abg(it)}</small>`)}</ul>
        <div class="ub-more">Ganze Rangliste ansehen →</div>
      </div>
      <div class="ub-teaser" data-goto="rang">
        <div class="ub-thead"><span class="ub-tico" style="background:#9a8f7d">A</span>Am häufigsten abwesend</div>
        <div class="ub-texpl">Wer fehlte anteilig am häufigsten? Bezogen auf die eigenen Sitzungen.</div>
        <ul class="ub-tlist">${teaserList(abwesend, it=>`${(it.van/(it.total||1)*100).toFixed(0)}% <small>${it.van}/${it.total}</small>`)}</ul>
        <div class="ub-more">Ganze Rangliste ansehen →</div>
      </div>
    </div>
    <h3 class="ub-sec">Wohin als Nächstes?</h3>
    <div class="ub-nav">
      <div class="ub-navcard" data-goto="mitglied"><b>Mitglied im Detail</b><span>Ein Ratsmitglied auswählen und jede einzelne Stimme sehen.</span></div>
      <div class="ub-navcard" data-goto="fraktionen"><b>Fraktionen vergleichen</b><span>Wie geschlossen stimmen die Parteien? Wer weicht ab?</span></div>
      <div class="ub-navcard" data-goto="votes"><b>Aktuelle Abstimmungen</b><span>Die neueste Sitzung und ihre Resultate im Detail.</span></div>
    </div>`;
  box.querySelectorAll("[data-goto]").forEach(el=>{
    el.style.cursor="pointer";
    el.onclick=()=>{ activateTab(el.dataset.goto); };
  });
}

/* ===== Netz der Interessenbindungen =====
   Kraftgerichtetes Layout auf Canvas, ohne Fremdbibliothek. Knoten stossen
   sich ab, Kanten ziehen zusammen, Organisationen hängen zusätzlich an ihrer
   Branche, dadurch bilden sich die Cluster. Alle Kräfte sind über Regler
   einstellbar, dazu Zoom, Verschieben und Ziehen einzelner Knoten: ohne das
   wird ein Netz mit zweihundert Knoten schnell unleserlich. */
const NETZ_FARBEN = {mitglied:"#8a1a1a", organisation:"#2b5c8a", branche:"#6b6459"};
let netzKnoten=[], netzKanten=[], netzGewaehlt=null, netzGeteiltMenge=new Set();
let netzFilterBranche="", netzFilterText="", netzNurGeteilt=false;

/* Stellschrauben, von den Reglern gesetzt */
const NP = {knoten:10, laenge:70, zug:12, abstoss:900, beschriftung:4,
            cluster:3, tiefe:2, minMandate:0};
/* Ansicht */
let netzZoom=1, netzOffX=0, netzOffY=0;
/* Bewegung: alpha kühlt ab, bei Änderungen wird neu aufgeheizt */
let netzAlpha=0, netzLaeuft=false, netzZieht=null;

function netzHeizen(a=1){ netzAlpha=Math.max(netzAlpha,a); netzSchleife(); }

function netzSchleife(){
  if(netzLaeuft) return;
  netzLaeuft=true;
  const takt=()=>{
    if(netzAlpha>0.005 || netzZieht){
      netzSchritt();
      netzAlpha*=0.985;
      netzMalen();
      requestAnimationFrame(takt);
    } else {
      netzLaeuft=false;
      netzMalen();
    }
  };
  requestAnimationFrame(takt);
}

function netzAufbauen(behalten=true){
  const canvas=document.getElementById("netz");
  if(!canvas || !(NETZ.knoten||[]).length) return;
  const proOrg={};
  (NETZ.kanten||[]).filter(k=>k.art!=="branche").forEach(k=>{
    (proOrg[k.nach]=proOrg[k.nach]||new Set()).add(k.von);
  });
  netzGeteiltMenge=new Set(Object.entries(proOrg).filter(([,ms])=>ms.size>1).map(([oid])=>oid));

  const passtOrg=o=>{
    if(netzFilterBranche && o.branche!==netzFilterBranche) return false;
    if(netzNurGeteilt && !netzGeteiltMenge.has(o.id)) return false;
    return true;
  };
  // Personen nach Anzahl ihrer Mandate filtern. Danach bleiben nur die
  // Organisationen übrig, an denen noch mindestens eine sichtbare Person hängt,
  // sonst stünden lauter Organisationen ohne Anschluss im Bild.
  const passtMit=m=>(m.anzahl||0) >= NP.minMandate;
  const kandidatMit=new Set((NETZ.knoten||[]).filter(k=>k.typ==="mitglied"&&passtMit(k)).map(k=>k.id));
  const kandidatOrg=new Set((NETZ.knoten||[]).filter(k=>k.typ==="organisation"&&passtOrg(k)).map(k=>k.id));

  const sichtbarOrg=new Set(), sichtbarMit=new Set();
  (NETZ.kanten||[]).filter(k=>k.art!=="branche").forEach(k=>{
    if(kandidatOrg.has(k.nach) && kandidatMit.has(k.von)){
      sichtbarOrg.add(k.nach); sichtbarMit.add(k.von);
    }
  });
  const branchenVon={}; (NETZ.knoten||[]).forEach(k=>{ if(k.typ==="organisation") branchenVon[k.id]="b:"+k.branche; });
  const sichtbarBra=new Set([...sichtbarOrg].map(id=>branchenVon[id]));

  const alt={}; if(behalten) netzKnoten.forEach(n=>alt[n.id]=n);
  netzKnoten=(NETZ.knoten||[]).filter(k=>
      (k.typ==="organisation"&&sichtbarOrg.has(k.id)) ||
      (k.typ==="mitglied"&&sichtbarMit.has(k.id)) ||
      (k.typ==="branche"&&sichtbarBra.has(k.id)))
    .map(k=>{
      const v=alt[k.id];
      return {...k, x:v?v.x:(Math.random()*600-300), y:v?v.y:(Math.random()*400-200), vx:0, vy:0};
    });
  const id2=Object.fromEntries(netzKnoten.map(n=>[n.id,n]));
  netzKanten=(NETZ.kanten||[]).filter(k=>id2[k.von]&&id2[k.nach])
    .map(k=>({...k, a:id2[k.von], b:id2[k.nach]}));
  netzTreffer();
  netzInfoLeer();
  netzHeizen(1);
}

function netzRadius(n){
  const grund = n.typ==="branche" ? 1.4 : (n.typ==="mitglied" ? 1 : 0.75);
  return (NP.knoten*0.55)*grund + Math.min(n.anzahl,8)*(NP.knoten*0.055) + 2;
}

function netzTreffer(){
  const q=netzFilterText.trim().toLowerCase();
  netzKnoten.forEach(n=>{ n.treffer = q ? n.label.toLowerCase().includes(q) : false; });
}

function netzSchritt(){
  const N=netzKnoten.length; if(!N) return;
  const alpha=Math.max(netzAlpha,0.08);
  for(let i=0;i<N;i++){
    const a=netzKnoten[i];
    for(let j=i+1;j<N;j++){
      const b=netzKnoten[j];
      let dx=b.x-a.x, dy=b.y-a.y, d2=dx*dx+dy*dy;
      if(d2<1){ dx=Math.random()-0.5; dy=Math.random()-0.5; d2=1; }
      if(d2>250000) continue;
      // Branchen stossen sich untereinander viel stärker ab, damit die Cluster
      // auseinanderrücken statt sich zu überlagern
      const beide = a.typ==="branche" && b.typ==="branche";
      const staerke = NP.abstoss * (beide ? NP.cluster*NP.cluster : 1);
      const kraft=staerke/d2, d=Math.sqrt(d2);
      const fx=kraft*dx/d, fy=kraft*dy/d;
      a.vx-=fx; a.vy-=fy; b.vx+=fx; b.vy+=fy;
    }
  }
  netzKanten.forEach(k=>{
    // Kanten zur Branche sind kürzer und ziehen stärker: das hält eine Branche
    // mit ihren Organisationen zusammen
    const zurBranche = k.art==="branche";
    const soll = zurBranche ? NP.laenge*0.45 : NP.laenge;
    const dx=k.b.x-k.a.x, dy=k.b.y-k.a.y, d=Math.hypot(dx,dy)||1;
    const kraft=(d-soll)*(NP.zug/1000)*(zurBranche ? NP.cluster : 1);
    const fx=kraft*dx/d, fy=kraft*dy/d;
    k.a.vx+=fx; k.a.vy+=fy; k.b.vx-=fx; k.b.vy-=fy;
  });
  netzKnoten.forEach(n=>{
    if(netzZieht && netzZieht.knoten===n){ n.vx=0; n.vy=0; return; }
    n.vx-=n.x*0.0018; n.vy-=n.y*0.0018;
    n.vx*=0.86; n.vy*=0.86;
    n.x+=n.vx*alpha*2; n.y+=n.vy*alpha*2;
  });
}

/* Bildschirm- und Weltkoordinaten */
function netzMasse(){
  const c=document.getElementById("netz");
  const b=c.getBoundingClientRect();
  return {c,b};
}
function zuWelt(sx,sy){
  const {b}=netzMasse();
  return {x:(sx-b.width/2-netzOffX)/netzZoom, y:(sy-b.height/2-netzOffY)/netzZoom};
}

function netzMalen(){
  const c=document.getElementById("netz"); if(!c) return;
  const g=c.getContext && c.getContext("2d");
  if(!g) return;                      // Umgebungen ohne Canvas (z. B. Tests)
  const dpr=window.devicePixelRatio||1;
  const b=c.getBoundingClientRect();
  if(c.width!==Math.round(b.width*dpr)||c.height!==Math.round(b.height*dpr)){
    c.width=Math.round(b.width*dpr); c.height=Math.round(b.height*dpr);
  }
  g.setTransform(dpr,0,0,dpr,0,0);
  g.clearRect(0,0,b.width,b.height);
  g.save();
  g.translate(b.width/2+netzOffX, b.height/2+netzOffY);
  g.scale(netzZoom, netzZoom);

  const q=netzFilterText.trim().length>0;
  const hervor = netzGewaehlt ? pfadVon(netzGewaehlt, NP.tiefe) : null;

  netzKanten.forEach(k=>{
    const an = !hervor || (hervor.has(k.von)&&hervor.has(k.nach));
    g.strokeStyle = k.art==="branche" ? (an?"#e2ddd3":"#f4f2ed") : (an?"#c4bbaa":"#efece6");
    g.lineWidth = (k.art==="branche" ? 0.7 : 1)/Math.max(netzZoom,0.6);
    g.beginPath(); g.moveTo(k.a.x,k.a.y); g.lineTo(k.b.x,k.b.y); g.stroke();
  });
  netzKnoten.forEach(n=>{
    const an = !hervor || hervor.has(n.id);
    const treffer = q && n.treffer;
    const r=netzRadius(n);
    g.globalAlpha = an ? 1 : 0.16;
    g.fillStyle = treffer ? "#e0a800" : NETZ_FARBEN[n.typ];
    g.beginPath(); g.arc(n.x,n.y,r,0,Math.PI*2); g.fill();
    if(netzGewaehlt && n.id===netzGewaehlt.id){
      g.strokeStyle="#1a1a1a"; g.lineWidth=2/netzZoom; g.stroke();
    }
    // Regler auf 0 heisst: alle beschriften
    const zeigen = n.typ==="branche" || treffer || (hervor&&hervor.has(n.id)) ||
                   NP.beschriftung===0 || n.anzahl>=NP.beschriftung;
    if(zeigen){
      g.globalAlpha = an ? 1 : 0.25;
      g.fillStyle="#1a1a1a";
      const gr = (n.typ==="branche" ? 12 : 11)/Math.max(netzZoom,0.75);
      g.font = n.typ==="branche" ? `600 ${gr}px Georgia, serif` : `${gr}px sans-serif`;
      g.textAlign="center";
      g.fillText(n.label.slice(0,38), n.x, n.y - r - 4/netzZoom);
    }
  });
  g.globalAlpha=1;
  g.restore();
}

/* Alle Knoten, die vom gewählten aus in höchstens `tiefe` Schritten erreichbar
   sind. Ein Klick auf ein Ratsmitglied zeigt damit nicht nur seine Mandate,
   sondern auch deren Branchen und die übrigen Mitglieder derselben
   Organisation; von einer Branche aus geht es entsprechend abwärts. */
function pfadVon(start, tiefe){
  const nachbarn={};
  netzKanten.forEach(k=>{
    (nachbarn[k.von]=nachbarn[k.von]||[]).push(k.nach);
    (nachbarn[k.nach]=nachbarn[k.nach]||[]).push(k.von);
  });
  const gesehen=new Set([start.id]);
  let rand=[start.id];
  for(let i=0;i<Math.max(1,tiefe);i++){
    const naechste=[];
    rand.forEach(id=>(nachbarn[id]||[]).forEach(n=>{
      if(!gesehen.has(n)){ gesehen.add(n); naechste.push(n); }
    }));
    rand=naechste;
    if(!rand.length) break;
  }
  return gesehen;
}

function netzInfoLeer(){
  const box=document.getElementById("netzInfo"); if(!box) return;
  const m=netzKnoten.filter(n=>n.typ==="mitglied").length;
  const o=netzKnoten.filter(n=>n.typ==="organisation").length;
  box.innerHTML=`<div class="ni-typ">Übersicht</div>
    <h4>${o} Organisationen</h4>
    <p><small>${m} Ratsmitglieder, ${netzKanten.filter(k=>k.art!=="branche").length} Mandate.
    ${netzGeteiltMenge.size} Organisationen werden von mehr als einem Ratsmitglied genannt.</small></p>
    ${NP.minMandate>0?`<p><small>Gezeigt werden nur Ratsmitglieder mit mindestens
      ${NP.minMandate} Interessenbindungen.</small></p>`:""}
    <p style="margin-top:9px"><small>Punkt anklicken zeigt die Verbindungen, Punkt ziehen ordnet um,
    Mausrad zoomt, Ziehen im leeren Bereich verschiebt.</small></p>`;
}

/* Angaben aus dem Handelsregister zu einer Organisation.
   Quelle: Zefix (Eidgenössisches Amt für das Handelsregister), abgefragt über
   lindas.admin.ch. Die Zuordnung erfolgt über einen Namensabgleich, ist also
   eine Aufbereitung und keine amtliche Auskunft. */
const HREG_INDEX = {};
["eindeutig","moeglich","nicht_gefunden"].forEach(stufe=>{
  (HREG[stufe]||[]).forEach(e=>{ HREG_INDEX[e.organisation]={...e, stufe}; });
});
function registerBlock(label){
  const e=HREG_INDEX[label];
  if(!e) return "";
  const stand=HREG.stand?` · Stand ${esc(HREG.stand)}`:"";
  if(e.stufe==="nicht_gefunden"){
    return `<div class="ni-hreg offen"><b>Handelsregister</b> kein Eintrag gefunden.
      Das ist kein Beleg dafür, dass es die Organisation nicht gibt: Schreibweise,
      Umbenennung oder Löschung sind die häufigsten Gründe.
      <small>Zefix${stand}</small></div>`;
  }
  const t=e.treffer[0];
  const uid=t.uid ? ` · ${esc(t.uid.replace(/^CHE(\d{3})(\d{3})(\d{3})$/,"CHE-$1.$2.$3"))}` : "";
  const weitere = e.treffer.length>1
    ? `<br><small>${e.treffer.length-1} weitere mögliche Treffer</small>` : "";
  return `<div class="ni-hreg ${e.stufe}"><b>Handelsregister</b>
    ${e.stufe==="eindeutig" ? "" : "möglicher Treffer: "}${esc(t.name)}${t.ort?", "+esc(t.ort):""}${uid}${weitere}
    <small>Zefix${stand}, über Namensabgleich zugeordnet. Verbindlich sind allein der
    beglaubigte Registerauszug und der Publikationstext im SHAB.</small></div>`;
}

function netzInfoZeigen(n){
  const box=document.getElementById("netzInfo"); if(!box) return;
  const eigene=netzKanten.filter(k=>k.von===n.id||k.nach===n.id);
  const zeilen=eigene.filter(k=>k.art!=="branche").map(k=>{
    const anderer = k.von===n.id ? k.b : k.a;
    const rolle = k.rolle ? ` <small>${esc(k.rolle)}</small>` : "";
    return `<li>${esc(anderer.label)}${rolle}</li>`;
  }).join("");
  const typ={mitglied:"Ratsmitglied", organisation:"Organisation", branche:"Branche"}[n.typ];
  const zusatz = n.typ==="mitglied" ? `<p><small>${esc(n.partei||"")}${n.fraktion?" · "+esc(n.fraktion):""}</small></p>`
               : n.typ==="organisation" ? `<p><small>${esc(n.branche||"")}${n.ort?" · "+esc(n.ort):""}</small></p>` : "";
  const pfad=pfadVon(n, NP.tiefe);
  const nach={}; netzKnoten.forEach(k=>nach[k.id]=k);
  const zaehlung=[...pfad].filter(id=>id!==n.id).map(id=>nach[id]).filter(Boolean);
  const stat=["mitglied","organisation","branche"].map(tp=>{
    const c=zaehlung.filter(k=>k.typ===tp).length;
    return c ? `${c} ${({mitglied:"Ratsmitglieder", organisation:"Organisationen", branche:"Branchen"})[tp]}` : null;
  }).filter(Boolean).join(", ");
  box.innerHTML=`<div class="ni-typ">${typ}</div><h4>${esc(n.label)}</h4>${zusatz}
    ${n.typ==="organisation" ? registerBlock(n.label) : ""}
    ${zeilen?`<ul>${zeilen}</ul>`:"<p><small>Keine Mandate erfasst.</small></p>"}
    ${stat?`<p style="margin-top:9px"><small>Im Pfad über ${NP.tiefe} Schritte: ${stat}.</small></p>`:""}`;
}

function knotenBei(sx,sy){
  const w=zuWelt(sx,sy);
  let beste=null, dist=1e9;
  netzKnoten.forEach(n=>{
    const d=Math.hypot(n.x-w.x,n.y-w.y);
    const grenze=Math.max(netzRadius(n)+6, 12/netzZoom);
    if(d<grenze && d<dist){ dist=d; beste=n; }
  });
  return beste;
}

function zoomSetzen(faktor, sx, sy){
  const {b}=netzMasse();
  const mx = sx!==undefined ? sx : b.width/2;
  const my = sy!==undefined ? sy : b.height/2;
  const vor=zuWelt(mx,my);
  netzZoom=Math.min(4, Math.max(0.25, netzZoom*faktor));
  const nach=zuWelt(mx,my);
  netzOffX += (nach.x-vor.x)*netzZoom;
  netzOffY += (nach.y-vor.y)*netzZoom;
  const a=document.getElementById("zoomWert");
  if(a) a.textContent=Math.round(netzZoom*100)+" %";
  netzMalen();
}

function initNetz(){
  const c=document.getElementById("netz"); if(!c) return;

  const sel=document.getElementById("netzBranche");
  [...new Set((NETZ.knoten||[]).filter(k=>k.typ==="branche").map(k=>k.label))].sort()
    .forEach(b=>{ const o=document.createElement("option"); o.value=b; o.textContent=b; sel.appendChild(o); });
  sel.onchange=()=>{ netzFilterBranche=sel.value; netzGewaehlt=null; netzAufbauen(); };

  const feld=document.getElementById("netzSuche");
  let t=null;
  feld.oninput=()=>{ clearTimeout(t); t=setTimeout(()=>{ netzFilterText=feld.value; netzTreffer(); netzMalen(); },180); };

  const gt=document.getElementById("netzGeteilt");
  gt.onchange=()=>{ netzNurGeteilt=gt.checked;
    document.getElementById("netzGeteiltWrap").classList.toggle("an", gt.checked);
    netzGewaehlt=null; netzAufbauen(); };

  document.getElementById("netzReset").onclick=()=>{
    netzFilterBranche=""; netzFilterText=""; netzNurGeteilt=false; netzGewaehlt=null;
    NP.minMandate=0;
    const rmm=document.getElementById("rMandate");
    if(rmm){ rmm.value=0; const w=document.getElementById("rMandateWert"); if(w) w.textContent="alle"; }
    sel.value=""; feld.value=""; gt.checked=false;
    document.getElementById("netzGeteiltWrap").classList.remove("an");
    netzZoom=1; netzOffX=0; netzOffY=0; zoomSetzen(1);
    netzAufbauen(false);
  };

  /* Regler */
  const rm=document.getElementById("rMandate");
  if(rm){
    const maxMandate=Math.max(...(NETZ.knoten||[]).filter(k=>k.typ==="mitglied").map(k=>k.anzahl||0), 1);
    rm.max=maxMandate;
  }
  const regler=[
    ["rKnoten","knoten", v=>v+" px"],
    ["rLaenge","laenge", v=>v+" px"],
    ["rZug","zug", v=>v],
    ["rAbstoss","abstoss", v=>v],
    ["rBeschriftung","beschriftung", v=>v==0?"alle":"ab "+v+" Verb."],
    ["rCluster","cluster", v=>v+"x"],
    ["rTiefe","tiefe", v=>v+" Schritte"],
    ["rMandate","minMandate", v=>v==0?"alle":"ab "+v],
  ];
  regler.forEach(([id,feldname,fmt])=>{
    const el=document.getElementById(id); if(!el) return;
    el.value=NP[feldname];
    const aus=document.getElementById(id+"Wert");
    const zeigen=()=>{ if(aus) aus.textContent=fmt(el.value); };
    zeigen();
    el.oninput=()=>{
      NP[feldname]=+el.value; zeigen();
      if(feldname==="knoten"||feldname==="beschriftung"){ netzMalen(); }
      else if(feldname==="tiefe"){
        if(netzGewaehlt) netzInfoZeigen(netzGewaehlt);
        netzMalen();
      } else if(feldname==="minMandate"){
        netzGewaehlt=null; netzAufbauen();
      } else { netzHeizen(0.6); }
    };
  });
  const neu=document.getElementById("netzNeu");
  if(neu) neu.onclick=()=>netzAufbauen(false);

  /* Zoom */
  document.getElementById("zoomEin").onclick=()=>zoomSetzen(1.25);
  document.getElementById("zoomAus").onclick=()=>zoomSetzen(0.8);
  document.getElementById("zoomWert").onclick=()=>{ netzZoom=1; netzOffX=0; netzOffY=0; zoomSetzen(1); };
  c.addEventListener("wheel",(e)=>{
    e.preventDefault();
    const b=c.getBoundingClientRect();
    zoomSetzen(e.deltaY<0?1.12:0.89, e.clientX-b.left, e.clientY-b.top);
  }, {passive:false});

  /* Ziehen: Knoten verschieben, im leeren Bereich die ganze Ansicht */
  let schieben=null, bewegt=false;
  c.addEventListener("pointerdown",(e)=>{
    const b=c.getBoundingClientRect();
    const sx=e.clientX-b.left, sy=e.clientY-b.top;
    const n=knotenBei(sx,sy);
    bewegt=false;
    if(n){ netzZieht={knoten:n}; netzHeizen(0.5); }
    else { schieben={x:e.clientX, y:e.clientY, ox:netzOffX, oy:netzOffY}; }
    c.setPointerCapture(e.pointerId);
  });
  c.addEventListener("pointermove",(e)=>{
    const b=c.getBoundingClientRect();
    if(netzZieht){
      bewegt=true;
      const w=zuWelt(e.clientX-b.left, e.clientY-b.top);
      netzZieht.knoten.x=w.x; netzZieht.knoten.y=w.y;
      netzMalen();
    } else if(schieben){
      const dx=e.clientX-schieben.x, dy=e.clientY-schieben.y;
      if(Math.abs(dx)+Math.abs(dy)>3) bewegt=true;
      netzOffX=schieben.ox+dx; netzOffY=schieben.oy+dy;
      netzMalen();
    }
  });
  const loslassen=(e)=>{
    if(netzZieht){ netzZieht=null; netzHeizen(0.3); }
    schieben=null;
    try{ c.releasePointerCapture(e.pointerId); }catch(_e){}
  };
  c.addEventListener("pointerup",(e)=>{
    const b=c.getBoundingClientRect();
    if(!bewegt){
      const n=knotenBei(e.clientX-b.left, e.clientY-b.top);
      netzGewaehlt = (n && netzGewaehlt && n.id===netzGewaehlt.id) ? null : n;
      if(netzGewaehlt) netzInfoZeigen(netzGewaehlt); else netzInfoLeer();
    }
    loslassen(e);
    netzMalen();
  });
  c.addEventListener("pointercancel", loslassen);

  const leg=document.getElementById("netzLegende");
  leg.innerHTML=Object.entries({Ratsmitglied:NETZ_FARBEN.mitglied, Organisation:NETZ_FARBEN.organisation, Branche:NETZ_FARBEN.branche})
    .map(([k,v])=>`<span><i style="background:${v}"></i>${k}</span>`).join("")
    + `<span><i style="background:#e0a800"></i>Suchtreffer</span>`;
  netzAufbauen(false);
}

function renderSession(){
  const lbl=document.getElementById("sitzungLabel");
  if(lbl) lbl.textContent =
    S().sitzung+" · "+S().votes.length+" Abstimmungen, "+S().members.length+" Ratsmitglieder.";
  renderVotes(); initMemberControls(); renderMembers();
}
fuelleLegislaturen(); fuelleSitzungen(); initVoteFilter();
initRankScope(); renderRang(); initMitglied(); initThemen(); initSpiderScope(); renderSession(); renderFrakTab(); renderUeberblick();
try{ initNetz(); }catch(e){ console.error("Netz konnte nicht aufgebaut werden:", e); }
'''

HTML = '''<!DOCTYPE html>
<html lang="de"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Kantonsrat Schaffhausen · Kantonsratsspiegel</title>
<style>__CSS__</style>
</head><body>
<div class="wrap">
<header class="masthead">
  <div class="eyebrow">Abstimmungstransparenz</div>
  <h1>Kantonsrat Schaffhausen</h1>
  <div class="sub">Alle namentlichen Abstimmungen, transparent aufbereitet.</div>
</header>
<div class="nav-select-wrap">
  <select class="nav-select" id="navSelect" aria-label="Ansicht wählen">
    <option value="ueberblick">Überblick</option>
    <option value="rang">Ranglisten</option>
    <option value="mitglied">Mitglied im Detail</option>
    <option value="themen">Themen</option>
    <option value="fraktionen">Fraktionen</option>
    <option value="interessen">Interessenbindungen</option>
    <optgroup label="Kantonsratssitzungen">
      <option value="votes">Abstimmungen</option>
      <option value="profile">Ratsmitglieder</option>
    </optgroup>
  </select>
</div>
<nav class="tabs">
  <button class="active" data-tab="ueberblick">Überblick</button>
  <button data-tab="rang">Ranglisten</button>
  <button data-tab="mitglied">Mitglied im Detail</button>
  <button data-tab="themen">Themen</button>
  <button data-tab="fraktionen">Fraktionen</button>
  <button data-tab="interessen">Interessenbindungen</button>
  <div class="tabs-dd" id="sessDd">
    <button type="button" id="sessDdBtn" aria-haspopup="true" aria-expanded="false">
      <span id="sessDdLabel">Kantonsratssitzungen</span><span class="caret">▾</span>
    </button>
    <div class="dd-menu" role="menu">
      <button data-tab="votes" role="menuitem">Abstimmungen<small>Jede Abstimmung der Sitzung, mit Namenslisten</small></button>
      <button data-tab="profile" role="menuitem">Ratsmitglieder<small>Alle 60 Mitglieder und ihr Stimmverhalten</small></button>
    </div>
  </div>
</nav>
<div class="sess-bar" id="sessScope" style="display:none">
  <label class="modus-schalter" id="modusWrap">
    <input type="checkbox" id="modusSuche">
    <span>Über alle Sitzungen suchen</span>
  </label>
  <label for="sessLeg">Legislatur</label>
  <select id="sessLeg"></select>
  <span id="sessSelWrap"><label for="sessSel">Sitzung</label>
  <select id="sessSel"></select></span>
</div>

<section class="panel active" id="tab-ueberblick">
  <div id="ueberblickInhalt"></div>
</section>

<section class="panel" id="tab-votes">
  <h2 class="section" id="votesTitel">Alle Abstimmungen dieser Sitzung</h2>
  <div class="section-note">Jede namentliche Abstimmung mit Resultat. Ja (grün), Nein (rot), Enthaltung (grau), Abwesenheit (hell). «Wer hat wie gestimmt?» klappt die Namen aller 60 Ratsmitglieder auf. Oben umschalten: eine einzelne Sitzung ansehen, oder über alle Sitzungen suchen, wahlweise eingegrenzt auf eine Legislatur.</div>
  <div class="vfilter">
    <div class="vfilter-row">
      <label for="vSuche">Suche</label>
      <input type="text" id="vSuche" placeholder="Stichwort, z. B. Steuerfuss, Spital, Kita …" autocomplete="off">
      <select id="vForm"><option value="">Alle Formen</option></select>
      <button class="vf-reset" id="vReset" type="button">zurücksetzen</button>
      <span class="vf-treffer" id="vTreffer"></span>
    </div>
    <div class="vfilter-row"><label>Thema</label><div class="tagzeile" id="tagOber"></div></div>
    <div class="vfilter-row" id="tagUnterRow" style="display:none"><div class="tagzeile ebene2" id="tagUnter"></div></div>
    <div class="vfilter-row" id="tagDetailRow" style="display:none"><div class="tagzeile ebene3" id="tagDetail"></div></div>
  </div>
  <div id="voteList"></div>
</section>
<section class="panel" id="tab-themen">
  <h2 class="section">Abstimmungen nach Thema</h2>
  <div class="section-note">Ein Thema wählen und sehen, wie der Rat und die einzelnen Mitglieder dazu gestimmt haben. Themen orientieren sich an den 9 Hauptgruppen der Schaffhauser Rechtssammlung. Rein deskriptiv, ohne Wertung.</div>
  <div class="filter-bar"><select id="tLeg"></select></div>
  <div id="themenChips" class="themen-chips"></div>
  <div id="themenInhalt"></div>
</section>

<section class="panel" id="tab-fraktionen">
  <h2 class="section">Abstimmungsverhalten der Fraktionen</h2>
  <div class="section-note">Ja-Quote, Enthaltungen, Präsenz und Geschlossenheit (Fraktionsdisziplin), darunter dieselben Kennzahlen als Profil im direkten Vergleich. Nach Legislatur oder einzelner Sitzung.</div>
  <div class="rank-intro"><select class="rank-scope" id="frakScopeSel"></select></div>
  <div class="section-note" id="frakScopeMeta" style="margin:-8px 0 16px"></div>
  <div class="frak-grid" id="frakGrid"></div>
  <h2 class="section" style="font-size:18px;margin-top:38px">Fraktionsprofil im Vergleich</h2>
  <div class="section-note">Gemitteltes Abstimmungsverhalten je Fraktion über fünf Kennzahlen.</div>
  <div class="disclaimer"><b>Lesehinweis:</b> Diese Achsen beschreiben <i>Verhaltensmuster</i> (Zustimmungsneigung, Geschlossenheit), nicht die politische Ausrichtung. Eine inhaltliche Links-Rechts-Einordnung würde eine redaktionelle Bewertung jeder Vorlage erfordern und ist bewusst noch nicht enthalten.</div>
  <div class="spider-wrap"><div><svg id="spider" width="470" height="380" viewBox="-45 0 470 380"></svg></div><div class="spider-controls" id="spiderToggles"></div></div>
</section>
<section class="panel" id="tab-profile">
  <h2 class="section">Einzelne Ratsmitglieder</h2>
  <div class="section-note">Filtern nach Fraktion, suchen nach Name. Klick auf Spaltentitel sortiert. Jedes Farbfeld ist eine Abstimmung: darüberfahren zeigt die Frage, ein Klick springt zur Abstimmung.</div>
  <div class="filter-bar"><select id="fFrak"></select><input id="fSearch" type="text" placeholder="Name suchen…"></div>
  <div class="legend-dots"><span><i class="vd-ja"></i>Ja</span><span><i class="vd-nein"></i>Nein</span><span><i class="vd-enth"></i>Enthaltung</span><span><i class="vd-van"></i>abwesend</span></div>
  <table class="member-table"><thead><tr>
    <th data-sort="name">Name</th><th data-sort="fraktion" class="hide-sm">Fraktion</th>
    <th data-sort="ja">Ja-Quote</th><th class="hide-sm">Stimmen</th>
  </tr></thead><tbody id="memberBody"></tbody></table>
</section>
<section class="panel" id="tab-mitglied">
  <h2 class="section">Mitglied im Detail</h2>
  <div class="section-note">Ein Ratsmitglied auswählen und sehen, wie es über die gewählte Legislatur bei jeder Vorlage gestimmt hat, mit persönlicher Statistik.</div>
  <div class="filter-bar">
    <select id="mLeg"></select>
    <select id="mMember"></select>
  </div>
  <div id="mProfile"></div>
</section>

<section class="panel" id="tab-interessen">
  <h2 class="section">Interessenbindungen im Netz</h2>
  <div class="section-note">Wer sitzt wo? Jeder Punkt ist ein Ratsmitglied, eine Organisation oder eine Branche. Eine Linie bedeutet ein deklariertes Mandat. Organisationen, die mehrere Ratsmitglieder nennen, rücken zwischen diese. Quelle der Mandate sind ausschliesslich die Selbstdeklarationen auf sh.ch, ohne eigene Zuschreibungen. Bei Organisationen mit Rechtsform kommt beim Anklicken die Angabe aus dem Handelsregister dazu (Zefix, Eidgenössisches Amt für das Handelsregister).</div>
  <div class="netz-leiste">
    <select id="netzBranche"><option value="">Alle Branchen</option></select>
    <input type="text" id="netzSuche" placeholder="Person oder Organisation suchen…" autocomplete="off">
    <label class="modus-schalter" id="netzGeteiltWrap"><input type="checkbox" id="netzGeteilt"><span>Nur geteilte Organisationen</span></label>
    <button class="vf-reset" type="button" id="netzReset">zurücksetzen</button>
    <span class="netz-zoom">
      <button type="button" id="zoomAus" title="kleiner">&minus;</button>
      <button type="button" id="zoomWert" title="auf 100 % zurücksetzen">100 %</button>
      <button type="button" id="zoomEin" title="grösser">+</button>
    </span>
  </div>
  <div class="netz-regler">
    <label>Knotengrösse <input type="range" id="rKnoten" min="4" max="26" step="1"><output id="rKnotenWert"></output></label>
    <label>Verbindungslänge <input type="range" id="rLaenge" min="30" max="240" step="5"><output id="rLaengeWert"></output></label>
    <label>Anziehung <input type="range" id="rZug" min="2" max="60" step="1"><output id="rZugWert"></output></label>
    <label>Abstossung <input type="range" id="rAbstoss" min="200" max="4000" step="50"><output id="rAbstossWert"></output></label>
    <label>Beschriftung <input type="range" id="rBeschriftung" min="0" max="12" step="1"><output id="rBeschriftungWert"></output></label>
    <label>Clusterstärke <input type="range" id="rCluster" min="1" max="8" step="0.5"><output id="rClusterWert"></output></label>
    <label>Pfadtiefe <input type="range" id="rTiefe" min="1" max="4" step="1"><output id="rTiefeWert"></output></label>
    <label>Mandate je Person <input type="range" id="rMandate" min="0" max="10" step="1"><output id="rMandateWert"></output></label>
    <button class="vf-reset" type="button" id="netzNeu">neu anordnen</button>
  </div>
  <div class="netz-wrap">
    <canvas id="netz"></canvas>
    <div class="netz-info" id="netzInfo"></div>
  </div>
  <div class="netz-legende" id="netzLegende"></div>
</section>
<section class="panel" id="tab-rang">
  <h2 class="section">Ranglisten</h2>
  <div class="section-note">Wer stimmt wie? Nach Legislatur oder einzelner Sitzung. Es werden nur amtierende Ratsmitglieder gezeigt; Präsenz und Quoten zählen relativ zu den Sitzungen seit Amtsantritt der jeweiligen Person. Jeweils Top 8.</div>
  <div class="rank-intro"><select class="rank-scope" id="rankScopeSel"></select></div>
  <div class="section-note" id="rankMeta" style="margin:-8px 0 16px"></div>
  <div class="disclaimer"><b>Hinweis:</b> Ja-, Nein- und Enthaltungs-Quoten beziehen sich auf die abgegebenen Stimmen (ohne Abwesenheiten). Umkehrabstimmungen sind hier nicht richtungskorrigiert, ein «Nein» kann inhaltlich Zustimmung zu einem Minderheitsantrag bedeuten.</div>
  <h2 class="section" style="font-size:18px;margin-top:10px">Ratsmitglieder</h2>
  <div class="rank-grid" id="rankMembers"></div>
  <h2 class="section" style="font-size:18px;margin-top:34px">Parteien</h2>
  <div class="rank-grid" id="rankParties"></div>
</section>

<footer class="foot">
  <b>Datenquellen:</b> Kanton Schaffhausen, namentliche Abstimmungen des Kantonsrats (Excel-Publikation der Parlamentsdienste), Wortprotokolle und Mitgliederangaben von sh.ch; Handelsregisterangaben aus Zefix des Eidgenössischen Amts für das Handelsregister, über lindas.admin.ch abgefragt und für die Darstellung über einen Namensabgleich zugeordnet, also aufbereitet und ohne Gewähr. Verbindlich sind allein der beglaubigte Registerauszug und der Publikationstext im SHAB. <b>Prototyp</b> · Aufbereitung ohne Gewähr. Aggregierte Kennzahlen sind noch nicht für Umkehrabstimmungen richtungskorrigiert.
</footer>
</div>
<script>__JS__</script>
</body></html>'''

out = HTML.replace("__CSS__", CSS).replace(
    "__JS__", JS.replace("__DATA__", data_str)
                .replace("__MITGLIEDER__", mitglieder_str)
                .replace("__NETZ__", netz_str)
                .replace("__PRUEFUNG__", pruefung_str))
open(OUTPUT / "kantonsrat-dashboard.html","w").write(out)
print("written",len(out),"chars")

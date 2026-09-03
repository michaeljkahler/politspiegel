#!/usr/bin/env python3
"""Baut die Uebersichtsseite «Politspiegel Schaffhausen».

Aufruf aus der Projektwurzel:
    python3 politspiegel/bauen.py

Liest    politspiegel/politspiegel.json              Titel, Untertitel, Kantonsratskasten
         abstimmungsspiegel/abstimmungen/*/vorlage.json  je Abstimmung Titel, Datum, Stand, Ergebnis
         data/all_sessions.json                       Kennzahlen des Kantonsratsspiegels
Schreibt site/index.html            die Uebersicht, zwei Kaesten
         site/abstimmung/index.html alle Abstimmungen: aktuell, kommend, vergangen
         site/dashboard.html        Weiterleitung auf kantonsrat/

Warum eine eigene Ebene: Der Kantonsratsspiegel ist 2,7 MB, die Abstimmungsseite
400 kB. Beides in eine Datei zu legen hiesse, jedem Besucher alles zu schicken,
auch wenn er nur eine Frage hat. Und jede neue Abstimmung wuerde die Datei
weiter aufblaehen. Die Uebersicht hier bleibt unter 10 kB, kommt ohne Skript und
ohne fremde Ressourcen aus und laedt in jedem Netz sofort.

Der Preis ist ein Klick mehr. Dafuer bleibt jede Seite fuer sich vollstaendig
und nach Jahren noch erreichbar, auch wenn die naechste ganz anders aussieht.

Warum die Abstimmungen aus den Vorlagen gelesen werden und nicht aus einer
Liste: Bis zum 3. September 2026 standen die Kaesten samt Kennzahlen von Hand
in einer JSON-Datei. Von Hand gepflegte Zahlen auf einer Uebersichtsseite
veralten unbemerkt, und zwar genau dann, wenn die Seite darunter aktuell ist.
Jetzt entscheidet der Abstimmungsordner: liegt dort eine vorlage.json und ist
die Seite gebaut, erscheint die Abstimmung.

Warum ein Kasten fuer alle Abstimmungen und nicht einer je Abstimmung: Mit
jeder Vorlage kaeme ein Kasten dazu, und nach zwei Jahren waere die Uebersicht
eine Halde. Darum stehen auf der Startseite genau zwei Kaesten, einer je
Angebot. Der Abstimmungskasten nennt die naechste Abstimmung, und ein
Aufklappfeld darin fuehrt zu jeder einzelnen: aktuell, kommend, vergangen. Die
vollstaendige Liste mit Ergebnissen liegt unter abstimmung/. Nichts wird
geloescht: eine alte Abstimmung bleibt unter ihrer Adresse erreichbar.
"""

from __future__ import annotations

import html
import json
import sys
from datetime import date
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
QUELLE = WURZEL / "politspiegel" / "politspiegel.json"
VORLAGEN = WURZEL / "abstimmungsspiegel" / "abstimmungen"
SITE = WURZEL / "site"
SITZUNGEN = WURZEL / "data" / "all_sessions.json"

BESCHREIBUNG = ("Politspiegel Schaffhausen: wie der Kantonsrat abstimmt, und "
                "was bei der naechsten kantonalen Abstimmung auf dem Zettel "
                "steht. Mit Quellen, offen hergeleitet.")

MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
          "September", "Oktober", "November", "Dezember"]


def e(t) -> str:
    return html.escape(str(t), quote=True)


def datum_lang(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.day}. {MONATE[d.month - 1]} {d.year}"


def datum_kurz(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.day:02d}.{d.month:02d}.{d.year}"


def prozent(z) -> str:
    return f"{float(z):.1f}".replace(".", ",") + " %"


CSS = """
:root{
  --pro:#0F766E; --pro-text:#0C6A62; --contra:#8E44AD; --contra-text:#7E3C9A;
  --grund:#FFFFFF; --flaeche:#F7F8FA; --karte:#FFFFFF;
  --text:#12161C; --text-leise:#5A626D; --linie:#E2E6EB;
}
@media (prefers-color-scheme:dark){
  :root{
    --pro:#3FB3A8; --pro-text:#3FB3A8; --contra:#C08AD8; --contra-text:#C08AD8;
    --grund:#12161C; --flaeche:#171C24; --karte:#1B212B;
    --text:#EEF1F5; --text-leise:#9AA3AF; --linie:#2C3440;
  }
}
*{box-sizing:border-box}
body{margin:0;background:var(--grund);color:var(--text);
  font-family:"Public Sans","Helvetica Neue",Arial,sans-serif;font-size:16px;line-height:1.55}
h1,h2,h3{font-family:Archivo,"Helvetica Neue",Arial,sans-serif;font-weight:600}
a{color:inherit}
.wrap{max-width:1000px;margin:0 auto;padding:0 24px 80px}

.kopf{border-bottom:1px solid var(--linie);padding:44px 0 30px;margin-bottom:34px}
.marke{font-size:13px;letter-spacing:.10em;text-transform:uppercase;
  color:var(--text-leise);font-family:Archivo,sans-serif;font-weight:600}
h1{font-size:clamp(30px,5vw,46px);line-height:1.1;margin:12px 0 10px;letter-spacing:-.015em}
.lead{margin:0;font-size:18px;color:var(--text-leise)}

.kaesten{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:20px;align-items:start}
.kasten{display:flex;flex-direction:column;border:1px solid var(--linie);border-radius:16px;
  padding:24px 26px 22px;background:var(--karte);text-decoration:none;color:inherit;
  transition:border-color .12s, transform .12s}
.kasten:hover,.kasten:focus-visible{border-color:var(--text-leise);transform:translateY(-2px)}
.kasten:focus-visible{outline:2px solid var(--text);outline-offset:3px}
.k-marke{font-family:Archivo,sans-serif;font-size:11px;font-weight:600;letter-spacing:.08em;
  text-transform:uppercase;padding:3px 10px;border-radius:999px;border:1px solid currentColor;
  align-self:flex-start;margin-bottom:14px}
.k-kantonsrat .k-marke{color:var(--pro-text)}
.k-abstimmung .k-marke{color:var(--contra-text)}
.kasten h2{margin:0 0 8px;font-size:23px;letter-spacing:-.01em}
.k-satz{margin:0 0 18px;font-size:15px;color:var(--text-leise);flex:1}
.k-zahlen{display:flex;flex-wrap:wrap;gap:8px 26px;padding-top:16px;
  border-top:1px solid var(--linie)}
.k-zahl{font-family:Archivo,sans-serif;font-size:19px;font-weight:600;
  font-variant-numeric:tabular-nums}
.k-zahl em{display:block;font-style:normal;font-size:12px;font-weight:400;
  letter-spacing:.05em;text-transform:uppercase;color:var(--text-leise);margin-top:2px}
.k-stand{margin:14px 0 0;font-size:12.5px;font-style:italic;color:var(--text-leise)}
.k-pfeil{margin:16px 0 0;font-family:Archivo,sans-serif;font-size:14px;font-weight:600}
.k-kantonsrat .k-pfeil{color:var(--pro-text)}
.k-abstimmung .k-pfeil{color:var(--contra-text)}

.kasten-div{cursor:default}
.kasten-div:hover{transform:none}
.k-titel-link{text-decoration:none;color:inherit}
.k-titel-link:hover h2{text-decoration:underline}
.k-wahl{margin:14px 0 0;border-top:1px solid var(--linie);padding-top:12px}
.k-wahl summary{cursor:pointer;list-style:none;display:flex;align-items:center;justify-content:space-between;
  font-family:Archivo,sans-serif;font-size:14px;font-weight:600;color:var(--contra-text);padding:4px 0}
.k-wahl summary::-webkit-details-marker{display:none}
.k-wahl summary::after{content:"";width:8px;height:8px;border-right:2px solid currentColor;border-bottom:2px solid currentColor;
  transform:rotate(45deg);margin-right:4px;transition:transform .15s}
.k-wahl[open] summary::after{transform:rotate(-135deg)}
.k-gruppe{margin:10px 0 0}
.k-gruppe h3{margin:0 0 4px;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--text-leise)}
.k-gruppe ul{list-style:none;margin:0;padding:0}
.k-gruppe li a{display:grid;grid-template-columns:86px 1fr;gap:10px;padding:7px 6px;border-radius:8px;
  text-decoration:none;color:inherit;font-size:14.5px;line-height:1.35}
.k-gruppe li a:hover{background:var(--flaeche)}
.k-gruppe time{color:var(--text-leise);font-variant-numeric:tabular-nums;font-size:13px;padding-top:1px}
.k-entwurf{font-size:12px;font-weight:400;color:var(--text-leise);font-style:italic;font-family:"Public Sans",sans-serif}
.k-gruppe .k-leer{font-size:13.5px;color:var(--text-leise);padding:4px 6px}

.zurueck{display:inline-flex;align-items:center;gap:6px;font-family:Archivo,sans-serif;font-size:13px;font-weight:600;
  letter-spacing:.08em;text-transform:uppercase;color:var(--text-leise);text-decoration:none;margin-bottom:10px}
.zurueck:hover{color:var(--text)}
.abschnitt{margin-top:44px}
.abschnitt h2{font-size:15px;letter-spacing:.06em;text-transform:uppercase;color:var(--text-leise);margin:0 0 12px}
.fruehere{margin-top:48px}
.fruehere h2{font-size:15px;letter-spacing:.06em;text-transform:uppercase;
  color:var(--text-leise);margin:0 0 6px}
.fruehere p.hinweis{margin:0 0 14px;font-size:14px;color:var(--text-leise)}
.liste{list-style:none;margin:0;padding:0;border-top:1px solid var(--linie)}
.liste li{border-bottom:1px solid var(--linie)}
.liste a{display:grid;grid-template-columns:110px 1fr;gap:4px 18px;padding:14px 4px;
  text-decoration:none;color:inherit}
.liste a:hover h3,.liste a:focus-visible h3{text-decoration:underline}
.liste time{font-variant-numeric:tabular-nums;color:var(--text-leise);font-size:14px;padding-top:3px}
.liste h3{margin:0;font-size:17px;font-weight:600}
.liste .erg{margin:2px 0 0;font-size:14px;color:var(--text-leise)}
.liste .erg b{color:var(--text);font-weight:600}
@media (max-width:560px){.liste a{grid-template-columns:1fr}}

.fuss{margin-top:52px;padding-top:22px;border-top:1px solid var(--linie);
  font-size:13.5px;color:var(--text-leise)}
.fuss a{text-decoration:underline}
"""


# ---------------------------------------------------------------- Quellen

def ratszahlen() -> list[dict] | None:
    """Kennzahlen des Kantonsratsspiegels, frisch aus den Ratsdaten.

    Fehlt die Datei, bleibt der Kasten ohne Zahlen statt mit falschen.
    """
    try:
        d = json.loads(SITZUNGEN.read_text(encoding="utf-8"))
    except Exception:
        return None
    s = d.get("sessions") or []
    if not s:
        return None
    return [{"wert": f"{sum(len(x.get('votes') or []) for x in s):,}".replace(",", " "),
             "einheit": "namentliche Abstimmungen"},
            {"wert": str(len(s)), "einheit": "Sitzungen"}]


def abstimmungen_lesen(ausblenden: set[str]) -> list[dict]:
    """Eine Zeile je Abstimmungsordner mit vorlage.json.

    Gelesen wird nur, was die Uebersicht braucht. Der Ordnername ist der
    Slug und damit die Adresse; das Datum steht in vorlage.abstimmung. Ohne
    gebaute Seite wird die Abstimmung gemeldet, aber nicht verlinkt: ein
    Kasten, der ins Leere fuehrt, ist schlimmer als keiner.
    """
    zeilen = []
    for pfad in sorted(VORLAGEN.glob("*/vorlage.json")):
        slug = pfad.parent.name
        if slug in ausblenden:
            continue
        try:
            d = json.loads(pfad.read_text(encoding="utf-8"))
        except Exception as ex:
            print(f"Hinweis: {pfad} nicht lesbar ({ex}), uebersprungen", file=sys.stderr)
            continue
        v = d.get("vorlage") or {}
        datum = v.get("abstimmung")
        if not datum:
            print(f"Hinweis: {slug} ohne vorlage.abstimmung, uebersprungen", file=sys.stderr)
            continue
        args = d.get("argumente") or []
        stellen = (d.get("textkritik") or {}).get("stellen") or []
        zeilen.append({
            "slug": slug,
            "pfad": f"abstimmung/{slug}/",
            "datum": datum,
            "titel": v.get("titel") or slug,
            "untertitel": v.get("untertitel") or "",
            "status": d.get("status") or "entwurf",
            "aussagen": sum(1 for a in args if a.get("fundstelle")),
            "stellen": len(stellen),
            "ergebnis": d.get("ergebnis"),
            "gebaut": (SITE / "abstimmung" / slug / "index.html").is_file(),
        })
    zeilen.sort(key=lambda z: z["datum"], reverse=True)
    return zeilen


# ---------------------------------------------------------------- Bausteine

def kasten(k) -> str:
    zahlen = "".join(
        f'<span class="k-zahl">{e(z["wert"])}<em>{e(z["einheit"])}</em></span>'
        for z in k.get("kennzahlen", []))
    stand = (f'<p class="k-stand">{e(k["stand"])}</p>' if k.get("stand") else "")
    return f"""
    <a class="kasten k-{e(k['art'])}" href="{e(k['pfad'])}">
      <span class="k-marke">{e(k['marke'])}</span>
      <h2>{e(k['titel'])}</h2>
      <p class="k-satz">{e(k['satz'])}</p>
      <div class="k-zahlen">{zahlen}</div>
      {stand}
      <p class="k-pfeil">ansehen &rarr;</p>
    </a>"""


def gruppen(zeilen, heute):
    """Aktuell (die naechste), kommend (die weiteren), vergangen; nur gebaute."""
    g = [z for z in zeilen if z["gebaut"]]
    kommend = sorted([z for z in g if z["datum"] >= heute], key=lambda z: z["datum"])
    vergangen = sorted([z for z in g if z["datum"] < heute], key=lambda z: z["datum"], reverse=True)
    aktuell = kommend[:1]
    return aktuell, kommend[1:], vergangen


def eintrag(z) -> str:
    entwurf = ' <span class="k-entwurf">Entwurf</span>' if z["status"] != "veroeffentlicht" else ""
    return (f'<li><a href="{e(z["pfad"])}"><time datetime="{e(z["datum"])}">{e(datum_kurz(z["datum"]))}</time>'
            f'<span>{e(z["titel"])}{entwurf}</span></a></li>')


def gruppe(titel, zs, leer) -> str:
    li = "".join(eintrag(z) for z in zs) if zs else f'<li class="k-leer">{e(leer)}</li>'
    return f'<div class="k-gruppe"><h3>{e(titel)}</h3><ul>{li}</ul></div>'


def abstimmungskasten(zeilen, heute) -> str:
    """Ein Kasten fuer den ganzen Abstimmungsspiegel. Der Titel fuehrt zur
    Listenseite abstimmung/, das Aufklappfeld direkt zu jeder Abstimmung.
    Kein <a> um den Kasten: ein Aufklappfeld in einem Link ist kein gueltiges
    HTML, und der Browser wuerde jeden Klick als Sprung werten."""
    aktuell, kommend, vergangen = gruppen(zeilen, heute)
    gesamt = len(aktuell) + len(kommend) + len(vergangen)
    if aktuell:
        z = aktuell[0]
        satz = (f"Nächste Abstimmung am {datum_lang(z['datum'])}: {z['titel']}. "
                "Zu jeder Vorlage die Argumente beider Seiten mit Fundstelle und Prüfung des Belegs.")
        zahlen = [{"wert": str(z["aussagen"]), "einheit": "Aussagen geprüft"},
                  {"wert": str(gesamt), "einheit": "Abstimmungen" if gesamt != 1 else "Abstimmung"}]
    else:
        satz = "Zu jeder kantonalen Vorlage die Argumente beider Seiten mit Fundstelle und Prüfung des Belegs."
        zahlen = [{"wert": str(gesamt), "einheit": "Abstimmungen" if gesamt != 1 else "Abstimmung"}]
    zahlen_html = "".join(f'<span class="k-zahl">{e(x["wert"])}<em>{e(x["einheit"])}</em></span>' for x in zahlen)
    wahl = (gruppe("Aktuell", aktuell, "keine Abstimmung angekündigt")
            + gruppe("Kommend", kommend, "keine weiteren angekündigt")
            + gruppe("Vergangen", vergangen, "noch keine"))
    return f"""
    <div class="kasten kasten-div k-abstimmung">
      <span class="k-marke">Laufend</span>
      <a class="k-titel-link" href="abstimmung/"><h2>Abstimmungsspiegel</h2></a>
      <p class="k-satz">{e(satz)}</p>
      <div class="k-zahlen">{zahlen_html}</div>
      <details class="k-wahl"><summary>Abstimmung wählen</summary>{wahl}</details>
      <p class="k-pfeil"><a class="k-titel-link" href="abstimmung/">alle Abstimmungen &rarr;</a></p>
    </div>"""


def ergebnis_text(erg) -> str:
    """Das Ergebnis als ein Satz, aus vorlage.json «ergebnis».

    Schema:
        "ergebnis": {
          "stimmbeteiligung": 48.3,
          "quelle": "sh.ch, amtliches Ergebnis vom ...",
          "fragen": [
            {"titel": "Initiative", "ja": 38.1, "angenommen": false},
            {"titel": "Gegenvorschlag", "ja": 61.5, "angenommen": true}
          ]
        }
    Eine einfache Vorlage hat eine Frage. Bei einer Doppelvorlage sind es
    zwei oder drei, die Stichfrage eingeschlossen.
    """
    if not erg:
        return "Ergebnis noch nicht nachgetragen"
    teile = []
    for f in erg.get("fragen") or []:
        t = e(f.get("titel", ""))
        if f.get("ja") is not None:
            t += f" <b>{prozent(f['ja'])} Ja</b>"
        if f.get("angenommen") is not None:
            t += ", angenommen" if f["angenommen"] else ", abgelehnt"
        teile.append(t)
    if erg.get("stimmbeteiligung") is not None:
        teile.append(f"Stimmbeteiligung {prozent(erg['stimmbeteiligung'])}")
    return " &middot; ".join(teile) or "Ergebnis noch nicht nachgetragen"


def fruehere(zeilen) -> str:
    if not zeilen:
        return ""
    li = "".join(f"""
    <li><a href="{e(z['pfad'])}">
      <time datetime="{e(z['datum'])}">{e(datum_kurz(z['datum']))}</time>
      <span><h3>{e(z['titel'])}</h3><p class="erg">{ergebnis_text(z['ergebnis'])}</p></span>
    </a></li>""" for z in zeilen)
    return f"""
<section class="fruehere">
  <h2>Frühere Abstimmungen</h2>
  <p class="hinweis">Jede Seite bleibt so stehen, wie sie vor der Abstimmung war.
  Das Ergebnis wird nachgetragen.</p>
  <ul class="liste">{li}
  </ul>
</section>"""


# ---------------------------------------------------------------- Seite

def bauen(d, zeilen) -> str:
    heute = date.today().isoformat()
    kr = d["kantonsrat"]
    kaesten = [{
        "art": "kantonsrat", "pfad": "kantonsrat/", "marke": "Laufend",
        "titel": kr.get("titel", "Kantonsratsspiegel"), "satz": kr["satz"],
        "kennzahlen": ratszahlen() or [{"wert": "", "einheit": "aus den Ratsdaten"}],
    }]
    html_kaesten = "".join(kasten(k) for k in kaesten) + abstimmungskasten(zeilen, heute)

    return f"""<!DOCTYPE html>
<html lang="de-CH">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(d['titel'])}</title>
<meta name="description" content="{e(BESCHREIBUNG)}">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="icon" href="favicon.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="manifest" href="manifest.webmanifest">
<meta name="theme-color" content="#0B0F14">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700&family=Public+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div class="wrap">

<header class="kopf">
  <p class="marke">Kanton Schaffhausen</p>
  <h1>{e(d['titel'])}</h1>
  <p class="lead">{e(d['untertitel'])}</p>
</header>

<main>
<div class="kaesten">{html_kaesten}
</div>
</main>

<footer class="fuss">
  <p><strong>Kein Angebot einer Partei und keines des Kantons.</strong> Beide
  Seiten stehen auf denselben Grundlagen: Wortprotokolle des Kantonsrats,
  amtliche Abstimmungsunterlagen, Geodaten von Bund und Kanton. Jede Zahl ist
  bis zu ihrer Quelle verfolgbar, jede eigene Auswertung als solche
  gekennzeichnet.</p>

  <p>Erzeugt am {date.today().strftime('%d.%m.%Y')}. Aufbereitung ohne Gewähr.</p>
</footer>

</div>
</body>
</html>
"""


def listenseite(zeilen) -> str:
    """abstimmung/index.html: alle Abstimmungen, aktuell, kommend, vergangen."""
    heute = date.today().isoformat()
    aktuell, kommend, vergangen = gruppen(zeilen, heute)

    def block(titel, zs, leer):
        if not zs:
            return f'<section class="abschnitt"><h2>{e(titel)}</h2><p class="hinweis">{e(leer)}</p></section>'
        li = "".join(f"""
    <li><a href="../{e(z['pfad'].split('/', 1)[1])}">
      <time datetime="{e(z['datum'])}">{e(datum_kurz(z['datum']))}</time>
      <span><h3>{e(z['titel'])}{' <span class="k-entwurf">Entwurf</span>' if z['status'] != 'veroeffentlicht' else ''}</h3>
      <p class="erg">{(e(z['untertitel']) + ' · ' if z['untertitel'] else '') + (ergebnis_text(z['ergebnis']) if z['datum'] < heute else str(z['aussagen']) + ' Aussagen geprüft')}</p></span>
    </a></li>""" for z in zs)
        return f'<section class="abschnitt"><h2>{e(titel)}</h2><ul class="liste">{li}\n  </ul></section>'

    return f"""<!DOCTYPE html>
<html lang="de-CH">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Abstimmungsspiegel · alle Abstimmungen</title>
<meta name="description" content="Abstimmungsspiegel Schaffhausen: zu jeder kantonalen Vorlage die Argumente beider Seiten mit Fundstelle und Prüfung des Belegs.">
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
<div class="wrap">

<header class="kopf">
  <a class="zurueck" href="../">&larr; Politspiegel Schaffhausen</a>
  <p class="marke">Kanton Schaffhausen</p>
  <h1>Abstimmungsspiegel</h1>
  <p class="lead">Zu jeder kantonalen Vorlage die Argumente beider Seiten mit Fundstelle und Prüfung des Belegs.
  Bewertet wird der Beleg, nicht das Argument.</p>
</header>

<main>
{block("Aktuell", aktuell, "Keine Abstimmung angekündigt.")}
{block("Kommend", kommend, "Keine weiteren Abstimmungen angekündigt.")}
{block("Vergangen", vergangen, "Noch keine vergangene Abstimmung. Jede Seite bleibt nach der Abstimmung so stehen, wie sie vorher war; das Ergebnis wird nachgetragen.")}
</main>

<footer class="fuss">
  <p>Erzeugt am {date.today().strftime('%d.%m.%Y')}. Aufbereitung ohne Gewähr.</p>
</footer>

</div>
</body>
</html>
"""


UMLEITUNG = """<!DOCTYPE html>
<html lang="de-CH">
<head>
<meta charset="utf-8">
<title>Kantonsratsspiegel &middot; verschoben</title>
<meta http-equiv="refresh" content="0; url=kantonsrat/">
<link rel="canonical" href="kantonsrat/">
<meta name="robots" content="noindex">
<style>body{font-family:"Public Sans",Helvetica,Arial,sans-serif;margin:15vh auto;
max-width:34em;padding:0 24px;line-height:1.55;color:#12161C}
a{color:#0C6A62}</style>
</head>
<body>
<p>Der Kantonsratsspiegel liegt jetzt unter
<a href="kantonsrat/">kantonsrat/</a>. Sie werden weitergeleitet.</p>
</body>
</html>
"""


def main() -> None:
    d = json.loads(QUELLE.read_text(encoding="utf-8"))
    zeilen = abstimmungen_lesen(set(d.get("ausblenden") or []))
    SITE.mkdir(parents=True, exist_ok=True)
    ziel = SITE / "index.html"
    ziel.write_text(bauen(d, zeilen), encoding="utf-8")
    (SITE / "abstimmung").mkdir(parents=True, exist_ok=True)
    (SITE / "abstimmung" / "index.html").write_text(listenseite(zeilen), encoding="utf-8")
    (SITE / "dashboard.html").write_text(UMLEITUNG, encoding="utf-8")
    heute = date.today().isoformat()
    print(f"geschrieben: {ziel}  ({ziel.stat().st_size/1024:.1f} kB), dazu abstimmung/index.html")
    print(f"  {'kantonsrat/':44s} "
          + ("vorhanden" if (SITE / "kantonsrat" / "index.html").is_file() else "FEHLT NOCH"))
    for z in zeilen:
        lage = "kommend " if z["datum"] >= heute else "vergangen"
        seite = "vorhanden" if z["gebaut"] else "FEHLT NOCH, nicht verlinkt"
        erg = "" if z["datum"] >= heute or z["ergebnis"] else ", Ergebnis fehlt"
        print(f"  {z['pfad']:44s} {lage}  {seite}  [{z['status']}]{erg}")


if __name__ == "__main__":
    main()

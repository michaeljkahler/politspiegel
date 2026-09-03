#!/usr/bin/env python3
"""Baut die Uebersichtsseite «Politspiegel Schaffhausen».

Aufruf aus der Projektwurzel:
    python3 politspiegel/bauen.py

Liest    politspiegel/politspiegel.json              Titel, Untertitel, Kantonsratskasten
         abstimmungsspiegel/abstimmungen/*/vorlage.json  je Abstimmung Titel, Datum, Stand, Ergebnis
         data/all_sessions.json                       Kennzahlen des Kantonsratsspiegels
Schreibt site/index.html            die Uebersicht
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
die Seite gebaut, erscheint die Abstimmung. Kommende stehen als Kasten oben,
vergangene als Liste darunter, mit dem Ergebnis, sobald es in der vorlage.json
unter «ergebnis» nachgetragen ist. Nichts wird geloescht: eine alte Abstimmung
bleibt unter ihrer Adresse erreichbar und in der Liste auffindbar.
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

.kaesten{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:20px}
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


def abstimmungskasten(z) -> str:
    satz = z["untertitel"]
    if satz:
        satz += ". "
    satz += "Die Argumente beider Seiten mit Fundstelle und Prüfung des Belegs."
    k = {
        "art": "abstimmung",
        "pfad": z["pfad"],
        "marke": datum_lang(z["datum"]),
        "titel": z["titel"],
        "satz": satz,
        "kennzahlen": [{"wert": str(z["aussagen"]), "einheit": "Aussagen geprüft"}],
    }
    if z["stellen"]:
        k["kennzahlen"].append({"wert": str(z["stellen"]), "einheit": "Stellen im Text geprüft"})
    if z["status"] != "veroeffentlicht":
        k["stand"] = "Entwurf, noch nicht veröffentlichungsreif"
    return kasten(k)


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
    kommend = [z for z in zeilen if z["datum"] >= heute and z["gebaut"]]
    vergangen = [z for z in zeilen if z["datum"] < heute and z["gebaut"]]
    # Kommende von nah nach fern: die naechste Abstimmung zuerst.
    kommend.sort(key=lambda z: z["datum"])
    html_kaesten = "".join(kasten(k) for k in kaesten)
    html_kaesten += "".join(abstimmungskasten(z) for z in kommend)

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
{fruehere(vergangen)}
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
    (SITE / "dashboard.html").write_text(UMLEITUNG, encoding="utf-8")
    heute = date.today().isoformat()
    print(f"geschrieben: {ziel}  ({ziel.stat().st_size/1024:.1f} kB)")
    print(f"  {'kantonsrat/':44s} "
          + ("vorhanden" if (SITE / "kantonsrat" / "index.html").is_file() else "FEHLT NOCH"))
    for z in zeilen:
        lage = "kommend " if z["datum"] >= heute else "vergangen"
        seite = "vorhanden" if z["gebaut"] else "FEHLT NOCH, nicht verlinkt"
        erg = "" if z["datum"] >= heute or z["ergebnis"] else ", Ergebnis fehlt"
        print(f"  {z['pfad']:44s} {lage}  {seite}  [{z['status']}]{erg}")


if __name__ == "__main__":
    main()

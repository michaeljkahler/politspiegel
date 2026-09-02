#!/usr/bin/env python3
"""
Veröffentlichen auf GitHub Pages
================================
Nimmt die fertige Ausgabe von build3.py, macht daraus die Seite, die im Netz
steht, und schiebt sie ins Repository.

Warum ein eigener Schritt und nicht direkt aus build3.py: die Seite im Netz
braucht Dinge, die lokal stören oder schlicht falsch wären. Sie heisst
index.html, damit die blosse Adresse sie öffnet. Sie trägt Vorschauangaben für
geteilte Links. Und sie liegt in einem eigenen Ordner site/, damit ins
Repository nur das kommt, was veröffentlicht werden soll, und nicht die
143 MB Wortprotokolle daneben.

Zugang
------
data/github_zugang.json, in .gitignore ausgeschlossen:

    {"benutzer": "...", "repo": "...", "token": "ghp_..."}

Das Token ist ein Personal Access Token mit Schreibrecht auf Inhalte dieses
einen Repositories (fine-grained, Contents: Read and write). Es steht nie im
Repository und nie in einer Commit-Nachricht.

Ausführen:
    python3 scripts/publish.py            # Probelauf, zeigt was passieren würde
    python3 scripts/publish.py --apply    # schreibt, committet und pusht
"""
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITE = ROOT / "site"
QUELLE = ROOT / "output" / "dashboard.html"
ZUGANG = DATA / "github_zugang.json"

TITEL = "Abstimmungsspiegel Kantonsrat Schaffhausen"
BESCHREIBUNG = ("Wie der Schaffhauser Kantonsrat abstimmt: alle namentlichen "
                "Abstimmungen der Legislatur, nach Ratsmitglied, Fraktion und Thema. "
                "Mit Vergleich der eigenen Haltung.")


def kopfzeilen(url):
    """Vorschauangaben für geteilte Links.

    Ohne sie erscheint ein geteilter Link als nackte Adresse. Mit ihnen als
    Karte mit Titel, Satz und Bild, in WhatsApp, Threema, Mastodon und auf den
    Social-Media-Plattformen gleichermassen.
    """
    return (
        '<meta name="description" content="' + BESCHREIBUNG + '">\n'
        '<meta property="og:type" content="website">\n'
        '<meta property="og:site_name" content="' + TITEL + '">\n'
        '<meta property="og:title" content="' + TITEL + '">\n'
        '<meta property="og:description" content="' + BESCHREIBUNG + '">\n'
        '<meta property="og:url" content="' + url + '">\n'
        '<meta property="og:image" content="' + url + 'vorschau.png">\n'
        '<meta property="og:locale" content="de_CH">\n'
        '<meta name="twitter:card" content="summary_large_image">\n'
        '<meta name="twitter:title" content="' + TITEL + '">\n'
        '<meta name="twitter:description" content="' + BESCHREIBUNG + '">\n'
        '<meta name="twitter:image" content="' + url + 'vorschau.png">\n'
        '<link rel="canonical" href="' + url + '">\n'
        '<meta name="robots" content="index, follow">\n'
        # Zeichen und Startbildschirm. Die Dateien liegen fest in site/ und
        # werden nicht bei jedem Lauf neu erzeugt. Relative Pfade, damit
        # nichts bricht, wenn das Repository einmal umzieht.
        '<link rel="icon" href="favicon.svg" type="image/svg+xml">\n'
        '<link rel="icon" href="favicon.png" sizes="32x32" type="image/png">\n'
        '<link rel="apple-touch-icon" href="apple-touch-icon.png">\n'
        '<link rel="manifest" href="manifest.webmanifest">\n'
        '<meta name="theme-color" content="#0B0F14">\n'
        '<meta name="apple-mobile-web-app-title" content="Abstimmungsspiegel">\n'
    )


def seite_bauen(url):
    html = QUELLE.read_text(encoding="utf-8")
    # Vorhandene Vorschauangaben aus einem früheren Lauf entfernen, sonst
    # sammeln sie sich bei jeder Veröffentlichung an.
    html = re.sub(r'\n?<meta (?:property="og:|name="twitter:)[^>]*>', "", html)
    html = re.sub(r'\n?<link rel="canonical"[^>]*>', "", html)
    html = re.sub(r'\n?<meta name="(?:description|robots|theme-color'
                  r'|apple-mobile-web-app-title)"[^>]*>', "", html)
    html = re.sub(r'\n?<link rel="(?:icon|apple-touch-icon|manifest)"[^>]*>', "", html)
    einf = html.find("</title>")
    if einf < 0:
        raise SystemExit("Kein <title> in der Ausgabe gefunden, Abbruch.")
    einf += len("</title>")
    return html[:einf] + "\n" + kopfzeilen(url) + html[einf:]


def lauf(*args, pruefen=True):
    r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    if pruefen and r.returncode:
        raise SystemExit(f"Fehlgeschlagen: {' '.join(args[:2])}\n{r.stderr.strip()[:400]}")
    return r


def main():
    schreiben = "--apply" in sys.argv
    if not QUELLE.exists():
        raise SystemExit(f"{QUELLE} fehlt. Zuerst build3.py laufen lassen.")
    if not ZUGANG.exists():
        raise SystemExit(
            f"{ZUGANG} fehlt. Anlegen mit "
            '{"benutzer": "...", "repo": "...", "token": "..."} '
            "und sicherstellen, dass die Datei in .gitignore steht.")

    z = json.load(open(ZUGANG, encoding="utf-8"))
    for feld in ("benutzer", "repo", "token"):
        if not z.get(feld):
            raise SystemExit(f"Feld «{feld}» fehlt in {ZUGANG.name}.")
    url = f"https://{z['benutzer']}.github.io/{z['repo']}/"

    SITE.mkdir(exist_ok=True)
    seite = seite_bauen(url)
    ziel = SITE / "index.html"
    alt = ziel.read_text(encoding="utf-8") if ziel.exists() else ""
    gleich = alt == seite

    print(f"Adresse:   {url}")
    print(f"Seite:     {len(seite) / 1048576:.2f} MB"
          + ("  (unverändert gegenüber der letzten Veröffentlichung)" if gleich else ""))

    if not schreiben:
        print("\n(Probelauf, nichts geschrieben. Mit --apply veröffentlichen.)")
        return

    ziel.write_text(seite, encoding="utf-8")
    (SITE / ".nojekyll").write_text("", encoding="utf-8")

    if not (ROOT / ".git").exists():
        print("Kein Repository, wird angelegt.")
        lauf("git", "init", "-b", "main")
    lauf("git", "config", "user.name", "Kantonsrats-Dashboard")
    lauf("git", "config", "user.email", f"{z['benutzer']}@users.noreply.github.com")

    # Der Token steht in der Fernadresse und darf darum nie in einen Commit
    # oder in eine Ausgabe geraten. Er wird bei jedem Lauf frisch gesetzt.
    fern = f"https://{z['benutzer']}:{z['token']}@github.com/{z['benutzer']}/{z['repo']}.git"
    lauf("git", "remote", "remove", "origin", pruefen=False)
    lauf("git", "remote", "add", "origin", fern)

    lauf("git", "add", "-A")
    stand = lauf("git", "status", "--porcelain")
    if not stand.stdout.strip():
        print("Nichts zu veröffentlichen, der Stand ist bereits oben.")
        return

    datenstand = ""
    try:
        s = json.load(open(DATA / "all_sessions.json", encoding="utf-8"))
        datenstand = s["sessions"][0]["sitzung"]
    except Exception:
        pass
    nachricht = f"Stand {date.today().isoformat()}"
    if datenstand:
        nachricht += f", neueste Sitzung: {datenstand}"
    lauf("git", "commit", "-m", nachricht)

    r = lauf("git", "push", "-u", "origin", "main", pruefen=False)
    if r.returncode:
        # Fehlertext säubern, damit der Token nicht in der Ausgabe landet
        fehler = (r.stderr or "").replace(z["token"], "***")
        raise SystemExit(f"Push fehlgeschlagen:\n{fehler.strip()[:500]}")

    print(f"Veröffentlicht: {nachricht}")
    print(f"Sichtbar unter {url} (GitHub Pages braucht ein bis zwei Minuten).")


if __name__ == "__main__":
    main()

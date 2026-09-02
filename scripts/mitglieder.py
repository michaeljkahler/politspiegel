#!/usr/bin/env python3
"""
Mitglieder des Kantonsrats: Porträt, Angaben und Interessenbindungen
====================================================================
Quelle ist die amtliche Seite «Mitglieder und Fraktionen» auf sh.ch. Die
Personendaten stecken dort als JSON im Seitenquelltext, ein Browser ist nicht
nötig. Je Person werden gelesen:

    Name, Mailadresse, Porträtbild (Base64 im Feld data_profilePicture)
    Geburtsdatum, Beruf, Adresse, Partei, Fraktion, Ratsmitglied seit
    Interessenbindungen (Freitext, zeilenweise aufgeteilt)

Die Bilder werden auf 160 Pixel verkleinert, sonst würde das Dashboard um
mehrere Megabyte wachsen.

Ausführen:
    python3 scripts/mitglieder.py            # Bericht
    python3 scripts/mitglieder.py --apply    # schreibt data/mitglieder.json
"""
import base64
import html
import io
import json
import re
import sys
from datetime import date
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ZIEL = DATA / "mitglieder.json"
QUELLE = ("https://sh.ch/CMS/Webseite/Kanton-Schaffhausen/Beh-rde/Parlament/"
          "Der-Kantonsrat/Mitglieder-und-Parteien/Mitglieder-und-Fraktionen-2304166-DE.html")
UA = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-CH,de;q=0.9",
}
BILD_KANTE = 160          # Pixel, quadratisch beschnitten

# Überschriften im Feld data_contact, in dieser Reihenfolge auf der Seite
FELDER = ["Geburtsdatum", "Beruf", "Adresse", "Partei", "Fraktion",
          "Ratsmitglied seit", "Interessenbindungen"]


def _objekt_ab(text, start):
    """Von einer öffnenden Klammer bis zur passenden schliessenden lesen."""
    tiefe, i, in_str, esc = 0, start, False, False
    while i < len(text):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "{":
                tiefe += 1
            elif c == "}":
                tiefe -= 1
                if tiefe == 0:
                    return text[start:i + 1]
        i += 1
    return None


def personen_aus_seite(text):
    """Alle Personenobjekte (contenttypeid 201) aus dem Seitenquelltext."""
    out = {}
    for m in re.finditer(r'\{"contentid":"(\d+)","domainid"', text):
        roh = _objekt_ab(text, m.start())
        if not roh:
            continue
        try:
            j = json.loads(roh)
        except Exception:
            continue
        if j.get("contenttypeid") != "201" or j["contentid"] in out:
            continue
        out[j["contentid"]] = j
    return out


def contact_parsen(roh):
    """Das HTML-Feld data_contact in die einzelnen Angaben zerlegen."""
    if not roh:
        return {}
    try:
        bloecke = json.loads(roh)
    except Exception:
        return {}
    text = " ".join(b.get("value", "") for b in bloecke if isinstance(b, dict))
    # Absätze zu Zeilen machen, damit mehrzeilige Angaben erhalten bleiben
    text = re.sub(r"</p>|<br\s*/?>", "\n", html.unescape(text))
    zeilen = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", z)).strip()
              for z in text.split("\n")]
    zeilen = [z for z in zeilen if z]

    ergebnis, aktuell = {}, None
    for z in zeilen:
        treffer = next((f for f in FELDER if z.rstrip(":").strip().lower() == f.lower()), None)
        if treffer:
            aktuell = treffer
            ergebnis.setdefault(aktuell, [])
            continue
        if aktuell:
            ergebnis[aktuell].append(z)
    return {k: v for k, v in ergebnis.items() if v}


def bild_verkleinern(b64):
    """Porträt quadratisch beschneiden und auf BILD_KANTE verkleinern."""
    if not b64:
        return None
    try:
        bild = Image.open(io.BytesIO(base64.b64decode(b64)))
    except Exception:
        return None
    bild = bild.convert("RGB")
    breite, hoehe = bild.size
    kante = min(breite, hoehe)
    links, oben = (breite - kante) // 2, 0        # oben beschneiden: Köpfe sitzen hoch
    bild = bild.crop((links, oben, links + kante, oben + kante))
    bild = bild.resize((BILD_KANTE, BILD_KANTE), Image.LANCZOS)
    puffer = io.BytesIO()
    bild.save(puffer, format="JPEG", quality=78, optimize=True)
    return base64.b64encode(puffer.getvalue()).decode()


def einlesen():
    """Alle Personenprofile holen.

    Die Übersichtsseite liefert nur die ersten zwölf Profile mit, der Rest wird
    im Browser nachgeladen. Darum stehen die contentids in
    data/mitglieder_ids.json und jedes Profil wird einzeln über die
    CMS-Schnittstelle geholt. Neue Ratsmitglieder werden dort ergänzt; der
    Abgleich mit den Abstimmungsdaten weiter unten zeigt an, wenn eines fehlt."""
    sess = requests.Session()
    sess.headers.update(UA)
    roh = {}

    # zuerst die Profile, die schon in der Übersichtsseite stecken
    try:
        r = sess.get(QUELLE, timeout=90)
        r.raise_for_status()
        roh.update(personen_aus_seite(r.text))
    except Exception as e:
        print(f"   ! Übersichtsseite nicht ladbar: {e}")

    ids_datei = DATA / "mitglieder_ids.json"
    bekannte = json.load(open(ids_datei, encoding="utf-8"))["ids"] if ids_datei.exists() else []
    for cid in bekannte:
        if cid in roh:
            continue
        try:
            j = sess.get("https://sh.ch/CMS/content",
                         params={"contentid": cid, "language": "DE"},
                         headers={"Accept": "application/json, text/javascript, */*; q=0.01",
                                  "X-Requested-With": "XMLHttpRequest"},
                         timeout=60).json()
        except Exception as e:
            print(f"   ! Profil {cid} nicht ladbar: {e}")
            continue
        if j.get("contenttypeid") == "201":
            roh[cid] = j

    mitglieder = []
    for cid, j in roh.items():
        angaben = contact_parsen(j.get("data_contact"))
        interessen = angaben.get("Interessenbindungen", [])
        mitglieder.append({
            "cid": cid,
            "nachname": (j.get("data_familyName") or "").strip(),
            "vorname": (j.get("data_name") or "").strip(),
            "name": (j.get("data_fullName") or "").strip(),
            "mail": (j.get("data_mail") or "").strip(),
            "geburtsdatum": " ".join(angaben.get("Geburtsdatum", [])),
            "beruf": " ".join(angaben.get("Beruf", [])),
            "adresse": ", ".join(angaben.get("Adresse", [])),
            "partei": " ".join(angaben.get("Partei", [])),
            "fraktion": " ".join(angaben.get("Fraktion", [])),
            "seit": " ".join(angaben.get("Ratsmitglied seit", [])),
            "interessenbindungen": interessen,
            "bild": bild_verkleinern(j.get("data_profilePicture")),
            "url": "https://sh.ch/CMS" + (j.get("data_permalink") or ""),
        })
    mitglieder.sort(key=lambda m: (m["nachname"], m["vorname"]))
    return mitglieder


def main():
    mitglieder = einlesen()
    mit_bild = sum(1 for m in mitglieder if m["bild"])
    mit_int = sum(1 for m in mitglieder if m["interessenbindungen"])
    anzahl_int = sum(len(m["interessenbindungen"]) for m in mitglieder)
    print(f"{len(mitglieder)} Mitglieder von sh.ch")
    print(f"   mit Porträt: {mit_bild}")
    print(f"   mit Interessenbindungen: {mit_int}, insgesamt {anzahl_int} Einträge")
    ohne = [m["name"] for m in mitglieder if not m["interessenbindungen"]]
    if ohne:
        print(f"   ohne Angabe: {', '.join(ohne)}")

    # Gegenprobe mit den Namen aus den Abstimmungsdaten
    pfad = DATA / "all_sessions.json"
    if pfad.exists():
        d = json.load(open(pfad, encoding="utf-8"))
        leg = d["legislaturen"][str(d["aktuelle_legislatur"])]
        aktiv = {k.replace("|", " ") for k in leg["aktive_mitglieder"]}
        hier = {f"{m['nachname']} {m['vorname']}" for m in mitglieder}
        fehlen = sorted(aktiv - hier)
        zuviel = sorted(hier - aktiv)
        print(f"   Abgleich mit den Abstimmungsdaten: {len(aktiv)} aktive Ratsmitglieder")
        if fehlen:
            print(f"   ! ohne Profil auf sh.ch: {', '.join(fehlen)}")
        if zuviel:
            print(f"   ! auf sh.ch, aber nicht in den Abstimmungsdaten: {', '.join(zuviel)}")

    if "--apply" in sys.argv:
        json.dump({"stand": date.today().isoformat(), "quelle": QUELLE,
                   "mitglieder": mitglieder},
                  open(ZIEL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        groesse = ZIEL.stat().st_size / 1e6
        print(f"\n{ZIEL.name} geschrieben ({groesse:.1f} MB).")
    else:
        print("\n(Probelauf, nichts geschrieben. Mit --apply schreiben.)")
        for m in mitglieder[:3]:
            print(f"\n  {m['name']} ({m['partei']}, {m['fraktion']}), {m['beruf']}, seit {m['seit']}")
            for i in m["interessenbindungen"]:
                print(f"     · {i}")


if __name__ == "__main__":
    main()

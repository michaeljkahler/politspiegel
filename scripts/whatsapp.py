#!/usr/bin/env python3
"""WhatsApp-Kanal: Kurzbeitrag je Sitzung zum Kopieren.

Schreibt je Sitzung einen Ordner nach Whatsappkanal/<slug>/ mit

    beitrag.txt      der fertige Text, 400 bis 600 Zeichen im Kern
    deckblatt-N.png  die Übersichtsbilder aus site/social/kantonsrat/<slug>/
    meta.json        Slug, Zeichenzahl, Stand, damit ein zweiter Lauf nichts
                     überschreibt

Der Ordner Whatsappkanal/ steht in .gitignore und wird nicht veröffentlicht:
der Kanal wird von Hand bedient, die Dateien bleiben auf dem Rechner.

Die Bilder stammen aus scripts/social.py; dieses Skript zeichnet nichts neu,
es wählt die Deckblätter der Karussells aus. Darum zuerst social.py laufen
lassen, dann whatsapp.py.

    python3 scripts/whatsapp.py --anzahl 2
    python3 scripts/whatsapp.py --sitzung 2026-09-21-nachmittag --neu

Textregeln wie in docs/KONZEPT_social-media.md: nur prüfbare Angaben, keine
Wertung. Die genannten Entscheide sind die mit dem kleinsten Stimmenabstand,
das ist eine Auswahl nach Zahl und keine Beurteilung.
"""
import argparse
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import social  # noqa: E402  (gleicher Ordner, liefert Auswertung und Slugs)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
QUELLE = ROOT / "site" / "social" / "kantonsrat"
AUS = ROOT / "Whatsappkanal"

SEITE_URL = "https://michaeljkahler.github.io/politspiegel/kantonsrat/"

# Kanäle des Politspiegels, wie im Fuss von site/index.html.
KANAELE = [
    ("Instagram", "instagram.com/politspiegel.sh"),
    ("TikTok", "tiktok.com/@politspiegel.sh"),
    ("Facebook", "facebook.com/122097032019472255"),
    ("YouTube", "youtube.com/@PolitspiegelSchaffhausen"),
]

KERN_MIN, KERN_MAX = 400, 600


def kuerze(text, n):
    text = text.strip()
    return text if len(text) <= n else text[: n - 1].rstrip(" ,;:") + "…"


def geschaefte(auswertungen):
    """Geschäfte in der Reihenfolge des Auftretens, mit Zahl der Abstimmungen."""
    reihe = []
    for a in auswertungen:
        g = (a["geschaeft"] or "").strip()
        if not g:
            continue
        for e in reihe:
            if e["name"] == g:
                e["n"] += 1
                break
        else:
            reihe.append({"name": g, "n": 1})
    return reihe


def ungueltig(a):
    """Abstimmungen, die das Protokoll selbst als ungültig führt. Sie tragen
    keinen Entscheid und gehören darum weder in die Bilanz noch in die Auswahl
    der knappsten Entscheide."""
    return re.match(r"ungültige abstimmung", (a["titel"] or "").strip().lower())


def abstand(a):
    """Stimmenabstand zwischen Ja und Nein."""
    return abs(a["c"]["ja"] - a["c"]["nein"])


def entscheid_satz(a):
    ja, nein = a["c"]["ja"], a["c"]["nein"]
    hoch, tief = (ja, nein) if ja >= nein else (nein, ja)
    return f"{social.listentitel(a)}: {a['ergebnis']}, {hoch} zu {tief}."


def text_bauen(sess, auswertungen):
    datum, zeit = social.datum_lang(sess["sitzung"])
    n = sess["n_votes"]
    kopf = (f"*Kantonsrat Schaffhausen, {datum}"
            + (f" ({zeit})" if zeit else "")
            + f": {n} namentliche Abstimmung{'en' if n != 1 else ''}.*")

    gueltig = [a for a in auswertungen if not ungueltig(a)]
    angenommen = sum(1 for a in gueltig if a["ergebnis"] == "Angenommen")
    abgelehnt = sum(1 for a in gueltig if a["ergebnis"] == "Abgelehnt")
    bilanz = f"{angenommen} angenommen, {abgelehnt} abgelehnt"
    rest = len(gueltig) - angenommen - abgelehnt
    if rest:
        bilanz += f", {rest} mit Stimmengleichheit"
    ohne = len(auswertungen) - len(gueltig)
    if ohne:
        bilanz += f", {ohne} ungültig"
    bilanz += "."

    # Geschäftszeile in drei Ausführlichkeiten, von lang nach kurz. Welche
    # genommen wird, entscheidet weiter unten das Zeichenbudget.
    gs = sorted(geschaefte(auswertungen), key=lambda e: -e["n"])
    zeilen_g = []
    for anzahl, laenge in ((3, 70), (2, 60), (1, 80)):
        teile = [f"{kuerze(e['name'], laenge)} ({e['n']})" if len(gs) > 1
                 else kuerze(e["name"], 110) for e in gs[:anzahl]]
        z = "Behandelt: " + "; ".join(teile)
        offen = len(gs) - min(anzahl, len(gs))
        if offen == 1:
            z += "; und ein weiteres Geschäft"
        elif offen > 1:
            z += f"; und {offen} weitere Geschäfte"
        z = z.rstrip(".") + "."
        if z not in zeilen_g:
            zeilen_g.append(z)
    if len(gs) > 1:
        zeilen_g.append(f"Behandelt: {len(gs)} Geschäfte, die meisten Abstimmungen zu "
                        + kuerze(gs[0]["name"], 70).rstrip(".") + ".")

    # Die knappsten Entscheide zuerst, so viele wie ins Zeichenbudget passen.
    knapp = sorted(gueltig, key=lambda a: (abstand(a), a["nr"]))
    schluss = ["", "Wer wie gestimmt hat: " + SEITE_URL,
               "Quelle: Abstimmungsprotokolle des Kantonsrats, sh.ch"]

    def baue(zeile_g, saetze):
        zeilen = [kopf, "", zeile_g, bilanz]
        if saetze:
            titel = "Knappster Entscheid:" if len(saetze) == 1 else "Knappste Entscheide:"
            zeilen += ["", titel] + [f"{i + 1}. {s}" for i, s in enumerate(saetze)]
        return "\n".join(zeilen + schluss)

    saetze = [entscheid_satz(a) for a in knapp[:3]]
    kern = None
    for k in range(len(saetze), 0, -1):   # so viele Entscheide wie möglich,
        for zeile_g in zeilen_g:          # dafür die Geschäftszeile kürzen
            probe = baue(zeile_g, saetze[:k])
            if len(probe) <= KERN_MAX:
                kern = probe
                break
        if kern:
            break
    if kern is None:
        kern = baue(zeilen_g[-1], saetze[:1])

    kanaele = "Politspiegel auch auf " + ", ".join(f"{k}: {u}" for k, u in KANAELE)
    return kern, kern + "\n\n" + kanaele


def deckblaetter(slug):
    """Erste Datei jedes Karussells: die Übersicht mit allen Abstimmungen."""
    ordner = QUELLE / slug
    pfad = ordner / "posts.json"
    if not pfad.exists():
        raise SystemExit(f"{pfad} fehlt. Zuerst scripts/social.py laufen lassen.")
    posts = json.loads(pfad.read_text(encoding="utf-8"))["posts"]
    aus = []
    for p in posts:
        if p.get("art") != "karussell" or not p.get("media"):
            continue
        name = p["media"][0].rsplit("/", 1)[-1]
        datei = ordner / name
        if datei.exists():
            aus.append(datei)
    return aus


def sitzung_bauen(sess, neu=False):
    slug = social.slug(sess["sitzung"])
    ziel = AUS / slug
    if (ziel / "beitrag.txt").exists() and not neu:
        print(f"{slug}: schon vorhanden, übersprungen (--neu zum Erneuern).")
        return None

    auswertungen = [social.auswerten(sess, i, v)
                    for i, v in enumerate(sess["votes"])]
    kern, ganz = text_bauen(sess, auswertungen)
    bilder = deckblaetter(slug)

    ziel.mkdir(parents=True, exist_ok=True)
    (ziel / "beitrag.txt").write_text(ganz + "\n", encoding="utf-8")
    kopien = []
    for i, b in enumerate(bilder, 1):
        name = "deckblatt.png" if len(bilder) == 1 else f"deckblatt-{i}.png"
        shutil.copyfile(b, ziel / name)
        kopien.append(name)
    (ziel / "meta.json").write_text(json.dumps({
        "sitzung": sess["sitzung"], "slug": slug, "stand": date.today().isoformat(),
        "zeichen_kern": len(kern), "zeichen_gesamt": len(ganz),
        "bilder": kopien, "quelle": f"site/social/kantonsrat/{slug}/",
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"{slug}: {len(kern)} Zeichen Kerntext, {len(ganz)} mit Kanälen, "
          f"{len(kopien)} Bild{'er' if len(kopien) != 1 else ''}")
    print(f"  Ordner: {ziel.relative_to(ROOT)}")
    if not (KERN_MIN <= len(kern) <= KERN_MAX):
        print(f"  ! Kerntext ausserhalb {KERN_MIN} bis {KERN_MAX} Zeichen, bitte ansehen.")
    return ziel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anzahl", type=int, default=1, help="die N neuesten Sitzungen")
    ap.add_argument("--sitzung", help="Slug einer Sitzung, z. B. 2026-09-21-nachmittag")
    ap.add_argument("--neu", action="store_true", help="vorhandene Ausgabe überschreiben")
    a = ap.parse_args()

    d = json.loads((DATA / "all_sessions.json").read_text(encoding="utf-8"))
    sessions = sorted(d["sessions"], key=social.sess_sort_key, reverse=True)
    if a.sitzung:
        sessions = [s for s in sessions if social.slug(s["sitzung"]) == a.sitzung]
        if not sessions:
            raise SystemExit(f"Keine Sitzung mit Slug {a.sitzung}.")
    else:
        sessions = sessions[: a.anzahl]

    for s in sessions:
        sitzung_bauen(s, neu=a.neu)


if __name__ == "__main__":
    main()

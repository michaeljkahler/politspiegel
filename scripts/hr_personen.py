#!/usr/bin/env python3
"""
Personensuche im Handelsregister Schaffhausen
=============================================
Fragt die Namen der Ratsmitglieder in der Personensuche des kantonalen
Handelsregisterportals ab und hält fest, welche Firmen dort auf einen Namen
eingetragen sind.

Rechtlicher Rahmen
------------------
Die robots.txt von sh.chregister.ch untersagt automatisierte Zugriffe
grundsätzlich. Das Handelsregisteramt des Kantons Schaffhausen hat für dieses
Projekt am 2. September 2026 eine Ausnahme erteilt, unter zwei Auflagen:

    höchstens 5 Namen pro Woche
    höchstens 2 vollständige Durchgänge pro Jahr
    mindestens 45 Sekunden zwischen zwei Personen

Die Pause von 45 Sekunden gilt zwischen Personen. Alle Registerauszüge, die zu
derselben Person gehören, dürfen unmittelbar nacheinander geöffnet werden.

Diese Grenzen stehen bewusst hier im Code und nicht bloss in der Anweisung des
wiederkehrenden Auftrags. Eine Anweisung kann missverstanden werden, eine
Schleife über fünf Namen nicht. Das Skript verweigert den Dienst, wenn ein Lauf
die Zusage überschreiten würde, auch wenn es öfter aufgerufen wird.

Jeder Lauf wird mit Zeitpunkt und abgefragten Namen protokolliert, damit sich
gegenüber dem Amt jederzeit belegen lässt, was tatsächlich abgefragt wurde.

Namensvettern
-------------
Die Suche läuft über den Nachnamen, und das Register führt Namensvettern
getrennt. Zu jedem Treffer wird darum der Registerauszug geöffnet und geprüft,
ob unter den eingetragenen Personen wirklich der Vorname des Ratsmitglieds
steht. Das Amt hat die Pause von 45 Sekunden ausdrücklich auf den Abstand
zwischen zwei Personen bezogen; die Auszüge einer Person dürfen unmittelbar
geöffnet werden.

Dass diese Prüfung nötig ist, zeigte gleich der erste Fall: die Suche nach
«Alaye» fand eine GmbH in Schaffhausen, eingetragen ist dort aber
Oluwafunso Akinola Alaye und nicht das Ratsmitglied Mayowa Alaye.

Geprüft wird über zwei Merkmale, weil keines allein genügt: den Vornamen und
die Wohngemeinde. Die Gemeinde stammt aus der Adresse auf sh.ch, und wo diese
fehlt, aus data/mitglieder_ergaenzung.json, wo jeder Nachtrag eine öffentliche
Quelle nennt. Der Ort trennt zwei
Personen gleichen Namens, sagt aber nichts, wenn beide am selben Ort wohnen;
bei «Alaye» ist genau das der Fall, dort entscheidet der Vorname.

Urteile je Treffer:
    bestaetigt              Nachname und Vorname stimmen, Wohnort passt
    bestaetigt_anderer_ort  Vorname stimmt, Wohnort weicht ab. Kein Ausschluss:
                            Register wie Deklaration können veraltet sein
    moeglich                nur der Ort stützt die Zuordnung
    namensvetter            Nachname stimmt, Vorname nicht
    unklar / ungeprueft     nicht zuzuordnen, oder kein Auszug abrufbar

Dazu das Feld «aktuell». Gestrichene Personeneinträge tragen im Auszug das Wort
«gelöscht:» vor dem Namen und bedeuten ein beendetes Mandat. Sie werden erfasst,
aber nicht als undeklarierte Interessenbindung gemeldet.

Auch «bestaetigt» bleibt ein Prüfhinweis. Verbindlich ist allein der beglaubigte
Registerauszug.

Gelöschte Firmen
----------------
Die Suche läuft mit den Häkchen «auch gelöschte Firmen» und «auch gestrichene
Personen», sonst fehlten beendete Mandate. Damit erscheinen aber Rechtseinheiten,
die es längst nicht mehr gibt: von 170 gefundenen Firmen waren 101 gelöscht,
59 Prozent aller Treffer betreffen sie. Von Hand findet man diese Firmen nicht
einmal, eine gewöhnliche Suche zeigt sie nicht.

Ein gelöschter Rechtsträger kann keine bestehende Interessenbindung sein. Erkannt
wird er auf zwei Wegen: beim Öffnen über die Trefferzeile trägt die Weiterleitung
ein Löschdatum (`?loeschung=20040213&uid=...`), und nachträglich prüft
`--firmen-pruefen`, ob auszug.xhtml?uid=... überhaupt Inhalt liefert. Beides
kostet nichts vom Kontingent, begrenzt sind die Namensabfragen.

Aus der ersten Handprüfung am 2. September 2026: von fünf vorgelegten Kandidaten
hielt einer stand. Drei der vier falschen betrafen gelöschte Firmen, der vierte
eine Person mit abweichender Wohngemeinde. Beide Fälle fängt das Skript seither
selbst ab.

Zwei Fallstricke, die je einen Lauf gekostet haben
--------------------------------------------------
1. Das Portal hält die Trefferliste in der Sitzung. Eine zweite Suche in
   derselben Sitzung liefert die Tabelle der ersten zurück, während die
   gemeldete Trefferzahl schon zur neuen gehört. Darum eine eigene Sitzung je
   Person, und zusätzlich der Abgleich zwischen Zeilenzahl und gemeldeter Zahl
   als Netz.
2. Der Auszug ist über auszug.xhtml?uid=... nur für bestehende Rechtseinheiten
   erreichbar. Gelöschte brauchen zusätzlich das Löschdatum, das nirgends in der
   Trefferliste steht. Der Knopf der Trefferzeile kennt es. Darum werden die
   Auszüge über diesen Knopf geöffnet und nicht über eine gebaute Adresse.

Ausführen:
    python3 scripts/hr_personen.py            # zeigt, was ein Lauf täte
    python3 scripts/hr_personen.py --apply    # fragt die nächsten 5 Namen ab
    python3 scripts/hr_personen.py --apply --vollstaendig   # einmalig alle Namen
    ... --minuten 8                          # nach 8 Minuten anhalten, Stand sichern
    python3 scripts/hr_personen.py --bericht  # vergleicht Register und Deklaration
    python3 scripts/hr_personen.py --neu-beurteilen   # ohne Abfrage neu bewerten
    python3 scripts/hr_personen.py --firmen-pruefen   # bestehen die Firmen noch?
    python3 scripts/hr_personen.py --auszug CHE-...   # einen Auszug ansehen
"""
import html
import json
import re
import sys
import time
import unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MITGLIEDER = DATA / "mitglieder.json"
STATUS = DATA / "hr_abfrage_status.json"
ZIEL = DATA / "hr_personen.json"

URL = "https://sh.chregister.ch/cr-portal/suche/suche.xhtml"
AUSZUG = "https://sh.chregister.ch/cr-portal/auszug/auszug.xhtml"
KENNUNG = ("kantonsrat-dashboard/1.0 (+nichtkommerzielles Transparenzprojekt "
           "Kantonsrat Schaffhausen; Kontakt via handelsregisteramt@sh.ch "
           "bekannt; Abfrage gemäss Zusage vom 02.09.2026)")

# Die zugesagten Grenzen. Nicht ohne neue Zusage des Amts ändern.
PRO_WOCHE = 5
DURCHGAENGE_PRO_JAHR = 2
TAGE_ZWISCHEN_LAEUFEN = 6      # ein Lauf je Kalenderwoche
WOCHEN_ZWISCHEN_DURCHGAENGEN = 8
# 45 Sekunden zwischen zwei Personen. Innerhalb einer Person dürfen alle
# Registerauszüge unmittelbar geöffnet werden; das Amt hat die Pause
# ausdrücklich auf den Abstand zwischen Personen bezogen.
PAUSE_JE_PERSON = 45

REGISTERPFLICHTIG = re.compile(
    r"\b(AG|GmbH|SA|Sàrl|Genossenschaft|Stiftung|Holding|KlG|KmG)\b", re.I)


# ── Abfrage ──────────────────────────────────────────────────────────────────

def sitzung():
    s = requests.Session()
    s.headers.update({"User-Agent": KENNUNG, "Accept-Language": "de-CH,de;q=0.9"})
    return s


def formular(s):
    """Sitzung eröffnen und die Formularangaben lesen.

    ViewState und die erzeugten Feldnamen (j_idt169 und so fort) ändern sich mit
    jeder neuen Fassung des Portals. Darum wird der Suchknopf über seine
    Beschriftung gesucht und nicht über eine festgeschriebene Kennung.
    """
    h = s.get(URL, timeout=60).text
    m = re.search(r'name="javax\.faces\.ViewState"[^>]*value="([^"]*)"', h)
    if not m:
        raise RuntimeError("Kein ViewState gefunden, das Portal hat sich geändert.")
    knopf = None
    for b in re.finditer(r'<button id="(idSucheForm:[^"]+)"[^>]*>(.*?)</button>', h, re.S):
        if re.sub(r"<[^>]+>", "", b.group(2)).strip() in ("Suchen", "Search", "Rechercher"):
            knopf = b.group(1)
            break
    if not knopf:
        raise RuntimeError("Kein Suchknopf gefunden, das Portal hat sich geändert.")
    haken = re.findall(r'name="(idSucheForm:panel:j_idt\d+_input)"', h)
    return m.group(1), knopf, haken


def suche(s, name, vs, knopf, haken):
    """Ein Nachname in der Personensuche. Gibt die Trefferliste zurück."""
    d = {"idSucheForm": "idSucheForm",
         "idSucheForm:idFirma": "",
         "idSucheForm:idPerson": name,
         "idSucheForm:panel:idRechtsform_input": "",
         "idSucheForm:panel:idSitz_input": "",
         "idSucheForm:panel:idSitz_hinput": "",
         "idSucheForm:panel:idShabDatum_input": "",
         "idSucheForm:panel:idShabNummer": "",
         "idSucheForm:panel:idDiverseTyp_input": "",
         "idSucheForm:panel:idDiverseSuchtext": "",
         "idSucheForm:panel_active": "-1",
         knopf: knopf,
         "javax.faces.ViewState": vs,
         "javax.faces.partial.ajax": "true",
         "javax.faces.source": knopf,
         "javax.faces.partial.execute": "@all",
         "javax.faces.partial.render": "idSucheForm"}
    # Auch gelöschte Firmen und gestrichene Personen, sonst fehlen beendete Mandate
    for k in haken:
        d[k] = "on"

    r = s.post(URL, data=d, timeout=90,
               headers={"Faces-Request": "partial/ajax", "X-Requested-With": "XMLHttpRequest"})
    r.raise_for_status()
    t = html.unescape(r.text)

    # Für das Öffnen der Auszüge: die Formularfelder ohne die AJAX-Angaben und
    # der ViewState, wie er nach der Suche gilt.
    basis = {k: v for k, v in d.items()
             if not k.startswith("javax.faces") and k != knopf}
    m_vs = re.search(r'ViewState:0"><!\[CDATA\[([^\]]+)\]\]', t)
    nach_vs = m_vs.group(1) if m_vs else vs

    # Eine leere Ergebnismenge meldet das Portal im Klartext und ohne die
    # Trefferzahl: «Für die angegebenen Suchkriterien wurden keine Einträge
    # gefunden.» Ohne diesen Fall sieht ein sauberes «nichts gefunden» aus wie
    # eine Seite, die das Skript nicht lesen konnte. Der Unterschied ist für ein
    # Transparenzprojekt wesentlich: geprüft und nichts gefunden ist eine
    # Aussage, nicht geprüft ist keine.
    if re.search(r"keine Eintr[äa]ge gefunden|no entries (were )?found"
                 r"|aucune inscription", t, re.I):
        return [], None, basis, nach_vs

    # Die Teilantwort enthält bei aufeinanderfolgenden Abfragen mehr als einen
    # Tabellenrumpf: den neuen und den aus der wiederhergestellten Ansicht. Wer
    # über das ganze Dokument sucht, sammelt beide ein und meldet die Treffer
    # der vorherigen Person. Darum ausschliesslich der letzte Rumpf.
    letzte = t.rfind("resultTable_data")
    bereich = t[letzte:] if letzte >= 0 else ""

    treffer = []
    for zeile in re.findall(r"<tr data-ri=\"\d+\"(.*?)</tr>", bereich, re.S):
        felder = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", x)).strip()
                  for x in re.findall(r"<td[^>]*>(.*?)</td>", zeile, re.S)]
        felder = [f for f in felder if f]
        # Nicht nur CHE-Nummern: Rechtseinheiten ohne UID tragen eine
        # ADM-Nummer, etwa «Parkhaus Herrenacker AG in Liquidation». Wer nur
        # auf CHE prüft, verliert sie stillschweigend, und Liquidationen sind
        # für die Interessenbindungen gerade interessant.
        if felder and re.match(r"[A-Z]{3}-\d{3}\.\d{3}\.\d{3}", felder[0]):
            treffer.append({"uid": felder[0],
                            "firma": felder[1] if len(felder) > 1 else None,
                            "sitz": felder[2] if len(felder) > 2 else None,
                            "rechtsform": felder[3] if len(felder) > 3 else None})

    m = re.search(r"(?:Anzahl gefundene Firmen|Number of companies found)[^0-9]*(\d+)", t)
    gemeldet = int(m.group(1)) if m else None
    if gemeldet is None:
        return treffer, "Trefferzahl nicht gefunden, Ergebnis ungeprüft", basis, nach_vs
    if gemeldet == len(treffer):
        return treffer, None, basis, nach_vs
    if gemeldet > len(treffer):
        # Mit frischer Sitzung je Person stimmen Zeilen und gemeldete Zahl
        # normalerweise überein. Bleibt eine Lücke, zeigt die Tabelle nur die
        # erste Seite: ein im Register häufiger Nachname. Solche Namen sind
        # ohnehin von Hand zu beurteilen, weil Namensvettern überwiegen.
        return treffer, (f"{gemeldet} Treffer im Register, angezeigt sind {len(treffer)}. "
                         f"Nur die erste Seite, Rest von Hand nachsehen."), basis, nach_vs
    # Mehr Zeilen als gemeldete Treffer heisst: die Antwort ist vermischt.
    # Dann lieber nichts als etwas Falsches.
    return None, (f"Antwort unstimmig: {len(treffer)} Zeilen bei {gemeldet} gemeldeten "
                  f"Treffern. Nicht übernommen."), basis, nach_vs


def kuerzen(s, n=300):
    s = re.sub(r"\s+", " ", s or "").strip()
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + " …"


def blank(s):
    return re.sub(r"\s+", " ", re.sub(r"<br\s*/?>", ", ", re.sub(r"<[^>]+>", " ", s))).strip()


def personen_aus_seite(s, seite):
    """Die eingetragenen Personen aus einer bereits geöffneten Auszugsseite.

    Die Seite liefert beim Abrufen nur das Gerüst; der Inhalt steckt in einem
    PrimeFaces-Panel, das über einen zweiten Aufruf angefordert wird.
    """
    i = seite.find('id="idAuszugForm"')
    m = re.search(r'name="javax\.faces\.ViewState"[^>]*value="([^"]*)"', seite[i:])
    if i < 0 or not m:
        return None, None, "Auszugsseite ohne Formular"
    p = "idAuszugForm:auszugContentPanel"
    r2 = s.post(AUSZUG, timeout=60,
                data={"idAuszugForm": "idAuszugForm", "javax.faces.ViewState": m.group(1),
                      "javax.faces.partial.ajax": "true", "javax.faces.source": p,
                      "javax.faces.partial.execute": p, "javax.faces.partial.render": p,
                      p: p},
                headers={"Faces-Request": "partial/ajax", "X-Requested-With": "XMLHttpRequest"})
    r2.raise_for_status()
    x = html.unescape(r2.text)

    # Der eingetragene Zweck sagt mehr über die Firma als ihr Name. Für die
    # Einordnung in eine Branche ist er die bessere Grundlage: «SAH Services
    # GmbH» verrät nichts, ihr Zweck schon.
    zweck = None
    for tab in re.findall(r"<table[^>]*>.*?</table>", x, re.S):
        kopf = blank(tab[:tab.find("</thead>")]) if "</thead>" in tab else ""
        if kopf.rstrip().endswith("Zweck") or re.search(r"\bZweck\b", kopf):
            for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", tab[tab.find("<tbody"):], re.S):
                f = [blank(td) for td in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
                lang = [x for x in f if len(x) > 30]
                if lang:
                    zweck = lang[0]
                    break
        if zweck:
            break

    for tab in re.findall(r"<table[^>]*>.*?</table>", x, re.S):
        kopf = blank(tab[:tab.find("</thead>")]) if "</thead>" in tab else ""
        if "Personalangaben" not in kopf or "Funktion" not in kopf:
            continue
        leute = []
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", tab[tab.find("<tbody"):], re.S):
            f = [blank(td) for td in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
            if len(f) < 4 or not f[-3]:
                continue
            eintrag = f[-3]
            # Gestrichene Personen tragen das Wort «gelöscht:» vor dem Namen.
            # Ohne Abtrennen scheitert schon der Vergleich des Nachnamens, und
            # ein beendetes Mandat sähe aus wie ein bestehendes.
            geloescht = bool(re.match(r"gel[öo]scht\s*:", eintrag, re.I))
            eintrag = re.sub(r"^gel[öo]scht\s*:\s*", "", eintrag, flags=re.I)
            leute.append({"eintrag": eintrag, "funktion": f[-2], "zeichnung": f[-1],
                          "geloescht": geloescht})
        return leute, zweck, None
    # Für gelöschte Rechtseinheiten gibt das Portal keinen Auszug heraus, die
    # Seite bleibt leer. Das ist kein Fehler, sondern eine Grenze der Quelle:
    # gesucht wird auch in gelöschten Firmen, angesehen werden können sie nicht.
    return None, None, ("Kein Auszug abrufbar, vermutlich eine gelöschte "
                        "Rechtseinheit. Zuordnung offen.")


ERGAENZUNG = DATA / "mitglieder_ergaenzung.json"


def ergaenzungen():
    """Von Hand nachgetragene Angaben, mit Quelle. Siehe die Datei selbst."""
    if not ERGAENZUNG.exists():
        return {}
    return json.loads(ERGAENZUNG.read_text(encoding="utf-8")).get("personen", {})


def gemeinde(adresse, name=None):
    """Die Wohngemeinde, aus der Adresse auf sh.ch oder aus der Ergänzung.

    Die Adressen auf sh.ch sind uneinheitlich erfasst: manche tragen hinten noch
    eine Mailadresse, manche bestehen nur aus Postleitzahl und Ort, drei fehlen
    ganz. Genommen wird, was nach der vierstelligen Postleitzahl steht, bis zum
    nächsten Komma.

    Fehlt die Adresse, greift data/mitglieder_ergaenzung.json. Dort steht je
    Person eine Quelle, und es steht dort ausschliesslich die Gemeinde: mehr
    braucht es nicht, um zwei Personen gleichen Namens zu trennen, und mehr
    gehört auch nicht in dieses Projekt.
    """
    m = re.search(r"\b\d{4}\s+([^,]+)", (adresse or "").strip())
    if m:
        return m.group(1).strip()
    if name:
        e = ergaenzungen().get(name) or {}
        return e.get("gemeinde")
    return None


def gleiche_gemeinde(a, b):
    a, b = norm(a), norm(b)
    if not a or not b:
        return None                      # nicht entscheidbar
    return a == b or a in b or b in a    # «Neuhausen» und «Neuhausen am Rheinfall»


def auszug_von_zeile(s, basis, vs, zeile):
    """Den Auszug einer Trefferzeile öffnen und die Personen auslesen.

    Der direkte Weg über auszug.xhtml?uid=... genügt nicht: gelöschte
    Rechtseinheiten brauchen zusätzlich das Löschdatum, und das steht nirgends
    in der Trefferliste. Der Knopf der Zeile weiss es und leitet auf die
    richtige Adresse weiter. Aus derselben Suche lassen sich nacheinander alle
    Zeilen öffnen, ohne die Suche zu wiederholen; das ist wichtig, weil
    begrenzt ist, wie viele Namen abgefragt werden dürfen, nicht wie viele
    Auszüge.
    """
    d = dict(basis)
    d["javax.faces.ViewState"] = vs
    link = f"idSucheForm:resultTable:{zeile}:auszugLink"
    d[link] = link
    try:
        r = s.post(URL, data=d, timeout=90)
        r.raise_for_status()
    except Exception as e:
        return None, None, f"Auszug nicht erreichbar: {str(e)[:80]}", None
    # Die Weiterleitung trägt bei gelöschten Rechtseinheiten ein Löschdatum:
    # .../auszug.xhtml?loeschung=20040213&uid=CHE-...  Das ist der zuverlässigste
    # Hinweis darauf, dass es die Firma nicht mehr gibt, und damit darauf, dass
    # ein dort eingetragenes Mandat nicht mehr besteht.
    m = re.search(r"[?&]loeschung=(\d{4})(\d{2})(\d{2})", r.url)
    geloescht = f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None
    leute, zweck, fehler = personen_aus_seite(s, r.text)
    return leute, zweck, fehler, geloescht


def ist_die_person(eintrag, nachname, vorname, wohnort=None):
    """Steht in diesem Registereintrag wirklich das gesuchte Ratsmitglied?

    Der Eintrag lautet «Nachname, Vorname Zweitname, von Bürgerort, in Wohnort».
    Geprüft wird auf zwei Wegen, weil keiner allein genügt:

      · Vorname. Das Register führt oft mehrere Vornamen, die Selbstdeklaration
        nur den Rufnamen; darum reicht ein Treffer unter den Vornamen.
      · Wohnort. Er trennt zwei Personen gleichen Namens, sagt aber nichts,
        wenn beide am selben Ort wohnen. Bei «Alaye» ist genau das der Fall:
        Ratsmitglied und Namensvetter wohnen beide in Schaffhausen, dort
        entscheidet allein der Vorname.

    Der Wohnort kann veraltet sein, im Register wie in der Selbstdeklaration.
    Ein abweichender Ort bei stimmendem Vornamen ist darum kein Ausschluss,
    sondern ein Vermerk.
    """
    teile = [t.strip() for t in eintrag.split(",")]
    if not teile or norm(teile[0]) != norm(nachname):
        return "anderer Nachname", None

    vornamen = set(norm(teile[1]).split()) if len(teile) > 1 else set()
    m = re.search(r"\bin\s+(.+)$", eintrag)
    ort_register = m.group(1).strip() if m else None
    ort_gleich = gleiche_gemeinde(wohnort, ort_register)

    if not vornamen:
        # Ohne Vornamen bleibt nur der Ort, und der allein genügt nicht.
        return ("moeglich" if ort_gleich else "unklar"), ort_register

    if norm(vorname) in vornamen:
        if ort_gleich is False:
            return "bestaetigt_anderer_ort", ort_register
        return "bestaetigt", ort_register

    return "namensvetter", ort_register


# ── Kontingent ───────────────────────────────────────────────────────────────

def status_lesen():
    if STATUS.exists():
        return json.loads(STATUS.read_text(encoding="utf-8"))
    return {"zusage": ("Handelsregisteramt des Kantons Schaffhausen, Rückmeldung vom "
                       "2. September 2026: Abfrage in Ordnung, wenn Menge und Zeitpunkt "
                       "verteilt werden, 5 Namen pro Woche, 2 Durchgänge pro Jahr."),
            "grenzen": {"pro_woche": PRO_WOCHE, "durchgaenge_pro_jahr": DURCHGAENGE_PRO_JAHR},
            "durchgaenge": [], "laeufe": []}


def naechste_namen(st, alle, voll=False):
    """Was der nächste Lauf abfragen darf, oder eine Begründung, warum nichts.

    `voll` ist die einmalige Ausnahme: das Amt hat am 2. September 2026
    telefonisch zugestanden, dass einmal alle Namen am Stück abgefragt werden
    dürfen und die Wochenregel danach in einem halben Jahr wieder greift. Diese
    Ausnahme lässt sich nur einmal ziehen, danach sperrt sie sich selbst.
    """
    heute = date.today()

    if voll:
        # Zuerst: läuft bereits ein vollständiger Durchgang? Dann wird er
        # fortgesetzt und kein zweiter angelegt. Ein Lauf über 59 Namen dauert
        # fast eine Stunde und wird zwischendurch abgebrochen; ohne diese
        # Prüfung entstünde bei jedem Neustart ein weiterer Durchgang.
        laufend = [d for d in st["durchgaenge"]
                   if d.get("art") == "vollstaendig" and not d.get("ende")]
        if laufend:
            d = laufend[0]
            rest = [n for n in d["warteschlange"] if n not in d["erledigt"]]
            if rest:
                return rest, None
            d["ende"] = heute.isoformat()
            return [], f"Durchgang {d['nr']} ist abgeschlossen."

        # Verbraucht ist die Ausnahme erst, wenn der Durchgang auch
        # abgeschlossen wurde. Ein Lauf, der wegen eines Fehlers abgebrochen
        # und dessen Daten verworfen wurden, darf nachgeholt werden.
        if any(d.get("art") == "vollstaendig" and d.get("ende") for d in st["durchgaenge"]):
            return [], ("Der vollständige Durchgang wurde bereits gezogen. Er war eine "
                        "einmalige Ausnahme; ab jetzt gilt wieder die Wochenregel.")
        offen_alt = [d for d in st["durchgaenge"] if not d.get("ende")]
        for d in offen_alt:
            d["ende"] = heute.isoformat()
            d["bemerkung"] = "durch den vollständigen Durchgang abgelöst"
        st["durchgaenge"].append({
            "nr": len(st["durchgaenge"]) + 1, "jahr": heute.year,
            "art": "vollstaendig",
            "start": heute.isoformat(), "ende": None,
            "grundlage": ("Telefonische Zusage des Handelsregisteramts vom 2. September "
                          "2026: einmal alle Namen am Stück, danach in einem halben Jahr "
                          "weiter nach der Wochenregel."),
            "warteschlange": alle, "erledigt": []})
        return alle, None

    ab = st.get("wochenregel_ab")
    if ab and heute < date.fromisoformat(ab):
        return [], (f"Nach dem vollständigen Durchgang ist Ruhe vereinbart. Die "
                    f"Wochenregel greift wieder ab {ab}.")

    letzter = st["laeufe"][-1]["datum"] if st["laeufe"] else None
    if letzter:
        vergangen = (heute - date.fromisoformat(letzter)).days
        if vergangen < TAGE_ZWISCHEN_LAEUFEN:
            return [], (f"Der letzte Lauf war vor {vergangen} Tagen. Zugesagt sind "
                        f"5 Namen pro Woche, der nächste Lauf ist ab dem "
                        f"{(date.fromisoformat(letzter) + timedelta(days=TAGE_ZWISCHEN_LAEUFEN)).isoformat()} möglich.")

    offen = [d for d in st["durchgaenge"] if not d.get("ende")]
    if offen:
        d = offen[0]
        rest = [n for n in d["warteschlange"] if n not in d["erledigt"]]
        if rest:
            return rest[:PRO_WOCHE], None
        d["ende"] = heute.isoformat()
        return [], f"Durchgang {d['nr']} ist abgeschlossen."

    # Neuer Durchgang?
    dieses_jahr = [d for d in st["durchgaenge"] if d["jahr"] == heute.year]
    if len(dieses_jahr) >= DURCHGAENGE_PRO_JAHR:
        return [], (f"{len(dieses_jahr)} Durchgänge in {heute.year} abgeschlossen, "
                    f"zugesagt sind {DURCHGAENGE_PRO_JAHR}. Der nächste beginnt "
                    f"frühestens im Januar {heute.year + 1}.")
    if st["durchgaenge"]:
        letztes_ende = st["durchgaenge"][-1].get("ende")
        if letztes_ende:
            warte = date.fromisoformat(letztes_ende) + timedelta(weeks=WOCHEN_ZWISCHEN_DURCHGAENGEN)
            if heute < warte:
                return [], (f"Der letzte Durchgang endete am {letztes_ende}. Damit die "
                            f"beiden Durchgänge übers Jahr verteilt sind, beginnt der "
                            f"nächste am {warte.isoformat()}.")

    nr = len(st["durchgaenge"]) + 1
    st["durchgaenge"].append({"nr": nr, "jahr": heute.year, "start": heute.isoformat(),
                              "ende": None, "warteschlange": alle, "erledigt": []})
    return alle[:PRO_WOCHE], None


# ── Ablauf ───────────────────────────────────────────────────────────────────

def mitglieder():
    m = json.loads(MITGLIEDER.read_text(encoding="utf-8"))
    return sorted(m["mitglieder"], key=lambda p: p["nachname"])


def deklarierte_firmen(p):
    roh = p.get("interessenbindungen") or []
    if isinstance(roh, str):
        try:
            roh = eval(roh)
        except Exception:
            roh = []
    return [x.lstrip("·- ").strip() for x in roh if REGISTERPFLICHTIG.search(x)]


def alle_deklarationen(p):
    """Jede Zeile der Selbstdeklaration, ungefiltert.

    `deklarierte_firmen` siebt auf Namen mit Rechtsform, weil nur solche
    überhaupt im Handelsregister stehen können. Für die Gegenrichtung ist das
    falsch: gefragt ist dort, ob ein Registerfund in der Deklaration schon
    vorkommt, und die Deklaration schreibt Rechtsformen oft nicht mit. Anna
    Brügel deklariert «SAH Schaffhausen (Schweizerisches Arbeitshilfswerk)»
    ohne Rechtsform; mit dem Filter galt ihr Vorstandsmandat als nicht
    deklariert, obwohl es dasteht.
    """
    roh = p.get("interessenbindungen") or []
    if isinstance(roh, str):
        try:
            roh = eval(roh)
        except Exception:
            roh = []
    return [x.lstrip("·- ").strip() for x in roh if x and x.strip()]


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


# Wörter, die für den Abgleich zweier Firmennamen nichts hergeben.
FUELLWORT = {"ag", "gmbh", "sa", "sarl", "genossenschaft", "stiftung", "holding",
             "verein", "co", "und", "der", "die", "das", "fuer", "von", "in",
             "kanton", "schaffhausen", "liquidation", "mitglied", "praesident",
             "verwaltungsrat", "stiftungsrat", "vorstand", "geschaeftsfuehrer",
             "inhaber", "gesellschafter"}


def firma_passt(register, deklarationen):
    """Meint die Deklaration dieselbe Firma wie der Registereintrag?

    Der frühere Vergleich verlangte, dass ein Name im anderen enthalten ist.
    Das scheitert an Alltäglichem: deklariert ist «Energieverbund Neuhausen AG»,
    im Register steht «Energieverbund Neuhausen am Rheinfall AG». Keiner der
    beiden enthält den anderen, und die Firma wäre fälschlich als nicht
    deklariert gemeldet worden, mitsamt dem Namen des Ratsmitglieds.

    Verglichen werden darum die tragenden Wörter. Stimmen sie überwiegend
    überein, gilt die Firma als deklariert. Im Zweifel lieber als deklariert
    behandeln: eine übersehene Deklaration kostet einen Fund, eine erfundene
    kostet den Ruf einer Person.
    """
    r = {w for w in norm(register).split() if len(w) > 2 and w not in FUELLWORT}
    if not r:
        return True
    for d in deklarationen:
        w = {x for x in norm(d).split() if len(x) > 2 and x not in FUELLWORT}
        if not w:
            continue
        gemein = len(r & w)
        if gemein and gemein / min(len(r), len(w)) >= 0.6:
            return True
    return False


def bericht():
    """Register gegen Deklaration halten. Reine Prüfhinweise, keine Feststellung."""
    if not ZIEL.exists():
        print(f"{ZIEL.name} fehlt, zuerst abfragen.")
        return
    daten = json.loads(ZIEL.read_text(encoding="utf-8"))
    leute = {p["name"]: p for p in mitglieder()}

    print(f"Abgefragt: {len(daten['personen'])} von {len(leute)} Ratsmitgliedern\n")
    offen = ungeprueft = vetter = 0
    for name, e in sorted(daten["personen"].items()):
        p = leute.get(name)
        if not p:
            continue
        dekl = deklarierte_firmen(p)
        dnorm = [norm(x) for x in dekl]
        # Aus der Adresse abgeleitet und nicht aus den gespeicherten Daten:
        # so gilt der Hinweis auch für Abfragen, die vor dieser Prüfung liefen.
        ort_bekannt = bool(gemeinde(p.get("adresse"), name))
        vetter += sum(1 for t in e["treffer"] if t.get("urteil") == "namensvetter")
        ungeprueft += sum(1 for t in e["treffer"] if t.get("urteil") in ("ungeprueft", "unklar"))

        # Nur was am Auszug auf diese Person lautet und nicht deklariert ist
        neu = []
        for t in e["treffer"]:
            if not str(t.get("urteil", "")).startswith("bestaetigt"):
                continue
            if not t.get("aktuell"):
                continue        # gestrichener Eintrag: das Mandat ist beendet
            if not firma_passt(t["firma"], alle_deklarationen(p)):
                neu.append(t)
        if neu:
            offen += len(neu)
            print(f"· {name} ({p.get('fraktion','')})")
            print(f"   deklariert: {', '.join(dekl) if dekl else 'keine Firma'}")
            for t in neu:
                if t.get("urteil") == "bestaetigt_anderer_ort":
                    warn = ("   ACHTUNG Wohnort weicht ab, möglicherweise eine andere "
                            "Person gleichen Namens\n")
                elif not ort_bekannt:
                    warn = ("   ACHTUNG keine Adresse hinterlegt, die Zuordnung ruht "
                            "allein auf dem Vornamen\n")
                else:
                    warn = ""
                print(warn + f"   im Register zusätzlich: {t['firma']}, {t['sitz']} "
                      f"({t['rechtsform']}, {t['uid']})")
                print(f"      eingetragen als: {t['person']['eintrag']}")
                print(f"      Funktion: {t['person']['funktion']}, "
                      f"{t['person']['zeichnung']}")
                print(f"      Auszug: {AUSZUG}?uid={t['uid']}")
            print()

    print(f"{offen} Firmen sind am Registerauszug auf das Ratsmitglied selbst "
          f"eingetragen, ohne dass ein passender Eintrag in der Selbstdeklaration "
          f"erkennbar ist.")
    print(f"{vetter} weitere Treffer betreffen Namensvettern und sind aussortiert, "
          f"{ungeprueft} liessen sich nicht abschliessend zuordnen.\n")
    print("Auch das Bestätigte bleibt ein Prüfhinweis. Der Abgleich mit der Deklaration "
          "läuft über den Firmennamen und erkennt eine anders geschriebene Umschreibung "
          "nicht. Ein Mandat kann seit der Deklaration beendet worden sein, und die "
          "Deklaration selbst kann veraltet sein. Verbindlich ist allein der beglaubigte "
          "Registerauszug. Vor jeder Veröffentlichung den Auszug ansehen und, wenn es "
          "eng wird, das Ratsmitglied fragen.")


def neu_beurteilen():
    """Die gespeicherten Treffer noch einmal beurteilen, ohne Netzzugriff.

    Die Personalangaben aus den Registerauszügen liegen bereits in
    hr_personen.json. Ändert sich die Beurteilungsgrundlage, etwa weil eine
    Wohngemeinde nachgetragen wurde, lässt sich alles daraus neu ableiten. Das
    schont das zugesagte Kontingent: neu abgefragt wird nichts.
    """
    if not ZIEL.exists():
        print(f"{ZIEL.name} fehlt.")
        return
    daten = json.loads(ZIEL.read_text(encoding="utf-8"))
    leute = {p["name"]: p for p in mitglieder()}
    geaendert = 0
    for name, e in daten["personen"].items():
        p = leute.get(name)
        if not p:
            continue
        wohnort = gemeinde(p.get("adresse"), name)
        for t in e["treffer"]:
            leute_reg = t.get("eingetragene")
            if not leute_reg:
                continue
            vorher = t.get("urteil")
            urteile = []
            for x in leute_reg:
                u, ort = ist_die_person(x["eintrag"], p["nachname"], p["vorname"], wohnort)
                x["ort_register"] = ort
                urteile.append((u, x))
            for stufe in ("bestaetigt", "bestaetigt_anderer_ort", "moeglich",
                          "namensvetter", "unklar"):
                passend = sorted((x for u, x in urteile if u == stufe),
                                 key=lambda x: bool(x.get("geloescht")))
                if passend:
                    t["urteil"] = stufe
                    t["person"] = passend[0]
                    t["aktuell"] = not passend[0].get("geloescht")
                    break
            else:
                t["urteil"] = "unklar"; t["person"] = None; t["aktuell"] = None
            t["ort_geprueft"] = bool(wohnort)
            if t["urteil"] != vorher:
                geaendert += 1
                print(f"   {name:24} {t['firma'][:40]:40} {vorher} -> {t['urteil']}")
    ZIEL.write_text(json.dumps(daten, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{geaendert} Urteile geändert, keine neue Abfrage.")


def firmen_pruefen():
    """Für die gespeicherten Treffer nachtragen, ob es die Firma noch gibt.

    Der schlichte Aufruf auszug.xhtml?uid=... liefert nur für bestehende
    Rechtseinheiten Inhalt; bei gelöschten bleibt die Seite leer, weil die
    Adresse ohne Löschdatum nicht auflöst. Das ist ein kostenloser Test: begrenzt
    sind die Namensabfragen, nicht die Auszüge.

    Nötig wurde er nach der ersten Handprüfung. Von fünf Kandidaten waren vier
    falsch, und drei davon betrafen Firmen, die es gar nicht mehr gibt. Sie
    tauchen nur auf, weil die Suche mit «auch gelöschte Firmen» läuft; von Hand
    findet man sie nicht einmal.
    """
    if not ZIEL.exists():
        print(f"{ZIEL.name} fehlt.")
        return
    daten = json.loads(ZIEL.read_text(encoding="utf-8"))
    # Zeitbudget wie beim Abfragelauf: nach einem vollständigen Durchgang sind
    # mehrere hundert Firmen zu prüfen, das dauert länger, als manche Umgebung
    # einen einzelnen Aufruf leben lässt. Darum wird der Stand laufend
    # geschrieben und der nächste Aufruf setzt fort; bereits geprüfte Firmen
    # überspringt die Schleife ohnehin. Das ändert nichts an den zugesagten
    # Grenzen: begrenzt sind die Namensabfragen, nicht die Auszüge.
    budget = None
    if "--minuten" in sys.argv:
        budget = time.time() + float(sys.argv[sys.argv.index("--minuten") + 1]) * 60
    gesehen, neu = {}, 0
    knapp = False
    for name, e in daten["personen"].items():
        if knapp:
            break
        for t in e["treffer"]:
            # Bereits geprüft und entweder gelöscht oder mit Zweck versehen:
            # dann gibt es nichts mehr zu holen.
            if t.get("firma_besteht") is False:
                continue
            if t.get("firma_besteht") is True and t.get("zweck"):
                continue
            uid = t["uid"]
            if uid not in gesehen:
                if budget and time.time() > budget:
                    knapp = True
                    break
                s = sitzung()
                leute, zweck, fehler = personen_aus_seite(
                    s, s.get(AUSZUG, params={"uid": uid}, timeout=60).text)
                gesehen[uid] = (bool(leute), zweck)
                time.sleep(0.4)
            t["firma_besteht"], zw = gesehen[uid]
            if zw and not t.get("zweck"):
                t["zweck"] = zw
            neu += 1
    ZIEL.write_text(json.dumps(daten, ensure_ascii=False, indent=1), encoding="utf-8")
    weg = sum(1 for v, _ in gesehen.values() if not v)
    print(f"{neu} Treffer nachgetragen, {len(gesehen)} Firmen geprüft, "
          f"davon {weg} gelöscht.")
    offen = len({t["uid"] for e in daten["personen"].values() for t in e["treffer"]
                 if t.get("firma_besteht") is None})
    if offen:
        print(f"Zeitbudget erreicht, noch {offen} Firmen offen. "
              f"Nächster Aufruf setzt fort.")


def suchbegriff(p, mit_vorname):
    """Was ins Feld «Person» geschrieben wird.

    Der Nachname allein ist bei häufigen Namen unbrauchbar: das Portal zeigt nur
    die erste Seite mit zwanzig Zeilen, und für «Müller» meldet es 500 Treffer.
    Nachname und Vorname zusammen grenzen so weit ein, dass die Liste
    vollständig zurückkommt: aus 500 Treffern für «Leu» werden 12 für «Leu
    Markus», der gesuchte Eintrag ist darunter. Die Reihenfolge folgt der
    Schreibweise im Register («Leu, Markus»).

    Beurteilt wird trotzdem weiter am Auszug. Die engere Suche spart die
    Namensvettern, sie ersetzt die Prüfung nicht: auch «Leu Markus» liefert
    Firmen, in denen ein anderer Markus Leu eingetragen ist.
    """
    if not mit_vorname:
        return p["nachname"]
    return f"{p['nachname']} {p['vorname'].split()[0]}"


def treffer_beurteilen(s, p, treffer, basis, nach_vs):
    """Jeden Treffer am Registerauszug prüfen und einordnen.

    Die Suche läuft über den Namen und wirft Namensvettern zusammen; erst der
    Auszug nennt die Vornamen. Diese Aufrufe gehören zur selben Person und
    brauchen darum keine Pause zwischen sich.
    """
    bestaetigt = beendet = 0
    wohnort = gemeinde(p.get("adresse"), p.get("name"))
    for zeile, t in enumerate(treffer):
        leute, zweck, fehler, firma_weg = auszug_von_zeile(s, basis, nach_vs, zeile)
        t["firma_geloescht"] = firma_weg
        t["zweck"] = zweck
        if fehler:
            t["person"] = None
            t["urteil"] = "ungeprueft"
            t["fehler"] = fehler
            continue
        t["eingetragene"] = leute
        urteile = []
        for e in leute:
            u, ort = ist_die_person(e["eintrag"], p["nachname"], p["vorname"], wohnort)
            e["ort_register"] = ort
            urteile.append((u, e))
        # Reihenfolge der Sicherheit: eindeutig, dann mit Ortsvorbehalt,
        # dann nur über den Ort gestützt, dann ausgeschlossen. Innerhalb
        # einer Stufe zählt ein bestehender Eintrag mehr als ein
        # gestrichener: gestrichen heisst, das Mandat ist beendet.
        for stufe in ("bestaetigt", "bestaetigt_anderer_ort", "moeglich",
                      "namensvetter", "unklar"):
            passend = sorted((e for u, e in urteile if u == stufe),
                             key=lambda e: bool(e.get("geloescht")))
            if passend:
                t["urteil"] = stufe
                t["person"] = passend[0]
                t["aktuell"] = not passend[0].get("geloescht")
                # Ohne hinterlegte Adresse ruht die Zuordnung allein auf dem
                # Vornamen. Bei drei Ratsmitgliedern führt sh.ch keine
                # Adresse; dort fehlt die zweite Stütze, und das muss im
                # Bericht sichtbar sein statt stillschweigend zu gelten.
                t["ort_geprueft"] = bool(wohnort)
                if stufe.startswith("bestaetigt"):
                    bestaetigt += 1
                    if not t["aktuell"]:
                        beendet += 1
                break
        else:
            t["urteil"] = "unklar"
            t["person"] = None
            t["aktuell"] = None
    return bestaetigt, beendet


def melden(name, treffer, bestaetigt, beendet, hinweis):
    """Die Zeilen, die ein Lauf je Person ausgibt."""
    vetter = sum(1 for t in treffer if t.get("urteil") == "namensvetter")
    print(f"   {name:28} {len(treffer)} Treffer, davon {bestaetigt} bestätigt"
          + (f" ({beendet} beendet)" if beendet else "")
          + (f", {vetter} Namensvetter" if vetter else "")
          + (f"  ({hinweis})" if hinweis else ""))
    for t in treffer:
        if str(t.get("urteil", "")).startswith("bestaetigt"):
            print(f"        · {t['firma']}, {t['sitz']}: {t['person']['funktion']}"
                  + ("" if t.get("aktuell") else "  [beendet]"))


def probe():
    """Eine einzelne Suche, nur um zu sehen, wie das Suchfeld reagiert.

    Öffnet keine Auszüge und schreibt nichts. Gedacht für die Frage, in welcher
    Schreibweise das Feld «Person» Vorname und Nachname versteht, bevor ein
    ganzer Stapel Namen darauf umgestellt wird. Eine Suche statt siebenundzwanzig
    ist die schonendere Art, das herauszufinden.
    """
    begriff = sys.argv[sys.argv.index("--probe") + 1]
    s = sitzung()
    vs, knopf, haken = formular(s)
    if "--roh" in sys.argv:
        # Für die Frage, was «Trefferzahl nicht gefunden» bedeutet: eine leere
        # Ergebnismenge oder eine Seite, die das Skript nicht liest.
        d = {"idSucheForm": "idSucheForm", "idSucheForm:idFirma": "",
             "idSucheForm:idPerson": begriff,
             "idSucheForm:panel:idRechtsform_input": "",
             "idSucheForm:panel:idSitz_input": "", "idSucheForm:panel:idSitz_hinput": "",
             "idSucheForm:panel:idShabDatum_input": "", "idSucheForm:panel:idShabNummer": "",
             "idSucheForm:panel:idDiverseTyp_input": "",
             "idSucheForm:panel:idDiverseSuchtext": "", "idSucheForm:panel_active": "-1",
             knopf: knopf, "javax.faces.ViewState": vs,
             "javax.faces.partial.ajax": "true", "javax.faces.source": knopf,
             "javax.faces.partial.execute": "@all",
             "javax.faces.partial.render": "idSucheForm"}
        for k in haken:
            d[k] = "on"
        t = html.unescape(s.post(URL, data=d, timeout=90,
                                 headers={"Faces-Request": "partial/ajax",
                                          "X-Requested-With": "XMLHttpRequest"}).text)
        print(f"Antwort {len(t)} Zeichen")
        for muster in ("Anzahl gefundene Firmen", "Number of companies found",
                       "Keine Datensätze", "No records", "resultTable_data",
                       "Zu viele", "too many", "genauer", "einschränken"):
            if muster.lower() in t.lower():
                i = t.lower().find(muster.lower())
                print(f"  gefunden {muster!r}: …{re.sub(r'<[^>]+>', ' ', t[i-80:i+160])}…")
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)).strip()
        print("\nSichtbarer Text:\n" + text[:1500])
        return
    treffer, hinweis, _, _ = suche(s, begriff, vs, knopf, haken)
    print(f"Suchbegriff: {begriff!r}")
    if treffer is None:
        print(f"Kein auswertbares Ergebnis: {hinweis}")
        return
    print(f"{len(treffer)} Zeilen gelesen" + (f"  ({hinweis})" if hinweis else ""))
    for t in treffer[:12]:
        print(f"   {t['uid']}  {t['firma']}, {t['sitz']}")


def unvollstaendig(daten):
    """Namen, deren gespeichertes Ergebnis nicht belastbar ist.

    Zwei Sorten: Trefferlisten, von denen das Portal nur die erste Seite mit
    zwanzig Zeilen herausgegeben hat, und Namen, bei denen es die Trefferzahl
    gar nicht erst gemeldet hat. Beide Male steht der Grund im Feld «hinweis».
    """
    raus = []
    for name, e in daten["personen"].items():
        h = e.get("hinweis") or ""
        if "angezeigt sind" in h or "Trefferzahl nicht gefunden" in h:
            raus.append(name)
    return sorted(raus)


def nachfassen():
    """Die unvollständigen Namen erneut abfragen, mit Vorname und Nachname.

    Grundlage ist der Entscheid von Michael vom 2. September 2026. Der
    vollständige Durchgang desselben Tages hat bei 24 von 59 Namen nur die
    erste Seite der Trefferliste erhalten und bei 3 Namen gar kein auswertbares
    Ergebnis. Für diese Namen ist der Durchgang faktisch nicht erfolgt, und die
    engere Suche behebt genau das: sie liefert dieselben Mandate in einer Liste,
    die vollständig zurückkommt.

    Die Auflagen des Amts bleiben in Kraft. Die 45 Sekunden zwischen zwei
    Personen werden eingehalten, jeder Lauf wird protokolliert, und der Stand
    wird nach jeder Person gesichert, damit ein Abbruch keine Abfrage doppelt
    nötig macht. Dass dieser Stapel über die im Skript hinterlegte Zusage
    hinausgeht, steht im Protokoll, damit es gegenüber dem Amt sichtbar ist und
    nicht in der Zahl der Läufe verschwindet.

    Die neuen Treffer werden zu den alten gelegt, nicht an ihre Stelle. Sollte
    die engere Suche einen Eintrag nicht finden, den der Nachname allein gefunden
    hat, geht er dadurch nicht verloren.
    """
    if not ZIEL.exists():
        print(f"{ZIEL.name} fehlt.")
        return
    daten = json.loads(ZIEL.read_text(encoding="utf-8"))
    st = status_lesen()
    leute = {p["name"]: p for p in mitglieder()}

    stand = st.setdefault("nachfassen", {})
    if not stand:
        stand.update({
            "start": date.today().isoformat(), "ende": None,
            "grundlage": ("Entscheid von Michael vom 2. September 2026. Der vollständige "
                          "Durchgang vom selben Tag lieferte bei diesen Namen nur die "
                          "erste Seite der Trefferliste oder gar keine Trefferzahl. Sie "
                          "werden mit Vorname und Nachname erneut abgefragt, weil die "
                          "engere Suche eine vollständige Liste zurückgibt. Dieser Stapel "
                          "geht über die Zusage des Amts vom 2. September 2026 hinaus."),
            "warteschlange": unvollstaendig(daten), "erledigt": []})

    if "--erneut" in sys.argv:
        # Namen, deren Lauf «Trefferzahl nicht gefunden» ergeben hat, noch einmal.
        # Bis zur Erkennung der leeren Ergebnismenge liess sich nicht sagen, ob
        # das Portal nichts gefunden oder das Skript nichts gelesen hat. Jetzt
        # lässt es sich, und die betroffenen Namen bekommen ein klares Ergebnis.
        wieder = [n for n in stand["erledigt"]
                  if "Trefferzahl nicht gefunden"
                  in (daten["personen"].get(n, {}).get("hinweis") or "")]
        stand["erledigt"] = [n for n in stand["erledigt"] if n not in wieder]
        stand["ende"] = None
        stand.setdefault("bemerkungen", []).append(
            {"am": date.today().isoformat(),
             "was": f"{len(wieder)} Namen erneut abgefragt, nachdem das Skript die leere "
                    f"Ergebnismenge des Portals erkennen gelernt hat: "
                    f"{', '.join(wieder)}"})
        print(f"{len(wieder)} Namen zurückgestellt: {', '.join(wieder)}")

    offen = [n for n in stand["warteschlange"] if n not in stand["erledigt"]]
    if not offen:
        stand["ende"] = date.today().isoformat()
        STATUS.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"Nachfassen abgeschlossen, {len(stand['erledigt'])} Namen.")
        return

    print(f"Nachfassen: {len(stand['erledigt'])} von {len(stand['warteschlange'])} erledigt.")
    if "--apply" not in sys.argv:
        print(f"Offen: {', '.join(offen)}")
        print("\n(Probelauf, nichts abgefragt. Mit --apply abfragen.)")
        return

    budget = None
    if "--minuten" in sys.argv:
        budget = time.time() + float(sys.argv[sys.argv.index("--minuten") + 1]) * 60

    for i, name in enumerate(offen):
        if budget and time.time() > budget:
            print(f"\nZeitbudget erreicht, {len(stand['erledigt'])} von "
                  f"{len(stand['warteschlange'])} erledigt. Nächster Aufruf setzt fort.")
            break
        p = leute.get(name)
        if not p:
            print(f"   ! {name}: nicht in mitglieder.json")
            stand["erledigt"].append(name)
            continue
        try:
            s = sitzung()
            vs, knopf, haken = formular(s)
            treffer, hinweis, basis, nach_vs = suche(
                s, suchbegriff(p, True), vs, knopf, haken)
        except Exception as e:
            print(f"   ! {name}: {str(e)[:120]}")
            break
        if treffer is None:
            print(f"   {name:28} übersprungen: {hinweis}")
            continue

        bestaetigt, beendet = treffer_beurteilen(s, p, treffer, basis, nach_vs)
        alt = daten["personen"].get(name, {}).get("treffer", [])
        bekannt = {(t["uid"], t.get("firma"), t.get("sitz")) for t in alt}
        dazu = [t for t in treffer
                if (t["uid"], t.get("firma"), t.get("sitz")) not in bekannt]
        daten["personen"][name] = {
            "nachname": p["nachname"], "vorname": p["vorname"],
            "abgefragt": date.today().isoformat(),
            "treffer": alt + dazu,
            "hinweis": hinweis,
            "nachgefasst": {"am": date.today().isoformat(),
                            "begriff": suchbegriff(p, True),
                            "vorher": len(alt), "neu": len(dazu)}}
        stand["erledigt"].append(name)
        melden(name, treffer, bestaetigt, beendet, hinweis)
        if dazu:
            print(f"        {len(dazu)} Treffer waren vorher nicht in der Liste.")

        daten["stand"] = date.today().isoformat()
        ZIEL.write_text(json.dumps(daten, ensure_ascii=False, indent=1), encoding="utf-8")
        STATUS.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
        if i < len(offen) - 1:
            time.sleep(PAUSE_JE_PERSON)

    st["laeufe"].append({"datum": date.today().isoformat(),
                         "zeit": datetime.now().strftime("%H:%M"),
                         "namen": offen, "art": "nachfassen"})
    if len(stand["erledigt"]) >= len(stand["warteschlange"]):
        stand["ende"] = date.today().isoformat()
        print("\nNachfassen abgeschlossen.")
    ZIEL.write_text(json.dumps(daten, ensure_ascii=False, indent=1), encoding="utf-8")
    STATUS.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    rest = len(stand["warteschlange"]) - len(stand["erledigt"])
    print(f"\nNoch offen: {rest} Namen.")


def main():
    if "--probe" in sys.argv:
        return probe()
    if "--nachfassen" in sys.argv:
        return nachfassen()
    if "--firmen-pruefen" in sys.argv:
        return firmen_pruefen()
    if "--neu-beurteilen" in sys.argv:
        return neu_beurteilen()
    if "--bericht" in sys.argv:
        return bericht()
    if "--auszug" in sys.argv:
        # Einzelner Auszug, für die Kontrolle von Hand. Zählt nicht gegen das
        # Kontingent: begrenzt sind die Namensabfragen, nicht die Auszüge.
        uid = sys.argv[sys.argv.index("--auszug") + 1]
        s = sitzung()
        leute, zweck, fehler = personen_aus_seite(s, s.get(AUSZUG, params={"uid": uid},
                                                          timeout=60).text)
        if fehler:
            print(f"{fehler}\nBei gelöschten Rechtseinheiten braucht die Adresse "
                  f"zusätzlich das Löschdatum; die findet der Lauf über die Trefferzeile.")
            return
        if zweck:
            print(f"Zweck: {kuerzen(zweck, 300)}\n")
        for e in leute:
            print(("gelöscht: " if e.get("geloescht") else "") + e["eintrag"])
            print(f"   {e['funktion']}, {e['zeichnung']}")
        return

    schreiben = "--apply" in sys.argv
    voll = "--vollstaendig" in sys.argv
    st = status_lesen()
    leute = mitglieder()
    alle = [p["name"] for p in leute]
    nach_name = {p["name"]: p for p in leute}

    dran, grund = naechste_namen(st, alle, voll)
    if not dran:
        print(grund)
        if schreiben:
            STATUS.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
        return

    d = [x for x in st["durchgaenge"] if not x.get("ende")][0]
    erledigt = len(d["erledigt"])
    print(f"Durchgang {d['nr']} ({d['jahr']}), gestartet {d['start']}: "
          f"{erledigt} von {len(alle)} erledigt.")
    print(f"Dieser Lauf fragt {len(dran)} Namen ab: {', '.join(dran)}")
    if not schreiben:
        print("\n(Probelauf, nichts abgefragt und nichts geschrieben. Mit --apply abfragen.)")
        return

    daten = json.loads(ZIEL.read_text(encoding="utf-8")) if ZIEL.exists() else {"personen": {}}
    # Zeitbudget: ein vollständiger Durchgang dauert bei 45 Sekunden Pause fast
    # eine Stunde. Wo die Umgebung lange Läufe abbricht, hält das Skript von
    # selbst rechtzeitig an und schreibt den Stand; der nächste Aufruf macht
    # weiter, wo dieser aufgehört hat.
    budget = None
    if "--minuten" in sys.argv:
        budget = time.time() + float(sys.argv[sys.argv.index("--minuten") + 1]) * 60

    for i, name in enumerate(dran):
        if budget and time.time() > budget:
            print(f"\nZeitbudget erreicht, {len(d['erledigt'])} von "
                  f"{len(d['warteschlange'])} erledigt. Nächster Aufruf setzt fort.")
            break
        p = nach_name[name]
        # Für jede Person eine frische Sitzung. Das Portal hält die Trefferliste
        # in der Sitzung: eine zweite Suche in derselben Sitzung liefert die
        # Tabelle der ersten zurück, während die gemeldete Trefferzahl schon zur
        # neuen gehört. Wer das übersieht, schreibt einem Ratsmitglied die
        # Firmen des zuvor gesuchten zu. Genau das ist beim ersten Lauf
        # passiert. Eine eigene Sitzung je Name kostet einen Seitenaufruf und
        # schliesst den Fehler aus.
        try:
            s = sitzung()
            vs, knopf, haken = formular(s)
            treffer, hinweis, basis, nach_vs = suche(
                s, suchbegriff(p, False), vs, knopf, haken)
        except Exception as e:
            print(f"   ! {name}: {str(e)[:120]}")
            break
        if treffer is None:
            # Unstimmige Antwort: der Name bleibt in der Warteschlange und wird
            # beim nächsten Lauf erneut abgefragt. Der Lauf zählt trotzdem
            # gegen das Kontingent, denn die Abfrage hat stattgefunden.
            print(f"   {name:28} übersprungen: {hinweis}")
            continue

        bestaetigt, beendet = treffer_beurteilen(s, p, treffer, basis, nach_vs)

        daten["personen"][name] = {"nachname": p["nachname"], "vorname": p["vorname"],
                                   "abgefragt": date.today().isoformat(),
                                   "treffer": treffer, "hinweis": hinweis}
        d["erledigt"].append(name)
        melden(name, treffer, bestaetigt, beendet, hinweis)

        # Zwischenstand sichern: ein vollständiger Durchgang dauert fast eine
        # Stunde, ein Abbruch darf die bisherigen Personen nicht kosten.
        daten["stand"] = date.today().isoformat()
        ZIEL.write_text(json.dumps(daten, ensure_ascii=False, indent=1), encoding="utf-8")
        STATUS.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")

        if i < len(dran) - 1:
            time.sleep(PAUSE_JE_PERSON)

    st["laeufe"].append({"datum": date.today().isoformat(),
                         "zeit": datetime.now().strftime("%H:%M"),
                         "namen": dran, "durchgang": d["nr"]})
    if len(d["erledigt"]) >= len(d["warteschlange"]):
        d["ende"] = date.today().isoformat()
        print(f"\nDurchgang {d['nr']} abgeschlossen.")
        if d.get("art") == "vollstaendig":
            # Ein halbes Jahr Ruhe, dann wieder fünf Namen pro Woche.
            weiter = date.today() + timedelta(weeks=26)
            st["wochenregel_ab"] = weiter.isoformat()
            print(f"Die Wochenregel greift wieder ab {weiter.isoformat()}.")

    daten["stand"] = date.today().isoformat()
    daten["quelle"] = ("Personensuche im Handelsregister des Kantons Schaffhausen "
                       "(sh.chregister.ch), abgefragt mit Zusage des Amts vom 02.09.2026")
    ZIEL.write_text(json.dumps(daten, ensure_ascii=False, indent=1), encoding="utf-8")
    STATUS.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    rest = len(d["warteschlange"]) - len(d["erledigt"])
    print(f"\n{ZIEL.name} und {STATUS.name} geschrieben. Noch offen in diesem "
          f"Durchgang: {rest} Namen, das sind {-(-rest // PRO_WOCHE)} weitere Wochen.")


if __name__ == "__main__":
    main()

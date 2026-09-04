#!/usr/bin/env python3
"""Livestream-Zeitmarken des Kantonsrats den namentlichen Abstimmungen zuordnen.

Aufruf aus der Projektwurzel:
    python3 scripts/youtube.py            # neue Videos holen, zuordnen, Bericht
    python3 scripts/youtube.py --neu      # alle Videos frisch laden (Kapitel nachgetragen?)
    python3 scripts/youtube.py --bericht  # nur zuordnen und berichten, nichts laden

Quelle: die Playlist des Kantons (PLAYLIST). Zu jeder Sitzung stellt der Kanton ein
Video ein, dessen Beschreibung die Traktanden mit Zeitmarken auflistet
(«02:20:20 : Bericht und Antrag des Regierungsrates vom 14. Januar 2025 betreffend
Änderung des Justizgesetzes …»). Diese Zeilen sind die Kapitel des Videos.

Schritte
1. Playlist lesen (ohne API-Schluessel, aus der Seite selbst; Fortsetzung ueber
   den Innertube-Endpunkt, wenn die Liste mehr als 100 Videos hat).
2. Je Video Titel, Datum und Beschreibung lesen, Kapitel daraus parsen. Ergebnis
   in data/youtube.json (Cache; ein Video wird nur neu geladen, wenn es fehlt,
   noch keine Kapitel hat oder --neu gesetzt ist).
3. Zuordnung: Sitzung und Video ueber das Datum; Abstimmung und Kapitel ueber das
   Geschaeft. Massgebend ist das Datum im Geschaeft («vom 14. Januar 2025»),
   ersatzweise die Wortueberdeckung des Kapiteltexts mit dem Geschaeft, mindestens
   RATE. Ergebnis in data/youtube_zuordnung.json, das build3.py einliest.

Grenzen
- Das Kapitel beginnt beim Aufruf des Geschaefts, nicht bei der Abstimmung; die
  Karte sagt darum «Debatte ab 2:20:20».
- Abstimmungen ohne Geschaeft (Anträge zur Traktandenliste, Wahlen ohne
  Traktandum) bleiben ohne Zeitmarke.
- Sitzungen vor dem ersten Video der Playlist bleiben ohne Zeitmarke.
"""

from __future__ import annotations

import concurrent.futures
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CACHE = DATA / "youtube.json"
ZUORDNUNG = DATA / "youtube_zuordnung.json"
PLAYLIST = "PL5I6CkmZNYeeEGoz_0uwXjEKFx4ibRScD"
UA = {"User-Agent": "Mozilla/5.0 (Politspiegel)", "Accept-Language": "de",
      "Cookie": "CONSENT=YES+cb; SOCS=CAI"}
RATE = 0.6
# Woerter, die fast jedes Traktandum enthaelt und darum nichts unterscheiden
FUELL = set("der die das des dem den und vom zum zur zu im in an auf für fuer mit von bericht antrag "
            "regierungsrats kantonsrats betreffend genehmigung nr über ueber eines einer eine ein".split())
MONATE = {m: i for i, m in enumerate(
    ["januar", "februar", "märz", "april", "mai", "juni", "juli", "august",
     "september", "oktober", "november", "dezember"], 1)}


def holen(url: str, daten: bytes | None = None, kopf: dict | None = None) -> str:
    req = urllib.request.Request(url, data=daten, headers={**UA, **(kopf or {})})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8", "replace")


# ---------------------------------------------------------------- Playlist
def playlist_ids() -> list[str]:
    t = holen(f"https://www.youtube.com/playlist?list={PLAYLIST}")
    ids: list[str] = []
    # Die Seite baut die Liste je nach Version anders (playlistVideoRenderer oder
    # lockupViewModel); die Video-IDs stehen in jeder Fassung als "videoId".
    # Fremde Videos (Empfehlungen) fallen spaeter ueber den Titel heraus.
    for i in re.findall(r'"videoId":"([A-Za-z0-9_-]{11})"', t):
        if i not in ids:
            ids.append(i)
    # Fortsetzung (mehr als 100 Videos)
    schluessel = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', t)
    version = re.search(r'"INNERTUBE_CLIENT_VERSION":"([^"]+)"', t)
    token = re.search(r'"continuationCommand":\{"token":"([^"]+)"', t)
    runden = 0
    while token and schluessel and version and runden < 20:
        runden += 1
        body = json.dumps({"context": {"client": {"clientName": "WEB", "clientVersion": version.group(1), "hl": "de"}},
                           "continuation": token.group(1)}).encode()
        try:
            antwort = holen(f"https://www.youtube.com/youtubei/v1/browse?key={schluessel.group(1)}&prettyPrint=false",
                            body, {"Content-Type": "application/json"})
        except Exception as e:
            print(f"  Hinweis: Fortsetzung der Playlist nicht lesbar ({e}); {len(ids)} Videos.")
            break
        neu = [i for i in re.findall(r'"videoId":"([A-Za-z0-9_-]{11})"', antwort) if i not in ids]
        ids.extend(neu)
        token = re.search(r'"continuationCommand":\{"token":"([^"]+)"', antwort)
        if not neu:
            break
    return ids


# ---------------------------------------------------------------- Video
def datum_aus_titel(titel: str) -> str | None:
    """«Kantonsratssitzung 24. August 2026» -> 24.08.2026"""
    m = re.search(r"(\d{1,2})\.\s*([A-Za-zäöü]+)\s+(\d{4})", titel)
    if not m or m.group(2).lower() not in MONATE:
        return None
    return f"{int(m.group(1)):02d}.{MONATE[m.group(2).lower()]:02d}.{m.group(3)}"


def kapitel_aus_beschreibung(text: str) -> list[dict]:
    """Zeilen «HH:MM:SS : Text», Folgezeilen ohne Zeitmarke haengen am Kapitel."""
    kap: list[dict] = []
    for zeile in text.splitlines():
        m = re.match(r"^\s*(\d{1,2}):(\d{2})(?::(\d{2}))?\s*:\s*(.*)$", zeile)
        if m:
            h, mi, s = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
            kap.append({"s": h * 3600 + mi * 60 + s, "text": m.group(4).strip()})
        elif kap and zeile.strip() and not zeile.startswith("___") and "youtube.com" not in zeile:
            kap[-1]["text"] = (kap[-1]["text"] + " " + zeile.strip()).strip()
    return kap


def video_lesen(vid: str) -> dict:
    t = holen(f"https://www.youtube.com/watch?v={vid}")
    m = re.search(r"ytInitialPlayerResponse\s*=\s*(\{.*?\});", t)
    d = json.loads(m.group(1)) if m else {}
    vd = d.get("videoDetails", {})
    titel = vd.get("title", "")
    return {"titel": titel, "datum": datum_aus_titel(titel),
            "dauer": int(vd.get("lengthSeconds") or 0),
            "kapitel": kapitel_aus_beschreibung(vd.get("shortDescription", ""))}


# ---------------------------------------------------------------- Zuordnung
def norm(s: str) -> str:
    s = s.lower().replace("regierungsrates", "regierungsrats").replace("kantonsrates", "kantonsrats")
    return re.sub(r"[^a-z0-9äöüé ]+", " ", s)


def woerter(s: str) -> set[str]:
    return {w for w in norm(s).split() if w not in FUELL and len(w) > 1}


def geschaeftsdatum(s: str) -> str | None:
    m = re.search(r"vom\s+(\d{1,2})\.\s*([A-Za-zäöü]+)\s+(\d{4})", s)
    if not m or m.group(2).lower() not in MONATE:
        return None
    return f"{int(m.group(1))}.{MONATE[m.group(2).lower()]}.{m.group(3)}"


def passendes_kapitel(geschaeft: str, kapitel: list[dict]) -> dict | None:
    if not geschaeft:
        return None
    gd = geschaeftsdatum(geschaeft)
    gw = woerter(geschaeft)
    beste, wert = None, 0.0
    for k in kapitel:
        kd = geschaeftsdatum(k["text"])
        if gd and kd and gd != kd:
            continue                                  # anderes Geschaeft
        kw = woerter(k["text"])
        if not kw or not gw:
            continue
        gemeinsam = len(gw & kw)
        rate = gemeinsam / max(1, min(len(gw), len(kw)))
        if gemeinsam < 2:
            rate = 0.0                                # ein Wort allein reicht nicht
        if gd and kd == gd:
            rate += 1                                 # Datum stimmt, das zaehlt am meisten
        if rate > wert:
            beste, wert = k, rate
    return beste if wert >= RATE else None


def zuordnen(videos: dict) -> dict:
    sitzungen = json.loads((DATA / "all_sessions.json").read_text(encoding="utf-8"))["sessions"]
    nach_datum: dict[str, list[tuple[str, dict]]] = {}
    for vid, v in videos.items():
        if v.get("datum"):
            nach_datum.setdefault(v["datum"], []).append((vid, v))
    aus = {}
    n_sitz = n_vote = n_ohne = 0
    for s in sitzungen:
        m = re.search(r"(\d{2}\.\d{2}\.\d{4})", s["sitzung"])
        if not m or m.group(1) not in nach_datum:
            continue
        # bei mehreren Videos am selben Tag das mit Kapiteln, sonst das laengste
        vid, v = sorted(nach_datum[m.group(1)], key=lambda x: (len(x[1]["kapitel"]), x[1]["dauer"]), reverse=True)[0]
        eintrag = {"video": vid, "abstimmungen": {}}
        n_sitz += 1
        for vote in s["votes"]:
            # Ohne uebergeordnetes Geschaeft ist der Titel selbst das Traktandum
            # (Postulat Nr. 2026/4 …, Geschaeftsbericht 2025 der …)
            text = vote.get("geschaeft") or ((vote.get("titel") or "") + " " + (vote.get("details") or ""))
            k = passendes_kapitel(text, v["kapitel"])
            if k:
                eintrag["abstimmungen"][str(vote["nr"])] = {"t": k["s"], "kapitel": k["text"][:120]}
                n_vote += 1
            else:
                n_ohne += 1
        aus[s["sitzung"]] = eintrag
    print(f"  Zuordnung: {n_sitz} Sitzungen mit Video, {n_vote} Abstimmungen mit Zeitmarke, {n_ohne} ohne.")
    return aus


def main() -> int:
    neu = "--neu" in sys.argv
    nur_bericht = "--bericht" in sys.argv
    videos = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    if not nur_bericht:
        ids = playlist_ids()
        print(f"  Playlist: {len(ids)} Videos")
        offen = [i for i in ids if neu or i not in videos or not videos[i].get("kapitel")]
        with concurrent.futures.ThreadPoolExecutor(6) as ex:
            for vid, v in zip(offen, ex.map(lambda i: video_lesen(i), offen)):
                videos[vid] = v
        for vid in ids:
            videos.setdefault(vid, {"titel": "", "datum": None, "dauer": 0, "kapitel": []})
        # nur Sitzungsvideos des Kantons behalten
        videos = {k: v for k, v in videos.items() if "kantonsrat" in v.get("titel", "").lower()}
        CACHE.write_text(json.dumps(videos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"  geladen: {len(offen)} Videos, {sum(1 for v in videos.values() if v['kapitel'])} mit Kapiteln")
    aus = zuordnen(videos)
    ZUORDNUNG.write_text(json.dumps(aus, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"  geschrieben: {ZUORDNUNG.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

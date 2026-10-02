# Politspiegel Schaffhausen

Das Dach. Eine leichte Übersichtsseite mit einem Kasten je Angebot:
Kantonsratsspiegel, Abstimmungsspiegel, Finanzspiegel und, als nationaler
Spiegel mit eigener Farbe, der Vertragsspiegel (Paket Schweiz–EU, eigenes
Repository `michaeljkahler/vertragsspiegel`). So muss niemand 2,7 MB
Kantonsratsspiegel laden, um die kommende Abstimmung anzusehen. Der
Abstimmungskasten nennt die nächste Abstimmung und hat ein Aufklappfeld
«Abstimmung wählen» (aktuell, kommend, vergangen), das als Ebene über den Kästen
darunter öffnet; die vollständige Liste liegt unter `/abstimmung/`.

Alle Kästen sind gleich gross: ab 880 px Fensterbreite zwei Spalten, alle Zeilen
gleich hoch, Kennzahlen und Fusszeile unten bündig. Darunter eine Spalte.

```
python3 politspiegel/bauen.py
```

Liest `politspiegel.json` (Titel, Untertitel, Texte der Kästen), die
`vorlage.json` jeder Abstimmung unter `abstimmungsspiegel/abstimmungen/`,
`data/all_sessions.json`, `finanzspiegel/daten/finanzspiegel.json` und die
veröffentlichte `kennzahlen.json` des Vertragsspiegels (Adresse aus
`vertrag.url`). Ist der Vertragsspiegel nicht erreichbar, gilt die zuletzt
gelesene Fassung in `data/vertragsspiegel_kennzahlen.json`. Schreibt `site/index.html`, `site/abstimmung/index.html`
(die Liste) und `site/dashboard.html` (Weiterleitung auf `kantonsrat/`).

Nichts auf der Übersicht wird von Hand gepflegt: Die Kennzahlen des
Kantonsratsspiegels kommen aus den Ratsdaten, die des Finanzspiegels aus dessen
Daten, die des Vertragsspiegels (Seiten, Wörter) aus dessen `kennzahlen.json`,
die Abstimmungen aus ihren Vorlagen. Von Hand gepflegte Zahlen auf einer Übersichtsseite veralten
unbemerkt, und zwar genau dann, wenn die Seite darunter aktuell ist.

## Die vier Ebenen

| Adresse | Name | Datei | Grösse |
|---|---|---|---|
| `/` | Politspiegel | `site/index.html` | 6 kB |
| `/kantonsrat/` | Kantonsratsspiegel | `site/kantonsrat/index.html` | 2,6 MB |
| `/abstimmung/` | Abstimmungsspiegel, alle Abstimmungen | `site/abstimmung/index.html` | 8 kB |
| `/abstimmung/<slug>/` | eine Abstimmung | `site/abstimmung/<slug>/index.html` | 0,1 bis 0,5 MB |
| `/finanzen/` | Finanzspiegel | `site/finanzen/index.html` | 0,3 MB |
| `michaeljkahler.github.io/vertragsspiegel/` | Vertragsspiegel, national | eigenes Repository | |
| `/dashboard.html` | Weiterleitung auf `/kantonsrat/` | | |

Bis zum 3. September 2026 lag der Kantonsratsspiegel unter dem Namen
«Abstimmungsspiegel» an der blossen Adresse. Geteilte Links landen jetzt auf
der Übersicht, wo er im ersten Kasten steht.

## Kommend und vergangen

Der Abstimmungstermin steht in `vorlage.abstimmung`. Die nächste Abstimmung ist
«aktuell», weitere künftige sind «kommend», zurückliegende «vergangen» und zeigen
das Ergebnis, sobald es in der `vorlage.json` unter `ergebnis` nachgetragen ist
(Schema in `abstimmungsspiegel/docs/14_TECHNIK.md`). Die Seite der Abstimmung
bleibt unverändert erreichbar. Jede Seite trägt oben links einen Heimlink zur
Übersicht; der Kantonsratsspiegel in der Seitenleiste und auf dem Telefon in der
oberen Leiste.

Verlinkt wird nur, was gebaut ist. Der Lauf meldet je Abstimmung, ob die
Zielseite vorhanden ist, ob sie kommend oder vergangen ist, welchen Status sie
trägt und ob das Ergebnis fehlt.

Soll eine Abstimmung nicht erscheinen, ohne ihren Ordner anzurühren: Slug in
`politspiegel.json` unter `ausblenden` eintragen. `finanzen` und `vertrag` in
derselben Liste blenden den jeweiligen Kasten aus.

`"testphase": true` in `politspiegel.json` blendet auf allen Seiten das
Eckband «Testphase» ein (`testphase.py`); nach dem Umschalten alle Seiten neu
bauen (`bauen.py`, `argumente.py` je Abstimmung, `scripts/publish.py`).

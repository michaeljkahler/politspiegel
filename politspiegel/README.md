# Politspiegel Schaffhausen

Das Dach. Eine leichte Übersichtsseite mit genau zwei Kästen, Kantonsratsspiegel
und Abstimmungsspiegel, damit niemand 2,7 MB Kantonsratsspiegel laden muss, um
die kommende Abstimmung anzusehen. Der Abstimmungskasten nennt die nächste
Abstimmung und hat ein Aufklappfeld «Abstimmung wählen» (aktuell, kommend,
vergangen); die vollständige Liste liegt unter `/abstimmung/`.

```
python3 politspiegel/bauen.py
```

Liest `politspiegel.json` (Titel, Untertitel, Kantonsratskasten), die
`vorlage.json` jeder Abstimmung unter `abstimmungsspiegel/abstimmungen/` und
`data/all_sessions.json`. Schreibt `site/index.html`, `site/abstimmung/index.html`
(die Liste) und `site/dashboard.html` (Weiterleitung auf `kantonsrat/`).

Nichts auf der Übersicht wird von Hand gepflegt: Die Kennzahlen des
Kantonsratsspiegels kommen aus den Ratsdaten, die Abstimmungen aus ihren
Vorlagen. Von Hand gepflegte Zahlen auf einer Übersichtsseite veralten
unbemerkt, und zwar genau dann, wenn die Seite darunter aktuell ist.

## Die drei Ebenen

| Adresse | Name | Datei | Grösse |
|---|---|---|---|
| `/` | Politspiegel | `site/index.html` | 6 kB |
| `/kantonsrat/` | Kantonsratsspiegel | `site/kantonsrat/index.html` | 2,6 MB |
| `/abstimmung/` | Abstimmungsspiegel, alle Abstimmungen | `site/abstimmung/index.html` | 8 kB |
| `/abstimmung/<slug>/` | eine Abstimmung | `site/abstimmung/<slug>/index.html` | 0,1 bis 0,5 MB |
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
`politspiegel.json` unter `ausblenden` eintragen.

`"testphase": true` in `politspiegel.json` blendet auf allen Seiten das
Eckband «Testphase» ein (`testphase.py`); nach dem Umschalten alle Seiten neu
bauen (`bauen.py`, `argumente.py` je Abstimmung, `scripts/publish.py`).

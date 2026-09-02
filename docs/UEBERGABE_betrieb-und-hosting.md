# Übergabe: Betrieb und Hosting

Stand 2. September 2026. Zwei Teile: was am laufenden Betrieb angepasst wurde, und der
Auftrag, das Dashboard öffentlich zu stellen.

---

## Teil 1 · Laufender Betrieb

### Der Ausgabeordner ist aufgeräumt

`output/` enthält nur noch **`dashboard.html`**, 2,65 MB, erzeugt von `scripts/build3.py`.
Gelöscht sind `kantonsrat-dashboard.html` (Ausgabe von build2.py), `design-vorschlaege.html`,
`matching-prototyp.html` und `prototyp-zuletzt-entschieden.html`. Die drei letzten waren
Entwurfsstände, deren Inhalt vollständig in build3 eingegangen ist.

### Der wiederkehrende Auftrag ist angepasst

Der Auftrag `kantonsrat-dashboard-update` läuft am 1. und 15. jedes Monats um 18 Uhr. Er rief
bis jetzt `build2.py` auf und hätte damit ab sofort eine Ausgabe erzeugt, die es nicht mehr
gibt. Geändert wurde:

- **`build2.py` durch `build3.py` ersetzt**, an beiden Stellen, mit dem ausdrücklichen
  Hinweis, dass `build2.py` und `matching.py` abgelöst sind.
- **Ein neuer Teil B: Fragetexte nachführen.** Das ist die Stelle, an der der Auftrag bisher
  blind war. Die Fragen im Reiter «Wer stimmt wie ich» werden nach Trennschärfe aus der
  laufenden Legislatur gewählt. Eine neue Sitzung kann die Auswahl darum auch bei
  Abstimmungen verschieben, die längst vorbei sind. Fällt dabei eine Abstimmung neu in die
  Liste, für die kein Text geschrieben ist, steht auf der Karte nur der Betreff des
  Geschäfts, und das ist irreführend: abgestimmt wird oft über einen Antrag innerhalb einer
  Vorlage, nicht über die Vorlage. `build3.py` meldet die Zahl am Ende jedes Laufs, der
  Auftrag nennt die betroffenen Abstimmungen und bietet an, die Texte zu schreiben. Die
  Regeln für solche Texte stehen im Auftrag selbst, damit sie beim Schreiben nicht neu
  hergeleitet werden müssen.
- Teil C (Interessenbindungen) ist inhaltlich unverändert, ruft aber ebenfalls `build3.py`.

### Einen eigenen Skill gibt es nicht

Das Projekt hat keinen installierten Skill. Die einzige Automatisierung ist der
wiederkehrende Auftrag, dessen Anweisungen unter
`Documents\Claude\Scheduled\kantonsrat-dashboard-update\SKILL.md` liegen. Ein zweiter Skill
wäre eine Verdopplung, solange der Ablauf halbmonatlich und immer gleich ist. Sinnvoll würde
ein Skill erst, wenn das Schreiben der Fragetexte oder das Erzeugen der Social-Media-Bilder
auf Zuruf abrufbar sein soll, unabhängig vom Zeitplan.

Im Projektordner liegt zudem `SKILL-geplante-pruefung.md`. Das ist ein Entwurf, kein
installierter Skill.

---

## Teil 2 · Auftrag an Claude Code: Dashboard veröffentlichen

### Ziel

Das Dashboard soll unter einer eigenen, neutralen Adresse im Netz stehen, die man am Telefon
diktieren kann. Kein Parteibezug im Namen, und **kein `github.io` in der Adresse**.

### Ausgangslage

- Das Dashboard ist **eine einzige HTML-Datei** ohne Server, ohne Datenbank, ohne externe
  Aufrufe. CSS, JavaScript, alle Daten und sogar die Porträts der Ratsmitglieder als base64
  stecken darin. Es lässt sich hosten, indem man die Datei irgendwo hinlegt.
- Der Ordner ist noch **kein Git-Repository**. `.gitignore` existiert bereits und schliesst
  `data/raw/` und `data/protokolle/` aus, zusammen 149 MB. Das muss so bleiben.
- Erzeugt wird die Datei lokal von `scripts/build3.py`. Ein Build im Netz ist nicht nötig und
  nicht erwünscht: die Rohdaten sollen nicht hochgeladen werden.

### Die Adresse

Ohne `github.io` geht es nur mit einer eigenen Domain. Ein Repository namens
`benutzer.github.io` ergibt zwar eine kürzere Adresse, aber der Vorbau bleibt. Also:

1. **Domain kaufen.** `.ch` verlangt keinen Wohnsitznachweis und kostet bei Schweizer
   Registraren rund 10 bis 15 Franken im Jahr. Vorschläge, in dieser Reihenfolge zu prüfen:
   `abstimmungsspiegel.ch`, `ratsspiegel.ch`, `stimmspiegel.ch`, `kantonsrat-sh.ch`,
   `sh-ratsspiegel.ch`. Verfügbarkeit muss beim Registrar geprüft werden, keiner der Namen
   ist hier reserviert. Der Name soll beschreiben, was die Seite zeigt, und keine Wertung
   enthalten; «Abstimmungsspiegel» ist bereits der Untertitel im Dashboard und passt darum
   am besten.
2. **GitHub Pages einrichten.** Öffentliches Repository, Pages aus dem Branch `main`, Ordner
   `/` oder `/docs`. Auf dem Gratisplan funktioniert Pages nur bei öffentlichen
   Repositories.
3. **Domain verbinden.** Eine Datei `CNAME` mit der blossen Domain ins veröffentlichte
   Verzeichnis, dann beim Registrar setzen:
   - Apex (`abstimmungsspiegel.ch`): vier A-Records auf `185.199.108.153`,
     `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - `www`: ein CNAME auf `benutzer.github.io`
   Danach in den Pages-Einstellungen **«Enforce HTTPS»** aktivieren, sobald das Zertifikat
   ausgestellt ist. Das dauert nach der DNS-Umstellung bis zu 24 Stunden.

   *Falls keine Domain gekauft werden soll:* Cloudflare Pages (`name.pages.dev`) oder Netlify
   (`name.netlify.app`) geben eine kürzere und neutralere Adresse als GitHub, der
   Anbietername bleibt aber sichtbar. Das ist die zweitbeste Lösung, nicht die gewünschte.

### Die Schaltfläche

Gemeint ist ein Einstieg, bei dem niemand nachdenken muss. Konkret:

1. **Die Datei heisst im Netz `index.html`.** Dann öffnet die blosse Domain das Dashboard
   direkt, ohne Pfad, ohne Klick auf einen Dateinamen. Das ist die eigentliche Schaltfläche.
   Lokal soll sie weiterhin `output/dashboard.html` heissen; das Umbenennen gehört in den
   Veröffentlichungsschritt, nicht in `build3.py`.
2. **Vorschau beim Teilen.** Ins `<head>` gehören Open-Graph- und Twitter-Angaben (`og:title`,
   `og:description`, `og:image`, `og:url`, `twitter:card=summary_large_image`), damit ein
   geteilter Link in WhatsApp, Threema und auf Social Media als Karte mit Bild erscheint statt
   als nackte URL. Als `og:image` eignet sich ein 1200×630-Ausschnitt im gleichen Layout wie
   die bestehenden Social-Media-Bilder. Das Bild muss als eigene Datei neben der Seite liegen,
   eine data-URL funktioniert dafür nicht.
3. **Favicon und Web-App-Manifest**, damit die Seite auf dem Telefon zum Startbildschirm
   hinzugefügt werden kann und dort ein Symbol statt eines leeren Blatts zeigt.
4. **Kein Zwischenschritt.** Keine Startseite, die erst auf das Dashboard verlinkt. Wer die
   Adresse eintippt, soll den Abstimmungsspiegel sehen.

### Veröffentlichen

Zwei Wege, beide zulässig:

- **Von Hand**, passend zum halbmonatlichen Rhythmus: nach jedem `build3.py` die Datei als
  `index.html` ins Repository kopieren und pushen.
- **Mit einer GitHub-Action**, die bei jedem Push auf `main` den Inhalt eines Ordners
  `site/` veröffentlicht. Der Build selbst läuft **nicht** in der Action, weil dafür die
  Rohdaten im Repository liegen müssten.

Der zweite Weg ist bequemer, der erste ehrlicher zum tatsächlichen Ablauf. Empfehlung: von
Hand beginnen, die Action nachrüsten, sobald der Rhythmus steht.

### Was vor dem Veröffentlichen noch hineingehört

Sobald die Seite öffentlich ist, gelten andere Anforderungen als bei einer Datei auf dem
eigenen Rechner:

- **Impressum** mit verantwortlicher Person und Kontaktmöglichkeit.
- **Quellenangabe.** Alle Abstimmungsdaten stammen von sh.ch, die Wortprotokolle ebenso. Das
  gehört sichtbar auf die Seite, nicht nur in die Dokumentation.
- **Lizenzhinweis für die Parteifarben.** Die Farben folgen dem Standard von SRF Data
  (`srfdata/swiss-party-colors`) unter CC BY-SA 4.0. Diese Lizenz verlangt Namensnennung.
  Zwei bewusste Abweichungen sind dokumentiert: AL in Magenta, GLP als abgedunkelte
  Textvariante.
- **Datenschutzhinweis.** Das Dashboard sendet nichts. Die Antworten im Matching bleiben im
  Browser, es gibt weder Konto noch Cookie noch Zählpixel. Das ist ein Vorteil und soll
  dastehen, aber es soll auch geprüft werden, ob GitHub Pages Zugriffsprotokolle führt, die
  offengelegt werden müssen.
- **Ein Hinweis auf die Grenzen der Daten.** Insbesondere: die Richtungskorrektur bei
  Umkehrabstimmungen ist zu 88 Prozent am Wortprotokoll oder von Hand geprüft, der Rest folgt
  einer Regel mit gemessener Fehlerquote von rund 5 Prozent. Wer die Zahlen zitiert, soll das
  wissen.

### Was nicht ins Repository gehört

`data/raw/` und `data/protokolle/` (149 MB, bereits ausgeschlossen), `archiv/` und
`__pycache__/`. Die Wortprotokolle sind öffentlich, aber sie gehören sh.ch und müssen nicht
zweitverteilt werden.

---

## Anhang: Was sich am Matching geändert hat

Beim Schreiben der Fragetexte ist ein Fehler in der Auswahl aufgefallen, der wichtiger war
als die fehlenden Texte.

Die Regel «je Geschäft nur die trennschärfste Abstimmung» liess von 253 Sachabstimmungen der
Legislatur nur 58 Fragen übrig, und von diesen teilten bloss 23 den Rat überhaupt. Ab Rang 27
waren alle einstimmig: 57:0, 54:0, 52:0. Solche Fragen ordnen niemanden zu, sie heben bei
jedem Nutzer alle Übereinstimmungswerte gleichmässig an und täuschen Nähe vor, die keine ist.
Die Modi 12/36/72 waren damit nicht erreichbar, das Dashboard zeigte 12/36/58.

Vier Änderungen in `build3.py`:

1. **Mindesttrennschärfe.** Die unterlegene Seite muss mindestens 15 Prozent halten.
2. **Ringverfahren statt einer Frage je Geschäft.** Zuerst die trennschärfste Abstimmung jeder
   Vorlage, dann die zweite jeder Vorlage und so fort. Der Kurzmodus bleibt breit gestreut,
   die langen Modi gehen in dieselben Vorlagen in die Tiefe.
3. **Motionen und Postulate zugelassen.** 94 Abstimmungen der Legislatur tragen keine
   Kommissionszuordnung und fielen deshalb heraus, obwohl sie politisch am meisten aussagen:
   Tempo 30, Konversionsmassnahmen, Verbot von Einweg-E-Zigaretten, Gemeindeautonomie beim
   Stimmrecht. Ihre Sachgruppe wird jetzt aus dem Überthema abgeleitet. Das Thema steuert nur
   Streuung und Beschriftung, nie die Rechnung; ein Fehlgriff kostet Ausgewogenheit, nicht
   Richtigkeit.
4. **Weitere Verfahrensfragen ausgeschlossen:** Rückweisungen an die Kommission, Vertagungen,
   Fristverkürzungen, Kommissionszuweisungen, die Aufteilung einer Vorlage und die Anträge auf
   Diskussion nach einer Interpellationsantwort. Dazu Dubletten: derselbe Antrag kommt bei
   einer sofortigen zweiten Lesung zweimal zur Abstimmung, am 19.05.2025 etwa der Antrag zur
   Neunmonatsfrist des Obergerichts. Es bleibt die trennschärfste der gleichlautenden.

Ergebnis: **72 Fragen**, Minderheitsanteil zwischen 16 und 50 Prozent, Median 34 Prozent,
verteilt auf fünf Sachgebiete. Alle 72 haben jetzt einen handgeschriebenen Fragetext und eine
neutrale Zusammenfassung in `data/frage_texte.json`.

### Ein Widerspruch in den Quellen, der stehen bleibt

Zwei Abstimmungen der Budgetsitzung vom 17.11.2025 (Abend) sind bewusst ausgeschlossen. Das
Protokoll hält fest, dem Gesamtbeitrag für das Energieförderprogramm sei mit 43:15 zugestimmt
worden. Im Excel steht dieses Ergebnis bei der Äufnung des Energie- und Klimafonds, während
beim Energieförderprogramm ein anderes Verhältnis eingetragen ist. Titel und Stimmen sind dort
gegeneinander verschoben. Welche Spalte zu welchem Beschluss gehört, lässt sich aus den
Quellen nicht entscheiden, und eine Frage daraus zu bauen hiesse, Stimmen einem womöglich
falschen Gegenstand zuzuordnen. Der Ausschluss steht mit Begründung als `FRAGE_AUSSCHLUSS` in
`build3.py`.

Das ist zugleich ein Hinweis darauf, dass die geplante Prüfung der Schlagworte gegen den
Debattentext breiter angelegt werden sollte: Sie sollte auch prüfen, ob Titel und
Stimmenverhältnis überhaupt zusammenpassen.

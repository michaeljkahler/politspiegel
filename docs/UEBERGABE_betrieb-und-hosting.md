# Übergabe: Betrieb und Hosting

Stand 2. September 2026. Was am laufenden Betrieb angepasst wurde, wie das Dashboard
veröffentlicht wird, und was dafür einmalig von Hand zu tun bleibt.

---

## Teil 1 · Laufender Betrieb

### Der Ausgabeordner ist aufgeräumt

`output/` enthält nur noch **`dashboard.html`**, 2,63 MB, erzeugt von `scripts/build3.py`.
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
- **Teil C (Interessenbindungen) nutzt neu den Zefix-Zugang.** Dazu unten mehr.
- **Ein neuer Teil D: veröffentlichen.** Er läuft am Schluss jedes Durchgangs.

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

## Teil 2 · Veröffentlichen auf GitHub Pages

**Entschieden:** Die Adresse darf `github.io` enthalten, eine eigene Domain wird nicht
gekauft. Die Seite steht damit unter `https://BENUTZER.github.io/REPO/`.

**Umgesetzt:** `scripts/publish.py` baut, committet und pusht. `site/index.html` ist die
veröffentlichte Seite, `output/dashboard.html` bleibt das lokale Bauergebnis und ist von der
Versionierung ausgeschlossen, sonst läge jede Fassung doppelt in der Historie. Das
Repository ist lokal angelegt, 44 Dateien, 8,8 MB.

### Was Michael einmalig tun muss

Drei Schritte, danach läuft es ohne Zutun:

1. **Repository auf GitHub anlegen.** Öffentlich, leer, ohne README (`publish.py` bringt den
   ganzen Inhalt mit). Der Name wird Teil der Adresse, also `politspiegel`.
2. **Token erzeugen.** GitHub, Settings, Developer settings, Personal access tokens,
   *Fine-grained tokens*. Nur dieses eine Repository auswählen, unter Permissions genau
   **«Contents: Read and write»**, alles andere auf «No access». Laufzeit setzen und den Tag
   notieren, an dem es abläuft: danach schlägt die Veröffentlichung fehl, bis ein neues
   Token da ist.
3. **Zugang ablegen** in `data/github_zugang.json`:

   ```json
   {"benutzer": "...", "repo": "politspiegel", "token": "github_pat_..."}
   ```

   Die Datei ist in `.gitignore` ausgeschlossen und darf dort nie entfernt werden.

Danach einmal `python3 scripts/publish.py --apply` von Hand, dann in den
Repository-Einstellungen **Pages** einschalten: Source «GitHub Actions». Den Rest erledigt
der Arbeitsablauf `.github/workflows/pages.yml`, der genau den Ordner `site/` ausliefert
(«Deploy from a branch» kann nur die Wurzel oder `/docs`). Nach ein bis zwei Minuten steht
die Seite.

**Nachtrag 3. September 2026.** Das Repository heisst `politspiegel`, die Seite steht unter
`https://michaeljkahler.github.io/politspiegel/`. Das Token steht nicht mehr in der
Fernadresse: `publish.py` gibt es nur dem Push-Befehl mit, und `origin` ist die gewöhnliche
Adresse `https://github.com/michaeljkahler/politspiegel.git`. Damit kann auch Claude Code
oder die Kommandozeile mit dem eigenen Git-Zugang pushen; Cowork und Claude Code teilen sich
dasselbe Repository. Cowork bleibt für den halbmonatlichen Auftrag zuständig, Claude Code
für Umbauten.

### Läuft das dann wirklich ohne Zutun?

Ja, mit zwei Einschränkungen, die man kennen sollte.

Der wiederkehrende Auftrag hat einen neuen Teil D bekommen, der nach jedem Lauf
`publish.py --apply` ausführt. Er läuft am 1. und 15. jedes Monats. Gab es nichts Neues,
meldet das Skript das und pusht nichts.

- **Beim ersten Lauf** müssen die Werkzeuge einmal freigegeben werden. Danach merkt sich der
  Auftrag die Freigabe und läuft unbeaufsichtigt. Am besten einmal «Jetzt ausführen»
  drücken, solange man zuschaut.
- **Das Token läuft ab.** Ein feingranulares Token hält höchstens ein Jahr. Der Auftrag
  erkennt den Authentifizierungsfehler, meldet ihn und legt von sich aus **kein** neues
  Token an. Das bleibt bewusst eine Handbewegung: ein Werkzeug, das sich selbst neue
  Schreibrechte besorgt, ist keine gute Idee.

Was der Auftrag von sich aus tut und was nicht, steht in seinem Teil D. Kurz: Er
veröffentlicht selbständig, schreibt fehlende Fragetexte selbständig, und er fragt nach,
wenn eine Abstimmung sich aus den Quellen nicht eindeutig klären lässt oder ein Zugang
nicht mehr greift.

### Was im Repository liegt und was nicht

Drin sind `scripts/`, `data/*.json`, `docs/` und `site/`. Das ist gewollt: bei einem
Transparenzprojekt gehört die Methode offengelegt, nicht nur das Ergebnis.

Draussen bleiben durch `.gitignore`:

- **`data/zefix_zugang.json` und `data/github_zugang.json`**, die Zugangsdaten. Die Regel
  steht bewusst als Erstes in der Datei.
- **`data/protokolle/` und `data/raw/`**, 149 MB Wortprotokolle. Sie sind öffentlich, gehören
  aber sh.ch und müssen nicht zweitverteilt werden.
- **`mail-*.md`**, die Korrespondenz mit dem Bundesamt für Justiz. Sie enthält keine
  Passwörter, aber Michaels Mailadresse, und private Post gehört nicht in ein öffentliches
  Repository.
- **`output/`** und `archiv/`.

Vor dem ersten Push wurde gegengeprüft, dass weder das Zefix-Passwort noch die Mailadresse
noch ein Token in einer versionierten Datei steht. Diese Prüfung gehört wiederholt, sobald
neue Dateiarten dazukommen.

---

## Teil 3 · Wenn doch einmal eine eigene Domain

Nicht mehr geplant, aber dokumentiert, falls die Adresse später kürzer werden soll.

### Ausgangslage

- Das Dashboard ist **eine einzige HTML-Datei** ohne Server, ohne Datenbank, ohne externe
  Aufrufe. CSS, JavaScript, alle Daten und sogar die Porträts der Ratsmitglieder als base64
  stecken darin. Es lässt sich hosten, indem man die Datei irgendwo hinlegt.
- Das Repository ist inzwischen angelegt, siehe Teil 2.
- Erzeugt wird die Datei lokal von `scripts/build3.py`. Ein Build im Netz ist nicht nötig und
  nicht erwünscht: die Rohdaten sollen nicht hochgeladen werden.

### Die Adresse

Ohne `github.io` ginge es nur mit einer eigenen Domain. Ein Repository namens
`benutzer.github.io` ergibt zwar eine kürzere Adresse, aber der Vorbau bleibt. Also:

1. **Domain kaufen.** `.ch` verlangt keinen Wohnsitznachweis und kostet bei Schweizer
   Registraren rund 10 bis 15 Franken im Jahr. Vorschläge, in dieser Reihenfolge zu prüfen:
   `politspiegel.ch`, `ratsspiegel.ch`, `stimmspiegel.ch`, `kantonsrat-sh.ch`,
   `sh-ratsspiegel.ch`. Verfügbarkeit muss beim Registrar geprüft werden, keiner der Namen
   ist hier reserviert. Der Name soll beschreiben, was die Seite zeigt, und keine Wertung
   enthalten; «Politspiegel» ist seit dem 3. September 2026 der Name des Dachs und passt darum
   am besten.
2. **GitHub Pages einrichten.** Öffentliches Repository, Pages aus dem Branch `main`, Ordner
   `/` oder `/docs`. Auf dem Gratisplan funktioniert Pages nur bei öffentlichen
   Repositories.
3. **Domain verbinden.** Eine Datei `CNAME` mit der blossen Domain ins veröffentlichte
   Verzeichnis, dann beim Registrar setzen:
   - Apex (`politspiegel.ch`): vier A-Records auf `185.199.108.153`,
     `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - `www`: ein CNAME auf `benutzer.github.io`
   Danach in den Pages-Einstellungen **«Enforce HTTPS»** aktivieren, sobald das Zertifikat
   ausgestellt ist. Das dauert nach der DNS-Umstellung bis zu 24 Stunden.

   *Falls keine Domain gekauft werden soll:* Cloudflare Pages (`name.pages.dev`) oder Netlify
   (`name.netlify.app`) geben eine kürzere und neutralere Adresse als GitHub, der
   Anbietername bleibt aber sichtbar. Das ist die zweitbeste Lösung, nicht die gewünschte.

### Was noch offen ist

`publish.py` setzt die Vorschauangaben bereits: `og:title`, `og:description`, `og:url` und
`twitter:card`. Zwei Dinge fehlen noch:

1. **Das Vorschaubild** `site/vorschau.png`, 1200 × 630, im Layout der bestehenden
   Social-Media-Bilder. Die Angaben verweisen schon darauf; solange die Datei fehlt, zeigt
   ein geteilter Link Titel und Satz, aber kein Bild. Es muss eine eigene Datei sein, eine
   data-URL funktioniert dafür nicht.
2. **Favicon und Web-App-Manifest**, damit die Seite auf dem Telefon zum Startbildschirm
   hinzugefügt werden kann und dort ein Symbol statt eines leeren Blatts zeigt.

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

---

## Anhang: Der Zefix-Zugang und was er wirklich kann

Der Zugang zur Zefix-REST-API ist seit dem 3. September 2026 aktiv und liegt in
`data/zefix_zugang.json`, ausgeschlossen von der Versionierung.

### Eine Personensuche gibt es nicht

`zefix.py` rief bisher einen Endpunkt `/person/search` auf und fing den Fehler still ab. Die
Schnittstellenbeschreibung der API
(`https://www.zefix.admin.ch/ZefixPublicREST/v3/api-docs`, öffentlich abrufbar) zählt genau
zehn Endpunkte auf, und alle betreffen Rechtseinheiten, Publikationen und Gemeinden. Eine
Abfrage «alle Mandate von Person X» ist damit nicht möglich; die Suche akzeptiert einen
Firmennamen, nicht einen Personennamen.

Das ist wichtig für die Wortwahl gegenüber der Öffentlichkeit: Es darf nie behauptet werden,
nicht deklarierte Mandate seien geprüft und ausgeschlossen worden. Sie sind es nicht.

### Was der Zugang stattdessen bringt

Der Abgleich wird nicht breiter, sondern belastbarer. `zefix.py` prüft jede deklarierte Firma
jetzt zusätzlich am amtlichen Register selbst und holt:

- **`status` und `deletionDate`**: steht die Firma noch im Register? Ein deklariertes Mandat
  bei einer gelöschten Firma ist ein Befund.
- **`oldNames`**: frühere Firmennamen. Damit lösen sich Fälle auf, die bisher als «nicht
  gefunden» galten. Aktuell sind das **18 Organisationen**, und Umbenennung ist laut Register
  der häufigste Grund für eine Fehlanzeige.
- **`legalSeat`, `address`, `canton`**: der Sitz aus erster Hand, womit ein «möglicher»
  Treffer erhärtet oder ausgeschlossen werden kann.
- **`purpose`**: der eingetragene Zweck, der zeigt, ob die gefundene Firma inhaltlich passt.
- **`zefixDetailWeb`**: der Link auf den amtlichen Eintrag. Er steht jetzt im Infokasten des
  Beziehungsnetzes, zusammen mit Status, Rechtsform, Sitz und früheren Namen.

Die zwei Befundarten, die das Skript ausdrücklich meldet, heissen `geloescht` und
`aufgeloest` und stehen unter `befunde` in `data/interessen_pruefung.json`. Der wiederkehrende
Auftrag ist angewiesen, sie namentlich zu melden.

### Warum die fehlende Personensuche keine Frage des Logins ist

Der HTTP-Test taugt dafür nicht: die Anmeldung wird vor dem Routing geprüft, darum antwortet
auch ein frei erfundener Pfad mit 401. Entschieden ist es über die Schnittstellenbeschreibung
selbst. Sie deklariert ein Sicherheitsschema `Zefix-Credentials` und wendet es global an, sie
beschreibt also genau die Endpunkte, die den Zugang verlangen, und listet dieselben zehn auf,
die ohne Anmeldung 401 liefern. Das Wort «person» kommt im ganzen Dokument null Mal vor,
weder als Endpunkt noch als Datenfeld. Ein Login schaltet Daten hinter diesen zehn Endpunkten
frei, keine weiteren Endpunkte.

Rest an Unsicherheit: `/api-docs` und `/v2/api-docs` sind selbst hinter der Anmeldung und
nicht lesbar. Dass dort ein Dokument läge, das dem öffentlichen, aktuellen und
zugangspflichtigen v3-Dokument widerspricht, ist unwahrscheinlich, aber nicht ausgeschlossen.

### Was am 2. September geprüft wurde und was nicht

Beim Einbau war der Zugang noch nicht freigeschaltet, jeder Aufruf antwortete mit 401.
Trotzdem liess sich das meiste prüfen, weil die Schnittstellenbeschreibung die genauen
Datentypen nennt. Der Abgleich hat drei Fehler zutage gefördert, die sonst still ins Leere
gelaufen wären:

- `Address` hat das Feld **`city`**, nicht `town`. Der Ort wäre immer leer geblieben.
- `zefixDetailWeb` und `legalForm.name` sind **keine Zeichenketten**, sondern Objekte mit den
  Sprachen de, fr, it und en. Der Link wäre als `[object Object]` in der Seite gelandet.
- `status` kennt genau drei Werte, **`ACTIVE`, `CANCELLED`, `BEING_CANCELLED`**. Die Prüfung
  suchte nach «gelöscht» und hätte nie angeschlagen, der wichtigste Befund wäre ausgeblieben.

Die Auswertung ist danach gegen eine nach Schema nachgebaute Antwort getestet, ebenso die
Darstellung im Infokasten für alle fünf Fälle (gelöscht, in Löschung, aktiv, leer, fehlend).

**Offen bleibt allein die echte Antwort.** Beim ersten Lauf ab dem 3. September ist zu
prüfen: ob die Namenssuche brauchbare Treffer liefert, wie viele der aktuell 18 nicht
auffindbaren Organisationen sich über frühere Namen auflösen, und ob die API eine
Abfragegrenze setzt, die den Lauf über 36 Firmen bremst.

---

## Anhang: Personensuche im Handelsregister Schaffhausen

Das Handelsregisteramt hat am 2. September 2026 zugesagt, dass die automatisierte
Personensuche für dieses Projekt in Ordnung geht, wenn Menge und Zeitpunkt verteilt werden:
**5 Namen pro Woche, 2 vollständige Durchgänge pro Jahr, mindestens 45 Sekunden zwischen
zwei Personen.** Die Auszüge, die zu derselben Person gehören, dürfen unmittelbar
nacheinander geöffnet werden; die Pause bezieht sich auf den Abstand zwischen Personen.

Bei 59 Ratsmitgliedern sind das 12 Wochen je Durchgang, also rund ein halbes Jahr für beide.

### Wie die Auflage durchgesetzt wird

`scripts/hr_personen.py` trägt die Grenzen im Code, nicht in einer Anweisung. Das Skript

- nimmt höchstens 5 Namen je Lauf,
- verweigert einen Lauf, wenn der letzte weniger als 6 Tage her ist,
- beginnt keinen dritten Durchgang im selben Kalenderjahr,
- hält 8 Wochen Abstand zwischen zwei Durchgängen,
- wartet 45 Sekunden zwischen zwei Personen,
- schickt eine Kennung im User-Agent, die auf das Projekt und die Zusage verweist,
- protokolliert jeden Lauf mit Datum, Zeit und Namen in `data/hr_abfrage_status.json`.

Das Protokoll ist der Grund, warum die Grenzen im Code stehen: Falls das Amt je nachfragt,
lässt sich auf die Zeile genau belegen, was abgefragt wurde. Eine Anweisung in Prosa kann
missverstanden werden, eine Schleife über fünf Namen nicht.

Der wöchentliche Auftrag `handelsregister-personensuche` läuft dienstags um 9 Uhr und ruft
nur dieses Skript. Er ist ausdrücklich angewiesen, die Sperre nicht zu umgehen, auch nicht
auf Zuruf.

### Der erste Lauf ging schief, und woran das auffiel

Der Lauf vom 2. September hat fünf Namen abgefragt und die Ergebnisse **falsch zugeordnet**.
Die Teilantwort des Portals enthält bei aufeinanderfolgenden Abfragen zwei Tabellen, die neue
und die aus der wiederhergestellten Ansicht. Die Auswertung sammelte beide ein und schrieb
darum einem Ratsmitglied die Treffer des vorherigen zu.

Aufgefallen ist es an einer Unstimmigkeit, die nicht sein kann: bei einem Namen erschienen
**6 Zeilen bei 2 gemeldeten Treffern**. Mehr Zeilen als Treffer geht nicht. Ohne diesen
Abgleich zwischen Zeilenzahl und der vom Portal gemeldeten Trefferzahl wäre der Fehler
unbemerkt geblieben, und es wären falsche Firmen unter falschen Namen in der Prüfliste
gelandet.

Behoben ist er dadurch, dass nur noch der **letzte** Tabellenrumpf der Antwort ausgewertet
wird. Zusätzlich gilt jetzt: stimmen Zeilenzahl und gemeldete Trefferzahl nicht überein, wird
das Ergebnis **nicht übernommen** und der Name kommt in der nächsten Woche erneut dran. Die
Korrektur ist gegen die gespeicherte Rohantwort und einen nachgebauten Mischfall geprüft.

Die falschen Daten sind gelöscht, die fünf Namen stehen wieder in der Warteschlange. Im
Protokoll ist der Lauf als verworfen vermerkt, samt der Kontrollabfrage, mit der der Fehler
eingegrenzt wurde. Damit wurden in dieser Woche 6 statt 5 Abfragen gemacht, eine über der
Zusage. Das steht so im Protokoll, statt es zu verschweigen.

### Die Auszüge werden mitgeprüft

Die Suche geht über den Nachnamen, und das Register führt Namensvettern getrennt. Das Skript
öffnet darum zu jedem Treffer den Registerauszug und liest die Personalangaben, also die
Zeile «Nachname, Vorname, von Ort, in Ort» mit Funktion und Zeichnungsart. Bestätigt wird ein
Treffer nur, wenn der Vorname des Ratsmitglieds unter den eingetragenen Vornamen vorkommt.
Das Register führt oft mehrere Vornamen, die Selbstdeklaration nur den Rufnamen, darum reicht
ein Treffer unter den Vornamen.

Drei Urteile: `bestaetigt`, `namensvetter`, `ungeprueft`. Nur das erste gehört in eine
Meldung.

**Wie wichtig das ist, zeigte gleich der erste Fall.** Die Suche nach «Alaye» findet in
Schaffhausen die PRAXIS 1503 GmbH. Eingetragen ist dort Oluwafunso Akinola Alaye, von
Winterthur, als Gesellschafter und Geschäftsführer. Das Ratsmitglied heisst Mayowa Alaye.
Ohne den Auszug wäre daraus ein Befund geworden, der eine falsche Person betrifft.

Technisch war das die grösste Hürde: die Auszugsseite liefert beim blossen Abrufen nur das
Gerüst, der Inhalt steckt in einem nachgeladenen PrimeFaces-Panel und braucht einen zweiten
Aufruf. Für gelöschte Rechtseinheiten gibt das Portal überhaupt keinen Auszug heraus, auch
im Browser nicht; solche Treffer bleiben `ungeprueft`. Gesucht wird also auch in gelöschten
Firmen, angesehen werden können sie nicht.

Einen einzelnen Auszug ansehen, ohne das Kontingent zu berühren:
`python3 scripts/hr_personen.py --auszug CHE-454.162.255`

Auch `bestaetigt` bleibt ein Prüfhinweis. Der Abgleich mit der Deklaration läuft über den
Firmennamen und erkennt eine anders geschriebene Umschreibung nicht, ein Mandat kann seit der
Deklaration beendet worden sein, und verbindlich ist allein der beglaubigte Registerauszug.
Vor einer Veröffentlichung den Auszug ansehen und, wenn es eng wird, das Ratsmitglied fragen.

`data/hr_personen.json` und `data/hr_abfrage_status.json` sind von der Versionierung
ausgeschlossen. Ungeprüfte Verbindungen zwischen namentlich genannten Politikern und Firmen
gehören nicht in ein öffentliches Repository. Ins Dashboard darf nur, was am Auszug
bestätigt ist.

---

## Anhang: Herkunft der Interessenbindungen im Dashboard

Seit dem 2. September zeigt das Dashboard, woher eine Interessenbindung stammt:

- **Blau** (`--q-dekl`, #0E4E8A): in der Selbstdeklaration auf sh.ch angegeben.
- **Gelb** (`--q-reg`, #F0A202): steht im Handelsregister des Kantons Schaffhausen, nicht
  aber in der Deklaration.

Sichtbar im Mitgliederprofil als beschriftetes Abzeichen mit Link auf den Registerauszug, und
im Beziehungsnetz als Kantenfarbe.

Die Legende im Beziehungsnetz erklärt seit dem 2. September das ganze Bild und nicht mehr nur
die beiden Linienarten: was ein Punkt ist (Ratsmitglied, Organisation, Branche, Organisation
nur im Handelsregister), was seine Grösse bedeutet, was die Linien unterscheiden und wie sich
Suchtreffer und angeklickte Punkte zeigen. Die Zeile zum Handelsregister erscheint nur, wenn
es dort etwas zu sehen gibt.

Dabei fiel ein selbst gebauter Konflikt auf: Suchtreffer wurden gelb eingefärbt, also genau
wie Organisationen, die nur im Register stehen. Ein gesuchter Verein sah damit aus wie ein
Registerfund. Suchtreffer behalten jetzt ihre Füllung und bekommen einen Ring in der
Fokusfarbe. Gelb ist allein den Registerorganisationen vorbehalten.

### Warum Farbe hier nie allein steht

Blau und Gelb trennen sich hervorragend, auch bei Farbsehschwäche: ΔE über 120 bei
Deuteranopie wie bei Protanopie. Gegenüber den Parteifarben ist der Abstand aber klein,
FDP-Blau liegt bei ΔE 15, EVP-Gelb bei ΔE 14. Darum:

- Die Herkunftsfarben liegen nur auf Kanten, Organisationen und Abzeichen, **nie auf
  Mitgliederknoten**, die die Parteifarbe tragen.
- Jede Markierung trägt zusätzlich Text («deklariert», «nur Handelsregister»).
- Im Netz sind Registerkanten zusätzlich **gestrichelt** und Registerorganisationen tragen
  einen Ring.

Wer die beiden Farben nicht unterscheiden kann, verliert also keine Information.

### Der Freigabeschritt

Zwischen Registerfund und Dashboard steht `data/interessen_register.json`. Nur Einträge mit
Status `bestaetigt` erscheinen. Erzeugt und nachgeführt wird die Liste von
`scripts/interessen_register.py`, die Arbeitsfassung liegt als
`data/interessen_register_pruefliste.md` daneben, beide von der Versionierung ausgeschlossen.

Vier Status: `offen` (Voreinstellung, erscheint nicht), `bestaetigt` (am Auszug geprüft,
erscheint gelb), `deklariert` (dieselbe Bindung, nur anders umschrieben) und `verworfen`.

Das ist derselbe Aufbau wie bei den Umkehrabstimmungen: die Maschine engt ein, ein Mensch
entscheidet. Nötig ist er, weil der Abgleich ein Namensabgleich bleibt und die Seite
öffentlich Personen benennt.

### Ein Fehler, den der Sichttest aufgedeckt hat

Beim ersten Bauen erschien bei Anna Brügel «Schweizerisches Arbeiterhilfswerk SAH
Schaffhausen» als nicht deklariert. Sie deklariert es aber, als «SAH Schaffhausen
(Schweizerisches Arbeitshilfswerk), Mitglied Vorstand».

Ursache war `deklarierte_firmen()`. Diese Funktion siebt die Deklaration auf Namen mit
Rechtsform, weil nur solche überhaupt im Handelsregister stehen können. Für die Frage «welche
deklarierte Firma suche ich im Register» ist das richtig. Für die Gegenfrage «steht dieser
Registerfund schon in der Deklaration» ist es falsch: die Deklaration schreibt Rechtsformen
oft gar nicht mit. Zwei von Brügels drei Angaben fielen durch den Filter und galten damit als
nicht vorhanden.

Behoben durch `alle_deklarationen()`, das jede Zeile zurückgibt. Die Zahl der Kandidaten fiel
von 8 auf 5, und die drei weggefallenen waren allesamt falsch. Bei einem Projekt, das
namentlich Ratsmitglieder nennt, war das der wichtigste Fund dieser Runde.

### Nachgetragene Wohngemeinden

Bei drei Ratsmitgliedern führt sh.ch keine Adresse. Ohne Wohngemeinde ruht die Zuordnung
eines Registerfunds allein auf dem Vornamen, und das genügt nicht: das Register kennt
mehrere Vornamen, die Deklaration nur den Rufnamen.

`data/mitglieder_ergaenzung.json` trägt solche Angaben nach. Für Christian Di Ronco steht
dort Neuhausen am Rheinfall, belegt durch die Kontaktangabe auf seiner eigenen Website. Die
Datei nennt je Person die Quelle und enthält **ausschliesslich die Gemeinde**: mehr braucht
es nicht, um zwei Personen gleichen Namens zu trennen, und mehr gehört nicht in dieses
Projekt. Sie ist von der Versionierung ausgeschlossen und geht in keine Auswertung ein.

Der Nachtrag hat sofort gewirkt: `python3 scripts/hr_personen.py --neu-beurteilen` bewertet
die gespeicherten Auszüge neu, ohne eine einzige Abfrage, und stufte einen Fund von
`bestaetigt` auf `bestaetigt_anderer_ort` herab. Im Register stand dort ein Mann mit
demselben Nachnamen und demselben Rufnamen als zweitem Vornamen, wohnhaft in einer anderen
Gemeinde als das Ratsmitglied. Ohne die Gemeinde wäre dieser Eintrag als dessen Mandat in
die Liste gegangen.

(Welches Ratsmitglied und welche Firma das betraf, steht bewusst nicht hier: der Fund wurde
geprüft und verworfen, und eine ausgeschiedene Verbindung gehört nicht in ein öffentliches
Repository. Nachzulesen ist sie in `data/interessen_register_voll.json`, das lokal bleibt.)

Damit ist auch eine Grenze berührt, die festgehalten gehört: Die Interessenbindungen selbst
stammen weiterhin **nur** aus der Selbstdeklaration auf sh.ch und aus dem Handelsregister.
Die eigene Website eines Ratsmitglieds wurde einmal herangezogen, und zwar allein für die
Wohngemeinde, also für die Frage, ob ein Registereintrag überhaupt diese Person betrifft.
Mandate, die auf einer privaten Website stehen, gehen nicht ins Dashboard: dort bedeutet
Blau «auf sh.ch deklariert», und das muss es weiter bedeuten.

### Was das Repository nicht enthält

Bei der Gegenprobe vor dem Veröffentlichen fiel auf, dass `data/mitglieder.json` neben Name,
Partei und Interessenbindungen auch **Wohnadresse, Geburtsdatum und Mailadresse** aller
59 Ratsmitglieder führt: 56 Adressen, 58 Geburtsdaten, 59 Mailadressen. Das steht so auf
sh.ch, aber es in ein Repository zu legen heisst, es zu vervielfältigen.

Das Dashboard braucht davon nur die Gemeinde, und die Ausgabe enthält weder Adresse noch
Geburtsdatum, das wurde geprüft. Die Datei ist darum von der Versionierung ausgeschlossen;
`scripts/mitglieder.py` stellt sie jederzeit wieder her. Wer das Repository klont, kann den
Bau also nachvollziehen, ohne die Personendaten mitgeliefert zu bekommen.

### Was die erste Handprüfung gelehrt hat

Michael hat die fünf Kandidaten am 2. September durchgesehen. **Einer hielt stand**, die
SAH Services GmbH bei Anna Brügel. Die anderen vier waren falsch.

Der Grund lag nicht am Namensabgleich, sondern an einer Eigenheit der Suche. Sie läuft mit
den Häkchen «auch gelöschte Firmen» und «auch gestrichene Personen», sonst fehlten beendete
Mandate. Damit erscheinen aber Rechtseinheiten, die es nicht mehr gibt, und der Auszug führt
deren Organe weiter, ohne sie als gestrichen zu kennzeichnen. Michael fiel es auf, weil er
die Firmen von Hand gar nicht finden konnte: eine gewöhnliche Suche zeigt sie nicht.

Die Zahlen sind deutlich: von 170 gefundenen Firmen sind **101 gelöscht**, das betrifft
59 Prozent aller Treffer.

Erkannt wird das jetzt auf zwei Wegen, beide ohne Kosten für das Kontingent, denn begrenzt
sind die Namensabfragen und nicht die Auszüge:

- Beim Öffnen über die Trefferzeile trägt die Weiterleitung bei gelöschten Rechtseinheiten
  ein Löschdatum: `auszug.xhtml?loeschung=20040213&uid=...`
- Nachträglich prüft `python3 scripts/hr_personen.py --firmen-pruefen`, ob
  `auszug.xhtml?uid=...` überhaupt Inhalt liefert. Bleibt die Seite leer, ist die Firma weg.

Auf die bisherigen 19 Namen angewandt sinkt die Kandidatenliste von 5 auf 2, und die drei
weggefallenen sind genau die, die Michael als falsch bezeichnet hat. Der vierte Fehltreffer
war schon vorher durch die abweichende Wohngemeinde markiert.

**Was das über den Wert des Registers sagt:** In einem der geprüften Fälle führt der Auszug
ein Ratsmitglied weiter als Mitglied des Verwaltungsrates, obwohl das Mandat abgemeldet ist.
Ein nicht gestrichener Registereintrag belegt also kein bestehendes Mandat. Verbindlich
bleibt der beglaubigte Auszug, und die Freigabe von Hand ist keine Formalie, sondern trägt
die Aussage.

### Registerfunde hängen an ihrer Branche

Deklarierte Organisationen sind im Beziehungsnetz an eine Branche gehängt, damit das Netz
thematisch geordnet bleibt. Registerfunde hingen anfangs allein am Ratsmitglied und fielen
aus dieser Ordnung heraus. Sie werden jetzt gleich behandelt.

Die Einteilung der deklarierten Organisationen läuft über den Namen (`interessen.branche`).
Bei Registerfunden steht mehr zur Verfügung: der **eingetragene Zweck** aus dem Auszug. Er
ist die bessere Grundlage, weil ein Firmenname oft nichts verrät. «SAH Services GmbH» ordnet
sich über den Namen nirgends ein, über ihren Zweck («Förderung der sozialen Integration,
Arbeitsintegration stellenloser Menschen») eindeutig unter «Soziales und Hilfswerke».

Der Name entscheidet zuerst, damit die Einteilung zu den deklarierten Organisationen passt;
erst wenn er nichts hergibt, zieht der Zweck. Gelesen wird der Zweck beim Öffnen des Auszugs,
also ohne zusätzliche Abfrage.

### Ausgeschiedene Ratsmitglieder, und ein Fehlschluss, der eine Person falsch bezeichnet hat

**Massgeblich ist die Namensliste der jüngsten Sitzung.** Sie führt den vollständigen Rat,
Abwesende eingeschlossen: eine Abwesenheit steht als Stimme «A» und nicht als fehlender Name.
Wer dort nicht mehr steht, früher in der Legislatur aber mitgestimmt hat, ist ausgeschieden.
Das sind **drei**: Severin Brüngger, Hannes Knapp und Lara Winzeler.

Sie tragen in Tabelle und Profil ein graues Abzeichen «ausgeschieden», dazu im Profil die
letzte Sitzung, an der sie teilgenommen haben. Mehr lässt sich nicht belegen, ein
Rücktrittsdatum steht in keiner der Quellen. Der Vermerk erscheint nur, wenn die laufende
Legislatur im Blick ist; in einer abgeschlossenen sind alle ausgeschieden, dort wäre er Lärm.

**Der erste Ansatz war falsch und ist lehrreich.** Er verglich die Abstimmungsdaten mit
`mitglieder.json` und erklärte jeden für ausgeschieden, der dort fehlt. Das ergab vier Namen,
darunter Lukas Bringolf, der der Justizkommission vorsitzt und in der jüngsten Sitzung
mitgestimmt hat.

Die Ursache: `mitglieder.json` entsteht aus den contentids in `mitglieder_ids.json`, und diese
Liste zählt 59 Einträge, während der Rat 60 Sitze hat. Auf der Mitgliederseite des Kantons
gibt es zu Bringolf schlicht keinen Personenkasten, also keine contentid und damit kein
Profil. **«Fehlt in unseren Stammdaten» und «nicht mehr im Rat» sind zwei verschiedene
Dinge**, und die Verwechslung stellt eine falsche Behauptung über eine namentlich genannte
Person ins Netz. Aufgefallen ist es nur, weil Michael die Person kennt.

Daraus zwei Änderungen:

- Das Kriterium stützt sich jetzt auf die Abstimmungsdaten selbst und nicht mehr auf die
  Vollständigkeit einer gescrapten Liste.
- Wer im Rat sitzt, aber kein Profil hat, wird beim Bauen ausdrücklich gemeldet und bekommt
  im Dashboard einen Hinweis: «Kein Profil auf sh.ch». Dort fehlen Porträt, Beruf und
  Selbstdeklaration, die Abstimmungsdaten sind davon nicht betroffen. Eine leere Seite ohne
  Erklärung sähe nach Fehler aus und legte nahe, die Person habe nichts deklariert.

Ausgeschiedene haben kein Porträt, weil sh.ch sie nicht mehr führt. Statt einer leeren dunklen
Scheibe zeigt der Platzhalter die Initialen im Parteiring.


---

## Anhang: Bilder für Social Media

Der Bilddownload deckt seit dem 2. September das ganze Dashboard ab, 16 Motive in sechs
Gruppen, alle im Hochformat 1080 × 1350:

- **Abstimmungen:** Neuste Abstimmung, Sitzungsüberblick
- **Rangliste Ratsmitglieder:** Zustimmung, Ablehnung, Präsenz, Abwesenheit, Enthaltungen
- **Rangliste Fraktionen:** Zustimmung, Präsenz, Geschlossenheit, Enthaltungen
- **Fraktionen:** Fraktionsvergleich
- **Einzelnes Ratsmitglied:** Profilkarte und Interessenbindungen, mit Auswahl der Person
- **Wer stimmt wie ich?:** das eigene Ergebnis nach Fraktionen und nach Ratsmitgliedern

Die neun Ranglisten teilen sich eine Zeichenfunktion und stehen als Daten in `MOTIVE`; sie
unterscheiden sich nur in Titel, Kennzahl und Untertitel. Zwei Kennzahlen, Ablehnungs- und
Abwesenheitsquote, werden dabei gerechnet, die übrigen kommen fertig aus `mitgliedStats()`
und `frakStats()`.

Drei Entscheide, die im Bild stecken:

- **Der Balken bezieht sich auf den höchsten Wert der Liste, nicht auf 100 Prozent.** Bei
  Präsenzwerten zwischen 88 und 99 wären sonst alle Balken gleich lang und die Grafik sagte
  nichts.
- **Fraktionen tragen ihre Fraktionsfarbe, Ratsmitglieder die ihrer Partei.** Wer `pkey` auf
  einen Fraktionsnamen anwendet, bekommt nur Grau; dafür gibt es `fkey`.
- **Auf dem Bild steht «Vorname Nachname».** In der Tabelle steht die Sortierform
  «Nachname Vorname», die auf einem geteilten Bild aber steif wirkt.

Die Motive «Wer stimmt wie ich?» erscheinen erst, wenn ein Ergebnis vorliegt, und stützen
sich auf dieselbe Rechnung wie die Anzeige: `matchRechnen()` wurde aus `auswerten()`
herausgelöst, damit Bild und Seite nicht zwei verschiedene Ergebnisse zeigen können. Eine
eigene Zählung war schon einmal falsch, weil `st.antworten` ein Objekt ist und kein `length`
hat.

Bei den Interessenbindungen gilt im Bild dieselbe Unterscheidung wie im Dashboard: blau
deklariert, gelb nur im Handelsregister, mit derselben Fussnote. Ein geteiltes Bild darf
nicht mehr behaupten als die Seite.

## Umbrüche in den Interessenbindungen (2. September 2026)

Auf sh.ch bricht eine lange Interessenbindung im Personenkasten über zwei Zeilen
um, und die Funktion landet allein auf der zweiten. Zeilenweise eingelesen wurden
daraus zwei Einträge, und aus der abgetrennten Funktion im Beziehungsnetz eine
eigene Organisation.

Betroffen waren sieben Einträge bei sechs Ratsmitgliedern: Bettina Looser (zwei),
Markus Müller, Peter Neukomm, Rainer Schmidig, Andreas Schnetzler, Erich Schudel.

`interessen_zusammenfuegen()` in `scripts/mitglieder.py` fügt sie beim Einlesen
wieder zusammen. Zwei Merkmale, die einzeln nicht taugen, tragen gemeinsam: das
Komma am Zeilenende fehlt bei Neukomms Zeile, die auf «(EKK)» endet, und der
Aufzählungsstrich fehlt bei sieben Profilen durchgehend, die ihre ganze
Deklaration ohne Striche führen. Führt eine Person überhaupt Striche, beginnt
jeder echte Eintrag mit einem, und eine strichlose Zeile gehört zur vorherigen.

Beim Zusammenfügen wird ein Komma ergänzt, wenn die Fortsetzung gross beginnt und
damit die Funktion ist, sonst nur ein Leerzeichen, damit aus Bettina Loosers
«und Extremismus NAP KT SH» kein falsches Komma wird. Ohne dieses Komma greift
die Aufteilung in Organisation und Funktion nicht, und Neukomms Kommission stünde
im Netz ohne seine Rolle.

`data/mitglieder.json` wurde einmalig nachgezogen, das Netz mit
`interessen.py --apply` neu erzeugt. Der Abgleich mit dem Handelsregister ändert
sich dadurch nicht (unverändert 5 Funde, 1 bestätigt).

Offen und bewusst nicht angefasst: Peter Neukomms Deklaration schreibt
«Stadtpräsident Schaffhauen». Der Tippfehler steht so auf sh.ch. Er erzeugt im
Netz einen Knoten «Schaffhauen». Eine stille Korrektur würde die Selbstdeklaration
verändern, darum bleibt sie stehen, bis Michael entscheidet.

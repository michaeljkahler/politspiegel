# Social Media: Konzept und Ablauf

Stand 3. September 2026. Gilt für Instagram, TikTok, Facebook und YouTube des Politspiegels.

## 1. Rahmen

1. Kanäle: Instagram @politspiegel.sh, TikTok @politspiegel.sh, Facebook-Seite, YouTube (Shorts). Alle in Metricool unter der Marke «politspiegel.sh» (ID 6841058) verbunden.
2. Zuständigkeit: Claude erzeugt Bilder, Videos und Texte, legt Beiträge in Metricool als Entwurf ab. Michael gibt jede Charge frei. Nichts geht ohne Freigabe online.
3. Kein Community-Management: Kommentare und Nachrichten werden nicht beantwortet. Rückfragen laufen über die Mailadresse im Impressum.
4. Berührungspunkte für Michael: einmalige Einrichtung, danach ein «ja» je Charge im Chat oder in Metricool.

## 2. Textregeln

1. Nummerierte Listen statt Fliesstext.
2. Nur prüfbare Fakten. Keine Wertung, keine Zuspitzung, keine Adjektive wie «überraschend» oder «knapp».
3. Ergebnisse heissen «Angenommen» oder «Abgelehnt», wie im Dashboard. Bei Umkehrabstimmungen steht «Ja bedeutet: …» dabei.
4. Jeder Beitrag nennt die Quelle (sh.ch) und die Adresse der Seite.
5. Höchstens drei Hashtags: #Schaffhausen #Kantonsrat #Politspiegel, beim Abstimmungsspiegel zusätzlich der Name der Vorlage.
6. Keine Verweise auf interne Dokumente.

## 3. Formate

### 3.1 Kantonsratsspiegel, nach jeder Sitzung

Erzeugt `scripts/social.py`, Ausgabe in `site/social/kantonsrat/<datum>/`.

1. Karussell (Instagram, Facebook, TikTok-Fotobeitrag), 1080 × 1350: Deckblatt mit nummerierter Liste aller Abstimmungen und Ergebnis, dann je Abstimmung eine Karte mit Titel, Geschäft, Ergebnis, Gesamtbalken, Fraktionsbalken. Höchstens zehn Bilder je Beitrag, bei mehr Abstimmungen Teil 1 und Teil 2.
2. Reel (Instagram Reel, TikTok, Facebook Reel, YouTube Short), 1080 × 1920: dieselben Karten als Diashow, 3,5 s Deckblatt, 4 s je Abstimmung, 3 s Schlussbild mit Adresse. Stumm, mit leerer Tonspur. Bei 14 Abstimmungen rund 60 s.
3. Bildtext: Sitzung, Datum, nummerierte Liste mit Ergebnis und Stimmenzahl, Adresse, Quelle, Hashtags.

### 3.2 Abstimmungsspiegel, vier Wochen vor dem Abstimmungssonntag

Serie je kantonale Vorlage, Bilder aus `abstimmungsspiegel/bausteine/teilen.py` (Motive vorlage, gegen, paar, kantonsrat, karussell). Rhythmus:

1. Woche 4: Vorlage vorstellen (Motiv «vorlage»): Titel, Termin, worum es geht, bei Ja, bei Nein.
2. Woche 3: Wie der Kantonsrat abgestimmt hat (Motiv «kantonsrat»).
3. Woche 2: Argumente beider Seiten, je ein Paar pro Beitrag (Motiv «paar»), Pro und Contra immer zusammen.
4. Woche 1: Auswertung der Argumente (Motiv «gegen») und eigene Analysen (Karten, Kennzahlen aus der Geoanalyse).
5. Letzte Woche: Erinnerung mit Termin und Adresse.

Noch offen: die Motive aus teilen.py werden im Browser gezeichnet. Für Metricool braucht es PNG-Dateien mit öffentlicher Adresse. Umsetzung als eigener Schritt (Rendering nach dem Muster von social.py).

### 3.3 Erklärposts, einmalig und bei Bedarf

1. Was ist der Politspiegel (drei Ebenen, keine Wertung, Quellen).
2. Wie liest man eine Abstimmungskarte (Farben, Umkehrabstimmungen).
3. Woher die Daten kommen und wie Fehler gemeldet werden.

## 4. Ablauf je Charge

1. `python3 scripts/social.py` erzeugt Bilder, Video und `posts.json` für die neueste Sitzung.
2. Commit und Push nach GitHub, damit die Dateien unter `https://michaeljkahler.github.io/politspiegel/social/…` öffentlich sind. Ein bis zwei Minuten warten.
3. Claude legt die Beiträge aus `posts.json` in Metricool als Entwurf an (draft: true), Termin nach «beste Zeit» je Netzwerk.
4. Michael prüft in Metricool oder im Chat und gibt frei. Claude setzt draft auf false.
5. `posts.json` wird auf `status: freigegeben` gesetzt, damit nichts doppelt angelegt wird.

Im wiederkehrenden Auftrag `kantonsrat-dashboard-update` (1. und 15. jedes Monats) läuft Schritt 1 bis 3 als Teil E, sobald eine neue Sitzung im Datenbestand ist.

## 5. Technik

1. Bilder mit Pillow, Schriften Archivo und Public Sans (OFL) in `scripts/assets/fonts/`.
2. Video mit ffmpeg, H.264, 30 fps, yuv420p, AAC-Stille.
3. Farben und Typografie nach `docs/DESIGN_entscheide.md`.
4. Metricool-Grenzen: Instagram höchstens 10 Bilder je Karussell und 2200 Zeichen Text; TikTok braucht Bild oder Video; YouTube braucht Titel und Kinder-Kennzeichnung.

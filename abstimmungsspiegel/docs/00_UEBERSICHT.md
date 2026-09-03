# Abstimmungsspiegel · Übersicht

Aufbereitung der Argumente zu kantonalen Abstimmungen: Zu jeder Aussage beider
Seiten stehen Wortlaut, Fundstelle und eine Prüfung des Belegs, damit sich jede
Stimmberechtigte ein eigenes Bild machen kann.

Bewertet wird **nie das Argument, sondern sein Beleg.** Werturteile werden
dargestellt, aber nicht benotet.

Der Abstimmungsspiegel ist Teil des Politspiegels Schaffhausen, neben dem
Kantonsratsspiegel. Beide teilen Farben, Schriften und
Datenbasis.

---

## Wo was steht

| Blatt | Inhalt |
|---|---|
| [10_METHODE.md](10_METHODE.md) | Warum nicht «Faktencheck», was die Politikwissenschaft hergibt, das Prüfschema mit fünf Achsen, Redaktionsprozess, Grenzen |
| [11_LAYOUT.md](11_LAYOUT.md) | Aufbau der Seite, Bausteine, Regeln für Telefon und Zeilenmass |
| [12_QS.md](12_QS.md) | Prüfliste vor jeder Veröffentlichung, in fünf Stufen |
| [13_GEODATEN.md](13_GEODATEN.md) | Drei Stufen von roh bis freigegeben, Quellen, Fallen |
| [14_TECHNIK.md](14_TECHNIK.md) | Ordner, Bauablauf, Datenschema, Veröffentlichung |

Diese fünf Blätter gelten für **jede** Vorlage. Alles Vorlagenspezifische steht
im jeweiligen Abstimmungsordner:

```
abstimmungen/2026-09-27-verkehrsfluss/docs/
  INHALT.md            Aussagen, Fundstellen, Textkritik
  GEO.md               welche Kartenebenen, woher, warum
  AUSWERTUNG_bus.md    eigene Rechnungen zu dieser Vorlage
  ENTSCHEIDE.md        was entschieden wurde und warum, was offen ist
  QS_PROTOKOLL.md      was geprüft und korrigiert wurde
```

Die Trennung ist der Zweck der Aufteilung. Beim ersten Fall stand alles in einem
Papier, das auf 1259 Zeilen wuchs; bei der dritten Abstimmung wäre nicht mehr
erkennbar gewesen, ob eine Regel allgemein gilt oder nur für den einen Fall.
Jetzt entscheidet der Ort darüber.

---

## Eine neue Abstimmung aufsetzen

1. **Ordner anlegen** unter `abstimmungen/<datum>-<kurzname>/`, Datum in der
   Form `JJJJ-MM-TT` und Kurzname klein und ohne Umlaute. Das Datum voran, damit
   die Ordner von selbst in der richtigen Reihenfolge stehen.
2. **`vorlage.json` schreiben.** Schema in [14_TECHNIK.md](14_TECHNIK.md).
   Gleiche Zahl Aussagen je Seite, jede mit Fundstelle. Prüfung nach
   [10_METHODE.md](10_METHODE.md).
3. **Geodaten beschaffen**, falls die Vorlage räumlich wirkt. Rohdaten nach
   `geo/01_roh/`, Aufbereitung nach `geo/02_aufbereitet/`, Beschaffungsskripte
   nach `geo/skripte/`. Regeln in [13_GEODATEN.md](13_GEODATEN.md).
4. **Freigeben:** `python3 abstimmungsspiegel/bausteine/geo_freigeben.py <slug>`.
   Der Prüfbericht sagt, was noch fehlt.
5. **Bauen:** `python3 abstimmungsspiegel/bausteine/argumente.py <slug>`.
6. **Übersicht erneuern:** `python3 politspiegel/bauen.py`. Die Übersicht
   liest die Abstimmung aus ihrer `vorlage.json`; eingetragen wird nichts.
   Solange `status` auf `entwurf` steht, trägt der Kasten den Vermerk «noch
   nicht veröffentlichungsreif».
7. **Prüfen** nach [12_QS.md](12_QS.md), Ergebnis nach `docs/QS_PROTOKOLL.md`.

Ob eine Vorlage überhaupt eine Karte braucht, entscheidet eine Frage: Wirkt sie
räumlich unterschiedlich? Eine Steuervorlage tut das nicht, eine Vorlage über
bestimmte Strassen schon. Ohne räumliche Wirkung ist eine Karte Dekoration.

---

## Der Stand

**Phase 1**, eigenständige Seite je Vorlage: umgesetzt, erste Vorlage gebaut,
noch nicht veröffentlicht. Bilder für Social Media (fünf Motive und ein
Karussell je Argument) seit dem 3. September 2026 eingebaut, siehe
[14_TECHNIK.md](14_TECHNIK.md).

**Phase 2**, Verbindung zum Kantonsratsspiegel: steht bereits.
Neben jedem Argument zeigt die Seite, wie die Fraktionen tatsächlich abgestimmt
haben, als dieselbe Frage im Rat lag. Das ist der Mehrwert, den kein bestehendes
Schweizer Angebot hat.

Was noch offen ist, steht je Vorlage in `docs/ENTSCHEIDE.md` unter «Offen».

Entschieden am 3. September 2026: Zweitprüfung und Anhörung der Komitees sind
keine Bedingung für die Veröffentlichung mehr. Veröffentlicht wird, sobald die
Prüfliste in [12_QS.md](12_QS.md) durch ist; die Komitees können sich jederzeit
direkt beim Herausgeber melden, Widerspruch wird als Zitat aufgenommen und
Korrekturen werden sichtbar protokolliert.

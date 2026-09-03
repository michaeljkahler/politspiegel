# Abstimmungsspiegel

Aufbereitung der Argumente zu kantonalen Abstimmungen im Kanton Schaffhausen.
Zu jeder Aussage beider Seiten stehen Wortlaut, Fundstelle und eine Prüfung des
Belegs. Bewertet wird nie das Argument, sondern sein Beleg.

**Einstieg: [docs/00_UEBERSICHT.md](docs/00_UEBERSICHT.md)**

## Bauen

```
python3 abstimmungsspiegel/bausteine/geo_freigeben.py 2026-09-27-verkehrsfluss
python3 abstimmungsspiegel/bausteine/argumente.py     2026-09-27-verkehrsfluss
python3 politspiegel/bauen.py
```

Die Reihenfolge ist zwingend: `argumente.py` bindet nur Geodaten aus
`geo/03_freigegeben/` ein, und diese Stufe füllt `geo_freigeben.py` erst nach
Prüfung. Die Übersicht findet die Abstimmung über ihre `vorlage.json` von
selbst.

Bis zum 3. September 2026 hiess dieser Teil «Argumentespiegel». Der Name
sagte, was geprüft wird, aber nicht, wozu: Auf dem Zettel steht eine
Abstimmung. Der Kantonsratsspiegel daneben zeigt, wie der Rat abstimmt; das
Dach über beiden ist der Politspiegel.

## Abstimmungen

| Termin | Vorlage | Ordner | Stand |
|---|---|---|---|
| 27.09.2026 | Verkehrsflussinitiative, mit Gegenvorschlag | [`abstimmungen/2026-09-27-verkehrsfluss/`](abstimmungen/2026-09-27-verkehrsfluss/) | veröffentlicht am 03.09.2026, Rückmeldungen offen |
| 29.11.2026 | Änderung des Spitalgesetzes (Motion «Mehr Flexibilität in der Lohnpolitik für die Spitäler Schaffhausen») | [`abstimmungen/2026-11-29-spitalgesetz/`](abstimmungen/2026-11-29-spitalgesetz/) | Rohling, Argumentarien ausstehend |

#!/usr/bin/env python3
"""
Tags für die Abstimmungen
=========================
Vergibt je Abstimmung zwei Sorten von Tags:

  form    Was für eine Abstimmung war das? (Antrag, Schlussabstimmung,
          Erheblicherklärung, Ordnungsantrag ...). Grundlage ist die Spalte
          "Betreff" der Excel, die über die Jahre 192 verschiedene Schreibweisen
          kennt, plus der Abstimmungstitel.

  inhalt  Worum ging es? Dreistufig: Überthema, Unterthema, Detailtag. Im
          Dashboard klickt man sich von oben nach unten durch. Gesucht wird in
          Titel, Detailtext, Geschäft, im Protokollsatz zur Abstimmung und in
          den Stichwörtern aus der Debatte (scripts/protokolle.py).

Ein Detailtag greift, wenn sein Muster im eigenen Text der Abstimmung steht
oder mindestens zweimal in den Debattenstichwörtern vorkommt. Damit werden
Nebenbemerkungen aus der Debatte nicht zum Thema.

Ausführen:
    python3 scripts/tags.py                 # Bericht mit Trefferzahlen
    python3 scripts/tags.py --apply         # schreibt die Tags in all_sessions.json
    python3 scripts/tags.py --probe Wohnung # zeigt, was ein Suchwort trifft
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SESSIONS = ROOT / "data" / "all_sessions.json"

# ---------------------------------------------------------------------------
# Form: Art der Abstimmung. Reihenfolge zählt, der erste Treffer ist die
# Hauptform. "Antrag" steht zuletzt, weil das Wort in fast jedem Titel steckt.
# ---------------------------------------------------------------------------
FORM = [
    ("Schlussabstimmung",     r"schluss\s*a[bs]{1,2}timmung|schlussabst"),
    ("Ordnungsantrag",        r"ordnungsantrag"),
    ("Rückweisung",           r"r[üu]ckweisung"),
    ("Rückkommen",            r"r[üu]ckkommen"),
    ("Eintreten",             r"\beintreten|nichteintreten"),
    ("2. Lesung",             r"\b[12]\.\s*lesung"),
    ("Erheblicherklärung",    r"erheblich"),
    ("Abschreibung",          r"abschreibung|abzuschreiben"),
    ("Fristverlängerung",     r"fristverl[äa]ngerung"),
    ("Kommissionszuweisung",  r"zuweisung|[üu]berweisung an|zuweisen"),
    ("Kreditbeschluss",       r"kredit|verpflichtungskredit"),
    ("Genehmigung",           r"genehmigung|genehmigen"),
    ("Wahl",                  r"\bwahl\b|wahlen|wahlgang"),
    ("Traktandenliste",       r"traktandenliste|traktandeliste|traktandenordnung"),
    ("Ausmehrung",            r"ausmehrung|ausmherung|gegen[üu]berstellung"),
    ("Planungserklärung",     r"planungserkl[äa]rung"),
    ("Volksinitiative",       r"volksinitiative|initiative|gegenvorschlag|gegenentwurf"),
    ("Diskussion",            r"\bdiskussion"),
    ("Antrag",                r"antrag"),
]

# ---------------------------------------------------------------------------
# Inhalt: Überthema -> Unterthema -> Detailtag -> Suchmuster
# ---------------------------------------------------------------------------
HIERARCHIE = {
    "Staat und Politik": {
        "Parlament": {
            "Parlamentsbetrieb": r"parlamentsbetrieb|milizparlament|ratsb[üu]ro|"
                                 r"sitzungsgeld|ratsmitglied|kantonsratspr[äa]sid",
            "Geschäftsordnung": r"gesch[äa]ftsordnung|gesch[äa]ftsreglement|"
                                r"vertretungsrecht|kommissionsgr[öo]sse",
            "Vorstösse und Fristen": r"bereinigung der sammlung|fristverl[äa]ngerung|"
                                     r"vorstosskontrolle|kleine anfrage",
            "Kommissionen": r"spezialkommission|kommissionsbestellung|"
                            r"gesch[äa]ftspr[üu]fungskommission|kommissionsarbeit",
        },
        "Regierung und Verwaltung": {
            "Regierungsplanung": r"legislaturprogramm|entwicklungsstrategie|"
                                 r"demografiestrategie|rechenschaftsbericht|"
                                 r"strategische ziele",
            "Verwaltungsorganisation": r"verwaltungsreform|departement|amtsstelle|"
                                       r"organisationsgesetz|verwaltungsorganisation",
            "Kantonspersonal": r"personalgesetz|personalrecht|besoldung|l[öo]hne|"
                               r"lohnsumme|lohnmassnahmen|stellenplan|stellenprozent|"
                               r"anstellungsbedingungen|personalpolitik|personalverordnung",
            "Pensionskasse": r"pensionskasse|berufliche vorsorge|deckungsgrad|"
                             r"stabilisierungsbeitrag",
        },
        "Volksrechte und Wahlen": {
            "Wahlrecht": r"wahlrecht|wahlkreis|wahlverfahren|stille wahl|proporz|majorz",
            "Stimmrecht und Initiativen": r"stimmrecht|volksrecht|unterschriftenzahl|"
                                          r"initiativrecht|referendumsrecht",
            "Politikfinanzierung": r"politikfinanzierung|transparenz.{0,25}politik|"
                                   r"parteienfinanzierung|offenlegung.{0,20}spenden",
        },
        "Gemeinden und Kooperation": {
            "Gemeindewesen": r"gemeindegesetz|gemeindeorganisation|gemeindefusion|"
                             r"gemeindeautonomie|gemeindeversammlung",
            "Aufgabenteilung": r"aufgabenteilung|entflechtung|lastenausgleich|"
                               r"aufgaben- und finanzierung",
            "Interkantonale Verträge": r"interkantonal|konkordat|vereinbarung mit den kantonen|"
                                       r"ostschweiz|grenz[üu]berschreitend",
        },
        "Information und Daten": {
            "Datenschutz": r"datenschutz|personendaten|informationssicherheit",
            "Digitalisierung": r"digitalisierung|informatik|e-government|cyber|"
                               r"it-projekt|elektronische",
            "Archiv und Öffentlichkeit": r"archiv|[öo]ffentlichkeitsprinzip|akteneinsicht",
            "Medien": r"\bmedien|medienplatz|presse|journalis|zeitung",
        },
    },
    "Finanzen und Steuern": {
        "Steuern": {
            "Steuerfuss": r"steuerfuss|steueransatz",
            "Steuergesetz": r"steuergesetz|besteuerung|steuerabzug|steuertarif|"
                            r"steuerbefreiung|individualbesteuerung",
            "Unternehmenssteuern": r"unternehmenssteuer|gewinnsteuer|kapitalsteuer|"
                                   r"mindestbesteuerung|juristische personen",
            "Besondere Abgaben": r"mehrwertabgabe|rebsteuer|handänderungssteuer|"
                                 r"motorfahrzeugsteuer|erbschaftssteuer|geb[üu]hren",
        },
        "Haushalt": {
            "Budget und Finanzplan": r"\bbudget|finanzplan|voranschlag|oktoberbrief|"
                                     r"globalbudget|aufgaben- und finanzplan",
            "Staatsrechnung": r"staatsrechnung|jahresrechnung|rechnungsabschluss|"
                              r"gesch[äa]ftsbericht",
            "Nachtragskredite": r"nachtragskredit|zusatzkredit|kreditüberschreitung",
            "Verpflichtungskredite": r"verpflichtungskredit|investitionskredit|"
                                     r"objektkredit",
        },
        "Finanzpolitik": {
            "Finanzhaushaltsgesetz": r"finanzhaushaltsgesetz|finanzhaushalt",
            "Reserven und Fonds": r"finanzpolitische reserve|\bfipol\b|"
                                  r"schwankungsreserve|generationenfonds|"
                                  r"[äa]ufnung|entnahme aus dem fonds",
            "Finanzausgleich": r"finanzausgleich|\bnfa\b|ressourcenausgleich",
            "Schulden und Vermögen": r"schuldenbremse|verschuldung|nettoschuld|"
                                     r"eigenkapital|nationalbank",
        },
        "Beteiligungen": {
            "Kantonalbank": r"\bshkb\b|kantonalbank",
            "Energieunternehmen": r"\baxpo\b|\beks\b|elektrizit[äa]tswerk",
            "Eignerstrategie": r"eignerstrategie|eigent[üu]merstrategie|"
                               r"beteiligung des kantons|aktion[äa]rsbindung",
        },
    },
    "Raum, Bau und Verkehr": {
        "Raumplanung und Bau": {
            "Richt- und Zonenplanung": r"richtplan|zonenplan|nutzungsplanung|"
                                       r"einzonung|auszonung|bauzone|ortsplanung",
            "Baugesetz": r"baugesetz|baubewilligung|gestaltungsplan|bauvorschrift|"
                         r"bauabstand|baureglement",
            "Wohnen und Bauland": r"wohnraum|wohnungsnot|wohnbau|wohnungsbau|"
                                  r"wohneigentum|mietwohnung|gemeinn[üu]tzige.{0,20}wohn|"
                                  r"wohnpolitik|bauland|verdichtung|siedlungsentwicklung|"
                                  r"leerstand|erstwohnung|zweitwohnung",
            "Landerwerb und Liegenschaften": r"landerwerb|liegenschaft|immobilien|"
                                             r"kantonsgeb[äa]ude|hochbauten",
        },
        "Verkehr": {
            "Strassen": r"strassengesetz|strassenrichtplan|kantonsstrasse|strassenbau|"
                        r"stra[sß]senunterhalt|umfahrung|kreisel",
            "Öffentlicher Verkehr": r"[öo]ffentliche[rn]? verkehr|\b[öo]v\b|bahn|\bbus\b|"
                                    r"ortsverkehr|hochrhein-bodensee|fahrplan|tarifverbund|"
                                    r"zuglinie|s-bahn|haltestelle|regionalverkehr|"
                                    r"ortsverkehrsbeitrag",
            "Velo und Fussverkehr": r"velo|fahrrad|fussg[äa]nger|langsamverkehr|fussverkehr|"
                                    r"veloweg|radweg",
            "Motorfahrzeuge und Parkierung": r"parkier|parkplatz|strassenverkehrssteuer|"
                                             r"strassenverkehrsamt|fahrzeugpr[üu]fung|"
                                             r"verkehrssicherheit",
        },
        "Infrastruktur": {
            "Hochwasserschutz": r"hochwasser|r[üu]ckhaltebecken|wasserbau",
            "Wasserversorgung und Abwasser": r"trinkwasser|abwasser|kl[äa]ranlage|"
                                             r"wasserversorgung|wasserwirtschaft",
            "Bauprojekte": r"neubau|sanierung|umbau|erweiterungsbau|schulhaus|"
                           r"spitalbau|kantonsschule",
        },
    },
    "Umwelt, Energie und Klima": {
        "Energie": {
            "Energiegesetz": r"energiegesetz|energieverordnung|energievorschrift|"
                             r"geb[äa]udeprogramm",
            "Erneuerbare Energien": r"solar|photovoltaik|windenergie|windkraft|biogas|"
                                    r"holzenergie|geothermie|w[äa]rmeverbund",
            "Energieversorgung": r"stromversorgung|energieversorgung|netzzuschlag|"
                                 r"stromnetz|kernkraft|versorgungssicherheit",
            "Energieförderung": r"energief[öo]rder|f[öo]rderprogramm.{0,20}energie|"
                                r"energie- und klimafonds",
        },
        "Klima und Natur": {
            "Klimaschutz": r"klimaschutz|klimafonds|klimapolitik|\bco2\b|"
                           r"treibhausgas|netto null",
            "Klimaanpassung": r"klimaanpassung|hitze|trockenheit|klimawandel",
            "Naturschutz und Biodiversität": r"naturschutz|biodiversit|artenschutz|"
                                             r"landschaftsschutz|[öo]kologische aufwertung",
            "Wald": r"\bwald|forst|waldgesetz|holznutzung",
            "Gewässer": r"gew[äa]sser|gew[äa]sserraum|renaturierung|\brhein\b|fischerei",
        },
        "Umweltbelastung": {
            "Abfall und Recycling": r"abfall|entsorgung|recycling|deponie|"
                                    r"kehricht|littering",
            "Luft und Lärm": r"luftreinhaltung|feinstaub|l[äa]rmschutz|fluglärm|"
                             r"lichtverschmutzung",
            "Altlasten und Schadstoffe": r"altlast|schadstoff|pestizid|pflanzenschutzmittel|"
                                         r"radioaktiv|tiefenlager",
        },
    },
    "Bildung, Kultur und Sport": {
        "Schule": {
            "Volksschule": r"volksschule|schulgesetz|schuldekret|kindergarten|"
                           r"primarschule|sekundarschule|unterricht|lehrplan",
            "Lehrpersonen": r"lehrperson|lehrerinnen|schulleitung|lehrerbesoldung",
            "Sonderpädagogik und Betreuung": r"sonderp[äa]dagog|integrative|"
                                             r"schulsozialarbeit|tagesstruktur|"
                                             r"schulische betreuung",
            "Privatschulen": r"privatschul|privater unterricht|homeschooling",
        },
        "Weiterführende Bildung": {
            "Mittelschule und Berufsbildung": r"kantonsschule|gymnasium|berufsbildung|"
                                              r"berufsfachschule|berufsmatur|lehrbetrieb|"
                                              r"lernende|brückenangebot",
            "Hochschule": r"hochschul|\bphsh\b|universit[äa]t|fachhochschule|"
                          r"p[äa]dagogische hochschule",
            "Stipendien": r"stipendi|studiendarlehen|ausbildungsbeitrag",
        },
        "Kultur und Sport": {
            "Kulturförderung": r"kulturf[öo]rder|kulturbeitrag|museum|theater|"
                               r"bibliothek|kulturhauptstadt|musikschule",
            "Denkmalpflege": r"denkmalpflege|heimatschutz|arch[äa]ologie|ortsbild",
            "Sport": r"\bsport|hallenbad|sportanlage|\bkasak\b|turnhalle|breitensport",
        },
    },
    "Gesundheit und Soziales": {
        "Gesundheitsversorgung": {
            "Spitäler": r"spital|spit[äa]ler|spitalgesetz|spitalrat|breitenau|"
                        r"spitalliste|globalkredit.{0,20}spital",
            "Ambulante Versorgung": r"hausarzt|arztpraxis|notfall|rettungsdienst|"
                                    r"ambulant|apotheke",
            "Psychische Gesundheit": r"psychiatr|psychisch|psychotherap|suizid",
            "Prävention": r"pr[äa]vention|screening|impfung|gesundheitsf[öo]rderung|"
                          r"sucht|tabak|alkohol",
        },
        "Alter und Pflege": {
            "Pflegefinanzierung": r"pflegefinanzierung|pflegegesetz|pflegekosten|"
                                  r"restfinanzierung",
            "Alters- und Pflegeheime": r"pflegeheim|altersheim|altersbetreuung|"
                                       r"heimliste|betagte|palliative",
            "Spitex und Betreuung zuhause": r"spitex|betreuung zuhause|hilfe und pflege",
        },
        "Soziale Sicherheit": {
            "Sozialhilfe": r"sozialhilfe|sozialhilfegesetz|existenzsicherung|armut",
            "Ergänzungsleistungen und AHV": r"erg[äa]nzungsleistung|\bahv\b|\biv\b|"
                                            r"invalidenversicherung|sozialversicherung|"
                                            r"alters- und hinterlassenen",
            "Prämienverbilligung": r"pr[äa]mienverbilligung|krankenversicherung|"
                                   r"krankenkasse|\bkvg\b",
            "Behinderung und Teilhabe": r"behinderten|behinderung|inklusion|"
                                        r"gleichstellung.{0,20}behinder",
        },
        "Familie und Gesellschaft": {
            "Kinderbetreuung": r"\bkita\b|kinderbetreuung|krippe|tagesfamilie|"
                               r"familienerg[äa]nzende",
            "Familienpolitik": r"familienzulage|familienpolitik|elternzeit|"
                               r"vereinbarkeit|kinderzulage",
            "Jugend": r"jugendliche|jugendarbeit|jugendschutz|kinder- und jugend",
            "Gleichstellung": r"gleichstellung|diskriminierung|h[äa]usliche gewalt|"
                              r"frauenhaus|lohngleichheit",
            "Asyl und Integration": r"asyl|integration|migration|fl[üu]chtling|"
                                    r"einb[üu]rgerung|ausl[äa]nderrecht",
        },
    },
    "Wirtschaft und Arbeit": {
        "Standort und Förderung": {
            "Wirtschaftsförderung": r"wirtschaftsf[öo]rderung|standortf[öo]rderung|"
                                    r"standortentwicklung|regionalentwicklung|"
                                    r"ansiedlung|innovation",
            "Tourismus": r"tourismus|touristisch|beherbergung|gastgewerbe",
            "Gewerbe und Handel": r"gewerbe|\bkmu\b|laden[öo]ffnung|binnenmarkt|"
                                  r"beschaffungswesen|submission|vergabe",
        },
        "Arbeit": {
            "Arbeitsmarkt": r"arbeitsmarkt|arbeitslos|fachkr[äa]ftemangel|"
                            r"stellensuchende|arbeitsvermittlung",
            "Arbeitsbedingungen": r"arbeitsgesetz|mindestlohn|arbeitsbedingungen|"
                                  r"gesamtarbeitsvertrag|teilzeit|arbeitszeit|"
                                  r"lohndumping",
        },
        "Land- und Forstwirtschaft": {
            "Landwirtschaft": r"landwirtschaftsgesetz|landwirtschaft|bauernbetrieb|"
                              r"direktzahlung|tierhaltung|strukturverbesserung",
            "Rebbau": r"rebbau|weinbau|rebfl[äa]che|rebsteuer",
        },
    },
    "Sicherheit und Recht": {
        "Polizei und Sicherheit": {
            "Polizeigesetz": r"polizeigesetz|polizeikorps|bedrohungsmanagement|"
                             r"polizeiliche|videoüberwachung",
            "Bevölkerungsschutz": r"zivilschutz|bev[öo]lkerungsschutz|feuerwehr|"
                                  r"katastrophen|notfallplanung",
            "Waffen und Gewalt": r"waffen|gewaltschutz|h[äa]usliche gewalt",
        },
        "Justiz": {
            "Gerichtsorganisation": r"justizgesetz|gerichtsorganisation|obergericht|"
                                    r"kantonsgericht|friedensrichter|rechtspflege",
            "Strafverfolgung": r"staatsanwaltschaft|strafverfolgung|strafprozess|"
                               r"strafvollzug|gef[äa]ngnis|einf[üu]hrungsgesetz.{0,30}strafgesetz",
            "Zivilrecht": r"zivilgesetzbuch|mietzins|mietrecht|hinterlegungsstelle|"
                          r"kindes- und erwachsenenschutz|\bkesb\b",
            "Verwaltungsrechtspflege": r"verwaltungsrechtspflege|rechtsschutz in verwaltungs|"
                                       r"beschwerdeverfahren|ombudsperson",
        },
    },
    "Verfahren im Rat": {
        "Ratsverfahren": {
            "Traktandenliste": r"traktandenliste|traktandeliste|umstellung der traktanden",
            "Ordnungsanträge": r"sofortige abstimmung|abbruch der diskussion|"
                               r"schlussvotum|ordnungsantrag",
            "Wahlgeschäfte": r"wahlgang|stille wahl|wahl eines mitglieds|"
                             r"wahl von zwei mitgliedern|ersatzwahl",
            "Formelles": r"ung[üu]ltige abstimmung|wiederholung der abstimmung|"
                         r"fehlerhafte abstimmung|verschiebung",
        },
    },
}


def eigener_text(v):
    """Text, der zur Abstimmung selbst gehört."""
    return " ".join([v.get("titel") or "", v.get("details") or "",
                     v.get("geschaeft") or "", v.get("typ") or "",
                     v.get("kontext") or ""])


def form_tags(v):
    t = f"{v.get('typ') or ''} {v.get('titel') or ''}"
    treffer = [tag for tag, muster in FORM if re.search(muster, t, re.I)]
    if not treffer:
        d = v.get("details") or ""
        treffer = [tag for tag, muster in FORM if re.search(muster, d, re.I)]
    return treffer[:3] or ["Sonstige"]


def inhalt_tags(v):
    """(überthemen, unterthemen, detailtags) für eine Abstimmung."""
    eigen = eigener_text(v)
    debatte = " ".join(v.get("stichworte") or [])
    ober, unter, detail = [], [], []
    for o, unterthemen in HIERARCHIE.items():
        for u, tags in unterthemen.items():
            for tag, muster in tags.items():
                if re.search(muster, eigen, re.I) or re.search(muster, debatte, re.I):
                    detail.append(tag)
                    if u not in unter:
                        unter.append(u)
                    if o not in ober:
                        ober.append(o)
    return ober, unter, detail


def hierarchie_flach():
    """Liste {ueberthema, unterthema, tag} in Reihenfolge der Definition."""
    out = []
    for o, unterthemen in HIERARCHIE.items():
        for u, tags in unterthemen.items():
            for tag in tags:
                out.append({"ueberthema": o, "unterthema": u, "tag": tag})
    return out


def main():
    daten = json.load(open(SESSIONS, encoding="utf-8"))
    votes = [v for s in daten["sessions"] for v in s["votes"]]

    if "--probe" in sys.argv:
        wort = sys.argv[sys.argv.index("--probe") + 1]
        pat = re.compile(wort, re.I)
        treffer = [v for v in votes
                   if pat.search(eigener_text(v) + " " + " ".join(v.get("stichworte") or []))]
        print(f"«{wort}»: {len(treffer)} Abstimmungen")
        for v in treffer[:15]:
            print(f"   {(v.get('titel') or '')[:50]:50} | {inhalt_tags(v)[2][:4]}")
        return

    fz, oz, uz, dz = Counter(), Counter(), Counter(), Counter()
    ohne = 0
    for v in votes:
        f = form_tags(v)
        o, u, dt = inhalt_tags(v)
        fz.update(f); oz.update(o); uz.update(u); dz.update(dt)
        if not dt:
            ohne += 1
        if "--apply" in sys.argv:
            v["tags_form"] = f
            v["tags_ueberthema"] = o
            v["tags_unterthema"] = u
            v["tags_detail"] = dt

    flach = hierarchie_flach()
    print(f"{len(votes)} Abstimmungen, {len(flach)} Detailtags in "
          f"{len(HIERARCHIE)} Überthemen\n")
    print("FORM")
    for tag, n in fz.most_common():
        print(f"  {n:5}  {tag}")
    print(f"\nINHALT  ({len(votes)-ohne} von {len(votes)} haben mindestens einen "
          f"Detailtag, {(len(votes)-ohne)/len(votes)*100:.0f} Prozent)")
    for o, unterthemen in HIERARCHIE.items():
        print(f"\n  {oz.get(o,0):5}  {o.upper()}")
        for u, tags in unterthemen.items():
            print(f"  {uz.get(u,0):5}    {u}")
            for tag in tags:
                print(f"  {dz.get(tag,0):5}      {tag}")

    if "--apply" in sys.argv:
        daten["tags_form_liste"] = [t for t, _ in FORM] + ["Sonstige"]
        daten["tags_hierarchie"] = flach
        json.dump(daten, open(SESSIONS, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"\n{SESSIONS.name} geschrieben.")
    else:
        print("\n(Probelauf, nichts geschrieben. Mit --apply schreiben.)")


if __name__ == "__main__":
    main()

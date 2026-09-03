#!/usr/bin/env python3
# Kosten-Nutzen-Verhaeltnis je Abschnitt (illustratives Szenario, gleiche Saetze wie Wirtschaftlichkeitsblatt).
# Nutzen = Unfallkostenersparnis + annualisierte Laermaufwertung; Kosten = Zeitkosten.
# Wichtig: rein monetaer, ohne nicht-monetaere Nutzen (Aufenthaltsqualitaet, Gesundheit, subjektive Sicherheit).
import json
VTTS=42.50      # CHF/Fahrzeugstunde (ARE/VSS)
DT_S=20         # Sekunden Zusatzzeit je km (ASTRA FB 1663)
DAYS=365
RED=0.20        # Unfallreduktion durch Tempo 30 (Szenario)
YEARS=15        # Auswertungszeitraum Unfaelle
VAL_FASS=900000 # CHF Wert je laermbelastete Fassade (Annahme)
NSDI=0.005      # Wertminderung je dB (ZKB/Baranzini)
DB=3            # dB-Reduktion durch Tempo 30 (BAFU)
CAP=0.03        # Kapitalisierung zur Annualisierung
# mittlere Unfallkosten je Personenschaden-Unfall, kantonal aus Schweregraden
_m=json.load(open('master_gemeinde.json'))['master']
_tot=sum(r['unf_total'] for r in _m) or 1
UNFALLKOSTEN_MEAN=(sum(r['getoetet'] for r in _m)*3170000
                   +sum(r['schwer'] for r in _m)*530000
                   +sum(r['leicht'] for r in _m)*33000)/_tot

def zeitkosten(p):  return p['fahrleistung']*DT_S/3600.0*DAYS*VTTS
def unfallnutzen(p):return (p['unf']/YEARS)*UNFALLKOSTEN_MEAN*RED
def laermnutzen(p): return p['fass_igw']*VAL_FASS*NSDI*DB*CAP
def nutzen(p):      return unfallnutzen(p)+laermnutzen(p)
def knv(p):
    z=zeitkosten(p)
    return (nutzen(p)/z) if z>0 else 0.0

# Zonen-Grenzen datengetrieben: Terzile der KNV-Verteilung ueber die verkehrsorientierten
# Abschnitte mit relevantem Verkehr (>=2000 Fz-km/Tag). Absolute Referenz waere KNV=1 (Nutzen=Kosten).
_rel=[p for p in json.load(open('per_abschnitt.json')) if p['km']>=0.2 and p['fkt']=='VO' and p['fahrleistung']>=2000]
_kn=sorted(knv(p) for p in _rel)
ZONE_T1=round(_kn[len(_kn)//3],3)          # untere Terzilgrenze (~0.066)
ZONE_T2=round(_kn[2*len(_kn)//3],3)        # obere Terzilgrenze (~0.113)
def knv_cat(v):
    return 'hoch' if v>=ZONE_T2 else ('mittel' if v>=ZONE_T1 else 'gering')

#!/usr/bin/env python3
# Gemeinsame Definition der Massnahmeneignung (Nutzen) pro Kantonsstrasse.
# Nutzen-Score kombiniert Sicherheits- und Laermnutzen:
#   N = Unfaelle pro km und Jahr  +  Laermfassaden ueber IGW / 50
# Kategorien (feste, nachvollziehbare Schwellen):
#   hoch   : N >= 1.5   (hohe Unfalldichte und/oder starke Laermbelastung)
#   mittel : N >= 0.6
#   gering : darunter

def nutzen_score(p):
    return p['unf_km_jahr'] + p['fass_igw'] / 50.0

def nutzen_cat(p):
    n = nutzen_score(p)
    if n >= 1.5: return 'hoch'
    if n >= 0.6: return 'mittel'
    return 'gering'

CAT_ORDER = ['hoch', 'mittel', 'gering']
CAT_LABEL = {'hoch': 'hohe Eignung', 'mittel': 'mittlere Eignung', 'gering': 'geringe Eignung'}
# Bubble-Fuellung / Rand (sequenzielle Gruen-Skala, nicht wertend-rot)
CAT_FILL   = {'hoch': '#0f7a54', 'mittel': '#63c39b', 'gering': '#d2e2da'}
CAT_STROKE = {'hoch': '#08492f', 'mittel': '#2f9e75', 'gering': '#9cbcae'}
# Kartenlinien (etwas kraeftiger, da duenn dargestellt)
CAT_LINE   = {'hoch': '#0f7a54', 'mittel': '#3aa87d', 'gering': '#aecabe'}

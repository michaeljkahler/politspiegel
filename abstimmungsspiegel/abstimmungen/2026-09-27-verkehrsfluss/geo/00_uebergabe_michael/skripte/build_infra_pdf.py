#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from collections import defaultdict, Counter
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak,
                                Table, TableStyle, KeepTogether)
from reportlab.lib.enums import TA_LEFT
from PIL import Image as PILImage

SLATE=colors.HexColor('#2F3B52'); GREY=colors.HexColor('#52514e')
st=getSampleStyleSheet()
H1=ParagraphStyle('H1',parent=st['Title'],fontName='Helvetica-Bold',fontSize=20,textColor=SLATE,alignment=TA_LEFT,spaceAfter=6,leading=24)
SUB=ParagraphStyle('SUB',parent=st['Normal'],fontName='Helvetica',fontSize=11.5,textColor=GREY,spaceAfter=2)
H2=ParagraphStyle('H2',parent=st['Heading2'],fontName='Helvetica-Bold',fontSize=13.5,textColor=SLATE,spaceBefore=8,spaceAfter=5,leading=17)
BODY=ParagraphStyle('BODY',parent=st['Normal'],fontName='Helvetica',fontSize=10.3,textColor=colors.HexColor('#1a1a1a'),leading=14.5,spaceAfter=6)
BULL=ParagraphStyle('BULL',parent=BODY,leftIndent=12,spaceAfter=3)
SMALL=ParagraphStyle('SMALL',parent=st['Normal'],fontName='Helvetica',fontSize=8.4,textColor=GREY,leading=11)
CAP=ParagraphStyle('CAP',parent=st['Normal'],fontName='Helvetica',fontSize=9.2,textColor=colors.HexColor('#333'),leading=12,spaceBefore=4)

R=json.load(open('infra_results.json'))
FACS=json.load(open('facilities.json'))
def canon(g): return (g or '').replace(' (SH)','').strip()
DS=Counter(f['cat'] for f in FACS)
ADM=defaultdict(Counter)
for f in FACS: ADM[canon(f['gem'])][f['cat']]+=1
def km(m): return ('%.2f'%(m/1000)).replace('.',',')
def pct(x,t): return ('%.0f'%(100*x/t)) if t else '0'
def cat_tot(key): return sum(r['stats'][key] for r in R)
TOT=sum(r['stats']['betroffen'] for r in R)
A100=cat_tot('alle_100'); A300=cat_tot('alle_300'); A500=cat_tot('alle_500')

story=[]
story.append(Spacer(1,0.3*cm))
story.append(Paragraph('Sensible Nutzungen an den betroffenen Kantonsstrassen', H1))
story.append(Paragraph('Grundlage zur Definition «kurze Abschnitte» · Verkehrsflussinitiative Kanton Schaffhausen', SUB))
story.append(Paragraph('Umkreise von 100 m, 300 m und 500 m um Schulen, Kindergärten, Alters- und Pflegeheime sowie weitere Sozialeinrichtungen. Stand: 19. August 2026.', SMALL))
story.append(Spacer(1,0.3*cm))
story.append(Paragraph('Zweck', H2))
story.append(Paragraph('Die Initiative lässt für «kurze Abschnitte» Ausnahmen vom Grundsatz Tempo 50 zu. Diese Auswertung zeigt je Gemeinde, wo die betroffenen '
 'verkehrsorientierten Kantonsstrassen innerorts nahe an sensiblen Nutzungen verlaufen, und macht so an direkten Beispielen fassbar, wie sich der Passus '
 'abgrenzen lässt. Der neu ergänzte 100-m-Umkreis bildet die enge, für «kurz» eher taugliche Nähe ab; 300 m und 500 m zeigen, wie stark ein weiter gefasstes '
 'Kriterium das betroffene Netz erfassen würde.', BODY))
story.append(Paragraph('Vorgehen', H2))
story.append(Paragraph('Betroffene Strassen sind die verkehrsorientierten Kantonsstrassen (überregional und regional nach kantonalem Strassenrichtplan) innerhalb '
 'des Baugebiets. Die Infrastruktur stammt aus dem gelieferten GeoPackage mit '+str(len(FACS))+' Standorten ('+str(DS['schule'])+' Schulen, '+str(DS['kindergarten'])+
 ' Kindergärten, '+str(DS['altersheim'])+' Alters- und Pflegeheime sowie '+str(DS['sozial'])+' weitere Sozialeinrichtungen wie betreutes Wohnen und Wohngruppen; Quelle OSM und kantonal). '
 'Um jede Anlage werden Umkreise von 100 m, 300 m und 500 m (Luftlinie) gelegt, je Gruppe eigene Farbe. Als «Kandidat kurzer Abschnitt» gilt eine betroffene Strasse '
 'innerhalb von 100 m (eng, kräftig rot) beziehungsweise 300 m (weiter, blass) einer Nutzung. Alle Berechnungen in LV95 (EPSG:2056).', BODY))
story.append(Paragraph('Kernbefunde', H2))
for b in [
 f'Kantonsweit sind {km(TOT)} km Kantonsstrasse betroffen. Innerhalb von 100 m einer sensiblen Nutzung liegen {km(A100)} km ({pct(A100,TOT)} Prozent), innerhalb von 300 m {km(A300)} km ({pct(A300,TOT)} Prozent) und innerhalb von 500 m {km(A500)} km ({pct(A500,TOT)} Prozent).',
 f'Der 100-m-Umkreis grenzt deutlich enger ein als der 300-m-Umkreis: rund {pct(A100,TOT)} statt {pct(A300,TOT)} Prozent des betroffenen Netzes. Nach Gruppe (innerhalb 100 m): Schulen {km(cat_tot("schule_100"))} km, Kindergärten {km(cat_tot("kindergarten_100"))} km, Alters- und Pflegeheime {km(cat_tot("altersheim_100"))} km, weitere Sozialeinrichtungen {km(cat_tot("sozial_100"))} km.',
 'Die Spannweite bleibt gross: bei 100 m reicht sie von 0 Prozent (viele Dörfer, deren Durchfahrt die Nutzungen umgeht) bis rund einem Drittel (Bargen, Ramsen), bei 300 m bis über 90 Prozent.',
]:
    story.append(Paragraph('•&nbsp;&nbsp;'+b, BULL))
story.append(Paragraph('Was das für die Definition bedeutet', H2))
story.append(Paragraph('Auch der enge 100-m-Umkreis entspricht entlang einer Strasse bis rund 200 m Fahrbahn je Anlage; auf anlagendichten Achsen summiert er sich weiter, '
 'in Schaffhausen etwa auf der Bachstrasse auf rund 560 m. Ein reines Umkreis-Kriterium bleibt damit grobkörnig. Für eine wirklich enge Fassung des Passus bieten sich '
 'an: die Beschränkung auf die tatsächliche Strassenfront oder Querung der Anlage statt eines Kreisumkreises, eine Längenobergrenze je Abschnitt (etwa 50 bis 150 m), '
 'sowie die Kopplung mit einem Sicherheits- oder Querungskriterium. Die drei Umkreise in Tabelle und Karten erlauben, die Schwelle bewusst zu wählen und ihre Wirkung auf '
 'das betroffene Netz direkt abzulesen. Die roten Abschnitte auf den Karten sind die engen Kandidaten (bis 100 m), die blassen die weiteren (bis 300 m).', BODY))
story.append(PageBreak())

story.append(Paragraph('Übersicht je Gemeinde', H2))
story.append(Paragraph('Betroffene verkehrsorientierte Kantonsstrasse innerorts und Anteil innerhalb 100 m, 300 m bzw. 500 m einer sensiblen Nutzung. '
 'Sortiert nach betroffener Länge. Anlagen S/K/H/So = Standorte je Gemeinde (Schule / Kindergarten / Heim / weitere Sozialeinrichtung).', SMALL))
story.append(Spacer(1,0.18*cm))
head=['Gemeinde','betr.\nkm','≤100 m\nkm','≤100 m\n%','≤300 m\nkm','≤300 m\n%','≤500 m\nkm','≤500 m\n%','Anlagen\nS/K/H/So']
data=[head]
for r in R:
    s=r['stats']; g=r['gemeinde'].replace(' (SH)',''); a=ADM[canon(r['gemeinde'])]
    data.append([g, km(s['betroffen']), km(s['alle_100']), pct(s['alle_100'],s['betroffen']),
                 km(s['alle_300']), pct(s['alle_300'],s['betroffen']), km(s['alle_500']), pct(s['alle_500'],s['betroffen']),
                 f"{a['schule']}/{a['kindergarten']}/{a['altersheim']}/{a['sozial']}"])
ST={c:sum(ADM[canon(r['gemeinde'])][c] for r in R) for c in ('schule','kindergarten','altersheim','sozial')}
data.append(['Kanton total', km(TOT), km(A100), pct(A100,TOT), km(A300), pct(A300,TOT), km(A500), pct(A500,TOT),
             f"{ST['schule']}/{ST['kindergarten']}/{ST['altersheim']}/{ST['sozial']}"])
tbl=Table(data, colWidths=[3.15*cm,1.4*cm,1.55*cm,1.4*cm,1.55*cm,1.4*cm,1.55*cm,1.4*cm,2.2*cm], repeatRows=1)
tsty=[('FONT',(0,0),(-1,-1),'Helvetica',8),('FONT',(0,0),(-1,0),'Helvetica-Bold',8),
    ('BACKGROUND',(0,0),(-1,0),SLATE),('TEXTCOLOR',(0,0),(-1,0),colors.white),
    ('ALIGN',(1,0),(-1,-1),'CENTER'),('ALIGN',(0,0),(0,-1),'LEFT'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
    ('TOPPADDING',(0,0),(-1,-1),2.5),('BOTTOMPADDING',(0,0),(-1,-1),2.5),
    ('LINEBELOW',(0,0),(-1,0),0.6,SLATE),('GRID',(0,1),(-1,-1),0.25,colors.HexColor('#dddddd')),
    ('FONT',(0,-1),(-1,-1),'Helvetica-Bold',8),('BACKGROUND',(0,-1),(-1,-1),colors.HexColor('#eef0f3'))]
for i in range(1,len(data)-1):
    if i%2==0: tsty.append(('BACKGROUND',(0,i),(-1,i),colors.HexColor('#f7f7f5')))
tbl.setStyle(TableStyle(tsty)); story.append(tbl)
story.append(Spacer(1,0.18*cm))
story.append(Paragraph('Lesehilfe: 0 Prozent bei 100 m bedeutet, dass keine betroffene Strasse innerhalb 100 m einer Nutzung liegt, die Durchfahrt also einen Abstand hält. '
 'Der Sprung von der 100- zur 300-Prozent-Spalte zeigt, wie stark ein weiter gefasstes Kriterium zusätzliche Strecken erfasst. Kantonsweit umfasst der Datensatz '
 +str(len(FACS))+' Standorte ('+str(DS['schule'])+'/'+str(DS['kindergarten'])+'/'+str(DS['altersheim'])+'/'+str(DS['sozial'])+'); aufgeführt sind die 17 Gemeinden mit betroffenen Strassen.', SMALL))
story.append(PageBreak())

UW=17.6*cm; MAXH=22.6*cm
def img(fn):
    w,h=PILImage.open(fn).size; asp=h/w; iw=UW; ih=iw*asp
    if ih>MAXH: ih=MAXH; iw=ih/asp
    return Image(fn,width=iw,height=ih)
def clean(nm): return 'unbenannt' if nm in ('Namenlos','unbenannt','') else nm.replace('strasse','str.')
def L(m): return (('%.2f'%(m/1000)).replace('.',',')+' km') if m>=1000 else (str(int(round(m)))+' m')
def ex_caption(r):
    s=r['stats']; n1=r['cand100_names']
    if n1 and r['cand100_len']>=1:
        base='Enge Kandidaten (≤ 100 m, nach Länge): '+' · '.join(f'{clean(n)} {L(l)}' for n,l in n1[:5])+'.'
    else:
        base='Keine betroffene Strasse innerhalb 100 m einer sensiblen Nutzung.'
    return base+f' Anteil des betroffenen Netzes: ≤ 100 m {pct(s["alle_100"],s["betroffen"])} Prozent, ≤ 300 m {pct(s["alle_300"],s["betroffen"])} Prozent, ≤ 500 m {pct(s["alle_500"],s["betroffen"])} Prozent.'
for r in R:
    story.append(KeepTogether([img(f"karte_{r['slug']}.png"), Paragraph(ex_caption(r), CAP)]))
    story.append(PageBreak())

story.append(Paragraph('Hinweise und Vorbehalte', H2))
for b in [
 'Umkreise sind Luftlinien um den Anlagenstandort, keine Netz- oder Fusswegdistanzen; die fussläufige Nähe kann geringer sein.',
 'Ein 100-m-Umkreis erfasst entlang einer Strasse bis rund 200 m Fahrbahn, ein 300-m-Umkreis bis rund 600 m. Die Anteile sind Obergrenzen für «Nähe», kein Mass für «kurz».',
 'Enthalten sind vier Gruppen: Schulen, Kindergärten, Alters- und Pflegeheime (inklusive Wohngruppen und betreutes Wohnen) sowie 15 weitere Sozialeinrichtungen aus einer separaten Ebene.',
 'Die Standorte stammen aus dem gelieferten GeoPackage (OpenStreetMap und kantonale Quellen); einzelne Standorte sind nachführbar. Ein Teil ist als «wahrscheinlich» eingestuft.',
 'Betroffen = verkehrsorientierte Kantonsstrassen innerorts (Baugebiet). Innerorts ist über das rechtsgültige Baugebiet abgegrenzt, nicht über die signalisierten Ortstafeln.',
]:
    story.append(Paragraph('•&nbsp;&nbsp;'+b, BULL))
story.append(Spacer(1,0.18*cm))
story.append(Paragraph('Quellen: Kantonsstrassen und Funktionsklassen (Strassenrichtplan), Baugebiet: Amt für Geoinformation Kanton Schaffhausen (geo.sh.ch). '
 'Standorte Schulen, Kindergärten, Alters- und Pflegeheime, weitere Sozialeinrichtungen: geliefertes GeoPackage (OpenStreetMap-Mitwirkende und kantonale Quellen). Bezugssystem LV95 (EPSG:2056).', SMALL))

def footer(cv,doc):
    cv.saveState(); cv.setFont('Helvetica',8); cv.setFillColor(GREY)
    cv.drawString(1.6*cm,1.0*cm,'Sensible Nutzungen an den betroffenen Kantonsstrassen · Verkehrsflussinitiative SH')
    cv.drawRightString(19.4*cm,1.0*cm,f'Seite {doc.page}')
    cv.setStrokeColor(colors.HexColor('#dddddd')); cv.line(1.6*cm,1.3*cm,19.4*cm,1.3*cm); cv.restoreState()
doc=SimpleDocTemplate('Karten_Infrastruktur_kurze_Abschnitte_SH.pdf', pagesize=A4,
    leftMargin=1.6*cm,rightMargin=1.6*cm,topMargin=1.5*cm,bottomMargin=1.6*cm,
    title='Sensible Nutzungen an den betroffenen Kantonsstrassen SH', author='Verkehrsflussinitiative SH')
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print('PDF written')

#!/usr/bin/env python3
# G12 - Kantonsweite Uebersicht: Verkehr vs Unfallrate aller verkehrsorientierten Abschnitte
import json, math, statistics
from suit import nutzen_cat, CAT_FILL, CAT_STROKE
FONT="Arial, 'Helvetica Neue', system-ui, sans-serif"
INK="#0b0b0b"; INK2="#52514e"; MUTED="#8a8881"; GRID="#e1e0d9"; PLANE="#f5f4f1"; CARD="#ffffff"; BLUE="#2a78d6"
per=[p for p in json.load(open('per_abschnitt.json')) if p['km']>=0.2 and p['fkt']=='VO']
MED=statistics.median([p['unf_km_jahr'] for p in per])
MAXF=max((p['fass_igw'] for p in per), default=1) or 1
W=1200; H=820; el=[]; A=el.append
def esc(t): return t.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
def txt(x,y,t,size=13,col=INK,anchor='start',weight='normal'):
    A(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{col}" text-anchor="{anchor}" font-weight="{weight}">{esc(t)}</text>')
def rect(x,y,w,h,fill,rx=0,stroke='none',sw=1,op=1):
    A(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" rx="{rx}" stroke="{stroke}" stroke-width="{sw}" opacity="{op}"/>')
def line(x1,y1,x2,y2,col=GRID,sw=1,dash='none'):
    A(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{col}" stroke-width="{sw}" stroke-dasharray="{dash}"/>')
def fmt_int(v): return f"{int(round(v)):,}".replace(',', "’")
def fmt1(v): return f"{v:.1f}".replace('.', ',')
def Rr(f): return 6.0+math.sqrt(f/MAXF)*24.0

A(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">')
rect(0,0,W,H,PLANE); rect(0,0,W,8,BLUE)
txt(44,50,'Wo lohnen sich gezielte Massnahmen?',26,INK,'start','bold')
txt(44,77,'Alle verkehrsorientierten Kantonsstrassen-Abschnitte innerorts. Waagrecht die Verkehrsmenge (Treiber der Zeitkosten), senkrecht die Unfallrate.',13.5,INK2)
txt(44,98,'Kreisgrösse = lärmbelastete Fassaden. Farbe = Eignung aus Unfalldichte und Lärm. Waagrechte Zonen je 1 Unfall pro km und Jahr.',12.5,MUTED)

px0=92; px1=W-70; py0=140; py1=H-96
XMAX=25000.0; YMAX=6.0
def X(v): return px0+min(v,XMAX)/XMAX*(px1-px0)
def Y(v): return py1-min(v,YMAX)/YMAX*(py1-py0)
rect(px0,py0,px1-px0,py1-py0,CARD,stroke=GRID,sw=1)
ZCOL=['#f4f7fb','#eaf1f8','#e0eaf4','#d6e2f0','#ccdbec','#c2d4e8']
for b in range(6): rect(px0,Y(b+1),px1-px0,Y(b)-Y(b+1),ZCOL[b])
for i in range(6):
    xv=XMAX*i/5; line(X(xv),py0,X(xv),py1,GRID,1); txt(X(xv),py1+18,fmt_int(xv),10.5,MUTED,'middle')
for yv in range(7):
    line(px0,Y(yv),px1,Y(yv),GRID,1); txt(px0-6,Y(yv)+3,str(yv),10.5,MUTED,'end')
line(px0,Y(MED),px1,Y(MED),'#c0392b',1.6,'6 3')
txt(px1-8,Y(MED)-5,'Median verkehrsorientierte Kt-Strassen SH: '+('%.2f'%MED).replace('.',','),10.5,'#c0392b','end','bold')
txt((px0+px1)/2,py1+40,'Verkehrsleistung  (Fz-km pro Tag)  →',13,INK2,'middle')
A(f'<text x="{px0-54:.1f}" y="{(py0+py1)/2:.1f}" font-size="13" fill="{INK2}" text-anchor="middle" transform="rotate(-90 {px0-54:.1f} {(py0+py1)/2:.1f})">Unfälle pro km und Jahr  →</text>')

pts=[{'x':X(p['fahrleistung']),'y':Y(p['unf_km_jahr']),'r':Rr(p['fass_igw']),'p':p,'cat':nutzen_cat(p),'clx':p['fahrleistung']>XMAX} for p in per]
for _ in range(150):
    moved=False
    for a in range(len(pts)):
        for b in range(a+1,len(pts)):
            dx=pts[b]['x']-pts[a]['x']; dy=pts[b]['y']-pts[a]['y']; d=(dx*dx+dy*dy)**0.5 or 0.01
            mind=pts[a]['r']+pts[b]['r']+2
            if d<mind:
                push=(mind-d)/2; ux,uy=dx/d,dy/d
                pts[a]['x']-=ux*push; pts[a]['y']-=uy*push; pts[b]['x']+=ux*push; pts[b]['y']+=uy*push; moved=True
    for q in pts: q['x']=min(max(q['x'],px0+q['r']),px1-q['r']); q['y']=min(max(q['y'],py0+q['r']),py1-q['r'])
    if not moved: break
for q in sorted(pts,key=lambda z:-z['r']):
    A(f'<circle cx="{q["x"]:.1f}" cy="{q["y"]:.1f}" r="{q["r"]:.1f}" fill="{CAT_FILL[q["cat"]]}" fill-opacity="0.85" stroke="{CAT_STROKE[q["cat"]]}" stroke-width="1.2"/>')
    if q['clx']: A(f'<text x="{px1-4:.1f}" y="{q["y"]-q["r"]-2:.1f}" font-size="12" fill="{CAT_STROKE[q["cat"]]}" text-anchor="end" font-weight="bold">▶</text>')
def sc(q): return q['p']['unf_km_jahr']+q['p']['fass_igw']/60.0
labels=sorted(pts,key=lambda z:-sc(z))[:10]
labels.sort(key=lambda z:z['y']); prevy=-100
for q in labels:
    p=q['p']; ly=q['y']
    if ly<prevy+15: ly=prevy+15
    prevy=ly
    anc='end' if q['x']>px1-160 else 'start'; lxp=q['x']-(q['r']+5) if anc=='end' else q['x']+q['r']+5
    nm=p['name'].replace('strasse','str.'); gem=p['gemeinde'].replace(' (SH)','').replace(' am Rheinfall','')
    txt(lxp,ly+3,f"{nm} ({gem})",10,INK,anc,'bold')

lx=W-250; ly=175
rect(lx-14,ly-22,250,116,CARD,rx=10,stroke=GRID,sw=1)
txt(lx,ly,'Kreisgrösse = Fassaden > IGW',12,INK,'start','bold')
for i,(f,l2) in enumerate([(300,'~300'),(100,'~100'),(20,'~20')]):
    cyl=ly+30+i*24; rr=Rr(f)
    A(f'<circle cx="{lx+22:.1f}" cy="{cyl:.1f}" r="{rr:.1f}" fill="#cbd5e1" fill-opacity="0.7" stroke="#94a3b8" stroke-width="1"/>')
    txt(lx+48,cyl+4,l2+' Fassaden',11.5,INK2,'start')
txt(44,H-40,'Abschnitte oben (hohe Unfallrate) und mit grossen Kreisen (viel Lärm) haben das grösste Nutzenpotenzial; liegen sie zugleich links, sind die Zeitkosten gering.',11.5,MUTED,'start')
txt(44,H-20,'Quellen: geo.sh.ch (Kantonsstrassen/Richtplan, DTV, Lärmbelastungskataster), ASTRA-Unfälle 2011 bis 2025. ▶ = Verkehr über der Skala.',11,MUTED,'start')
A('</svg>')
open('G12_Prioritaeten.svg','w').write('\n'.join(el)); print('G12 rewritten; Abschnitte', len(per), 'Median', round(MED,2))

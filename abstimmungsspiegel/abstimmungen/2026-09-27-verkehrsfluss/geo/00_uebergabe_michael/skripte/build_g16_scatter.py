#!/usr/bin/env python3
# G16 - Nutzen gegen Zeitkosten mit Eignungszonen, kantonsweit (verkehrsorientierte Abschnitte)
import json
from suit import nutzen_cat, CAT_FILL, CAT_STROKE
import knv as K
FONT="Arial, 'Helvetica Neue', system-ui, sans-serif"
INK="#0b0b0b"; INK2="#52514e"; MUTED="#8a8881"; GRID="#e1e0d9"; PLANE="#f5f4f1"; CARD="#ffffff"; BLUE="#2a78d6"
CFILL={'hoch':'#0f7a54','mittel':'#63c39b','gering':'#d2e2da'}; CSTR={'hoch':'#08492f','mittel':'#2f9e75','gering':'#9cbcae'}
ZONE={'hoch':'#e7f4ee','mittel':'#f1f8f4','gering':'#f7f6f2'}

per=[p for p in json.load(open('per_abschnitt.json')) if p['km']>=0.2 and p['fkt']=='VO' and p['fahrleistung']>=2000]
for p in per: p['_k']=K.zeitkosten(p); p['_n']=K.nutzen(p); p['_r']=K.knv(p); p['_cat']=K.knv_cat(p['_r'])
per.sort(key=lambda p:-p['_r'])

W=1200; H=820; el=[]; A=el.append
def esc(t): return t.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
def txt(x,y,t,size=13,col=INK,anchor='start',weight='normal'):
    A(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{col}" text-anchor="{anchor}" font-weight="{weight}">{esc(t)}</text>')
def rect(x,y,w,h,fill,rx=0,stroke='none',sw=1,op=1):
    A(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" rx="{rx}" stroke="{stroke}" stroke-width="{sw}" opacity="{op}"/>')
def line(x1,y1,x2,y2,col=GRID,sw=1,dash='none'):
    A(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{col}" stroke-width="{sw}" stroke-dasharray="{dash}"/>')
def fmt_k(v): return (f"{v/1000:.0f}k" if v>0 else "0")

A(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">')
rect(0,0,W,H,PLANE); rect(0,0,W,8,BLUE)
txt(44,50,'Nutzen gegen Zeitkosten der verkehrsorientierten Abschnitte',25,INK,'start','bold')
txt(44,77,'Alle verkehrsorientierten Kantonsstrassen-Abschnitte innerorts (ab 2000 Fz-km/Tag). Waagrecht die Zeitkosten, senkrecht der monetarisierte Nutzen, je Franken pro Jahr.',13.5,INK2)
txt(44,98,'Die Zonen entsprechen den Terzilen der Verhältnis-Verteilung über alle Abschnitte. Oben links ist der Nutzen je Franken am höchsten. Illustratives Szenario.',12.5,MUTED)

px0=92; px1=W-70; py0=140; py1=H-92
XMAX=max(p['_k'] for p in per)*1.08
YMAX=max(p['_n'] for p in per)*1.2
def X(v): return px0+v/XMAX*(px1-px0)
def Y(v): return py1-min(v,YMAX)/YMAX*(py1-py0)
rect(px0,py0,px1-px0,py1-py0,CARD,stroke=GRID,sw=1)
A(f'<polygon points="{X(0):.1f},{Y(0):.1f} {X(min(XMAX,YMAX/K.ZONE_T2)):.1f},{Y(min(K.ZONE_T2*XMAX,YMAX)):.1f} {px0:.1f},{py0:.1f} {px0:.1f},{Y(YMAX):.1f}" fill="{ZONE["hoch"]}"/>')
A(f'<polygon points="{X(0):.1f},{Y(0):.1f} {X(min(XMAX,YMAX/K.ZONE_T2)):.1f},{Y(min(K.ZONE_T2*XMAX,YMAX)):.1f} {X(min(XMAX,YMAX/K.ZONE_T1)):.1f},{Y(min(K.ZONE_T1*XMAX,YMAX)):.1f}" fill="{ZONE["mittel"]}"/>')
A(f'<polygon points="{X(0):.1f},{Y(0):.1f} {X(min(XMAX,YMAX/K.ZONE_T1)):.1f},{Y(min(K.ZONE_T1*XMAX,YMAX)):.1f} {X(XMAX):.1f},{Y(0):.1f}" fill="{ZONE["gering"]}"/>')
for r,lab in [(K.ZONE_T2,'oberes Terzil'),(K.ZONE_T1,'unteres Terzil')]:
    xe=min(XMAX,YMAX/r); ye=min(r*XMAX,YMAX)
    line(X(0),Y(0),X(xe),Y(ye),'#9db8ab',1.3,'5 3'); txt(X(xe)-4,Y(ye)-6,lab+(' '+('%.2f'%r).replace('.',',')),10.5,'#5f8a75','end','bold')
for i in range(5):
    xv=XMAX*i/4; line(X(xv),py0,X(xv),py1,GRID,1); txt(X(xv),py1+18,fmt_k(xv),10.5,MUTED,'middle')
    yv=YMAX*i/4; line(px0,Y(yv),px1,Y(yv),GRID,1); txt(px0-6,Y(yv)+3,fmt_k(yv),10.5,MUTED,'end')
txt((px0+px1)/2,py1+40,'Zeitkosten  (CHF pro Jahr)  →',13,INK2,'middle')
A(f'<text x="{px0-54:.1f}" y="{(py0+py1)/2:.1f}" font-size="13" fill="{INK2}" text-anchor="middle" transform="rotate(-90 {px0-54:.1f} {(py0+py1)/2:.1f})">Nutzen  (CHF pro Jahr)  →</text>')

pts=[{'x':X(p['_k']),'y':Y(p['_n']),'p':p} for p in per]
for _ in range(150):
    moved=False
    for a in range(len(pts)):
        for b in range(a+1,len(pts)):
            dx=pts[b]['x']-pts[a]['x']; dy=pts[b]['y']-pts[a]['y']; d=(dx*dx+dy*dy)**0.5 or 0.01
            if d<19:
                push=(19-d)/2; ux,uy=dx/d,dy/d
                pts[a]['x']-=ux*push; pts[a]['y']-=uy*push; pts[b]['x']+=ux*push; pts[b]['y']+=uy*push; moved=True
    for q in pts: q['x']=min(max(q['x'],px0+9),px1-9); q['y']=min(max(q['y'],py0+9),py1-9)
    if not moved: break
for q in pts:
    p=q['p']; cat=p['_cat']
    A(f'<circle cx="{q["x"]:.1f}" cy="{q["y"]:.1f}" r="8.5" fill="{CFILL[cat]}" fill-opacity="0.92" stroke="{CSTR[cat]}" stroke-width="1.2"/>')
labels=sorted(pts,key=lambda z:-z['p']['_n'])[:9]
labels.sort(key=lambda z:z['y']); prevy=-100
for q in labels:
    p=q['p']; ly=q['y']
    if ly<prevy+15: ly=prevy+15
    prevy=ly
    lxp=q['x']+12
    nm=p['name'].replace('strasse','str.'); gem=p['gemeinde'].replace(' (SH)','').replace(' am Rheinfall','')
    if lxp>px1-150: lxp=q['x']-12; anc='end'
    else: anc='start'
    line(q['x'],q['y'],lxp+(-2 if anc=='end' else 2),ly,'#c9c7c0',0.8)
    txt(lxp,ly+3,f"{nm} ({gem})",10,INK,anc,'bold')

txt(44,H-40,'Farbe = Terzil-Zone des Verhältnisses (oben links am besten). Beschriftet sind die neun Abschnitte mit dem grössten absoluten Nutzen. Kein Abschnitt erreicht 1,0 im rein monetären Szenario.',11.5,MUTED,'start')
txt(44,H-20,'Quellen: Zeitwert ARE/VSS (SN 641 824); Unfallkosten bfu/Ecoplan; Reisezeit ASTRA FB 1663; Lärm/Wertminderung BAFU/ZKB. Verfahren analog NISTRA (ASTRA).',11,MUTED,'start')
A('</svg>')
open('G16_KostenNutzen_Streuung.svg','w').write('\n'.join(el))
print('G16 scatter written; Punkte', len(per), 'hoch-Zone', sum(1 for p in per if p['_cat']=='hoch'))

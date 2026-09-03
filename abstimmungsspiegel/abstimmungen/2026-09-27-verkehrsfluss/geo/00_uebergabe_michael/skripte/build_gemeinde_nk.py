#!/usr/bin/env python3
# G16 pro Gemeinde: Nutzen je km gegen Zeitkosten je km (Intensitaet), einheitliche Achsen + Terzil-Zonen.
import json, math
from collections import defaultdict
import knv as K
FONT="Arial, 'Helvetica Neue', system-ui, sans-serif"
INK="#0b0b0b"; INK2="#52514e"; MUTED="#8a8881"; GRID="#e1e0d9"; PLANE="#f5f4f1"; CARD="#ffffff"; BLUE="#2a78d6"
CFILL={'hoch':'#0f7a54','mittel':'#63c39b','gering':'#d2e2da'}; CSTR={'hoch':'#08492f','mittel':'#2f9e75','gering':'#9cbcae'}
ZONE={'hoch':'#e7f4ee','mittel':'#f1f8f4','gering':'#f7f6f2'}

per=[p for p in json.load(open('per_abschnitt.json')) if p['km']>=0.2 and p['fkt']=='VO' and p['gemeinde']]
bytown=defaultdict(list)
for p in per: bytown[p['gemeinde']].append(p)
TOWNS=[g for g in bytown if len(bytown[g])>=3]
TOWNS.sort(key=lambda g:-len(bytown[g]))
XMAX=1500000.0; YMAX=230000.0        # einheitliche Intensitaets-Achsen (CHF je km und Jahr)
T1=K.ZONE_T1; T2=K.ZONE_T2
def kk(p): return K.zeitkosten(p)/p['km']
def nk(p): return K.nutzen(p)/p['km']

def esc(t): return t.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
def slug(g): return g.replace(' (SH)','').replace(' am Rheinfall','').replace(' am Rhein','_am_Rhein').replace(' ','_')
def f2(v): return f"{v:.2f}".replace('.',',')
def fk(v): return f"{v/1000:.0f}k"

def build(town):
    rows=sorted(bytown[town], key=lambda p:-K.knv(p))
    n=len(rows); W=1420; H=880; el=[]; A=el.append
    def txt(x,y,t,size=13,col=INK,anchor='start',weight='normal'):
        A(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{col}" text-anchor="{anchor}" font-weight="{weight}">{esc(t)}</text>')
    def rect(x,y,w,h,fill,rx=0,stroke='none',sw=1,op=1):
        A(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" rx="{rx}" stroke="{stroke}" stroke-width="{sw}" opacity="{op}"/>')
    def line(x1,y1,x2,y2,col=GRID,sw=1,dash='none'):
        A(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{col}" stroke-width="{sw}" stroke-dasharray="{dash}"/>')
    A(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">')
    rect(0,0,W,H,PLANE); rect(0,0,W,8,BLUE)
    disp=town.replace(' (SH)','')
    txt(46,50,f'Nutzen und Zeitkosten je Kilometer: {disp}',27,INK,'start','bold')
    txt(46,78,'Intensität je Strassenkilometer: waagrecht die Zeitkosten je km, senkrecht der Nutzen je km, beide in Franken pro km und Jahr.',15,INK2)
    txt(46,99,'Je km gerechnet, dadurch unabhängig von der Gemeindegrösse vergleichbar. Zonen = Terzile des Kosten-Nutzen-Verhältnisses. Illustratives Szenario.',13,MUTED)
    px0=86; px1=708; py0=150; py1=770
    def X(v): return px0+min(v,XMAX)/XMAX*(px1-px0)
    def Y(v): return py1-min(v,YMAX)/YMAX*(py1-py0)
    rect(px0,py0,px1-px0,py1-py0,CARD,stroke=GRID,sw=1)
    A(f'<polygon points="{X(0):.1f},{Y(0):.1f} {X(min(XMAX,YMAX/T2)):.1f},{Y(min(T2*XMAX,YMAX)):.1f} {px0:.1f},{py0:.1f} {px0:.1f},{Y(YMAX):.1f}" fill="{ZONE["hoch"]}"/>')
    A(f'<polygon points="{X(0):.1f},{Y(0):.1f} {X(min(XMAX,YMAX/T2)):.1f},{Y(min(T2*XMAX,YMAX)):.1f} {X(min(XMAX,YMAX/T1)):.1f},{Y(min(T1*XMAX,YMAX)):.1f}" fill="{ZONE["mittel"]}"/>')
    A(f'<polygon points="{X(0):.1f},{Y(0):.1f} {X(min(XMAX,YMAX/T1)):.1f},{Y(min(T1*XMAX,YMAX)):.1f} {X(XMAX):.1f},{Y(0):.1f}" fill="{ZONE["gering"]}"/>')
    for r,lab in [(T2,'oberes Terzil '+f2(T2)),(T1,'unteres Terzil '+f2(T1))]:
        xe=min(XMAX,YMAX/r); ye=min(r*XMAX,YMAX)
        line(X(0),Y(0),X(xe),Y(ye),'#9db8ab',1.2,'5 3'); txt(X(xe)-4,Y(ye)-6,lab,10,'#5f8a75','end','bold')
    for i in range(5):
        xv=XMAX*i/4; line(X(xv),py0,X(xv),py1,GRID,1); txt(X(xv),py1+20,fk(xv),11,MUTED,'middle')
        yv=YMAX*i/4; line(px0,Y(yv),px1,Y(yv),GRID,1); txt(px0-8,Y(yv)+4,fk(yv),11,MUTED,'end')
    txt((px0+px1)/2,py1+42,'Zeitkosten je km  (CHF pro km und Jahr)  →',13,INK2,'middle')
    A(f'<text x="{px0-54:.1f}" y="{(py0+py1)/2:.1f}" font-size="13" fill="{INK2}" text-anchor="middle" transform="rotate(-90 {px0-54:.1f} {(py0+py1)/2:.1f})">Nutzen je km  (CHF pro km und Jahr)  →</text>')
    vp=[{'x':X(kk(p)),'y':Y(nk(p)),'i':i,'cat':K.knv_cat(K.knv(p)),'clx':kk(p)>XMAX} for i,p in enumerate(rows,1)]
    for _ in range(140):
        moved=False
        for a in range(len(vp)):
            for b in range(a+1,len(vp)):
                dx=vp[b]['x']-vp[a]['x']; dy=vp[b]['y']-vp[a]['y']; d=(dx*dx+dy*dy)**0.5 or 0.01
                if d<21:
                    push=(21-d)/2; ux,uy=dx/d,dy/d
                    vp[a]['x']-=ux*push; vp[a]['y']-=uy*push; vp[b]['x']+=ux*push; vp[b]['y']+=uy*push; moved=True
        for q in vp: q['x']=min(max(q['x'],px0+10),px1-10); q['y']=min(max(q['y'],py0+10),py1-10)
        if not moved: break
    for q in vp:
        A(f'<circle cx="{q["x"]:.1f}" cy="{q["y"]:.1f}" r="10" fill="{CFILL[q["cat"]]}" fill-opacity="0.92" stroke="{CSTR[q["cat"]]}" stroke-width="1.3"/>')
        if q['clx']: A(f'<text x="{px1-4:.1f}" y="{q["y"]-13:.1f}" font-size="12" fill="{CSTR[q["cat"]]}" text-anchor="end" font-weight="bold">▶</text>')
        txt(q['x'],q['y']+3.6,str(q['i']),10.5,'#ffffff' if q['cat'] in ('hoch','mittel') else INK,'middle','bold')
    lx=768; lw=W-lx-28; lyt=150
    rect(lx,lyt,lw,py1-lyt,CARD,rx=10,stroke=GRID,sw=1.2)
    txt(lx+18,lyt+25,f'{n} verkehrsorientierte Abschnitte, nach Verhältnis',13,INK,'start','bold')
    line(lx+16,lyt+37,lx+lw-16,lyt+37,GRID,1)
    top=lyt+50; rh=min(58,(py1-lyt-58)/max(n,1)); cvx=lx+lw-16
    for i,p in enumerate(rows,1):
        yy=top+(i-0.5)*rh; cat=K.knv_cat(K.knv(p))
        A(f'<circle cx="{lx+30:.1f}" cy="{yy-6:.1f}" r="12" fill="{CFILL[cat]}" stroke="{CSTR[cat]}" stroke-width="1.3"/>')
        txt(lx+30,yy-2.2,str(i),11,'#ffffff' if cat in ('hoch','mittel') else INK,'middle','bold')
        nm=p['name']; nm=nm[:26]+'…' if len(nm)>27 else nm
        txt(lx+52,yy-3,nm,13,INK,'start','bold')
        txt(lx+52,yy+12,f"Nutzen {fk(nk(p))} / Kosten {fk(kk(p))} je km",10.5,INK2,'start')
        txt(cvx,yy-3,'Verh. '+f2(K.knv(p)),11.5,CSTR[cat] if cat!='gering' else MUTED,'end','bold')
        if i<n: line(lx+16,top+i*rh,lx+lw-16,top+i*rh,'#eeede8',1)
    txt(46,H-40,'Alle Gemeinden mit gleicher Skala. Farbe = Terzil-Zone des Verhältnisses. ▶ = Zeitkosten je km über der Skala. Überlappende Kreise leicht entzerrt.',11.5,MUTED,'start')
    txt(46,H-18,'Quellen: Zeitwert ARE/VSS (SN 641 824); Unfallkosten bfu/Ecoplan; Reisezeit ASTRA FB 1663; Lärm/Wertminderung BAFU/ZKB.',11,MUTED,'start')
    A('</svg>')
    fn=f'G16b_{slug(town)}.svg'; open(fn,'w').write('\n'.join(el)); return fn

names=[build(t) for t in TOWNS]
print('G16-pro-Gemeinde (Intensitaet):', len(names), 'Grafiken')

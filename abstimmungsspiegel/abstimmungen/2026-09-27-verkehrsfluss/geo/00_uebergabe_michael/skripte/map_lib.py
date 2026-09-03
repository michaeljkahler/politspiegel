#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Kartenbasis + Renderer: betroffene (verkehrsorientierte) Kantonsstrassen innerorts je Gemeinde,
# Umkreise 100/300/500 m um Schulen, Kindergaerten, Alters-/Pflegeheime und weitere Sozialeinrichtungen
# (farbcodiert je Gruppe), Hervorhebung betroffener Abschnitte innerhalb 100 m und 300 m. LV95.
import json, math
from collections import defaultdict
from shapely.geometry import shape, Point, box
from shapely.ops import unary_union
from shapely.strtree import STRtree

VO_TYP={'Kanton.ueberregionale Strasse','Kanton.regionale Strasse'}
SO_TYP={'Kanton.ueber lokale Strasse'}; NAT_TYP={'Kanton.Nationalstrasse'}

def load_base():
    roads=json.load(open('roads_fkt.geojson'))['features']
    bg=json.load(open('baugebiet.geojson'))['features']
    inner_polys=[(shape(f['geometry']), f['properties'].get('gemeinde')) for f in bg if f['properties'].get('baugebiet')=='ja']
    inner_by_gem=defaultdict(list)
    for geom,gem in inner_polys:
        if gem: inner_by_gem[gem].append(geom)
    inner_union_by_gem={g:unary_union(v) for g,v in inner_by_gem.items()}
    inner_all=unary_union([g for g,_ in inner_polys])
    vo=[shape(f['geometry']) for f in roads if f['properties'].get('typ') in VO_TYP]
    context=[shape(f['geometry']) for f in roads if f['properties'].get('typ') in (SO_TYP|NAT_TYP)]
    vo_pieces=defaultdict(list)
    gems=list(inner_union_by_gem.keys()); polys=[inner_union_by_gem[g] for g in gems]
    tree=STRtree(polys)
    for ln in vo:
        for idx in tree.query(ln):
            gem=gems[idx]; inter=ln.intersection(polys[idx])
            if inter.is_empty: continue
            if inter.geom_type=='LineString': vo_pieces[gem].append(inter)
            elif inter.geom_type=='MultiLineString': vo_pieces[gem].extend(list(inter.geoms))
    return dict(vo_pieces=vo_pieces, context=context, vo_all=vo,
               inner_union_by_gem=inner_union_by_gem, inner_all=inner_all)

FONT="Arial, 'Helvetica Neue', system-ui, sans-serif"
INK="#141414"; INK2="#555"; MUTED="#8a8881"
CAT_ORDER=['schule','kindergarten','altersheim','sozial']
CAT={'schule':{'label':'Schule','col':'#d95f0e'},
     'kindergarten':{'label':'Kindergarten','col':'#1b9e77'},
     'altersheim':{'label':'Alters-/Pflegeheim','col':'#6a51a3'},
     'sozial':{'label':'Weitere Sozialeinrichtung','col':'#2166ac'}}
ROAD_VO="#141414"; ROAD_CTX="#cbc9c2"; INNER_FILL="#f2f1ec"; INNER_STROKE="#e4e2da"
CAND100="#e6194B"; CAND300="#f4a6ae"
RADII=[500,300,100]; FILLOP={500:0.05,300:0.09,100:0.17}

def _bounds(geoms):
    xs0=ys0=1e18; xs1=ys1=-1e18
    for g in geoms:
        a,b,c,d=g.bounds; xs0=min(xs0,a); ys0=min(ys0,b); xs1=max(xs1,c); ys1=max(ys1,d)
    return xs0,ys0,xs1,ys1

def compute_stats(base, gem, facs):
    vo=unary_union(base['vo_pieces'].get(gem,[])) if base['vo_pieces'].get(gem) else None
    if vo is None or vo.is_empty: return None
    s={'betroffen':vo.length}
    for grp in ['alle']+CAT_ORDER:
        pts=[Point(f['x'],f['y']) for f in facs if (grp=='alle' or f['cat']==grp)]
        for r in (100,300,500):
            s[f'{grp}_{r}']= vo.intersection(unary_union([p.buffer(r) for p in pts])).length if pts else 0.0
    return s

def render_gemeinde(gem, base, facilities, out=None, W=1500, pad=46, header=74, footer=214):
    inner=base['inner_union_by_gem'].get(gem); vo=base['vo_pieces'].get(gem,[])
    if inner is None: raise ValueError('unbekannte Gemeinde '+gem)
    ref_roads=unary_union(vo) if vo else inner
    facs=[f for f in facilities if Point(f['x'],f['y']).distance(ref_roads)<=560]
    parts=list(vo)+[Point(f['x'],f['y']).buffer(320) for f in facs]
    if not parts: parts=[inner]
    minx,miny,maxx,maxy=_bounds(parts)
    mgx=max(130,(maxx-minx)*0.05); mgy=max(130,(maxy-miny)*0.05)
    minx-=mgx; maxx+=mgx; miny-=mgy; maxy+=mgy
    mw=maxx-minx; mh=maxy-miny; scale=(W-2*pad)/mw; mapH=mh*scale; H=int(header+mapH+footer)
    def X(x): return pad+(x-minx)*scale
    def Y(y): return header+mapH-(y-miny)*scale
    el=[]; A=el.append
    def esc(t): return (t or '').replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
    def path(geom,stroke,sw,dash='none',op=1.0,cap='round'):
        for g in (geom.geoms if geom.geom_type.startswith('Multi') else [geom]):
            if g.geom_type!='LineString' or g.is_empty: continue
            d='M'+' L'.join(f'{X(x):.1f},{Y(y):.1f}' for x,y in g.coords)
            A(f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="{cap}" stroke-linejoin="round" stroke-dasharray="{dash}" opacity="{op}"/>')
    def poly(geom,fill,stroke,sw,op=1.0):
        for g in (geom.geoms if geom.geom_type.startswith('Multi') else [geom]):
            if g.geom_type!='Polygon' or g.is_empty: continue
            ext='M'+' L'.join(f'{X(x):.1f},{Y(y):.1f}' for x,y in g.exterior.coords)+' Z'
            hs=''.join(' M'+' L'.join(f'{X(x):.1f},{Y(y):.1f}' for x,y in r.coords)+' Z' for r in g.interiors)
            A(f'<path d="{ext}{hs}" fill="{fill}" fill-rule="evenodd" stroke="{stroke}" stroke-width="{sw}" opacity="{op}"/>')
    def txt(x,y,t,size=13,col=INK,anchor='start',weight='normal',op=1.0):
        A(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{col}" text-anchor="{anchor}" font-weight="{weight}" opacity="{op}">{esc(t)}</text>')
    def marker(cat,x,y,r=5.4):
        col=CAT[cat]['col']
        if cat=='schule': A(f'<rect x="{x-r:.1f}" y="{y-r:.1f}" width="{2*r:.1f}" height="{2*r:.1f}" fill="{col}" stroke="#fff" stroke-width="1.3"/>')
        elif cat=='kindergarten': A(f'<polygon points="{x:.1f},{y-r-0.6:.1f} {x-r-0.4:.1f},{y+r-0.6:.1f} {x+r+0.4:.1f},{y+r-0.6:.1f}" fill="{col}" stroke="#fff" stroke-width="1.3"/>')
        elif cat=='altersheim': A(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{col}" stroke="#fff" stroke-width="1.3"/>')
        else: A(f'<polygon points="{x:.1f},{y-r-1:.1f} {x+r+1:.1f},{y:.1f} {x:.1f},{y+r+1:.1f} {x-r-1:.1f},{y:.1f}" fill="{col}" stroke="#fff" stroke-width="1.3"/>')

    A(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">')
    A(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>')
    A(f'<clipPath id="mp"><rect x="0" y="{header}" width="{W}" height="{mapH:.1f}"/></clipPath>')
    A(f'<g clip-path="url(#mp)">')
    poly(inner, INNER_FILL, INNER_STROKE, 1.0)
    view=box(minx,miny,maxx,maxy)
    for g in base['context']:
        if g.intersects(view): path(g, ROAD_CTX, 1.5)
    facpts={c:[Point(f['x'],f['y']) for f in facs if f['cat']==c] for c in CAT_ORDER}
    for r in RADII:
        for c in CAT_ORDER:
            if not facpts[c]: continue
            col=CAT[c]['col']; u=unary_union([p.buffer(r) for p in facpts[c]])
            poly(u, col,'none',0,op=FILLOP[r])
            if r==100: path(u.boundary, col, 1.1, op=0.5)
    allpts=[p for c in CAT_ORDER for p in facpts[c]]
    if allpts:
        u3=unary_union([p.buffer(300) for p in allpts]); u1=unary_union([p.buffer(100) for p in allpts])
        for g in vo:
            hi=g.intersection(u3)
            if not hi.is_empty: path(hi, CAND300, 5.5, op=0.5)
        for g in vo:
            hi=g.intersection(u1)
            if not hi.is_empty: path(hi, CAND100, 9.0, op=0.95)
    for g in vo: path(g, ROAD_VO, 3.0)
    for f in facs: marker(f['cat'], X(f['x']), Y(f['y']))
    A('</g>')
    disp=gem.replace(' (SH)','')
    txt(pad, 34, f'{disp}: betroffene Strassen und Umkreise sensibler Nutzungen', 23, INK,'start','bold')
    txt(pad, 56, 'Verkehrsorientierte Kantonsstrassen innerorts mit 100 m, 300 m und 500 m Umkreis um Schulen, Kindergärten, Alters-/Pflegeheime und weitere Sozialeinrichtungen.', 12.5, INK2)
    fy=header+mapH
    A(f'<line x1="0" y1="{fy:.1f}" x2="{W}" y2="{fy:.1f}" stroke="#e4e2da" stroke-width="1"/>')
    yA=fy+24; x=pad
    def leg_line(x,y,col,sw,label,w2=34,extra=None):
        A(f'<line x1="{x}" y1="{y-4:.1f}" x2="{x+w2}" y2="{y-4:.1f}" stroke="{col}" stroke-width="{sw}"/>')
        if extra: A(f'<line x1="{x}" y1="{y-4:.1f}" x2="{x+w2}" y2="{y-4:.1f}" stroke="{extra}" stroke-width="3"/>')
        txt(x+w2+8, y, label, 12, INK); return x+w2+8+len(label)*6.7+26
    x=leg_line(x,yA,ROAD_VO,3,'Betroffene Kantonsstrasse')
    x=leg_line(x,yA,CAND100,7,'Kandidat ≤ 100 m',34,ROAD_VO)
    x=leg_line(x,yA,CAND300,7,'Kandidat ≤ 300 m',34,ROAD_VO)
    x=leg_line(x,yA,ROAD_CTX,2.2,'übrige Kantonsstrasse')
    yB=fy+50; x=pad
    for c in CAT_ORDER:
        marker(c,x+8,yB-4); txt(x+22,yB,CAT[c]['label'],12,INK); x+=22+len(CAT[c]['label'])*6.9+26
    yC=fy+76; x=pad
    for i,r in enumerate([100,300,500]):
        A(f'<rect x="{x}" y="{yC-11:.1f}" width="15" height="12" fill="#6a51a3" opacity="{FILLOP[r]+0.02}"/>'); x+=18
    txt(x+4,yC,'Umkreis 100 / 300 / 500 m (zunehmend blasser)',12,INK)
    s=compute_stats(base, gem, facilities); yD=fy+102
    if s:
        def km(v): return ('%.2f'%(v/1000)).replace('.',',')
        def pc(v): return ('%.0f'%(100*v/s['betroffen'])) if s['betroffen'] else '0'
        txt(pad,yD,f"Betroffen {km(s['betroffen'])} km  ·  ≤ 100 m: {km(s['alle_100'])} km ({pc(s['alle_100'])}%)  ·  ≤ 300 m: {km(s['alle_300'])} km ({pc(s['alle_300'])}%)  ·  ≤ 500 m: {km(s['alle_500'])} km ({pc(s['alle_500'])}%)",12.5,INK,'start','bold')
    sb=500*scale; bx=pad; by=H-16
    A(f'<line x1="{bx:.1f}" y1="{by:.1f}" x2="{bx+sb:.1f}" y2="{by:.1f}" stroke="{INK}" stroke-width="2"/>')
    A(f'<line x1="{bx:.1f}" y1="{by-4:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="{INK}" stroke-width="2"/>')
    A(f'<line x1="{bx+sb:.1f}" y1="{by-4:.1f}" x2="{bx+sb:.1f}" y2="{by:.1f}" stroke="{INK}" stroke-width="2"/>')
    txt(bx+sb+8,by,'500 m',11,INK2,'start')
    txt(W-pad,by,'Strassen: geo.sh.ch (Richtplan/Baugebiet) · Infrastruktur: Nutzer-GeoPackage (OSM/kantonal) · LV95',9.5,MUTED,'end')
    A('</svg>')
    svg='\n'.join(el)
    if out: open(out,'w').write(svg)
    return svg, W, H, s

if __name__=='__main__':
    base=load_base(); facs=json.load(open('facilities.json'))
    render_gemeinde('Schaffhausen', base, facs, out='map_test_SH.svg'); print('test ok')

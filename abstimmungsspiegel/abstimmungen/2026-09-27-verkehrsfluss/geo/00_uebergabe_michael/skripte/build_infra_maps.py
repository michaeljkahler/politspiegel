#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from collections import defaultdict
import map_lib as M
from shapely.geometry import shape, Point
from shapely.ops import unary_union
from shapely.strtree import STRtree
import cairosvg

def slug(g): return g.replace(' (SH)','').replace(' am Rheinfall','').replace(' am Rhein','_am_Rhein').replace(' ','_')

base=M.load_base()
facs=json.load(open('facilities.json'))
GEMS=sorted(base['vo_pieces'], key=lambda g:-sum(x.length for x in base['vo_pieces'][g]))
allpts=[Point(f['x'],f['y']) for f in facs]
U={r:unary_union([p.buffer(r) for p in allpts]) for r in (100,300)}

nb=json.load(open('netzbelastung.geojson'))['features']
nb_lines=[shape(f['geometry']) for f in nb]; nb_names=[f['properties'].get('strassenname') for f in nb]
nbtree=STRtree(nb_lines)

def name_candidates(gem, radius):
    vo=unary_union(base['vo_pieces'][gem]); cand=vo.intersection(U[radius])
    if cand.is_empty: return [], 0.0, None
    segs=list(cand.geoms) if cand.geom_type.startswith('Multi') else [cand]
    byname=defaultdict(float)
    for s in segs:
        if s.geom_type!='LineString' or s.length<1: continue
        mid=s.interpolate(0.5, normalized=True); best=None; bd=1e9
        for i in nbtree.query(mid.buffer(45)):
            d=nb_lines[i].distance(mid)
            if d<bd: bd=d; best=nb_names[i]
        nm=best if (best and bd<=45 and best.strip()) else 'unbenannt'
        byname[nm]+=s.length
    return sorted(byname.items(), key=lambda x:-x[1]), cand.length, cand

results=[]; cand_features=[]
for gem in GEMS:
    svg,W,H,s=M.render_gemeinde(gem, base, facs, out=f'karte_{slug(gem)}.svg')
    cairosvg.svg2png(url=f'karte_{slug(gem)}.svg', write_to=f'karte_{slug(gem)}.png', output_width=1700)
    n100,l100,g100=name_candidates(gem,100); n300,l300,g300=name_candidates(gem,300)
    for radius,cg in [(100,g100),(300,g300)]:
        if cg is None or cg.is_empty: continue
        for g in (cg.geoms if cg.geom_type.startswith('Multi') else [cg]):
            if g.geom_type=='LineString':
                cand_features.append({'type':'Feature','properties':{'gemeinde':gem,'radius_m':radius,'typ':f'kandidat_<= {radius}m'},
                    'geometry':{'type':'LineString','coordinates':[[round(x,2),round(y,2)] for x,y in g.coords]}})
    results.append({'gemeinde':gem,'slug':slug(gem),'stats':s,
                    'cand100_names':n100[:6],'cand100_len':l100,'cand300_names':n300[:6],'cand300_len':l300})
    print(f'{gem:24s} betr {s["betroffen"]/1000:5.2f} | <=100 {100*s["alle_100"]/s["betroffen"]:4.0f}%  <=300 {100*s["alle_300"]/s["betroffen"]:4.0f}%')

json.dump(results, open('infra_results.json','w'), ensure_ascii=False)
json.dump({'type':'FeatureCollection','name':'kandidaten_kurze_abschnitte',
           'crs':{'type':'name','properties':{'name':'urn:ogc:def:crs:EPSG::2056'}},
           'features':cand_features}, open('kandidaten_kurze_abschnitte.geojson','w'), ensure_ascii=False)
print('\nMaps', len(GEMS), '| candidate features', len(cand_features))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Erzeugt facilities.json (4 Gruppen) aus dem Infrastruktur-GeoPackage v2.
# Jeder Eintrag: {cat, name, gem, x, y, unterkat}; cat in {schule, kindergarten, altersheim, sozial}; LV95.
import fiona, json
from shapely.geometry import shape
GPKG='infra_SH_v2.gpkg'
CATMAP={'kindergaerten':'kindergarten','schulen':'schule','pflegeheime':'altersheim','unklar_sozialeinrichtungen':'sozial'}
facs=[]
for lyr,cat in CATMAP.items():
    with fiona.open(GPKG,layer=lyr) as src:
        for ft in src:
            g=shape(ft['geometry']); p=dict(ft['properties'])
            facs.append({'cat':cat,'name':(p.get('name') or p.get('bezeichnung') or '').strip(),
                         'gem':p.get('gemeinde'),'x':g.x,'y':g.y,'unterkat':p.get('unterkategorie')})
json.dump(facs, open('facilities.json','w'), ensure_ascii=False)
from collections import Counter
print('facilities.json:', len(facs), dict(Counter(f['cat'] for f in facs)))

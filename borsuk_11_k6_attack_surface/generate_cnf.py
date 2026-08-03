#!/usr/bin/env python3
"""Regenerate the symmetry-broken DIMACS instance and variable map."""
from __future__ import annotations
import itertools,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
N=11;K=6;BASE=(1<<6)-1
CENTERS=[0,63,455,748,858,945,1241,1396,1450,1635,1686,1805]
vs=[x for x in range(1<<N) if x.bit_count()%2==0 and x.bit_count()<=K and (x^BASE).bit_count()<=K]
s=set(vs);masks=[sum(1<<i for i in c) for c in itertools.combinations(range(N),K)]
edges=sorted((a,a^m) for a in vs for m in masks if a<(a^m) and (a^m) in s)
fixed={v:c for c,v in enumerate(CENTERS)}
allowed={v:[c for c,z in enumerate(CENTERS) if (v^z).bit_count()!=6] for v in vs if v not in fixed}
var={};rev=[]
for v in vs:
    if v in fixed:continue
    for c in allowed[v]:var[(v,c)]=len(rev)+1;rev.append((v,c))
clauses=[]
for v,cs in allowed.items():
    ids=[var[(v,c)] for c in cs];clauses.append(ids)
    clauses.extend([-ids[i],-ids[j]] for i in range(len(ids)) for j in range(i+1,len(ids)))
for a,b in edges:
    if a in fixed or b in fixed:continue
    clauses.extend([-var[(a,c)],-var[(b,c)]] for c in sorted(set(allowed[a])&set(allowed[b])))
with (ROOT/"k6_trim_12color.cnf").open("w") as f:
    f.write("c Borsuk n=11 k=6 canonical trim graph 12-colorability\n")
    f.write("c Fixed Hadamard 12-clique removes all color permutation symmetry.\n")
    f.write(f"p cnf {len(rev)} {len(clauses)}\n")
    for q in clauses:f.write(" ".join(map(str,q))+" 0\n")
mapping={"schema":"dimacs-variable-map-v1","variables":{str(i+1):{"vertex":v,"color":c} for i,(v,c) in enumerate(rev)},"fixed_colors":{str(v):c for v,c in fixed.items()},"allowed_color_counts":{"6":560,"9":120}}
(ROOT/"variable_map.json").write_text(json.dumps(mapping,indent=2,sort_keys=True)+"\n")
print(len(rev),len(clauses))

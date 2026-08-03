#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import itertools
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
N=11; K=6; BASE=(1<<6)-1
CENTERS=[0,63,455,748,858,945,1241,1396,1450,1635,1686,1805]

def vertices():
    return [x for x in range(1<<N)
            if x.bit_count()%2==0
            and x.bit_count()<=K
            and (x^BASE).bit_count()<=K]

def canonical_edges(vs):
    s=set(vs)
    masks=[sum(1<<i for i in c) for c in itertools.combinations(range(N),K)]
    out=[]
    for a in vs:
        for m in masks:
            b=a^m
            if b in s and a<b: out.append((a,b))
    return sorted(out)

def digest_edges(edges):
    return hashlib.sha256("".join(f"{a},{b}\n" for a,b in edges).encode()).hexdigest()

def main():
    report=json.loads((ROOT/"report.json").read_text())
    partial=json.loads((ROOT/"partial_witness.json").read_text())
    vs=vertices(); edges=canonical_edges(vs); eset=set(edges)

    assert len(vs)==692
    assert len(edges)==104606
    assert digest_edges(edges)==report["trim_graph"]["sha256"]
    assert all(c in set(vs) for c in CENTERS)
    assert all((a^b).bit_count()==6
               for i,a in enumerate(CENTERS) for b in CENTERS[i+1:])

    supplied_edges=[]
    for line in (ROOT/"trim_graph_edges.csv").read_text().splitlines():
        a,b=map(int,line.split(",")); supplied_edges.append((a,b))
    assert supplied_edges==edges

    assigned={int(v):c for v,c in partial["assigned"].items()}
    uncolored=partial["uncolored"]
    assert len(assigned)==572 and len(uncolored)==120
    assert set(assigned).isdisjoint(uncolored)
    assert set(assigned)|set(uncolored)==set(vs)
    assert all(isinstance(c,int) and 0<=c<12 for c in assigned.values())
    assert not any(a in assigned and b in assigned and assigned[a]==assigned[b]
                   for a,b in edges)

    classes={c:[] for c in range(12)}
    for v,c in assigned.items(): classes[c].append(v)
    for v in uncolored:
        for c in range(12):
            assert any((v^u).bit_count()==6 for u in classes[c]), (v,c)

    uset=set(uncolored)
    core=[(a,b) for a,b in edges if a in uset and b in uset]
    assert len(core)==3015
    assert digest_edges(core)==report["core"]["sha256"]
    deg={v:0 for v in uncolored}
    for a,b in core: deg[a]+=1;deg[b]+=1
    assert sorted(deg.values()).count(48)==30
    assert sorted(deg.values()).count(51)==90

    # Verify fixed-clique list reduction.
    allowed={}
    for v in vs:
        if v in CENTERS: continue
        allowed[v]=[c for c,center in enumerate(CENTERS)
                    if (v^center).bit_count()!=6]
    counts={}
    for cs in allowed.values(): counts[len(cs)]=counts.get(len(cs),0)+1
    assert counts=={6:560,9:120}
    assert sum(map(len,allowed.values()))==4440

    # Parse DIMACS counts and every literal range.
    cnf=ROOT/"k6_trim_12color.cnf"
    nvars=nclauses=None; actual=0
    for line in cnf.read_text().splitlines():
        if not line or line.startswith("c"): continue
        if line.startswith("p "):
            _,kind,nvars,nclauses=line.split()
            assert kind=="cnf";nvars=int(nvars);nclauses=int(nclauses)
        else:
            lits=list(map(int,line.split()))
            assert lits[-1]==0 and all(1<=abs(x)<=4440 for x in lits[:-1])
            actual+=1
    assert (nvars,nclauses,actual)==(4440,362120,362120)
    digest=hashlib.sha256(cnf.read_bytes()).hexdigest()
    assert digest==report["symmetry_broken_sat"]["cnf_sha256"]

    print(json.dumps({
        "status":"PASS",
        "trim_vertices":len(vs),
        "trim_edges":len(edges),
        "hadamard_clique":len(CENTERS),
        "sat_variables":nvars,
        "sat_clauses":actual,
        "partial_assigned":len(assigned),
        "core_vertices":len(uncolored),
        "core_edges":len(core),
        "graph_sha256":digest_edges(edges),
        "cnf_sha256":digest
    },indent=2))

if __name__=="__main__":
    main()

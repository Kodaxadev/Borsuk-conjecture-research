#!/usr/bin/env python3
"""Verify a SAT solver model for k6_trim_12color.cnf.

Accepts DIMACS solver output containing `v` lines or bare integer lines.
UNSAT text is not accepted as a proof.
"""
from __future__ import annotations
import itertools,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
CENTERS=[0,63,455,748,858,945,1241,1396,1450,1635,1686,1805]
N=11;K=6;BASE=(1<<6)-1

def main():
    if len(sys.argv)!=2:
        raise SystemExit("usage: python verify_solution.py solver_output.txt")
    text=Path(sys.argv[1]).read_text(errors="replace")
    if "UNSAT" in text.upper():
        raise SystemExit("UNSAT text is not a certificate. Supply and independently verify DRAT/LRAT.")
    positives=set()
    for line in text.splitlines():
        s=line.strip()
        if not s or s[0] in "csp": 
            if s.startswith("v "): s=s[2:]
            else: continue
        for tok in s.split():
            try:x=int(tok)
            except ValueError:continue
            if x>0:positives.add(x)
    mapping=json.loads((ROOT/"variable_map.json").read_text())
    vars={int(k):(v["vertex"],v["color"]) for k,v in mapping["variables"].items()}
    colors={v:c for c,v in enumerate(CENTERS)}
    per_vertex={}
    for x in positives:
        if x not in vars: continue
        v,c=vars[x];per_vertex.setdefault(v,[]).append(c)
    vs=[x for x in range(1<<N) if x.bit_count()%2==0 and x.bit_count()<=K and (x^BASE).bit_count()<=K]
    for v in vs:
        if v in colors:continue
        cs=per_vertex.get(v,[])
        if len(cs)!=1:raise SystemExit(f"vertex {v} has {len(cs)} selected colors: {cs}")
        colors[v]=cs[0]
    assert len(colors)==692
    bad=[]
    for i,a in enumerate(vs):
        for b in vs[i+1:]:
            if (a^b).bit_count()==K and colors[a]==colors[b]:
                bad.append((a,b,colors[a]))
                if len(bad)>=10:break
        if len(bad)>=10:break
    if bad:raise SystemExit(f"FAIL monochromatic edges: {bad}")
    out=ROOT/"verified_coloring.json"
    out.write_text(json.dumps({str(v):colors[v] for v in sorted(colors)},indent=2)+"\n")
    print(f"PASS: verified 12-coloring of all {len(vs)} trim vertices; wrote {out.name}")

if __name__=="__main__":main()

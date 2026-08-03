#!/usr/bin/env python3
"""Independent verifier for the candidate proof of Borsuk(11,4).

Uses only the Python standard library. It reconstructs the three canonical
even-parity cover graphs, checks supplied coloring witnesses in two independent
ways, enumerates all maximal cliques of J(11,4), and writes report.json.
"""
from __future__ import annotations
from collections import Counter
from itertools import combinations
from pathlib import Path
import hashlib
import json

N = 11
K = 4

def encode(items):
    return sum(1 << i for i in items)

def bitstring(x):
    return format(x, f"0{N}b")

def hamming(a,b):
    return (a ^ b).bit_count()

def even_ball_2():
    return [x for x in range(1 << N) if x.bit_count() in (0,2)]

def triangle_cover():
    # Pairwise Hamming-distance-4 triangle: 0, A, B.
    centers = [0, encode({0,1,2,3}), encode({0,1,4,5})]
    return [
        x for x in range(1 << N)
        if x.bit_count() % 2 == 0
        and all(hamming(x,c) <= K for c in centers)
    ]

def star_cover():
    common={0,1,2}
    weight4=[encode(common | {j}) for j in range(3,N)]
    return sorted(set(even_ball_2()) | set(weight4))

def top_cover():
    weight4=[encode(s) for s in combinations(range(5),4)]
    return sorted(set(even_ball_2()) | set(weight4))

def canonical_edges(vertices):
    vertices=sorted(vertices)
    return [
        (u,v)
        for i,u in enumerate(vertices)
        for v in vertices[i+1:]
        if hamming(u,v)==K
    ]

def graph_hash(edges):
    payload="".join(
        f"{bitstring(u)} {bitstring(v)}\n" for u,v in edges
    ).encode("ascii")
    return hashlib.sha256(payload).hexdigest()

def verify_coloring_by_edges(vertices, colors):
    assert set(vertices)==set(colors), "Witness vertex set differs from reconstructed graph"
    for u,v in canonical_edges(vertices):
        assert colors[u] != colors[v], (
            f"Monochromatic diameter edge {bitstring(u)}--{bitstring(v)}"
        )

def verify_coloring_by_classes(vertices, colors):
    classes={}
    for v in vertices:
        classes.setdefault(colors[v],[]).append(v)
    for color,vs in classes.items():
        for i,u in enumerate(vs):
            for v in vs[i+1:]:
                assert hamming(u,v) != K, (
                    f"Color class {color} contains a distance-{K} pair"
                )
    return {str(c):len(vs) for c,vs in sorted(classes.items())}

def johnson_maximal_cliques():
    """Enumerate maximal cliques of J(11,4) via Bron--Kerbosch."""
    subsets=[frozenset(s) for s in combinations(range(N),4)]
    index={s:i for i,s in enumerate(subsets)}
    adjacency=[set() for _ in subsets]
    universe=set(range(N))
    for i,A in enumerate(subsets):
        for a in A:
            for b in universe-A:
                B=frozenset((set(A)-{a})|{b})
                adjacency[i].add(index[B])

    maximal=[]
    def bron_kerbosch(R,P,X):
        if not P and not X:
            maximal.append(tuple(sorted(R)))
            return
        pivot=max(P|X,key=lambda u:len(P & adjacency[u])) if P or X else None
        candidates=list(P - adjacency[pivot]) if pivot is not None else list(P)
        for v in candidates:
            bron_kerbosch(R|{v}, P & adjacency[v], X & adjacency[v])
            P.remove(v)
            X.add(v)

    bron_kerbosch(set(),set(range(len(subsets))),set())

    star=top=0
    failures=[]
    for clique in maximal:
        family=[set(subsets[i]) for i in clique]
        common=set.intersection(*family)
        union=set.union(*family)
        if len(common)==3:
            star += 1
        elif len(union)==5:
            top += 1
        else:
            failures.append({
                "members":[sorted(f) for f in family],
                "common":sorted(common),
                "union":sorted(union),
            })

    sizes=Counter(map(len,maximal))
    assert not failures, "A maximal Johnson clique was neither a star nor a top"
    assert star == 165, f"Expected C(11,3)=165 stars, found {star}"
    assert top == 462, f"Expected C(11,5)=462 tops, found {top}"
    assert sizes == Counter({8:165,5:462}), f"Unexpected clique sizes: {sizes}"
    return {
        "vertices":len(subsets),
        "edges":sum(map(len,adjacency))//2,
        "maximal_cliques":len(maximal),
        "star_cliques":star,
        "top_cliques":top,
        "size_distribution":{str(k):v for k,v in sorted(sizes.items())},
    }

def main():
    witness=json.loads(Path(__file__).with_name("witness.json").read_text())
    reconstructed={
        "triangle_trim_even":triangle_cover(),
        "star_plus_even_ball":star_cover(),
        "top_plus_even_ball":top_cover(),
    }
    report={
        "n":N,
        "diameter":K,
        "status":"all checks passed",
        "covers":{},
        "johnson_J_11_4":johnson_maximal_cliques(),
    }
    for name,vertices in reconstructed.items():
        raw=witness["colorings"][name]
        colors={int(v,2):int(c) for v,c in raw.items()}
        verify_coloring_by_edges(vertices,colors)
        class_sizes=verify_coloring_by_classes(vertices,colors)
        edges=canonical_edges(vertices)
        count=len(set(colors.values()))
        assert count <= 12, f"{name} uses {count} colors"
        report["covers"][name]={
            "vertices":len(vertices),
            "edges":len(edges),
            "colors":count,
            "color_class_sizes":class_sizes,
            "edge_list_sha256":graph_hash(edges),
            "verified_by":["edge scan","color-class diameter scan"],
        }
    out=Path(__file__).with_name("report.json")
    out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2,sort_keys=True))

if __name__=="__main__":
    main()

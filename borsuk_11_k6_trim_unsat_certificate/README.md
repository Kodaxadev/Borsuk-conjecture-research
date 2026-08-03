# Certified UNSAT result for the universal n=11, k=6 trim cover

## Exact result

Let A be a fixed cube vertex at Hamming distance 6 from 0, and let T be the even-parity vertices x in {0,1}^11 satisfying d(x,0) <= 6 and d(x,A) <= 6. The exact-distance-6 graph induced by T has 692 vertices and 104,606 edges.

The supplied CNF asks whether this graph has a proper 12-coloring after fixing a known 12-clique to the twelve colors. The CNF is UNSAT.

## What this does not prove

This does not disprove or settle the n=11, diameter-6 Boolean Borsuk case. T itself contains pairs farther than 6 apart, so it is a universal cover of possible normalized components rather than a legal diameter-6 set. The result proves that the one-base cover is too coarse. The next proof layer must branch on additional vertices or equivalent diameter-compatibility constraints.

## Certificate chain

1. `k6_trim_12color.cnf`: exact graph-coloring instance.
2. `minicdcl_drat.cpp`: self-contained CDCL solver that emits clause additions and deletions.
3. `k6_trim_12color.drat.gz`: proof trace; decompress before checking.
4. `drup_check.cpp`: separately implemented forward DRUP/RUP checker.
5. `k6_drup_check.out`: successful verification summary.

The checker validated 234,857 clause additions, processed 219,998 deletion steps, and verified the final empty clause. It also rejected a deliberately corrupted first lemma and a trace missing its empty clause.

## Reproduction

```sh
g++ -O3 -std=c++17 minicdcl_drat.cpp -o minicdcl_drat
g++ -O3 -std=c++17 drup_check.cpp -o drup_check
./minicdcl_drat k6_trim_12color.cnf 300 model.txt proof.drat
./drup_check k6_trim_12color.cnf proof.drat
```

The solver uses exit code 20 for UNSAT, following common SAT-solver convention.

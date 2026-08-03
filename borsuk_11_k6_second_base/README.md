# Borsuk 11, diameter 6 — exact second-base reduction

## Status

This package does **not yet settle** the diameter-6 case. It replaces the
certified-UNSAT one-base trim by three exact, theorem-relevant branch graphs.
Proving that all three graphs are 12-colorable would prove the
11-dimensional Boolean Borsuk statement for diameter 6.

## Reduction

Let `C` be a connected component of the exact-distance-6 graph of a set
`S subset {0,1}^11` having Hamming diameter at most 6.

Translate one edge of `C` to

- `0`, and
- `A = {0,1,2,3,4,5}`, encoded as `63`.

Every component vertex then has even weight, distance at most 6 from `0`,
and distance at most 6 from `A`. This is the 692-vertex one-base trim from
the earlier attack package.

If `C` has only one or two vertices, it is trivially 12-colorable. Otherwise,
connectedness guarantees an edge from `{0,A}` to a third vertex. Swapping `0`
and `A` by XOR with `A` when necessary lets us choose a third vertex `B` with
`d(0,B)=6`.

Now `A` and `B` are both 6-subsets. Since `d(A,B)<=6`, their intersection has
size at least 3. The value 6 gives `B=A`, so the only possibilities are

- `|A cap B|=3`, equivalently `d(A,B)=6`;
- `|A cap B|=4`, equivalently `d(A,B)=4`;
- `|A cap B|=5`, equivalently `d(A,B)=2`.

The pointwise stabilizer of `0` and `A` is `S_6 x S_5`, and it is transitive
on each of these three classes. Therefore only three representative branch
sets must be considered:

`U_B = {x : wt(x) even, d(x,0)<=6, d(x,A)<=6, d(x,B)<=6}`.

Every normalized component with at least three vertices lies inside one of
these three branch sets.

## Exact branch statistics

| `|A cap B|` | Representative `B` | Orbit size | Vertices | Distance-6 edges | CNF variables | CNF clauses |
|---:|---:|---:|---:|---:|---:|---:|
| 3 | 455 | 200 | 555 | 65,886 | 3,522 | 223,071 |
| 4 | 207 | 150 | 582 | 72,827 | 4,274 | 357,552 |
| 5 | 95 | 30 | 618 | 82,598 | 4,554 | 407,273 |

The CNFs use 12 colors and fix every surviving vertex of the known Hadamard
clique to a distinct named color. This is symmetry breaking only and does not
strengthen the coloring problem.

## Reproduce

```bash
python borsuk_11_k6_second_base/enumerate_second_base.py \
  --out generated_second_base \
  --emit-cnf
```

The script uses only the Python standard library. It reconstructs the trim,
exhaustively checks the three orbit classes, verifies branch edge hashes, and
emits DIMACS instances plus variable maps.

## Interpretation of solver results

- **All three SAT:** the diameter-6 case is proved, assuming the explicit
  colorings independently verify.
- **Any branch UNSAT:** the three-base universal branch is still too coarse.
  UNSAT does not refute Borsuk because each branch set still contains pairs at
  distance greater than 6. The next layer must add another compatible vertex
  or encode more of the diameter constraints.
- **SAT for only some branches:** retain their coloring witnesses and continue
  branching only inside the unresolved branch types.

See `second_base_report.json` for the exact counts and hashes.

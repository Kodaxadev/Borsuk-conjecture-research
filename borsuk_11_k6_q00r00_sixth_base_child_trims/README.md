# q00r00 sixth-base child trims

## Governed target

This package generates the 36 universal trims attached to the frozen compatible sixth-base representatives

```text
q00r00-s000 through q00r00-s035
```

from the execution-bound classification package at branch head
`bb2fb6879805d1d7f024c67554dae4784ebab219`.

The only governed case input is the exact classification child manifest with SHA-256
`180e8398807c95478ac7cb62262758314a9c49270a487de0370f384dff39efb5`.
The input is bound to classification workflow run `30842512224`, job `91782782478`,
artifact `8867349456`, and artifact archive SHA-256
`0f45e952cda60a47f01fb0a415de07438cc9bc32f3d4811c8d17ce1cb2982a7d`.

## Trim definition

For each frozen representative `r`, let

```text
B_r = (0, 63, 455, 1611, 732, r).
```

The universal child trim is the ascending set of all `v` in the 11-cube satisfying

```text
wt(v) is even
and d_H(v,b) <= 6 for every b in B_r.
```

For every child the generated certificate contains:

- `base.json` — six-point base, exact predicate, parent binding, and status;
- `vertices.txt` — complete ascending trim-vertex list;
- `distance6_edges.csv` — complete lexicographic exact-distance-six pair list;
- `incompatible_pairs.csv` — complete lexicographic distance-greater-than-six pair list;
- `summary.json` — counts, paths, sizes, and SHA-256 hashes.

The aggregate `manifest.json` binds all 36 children and all child files.

## Frozen output

- children: **36**
- total trim-vertex entries across children: **10,513**
- child trim-size range: **248–328**
- total exact-distance-six edges across children: **611,145**
- child edge-count range: **11,859–21,642**
- total incompatible pairs across children: **178,886**
- child incompatible-pair range: **3,552–6,649**
- aggregate manifest SHA-256: `559f83e4eb245902b9ec1808812248694c7931a535213c45b50d7a89a461e5fa`
- canonical `SHA256SUMS` SHA-256: `45e96e2b460d6f968ed664b06ec59adc6091040273acf9cfbc022d3a1586654c`

## Independent reproduction

```bash
python verify_package.py
```

The verifier runs a Python generator and a separately implemented JavaScript generator into isolated directories. Neither implementation consumes the other's output. It requires identical output paths, sizes, and bytes, then independently reconstructs every vertex and pair set from the six-point bases.

Successful verification writes the canonical certificate tree to `generated/`. CI uploads that directory as the workflow artifact `q00r00-sixth-base-child-trims`.

## Mathematical boundary

This package creates universal trim certificates only.

- Every child remains `UNKNOWN`.
- No SAT solver is run.
- No coloring witness is claimed.
- No UNSAT inference is made.
- No cases are recanonicalized, merged, split, or refined.
- `q00r00` remains `UNKNOWN`.
- `q00` remains `UNKNOWN`.
- `n11-k6-full` remains Gate 2 / `OPEN`.

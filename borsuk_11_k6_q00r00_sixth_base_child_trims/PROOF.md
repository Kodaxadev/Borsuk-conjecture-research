# Exhaustiveness argument for the 36 child trims

## Frozen case source

The package reads exactly 36 rows from `input/classification_child_manifest.csv` and rejects any byte change from the classification artifact member hash
`180e8398807c95478ac7cb62262758314a9c49270a487de0370f384dff39efb5`.
The identifiers must be exactly `q00r00-s000` through `q00r00-s035`, in order, with distinct representatives and status `UNKNOWN`.

The copied execution binding is also hash-frozen and checked against the successful classification run, job, source commit, artifact ID, archive digest, and unresolved parent statuses.

## Complete vertex enumeration

For each representative `r`, both implementations form

```text
B_r = (0, 63, 455, 1611, 732, r)
```

and scan all 2,048 vertices of the 11-dimensional cube. A vertex is retained exactly when it has even Hamming weight and lies at Hamming distance at most six from every point in `B_r`.

The package verifier repeats this full cube scan and requires equality with the serialized ascending vertex list.

## Complete pair classification

For every unordered pair of distinct trim vertices, the implementations compute the Hamming distance exactly.

- Distance six pairs enter `distance6_edges.csv`.
- Distance greater than six pairs enter `incompatible_pairs.csv`.
- Smaller-distance pairs enter neither file.

The verifier recomputes every unordered pair, requires exact list equality, checks strict lexicographic ordering and unique endpoints, and confirms that edge and incompatible-pair sets are disjoint.

## File and aggregate binding

Each child summary binds its base, vertex, edge, and incompatible-pair files by relative path, byte size, count, and SHA-256. The aggregate manifest binds every child summary and repeats the frozen classification identifiers.

`SHA256SUMS` covers every canonical mathematical file except its own row and the nonmathematical generation report. `EXPECTED_OUTPUT.json` freezes the aggregate manifest hash, checksum-manifest hash, file count, count ranges, and aggregate totals.

## Independent implementation

The Python and JavaScript implementations share only the governed input files and serialization specification. They do not import common mathematical code and write to separate output directories. Verification requires identical path sets and byte-for-byte equality before the primary tree is accepted as the canonical artifact.

## Scope

This establishes a finite, reproducible construction of the 36 universal child trims. It does not establish that any trim is 12-colorable or not 12-colorable, and it changes no mathematical status.

# q00r00 compatible sixth-base classification

## Governed target

This package classifies every legal sixth vertex extending the fixed five-point base

```text
B = (0, 63, 455, 1611, 732)
  = (0x000, 0x03f, 0x1c7, 0x64b, 0x2dc)
```

under the full affine-cube-isometry stabilizer preserving `B` as an unordered set.
It does not generate sixth-base child trims and does not change any mathematical status.

## Compatibility predicate

A cube vertex `v` is a compatible sixth-vertex candidate exactly when

```text
v not in B
wt(v) is even
and d_H(v,b) <= 6 for every b in B.
```

## Frozen classification

- compatible candidates: **329**
- unordered base stabilizer order: **24**
- induced base permutations: **12**
- pointwise stabilizer order: **2**
- unordered-stabilizer orbits: **36**
- pointwise-only negative-control orbits: **222**
- candidate SHA-256: `67b1aa6542de0af7db525681e1a0cbfbfe6e56e3cb56c781e09708b41fdcff80`
- child manifest SHA-256: `180e8398807c95478ac7cb62262758314a9c49270a487de0370f384dff39efb5`
- stabilizer JSON SHA-256: `93145769f74924b2ff823adbe6f3b2bf8886bb7165c5c5fbb644b1e0f079c33d`
- orbit JSON SHA-256: `40b23c5c7c726a0526c501aa8b783c5b086d71fd2ffd7c7a3041b235293db1de`

The governed cases are `q00r00-s000` through `q00r00-s035`. Every child remains `UNKNOWN`.

## Reproduce

```bash
python verify_package.py
```

The Python and JavaScript implementations independently reconstruct the candidate set,
unordered set stabilizer, pointwise negative control, complete orbit partition, explicit
representative-to-member automorphisms, and all frozen hashes. The package verifier
requires byte-for-byte agreement. It writes the complete `generated/orbits.json` and
`generated/stabilizer.json` certificates locally; CI uploads the regenerated directory as
an immutable workflow artifact.

## Execution binding

The classification is bound to workflow run `30842512224`, successful job
`classify` (`91782782478`), source commit
`1cee54611bf414f7961cbdd43f5fc2b867b3230d`, and artifact
`q00r00-sixth-base-classification` (`8867349456`).

The downloaded archive SHA-256 is
`0f45e952cda60a47f01fb0a415de07438cc9bc32f3d4811c8d17ce1cb2982a7d`,
matching the GitHub artifact digest. See `EXECUTION_BINDING.json` for the complete
machine-readable binding.

Evidence state:

```text
COMPUTATIONAL / CI_INDEPENDENTLY_REPRODUCED / EXECUTION_BOUND / WORKING
```

## Next governed work

The next work unit is generation and independent verification of the 36 compatible
sixth-base child trims. See `NEXT_WORK_UNIT.md`. Classification is complete; solving or
further refining the children is outside this package.

## Mathematical boundary

This is a finite classification result for fixed base `q00r00`, not a coloring result.
No sixth-base child trim is generated here. `q00r00`, `q00`, and `n11-k6-full` retain
their prior unresolved status.

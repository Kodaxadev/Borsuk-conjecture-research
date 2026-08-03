# Borsuk 11, diameter 8 — independently checkable candidate

This package contains a proof reduction and an explicit 12-coloring of
the universal finite cover graph

`B = {x in {0,1}^11 : weight(x) is even and weight(x) <= 8}`.

## Run

Python 3, standard library only:

```bash
python verify.py
```

Node.js, independent pairwise implementation:

```bash
node verify_independent.js
```

Both should report:

- 1,013 vertices
- 82,665 exact-distance-8 edges
- 12 colors
- zero monochromatic edges
- graph SHA-256 `32ed0ca436667ccbd7d026cc06d0990e31350684b2d0136cc93f7c3225294952`

## Files

- `PROOF.md` — mathematical reduction.
- `witness.json` — complete vertex-to-color certificate.
- `verify.py` — mask-generated graph verifier.
- `verify_independent.js` — independently implemented pairwise verifier.
- `report.json` — expected verification summary.
- `dependency_graph.json` — claim and artifact dependencies.
- `HOSTILE_AUDIT.md` — known limitations and attempted failure modes.
- `SHA256SUMS` — hashes of package files.

The coloring is a certificate, not a claim that the graph's chromatic
number equals 12. Only the upper bound is needed.

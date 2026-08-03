# Borsuk 11, diameter 6 — exact attack package

This package does **not** claim the diameter-6 case is solved. It
compresses the remaining work into a canonical, symmetry-broken finite
instance and records a structured 120-vertex obstruction core.

## Verify the package

```bash
python verify_structure.py
node verify_independent.js
sha256sum -c SHA256SUMS
```

Expected principal values:

- trim vertices: 692
- trim edges: 104,606
- Hadamard clique: 12
- reduced SAT variables: 4,440
- SAT clauses: 362,120
- partial coloring: 572 assigned, 120 uncolored
- obstruction-core edges: 3,015
- trim graph hash: `a0c7fb01f50083df21ef1e74e478dda4a372455585e1e780763847a4a758fb55`
- CNF hash: `6adb2e0eeb83ed029b4330ff6a1e87e7692694c9d5860be58ac3c5818c8dce4d`

## Solve

Run a modern SAT solver on:

```bash
kissat k6_trim_12color.cnf > solver_output.txt
```

A SAT model can be checked with:

```bash
python verify_solution.py solver_output.txt
```

An UNSAT result should only be trusted with a proof-producing solver and
an independently checked DRAT/LRAT certificate. UNSAT would show that
this universal trim cover is too coarse; it would not disprove Borsuk.

See `ATTACK_SURFACE.md` for the mathematical reduction and limitations.

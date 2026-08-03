# Hostile audit of the candidate Borsuk(11,4) proof

## Claim scope

The package proves only the diameter-four subcase in the 11-dimensional
Boolean cube. It does not prove the full dimension-11 statement; diameters six
and eight remain outside this package.

## Attack 1: Different components are normalized by different isometries

This is harmless. Components of the exact-distance-four graph have no edges
between them, so each may be colored independently and the same 12 labels may
be reused. The isometries are proof devices; they do not need to agree across
components.

## Attack 2: Translation does not force even weight

For a connected component it does. After one vertex is translated to zero,
every path from zero consists of edges changing exactly four coordinates.
Parity is therefore invariant along the path. This would fail for an arbitrary
nonconnected subset, which is why the proof first separates components.

## Attack 3: Weight-three vertices were silently discarded

They are absent only after the connected-component parity reduction. Diameter
at most four bounds the weight by four, and even parity leaves weights zero,
two, and four. The original paper's short Proposition 6 proof does not spell
this reduction out; this package does.

## Attack 4: The Johnson classification omits small families

A family with zero or one weight-four member is trivially contained in a star.
For at least two members, the elementary proof in `PROOF.md` applies. The
independent maximal-clique enumeration also finds only stars and tops.

## Attack 5: A triangle may have another isometry type

After translating one triangle vertex to zero, the other two supports have
size four and intersection size two. Coordinate permutations act transitively
on ordered pairs of four-sets with intersection two, giving the stated normal
form.

## Attack 6: The coloring search itself might be wrong

The search procedure is irrelevant once a witness exists. The package stores
explicit colors and reconstructs all graph edges from first principles. Python
and JavaScript implementations independently obtain identical vertex counts,
edge counts, graph hashes, and successful edge checks.

## Attack 7: Proper coloring may not imply smaller diameter

Every original pair has distance at most four. A proper coloring forbids
same-colored pairs at distance exactly four, so every color class has diameter
strictly below four.

## Attack 8: The result might already be known

That is a priority and attribution question, not a correctness issue. Searches
through August 2, 2026 found the 2025 dimension-10 preprint but no indexed
source explicitly settling the dimension-11 diameter-four case. This absence
must be checked with the authors and specialists before any novelty claim.

## Remaining trust boundary

The remaining assumptions are elementary finite mathematics plus the
correctness of two very small verifier implementations. No solver's UNSAT
answer, timeout convention, floating-point computation, or uncheckable search
coverage is used.

# Hostile audit

## The generator silently recanonicalizes the 36 cases

Rejected. The exact child-manifest bytes are hash-frozen. IDs, order, representative encodings, uniqueness, orbit data, and `UNKNOWN` status are validated. No symmetry computation exists in this package.

## A representative is omitted or consumed twice

Rejected. The manifest must contain exactly the sequential IDs `q00r00-s000` through `q00r00-s035`, and all 36 representatives must be distinct. The aggregate output must preserve the same sequence exactly once.

## The trim predicate omits the parity restriction

Rejected. Both implementations independently require even Hamming weight and distance at most six from all six base points. The package verifier performs its own exhaustive scan of all 2,048 vertices.

## A trim list is incomplete but internally consistent

Rejected. The verifier reconstructs the full admissible vertex set from the predicate rather than trusting counts or hashes.

## Edges and incompatible pairs are confused

Rejected. Every unordered pair is independently recomputed. Distance exactly six and distance greater than six are checked separately, and the serialized sets must be disjoint and exhaustive for their respective predicates.

## Pair files contain duplicates or reversed rows

Rejected. Pair endpoints must satisfy `left < right`; files must be strictly lexicographically increasing. The verifier requires exact equality with independently reconstructed canonical lists.

## Both implementations accidentally compare one implementation with itself

Rejected. Python and JavaScript run as separate processes into isolated directories. Output path sets, sizes, and SHA-256 hashes are compared before either tree is accepted.

## Generated files are detached from the classification evidence

Rejected. Every child base record and the aggregate manifest carry the classification source commit, workflow run, artifact ID, archive digest, and frozen classification-member hashes.

## Generation changes child or parent status

Rejected. All child metadata and summaries must remain `UNKNOWN`, while the aggregate status boundary fixes `q00r00` and `q00` as `UNKNOWN` and `n11-k6-full` as Gate 2 / `OPEN`.

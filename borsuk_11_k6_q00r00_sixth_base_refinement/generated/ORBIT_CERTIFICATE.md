# Complete orbit certificate

The canonical complete certificate is generated as `orbits.json` by both independent implementations.

- canonical SHA-256: `40b23c5c7c726a0526c501aa8b783c5b086d71fd2ffd7c7a3041b235293db1de`
- candidates: 329
- unordered orbits: 36
- explicit representative-to-member maps: included for every orbit member

Regenerate and check byte agreement with:

```bash
python verify_package.py
sha256sum generated/orbits.json
```

CI uploads the regenerated `generated/` directory, including the full `orbits.json` and `stabilizer.json`, as a workflow artifact.

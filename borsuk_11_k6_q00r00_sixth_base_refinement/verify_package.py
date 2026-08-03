#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED = {
    "child_manifest.csv": "180e8398807c95478ac7cb62262758314a9c49270a487de0370f384dff39efb5",
    "classification.json": "ba6e09a0ae0125323dab047c1b2cd6dc98359e366141d36e3afbac3c1c2b2bbb",
    "compatible_candidates.txt": "67b1aa6542de0af7db525681e1a0cbfbfe6e56e3cb56c781e09708b41fdcff80",
    "orbits.json": "40b23c5c7c726a0526c501aa8b783c5b086d71fd2ffd7c7a3041b235293db1de",
    "stabilizer.json": "93145769f74924b2ff823adbe6f3b2bf8886bb7165c5c5fbb644b1e0f079c33d",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def validate_report(path: Path) -> None:
    report = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "candidate_count": 329,
        "induced_base_permutation_count": 12,
        "orbit_count": 36,
        "pointwise_orbit_count_negative_control": 222,
        "pointwise_stabilizer_order": 2,
        "stabilizer_generator_count": 3,
        "stabilizer_order": 24,
        "status": "PASS",
    }
    for key, value in expected.items():
        if report.get(key) != value:
            raise SystemExit(f"classification value mismatch for {key}: {report.get(key)!r}")
    checks = report.get("checks")
    if not isinstance(checks, dict) or not checks or not all(value is True for value in checks.values()):
        raise SystemExit("classification checks are not uniformly true")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="q00r00-sixth-") as temp:
        temp_root = Path(temp)
        python_out = temp_root / "python"
        js_out = temp_root / "javascript"
        run(["python", str(ROOT / "classify_sixth.py"), "--output-dir", str(python_out)])
        run(["node", str(ROOT / "verify_independent.js"), "--output-dir", str(js_out)])
        python_names = sorted(path.name for path in python_out.iterdir())
        js_names = sorted(path.name for path in js_out.iterdir())
        if python_names != js_names:
            raise SystemExit(f"implementation output sets differ: {python_names} != {js_names}")
        for name in python_names:
            if (python_out / name).read_bytes() != (js_out / name).read_bytes():
                raise SystemExit(f"independent outputs differ: {name}")
        for name, expected in EXPECTED.items():
            observed = digest(python_out / name)
            if observed != expected:
                raise SystemExit(f"frozen digest mismatch for {name}: {observed}")
        validate_report(python_out / "classification.json")
        generated = ROOT / "generated"
        if generated.exists():
            shutil.rmtree(generated)
        shutil.copytree(python_out, generated)
    print("PASS independent_byte_agreement=true candidates=329 unordered_order=24 pointwise_order=2 unordered_orbits=36 pointwise_orbits=222 children_status=UNKNOWN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

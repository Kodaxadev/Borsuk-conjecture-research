#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", type=Path, required=True)
    parser.add_argument("--expected", type=Path, required=True)
    args = parser.parse_args()
    expected = json.loads(args.expected.read_text(encoding="utf-8"))
    aggregate = json.loads((args.instances / "instances.json").read_text(encoding="utf-8"))
    if aggregate["case_count"] != expected["case_count"] or aggregate["case_ids"] != expected["case_ids"]:
        raise SystemExit("pilot case set changed")
    if aggregate["totals"] != expected["totals"]:
        raise SystemExit("pilot aggregate totals changed")
    if sha256_file(args.instances / "instances.json") != expected["instances_sha256"]:
        raise SystemExit("instances.json hash changed")
    if sha256_file(args.instances / "SHA256SUMS") != expected["sha256sums_sha256"]:
        raise SystemExit("SHA256SUMS hash changed")
    for case_id in expected["case_ids"]:
        metadata_path = args.instances / "cases" / case_id / f"{case_id}_metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        fingerprint = expected["case_fingerprints"][case_id]
        for field, value in fingerprint.items():
            if metadata.get(field) != value:
                raise SystemExit(f"frozen field changed for {case_id}: {field}")
        for name, field in [
            (f"{case_id}_12color.cnf", "cnf_sha256"),
            (f"{case_id}_variable_map.json", "variable_map_sha256"),
            (f"{case_id}_vertices.txt", "vertices_sha256"),
            (f"{case_id}_distance6_edges.csv", "edges_sha256"),
        ]:
            if sha256_file(metadata_path.parent / name) != fingerprint[field]:
                raise SystemExit(f"file hash changed for {case_id}: {name}")
    listed: set[str] = set()
    for line in (args.instances / "SHA256SUMS").read_text(encoding="ascii").splitlines():
        digest, relative = line.split("  ", 1)
        if relative in listed:
            raise SystemExit(f"duplicate checksum entry: {relative}")
        path = args.instances / relative
        if not path.is_file() or sha256_file(path) != digest:
            raise SystemExit(f"checksum mismatch: {relative}")
        listed.add(relative)
    intended = {
        path.relative_to(args.instances).as_posix()
        for path in args.instances.rglob("*")
        if path.is_file() and path.name != "SHA256SUMS"
    }
    if listed != intended:
        raise SystemExit("SHA256SUMS coverage mismatch")
    print(json.dumps({
        "status": "PASS",
        "case_count": expected["case_count"],
        "instances_sha256": expected["instances_sha256"],
        "sha256sums_sha256": expected["sha256sums_sha256"],
        "totals": expected["totals"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

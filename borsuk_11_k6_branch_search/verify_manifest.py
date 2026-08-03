#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parent
MANIFEST_PATH = PACKAGE / "manifest.json"
CLAIMS_PATH = ROOT / "research" / "claims.json"
N = 11
A = (1 << 6) - 1
ALLOWED_STATES = {"SAT_CLOSED", "UNSAT_BRANCHED", "LEGAL_UNSAT", "UNKNOWN"}


def distance(left: int, right: int) -> int:
    return (left ^ right).bit_count()


def root_vertices() -> set[int]:
    return {
        mask
        for mask in range(1 << N)
        if mask.bit_count() % 2 == 0
        and mask.bit_count() <= 6
        and distance(mask, A) <= 6
    }


def vertex_hash(vertices: set[int]) -> str:
    data = "".join(f"{mask:03x}\n" for mask in sorted(vertices)).encode("ascii")
    return hashlib.sha256(data).hexdigest()


def parse_mask(value: Any, context: str) -> int:
    if not isinstance(value, str) or len(value) != 3:
        raise ValueError(f"{context}: expected a three-digit hexadecimal mask")
    try:
        mask = int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{context}: invalid hexadecimal mask {value!r}") from exc
    if not 0 <= mask < (1 << N):
        raise ValueError(f"{context}: mask outside the 11-cube: {value}")
    return mask


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    claims = json.loads(CLAIMS_PATH.read_text(encoding="utf-8"))
    claim_by_id = {claim["id"]: claim for claim in claims["claims"]}
    errors: list[str] = []

    if manifest.get("schema_version") != 1:
        fail(errors, "schema_version must equal 1")
    target_id = manifest.get("theorem_target_claim_id")
    if target_id not in claim_by_id:
        fail(errors, f"unknown theorem target claim: {target_id!r}")
    elif claim_by_id[target_id]["status"] != "open":
        fail(errors, "theorem target must remain open while theorem_complete is false")
    if manifest.get("theorem_complete") is not False:
        fail(errors, "initial manifest must not claim theorem completion")

    nodes = manifest.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        fail(errors, "nodes must be a non-empty array")
        nodes = []

    node_by_id: dict[str, dict[str, Any]] = {}
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("id"), str):
            fail(errors, "every node must be an object with a string id")
            continue
        node_id = node["id"]
        if node_id in node_by_id:
            fail(errors, f"duplicate node id: {node_id}")
        node_by_id[node_id] = node
        if node.get("state") not in ALLOWED_STATES:
            fail(errors, f"{node_id}: unsupported state {node.get('state')!r}")

    root_id = manifest.get("root_node")
    if root_id not in node_by_id:
        fail(errors, f"root_node not found: {root_id!r}")
    elif node_by_id[root_id].get("parent") is not None:
        fail(errors, f"{root_id}: root parent must be null")

    computed_sets: dict[str, set[int]] = {}

    def compute_set(node_id: str, stack: set[str] | None = None) -> set[int]:
        if node_id in computed_sets:
            return computed_sets[node_id]
        if stack is None:
            stack = set()
        if node_id in stack:
            raise ValueError(f"cycle detected at {node_id}")
        stack.add(node_id)
        node = node_by_id[node_id]
        parent_id = node.get("parent")
        if parent_id is None:
            vertices = root_vertices()
        else:
            if parent_id not in node_by_id:
                raise ValueError(f"{node_id}: unknown parent {parent_id!r}")
            vertices = set(compute_set(parent_id, stack))
            removed = parse_mask(node.get("removed_from_parent"), f"{node_id}.removed_from_parent")
            if removed not in vertices:
                raise ValueError(f"{node_id}: removed vertex is absent from parent")
            vertices.remove(removed)
        stack.remove(node_id)
        computed_sets[node_id] = vertices
        return vertices

    for node_id, node in node_by_id.items():
        try:
            vertices = compute_set(node_id)
        except ValueError as exc:
            fail(errors, str(exc))
            continue
        if node.get("vertex_count") != len(vertices):
            fail(errors, f"{node_id}: vertex_count mismatch")
        actual_hash = vertex_hash(vertices)
        if node.get("vertex_sha256") != actual_hash:
            fail(errors, f"{node_id}: vertex_sha256 mismatch; expected {actual_hash}")

        children = node.get("children")
        if not isinstance(children, list) or not all(isinstance(child, str) for child in children):
            fail(errors, f"{node_id}: children must be an array of node ids")
            children = []
        for child_id in children:
            if child_id not in node_by_id:
                fail(errors, f"{node_id}: unknown child {child_id}")
            elif node_by_id[child_id].get("parent") != node_id:
                fail(errors, f"{node_id}: child {child_id} has wrong parent")

        state = node.get("state")
        if state == "UNSAT_BRANCHED":
            certificate_id = node.get("certificate_claim_id")
            certificate = claim_by_id.get(certificate_id)
            if certificate is None or certificate.get("status") != "certified-obstruction":
                fail(errors, f"{node_id}: missing certified obstruction reference")
            edge = node.get("branch_edge")
            if not isinstance(edge, dict):
                fail(errors, f"{node_id}: missing branch_edge")
                continue
            try:
                left = parse_mask(edge.get("left"), f"{node_id}.branch_edge.left")
                right = parse_mask(edge.get("right"), f"{node_id}.branch_edge.right")
            except ValueError as exc:
                fail(errors, str(exc))
                continue
            d = distance(left, right)
            if left not in vertices or right not in vertices:
                fail(errors, f"{node_id}: branch edge endpoint absent")
            if d <= 6 or edge.get("distance") != d:
                fail(errors, f"{node_id}: branch edge is not a recorded incompatibility")
            if len(children) != 2:
                fail(errors, f"{node_id}: UNSAT_BRANCHED requires exactly two children")
            else:
                removed = {node_by_id[child].get("removed_from_parent") for child in children}
                if removed != {f"{left:03x}", f"{right:03x}"}:
                    fail(errors, f"{node_id}: children must delete opposite branch endpoints")
        elif state == "UNKNOWN":
            if children:
                fail(errors, f"{node_id}: UNKNOWN node must not pretend to have completed children")
            if not isinstance(node.get("reason"), str) or not node["reason"].strip():
                fail(errors, f"{node_id}: UNKNOWN node requires a reason")
        elif state == "LEGAL_UNSAT":
            if any(distance(left, right) > 6 for left in vertices for right in vertices if left < right):
                fail(errors, f"{node_id}: LEGAL_UNSAT node contains an incompatible pair")

    if errors:
        print("Manifest verification failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Manifest OK: {len(node_by_id)} nodes")
    print(f"Root: {root_id}")
    print("Open UNKNOWN leaves: " + str(sum(node["state"] == "UNKNOWN" for node in nodes)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Archive-level checks for the seventh-base colorability pilot binding.

Nothing here trusts a recorded conclusion.  Every case coloring is recomputed
from the raw Kissat assignment and the frozen variable map, then every
distance-six edge is rechecked from the frozen edge CSV; checked-coloring.json
is compared against that recomputation rather than used as the source of truth.
"""
import hashlib
import json
import os
import zipfile

CLAIM_ID = "n11-k6-q00r00-seventh-base-colorability-pilot"
SCHEMA = "borsuk-q00r00-seventh-base-colorability-pilot-execution-binding-v1"
WORKFLOW_ID = 326703705
RUN_ID = 30880666065
RUN_ATTEMPT = 1
EVENT = "workflow_dispatch"
BRANCH = "research/q00r00-seventh-base-colorability-pilot"
REF = "refs/heads/" + BRANCH
HEAD_SHA = "8ef3163bb508d37f1adba5d246b1b0dd636b0778"

FROZEN_TOTALS = {
    "cases": 15,
    "vertices": 2840,
    "distance_six_edges": 100083,
    "incompatible_pairs": 27343,
    "compact_variables": 18397,
    "compact_clauses": 403257,
}

CLOSED_GRANDCHILDREN = [
    "q00r00-s026-t066", "q00r00-s028-t116", "q00r00-s028-t144",
    "q00r00-s028-t148", "q00r00-s028-t154", "q00r00-s030-t084",
    "q00r00-s030-t086", "q00r00-s031-t041", "q00r00-s033-t084",
    "q00r00-s034-t025", "q00r00-s034-t028", "q00r00-s034-t033",
    "q00r00-s034-t034", "q00r00-s034-t035", "q00r00-s035-t008",
]

AFFECTED_PARENTS = ["q00r00-s026", "q00r00-s028", "q00r00-s030", "q00r00-s031",
                    "q00r00-s033", "q00r00-s034", "q00r00-s035"]

RESULT_PARTITION = {"SAT_CHECKED_COLORING": 15, "PROOF_CHECKED_UNSAT": 0,
                    "UNKNOWN": 0}


class Report(object):
    """Collects failures instead of aborting, so one run reports everything."""

    def __init__(self):
        self.failures = []
        self.checks = 0

    def require(self, cond, message):
        self.checks += 1
        if not cond:
            self.failures.append(message)
        return bool(cond)


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def check_artifacts(binding, evidence_dir, rep):
    """Digest, size, sidecar and aggregate-manifest checks for all 17 ZIPs."""
    records = binding["artifacts"]["records"]
    rep.require(len(records) == 17,
                "expected 17 artifact records, got %d" % len(records))
    rep.require(binding["artifacts"]["count"] == 17, "artifact count field != 17")

    root = os.path.dirname(os.path.dirname(os.path.dirname(evidence_dir)))
    archives = {}
    for rec in records:
        path = os.path.join(root, rec["repository_path"])
        name = os.path.basename(path)
        if not rep.require(os.path.exists(path), "missing archive %s" % name):
            continue
        data = read_bytes(path)
        digest = sha256_bytes(data)
        archives[rec["artifact_type"]] = path
        rep.require(digest == rec["local_zip_sha256"],
                    "%s: sha256 != recorded local digest" % name)
        rep.require(digest == rec["github_digest_sha256"],
                    "%s: sha256 != GitHub digest" % name)
        rep.require(len(data) == rec["size_in_bytes"],
                    "%s: size != GitHub size" % name)
        rep.require(rec["workflow_run_id"] == RUN_ID, "%s: wrong run id" % name)
        rep.require(rec["workflow_run_head_sha"] == HEAD_SHA,
                    "%s: wrong head sha" % name)

        with zipfile.ZipFile(path) as archive:
            members = [n for n in archive.namelist() if not n.endswith("/")]
        rep.require(len(members) == rec["file_count"],
                    "%s: file count %d != recorded %d"
                    % (name, len(members), rec["file_count"]))

        sidecar = os.path.join(root, rec["repository_checksum_path"])
        if rep.require(os.path.exists(sidecar), "missing sidecar for %s" % name):
            raw = read_bytes(sidecar)
            rep.require(b"\r" not in raw, "%s.sha256 contains CR bytes" % name)
            rep.require(raw.decode().strip().split()[0] == digest,
                        "%s.sha256 digest mismatch" % name)

    _check_aggregate_manifest(binding, root, rep)
    return archives


def _check_aggregate_manifest(binding, root, rep):
    path = os.path.join(root, binding["artifacts"]["aggregate_manifest_path"])
    if not rep.require(os.path.exists(path), "missing aggregate SHA256SUMS"):
        return
    raw = read_bytes(path)
    rep.require(b"\r" not in raw, "aggregate SHA256SUMS contains CR bytes")
    rep.require(sha256_bytes(raw) == binding["artifacts"]["aggregate_manifest_sha256"],
                "aggregate SHA256SUMS digest != recorded value")
    lines = [l for l in raw.decode().splitlines() if l.strip()]
    rep.require(len(lines) == 17, "aggregate SHA256SUMS has %d entries" % len(lines))
    base = os.path.dirname(path)
    for line in lines:
        expected, filename = line.split(None, 1)
        target = os.path.join(base, filename.strip())
        if rep.require(os.path.exists(target),
                       "SHA256SUMS references missing %s" % filename.strip()):
            rep.require(sha256_bytes(read_bytes(target)) == expected,
                        "SHA256SUMS mismatch for %s" % filename.strip())


def _check_certificate(cert, case_id, blob, rep):
    rep.require(cert["claim_id"] == CLAIM_ID, "%s: claim_id" % case_id)
    rep.require(cert["case_id"] == case_id, "%s: case_id" % case_id)
    execution = cert["execution"]
    rep.require(execution["workflow_run_id"] == RUN_ID, "%s: run id" % case_id)
    rep.require(execution["workflow_run_attempt"] == RUN_ATTEMPT,
                "%s: attempt" % case_id)
    rep.require(execution["workflow_ref"] == REF, "%s: ref" % case_id)
    rep.require(execution["workflow_sha"] == HEAD_SHA, "%s: workflow sha" % case_id)
    rep.require(cert["certificate_state"] == "SAT_CHECKED_COLORING",
                "%s: certificate_state" % case_id)
    rep.require(cert["solver"]["exit_status"] == 10, "%s: solver exit" % case_id)
    rep.require(cert["repository_status_changed"] is False,
                "%s: repository_status_changed" % case_id)
    rep.require(cert["parent_status_changed"] is False,
                "%s: parent_status_changed" % case_id)
    rep.require(cert["q00r00_status_changed"] is False,
                "%s: q00r00_status_changed" % case_id)
    effect = cert["mathematical_effect"]
    rep.require(effect["branch_action"] == "CLOSE_GRANDCHILD_ONLY",
                "%s: branch_action" % case_id)
    rep.require(effect["parent_child_status"] == "UNKNOWN",
                "%s: parent_child_status" % case_id)
    for filename, meta in cert["files"].items():
        rep.require(filename in blob
                    and sha256_bytes(blob[filename]) == meta["sha256"]
                    and len(blob[filename]) == meta["size_bytes"],
                    "%s: certificate file record %s" % (case_id, filename))


def _recompute_coloring(blob, case_id, variable_map, rep):
    """Rebuild the coloring from the raw solver assignment."""
    allowed = {int(k): set(v) for k, v in variable_map["allowed_colors"].items()}
    assigned = set()
    covered = set()
    for line in blob["solver.out"].decode().splitlines():
        if not line.startswith("v "):
            continue
        for token in line[2:].split():
            literal = int(token)
            if literal == 0:
                continue
            covered.add(abs(literal))
            if literal > 0:
                assigned.add(literal)
    rep.require(len(covered) == variable_map["variables"],
                "%s: assignment covers %d of %d variables"
                % (case_id, len(covered), variable_map["variables"]))

    selected = {}
    for entry in variable_map["variable_order"]:
        if entry["variable"] in assigned:
            selected.setdefault(entry["vertex"], []).append(entry["color"])

    coloring = {}
    for vertex in variable_map["vertices"]:
        colors = selected.get(vertex, [])
        if not rep.require(len(colors) == 1,
                           "%s: vertex %s has %d selected colors"
                           % (case_id, vertex, len(colors))):
            continue
        rep.require(colors[0] in allowed[vertex],
                    "%s: vertex %s colored outside allowed set" % (case_id, vertex))
        coloring[vertex] = colors[0]
    return coloring


def _check_edges(blob, case_id, coloring, instance, rep):
    rows = blob["%s_distance6_edges.csv" % case_id].decode().splitlines()
    rep.require(rows[0].strip() == "left,right", "%s: edge csv header" % case_id)
    checked = 0
    monochromatic = 0
    for row in rows[1:]:
        row = row.strip()
        if not row:
            continue
        left, right = row.split(",")
        left, right = int(left, 16), int(right, 16)
        if left not in coloring or right not in coloring:
            rep.require(False, "%s: edge endpoint uncolored" % case_id)
            continue
        checked += 1
        if coloring[left] == coloring[right]:
            monochromatic += 1
    rep.require(checked == instance["edges"],
                "%s: checked %d edges != %d" % (case_id, checked, instance["edges"]))
    rep.require(monochromatic == 0,
                "%s: %d monochromatic distance-six edges" % (case_id, monochromatic))


def recheck_case(path, case_id, rep):
    """Recompute the coloring from raw solver output and recheck every edge."""
    with zipfile.ZipFile(path) as archive:
        blob = {n: archive.read(n) for n in archive.namelist()
                if not n.endswith("/")}

    rep.require(len(blob) == 21, "%s: %d files != 21" % (case_id, len(blob)))
    manifest = [l for l in blob["artifact-sha256.txt"].decode().splitlines()
                if l.strip()]
    for line in manifest:
        expected, filename = line.split(None, 1)
        filename = filename.strip()
        rep.require(filename in blob and sha256_bytes(blob[filename]) == expected,
                    "%s: artifact manifest entry %s" % (case_id, filename))
    unlisted = sorted(set(blob) - {l.split(None, 1)[1].strip() for l in manifest})
    rep.require(unlisted == ["artifact-sha256.txt", "finalize.out"],
                "%s: unexpected unlisted files %s" % (case_id, unlisted))

    cert = json.loads(blob["certificate-result.json"])
    _check_certificate(cert, case_id, blob, rep)

    instance = cert["instance"]
    variable_map = json.loads(blob["%s_variable_map.json" % case_id])
    coloring = _recompute_coloring(blob, case_id, variable_map, rep)
    rep.require(len(coloring) == instance["vertices"],
                "%s: coloring covers %d of %d vertices"
                % (case_id, len(coloring), instance["vertices"]))

    vertex_lines = [l.strip() for l
                    in blob["%s_vertices.txt" % case_id].decode().splitlines()
                    if l.strip()]
    rep.require({int(v, 16) for v in vertex_lines} == set(variable_map["vertices"]),
                "%s: vertices.txt disagrees with variable map" % case_id)

    _check_edges(blob, case_id, coloring, instance, rep)

    colors_used = len(set(coloring.values()))
    rep.require(colors_used == 12, "%s: %d colors used" % (case_id, colors_used))

    checked_coloring = json.loads(blob["checked-coloring.json"])
    rep.require({int(k): v for k, v in checked_coloring["coloring"].items()}
                == coloring,
                "%s: recomputed coloring differs from checked-coloring.json" % case_id)
    rep.require(checked_coloring["colors_used"] == 12, "%s: cc colors" % case_id)
    rep.require(checked_coloring["edges_checked"] == instance["edges"],
                "%s: cc edges_checked" % case_id)

    return {
        "vertices": instance["vertices"],
        "edges": instance["edges"],
        "incompatible_pairs": instance["incompatible_pairs"],
        "variables": instance["variables"],
        "clauses": instance["clauses"],
        "certificate_result_sha256": sha256_bytes(blob["certificate-result.json"]),
        "checked_coloring_sha256": sha256_bytes(blob["checked-coloring.json"]),
        "blob": blob,
    }


def check_summary(path, case_blobs, rep):
    """Verify the summary archive and its 315-entry result-file manifest."""
    with zipfile.ZipFile(path) as archive:
        members = [n for n in archive.namelist() if not n.endswith("/")]
        blob = {n: archive.read(n) for n in members}
    rep.require(len(members) == 3, "summary archive has %d files" % len(members))

    for line in [l for l in blob["SHA256SUMS"].decode().splitlines() if l.strip()]:
        expected, filename = line.split(None, 1)
        filename = filename.strip()
        rep.require(filename in blob and sha256_bytes(blob[filename]) == expected,
                    "summary SHA256SUMS entry %s" % filename)

    summary = json.loads(blob["pilot-summary.json"])
    rep.require(summary["result_counts"] == RESULT_PARTITION, "summary result_counts")
    rep.require(sorted(summary["closed_grandchildren"]) == sorted(CLOSED_GRANDCHILDREN),
                "summary closed_grandchildren")
    rep.require(summary["certified_eighth_base_refinement_frontier"] == [],
                "eighth-base frontier not empty")
    rep.require(summary["incomplete_pilot_cases"] == [],
                "incomplete pilot cases not empty")
    rep.require(summary["parent_closure_count"] == 0, "parent_closure_count != 0")
    rep.require(summary["parent_closure_not_implied"] is True,
                "parent_closure_not_implied")
    rep.require(summary["repository_effect"]
                == "ELIGIBLE_FOR_POST_UPLOAD_EXECUTION_BINDING_ONLY",
                "summary repository_effect")
    rep.require(sorted(summary["affected_sixth_base_parents"])
                == sorted(AFFECTED_PARENTS), "affected sixth-base parents")
    status = summary["mathematical_status"]
    rep.require(status["q00r00"] == "UNKNOWN", "q00r00 status")
    rep.require(status["q00"] == "UNKNOWN", "q00 status")
    rep.require(status["sixth_base_parents"] == "UNKNOWN", "sixth-base parents")
    rep.require(status["n11-k6-full"] == "Gate 2 / OPEN", "n11-k6-full status")

    entries = json.loads(blob["result-file-manifest.json"])["files"]
    rep.require(len(entries) == 315,
                "result-file manifest has %d entries" % len(entries))
    verified = 0
    for entry in entries:
        case_dir, filename = entry["path"].split("/", 1)
        case_id = case_dir.replace("-seventh-base-pilot", "")
        data = case_blobs.get(case_id, {}).get(filename)
        if data is not None and sha256_bytes(data) == entry["sha256"] \
                and len(data) == entry["size_bytes"]:
            verified += 1
    rep.require(verified == len(entries),
                "result-file manifest verified %d of %d byte-for-byte"
                % (verified, len(entries)))

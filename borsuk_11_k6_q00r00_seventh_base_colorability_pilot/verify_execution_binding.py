#!/usr/bin/env python3
"""Verify the seventh-base colorability pilot execution binding.

Checks EXECUTION_BINDING.json against the archived GitHub artifact ZIPs stored
beside it, and re-derives the mathematical result from those archives instead
of trusting anything the binding asserts.

Usage:
    python verify_execution_binding.py [EVIDENCE_DIR]

EVIDENCE_DIR defaults to evidence/run-30880666065 next to this file.
Exit status is 0 when every check passes and 1 otherwise.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pilot_binding_checks import (  # noqa: E402
    CLAIM_ID, CLOSED_GRANDCHILDREN, EVENT, FROZEN_TOTALS, HEAD_SHA,
    RESULT_PARTITION, RUN_ATTEMPT, RUN_ID, SCHEMA, WORKFLOW_ID, BRANCH,
    Report, check_artifacts, check_summary, read_bytes, recheck_case,
    sha256_bytes,
)


def check_binding_claims(binding, totals, hashes, rep):
    """Cross-check the binding's own assertions against recomputed facts."""
    rep.require(binding["schema"] == SCHEMA, "binding schema")
    rep.require(binding["claim_id"] == CLAIM_ID, "binding claim_id")

    workflow = binding["workflow"]
    rep.require(workflow["workflow_id"] == WORKFLOW_ID, "workflow id")
    rep.require(workflow["run_id"] == RUN_ID, "run id")
    rep.require(workflow["run_attempt"] == RUN_ATTEMPT, "run attempt")
    rep.require(workflow["event"] == EVENT, "event")
    rep.require(workflow["branch"] == BRANCH, "branch")
    rep.require(workflow["head_sha"] == HEAD_SHA, "head sha")
    rep.require(workflow["conclusion"] == "success", "run conclusion")

    jobs = binding["jobs"]
    rep.require(jobs["total"] == 17, "job total")
    rep.require(jobs["successful"] == 17, "successful jobs")
    rep.require(len(jobs["case_jobs"]) == 15, "case job count")
    rep.require(jobs["sat_check_steps_successful"] == 15, "SAT steps")
    rep.require(jobs["unsat_check_steps_skipped"] == 15, "UNSAT steps skipped")

    frozen = binding["frozen_instance_totals"]
    for key, expected in FROZEN_TOTALS.items():
        rep.require(frozen[key] == expected,
                    "frozen total %s = %s != %s" % (key, frozen[key], expected))
        rep.require(totals[key] == expected,
                    "recomputed total %s = %s != %s" % (key, totals[key], expected))

    expected_partition = dict(RESULT_PARTITION)
    expected_partition["total"] = 15
    rep.require(binding["result_partition"] == expected_partition,
                "binding result partition")

    _check_effect(binding["mathematical_effect"], rep)

    rep.require(len(binding["known_defects"]) >= 1, "known defect record missing")
    defect = binding["known_defects"][0]
    rep.require(defect["severity"] == "LOW", "defect severity")
    rep.require(defect["status"] == "DEFERRED", "defect disposition")

    for record in binding["cases"]:
        case_id = record["case_id"]
        rep.require(record["certificate_result_sha256"]
                    == hashes[case_id]["certificate_result_sha256"],
                    "%s: bound certificate hash" % case_id)
        rep.require(record["checked_coloring_sha256"]
                    == hashes[case_id]["checked_coloring_sha256"],
                    "%s: bound checked-coloring hash" % case_id)
        rep.require(record["sat_check_step_conclusion"] == "success",
                    "%s: SAT step" % case_id)
        rep.require(record["unsat_check_step_conclusion"] == "skipped",
                    "%s: UNSAT step" % case_id)


def _check_effect(effect, rep):
    rep.require(effect["closed_grandchildren"] == 15, "closed grandchildren")
    rep.require(effect["closed_grandchild_ids"] == CLOSED_GRANDCHILDREN,
                "closed grandchild ids")
    rep.require(effect["certified_eighth_base_frontier"] == 0,
                "eighth-base frontier")
    rep.require(effect["incomplete_pilot_cases"] == 0, "incomplete cases")
    rep.require(effect["nonpilot_grandchildren_remaining_unknown"] == 4461,
                "remaining unknown grandchildren")
    rep.require(effect["sixth_base_parents_closed"] == 0, "parents closed")
    rep.require(effect["q00r00"] == "UNKNOWN", "q00r00")
    rep.require(effect["q00"] == "UNKNOWN", "q00")
    rep.require(effect["n11-k6-full"] == "Gate 2 / OPEN", "n11-k6-full")
    rep.require(effect["eighth_base_work_authorized"] is False,
                "eighth-base work must not be authorized")


def main(argv):
    here = os.path.dirname(os.path.abspath(__file__))
    evidence_dir = argv[1] if len(argv) > 1 \
        else os.path.join(here, "evidence", "run-30880666065")
    binding_path = os.path.join(evidence_dir, "EXECUTION_BINDING.json")

    rep = Report()
    if not os.path.exists(binding_path):
        print("FAIL: EXECUTION_BINDING.json not found at %s" % binding_path)
        return 1

    raw = read_bytes(binding_path)
    binding = json.loads(raw)
    print("execution binding sha256: %s" % sha256_bytes(raw))

    archives = check_artifacts(binding, evidence_dir, rep)

    totals = {"cases": 0, "vertices": 0, "distance_six_edges": 0,
              "incompatible_pairs": 0, "compact_variables": 0,
              "compact_clauses": 0}
    hashes = {}
    case_blobs = {}
    for case_id in CLOSED_GRANDCHILDREN:
        path = archives.get(case_id)
        if not rep.require(path is not None, "missing archive for %s" % case_id):
            continue
        result = recheck_case(path, case_id, rep)
        case_blobs[case_id] = result.pop("blob")
        hashes[case_id] = result
        totals["cases"] += 1
        totals["vertices"] += result["vertices"]
        totals["distance_six_edges"] += result["edges"]
        totals["incompatible_pairs"] += result["incompatible_pairs"]
        totals["compact_variables"] += result["variables"]
        totals["compact_clauses"] += result["clauses"]

    if rep.require("summary" in archives, "missing summary archive"):
        check_summary(archives["summary"], case_blobs, rep)

    check_binding_claims(binding, totals, hashes, rep)

    print("checks run: %d" % rep.checks)
    print("recomputed totals: %d cases, %d vertices, %d distance-six edges, "
          "%d incompatible pairs, %d variables, %d clauses"
          % (totals["cases"], totals["vertices"], totals["distance_six_edges"],
             totals["incompatible_pairs"], totals["compact_variables"],
             totals["compact_clauses"]))
    if rep.failures:
        print("FAIL: %d problem(s)" % len(rep.failures))
        for failure in rep.failures:
            print("  - %s" % failure)
        return 1
    print("PASS: execution binding consistent with archived artifacts")
    print("  15 closed grandchildren / 0 certified eighth-base / 0 incomplete")
    print("  0 sixth-base parents closed; q00r00, q00 UNKNOWN; "
          "n11-k6-full Gate 2 / OPEN")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

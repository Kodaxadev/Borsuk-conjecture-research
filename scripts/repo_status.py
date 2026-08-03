#!/usr/bin/env python3
"""Print the repository's machine-readable research status."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "research" / "claims.json"


def summarize() -> None:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    claims = data["claims"]
    active_id = data["active_target"]
    active = next(claim for claim in claims if claim["id"] == active_id)
    counts = Counter(claim["status"] for claim in claims)

    print("Borsuk Conjecture Research status")
    print("=================================")
    print(f"Registry: {REGISTRY.relative_to(ROOT)}")
    print(f"Updated: {data['updated']}")
    print(f"Active target: {active['id']} — {active['title']}")
    print(f"Active status: {active['status']}")
    print()

    print("Claim totals")
    print("------------")
    for status in sorted(counts):
        print(f"- {status}: {counts[status]}")
    print()

    print("Claims")
    print("------")
    for claim in claims:
        marker = "*" if claim["id"] == active_id else "-"
        visibility = "public-scope wording allowed" if claim["public_claim_allowed"] else "do not promote publicly"
        print(f"{marker} {claim['id']}: {claim['status']} ({visibility})")
        print(f"  package: {claim['package']}")
        print(f"  claim: {claim['claim']}")
        if claim.get("depends_on"):
            print(f"  depends on: {', '.join(claim['depends_on'])}")
        print(f"  primary limitation: {claim['limitations'][0]}")


if __name__ == "__main__":
    summarize()

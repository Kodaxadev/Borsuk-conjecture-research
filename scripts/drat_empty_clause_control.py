#!/usr/bin/env python3
"""Create a format-aware, record-aligned DRAT negative control.

The output proof is an exact prefix ending before the first empty-clause
addition and, optionally, a requested number of complete predecessor records.
Truncating before the first empty-clause record removes every later explicit
empty-clause addition without cutting through a DRAT record.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mmap
from collections import deque
from pathlib import Path


CHUNK_SIZE = 1024 * 1024


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def detect_format(path: Path) -> str:
    with path.open("rb") as handle:
        sample = handle.read(64 * 1024)
    if not sample:
        raise ValueError("proof is empty")
    if b"\x00" in sample:
        return "binary"
    stripped = sample.lstrip()
    if not stripped:
        raise ValueError("proof contains only whitespace")
    if stripped[:1] == b"a":
        return "binary"
    if stripped[:1] == b"d" and stripped[1:2] != b" ":
        return "binary"
    return "ascii"


def find_ascii_boundary(
    path: Path, preceding_records: int
) -> tuple[list[int], int, int, int]:
    offsets: list[int] = []
    records = 0
    first_empty_record = 0
    cutoff = -1
    history: deque[int] = deque(maxlen=preceding_records + 1)

    with path.open("rb") as handle:
        while True:
            line_start = handle.tell()
            line = handle.readline()
            if not line:
                break
            body = line.rstrip(b"\r\n").strip()
            if not body or body.startswith(b"c"):
                continue
            tokens = body.split()
            is_deletion = tokens[:1] == [b"d"]
            clause_tokens = tokens[1:] if is_deletion else tokens
            if not clause_tokens or clause_tokens[-1] != b"0":
                raise ValueError(
                    f"invalid ASCII DRAT record at byte {line_start}: "
                    "record does not terminate with 0"
                )
            for token in clause_tokens:
                try:
                    int(token)
                except ValueError as exc:
                    raise ValueError(
                        f"invalid ASCII DRAT token {token!r} at byte {line_start}"
                    ) from exc

            records += 1
            history.append(line_start)
            if not is_deletion and clause_tokens == [b"0"]:
                offsets.append(line_start)
                if cutoff < 0:
                    if len(history) < preceding_records + 1:
                        raise ValueError(
                            "not enough predecessor records before first empty clause"
                        )
                    cutoff = history[0]
                    first_empty_record = records

    return offsets, records, first_empty_record, cutoff


def read_binary_varint(proof: mmap.mmap, pos: int, size: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        if pos >= size:
            raise ValueError("truncated binary DRAT literal")
        byte = proof[pos]
        pos += 1
        value |= (byte & 0x7F) << shift
        if byte <= 0x7F:
            return value, pos
        shift += 7
        if shift > 63:
            raise ValueError("binary DRAT literal exceeds 64-bit parser limit")


def find_binary_boundary(
    path: Path, preceding_records: int
) -> tuple[list[int], int, int, int]:
    offsets: list[int] = []
    records = 0
    first_empty_record = 0
    cutoff = -1
    history: deque[int] = deque(maxlen=preceding_records + 1)

    with path.open("rb") as handle:
        with mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as proof:
            size = len(proof)
            pos = 0
            while pos < size:
                record_start = pos
                marker = proof[pos]
                pos += 1
                if marker not in (ord("a"), ord("d")):
                    raise ValueError(
                        f"invalid binary DRAT marker 0x{marker:02x} "
                        f"at byte {record_start}"
                    )
                is_addition = marker == ord("a")
                literal_count = 0
                while True:
                    encoded_literal, pos = read_binary_varint(proof, pos, size)
                    if encoded_literal == 0:
                        break
                    literal_count += 1

                records += 1
                history.append(record_start)
                if is_addition and literal_count == 0:
                    offsets.append(record_start)
                    if cutoff < 0:
                        if len(history) < preceding_records + 1:
                            raise ValueError(
                                "not enough predecessor records before first empty clause"
                            )
                        cutoff = history[0]
                        first_empty_record = records

    return offsets, records, first_empty_record, cutoff


def copy_prefix(source: Path, destination: Path, byte_count: int) -> None:
    if byte_count <= 0:
        raise ValueError("negative control would be empty or invalid")
    destination.parent.mkdir(parents=True, exist_ok=True)
    remaining = byte_count
    with source.open("rb") as src, destination.open("wb") as dst:
        while remaining:
            chunk = src.read(min(CHUNK_SIZE, remaining))
            if not chunk:
                raise ValueError("source ended before requested truncation point")
            dst.write(chunk)
            remaining -= len(chunk)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("proof", type=Path)
    parser.add_argument("negative_proof", type=Path)
    parser.add_argument("metadata", type=Path)
    parser.add_argument(
        "--preceding-records",
        type=int,
        default=0,
        help=(
            "also remove this many complete records immediately preceding "
            "the first empty-clause addition"
        ),
    )
    args = parser.parse_args()
    if args.preceding_records < 0:
        parser.error("--preceding-records must be non-negative")
    return args


def main() -> int:
    args = parse_args()
    proof: Path = args.proof
    negative: Path = args.negative_proof
    metadata: Path = args.metadata
    preceding_records: int = args.preceding_records

    if not proof.is_file():
        raise FileNotFoundError(proof)

    proof_format = detect_format(proof)
    if proof_format == "binary":
        offsets, record_count, first_empty_record, cutoff = find_binary_boundary(
            proof, preceding_records
        )
    else:
        offsets, record_count, first_empty_record, cutoff = find_ascii_boundary(
            proof, preceding_records
        )

    if not offsets:
        raise ValueError("proof contains no empty-clause addition")
    if cutoff < 0:
        raise ValueError("failed to locate record-aligned truncation boundary")

    copy_prefix(proof, negative, cutoff)

    proof_size = proof.stat().st_size
    negative_size = negative.stat().st_size
    if negative_size != cutoff or negative_size >= proof_size:
        raise ValueError("negative-control size invariant failed")

    payload: dict[str, object] = {
        "schema": "drat-format-aware-negative-control-v2",
        "proof_format": proof_format,
        "proof_path": str(proof),
        "proof_bytes": proof_size,
        "proof_sha256": sha256_file(proof),
        "record_count": record_count,
        "empty_clause_addition_count": len(offsets),
        "empty_clause_addition_offsets": offsets,
        "first_empty_clause_record_index": first_empty_record,
        "preceding_records_removed": preceding_records,
        "removed_record_count_at_boundary": preceding_records + 1,
        "truncation_strategy": (
            "truncate at a complete record boundary before the first "
            f"empty-clause addition and {preceding_records} predecessor record(s)"
        ),
        "truncation_offset": cutoff,
        "negative_proof_path": str(negative),
        "negative_proof_bytes": negative_size,
        "negative_proof_sha256": sha256_file(negative),
    }
    write_json(metadata, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

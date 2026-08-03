#!/usr/bin/env python3
"""Summarize the repository's current top-level research structure.

This lightweight helper is intended to give a consistent human-readable snapshot
of where the active mathematical artifacts live in the archive.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def summarize() -> None:
    entries = sorted(p for p in ROOT.iterdir() if p.is_dir() and not p.name.startswith('.'))
    print('Borsuk Conjecture Research workspace overview')
    print('===========================================')
    for entry in entries:
        print(f"- {entry.name}")


if __name__ == '__main__':
    summarize()

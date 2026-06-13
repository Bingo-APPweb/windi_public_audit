#!/usr/bin/env python3
"""Read-only authority gate checks for AWAITING I9 documents."""

from __future__ import annotations

import argparse
from pathlib import Path


DECISION_MARKERS = ("I9:", "I9 Decision:")


def status_of(text: str) -> str:
    for line in text.splitlines()[:40]:
        if line.startswith("**Status:**"):
            return line.split(":**", 1)[1].strip()
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docs_dir", nargs="?", default="docs")
    args = parser.parse_args()

    docs_dir = Path(args.docs_dir)
    awaiting = []
    for path in sorted(docs_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        if status_of(text) == "AWAITING I9":
            awaiting.append((path, text))

    issues = 0
    for path, text in awaiting:
        boxes = text.count("[ ]")
        decision_markers = [m for m in DECISION_MARKERS if m in text]
        print(f"AWAITING_I9 {path.name} unchecked_boxes={boxes}")
        if boxes == 0:
            print("  WARN no explicit unchecked decision boxes found")
            issues += 1
        if decision_markers:
            print(f"  WARN contains decision marker text: {', '.join(decision_markers)}")
            issues += 1

    print(f"SUMMARY awaiting_i9={len(awaiting)} issues={issues}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate reviewable header patch proposals from a sanitation matrix."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_MISSION = "WINDI-HIOS document continuity"
DEFAULT_PURPOSE = "Preserve document metadata for continuity checks"


def proposed_lines(row: dict) -> list[str]:
    missing = set(row.get("missing_headers", []))
    status = row.get("status") or "CANDIDATE"
    lines: list[str] = []
    if "Status" in missing:
        lines.append(f"**Status:** {status if status != 'MISSING' else 'CANDIDATE'}")
    if "Date" in missing:
        lines.append("**Date:** 2026-06-13")
    if "Mission" in missing:
        lines.append(f"**Mission:** {DEFAULT_MISSION}")
    if "Purpose" in missing:
        lines.append(f"**Purpose:** {DEFAULT_PURPOSE}")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("matrix_json", help="JSON produced by document_sanitation_matrix.py")
    parser.add_argument("--md-out", default=None)
    args = parser.parse_args()

    matrix = json.loads(Path(args.matrix_json).read_text(encoding="utf-8"))
    rows = [row for row in matrix["rows"] if row["action"] == "HEADER_PATCH"]

    lines = [
        "# HEADER-PATCH-PROPOSALS-001",
        "",
        "**Status:** CANDIDATE",
        "**Date:** 2026-06-13",
        "**Mission:** Document continuity header patch proposals",
        "**Purpose:** Propose missing metadata lines without mutating source documents",
        "",
        "## Rule",
        "",
        "This document proposes header metadata only. It does not alter historical bodies, statuses, decisions, or sealed content.",
        "",
        "## Proposals",
        "",
    ]

    for row in rows:
        lines.extend(
            [
                f"### {row['name']}",
                "",
                f"- Current status: `{row['status']}`",
                f"- Missing headers: `{', '.join(row['missing_headers'])}`",
                f"- Source hash: `{row['sha256']}`",
                "",
                "Proposed metadata lines:",
                "",
                "```text",
            ]
        )
        lines.extend(proposed_lines(row))
        lines.extend(["```", ""])

    lines.extend(
        [
            "## Line of Guard",
            "",
            "> A header patch clarifies metadata. It must not rewrite doctrine.",
        ]
    )

    output = "\n".join(lines) + "\n"
    if args.md_out:
        Path(args.md_out).write_text(output, encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

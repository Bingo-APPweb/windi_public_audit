#!/usr/bin/env python3
"""Build a sanitation matrix from continuity_check.py JSON output."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def classify(item: dict) -> tuple[str, str]:
    name = item["name"]
    status = item.get("status") or ""
    missing = set(item.get("missing_headers", []))

    if name.lower().endswith(("notes.md", "correcoes-codex.md")) or "notes" in name.lower():
        return "RAW_NOTE", "Keep as source note or move to notes archive; do not normalize as doctrine."
    if not status:
        return "NEEDS_TRIAGE", "Missing status and required headers; classify before use."
    if not item.get("status_known", False):
        return "STATUS_NORMALIZE", "Map legacy/free-form status to DOCUMENT-STATUS-STANDARD-001."
    if missing:
        return "HEADER_PATCH", "Add missing required metadata without changing body."
    return "OK", "No action required."


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("check_json", help="JSON produced by continuity_check.py")
    parser.add_argument("--md-out", default=None, help="Optional markdown output path")
    parser.add_argument("--json-out", default=None, help="Optional JSON output path")
    args = parser.parse_args()

    data = json.loads(Path(args.check_json).read_text(encoding="utf-8"))
    rows = []
    for item in data["results"]:
        action, recommendation = classify(item)
        rows.append(
            {
                "name": item["name"],
                "status": item.get("status") or "MISSING",
                "missing_headers": item.get("missing_headers", []),
                "action": action,
                "recommendation": recommendation,
                "sha256": item["sha256"],
            }
        )

    matrix = {
        "source": args.check_json,
        "files": len(rows),
        "actions": {},
        "rows": rows,
    }
    for row in rows:
        matrix["actions"][row["action"]] = matrix["actions"].get(row["action"], 0) + 1

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(matrix, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )

    lines = [
        "# DOCUMENT-SANITATION-MATRIX-001",
        "",
        "**Status:** MEASURED",
        "**Date:** 2026-06-13",
        "**Mission:** Document continuity sanitation",
        "**Purpose:** Classify documentation status/header issues without mutating source files",
        "",
        "## Summary",
        "",
    ]
    for action, count in sorted(matrix["actions"].items()):
        lines.append(f"- `{action}`: {count}")
    lines.extend(
        [
            "",
            "## Matrix",
            "",
            "| file | status | missing_headers | action | recommendation |",
            "|---|---|---|---|---|",
        ]
    )
    for row in rows:
        missing = ", ".join(row["missing_headers"]) if row["missing_headers"] else "-"
        lines.append(
            f"| `{row['name']}` | `{row['status']}` | {missing} | `{row['action']}` | {row['recommendation']} |"
        )
    lines.extend(
        [
            "",
            "## Line of Guard",
            "",
            "> Saneamento documental classifica antes de corrigir.",
        ]
    )
    md = "\n".join(lines) + "\n"

    if args.md_out:
        Path(args.md_out).write_text(md, encoding="utf-8")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

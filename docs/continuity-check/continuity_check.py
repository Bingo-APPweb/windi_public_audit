#!/usr/bin/env python3
"""Read-only continuity check for WINDI-HIOS documentation artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


KNOWN_STATUSES = {
    "DRAFT",
    "CANDIDATE",
    "AWAITING I9",
    "SEALED",
    "MEASURED",
    "SUPERSEDED",
    "REJECTED",
    "BLOCKED",
}

REQUIRED_HEADERS = ("Status", "Date", "Mission", "Purpose")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_header(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines()[:40]:
        stripped = line.strip()
        if not stripped.startswith("**") or ":**" not in stripped:
            continue
        key_part, value = stripped.split(":**", 1)
        key = key_part.strip("* ")
        fields[key] = value.strip()
    return fields


def check_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    fields = parse_header(text)
    status = fields.get("Status", "")
    return {
        "path": str(path),
        "name": path.name,
        "sha256": sha256(path),
        "line_count": len(text.splitlines()),
        "status": status,
        "status_known": status in KNOWN_STATUSES,
        "missing_headers": [h for h in REQUIRED_HEADERS if h not in fields],
        "awaiting_i9_boxes": text.count("[ ]") if status == "AWAITING I9" else 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "docs_dir",
        nargs="?",
        default="docs",
        help="Directory containing markdown docs",
    )
    parser.add_argument(
        "--json-out",
        default=None,
        help="Optional JSON report path",
    )
    args = parser.parse_args()

    docs_dir = Path(args.docs_dir)
    files = sorted(docs_dir.glob("*.md"))
    report = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "docs_dir": str(docs_dir),
        "files_checked": len(files),
        "known_statuses": sorted(KNOWN_STATUSES),
        "results": [check_file(path) for path in files],
    }

    failures = [
        item
        for item in report["results"]
        if item["missing_headers"] or not item["status_known"]
    ]
    report["summary"] = {
        "files_checked": len(files),
        "files_with_header_or_status_issues": len(failures),
    }

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(report, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )

    for item in report["results"]:
        marker = "OK" if not item["missing_headers"] and item["status_known"] else "WARN"
        print(
            f"{marker} {item['name']} status={item['status'] or 'MISSING'} "
            f"lines={item['line_count']} sha256={item['sha256']}"
        )
        if item["missing_headers"]:
            print(f"  missing_headers={','.join(item['missing_headers'])}")
        if item["status"] and not item["status_known"]:
            print(f"  unknown_status={item['status']}")

    print(
        "SUMMARY files_checked={files_checked} issues={issues}".format(
            files_checked=report["summary"]["files_checked"],
            issues=report["summary"]["files_with_header_or_status_issues"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate read-only research receipt candidates for documentation artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Artifacts to hash")
    parser.add_argument("--json-out", default=None)
    parser.add_argument("--actor", default="codex-continuity-ops")
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    candidates = []
    for raw in args.paths:
        path = Path(raw)
        digest = sha256(path)
        candidates.append(
            {
                "receipt_candidate_id": f"RESEARCH-CANDIDATE-{path.stem}-{digest[:12]}",
                "artifact_path": str(path),
                "artifact_hash": digest,
                "generated_at": generated_at,
                "actor": args.actor,
                "source_decision": "no_i9_research_candidate_only",
                "status": "CANDIDATE",
                "witness_class": None,
                "ledger_status": "not_submitted",
            }
        )

    output = {"generated_at": generated_at, "candidates": candidates}
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(output, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
    else:
        print(json.dumps(output, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

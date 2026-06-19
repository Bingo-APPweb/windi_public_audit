#!/usr/bin/env python3
"""Check that Participation Layer index references exist."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


DOC_RE = re.compile(r"`([^`]+\.md)`")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs-dir", default="docs")
    parser.add_argument("--index", default="docs/PARTICIPATION-LAYER-INDEX-001.md")
    args = parser.parse_args()

    docs_dir = Path(args.docs_dir)
    index_path = Path(args.index)
    text = index_path.read_text(encoding="utf-8")
    refs = sorted(set(DOC_RE.findall(text)))

    missing = []
    for ref in refs:
        exists = (docs_dir / ref).exists()
        print(f"{'OK' if exists else 'MISSING'} {ref}")
        if not exists:
            missing.append(ref)

    print(f"SUMMARY refs={len(refs)} missing={len(missing)}")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())

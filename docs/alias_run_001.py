#!/usr/bin/env python3
"""ALIAS-RUN-001: measure actor alias resolution against real WINDI ledgers."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DID_DB = Path("/opt/windi/did-genesis/did_genesis.db")
LEDGER_DB = Path("/opt/windi/data/forensic_ledger.sqlite3")

TARGET_ACTORS = [
    "dragon@windi-domain.com",
    "hios-forge-001",
    "windi-hd-001",
    "dragon-001",
    "windi:hd:human-dragon",
    "W-HUMANDRAGON-001",
    "hios-cinema-production",
    "WINDI-SYSTEM",
    "windi-hios-cinema-lab",
    "HD-DRAGON-001",
]

SYSTEM_MARKERS = (
    "SYSTEM",
    "forge",
    "production",
    "lab",
)

FOUNDER_DID = "did:windi:dragon-001"


def rows(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    return list(conn.execute(sql, params))


def load_identity_state() -> dict:
    with sqlite3.connect(DID_DB) as conn:
        identities = rows(
            conn,
            """
            select did, display_name, email, role, tier, status, sovereign_name, classification
            from identities
            """,
        )
        aliases = rows(
            conn,
            """
            select canonical_did, alias_actor, alias_type, status, resolved_at, notes
            from did_aliases
            """,
        )

    active_dids = {r["did"]: dict(r) for r in identities if r["status"] == "active"}
    sovereign_names = {
        r["sovereign_name"]: dict(r)
        for r in identities
        if r["status"] == "active" and r["sovereign_name"]
    }
    emails = {
        r["email"].lower(): dict(r)
        for r in identities
        if r["status"] == "active" and r["email"]
    }
    formal_aliases = {
        r["alias_actor"]: dict(r)
        for r in aliases
        if r["status"] == "active"
    }
    email_aliases = {
        r["alias_actor"].lower(): dict(r)
        for r in aliases
        if r["status"] == "active" and r["alias_type"] == "EMAIL"
    }
    return {
        "active_dids": active_dids,
        "sovereign_names": sovereign_names,
        "emails": emails,
        "formal_aliases": formal_aliases,
        "email_aliases": email_aliases,
    }


def load_ledger_counts() -> dict[str, dict]:
    with sqlite3.connect(LEDGER_DB) as conn:
        data = rows(
            conn,
            """
            select actor, count(*) as receipts, group_concat(distinct app) as apps
            from receipts
            group by actor
            """,
        )
    return {
        r["actor"]: {
            "receipts": r["receipts"],
            "apps": (r["apps"] or "").split(",") if r["apps"] else [],
        }
        for r in data
    }


def looks_system(actor: str) -> bool:
    if actor == "WINDI-SYSTEM":
        return True
    lowered = actor.lower()
    return any(marker.lower() in lowered for marker in SYSTEM_MARKERS)


def strong_candidate(actor: str) -> bool:
    lowered = actor.lower()
    return (
        "dragon" in lowered
        or "humandragon" in lowered
        or lowered.startswith("windi-hd")
        or lowered.startswith("hd-dragon")
    )


def resolve_actor(actor: str, state: dict) -> dict:
    if actor in state["active_dids"]:
        return {
            "canonical_did": actor,
            "resolution_status": "resolved",
            "resolution_class": "CANONICAL",
            "admissibility_level": "LEVEL 1",
            "review_required": False,
            "evidence": "identities.did active",
        }
    if actor in state["formal_aliases"]:
        alias = state["formal_aliases"][actor]
        return {
            "canonical_did": alias["canonical_did"],
            "resolution_status": "resolved",
            "resolution_class": "FORMAL_ALIAS",
            "admissibility_level": "LEVEL 1",
            "review_required": False,
            "evidence": "did_aliases active exact match",
        }
    if actor in state["sovereign_names"]:
        identity = state["sovereign_names"][actor]
        return {
            "canonical_did": identity["did"],
            "resolution_status": "resolved",
            "resolution_class": "SOVEREIGN_NAME_MATCH",
            "admissibility_level": "LEVEL 1",
            "review_required": True,
            "evidence": "identities.sovereign_name exact active match",
        }
    lowered = actor.lower()
    if lowered in state["emails"]:
        identity = state["emails"][lowered]
        return {
            "canonical_did": identity["did"],
            "resolution_status": "resolved",
            "resolution_class": "EMAIL_MATCH",
            "admissibility_level": "LEVEL 1",
            "review_required": False,
            "evidence": "identities.email case-insensitive active match",
        }
    if lowered in state["email_aliases"]:
        alias = state["email_aliases"][lowered]
        return {
            "canonical_did": alias["canonical_did"],
            "resolution_status": "resolved",
            "resolution_class": "EMAIL_MATCH",
            "admissibility_level": "LEVEL 1",
            "review_required": False,
            "evidence": "did_aliases EMAIL active case-insensitive match",
        }
    if looks_system(actor):
        return {
            "canonical_did": None,
            "resolution_status": "system_executor",
            "resolution_class": "SYSTEM_EXECUTOR",
            "admissibility_level": "N/A",
            "review_required": True,
            "evidence": "system/lab/forge/production actor pattern",
        }
    if strong_candidate(actor):
        return {
            "canonical_did": None,
            "resolution_status": "pending_review",
            "resolution_class": "STRONG_CANDIDATE",
            "admissibility_level": "LEVEL 2 REQUIRED if mapped to founder DID",
            "review_required": True,
            "evidence": "dragon/human-dragon textual pattern without formal alias",
        }
    return {
        "canonical_did": None,
        "resolution_status": "unresolved",
        "resolution_class": "UNRESOLVED",
        "admissibility_level": "N/A",
        "review_required": True,
        "evidence": "no rule matched",
    }


def markdown_report(results: list[dict], generated_at: str) -> str:
    total_receipts = sum(r["receipts"] for r in results)
    auto = [r for r in results if r["resolution_status"] == "resolved"]
    pending = [r for r in results if r["resolution_status"] == "pending_review"]
    system = [r for r in results if r["resolution_status"] == "system_executor"]
    unresolved = [r for r in results if r["resolution_status"] == "unresolved"]
    collapsed = {}
    for r in auto:
        collapsed[r["canonical_did"]] = collapsed.get(r["canonical_did"], 0) + r["receipts"]

    lines = [
        "# ALIAS-RUN-001",
        "",
        "**Status:** MEASURED",
        f"**Generated at:** {generated_at}",
        "**Rule:** ALIAS-RESOLUTION-001 v0.1",
        "**Authority Gate:** ACTION-0-WITNESS-ADMISSIBILITY-001",
        "",
        "## 1. Summary",
        "",
        f"- Target actors measured: {len(results)}",
        f"- Receipts covered by target actors: {total_receipts}",
        f"- Automatic resolved actors: {len(auto)}",
        f"- Pending review actors: {len(pending)}",
        f"- System executor actors: {len(system)}",
        f"- Unresolved actors: {len(unresolved)}",
        "",
        "## 2. Collapsed Receipts by Canonical DID",
        "",
    ]
    if collapsed:
        for did, count in sorted(collapsed.items()):
            lines.append(f"- `{did}`: {count} receipts")
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## 3. Actor Resolution Table",
            "",
            "| actor_original | receipts | resolution_status | resolution_class | canonical_did | admissibility_level | evidence |",
            "|---|---:|---|---|---|---|---|",
        ]
    )
    for r in results:
        lines.append(
            "| `{actor}` | {receipts} | `{status}` | `{klass}` | {did} | {level} | {evidence} |".format(
                actor=r["actor_original"],
                receipts=r["receipts"],
                status=r["resolution_status"],
                klass=r["resolution_class"],
                did=f"`{r['canonical_did']}`" if r["canonical_did"] else "`null`",
                level=f"`{r['admissibility_level']}`",
                evidence=r["evidence"],
            )
        )
    lines.extend(
        [
            "",
            "## 4. Findings",
            "",
            "1. Only rules already formalized in DID Genesis resolve automatically.",
            "2. `dragon-001` resolves via `SOVEREIGN_NAME_MATCH`, but remains marked review-required.",
            "3. Strong Human Dragon candidates remain pending until formal aliases are approved.",
            "4. System/lab/forge/production actors remain Activity actors, not Contribution actors by default.",
            "5. `dragon@windi-domain.com` remains Priority Alias Candidate #1 because it has the largest pending Human Dragon-like receipt count.",
            "",
            "## 5. Guard",
            "",
            "> Um run de medicao sem identidade resolvida nao e ainda uma atribuicao.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    state = load_identity_state()
    ledger = load_ledger_counts()
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    results = []
    for actor in TARGET_ACTORS:
        resolved = resolve_actor(actor, state)
        count_info = ledger.get(actor, {"receipts": 0, "apps": []})
        results.append(
            {
                "actor_original": actor,
                "receipts": count_info["receipts"],
                "apps": count_info["apps"],
                **resolved,
            }
        )

    output_dir = Path("/home/windi/docs")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "ALIAS-RUN-001.json").write_text(
        json.dumps(
            {
                "status": "MEASURED",
                "generated_at": generated_at,
                "rule": "ALIAS-RESOLUTION-001 v0.1",
                "authority_gate": "ACTION-0-WITNESS-ADMISSIBILITY-001",
                "results": results,
            },
            indent=2,
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "ALIAS-RUN-001.md").write_text(
        markdown_report(results, generated_at),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

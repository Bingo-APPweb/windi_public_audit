#!/usr/bin/env python3
"""
W-DID-GENESIS Ledger Client
===========================
P0 Implementation — §299 PLAYGROUND-MUSTER-001

Handles birth_receipt emission to Forensic Ledger :8101
with G2 atomicity guarantees (no orphan receipts).

Liga IA+H · Kempten, Bavaria · 2026
"""

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple

import httpx

# Configuration
LEDGER_URL = os.environ.get("LEDGER_URL", "http://127.0.0.1:8101")
SECRET_KEY = os.environ.get("WINDI_DID_SECRET", "windi-did-genesis-dragon-2026")
TIMEOUT_POST = 10.0
TIMEOUT_GET = 5.0

log = logging.getLogger("w-did-genesis.ledger")


def generate_birth_lookup_key(canonical_did: str) -> str:
    """
    Generate deterministic lookup key for a DID.
    Used for idempotent receipt queries.

    NOTE: This is NOT anti-forjamento (see P1-AUTH debt).
    It's purely for lookup/reconciliation.
    """
    return hashlib.sha256(f"{SECRET_KEY}:birth:{canonical_did}".encode()).hexdigest()[:32]


def generate_birth_receipt_id(canonical_did: str) -> str:
    """
    Generate deterministic receipt ID for a birth.
    Format: WINDI-BIRTH-{did_short}
    """
    did_short = canonical_did.replace("did:windi:", "")
    return f"WINDI-BIRTH-{did_short}"


def generate_failure_receipt_id(canonical_did: str) -> str:
    """
    Generate deterministic receipt ID for a birth failure.
    Format: WINDI-BIRTH-FAILURE-{did_short}
    """
    did_short = canonical_did.replace("did:windi:", "")
    return f"WINDI-BIRTH-FAILURE-{did_short}"


def build_birth_receipt(
    canonical_did: str,
    sovereign_name: str,
    email: str,
    birth_timestamp: str
) -> Dict[str, Any]:
    """
    Build the birth_receipt payload for the Ledger.

    doc_type: birth_receipt — proves successful birth.
    """
    birth_lookup_key = generate_birth_lookup_key(canonical_did)
    receipt_id = generate_birth_receipt_id(canonical_did)

    # Content for hash (deterministic)
    content_for_hash = json.dumps({
        "canonical_did": canonical_did,
        "sovereign_name": sovereign_name,
        "email_hash": hashlib.sha256(email.lower().encode()).hexdigest(),
        "birth_timestamp": birth_timestamp,
        "birth_lookup_key": birth_lookup_key
    }, sort_keys=True)

    content_hash = f"sha256:{hashlib.sha256(content_for_hash.encode()).hexdigest()}"

    return {
        "id": receipt_id,
        "doc_type": "birth_receipt",
        "wallet_id": canonical_did,
        "actor": "did:windi:dragon-001",  # Human Dragon (P1: create Service DID)
        "schema_version": "1.0",
        "app": "w-did-genesis",
        "doc_name": f"Birth Certificate: {sovereign_name}",
        "governance_level": "HIGH",
        "content_hash": content_hash,
        "sge_score": 0.95,
        "metadata": {
            "birth_origin": "W-DID-GENESIS-8096",
            "birth_method": "passphrase",  # Future: "ed25519"
            "tier_at_birth": "SEED",
            "sovereign_name": sovereign_name
        }
    }


def build_failure_receipt(
    canonical_did: str,
    failure_cause: str,
    attempted_at: str,
    failed_at: str
) -> Dict[str, Any]:
    """
    Build the birth_failure receipt payload for the Ledger.

    doc_type: birth_failure — proves failed birth (transparent).
    Cause is PUBLIC (not hashed) per Human Dragon decision.
    """
    birth_lookup_key = generate_birth_lookup_key(canonical_did)
    receipt_id = generate_failure_receipt_id(canonical_did)

    # Content for hash (aligned with Contenção 3)
    content_for_hash = json.dumps({
        "canonical_did": canonical_did,
        "failure_cause": failure_cause,
        "failure_timestamp": failed_at,
        "birth_lookup_key": birth_lookup_key
    }, sort_keys=True)

    content_hash = f"sha256:{hashlib.sha256(content_for_hash.encode()).hexdigest()}"

    return {
        "id": receipt_id,
        "doc_type": "birth_failure",
        "wallet_id": canonical_did,
        "actor": "did:windi:dragon-001",  # Human Dragon (P1: create Service DID)
        "schema_version": "1.0",
        "app": "w-did-genesis",
        "doc_name": f"Birth Failure: {canonical_did}",
        "governance_level": "LOW",
        "content_hash": content_hash,
        "sge_score": 0.5,
        "metadata": {
            "cause": failure_cause,  # PUBLIC: ledger_unreachable | ledger_confirmed_404 | expired_after_ttl
            "attempted_at": attempted_at,
            "failed_at": failed_at
        }
    }


def check_receipt_exists(receipt_id: str) -> Tuple[bool, Optional[Dict]]:
    """
    Check if a receipt exists in the Ledger.

    Returns:
        (exists: bool, receipt: Optional[Dict])

    G2 Guarantee: This is idempotent and safe to call multiple times.
    """
    try:
        with httpx.Client(timeout=TIMEOUT_GET) as client:
            resp = client.get(f"{LEDGER_URL}/api/receipts/{receipt_id}")

            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok") and data.get("receipt"):
                    return (True, data["receipt"])

            elif resp.status_code == 404:
                # Confirmed absent (not infra error)
                return (False, None)

            else:
                # Unexpected response — treat as unreachable
                log.warning(f"Unexpected Ledger response: {resp.status_code}")
                raise httpx.RequestError(f"Unexpected status: {resp.status_code}")

    except httpx.RequestError as e:
        log.warning(f"Ledger unreachable during check: {e}")
        raise  # Let caller handle

    return (False, None)


def post_receipt(receipt: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Post a receipt to the Ledger.

    Returns:
        (success: bool, receipt_id: Optional[str])

    G2 Guarantee: Caller must handle failure atomically.
    """
    try:
        with httpx.Client(timeout=TIMEOUT_POST) as client:
            resp = client.post(
                f"{LEDGER_URL}/api/receipts",
                json=receipt
            )

            data = resp.json()

            if data.get("ok"):
                return (True, data.get("id"))
            else:
                log.error(f"Ledger POST failed: {data}")
                return (False, None)

    except httpx.RequestError as e:
        log.warning(f"Ledger unreachable during POST: {e}")
        raise  # Let caller handle


def seal_birth(
    canonical_did: str,
    sovereign_name: str,
    email: str,
    birth_timestamp: str
) -> Tuple[str, str]:
    """
    Attempt to seal a birth in the Ledger.

    Returns:
        (status: str, receipt_id: str)

        status: 'sealed' | 'pending' | 'failed'

    G2 Atomicity: If Ledger is down, checks if receipt exists before failing.
    """
    receipt = build_birth_receipt(canonical_did, sovereign_name, email, birth_timestamp)
    receipt_id = receipt["id"]

    try:
        # Try to POST the receipt
        success, returned_id = post_receipt(receipt)

        if success:
            log.info(f"Birth sealed: {canonical_did} -> {receipt_id}")
            return ("sealed", receipt_id)
        else:
            # POST returned error — check if it already exists (idempotency)
            try:
                exists, _ = check_receipt_exists(receipt_id)
                if exists:
                    log.info(f"Birth already sealed (idempotent): {canonical_did}")
                    return ("sealed", receipt_id)
            except httpx.RequestError:
                pass

            return ("failed", receipt_id)

    except httpx.RequestError:
        # Ledger unreachable during POST — check if it exists anyway
        # (handles case where POST succeeded but response was lost)
        try:
            exists, _ = check_receipt_exists(receipt_id)
            if exists:
                log.info(f"Birth reconciled (POST lost, receipt exists): {canonical_did}")
                return ("sealed", receipt_id)
        except httpx.RequestError:
            pass

        # Truly unreachable — return pending
        log.warning(f"Birth pending (Ledger unreachable): {canonical_did}")
        return ("pending", receipt_id)


# ══════════════════════════════════════════════════════════════════════════════
# §W-RAG-MITIGATION-001 — SUSPEND/RESTORE RECEIPTS
# DOUTRINA-DID-REVOGACAO-001 (pending seal)
# ══════════════════════════════════════════════════════════════════════════════

def generate_suspend_receipt_id(target_did: str, timestamp: str) -> str:
    """
    Generate unique receipt ID for a suspension.
    Format: WINDI-DID-SUSPEND-{timestamp}-{did_hash}
    """
    ts_short = timestamp.replace("-", "").replace(":", "").replace("T", "")[:14]
    did_hash = hashlib.sha256(target_did.encode()).hexdigest()[:8].upper()
    return f"WINDI-DID-SUSPEND-{ts_short}-{did_hash}"


def generate_restore_receipt_id(target_did: str, timestamp: str) -> str:
    """
    Generate unique receipt ID for a restoration.
    Format: WINDI-DID-RESTORE-{timestamp}-{did_hash}
    """
    ts_short = timestamp.replace("-", "").replace(":", "").replace("T", "")[:14]
    did_hash = hashlib.sha256(target_did.encode()).hexdigest()[:8].upper()
    return f"WINDI-DID-RESTORE-{ts_short}-{did_hash}"


def build_suspend_receipt(
    target_did: str,
    target_tier: str,
    suspended_by: str,
    suspended_by_tier: str,
    reason: str,
    authorization: str,
    suspended_at: str,
    sessions_invalidated: int,
    is_self_suspension: bool = False
) -> Dict[str, Any]:
    """
    Build the suspend_receipt payload for the Ledger.

    doc_type: did_suspend — proves DID was suspended.

    §W-RAG-MITIGATION-001 Self-Suspension Rule:
    - When is_self_suspension=True, actor becomes "w-did-genesis"
    - The actual requester goes in on_behalf_of
    - This ensures SEED self-suspensions get sealed (SEED DIDs aren't in Ledger registry)

    Constitutional principle:
    "When the holder is not a recognized actor in the Ledger,
     the service seals as technical actor and preserves the human in on_behalf_of."
    """
    receipt_id = generate_suspend_receipt_id(target_did, suspended_at)

    # Determine actor based on self-suspension
    # §W-RAG-MITIGATION-001: Self-suspension tracking
    # Note: Ledger D5 semantic (wallet_id→actor) means actor column shows target_did
    # The human requester is preserved in metadata.on_behalf_of for full audit trail
    if is_self_suspension:
        ledger_actor = "w-did-genesis@windi-domain.com"  # For actor validation (D5 overwrites)
        on_behalf_of = suspended_by  # The human who requested (preserved for audit)
        operation = "self_suspend"
    else:
        ledger_actor = suspended_by
        on_behalf_of = None
        operation = "suspend"

    # Content for hash (deterministic, auditable)
    content_for_hash = json.dumps({
        "target_did": target_did,
        "target_tier": target_tier,
        "suspended_by": suspended_by,
        "suspended_by_tier": suspended_by_tier,
        "on_behalf_of": on_behalf_of,
        "reason": reason,
        "authorization": authorization,
        "suspended_at": suspended_at,
        "sessions_invalidated": sessions_invalidated,
        "is_self_suspension": is_self_suspension
    }, sort_keys=True)

    content_hash = f"sha256:{hashlib.sha256(content_for_hash.encode()).hexdigest()}"

    metadata = {
        "operation": operation,
        "target_did": target_did,
        "target_tier": target_tier,
        "suspended_by": suspended_by,
        "suspended_by_tier": suspended_by_tier,
        "reason": reason,
        "authorization": authorization,
        "sessions_invalidated": sessions_invalidated
    }

    # Add on_behalf_of only for self-suspensions (never null when present)
    if is_self_suspension:
        metadata["on_behalf_of"] = on_behalf_of
        metadata["requested_by"] = on_behalf_of

    return {
        "id": receipt_id,
        "doc_type": "did_suspend",
        "wallet_id": target_did,
        "actor": ledger_actor,
        "schema_version": "1.0",
        "app": "w-did-genesis",
        "doc_name": f"DID {'Self-' if is_self_suspension else ''}Suspension: {target_did}",
        "governance_level": "HIGH",
        "content_hash": content_hash,
        "sge_score": 0.95,
        "metadata": metadata
    }


def build_restore_receipt(
    target_did: str,
    target_tier: str,
    restored_by: str,
    restored_by_tier: str,
    reason: str,
    evidence: Optional[str],
    authorization: str,
    restored_at: str
) -> Dict[str, Any]:
    """
    Build the restore_receipt payload for the Ledger.

    doc_type: did_restore — proves DID was restored.
    """
    receipt_id = generate_restore_receipt_id(target_did, restored_at)

    # Content for hash (deterministic, auditable)
    content_for_hash = json.dumps({
        "target_did": target_did,
        "target_tier": target_tier,
        "restored_by": restored_by,
        "restored_by_tier": restored_by_tier,
        "reason": reason,
        "evidence": evidence,
        "authorization": authorization,
        "restored_at": restored_at
    }, sort_keys=True)

    content_hash = f"sha256:{hashlib.sha256(content_for_hash.encode()).hexdigest()}"

    return {
        "id": receipt_id,
        "doc_type": "did_restore",
        "wallet_id": target_did,
        "actor": restored_by,
        "schema_version": "1.0",
        "app": "w-did-genesis",
        "doc_name": f"DID Restoration: {target_did}",
        "governance_level": "HIGH",
        "content_hash": content_hash,
        "sge_score": 0.95,
        "metadata": {
            "operation": "restore",
            "target_did": target_did,
            "target_tier": target_tier,
            "restored_by": restored_by,
            "restored_by_tier": restored_by_tier,
            "reason": reason,
            "evidence": evidence,
            "authorization": authorization,
            "asymmetry_note": "Restoration requires ORACLE authority. Self-restore is forbidden."
        }
    }


def seal_suspend(
    target_did: str,
    target_tier: str,
    suspended_by: str,
    suspended_by_tier: str,
    reason: str,
    authorization: str,
    suspended_at: str,
    sessions_invalidated: int,
    is_self_suspension: bool = False
) -> Tuple[str, str]:
    """
    Seal a DID suspension in the Ledger.

    Returns:
        (status: str, receipt_id: str)
        status: 'sealed' | 'pending' | 'failed'

    §W-RAG-MITIGATION-001:
    When is_self_suspension=True, uses w-did-genesis as actor
    to ensure SEED self-suspensions get sealed in the Ledger.
    """
    receipt = build_suspend_receipt(
        target_did, target_tier, suspended_by, suspended_by_tier,
        reason, authorization, suspended_at, sessions_invalidated,
        is_self_suspension=is_self_suspension
    )
    receipt_id = receipt["id"]
    # Note: Ledger D5 semantic maps wallet_id→actor, so actor column shows target_did
    # The actual requester is preserved in metadata.on_behalf_of for self-suspensions

    try:
        success, returned_id = post_receipt(receipt)

        if success:
            log.info(f"Suspend sealed: {target_did} by {suspended_by} -> {receipt_id}")
            return ("sealed", receipt_id)
        else:
            # Check if already exists (idempotency)
            try:
                exists, _ = check_receipt_exists(receipt_id)
                if exists:
                    log.info(f"Suspend already sealed (idempotent): {target_did}")
                    return ("sealed", receipt_id)
            except httpx.RequestError:
                pass
            return ("failed", receipt_id)

    except httpx.RequestError:
        # Ledger unreachable — check if exists
        try:
            exists, _ = check_receipt_exists(receipt_id)
            if exists:
                log.info(f"Suspend reconciled (POST lost, receipt exists): {target_did}")
                return ("sealed", receipt_id)
        except httpx.RequestError:
            pass

        log.warning(f"Suspend pending (Ledger unreachable): {target_did}")
        return ("pending", receipt_id)


def seal_restore(
    target_did: str,
    target_tier: str,
    restored_by: str,
    restored_by_tier: str,
    reason: str,
    evidence: Optional[str],
    authorization: str,
    restored_at: str
) -> Tuple[str, str]:
    """
    Seal a DID restoration in the Ledger.

    Returns:
        (status: str, receipt_id: str)
        status: 'sealed' | 'pending' | 'failed'
    """
    receipt = build_restore_receipt(
        target_did, target_tier, restored_by, restored_by_tier,
        reason, evidence, authorization, restored_at
    )
    receipt_id = receipt["id"]

    try:
        success, returned_id = post_receipt(receipt)

        if success:
            log.info(f"Restore sealed: {target_did} by {restored_by} -> {receipt_id}")
            return ("sealed", receipt_id)
        else:
            try:
                exists, _ = check_receipt_exists(receipt_id)
                if exists:
                    log.info(f"Restore already sealed (idempotent): {target_did}")
                    return ("sealed", receipt_id)
            except httpx.RequestError:
                pass
            return ("failed", receipt_id)

    except httpx.RequestError:
        try:
            exists, _ = check_receipt_exists(receipt_id)
            if exists:
                log.info(f"Restore reconciled (POST lost, receipt exists): {target_did}")
                return ("sealed", receipt_id)
        except httpx.RequestError:
            pass

        log.warning(f"Restore pending (Ledger unreachable): {target_did}")
        return ("pending", receipt_id)

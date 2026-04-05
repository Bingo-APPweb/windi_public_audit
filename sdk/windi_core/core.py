"""
WINDI SDK v1.0 — Core Functions

The 4 Sacred Functions of the WINDI Core Protocol:

1. seal()      - I9 Gate: Human approval before commitment
2. ledger()    - I11: Eternal anchoring with cryptographic proof
3. render_jmpg() - Visual proof card generation
4. distribute() - Multi-channel distribution

"Escala não vem de fazer tudo igual.
 Vem de garantir que tudo termina da mesma forma."

Liga IA+H · Kempten, Bavaria · 05 Abril 2026
"""

import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Union
import httpx

from .models import SealResult, LedgerReceipt, JMPGResult, DistributeResult

# ═══════════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════════

WINDI_BASE_URL = "https://windi-domain.com"
LEDGER_URL = "http://127.0.0.1:8101"
COMM_URL = "http://127.0.0.1:8132"
VERIFY_URL = f"{WINDI_BASE_URL}/verify-public"

DEFAULT_TIMEOUT = 30.0


# ═══════════════════════════════════════════════════════════════════════════════
# 1. SEAL — I9 Gate (Human Approval)
# ═══════════════════════════════════════════════════════════════════════════════

async def seal(
    artifact: Union[str, Path, bytes],
    wallet_id: str,
    human_approved: bool = True,
    title: Optional[str] = None,
) -> SealResult:
    """
    Prepare an artifact for sealing (I9 Gate).

    This function computes the content hash and prepares the artifact
    for ledger anchoring. The human_approved flag MUST be True for
    the seal to be valid (I9 invariant).

    Args:
        artifact: Path to file, or raw bytes
        wallet_id: DID of the actor
        human_approved: Must be True (I9 requires human decision)
        title: Optional title for the artifact

    Returns:
        SealResult with content_hash ready for ledger anchoring

    Example:
        result = await seal("/path/to/video.mp4", "did:windi:user:001")
        if result.ready_for_ledger:
            receipt = await ledger(result)
    """
    # I9: Human approval is mandatory
    if not human_approved:
        return SealResult(
            ok=False,
            error="I9 violation: human_approved must be True"
        )

    try:
        # Get artifact bytes
        if isinstance(artifact, (str, Path)):
            artifact_path = Path(artifact)
            if not artifact_path.exists():
                return SealResult(ok=False, error=f"Artifact not found: {artifact}")
            with open(artifact_path, "rb") as f:
                content = f.read()
            path_str = str(artifact_path)
        else:
            content = artifact
            path_str = None

        # Compute SHA-256 hash
        content_hash = hashlib.sha256(content).hexdigest()

        return SealResult(
            ok=True,
            content_hash=content_hash,
            artifact_path=path_str,
            wallet_id=wallet_id,
            human_approved=True,
            timestamp=datetime.now(),
        )

    except Exception as e:
        return SealResult(ok=False, error=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# 2. LEDGER — I11 (Eternal Anchoring)
# ═══════════════════════════════════════════════════════════════════════════════

async def ledger(
    seal_result: SealResult,
    doc_type: str = "artifact",
    doc_name: Optional[str] = None,
    app: str = "windi-sdk",
    governance_level: str = "HIGH",
) -> LedgerReceipt:
    """
    Anchor a sealed artifact to the WINDI Forensic Ledger (I11).

    This creates an immutable receipt that can be verified publicly.
    Once anchored, the proof cannot be modified or deleted.

    Args:
        seal_result: Result from seal() function
        doc_type: Type of document/artifact
        doc_name: Name for the artifact
        app: Source application identifier
        governance_level: HIGH, MEDIUM, or LOW

    Returns:
        LedgerReceipt with receipt_id and verify_url

    Example:
        receipt = await ledger(seal_result, doc_type="video")
        print(f"Verify at: {receipt.verify_url}")
    """
    if not seal_result.ready_for_ledger:
        return LedgerReceipt(
            ok=False,
            error="Seal not ready for ledger (missing hash or approval)"
        )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LEDGER_URL}/api/receipts",
                json={
                    "actor": seal_result.wallet_id,
                    "app": app,
                    "doc_type": doc_type,
                    "doc_name": doc_name or f"Artifact-{seal_result.content_hash[:8]}",
                    "content_hash": f"sha256:{seal_result.content_hash}",
                    "governance_level": governance_level,
                    "invariants": ["I9", "I11"],
                },
                timeout=DEFAULT_TIMEOUT,
            )

            if response.status_code == 200:
                data = response.json()
                receipt_id = data.get("receipt_id")
                return LedgerReceipt(
                    ok=True,
                    receipt_id=receipt_id,
                    content_hash=seal_result.content_hash,
                    verify_url=f"{VERIFY_URL}/?id={receipt_id}",
                    timestamp=datetime.now(),
                    governance_level=governance_level,
                )
            else:
                return LedgerReceipt(
                    ok=False,
                    error=f"Ledger error: {response.status_code} - {response.text}"
                )

    except Exception as e:
        return LedgerReceipt(ok=False, error=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# 3. RENDER_JMPG — Visual Proof Card
# ═══════════════════════════════════════════════════════════════════════════════

async def render_jmpg(
    receipt_id: str,
    title: Optional[str] = None,
    profile: str = "telegram_square",
    source_app: Optional[str] = None,
) -> JMPGResult:
    """
    Render a JMPG proof card for a receipt.

    Creates a visual representation of the proof that can be
    shared on social media, email, or any communication channel.

    Args:
        receipt_id: WINDI receipt ID
        title: Optional title for the card
        profile: Render profile (telegram_square, telegram_landscape)
        source_app: Source application name

    Returns:
        JMPGResult with image_url

    Example:
        jmpg = await render_jmpg("WINDI-VDCUT-20260405-XXXX")
        print(f"Image: {jmpg.image_url}")
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{COMM_URL}/comm/render/jmpg",
                json={
                    "receipt_id": receipt_id,
                    "profile": profile,
                    "title": title,
                    "source_app": source_app,
                },
                timeout=DEFAULT_TIMEOUT,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    return JMPGResult(
                        ok=True,
                        receipt_id=receipt_id,
                        image_path=data.get("image_path"),
                        image_url=data.get("image_url"),
                        verify_url=data.get("verify_url"),
                        profile=profile,
                    )
                else:
                    return JMPGResult(ok=False, error=data.get("error"))
            else:
                return JMPGResult(
                    ok=False,
                    error=f"Render error: {response.status_code}"
                )

    except Exception as e:
        return JMPGResult(ok=False, error=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# 4. DISTRIBUTE — Multi-Channel Distribution
# ═══════════════════════════════════════════════════════════════════════════════

async def distribute(
    receipt_id: str,
    channel: str = "telegram",
    chat_id: Optional[str] = None,
    title: Optional[str] = None,
    lang: str = "EN",
    communique: bool = True,
) -> DistributeResult:
    """
    Distribute a proof card via communication channels.

    Sends the JMPG proof card with institutional communiqué text
    to the specified channel (Telegram, Email, etc.).

    Args:
        receipt_id: WINDI receipt ID
        channel: Distribution channel ("telegram")
        chat_id: Target chat/channel ID (required for Telegram)
        title: Optional title for the message
        lang: Language for communiqué (PT, EN, DE)
        communique: Use institutional communiqué format

    Returns:
        DistributeResult with channel-specific result

    Example:
        result = await distribute(
            "WINDI-VDCUT-20260405-XXXX",
            channel="telegram",
            chat_id="8618440285",
            lang="PT"
        )
    """
    if channel == "telegram" and not chat_id:
        return DistributeResult(
            ok=False,
            channel=channel,
            error="chat_id required for Telegram"
        )

    try:
        endpoint = "/comm/communique" if communique else "/comm/distribute"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{COMM_URL}{endpoint}",
                json={
                    "receipt_id": receipt_id,
                    "channel": channel,
                    "chat_id": chat_id,
                    "title": title,
                    "lang": lang,
                },
                timeout=DEFAULT_TIMEOUT,
            )

            if response.status_code == 200:
                data = response.json()
                telegram_result = data.get("telegram_result", {})
                return DistributeResult(
                    ok=data.get("ok", False),
                    channel=channel,
                    receipt_id=receipt_id,
                    image_url=data.get("image_url"),
                    message_id=telegram_result.get("result", {}).get("message_id"),
                    telegram_result=telegram_result,
                    error=data.get("error"),
                )
            else:
                return DistributeResult(
                    ok=False,
                    channel=channel,
                    error=f"Distribute error: {response.status_code}"
                )

    except Exception as e:
        return DistributeResult(ok=False, channel=channel, error=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# 5. PUBLISH — Public Distribution (§137 / §122.4 Compliant)
# ═══════════════════════════════════════════════════════════════════════════════

async def publish(
    receipt_id: str,
    channel: str = "telegram",
    chat_id: str = None,
    title: Optional[str] = None,
    lang: str = "EN",
) -> DistributeResult:
    """
    Publish proof to PUBLIC channels (§137 / §122.4 Compliant).

    SENDS LINK ONLY — NO FILES.

    This function is for PUBLIC distribution where hash integrity matters.
    Telegram transcodes images, breaking SHA-256 verification.
    For private chats, use distribute() instead.

    "O canal Telegram não transmite ficheiros. Transmite acesso."

    Args:
        receipt_id: WINDI receipt ID
        channel: Distribution channel ("telegram")
        chat_id: Target channel ID (required)
        title: Optional title for the post
        lang: Language for post (PT, EN, DE)

    Returns:
        DistributeResult with channel-specific result

    Example:
        # Publish to WINDI public channel
        result = await publish(
            "WINDI-VDCUT-20260405-XXXX",
            chat_id="@windi_public",
            lang="EN"
        )
    """
    if channel == "telegram" and not chat_id:
        return DistributeResult(
            ok=False,
            channel=channel,
            error="chat_id required for public Telegram publishing"
        )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{COMM_URL}/comm/publish",
                json={
                    "receipt_id": receipt_id,
                    "channel": channel,
                    "chat_id": chat_id,
                    "title": title,
                    "lang": lang,
                },
                timeout=DEFAULT_TIMEOUT,
            )

            if response.status_code == 200:
                data = response.json()
                return DistributeResult(
                    ok=data.get("ok", False),
                    channel=channel,
                    receipt_id=receipt_id,
                    image_url=data.get("jmpg_url"),  # URL only, not sent
                    telegram_result=data.get("telegram_result"),
                    error=data.get("error"),
                )
            else:
                return DistributeResult(
                    ok=False,
                    channel=channel,
                    error=f"Publish error: {response.status_code}"
                )

    except Exception as e:
        return DistributeResult(ok=False, channel=channel, error=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# Convenience: Full Pipeline
# ═══════════════════════════════════════════════════════════════════════════════

async def prove_and_share(
    artifact: Union[str, Path, bytes],
    wallet_id: str,
    title: Optional[str] = None,
    chat_id: Optional[str] = None,
    lang: str = "EN",
) -> dict:
    """
    Complete pipeline: Seal → Ledger → Render → Distribute.

    Convenience function that runs the full WINDI Core Protocol
    in a single call.

    Args:
        artifact: Path to file or bytes
        wallet_id: DID of the actor
        title: Title for the proof
        chat_id: Telegram chat ID (optional)
        lang: Language for communiqué

    Returns:
        Dict with all results from each stage

    Example:
        result = await prove_and_share(
            "/path/to/document.pdf",
            "did:windi:user:001",
            title="Contract signed",
            chat_id="8618440285"
        )
    """
    # 1. Seal
    seal_result = await seal(artifact, wallet_id, human_approved=True, title=title)
    if not seal_result.ok:
        return {"ok": False, "stage": "seal", "error": seal_result.error}

    # 2. Ledger
    receipt = await ledger(seal_result, doc_name=title)
    if not receipt.ok:
        return {"ok": False, "stage": "ledger", "error": receipt.error}

    # 3. Render JMPG
    jmpg = await render_jmpg(receipt.receipt_id, title=title)
    if not jmpg.ok:
        return {"ok": False, "stage": "render", "error": jmpg.error}

    # 4. Distribute (optional)
    distribute_result = None
    if chat_id:
        distribute_result = await distribute(
            receipt.receipt_id,
            chat_id=chat_id,
            title=title,
            lang=lang,
        )

    return {
        "ok": True,
        "seal": seal_result,
        "receipt": receipt,
        "jmpg": jmpg,
        "distribute": distribute_result,
        "verify_url": receipt.verify_url,
        "image_url": jmpg.image_url,
    }

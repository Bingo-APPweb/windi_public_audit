"""
W-PRESENCE-001 — Presence Seal Core Module
============================================
WINDI Publishing House · Kempten, Bavaria
Created: 02 Apr 2026

Módulo core para selagem de momentos de presença.

Filosofia:
    "Presence is not detected. It is declared and sealed."

Princípios:
    - Presença é DECLARADA pelo humano, não detectada pelo sistema
    - Apenas HASH da evidência vai para o Ledger (nunca conteúdo bruto)
    - presence_level é CALCULADO, não escolhido manualmente
    - Payload é DETERMINÍSTICO para hash consistente
    - Ledger down = state FAILED (fail-closed para seal, não para index)

Invariantes:
    I14 — Presence Integrity: "provar que eu estava lá"
    I9  — Autonomy Prohibition: confirmação humana obrigatória
    I11 — Cryptographic Permanence: Ledger = IRREMEDIÁVEL

Hierarquia Probatória:
    P1 = Temporal   (DID + timestamp + intent)
    P2 = Contextual (P1 + evidence)
    P3 = Spatial    (P2 + GPS location)
"""

import hashlib
import json
import uuid
import sqlite3
import re
import requests
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

# ==============================================================================
# CONFIGURAÇÃO
# ==============================================================================

# Database
DB_PATH = Path("/opt/windi/windi-travel/identity-gate/windi_travel_identity.db")

# Ledger endpoint
LEDGER_URL = "http://127.0.0.1:8101/api/receipts"
LEDGER_TIMEOUT = 6  # segundos

# Verify URL base
VERIFY_BASE = "https://windi-domain.com/verify-public/?id="

# ==============================================================================
# DATACLASSES
# ==============================================================================

@dataclass
class Location:
    """Dados de localização."""
    mode: str = "none"      # 'gps' | 'ip' | 'none'
    lat: Optional[float] = None
    lng: Optional[float] = None
    precision_m: Optional[int] = None
    label: Optional[str] = None


@dataclass
class Evidence:
    """Dados de evidência."""
    kind: str = "none"      # 'image' | 'audio' | 'text' | 'none'
    hash: Optional[str] = None   # SHA-256 da evidência
    path: Optional[str] = None   # Path local ou URL
    mime: Optional[str] = None   # MIME type


@dataclass
class PresencePayload:
    """Payload completo para seal."""
    # Identidade
    did: str
    session_id: Optional[str]

    # Timestamps
    declared_at: str        # ISO 8601 UTC

    # Conteúdo
    intent: str
    title: Optional[str]

    # Classificação (calculada)
    presence_level: str     # P1 | P2 | P3

    # Localização
    location: Location

    # Evidência (só hash, nunca conteúdo)
    evidence: Evidence

    # Metadata
    app: str = "windi-travel"
    version: str = "1.0.0"


@dataclass
class SealResult:
    """Resultado da selagem."""
    success: bool
    local_id: Optional[str] = None
    receipt_id: Optional[str] = None
    content_hash: Optional[str] = None
    verify_url: Optional[str] = None
    presence_level: Optional[str] = None
    state: str = "PENDING"
    error: Optional[str] = None


# ==============================================================================
# NORMALIZAÇÃO E IDEMPOTÊNCIA
# ==============================================================================

def normalize_text(text: str) -> str:
    """
    Normaliza texto para hash consistente.

    Operações:
        1. Strip (remove espaços início/fim)
        2. Colapsa múltiplos espaços em um
        3. Remove caracteres de controle

    Args:
        text: Texto original

    Returns:
        Texto normalizado

    Exemplo:
        "  Primeiro   dia  " → "Primeiro dia"
    """
    if not text:
        return ""
    # Strip
    text = text.strip()
    # Colapsar espaços múltiplos
    text = re.sub(r'\s+', ' ', text)
    return text


def check_hash_exists(content_hash: str) -> Optional[str]:
    """
    Verifica se content_hash já existe no índice.

    Garante IDEMPOTÊNCIA: mesmo momento não gera múltiplos receipts.

    Args:
        content_hash: SHA-256 do payload

    Returns:
        receipt_id se existir, None se não
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("""
            SELECT receipt_id FROM presence_moments
            WHERE content_hash = ? AND state = 'SEALED'
        """, (content_hash,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    except sqlite3.Error:
        return None


def generate_backend_timestamp() -> str:
    """
    Gera timestamp no BACKEND.

    CRÍTICO: declared_at é gerado aqui, NÃO confiamos no frontend.

    Returns:
        ISO 8601 UTC sem microsegundos
    """
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# ==============================================================================
# FUNÇÕES CORE
# ==============================================================================

def classify_presence_level(
    intent: str,
    evidence: Evidence,
    location: Location
) -> str:
    """
    Classifica o nível de presença baseado nos dados reais.

    NÃO é input manual — é CALCULADO.

    Hierarquia:
        P1 = DID + timestamp + intent
        P2 = P1 + evidence (image/audio/text)
        P3 = P2 + GPS location

    Args:
        intent: Intenção declarada (obrigatório)
        evidence: Dados de evidência
        location: Dados de localização

    Returns:
        'P1', 'P2', ou 'P3'

    Regras:
        - GPS com lat/lng válidos = P3
        - Evidence com hash válido = P2 (mínimo)
        - Apenas intent = P1
    """
    # P3 requer GPS real (não IP)
    if (location.mode == "gps" and
        location.lat is not None and
        location.lng is not None):
        return "P3"

    # P2 requer evidência com hash
    if (evidence.kind != "none" and
        evidence.hash is not None and
        len(evidence.hash) == 64):  # SHA-256 = 64 hex chars
        return "P2"

    # P1 = default (DID + timestamp + intent)
    return "P1"


def compose_presence_payload(
    did: str,
    intent: str,
    session_id: Optional[str] = None,
    title: Optional[str] = None,
    location: Optional[Dict[str, Any]] = None,
    evidence: Optional[Dict[str, Any]] = None
) -> PresencePayload:
    """
    Compõe payload de presença para selagem.

    CANONICAL PAYLOAD: estrutura FIXA, mesmos campos SEMPRE.
    DETERMINÍSTICO: mesmo input normalizado = mesmo hash.
    TIMESTAMP BACKEND: declared_at gerado aqui, não confiamos no frontend.

    Args:
        did: DID do declarante (obrigatório)
        intent: Intenção declarada (obrigatório)
        session_id: ID da sessão soberana (opcional)
        title: Título do momento (opcional)
        location: Dict com mode, lat, lng, precision_m, label
        evidence: Dict com kind, hash, path, mime

    Returns:
        PresencePayload pronto para hash e seal

    Nota:
        declared_at é SEMPRE gerado no backend.
        Isso garante integridade temporal.
    """
    # TIMESTAMP GERADO NO BACKEND (não confiar no frontend)
    ts = generate_backend_timestamp()

    # NORMALIZAÇÃO DE TEXTO (evita hashes diferentes para mesmo conteúdo)
    normalized_intent = normalize_text(intent)
    normalized_title = normalize_text(title) if title else ""

    # CANONICAL LOCATION (estrutura fixa, mesmo com valores vazios)
    loc = Location(
        mode=location.get("mode", "none") if location else "none",
        lat=location.get("lat") if location else None,
        lng=location.get("lng") if location else None,
        precision_m=location.get("precision_m") if location else None,
        label=normalize_text(location.get("label", "")) if location else ""
    )

    # CANONICAL EVIDENCE (estrutura fixa, NUNCA conteúdo bruto)
    evd = Evidence(
        kind=evidence.get("kind", "none") if evidence else "none",
        hash=evidence.get("hash") if evidence else None,
        path=evidence.get("path") if evidence else None,
        mime=evidence.get("mime", "") if evidence else ""
    )

    # Classificar nível (CALCULADO, não manual)
    level = classify_presence_level(normalized_intent, evd, loc)

    return PresencePayload(
        did=did,
        session_id=session_id or "",  # String vazia, não None (canonical)
        declared_at=ts,
        intent=normalized_intent,
        title=normalized_title,
        presence_level=level,
        location=loc,
        evidence=evd
    )


def calculate_content_hash(payload: PresencePayload) -> str:
    """
    Calcula hash SHA-256 do payload.

    DETERMINÍSTICO: JSON com sorted keys, sem espaços extras.

    Args:
        payload: PresencePayload completo

    Returns:
        Hash SHA-256 como hex string (64 chars)

    Nota:
        O mesmo payload sempre gera o mesmo hash.
        Isso é FUNDAMENTAL para verificação.
    """
    # Converter para dict
    data = asdict(payload)

    # JSON determinístico (sorted keys, sem espaços, sem indent)
    json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))

    # SHA-256
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()


def generate_receipt_id() -> str:
    """
    Gera receipt ID único para o Ledger.

    Formato: WINDI-PRESENCE-YYYYMMDDHHMMSS-XXXX

    Returns:
        Receipt ID string
    """
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    suffix = uuid.uuid4().hex[:6].lower()
    return f"WINDI-PRESENCE-{ts}-{suffix}"


def seal_presence_to_ledger(
    payload: PresencePayload,
    content_hash: str,
    receipt_id: str
) -> Tuple[bool, Optional[str]]:
    """
    Envia presença para o Ledger Forense.

    NUNCA envia evidência bruta — apenas hash.

    Args:
        payload: PresencePayload completo
        content_hash: Hash SHA-256 do payload
        receipt_id: ID único do receipt

    Returns:
        Tuple[success: bool, error: Optional[str]]

    Tratamento de erro:
        - Ledger down = (False, "Ledger unavailable")
        - Timeout = (False, "Timeout")
        - Outro erro = (False, str(error))
    """
    try:
        ledger_payload = {
            "id": receipt_id,
            "actor": payload.did,
            "app": "windi-travel-presence",
            "doc_name": payload.title or f"Presence Seal ({payload.presence_level})",
            "doc_type": "PRESENCE",
            "governance_level": "HIGH",
            "content_hash": f"sha256:{content_hash}",
            "sge_score": 85,
            "invariant": "I14",
            "metadata": json.dumps({
                "presence_level": payload.presence_level,
                "intent": payload.intent[:200],  # Truncar para metadata
                "declared_at": payload.declared_at,
                "location_mode": payload.location.mode,
                "location_label": payload.location.label,
                "evidence_kind": payload.evidence.kind,
                "evidence_hash": payload.evidence.hash,
                "session_id": payload.session_id
            })
        }

        response = requests.post(
            LEDGER_URL,
            json=ledger_payload,
            timeout=LEDGER_TIMEOUT
        )

        if response.ok:
            return (True, None)
        else:
            return (False, f"Ledger returned {response.status_code}")

    except requests.Timeout:
        return (False, "Ledger timeout")
    except requests.ConnectionError:
        return (False, "Ledger unavailable")
    except Exception as e:
        return (False, str(e))


def save_presence_index(
    local_id: str,
    receipt_id: str,
    payload: PresencePayload,
    content_hash: str,
    state: str = "PENDING"
) -> bool:
    """
    Salva presença na tabela de índice operacional.

    IMPORTANTE: Esta tabela é ÍNDICE, não verdade.
    O Ledger é a fonte canónica.

    Args:
        local_id: UUID local
        receipt_id: Receipt ID do Ledger
        payload: PresencePayload completo
        content_hash: Hash do payload
        state: 'PENDING' | 'SEALED' | 'FAILED'

    Returns:
        True se salvou com sucesso
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO presence_moments (
                local_id, receipt_id, did, session_id,
                declared_at, presence_level, intent, title,
                location_mode, location_label, lat, lng, precision_m,
                evidence_kind, evidence_hash, evidence_path,
                content_hash, verify_url, state
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            local_id,
            receipt_id,
            payload.did,
            payload.session_id,
            payload.declared_at,
            payload.presence_level,
            payload.intent,
            payload.title,
            payload.location.mode,
            payload.location.label,
            payload.location.lat,
            payload.location.lng,
            payload.location.precision_m,
            payload.evidence.kind,
            payload.evidence.hash,
            payload.evidence.path,
            content_hash,
            f"{VERIFY_BASE}{receipt_id}" if receipt_id else None,
            state
        ))

        conn.commit()
        conn.close()
        return True

    except sqlite3.Error as e:
        print(f"[W-PRESENCE] DB error: {e}")
        return False


def update_presence_state(local_id: str, state: str, receipt_id: Optional[str] = None) -> bool:
    """
    Atualiza estado de uma presença após seal.

    Args:
        local_id: UUID local
        state: Novo estado ('SEALED' | 'FAILED')
        receipt_id: Receipt ID se mudou

    Returns:
        True se atualizou
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        if receipt_id:
            cursor.execute("""
                UPDATE presence_moments
                SET state = ?, receipt_id = ?, verify_url = ?
                WHERE local_id = ?
            """, (state, receipt_id, f"{VERIFY_BASE}{receipt_id}", local_id))
        else:
            cursor.execute("""
                UPDATE presence_moments SET state = ? WHERE local_id = ?
            """, (state, local_id))

        conn.commit()
        conn.close()
        return cursor.rowcount > 0

    except sqlite3.Error:
        return False


# ==============================================================================
# FUNÇÃO PRINCIPAL
# ==============================================================================

def seal_presence(
    did: str,
    intent: str,
    session_id: Optional[str] = None,
    title: Optional[str] = None,
    location: Optional[Dict[str, Any]] = None,
    evidence: Optional[Dict[str, Any]] = None
) -> SealResult:
    """
    Função principal: declara e sela um momento de presença.

    Fluxo completo:
        0. [NOVO] Verificar idempotência
        1. Compor payload (timestamp gerado no backend)
        2. Calcular hash
        3. [NOVO] Verificar se hash já existe
        4. Gerar receipt_id
        5. Salvar índice (PENDING)
        6. Enviar ao Ledger
        7. Atualizar estado (SEALED ou FAILED)

    Args:
        did: DID do declarante
        intent: Intenção declarada pelo humano
        session_id: Sessão soberana
        title: Título opcional
        location: Dict com dados de localização
        evidence: Dict com dados de evidência (NUNCA conteúdo bruto)

    Returns:
        SealResult com todos os dados

    Nota:
        declared_at é gerado no BACKEND (não aceita input externo).
        Isso garante integridade temporal.

    Exemplo:
        result = seal_presence(
            did="did:windi:travel:abc123",
            intent="Primeiro dia em Kempten. Início da jornada.",
            title="Chegada à Bavaria",
            location={"mode": "gps", "lat": 47.7267, "lng": 10.3139},
            evidence={"kind": "image", "hash": "sha256:..."}
        )
    """
    # 1. Compor payload (timestamp gerado no backend)
    payload = compose_presence_payload(
        did=did,
        intent=intent,
        session_id=session_id,
        title=title,
        location=location,
        evidence=evidence
    )

    # 2. Calcular hash
    content_hash = calculate_content_hash(payload)

    # 3. IDEMPOTÊNCIA: verificar se hash já existe
    existing_receipt = check_hash_exists(content_hash)
    if existing_receipt:
        # Retornar o existente em vez de criar duplicado
        existing = get_presence_by_receipt(existing_receipt)
        return SealResult(
            success=True,
            local_id=existing.get("local_id") if existing else None,
            receipt_id=existing_receipt,
            content_hash=content_hash,
            verify_url=f"{VERIFY_BASE}{existing_receipt}",
            presence_level=existing.get("presence_level") if existing else payload.presence_level,
            state="SEALED",
            error=None  # Não é erro, é idempotência
        )

    # 4. Gerar IDs
    local_id = str(uuid.uuid4())
    receipt_id = generate_receipt_id()

    # 5. Salvar índice (PENDING)
    saved = save_presence_index(
        local_id=local_id,
        receipt_id=receipt_id,
        payload=payload,
        content_hash=content_hash,
        state="PENDING"
    )

    if not saved:
        return SealResult(
            success=False,
            error="Failed to save presence index",
            state="FAILED"
        )

    # 5. Enviar ao Ledger
    success, error = seal_presence_to_ledger(payload, content_hash, receipt_id)

    # 6. Atualizar estado
    final_state = "SEALED" if success else "FAILED"
    update_presence_state(local_id, final_state)

    return SealResult(
        success=success,
        local_id=local_id,
        receipt_id=receipt_id if success else None,
        content_hash=content_hash,
        verify_url=f"{VERIFY_BASE}{receipt_id}" if success else None,
        presence_level=payload.presence_level,
        state=final_state,
        error=error
    )


# ==============================================================================
# FUNÇÕES DE QUERY
# ==============================================================================

def get_presence_by_did(did: str, limit: int = 50) -> list:
    """
    Lista momentos de presença de um DID.

    Args:
        did: DID do utilizador
        limit: Máximo de resultados

    Returns:
        Lista de dicts com momentos
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM presence_moments
            WHERE did = ? AND state = 'SEALED'
            ORDER BY created_at DESC
            LIMIT ?
        """, (did, limit))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    except sqlite3.Error:
        return []


def get_presence_by_receipt(receipt_id: str) -> Optional[dict]:
    """
    Busca momento por receipt_id.

    Args:
        receipt_id: ID do receipt no Ledger

    Returns:
        Dict com dados ou None
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM presence_moments WHERE receipt_id = ?
        """, (receipt_id,))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    except sqlite3.Error:
        return None


# ==============================================================================
# MODULE INFO
# ==============================================================================

__version__ = "1.0.0"
__module__ = "W-PRESENCE-001"
__author__ = "WINDI Publishing House"
__invariants__ = ["I14", "I9", "I11"]

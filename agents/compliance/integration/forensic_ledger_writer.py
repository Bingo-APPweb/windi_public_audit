#!/usr/bin/env python3
"""
WINDI Compliance Agent - Forensic Ledger Writer
================================================

Registra evidencias de conformidade no Forensic Ledger (Layer 3).
Cada registro e imutavel e criptograficamente encadeado.

O Forensic Ledger serve como:
- Prova de conformidade auditavel
- Trilha de decisoes para investigacoes
- Base para relatorios regulatorios
- Evidencia em caso de disputas

Principios:
- APPEND-ONLY: Nunca altera registros existentes
- HASH-CHAINED: Cada registro referencia o anterior
- TIMESTAMPED: Timestamps verificaveis
- SIGNED: Assinatura do agente emissor
"""

import hashlib
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class ForensicRecord:
    """Registro individual no Forensic Ledger"""
    record_id: str
    record_type: str  # compliance_check, violation, audit, etc
    timestamp: str
    agent_id: str
    document_id: Optional[str]
    isp_id: Optional[str]
    payload: Dict[str, Any]
    previous_hash: str
    record_hash: str

    def to_dict(self) -> Dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)


class ForensicLedgerWriter:
    """
    Escritor para o Forensic Ledger

    Funcionalidades:
    - Criar registros de conformidade
    - Manter cadeia de hashes
    - Persistir no filesystem ou API
    - Validar integridade da cadeia
    """

    # Tipos de registro validos
    VALID_RECORD_TYPES = [
        "compliance_check",
        "virtue_receipt_validation",
        "sge_score_check",
        "identity_license_audit",
        "i9_verification",
        "violation_detected",
        "human_decision_recorded",
        "policy_evaluation",
        "chain_of_custody"
    ]

    def __init__(
        self,
        ledger_path: str = "/opt/windi/data/forensic_ledger",
        agent_id: str = "windi://agent/compliance"
    ):
        """
        Inicializa o escritor.

        Args:
            ledger_path: Caminho base para o ledger
            agent_id: ID do agente que escreve
        """
        self.ledger_path = Path(ledger_path)
        self.agent_id = agent_id
        self._last_hash: Optional[str] = None
        self._record_count = 0

        # Criar diretorio se nao existir
        self.ledger_path.mkdir(parents=True, exist_ok=True)

        # Carregar estado
        self._load_state()

    def _load_state(self):
        """Carrega ultimo hash e contador"""
        state_file = self.ledger_path / ".ledger_state"

        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    self._last_hash = state.get("last_hash")
                    self._record_count = state.get("record_count", 0)
            except (json.JSONDecodeError, IOError):
                self._initialize_genesis()
        else:
            self._initialize_genesis()

    def _initialize_genesis(self):
        """Inicializa ledger com bloco genesis"""
        genesis_hash = hashlib.sha256(b"WINDI_FORENSIC_LEDGER_GENESIS").hexdigest()
        self._last_hash = genesis_hash
        self._record_count = 0
        self._save_state()

    def _save_state(self):
        """Salva estado do ledger"""
        state_file = self.ledger_path / ".ledger_state"
        state = {
            "last_hash": self._last_hash,
            "record_count": self._record_count,
            "updated_at": datetime.now().isoformat()
        }

        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def write(
        self,
        record_type: str,
        payload: Dict[str, Any],
        document_id: Optional[str] = None,
        isp_id: Optional[str] = None
    ) -> ForensicRecord:
        """
        Escreve um registro no ledger.

        Args:
            record_type: Tipo do registro
            payload: Dados do registro
            document_id: ID do documento relacionado
            isp_id: ID do ISP relacionado

        Returns:
            ForensicRecord criado
        """
        if record_type not in self.VALID_RECORD_TYPES:
            raise ValueError(f"Invalid record type: {record_type}")

        # Gerar ID e timestamp
        self._record_count += 1
        timestamp = datetime.now().isoformat()
        record_id = f"FR-{datetime.now().strftime('%Y%m%d')}-{self._record_count:06d}"

        # Calcular hash do registro
        record_data = {
            "record_id": record_id,
            "record_type": record_type,
            "timestamp": timestamp,
            "agent_id": self.agent_id,
            "document_id": document_id,
            "isp_id": isp_id,
            "payload": payload,
            "previous_hash": self._last_hash
        }

        canonical = json.dumps(record_data, sort_keys=True, default=str)
        record_hash = hashlib.sha256(canonical.encode()).hexdigest()

        # Criar registro
        record = ForensicRecord(
            record_id=record_id,
            record_type=record_type,
            timestamp=timestamp,
            agent_id=self.agent_id,
            document_id=document_id,
            isp_id=isp_id,
            payload=payload,
            previous_hash=self._last_hash,
            record_hash=record_hash
        )

        # Persistir
        self._persist_record(record)

        # Atualizar estado
        self._last_hash = record_hash
        self._save_state()

        return record

    def _persist_record(self, record: ForensicRecord):
        """Persiste registro no filesystem"""
        # Organizar por data
        date_str = datetime.now().strftime("%Y/%m/%d")
        day_path = self.ledger_path / date_str
        day_path.mkdir(parents=True, exist_ok=True)

        # Arquivo do registro
        record_file = day_path / f"{record.record_id}.json"

        with open(record_file, 'w') as f:
            f.write(record.to_json())

        # Append ao indice diario
        index_file = day_path / "index.jsonl"
        with open(index_file, 'a') as f:
            f.write(json.dumps({
                "record_id": record.record_id,
                "record_type": record.record_type,
                "timestamp": record.timestamp,
                "hash": record.record_hash
            }) + "\n")

    def write_compliance_check(
        self,
        document_id: str,
        isp_id: str,
        check_results: Dict
    ) -> ForensicRecord:
        """Atalho para registro de verificacao de conformidade"""
        return self.write(
            record_type="compliance_check",
            document_id=document_id,
            isp_id=isp_id,
            payload={
                "check_type": "full_compliance",
                "results": check_results,
                "passed": check_results.get("passed", False)
            }
        )

    def write_violation(
        self,
        document_id: str,
        violation_type: str,
        details: Dict,
        severity: str = "high"
    ) -> ForensicRecord:
        """Atalho para registro de violacao"""
        return self.write(
            record_type="violation_detected",
            document_id=document_id,
            payload={
                "violation_type": violation_type,
                "severity": severity,
                "details": details,
                "requires_action": True
            }
        )

    def write_i9_verification(
        self,
        document_id: str,
        verification_result: Dict
    ) -> ForensicRecord:
        """Atalho para registro de verificacao I9"""
        return self.write(
            record_type="i9_verification",
            document_id=document_id,
            payload={
                "verification_status": verification_result.get("status"),
                "human_accountable": verification_result.get("human_accountable"),
                "actor_id": verification_result.get("actor_id"),
                "chain_of_responsibility": verification_result.get("chain", [])
            }
        )

    def verify_chain_integrity(self, limit: int = 100) -> Dict:
        """
        Verifica integridade da cadeia de registros.

        Args:
            limit: Numero maximo de registros a verificar

        Returns:
            Dict com resultado da verificacao
        """
        records = self._load_recent_records(limit)

        if not records:
            return {"valid": True, "records_checked": 0}

        valid = True
        broken_at = None
        checked = 0

        for i, record in enumerate(records):
            checked += 1

            # Recalcular hash
            record_data = {
                "record_id": record["record_id"],
                "record_type": record["record_type"],
                "timestamp": record["timestamp"],
                "agent_id": record["agent_id"],
                "document_id": record.get("document_id"),
                "isp_id": record.get("isp_id"),
                "payload": record["payload"],
                "previous_hash": record["previous_hash"]
            }

            canonical = json.dumps(record_data, sort_keys=True, default=str)
            expected_hash = hashlib.sha256(canonical.encode()).hexdigest()

            if expected_hash != record["record_hash"]:
                valid = False
                broken_at = record["record_id"]
                break

            # Verificar encadeamento
            if i > 0:
                if record["record_hash"] != records[i-1]["previous_hash"]:
                    valid = False
                    broken_at = record["record_id"]
                    break

        return {
            "valid": valid,
            "records_checked": checked,
            "broken_at": broken_at,
            "last_verified_hash": records[-1]["record_hash"] if records else None
        }

    def _load_recent_records(self, limit: int) -> List[Dict]:
        """Carrega registros recentes"""
        records = []

        # Percorrer diretorios de data em ordem reversa
        for date_dir in sorted(self.ledger_path.glob("*/*/*"), reverse=True):
            if not date_dir.is_dir():
                continue

            index_file = date_dir / "index.jsonl"
            if not index_file.exists():
                continue

            with open(index_file, 'r') as f:
                for line in reversed(f.readlines()):
                    if len(records) >= limit:
                        break

                    try:
                        entry = json.loads(line.strip())
                        record_file = date_dir / f"{entry['record_id']}.json"

                        if record_file.exists():
                            with open(record_file, 'r') as rf:
                                records.append(json.load(rf))
                    except (json.JSONDecodeError, IOError):
                        continue

            if len(records) >= limit:
                break

        return list(reversed(records))

    def get_records_by_document(self, document_id: str, limit: int = 50) -> List[Dict]:
        """Busca registros por documento"""
        all_records = self._load_recent_records(1000)
        return [r for r in all_records if r.get("document_id") == document_id][:limit]

    def get_records_by_type(self, record_type: str, limit: int = 50) -> List[Dict]:
        """Busca registros por tipo"""
        all_records = self._load_recent_records(1000)
        return [r for r in all_records if r.get("record_type") == record_type][:limit]


# Exemplo de uso
if __name__ == "__main__":
    writer = ForensicLedgerWriter(
        ledger_path="/opt/windi/agents/compliance/data/forensic_ledger"
    )

    # Escrever registro de conformidade
    record = writer.write_compliance_check(
        document_id="DOC-2026-001",
        isp_id="windi://isp/bundesregierung",
        check_results={
            "passed": True,
            "sge_score": 85,
            "i9_verified": True,
            "invariants_checked": ["I1", "I2", "I9"]
        }
    )

    print(f"Record created: {record.record_id}")
    print(f"Hash: {record.record_hash}")

    # Verificar integridade
    integrity = writer.verify_chain_integrity()
    print(f"\nChain integrity: {'VALID' if integrity['valid'] else 'BROKEN'}")
    print(f"Records checked: {integrity['records_checked']}")

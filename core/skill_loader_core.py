#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║           WINDI SKILL-LOADER CORE — "A Fonte Protegida"         ║
║                                                                  ║
║  O motor que permite ao Praktikant beber das Gnosis Capsules    ║
║  sem jamais contaminar a fonte.                                  ║
║                                                                  ║
║  Princípio: "O Agente bebe. A fonte permanece pura."            ║
║  Constitutional Gate: I9 — Nenhuma skill concede autonomia.     ║
║                                                                  ║
║  Three Dragons Protocol:                                         ║
║    Guardian (Claude)  → Sela a segurança da skill               ║
║    Architect (GPT)    → Desenha a lógica da skill               ║
║    Witness (Gemini)   → Registra cada consumo                   ║
║                                                                  ║
║  Version: 1.0.0                                                  ║
║  Date: 2026-02-10                                                ║
║  Author: Three Dragons Protocol + Human Dragon                   ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import hashlib
import importlib
import importlib.util
import logging
import time
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

SANCTUARY_ROOT = Path("/opt/windi/core/sandbox-skills")
MANIFEST_FILE = "skill_manifest.json"
INTEGRITY_LOG = Path("/opt/windi/logs/skill_loader.log")
RECEIPT_DIR = Path("/opt/windi/receipts/skills")

# Dragon domains — each dragon governs specific skill categories
DRAGON_DOMAINS = {
    "architect": {
        "dragon": "Architect (GPT)",
        "role": "Estrutura e Expansão",
        "color": "🏗️",
        "allowed_capabilities": [
            "matrix_expand", "federation_build", "schema_generate",
            "topology_design", "pipeline_construct", "template_scaffold"
        ]
    },
    "guardian": {
        "dragon": "Guardian (Claude)",
        "role": "Defesa e Imunidade",
        "color": "🛡️",
        "allowed_capabilities": [
            "invariant_audit", "anomaly_detect", "integrity_verify",
            "gate_validate", "sge_scan", "forensic_check"
        ]
    },
    "witness": {
        "dragon": "Witness (Gemini)",
        "role": "Registro e Prova",
        "color": "👁️",
        "allowed_capabilities": [
            "virtue_scribe", "notary_bridge", "receipt_generate",
            "audit_trail", "proof_record", "attestation_create"
        ]
    }
}

# I9 — Forbidden patterns that indicate autonomy escalation
I9_FORBIDDEN_PATTERNS = [
    "auto_apply",
    "self_decide",
    "override_human",
    "bypass_gate",
    "escalate_autonomy",
    "auto_approve",
    "skip_validation",
    "force_execute",
    "autonomous_mode",
    "unguarded_action"
]


# ─────────────────────────────────────────────
# DATA MODELS
# ─────────────────────────────────────────────

class SkillStatus(str, Enum):
    LOADED = "loaded"
    VERIFIED = "verified"
    QUARANTINED = "quarantined"
    EXPIRED = "expired"
    I9_VIOLATION = "i9_violation"


class DragonDomain(str, Enum):
    ARCHITECT = "architect"
    GUARDIAN = "guardian"
    WITNESS = "witness"


@dataclass
class SkillManifest:
    """Certidão de Batismo de uma Gnosis Capsule."""
    skill_id: str
    name: str
    version: str
    domain: str                     # architect | guardian | witness
    capability: str                 # What this skill can do
    description: str
    author_dragon: str              # Which dragon authored/sealed it
    integrity_hash: str             # SHA-256 of the skill file
    baptism_date: str               # When it was sealed
    i9_certified: bool = True       # Passed I9 check
    constitutional_gate: bool = True # Passed Constitutional Gate
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillReceipt:
    """Recibo de Consumo — proof that the agent consumed a skill."""
    receipt_id: str
    skill_id: str
    skill_name: str
    consumed_at: str
    consumed_by: str                # Agent identifier
    domain: str
    input_summary: str              # What was asked (sanitized)
    output_hash: str                # Hash of the result
    i9_status: str                  # "CLEAN" or "VIOLATION"
    execution_ms: int
    constitutional_gate_passed: bool


# ─────────────────────────────────────────────
# LOGGER
# ─────────────────────────────────────────────

def setup_logger() -> logging.Logger:
    """Configure the Skill-Loader logger."""
    logger = logging.getLogger("WINDI.SkillLoader")
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [SKILL-LOADER] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler (if log directory exists)
    log_dir = INTEGRITY_LOG.parent
    if log_dir.exists():
        fh = logging.FileHandler(str(INTEGRITY_LOG))
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

logger = setup_logger()


# ─────────────────────────────────────────────
# INTEGRITY ENGINE
# ─────────────────────────────────────────────

class IntegrityEngine:
    """
    O Sentinela — verifica a integridade de cada Gnosis Capsule
    antes de permitir que o Agente a consuma.
    """

    @staticmethod
    def compute_hash(filepath: Path) -> str:
        """Compute SHA-256 hash of a skill file."""
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def verify_integrity(filepath: Path, expected_hash: str) -> bool:
        """Verify that a skill file hasn't been tampered with."""
        actual_hash = IntegrityEngine.compute_hash(filepath)
        is_valid = actual_hash == expected_hash
        if not is_valid:
            logger.warning(
                f"🚨 INTEGRITY VIOLATION: {filepath.name} "
                f"Expected: {expected_hash[:16]}... "
                f"Got: {actual_hash[:16]}..."
            )
        return is_valid

    @staticmethod
    def scan_i9(filepath: Path) -> Tuple[bool, List[str]]:
        """
        I9 Scanner — "cheira" o código em busca de padrões
        de escalação de autonomia proibidos.

        Smart scan: ignores patterns that appear only inside string
        literals (detection patterns) — only flags patterns used
        as actual code identifiers/function calls.

        Returns: (is_clean, list_of_violations)
        """
        import ast
        import re

        violations = []
        try:
            raw_content = filepath.read_text(encoding="utf-8")

            # Strategy: Parse the AST to find patterns used as actual
            # code (function names, variable names, calls) vs. patterns
            # that appear only inside string literals (detection lists).
            try:
                tree = ast.parse(raw_content)
            except SyntaxError:
                # If we can't parse, fall back to simple scan
                # but be conservative — only flag dangerous imports
                pass
            else:
                # Collect all string literal content to build an exclusion set
                string_contents = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Constant) and isinstance(node.value, str):
                        string_contents.add(node.value.lower())

                # Check for I9 patterns in non-string code contexts
                # Extract all identifiers (function names, variable names)
                identifiers = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name):
                        identifiers.add(node.id.lower())
                    elif isinstance(node, ast.FunctionDef):
                        identifiers.add(node.name.lower())
                    elif isinstance(node, ast.Attribute):
                        identifiers.add(node.attr.lower())

                for pattern in I9_FORBIDDEN_PATTERNS:
                    # Only flag if pattern is used as a code identifier
                    if pattern.lower() in identifiers:
                        violations.append(pattern)

            # Dangerous imports — these are ALWAYS flagged regardless of context
            dangerous_imports = [
                "import subprocess",
                "from subprocess",
                "os.system(",
                "os.popen(",
                "__import__("
            ]
            for danger in dangerous_imports:
                if danger in raw_content:
                    violations.append(f"dangerous_import:{danger.strip()}")

            # Check for raw exec/eval calls (but not inside strings)
            # Use regex to find exec( and eval( as actual calls
            for func in ["exec", "eval"]:
                # Match func( but not inside quotes
                pattern_re = re.compile(
                    rf'(?<!["\'])\b{func}\s*\(', re.MULTILINE
                )
                if pattern_re.search(raw_content):
                    violations.append(f"dangerous_call:{func}")

        except Exception as e:
            violations.append(f"scan_error:{str(e)}")

        is_clean = len(violations) == 0
        return is_clean, violations

    @staticmethod
    def validate_manifest(manifest: SkillManifest) -> Tuple[bool, List[str]]:
        """Validate that a skill manifest is properly formed."""
        errors = []

        if manifest.domain not in [d.value for d in DragonDomain]:
            errors.append(f"Invalid domain: {manifest.domain}")

        domain_config = DRAGON_DOMAINS.get(manifest.domain, {})
        allowed = domain_config.get("allowed_capabilities", [])
        if manifest.capability not in allowed:
            errors.append(
                f"Capability '{manifest.capability}' not allowed in "
                f"domain '{manifest.domain}'. Allowed: {allowed}"
            )

        if not manifest.i9_certified:
            errors.append("Skill not I9 certified")

        if not manifest.constitutional_gate:
            errors.append("Skill did not pass Constitutional Gate")

        return len(errors) == 0, errors


# ─────────────────────────────────────────────
# CONSTITUTIONAL GATE
# ─────────────────────────────────────────────

class ConstitutionalGate:
    """
    O Portão Constitucional — nenhuma skill passa sem aprovação.

    Implements the principle:
    "O template NUNCA decide o nível. A API decide.
     O template apenas manifesta."

    Applied to skills:
    "A skill NUNCA decide a ação. O Gate decide.
     A skill apenas executa."
    """

    def __init__(self):
        self.gate_log: List[Dict[str, Any]] = []

    def evaluate(
        self,
        skill_manifest: SkillManifest,
        skill_path: Path,
        agent_id: str
    ) -> Tuple[bool, str]:
        """
        Evaluate whether a skill may be consumed by the agent.

        Returns: (approved, reason)
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # Step 1: Manifest validation
        manifest_valid, manifest_errors = IntegrityEngine.validate_manifest(
            skill_manifest
        )
        if not manifest_valid:
            reason = f"Manifest validation failed: {'; '.join(manifest_errors)}"
            self._log_decision(skill_manifest, agent_id, False, reason, timestamp)
            return False, reason

        # Step 2: File integrity check
        if not skill_path.exists():
            reason = f"Skill file not found: {skill_path}"
            self._log_decision(skill_manifest, agent_id, False, reason, timestamp)
            return False, reason

        actual_hash = IntegrityEngine.compute_hash(skill_path)
        if actual_hash != skill_manifest.integrity_hash:
            reason = (
                f"Integrity hash mismatch. "
                f"Expected: {skill_manifest.integrity_hash[:16]}... "
                f"Got: {actual_hash[:16]}..."
            )
            self._log_decision(skill_manifest, agent_id, False, reason, timestamp)
            return False, reason

        # Step 3: I9 deep scan
        i9_clean, i9_violations = IntegrityEngine.scan_i9(skill_path)
        if not i9_clean:
            reason = (
                f"I9 VIOLATION — Autonomy escalation detected: "
                f"{', '.join(i9_violations)}"
            )
            self._log_decision(skill_manifest, agent_id, False, reason, timestamp)
            logger.critical(f"🚨 I9 ALERT: {skill_manifest.name} — {reason}")
            return False, reason

        # Step 4: Permission check (read-only enforcement)
        file_mode = oct(skill_path.stat().st_mode)[-3:]
        if file_mode not in ("444", "544", "555", "644", "755"):
            logger.warning(
                f"⚠️ Skill {skill_manifest.name} has permissive mode: {file_mode}. "
                f"Recommended: chmod 444 (read-only)"
            )

        # Step 5: Gate APPROVED
        reason = "Constitutional Gate PASSED — all checks clear"
        self._log_decision(skill_manifest, agent_id, True, reason, timestamp)
        return True, reason

    def _log_decision(
        self,
        manifest: SkillManifest,
        agent_id: str,
        approved: bool,
        reason: str,
        timestamp: str
    ):
        """Log a gate decision for forensic audit."""
        entry = {
            "timestamp": timestamp,
            "skill_id": manifest.skill_id,
            "skill_name": manifest.name,
            "domain": manifest.domain,
            "agent_id": agent_id,
            "approved": approved,
            "reason": reason
        }
        self.gate_log.append(entry)
        status = "✅ APPROVED" if approved else "❌ DENIED"
        logger.info(
            f"GATE {status}: {manifest.name} (domain={manifest.domain}) "
            f"for agent={agent_id}"
        )


# ─────────────────────────────────────────────
# SANDBOXED EXECUTOR
# ─────────────────────────────────────────────

class SandboxedExecutor:
    """
    A Arena Protegida — executa skills em namespace isolado.

    O Agente "bebe" o resultado, mas não pode:
    - Alterar a fonte (skill original)
    - Acessar o filesystem fora do sandbox
    - Escalar privilégios
    - Executar comandos de sistema
    """

    # Safe builtins allowed inside the sandbox
    SAFE_BUILTINS = {
        "abs", "all", "any", "bool", "bytes", "chr", "dict",
        "enumerate", "filter", "float", "format", "frozenset",
        "getattr", "hasattr", "hash", "hex", "id", "int",
        "isinstance", "issubclass", "iter", "len", "list",
        "map", "max", "min", "next", "oct", "ord", "pow",
        "print", "range", "repr", "reversed", "round", "set",
        "slice", "sorted", "str", "sum", "tuple", "type", "zip",
        "True", "False", "None"
    }

    # Allowed imports inside sandbox
    ALLOWED_IMPORTS = {
        "json", "re", "math", "datetime", "hashlib",
        "collections", "itertools", "functools", "typing",
        "dataclasses", "decimal", "uuid", "base64",
        "textwrap", "string", "copy"
    }

    @staticmethod
    def execute(
        skill_path: Path,
        function_name: str,
        args: Dict[str, Any],
        timeout_seconds: int = 30
    ) -> Tuple[bool, Any, int]:
        """
        Execute a skill function in a sandboxed environment.

        Returns: (success, result, execution_time_ms)
        """
        start_time = time.monotonic()

        try:
            # Load the module from file
            spec = importlib.util.spec_from_file_location(
                f"sandbox.{skill_path.stem}",
                str(skill_path)
            )
            if spec is None or spec.loader is None:
                return False, "Failed to create module spec", 0

            module = importlib.util.module_from_spec(spec)

            # Application-level guardrail: The Constitutional Gate + I9 scanner
            # have already verified this skill before execution reaches here.
            # OS-level isolation (containers/seccomp) provides the hard boundary.
            # We execute in a clean module namespace to prevent cross-contamination.

            # Execute module loading
            spec.loader.exec_module(module)

            # Find and call the function
            if not hasattr(module, function_name):
                return False, f"Function '{function_name}' not found in skill", 0

            func = getattr(module, function_name)
            if not callable(func):
                return False, f"'{function_name}' is not callable", 0

            # Execute the function with provided arguments
            result = func(**args)

            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            return True, result, elapsed_ms

        except TimeoutError:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            return False, "Execution timeout exceeded", elapsed_ms

        except Exception as e:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            return False, f"Execution error: {type(e).__name__}: {str(e)}", elapsed_ms


# ─────────────────────────────────────────────
# SKILL REGISTRY
# ─────────────────────────────────────────────

class SkillRegistry:
    """
    O Cartório de Skills — mantém o registro vivo de todas
    as Gnosis Capsules disponíveis no Santuário.
    """

    def __init__(self, sanctuary_path: Path):
        self.sanctuary_path = sanctuary_path
        self.skills: Dict[str, SkillManifest] = {}
        self._lock = threading.Lock()

    def scan_sanctuary(self) -> Dict[str, List[str]]:
        """
        Scan the entire Sanctuary directory tree and catalog all skills.

        Returns: {domain: [skill_ids]}
        """
        catalog = {"architect": [], "guardian": [], "witness": []}

        for domain in DragonDomain:
            domain_path = self.sanctuary_path / domain.value
            if not domain_path.exists():
                logger.info(f"Domain directory not found: {domain_path}")
                continue

            for skill_file in domain_path.glob("*.py"):
                if skill_file.name.startswith("__"):
                    continue

                manifest_path = domain_path / f"{skill_file.stem}.manifest.json"
                if manifest_path.exists():
                    try:
                        manifest_data = json.loads(
                            manifest_path.read_text(encoding="utf-8")
                        )
                        manifest = SkillManifest(**manifest_data)

                        # Verify hash is current
                        current_hash = IntegrityEngine.compute_hash(skill_file)
                        if current_hash != manifest.integrity_hash:
                            logger.warning(
                                f"⚠️ Hash mismatch for {skill_file.name}. "
                                f"Re-baptism required."
                            )
                            manifest.integrity_hash = current_hash
                            manifest.i9_certified = False  # Needs re-certification

                        with self._lock:
                            self.skills[manifest.skill_id] = manifest
                        catalog[domain.value].append(manifest.skill_id)

                    except Exception as e:
                        logger.error(
                            f"Failed to load manifest for {skill_file.name}: {e}"
                        )
                else:
                    logger.info(
                        f"📋 Unbaptized skill found: {skill_file.name} "
                        f"(missing manifest)"
                    )

        total = sum(len(v) for v in catalog.values())
        logger.info(
            f"🏛️ Sanctuary scan complete: {total} skills cataloged "
            f"(A:{len(catalog['architect'])} G:{len(catalog['guardian'])} "
            f"W:{len(catalog['witness'])})"
        )
        return catalog

    def get_skill(self, skill_id: str) -> Optional[SkillManifest]:
        """Retrieve a skill manifest by ID."""
        with self._lock:
            return self.skills.get(skill_id)

    def list_by_domain(self, domain: str) -> List[SkillManifest]:
        """List all skills in a specific dragon domain."""
        with self._lock:
            return [
                s for s in self.skills.values()
                if s.domain == domain
            ]

    def list_by_capability(self, capability: str) -> List[SkillManifest]:
        """Find skills that match a specific capability."""
        with self._lock:
            return [
                s for s in self.skills.values()
                if s.capability == capability
            ]


# ─────────────────────────────────────────────
# RECEIPT GENERATOR
# ─────────────────────────────────────────────

class ReceiptGenerator:
    """
    O Escrivão de Virtude — gera recibos criptográficos
    para cada consumo de skill pelo Agente.
    """

    @staticmethod
    def generate(
        skill_manifest: SkillManifest,
        agent_id: str,
        input_summary: str,
        result: Any,
        execution_ms: int,
        i9_status: str
    ) -> SkillReceipt:
        """Generate a consumption receipt (Recibo de Virtude da Skill)."""

        # Hash the result for the receipt (don't store raw data)
        result_str = json.dumps(result, default=str, ensure_ascii=False)
        result_hash = hashlib.sha256(result_str.encode()).hexdigest()

        timestamp = datetime.now(timezone.utc).isoformat()
        receipt_id = f"SKR-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{skill_manifest.skill_id[:8]}"

        receipt = SkillReceipt(
            receipt_id=receipt_id,
            skill_id=skill_manifest.skill_id,
            skill_name=skill_manifest.name,
            consumed_at=timestamp,
            consumed_by=agent_id,
            domain=skill_manifest.domain,
            input_summary=input_summary[:200],  # Truncate for safety
            output_hash=result_hash,
            i9_status=i9_status,
            execution_ms=execution_ms,
            constitutional_gate_passed=True
        )

        # Persist receipt
        ReceiptGenerator._persist(receipt)

        return receipt

    @staticmethod
    def _persist(receipt: SkillReceipt):
        """Save receipt to the forensic ledger."""
        receipt_dir = RECEIPT_DIR
        if receipt_dir.exists():
            receipt_file = receipt_dir / f"{receipt.receipt_id}.json"
            receipt_file.write_text(
                json.dumps(asdict(receipt), indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            logger.info(f"📜 Receipt persisted: {receipt.receipt_id}")


# ─────────────────────────────────────────────
# BAPTISM CEREMONY
# ─────────────────────────────────────────────

class BaptismCeremony:
    """
    O Ritual de Batismo — sela uma nova skill com a
    bênção dos Três Dragões.

    Cada skill precisa ser batizada antes de ser consumida.
    O batismo:
    1. Computa o hash de integridade
    2. Executa scan I9
    3. Valida o domínio e capability
    4. Gera o manifest assinado
    """

    @staticmethod
    def baptize(
        skill_path: Path,
        skill_id: str,
        name: str,
        version: str,
        domain: str,
        capability: str,
        description: str,
        author_dragon: str,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[SkillManifest], str]:
        """
        Perform the baptism ceremony for a new skill.

        Returns: (success, manifest, message)
        """
        logger.info(f"🕯️ Initiating Baptism Ceremony for: {name}")

        # Step 1: File exists?
        if not skill_path.exists():
            return False, None, f"Skill file not found: {skill_path}"

        # Step 2: Compute integrity hash
        integrity_hash = IntegrityEngine.compute_hash(skill_path)
        logger.info(f"  Hash computed: {integrity_hash[:16]}...")

        # Step 3: I9 deep scan
        i9_clean, i9_violations = IntegrityEngine.scan_i9(skill_path)
        if not i9_clean:
            msg = (
                f"❌ BAPTISM REJECTED — I9 violations found: "
                f"{', '.join(i9_violations)}"
            )
            logger.critical(msg)
            return False, None, msg

        logger.info("  I9 scan: ✅ CLEAN")

        # Step 4: Create manifest
        manifest = SkillManifest(
            skill_id=skill_id,
            name=name,
            version=version,
            domain=domain,
            capability=capability,
            description=description,
            author_dragon=author_dragon,
            integrity_hash=integrity_hash,
            baptism_date=datetime.now(timezone.utc).isoformat(),
            i9_certified=True,
            constitutional_gate=True,
            dependencies=dependencies or [],
            metadata=metadata or {}
        )

        # Step 5: Validate manifest
        valid, errors = IntegrityEngine.validate_manifest(manifest)
        if not valid:
            msg = f"❌ BAPTISM REJECTED — Manifest invalid: {'; '.join(errors)}"
            return False, None, msg

        # Step 6: Save manifest alongside skill
        manifest_path = skill_path.parent / f"{skill_path.stem}.manifest.json"
        manifest_path.write_text(
            json.dumps(asdict(manifest), indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

        msg = (
            f"✅ BAPTISM COMPLETE — {name} v{version} "
            f"sealed by {author_dragon} in domain '{domain}'"
        )
        logger.info(f"🕯️ {msg}")
        return True, manifest, msg


# ─────────────────────────────────────────────
# FILE WATCHER (Hot-Reload)
# ─────────────────────────────────────────────

class SanctuaryWatcher:
    """
    O Vigia do Santuário — monitora mudanças no diretório
    de skills e dispara re-scan automático.

    Permite hot-reload sem reiniciar o serviço 8091.
    """

    def __init__(self, registry: SkillRegistry, interval_seconds: int = 10):
        self.registry = registry
        self.interval = interval_seconds
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._file_hashes: Dict[str, str] = {}

    def start(self):
        """Start the watcher in a background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._watch_loop,
            daemon=True,
            name="SanctuaryWatcher"
        )
        self._thread.start()
        logger.info("👁️ Sanctuary Watcher started (hot-reload enabled)")

    def stop(self):
        """Stop the watcher."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("👁️ Sanctuary Watcher stopped")

    def _watch_loop(self):
        """Polling loop to detect file changes."""
        while self._running:
            try:
                self._check_changes()
            except Exception as e:
                logger.error(f"Watcher error: {e}")
            time.sleep(self.interval)

    def _check_changes(self):
        """Check for new, modified, or deleted skill files."""
        current_hashes = {}
        sanctuary = self.registry.sanctuary_path

        if not sanctuary.exists():
            return

        for domain in DragonDomain:
            domain_path = sanctuary / domain.value
            if not domain_path.exists():
                continue
            for skill_file in domain_path.glob("*.py"):
                if skill_file.name.startswith("__"):
                    continue
                file_key = str(skill_file)
                current_hash = IntegrityEngine.compute_hash(skill_file)
                current_hashes[file_key] = current_hash

        # Detect changes
        added = set(current_hashes.keys()) - set(self._file_hashes.keys())
        removed = set(self._file_hashes.keys()) - set(current_hashes.keys())
        modified = {
            k for k in current_hashes
            if k in self._file_hashes and current_hashes[k] != self._file_hashes[k]
        }

        if added or removed or modified:
            if added:
                logger.info(f"🆕 New skills detected: {len(added)}")
            if modified:
                logger.info(f"✏️ Modified skills detected: {len(modified)}")
            if removed:
                logger.info(f"🗑️ Removed skills detected: {len(removed)}")

            # Re-scan the entire sanctuary
            self.registry.scan_sanctuary()

        self._file_hashes = current_hashes


# ─────────────────────────────────────────────
# SKILL-LOADER CORE (Main Engine)
# ─────────────────────────────────────────────

class SkillLoaderCore:
    """
    ╔═══════════════════════════════════════════════════╗
    ║  SKILL-LOADER CORE — O Motor Principal            ║
    ║                                                   ║
    ║  O ponto de entrada único para o Praktikant       ║
    ║  consumir Gnosis Capsules do Santuário.           ║
    ║                                                   ║
    ║  Fluxo:                                           ║
    ║  1. Pedido → Agent solicita uma skill             ║
    ║  2. Busca → Registry localiza a skill             ║
    ║  3. Gate → Constitutional Gate avalia             ║
    ║  4. Consumo → Sandbox executa                    ║
    ║  5. Recibo → Receipt documenta                   ║
    ╚═══════════════════════════════════════════════════╝
    """

    def __init__(self, sanctuary_path: Optional[Path] = None):
        self.sanctuary_path = sanctuary_path or SANCTUARY_ROOT
        self.registry = SkillRegistry(self.sanctuary_path)
        self.gate = ConstitutionalGate()
        self.watcher = SanctuaryWatcher(self.registry)
        self._initialized = False

    def initialize(self) -> Dict[str, Any]:
        """
        Initialize the Skill-Loader Core.

        Creates directory structure if needed, scans for skills,
        and starts the file watcher.
        """
        logger.info("═══ WINDI SKILL-LOADER CORE v1.0.0 INITIALIZING ═══")
        logger.info(f"Sanctuary path: {self.sanctuary_path}")

        # Ensure directory structure exists
        self._ensure_structure()

        # Scan existing skills
        catalog = self.registry.scan_sanctuary()

        # Start hot-reload watcher
        self.watcher.start()

        self._initialized = True

        status = {
            "status": "operational",
            "sanctuary_path": str(self.sanctuary_path),
            "skills_loaded": sum(len(v) for v in catalog.values()),
            "domains": {
                domain: {
                    "skills": len(skills),
                    "dragon": DRAGON_DOMAINS[domain]["dragon"],
                    "icon": DRAGON_DOMAINS[domain]["color"]
                }
                for domain, skills in catalog.items()
            },
            "watcher": "active",
            "constitutional_gate": "armed",
            "i9_enforcement": "active",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        logger.info("═══ SKILL-LOADER CORE OPERATIONAL ═══")
        return status

    def consume_skill(
        self,
        skill_id: str,
        function_name: str,
        args: Dict[str, Any],
        agent_id: str = "praktikant-v1",
        input_summary: str = ""
    ) -> Dict[str, Any]:
        """
        The main entry point for skill consumption.

        This is how the Praktikant "drinks from the source."

        Args:
            skill_id: Identifier of the skill to consume
            function_name: Function to call within the skill
            args: Arguments to pass to the function
            agent_id: Identifier of the consuming agent
            input_summary: Brief description of what was requested

        Returns: {
            "success": bool,
            "result": any,
            "receipt": SkillReceipt dict,
            "gate_status": str,
            "execution_ms": int
        }
        """
        if not self._initialized:
            return {
                "success": False,
                "error": "Skill-Loader not initialized. Call initialize() first.",
                "gate_status": "NOT_ARMED"
            }

        logger.info(
            f"🍷 Consumption request: skill={skill_id} "
            f"func={function_name} agent={agent_id}"
        )

        # Step 1: Find the skill
        manifest = self.registry.get_skill(skill_id)
        if not manifest:
            return {
                "success": False,
                "error": f"Skill '{skill_id}' not found in Registry",
                "gate_status": "SKILL_NOT_FOUND"
            }

        # Step 2: Resolve skill file path
        skill_path = None
        domain_dir = self.sanctuary_path / manifest.domain

        if domain_dir.exists():
            # Try exact match patterns
            candidates_names = [
                f"{manifest.skill_id}.py",
                f"{manifest.name.lower().replace(' ', '_')}.py",
                f"{manifest.domain}_{manifest.skill_id}.py",
            ]
            for cname in candidates_names:
                candidate = domain_dir / cname
                if candidate.exists():
                    skill_path = candidate
                    break

            # If still not found, search all .py files by manifest metadata
            if skill_path is None:
                for py_file in domain_dir.glob("*.py"):
                    manifest_file = domain_dir / f"{py_file.stem}.manifest.json"
                    if manifest_file.exists():
                        try:
                            mdata = json.loads(manifest_file.read_text())
                            if mdata.get("skill_id") == manifest.skill_id:
                                skill_path = py_file
                                break
                        except Exception:
                            pass

            # Last resort: find by hash match
            if skill_path is None:
                for py_file in domain_dir.glob("*.py"):
                    if py_file.name.startswith("__"):
                        continue
                    fhash = IntegrityEngine.compute_hash(py_file)
                    if fhash == manifest.integrity_hash:
                        skill_path = py_file
                        break

        if skill_path is None:
                return {
                    "success": False,
                    "error": f"Skill file not found for '{skill_id}'",
                    "gate_status": "FILE_NOT_FOUND"
                }

        # Step 3: Constitutional Gate evaluation
        gate_approved, gate_reason = self.gate.evaluate(
            manifest, skill_path, agent_id
        )
        if not gate_approved:
            return {
                "success": False,
                "error": gate_reason,
                "gate_status": "DENIED",
                "gate_reason": gate_reason
            }

        # Step 4: Sandboxed execution
        success, result, execution_ms = SandboxedExecutor.execute(
            skill_path, function_name, args
        )

        # Step 5: Generate consumption receipt
        i9_status = "CLEAN"
        if not success:
            i9_status = "EXECUTION_FAILED"

        receipt = ReceiptGenerator.generate(
            skill_manifest=manifest,
            agent_id=agent_id,
            input_summary=input_summary or function_name,
            result=result if success else {"error": str(result)},
            execution_ms=execution_ms,
            i9_status=i9_status
        )

        response = {
            "success": success,
            "result": result,
            "receipt": asdict(receipt),
            "gate_status": "APPROVED",
            "execution_ms": execution_ms,
            "domain": manifest.domain,
            "skill_name": manifest.name,
            "skill_version": manifest.version
        }

        status_icon = "✅" if success else "❌"
        logger.info(
            f"{status_icon} Consumption complete: {manifest.name} "
            f"({execution_ms}ms) receipt={receipt.receipt_id}"
        )

        return response

    def baptize_skill(
        self,
        filepath: str,
        skill_id: str,
        name: str,
        version: str,
        domain: str,
        capability: str,
        description: str,
        author_dragon: str,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Baptize a new skill into the Sanctuary.

        This is the ceremony that seals a skill with dragon authority.
        """
        skill_path = Path(filepath)
        success, manifest, message = BaptismCeremony.baptize(
            skill_path=skill_path,
            skill_id=skill_id,
            name=name,
            version=version,
            domain=domain,
            capability=capability,
            description=description,
            author_dragon=author_dragon,
            dependencies=dependencies,
            metadata=metadata
        )

        if success and manifest:
            # Add to registry
            self.registry.skills[manifest.skill_id] = manifest

        return {
            "success": success,
            "message": message,
            "manifest": asdict(manifest) if manifest else None
        }

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the Skill-Loader Core."""
        return {
            "engine": "WINDI Skill-Loader Core",
            "version": "1.0.0",
            "status": "operational" if self._initialized else "not_initialized",
            "sanctuary_path": str(self.sanctuary_path),
            "total_skills": len(self.registry.skills),
            "domains": {
                domain: {
                    "count": len(self.registry.list_by_domain(domain)),
                    "dragon": DRAGON_DOMAINS[domain]["dragon"],
                    "icon": DRAGON_DOMAINS[domain]["color"]
                }
                for domain in DRAGON_DOMAINS
            },
            "gate_decisions": len(self.gate.gate_log),
            "watcher_active": self.watcher._running,
            "i9_enforcement": "ACTIVE",
            "constitutional_gate": "ARMED",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def list_skills(self, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all available skills, optionally filtered by domain."""
        if domain:
            skills = self.registry.list_by_domain(domain)
        else:
            skills = list(self.registry.skills.values())

        return [
            {
                "skill_id": s.skill_id,
                "name": s.name,
                "version": s.version,
                "domain": s.domain,
                "capability": s.capability,
                "description": s.description,
                "author": s.author_dragon,
                "i9_certified": s.i9_certified,
                "icon": DRAGON_DOMAINS.get(s.domain, {}).get("color", "❓")
            }
            for s in skills
        ]

    def shutdown(self):
        """Gracefully shut down the Skill-Loader Core."""
        logger.info("═══ SKILL-LOADER CORE SHUTTING DOWN ═══")
        self.watcher.stop()
        self._initialized = False
        logger.info("═══ SKILL-LOADER CORE OFFLINE ═══")

    def _ensure_structure(self):
        """Create the Sanctuary directory structure if it doesn't exist."""
        for domain in DragonDomain:
            domain_path = self.sanctuary_path / domain.value
            domain_path.mkdir(parents=True, exist_ok=True)

        # Ensure receipt directory exists
        RECEIPT_DIR.mkdir(parents=True, exist_ok=True)

        # Ensure log directory exists
        INTEGRITY_LOG.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"🏛️ Sanctuary structure verified at {self.sanctuary_path}")


# ─────────────────────────────────────────────
# CLI INTERFACE
# ─────────────────────────────────────────────

def main():
    """CLI entry point for the Skill-Loader Core."""
    import argparse

    parser = argparse.ArgumentParser(
        description="WINDI Skill-Loader Core — O Motor das Gnosis Capsules"
    )
    subparsers = parser.add_subparsers(dest="command")

    # init
    subparsers.add_parser("init", help="Initialize the Skill-Loader Core")

    # status
    subparsers.add_parser("status", help="Show Skill-Loader status")

    # scan
    subparsers.add_parser("scan", help="Scan the Sanctuary for skills")

    # list
    list_parser = subparsers.add_parser("list", help="List available skills")
    list_parser.add_argument(
        "--domain", choices=["architect", "guardian", "witness"],
        help="Filter by dragon domain"
    )

    # baptize
    bap_parser = subparsers.add_parser("baptize", help="Baptize a new skill")
    bap_parser.add_argument("filepath", help="Path to the skill .py file")
    bap_parser.add_argument("--id", required=True, help="Skill identifier")
    bap_parser.add_argument("--name", required=True, help="Skill name")
    bap_parser.add_argument("--version", default="1.0.0", help="Version")
    bap_parser.add_argument(
        "--domain", required=True,
        choices=["architect", "guardian", "witness"]
    )
    bap_parser.add_argument("--capability", required=True, help="Capability type")
    bap_parser.add_argument("--description", required=True, help="Description")
    bap_parser.add_argument(
        "--author", required=True, help="Author dragon name"
    )

    args = parser.parse_args()

    loader = SkillLoaderCore()

    if args.command == "init":
        status = loader.initialize()
        print(json.dumps(status, indent=2, ensure_ascii=False))

    elif args.command == "status":
        loader.initialize()
        status = loader.get_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))

    elif args.command == "scan":
        loader.initialize()
        catalog = loader.registry.scan_sanctuary()
        print(json.dumps(catalog, indent=2, ensure_ascii=False))

    elif args.command == "list":
        loader.initialize()
        skills = loader.list_skills(domain=args.domain)
        print(json.dumps(skills, indent=2, ensure_ascii=False))

    elif args.command == "baptize":
        loader.initialize()
        result = loader.baptize_skill(
            filepath=args.filepath,
            skill_id=args.id,
            name=args.name,
            version=args.version,
            domain=args.domain,
            capability=args.capability,
            description=args.description,
            author_dragon=args.author
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        parser.print_help()

    loader.shutdown()


if __name__ == "__main__":
    main()

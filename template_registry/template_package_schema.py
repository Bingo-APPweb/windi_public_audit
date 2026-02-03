#!/usr/bin/env python3
"""
WINDI Template Package Schema & Validator v4.5
===============================================
Sistema de validação de templates institucionais.

Regra-mãe:
- Corporate Layer pode customizar forma
- Core DNA define os limites
- Institutional Layer define o contexto
- Governança não é opção. É infraestrutura.

KI verarbeitet. Mensch entscheidet. WINDI garantiert.
"""

import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum


class TemplateCategory(Enum):
    EU_OFFICIAL = "eu_official_v1"
    GERMAN_GOV = "german_gov_v1"
    WINDI_FORMAL = "windi_formal_v1"


class InstitutionalBaseType(Enum):
    EU_OFFICIAL = "eu_official_v1"
    GERMAN_GOV = "german_gov_v1"
    WINDI_FORMAL = "windi_formal_v1"


@dataclass
class CoreDNA:
    """
    DNA de governança WINDI.
    Este bloco NUNCA pode ser alterado por parceiros.
    """
    human_authorship_notice: bool = True
    governance_seal: bool = True
    eu_ai_act_disclosure: bool = True
    windi_publishing_attribution: bool = True
    qr_hash_verification: bool = True
    governance_seal_text: str = "KI verarbeitet. Mensch entscheidet. WINDI garantiert."
    compliance_declaration: str = "EU AI Act Compliant"
    publisher_name: str = "WINDI Publishing House"

    def is_valid(self) -> bool:
        return all([
            self.human_authorship_notice,
            self.governance_seal,
            self.eu_ai_act_disclosure,
            self.windi_publishing_attribution,
            self.qr_hash_verification
        ])

@dataclass
class InstitutionalBase:
    """
    Camada institucional base.
    Parceiros escolhem, mas não podem alterar.
    """
    base_id: str
    mandatory_sections: List[str] = field(default_factory=lambda: [
        "header", "subject_line", "body", "signature_block", "footer"
    ])
    formal_tone: bool = True
    language_scope: List[str] = field(default_factory=lambda: ["de", "en"])
    document_structure_required: bool = True

    @classmethod
    def get_valid_base_ids(cls) -> List[str]:
        return [e.value for e in InstitutionalBaseType]

    def is_valid_base(self) -> bool:
        return self.base_id in self.get_valid_base_ids()


@dataclass
class BrandingConfig:
    """Configuração de branding do parceiro."""
    logo_url: Optional[str] = None
    primary_color: str = "#1a5f2a"
    secondary_color: str = "#333333"
    accent_color: str = "#d4af37"
    font_family: str = "Arial, sans-serif"


@dataclass
class AdditionalSection:
    """Seção adicional definida pelo parceiro."""
    id: str
    title: Dict[str, str]
    placement: str
    required: bool = False
    content_template: str = ""


@dataclass
class CorporateLayer:
    """
    Camada corporativa customizável com limites.
    """
    organization_name: str
    branding: BrandingConfig = field(default_factory=BrandingConfig)
    additional_sections: List[AdditionalSection] = field(default_factory=list)
    terminology_overrides: Dict[str, str] = field(default_factory=dict)
    custom_css: str = ""

    FORBIDDEN_CSS_PATTERNS = [
        ".human-authorship-notice { display: none",
        ".governance-seal { display: none",
        ".verification-block { display: none",
        ".windi-footer { display: none",
        "visibility: hidden"
    ]

    def validate_css(self) -> Tuple[bool, List[str]]:
        violations = []
        css_lower = self.custom_css.lower()
        for pattern in self.FORBIDDEN_CSS_PATTERNS:
            if pattern.lower() in css_lower:
                violations.append(f"CSS proibido: tentativa de ocultar governança")
        return len(violations) == 0, violations

@dataclass
class TemplateMetadata:
    """Metadados para auditoria e rastreabilidade."""
    created_by_org: str
    reviewed_by_windi: bool = False
    compliance_checked: bool = False
    template_version: str = "1.0.0"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    review_notes: str = ""
    approved_by: Optional[str] = None


@dataclass
class TemplatePackage:
    """
    Pacote de template completo.
    Sempre tem 3 blocos obrigatórios:
    1. Core DNA (herdado, não editável)
    2. Institutional Base (escolhido, não editável)
    3. Corporate Layer (customizável com limites)
    """
    template_id: str
    institutional_base: InstitutionalBase
    corporate_layer: CorporateLayer
    metadata: TemplateMetadata
    core_dna: CoreDNA = field(default_factory=CoreDNA)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_id": self.template_id,
            "inherits": {
                "core_dna": "windi_core_v1",
                "institutional_base": self.institutional_base.base_id
            },
            "core_dna_enforced": asdict(self.core_dna),
            "institutional_constraints": {
                "base_id": self.institutional_base.base_id,
                "mandatory_sections": self.institutional_base.mandatory_sections,
                "formal_tone": self.institutional_base.formal_tone,
                "language_scope": self.institutional_base.language_scope
            },
            "corporate_layer": {
                "organization_name": self.corporate_layer.organization_name,
                "branding": asdict(self.corporate_layer.branding),
                "additional_sections": [asdict(s) for s in self.corporate_layer.additional_sections],
                "terminology_overrides": self.corporate_layer.terminology_overrides
            },
            "metadata": asdict(self.metadata)
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

class ValidationError:
    """Representa um erro de validação."""
    def __init__(self, code: str, message: str, severity: str = "error"):
        self.code = code
        self.message = message
        self.severity = severity

    def __repr__(self):
        return f"[{self.severity.upper()}] {self.code}: {self.message}"


class TemplateValidator:
    """
    Validador de Template Packages.
    RECUSA templates que violam governança.
    """

    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []

    def validate(self, package: TemplatePackage) -> Tuple[bool, List[ValidationError]]:
        self.errors = []
        self.warnings = []
        self._validate_core_dna(package.core_dna)
        self._validate_institutional_base(package.institutional_base)
        self._validate_corporate_layer(package.corporate_layer, package.institutional_base)
        self._validate_metadata(package.metadata)
        self._validate_template_id(package.template_id)
        is_valid = len(self.errors) == 0
        return is_valid, self.errors + self.warnings

    def _validate_core_dna(self, dna: CoreDNA):
        if not dna.human_authorship_notice:
            self.errors.append(ValidationError("CORE_DNA_001", "Human Authorship Notice não pode ser desativado"))
        if not dna.governance_seal:
            self.errors.append(ValidationError("CORE_DNA_002", "Governance Seal não pode ser desativado"))
        if not dna.eu_ai_act_disclosure:
            self.errors.append(ValidationError("CORE_DNA_003", "EU AI Act Disclosure não pode ser desativado"))
        if not dna.windi_publishing_attribution:
            self.errors.append(ValidationError("CORE_DNA_004", "WINDI Publishing Attribution não pode ser removida"))
        if not dna.qr_hash_verification:
            self.errors.append(ValidationError("CORE_DNA_005", "QR/Hash Verification não pode ser desativado"))
        canonical_seal = "KI verarbeitet. Mensch entscheidet. WINDI garantiert."
        if dna.governance_seal_text != canonical_seal:
            self.errors.append(ValidationError("CORE_DNA_006", f"Governance Seal text alterado"))
        if dna.compliance_declaration != "EU AI Act Compliant":
            self.errors.append(ValidationError("CORE_DNA_007", "Compliance declaration não pode ser alterada"))

    def _validate_institutional_base(self, base: InstitutionalBase):
        if not base.is_valid_base():
            valid_bases = ", ".join(base.get_valid_base_ids())
            self.errors.append(ValidationError("INST_BASE_001", f"Base inválida: '{base.base_id}'. Válidas: {valid_bases}"))
        for section in ["header", "body", "footer"]:
            if section not in base.mandatory_sections:
                self.errors.append(ValidationError("INST_BASE_002", f"Seção obrigatória removida: '{section}'"))
        if not base.document_structure_required:
            self.errors.append(ValidationError("INST_BASE_003", "document_structure_required não pode ser False"))

    def _validate_corporate_layer(self, corp: CorporateLayer, base: InstitutionalBase):
        if not corp.organization_name:
            self.errors.append(ValidationError("CORP_001", "organization_name é obrigatório"))
        css_valid, css_violations = corp.validate_css()
        if not css_valid:
            for v in css_violations:
                self.errors.append(ValidationError("CORP_002", v))
        for section in corp.additional_sections:
            if section.id in base.mandatory_sections:
                self.errors.append(ValidationError("CORP_003", f"Seção '{section.id}' conflita com obrigatória"))
        forbidden_terms = ["human_authorship", "governance", "ai_disclosure", "verification", "compliance", "windi"]
        for term in corp.terminology_overrides.keys():
            if any(ft in term.lower() for ft in forbidden_terms):
                self.errors.append(ValidationError("CORP_005", f"Não pode sobrescrever termo de governança: '{term}'"))

    def _validate_metadata(self, meta: TemplateMetadata):
        if not meta.created_by_org:
            self.errors.append(ValidationError("META_001", "created_by_org é obrigatório"))
        if not meta.reviewed_by_windi:
            self.warnings.append(ValidationError("META_002", "Template não revisado pela WINDI", "warning"))
        if not meta.compliance_checked:
            self.warnings.append(ValidationError("META_003", "Compliance check pendente", "warning"))

    def _validate_template_id(self, template_id: str):
        if not template_id:
            self.errors.append(ValidationError("ID_001", "template_id é obrigatório"))
            return
        reserved = ["windi_core", "eu_official", "german_gov", "windi_formal"]
        for r in reserved:
            if template_id.startswith(r):
                self.errors.append(ValidationError("ID_003", f"Prefixo reservado: '{r}'"))

    def generate_report(self, package: TemplatePackage) -> str:
        is_valid, issues = self.validate(package)
        lines = ["=" * 50, "WINDI Template Validator - Relatório", "=" * 50]
        lines.append(f"Template ID: {package.template_id}")
        lines.append(f"Organização: {package.corporate_layer.organization_name}")
        lines.append(f"Base: {package.institutional_base.base_id}")
        lines.append("")
        lines.append("✅ APROVADO" if is_valid else "❌ REPROVADO")
        lines.append(f"Erros: {len(self.errors)} | Avisos: {len(self.warnings)}")
        if self.errors:
            lines.append("\n--- ERROS ---")
            for e in self.errors:
                lines.append(f"  ❌ [{e.code}] {e.message}")
        if self.warnings:
            lines.append("\n--- AVISOS ---")
            for w in self.warnings:
                lines.append(f"  ⚠️ [{w.code}] {w.message}")
        lines.append("\nKI verarbeitet. Mensch entscheidet. WINDI garantiert.")
        return "\n".join(lines)


if __name__ == "__main__":
    print("WINDI Template Package Schema v4.5")
    print("=" * 40)
    validator = TemplateValidator()
    pkg = TemplatePackage(
        template_id="db_official_v1",
        institutional_base=InstitutionalBase(base_id="german_gov_v1"),
        corporate_layer=CorporateLayer(organization_name="Deutsche Bahn AG"),
        metadata=TemplateMetadata(created_by_org="Deutsche Bahn AG", reviewed_by_windi=True, compliance_checked=True)
    )
    print(validator.generate_report(pkg))



#!/usr/bin/env python3
"""
WINDI Compliance Agent - ISP Manager Client
============================================

Cliente para integracao com o ISP Manager Agent.
Consulta perfis institucionais (Institutional Style Profiles)
para validacao de conformidade.

O ISP define:
- Regras de governanca especificas da instituicao
- Baseline de SGE score esperado
- Requisitos regulatorios aplicaveis
- Constraints de processamento
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import requests


@dataclass
class ISPProfile:
    """Perfil Institucional (Institutional Style Profile)"""
    isp_id: str
    institution_name: str
    governance_tier: str  # tier1, tier2, tier3
    regulatory_frameworks: List[str]
    sge_baseline: Dict[str, float]
    identity_requirements: Dict
    constraints: Dict
    last_updated: str
    hash: str


class ISPManagerClient:
    """
    Cliente para ISP Manager Agent

    Funcionalidades:
    - Buscar perfil por ID
    - Listar perfis ativos
    - Validar documento contra regras do ISP
    - Obter baseline de conformidade
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8800",
        timeout: int = 30
    ):
        """
        Inicializa cliente.

        Args:
            base_url: URL base do ISP Manager
            timeout: Timeout em segundos
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._cache: Dict[str, ISPProfile] = {}

    def get_profile(self, isp_id: str, use_cache: bool = True) -> Optional[ISPProfile]:
        """
        Busca perfil institucional por ID.

        Args:
            isp_id: ID do ISP (ex: windi://isp/bundesregierung)
            use_cache: Se deve usar cache local

        Returns:
            ISPProfile ou None se nao encontrado
        """
        # Verificar cache
        if use_cache and isp_id in self._cache:
            return self._cache[isp_id]

        try:
            # Extrair nome do ISP do ID
            isp_name = isp_id.split("/")[-1] if "/" in isp_id else isp_id

            response = requests.get(
                f"{self.base_url}/api/v1/isp/{isp_name}",
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                profile = self._parse_profile(data)
                self._cache[isp_id] = profile
                return profile

            return None

        except requests.RequestException as e:
            # Em caso de erro, tentar carregar do filesystem
            return self._load_from_filesystem(isp_id)

    def _load_from_filesystem(self, isp_id: str) -> Optional[ISPProfile]:
        """Carrega ISP do filesystem como fallback"""
        try:
            isp_name = isp_id.split("/")[-1] if "/" in isp_id else isp_id
            isp_path = f"/opt/windi/isp/{isp_name}/manifest.json"

            with open(isp_path, 'r') as f:
                data = json.load(f)
                return self._parse_profile(data)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def _parse_profile(self, data: Dict) -> ISPProfile:
        """Converte dados JSON para ISPProfile"""
        # Calcular hash do perfil
        canonical = json.dumps(data, sort_keys=True, default=str)
        profile_hash = hashlib.sha256(canonical.encode()).hexdigest()

        return ISPProfile(
            isp_id=data.get("isp_id", data.get("id", "unknown")),
            institution_name=data.get("institution_name", data.get("name", "")),
            governance_tier=data.get("governance_tier", data.get("tier", "tier2")),
            regulatory_frameworks=data.get("regulatory_frameworks",
                                          data.get("frameworks", [])),
            sge_baseline=data.get("sge_baseline", {
                "mean": 70,
                "min_expected": 50,
                "std": 10
            }),
            identity_requirements=data.get("identity_requirements", {}),
            constraints=data.get("constraints", {}),
            last_updated=data.get("last_updated", datetime.now().isoformat()),
            hash=profile_hash
        )

    def list_active_profiles(self) -> List[str]:
        """Lista IDs de todos os perfis ativos"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/isp",
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                return [isp["isp_id"] for isp in data.get("isps", [])]

            return []

        except requests.RequestException:
            # Fallback: listar do filesystem
            return self._list_from_filesystem()

    def _list_from_filesystem(self) -> List[str]:
        """Lista ISPs do filesystem"""
        import os
        isp_base = "/opt/windi/isp"
        isps = []

        try:
            for entry in os.listdir(isp_base):
                manifest_path = os.path.join(isp_base, entry, "manifest.json")
                if os.path.isfile(manifest_path):
                    isps.append(f"windi://isp/{entry}")
        except OSError:
            pass

        return isps

    def get_compliance_requirements(self, isp_id: str) -> Dict:
        """
        Obtem requisitos de conformidade para um ISP.

        Returns:
            Dict com requisitos de conformidade
        """
        profile = self.get_profile(isp_id)
        if not profile:
            return {}

        return {
            "isp_id": profile.isp_id,
            "governance_tier": profile.governance_tier,
            "regulatory_frameworks": profile.regulatory_frameworks,
            "sge_requirements": {
                "minimum_score": profile.sge_baseline.get("min_expected", 50),
                "expected_range": {
                    "mean": profile.sge_baseline.get("mean", 70),
                    "std": profile.sge_baseline.get("std", 10)
                }
            },
            "identity_requirements": profile.identity_requirements,
            "constraints": profile.constraints
        }

    def validate_against_isp(
        self,
        isp_id: str,
        document_metadata: Dict
    ) -> Dict:
        """
        Valida metadados de documento contra regras do ISP.

        Args:
            isp_id: ID do ISP
            document_metadata: Metadados do documento

        Returns:
            Dict com resultado da validacao
        """
        profile = self.get_profile(isp_id)
        if not profile:
            return {
                "valid": False,
                "error": f"ISP not found: {isp_id}",
                "checks": []
            }

        checks = []

        # Verificar SGE score
        sge_score = document_metadata.get("sge_score")
        if sge_score is not None:
            min_expected = profile.sge_baseline.get("min_expected", 50)
            checks.append({
                "check": "sge_score",
                "passed": sge_score >= min_expected,
                "value": sge_score,
                "requirement": f">= {min_expected}"
            })

        # Verificar risk level
        risk_level = document_metadata.get("risk_level", "").lower()
        tier_risk_limits = {
            "tier1": ["low", "medium"],
            "tier2": ["low", "medium", "high"],
            "tier3": ["low", "medium", "high", "critical"]
        }
        allowed_risks = tier_risk_limits.get(profile.governance_tier, ["low"])
        checks.append({
            "check": "risk_level",
            "passed": risk_level in allowed_risks,
            "value": risk_level,
            "requirement": f"in {allowed_risks}"
        })

        # Verificar frameworks regulatorios
        doc_frameworks = document_metadata.get("regulatory_frameworks", [])
        required_frameworks = set(profile.regulatory_frameworks)
        doc_frameworks_set = set(doc_frameworks)
        missing = required_frameworks - doc_frameworks_set
        checks.append({
            "check": "regulatory_frameworks",
            "passed": len(missing) == 0,
            "value": doc_frameworks,
            "requirement": list(required_frameworks),
            "missing": list(missing) if missing else None
        })

        all_passed = all(c["passed"] for c in checks)

        return {
            "valid": all_passed,
            "isp_id": isp_id,
            "governance_tier": profile.governance_tier,
            "checks": checks,
            "timestamp": datetime.now().isoformat()
        }

    def clear_cache(self):
        """Limpa cache de perfis"""
        self._cache.clear()


# Exemplo de uso
if __name__ == "__main__":
    client = ISPManagerClient()

    # Listar perfis
    print("Active ISPs:", client.list_active_profiles())

    # Buscar perfil
    profile = client.get_profile("windi://isp/bundesregierung")
    if profile:
        print(f"\nProfile: {profile.institution_name}")
        print(f"Tier: {profile.governance_tier}")
        print(f"Frameworks: {profile.regulatory_frameworks}")

#!/usr/bin/env python3
"""
WINDI Onboarding Agent v1.0.0 — Three Dragons Protocol
=======================================================

Automated client onboarding with human-gated activation.
Draft-only until Sovereign approval. Zero-knowledge compliant.

"Escala sem Fricção"

Author: WINDI Publishing House / Three Dragons Protocol
License: Proprietary — WINDI Governance Framework
"""

import json
import hashlib
import argparse
import os
import glob
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any


class OnboardingAgent:
    """
    WINDI Onboarding Agent v1.0.0

    Automated client onboarding with human-gated activation.
    Draft-only until Sovereign approval. Zero-knowledge compliant.

    Stages:
    1. INTAKE - Validate client data
    2. CLASSIFY - Recommend governance level
    3. GENERATE - Create ISP draft
    4. VALIDATE - Run scanner
    5. PROVISION - Prepare environment
    6. ACTIVATE - Await human approval
    """

    # Required fields for intake
    REQUIRED_FIELDS = ["name", "legal_form", "sector", "country", "contact_email"]
    RECOMMENDED_FIELDS = ["employees_range", "revenue_range", "compliance_frameworks", "document_types", "regional_presence"]

    def __init__(self, config_path: str = '/opt/windi/agents/onboarding_agent/manifest.json'):
        """
        Initialize the Onboarding Agent.

        Args:
            config_path: Path to manifest.json
        """
        self.config_path = config_path
        self.base_path = os.path.dirname(config_path)

        # Load configuration
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                self.manifest = json.load(f)
        else:
            self.manifest = {"agent_id": "onboarding-agent", "version": "1.0.0"}

        # Define paths
        self.intake_path = os.path.join(self.base_path, 'intake')
        self.validation_path = os.path.join(self.base_path, 'validation')
        self.provisioning_path = os.path.join(self.base_path, 'provisioning', 'pending')
        self.logs_path = os.path.join(self.base_path, 'logs')
        self.isp_path = '/opt/windi/isp/'
        self.governance_levels_path = '/opt/windi/engine/governance_levels.json'

        # Ensure directories exist
        for path in [self.intake_path, self.validation_path, self.provisioning_path, self.logs_path]:
            os.makedirs(path, exist_ok=True)

        # Load governance levels
        self.governance_levels = self._load_governance_levels()

    def _load_governance_levels(self) -> Dict:
        """Load governance level definitions."""
        if os.path.exists(self.governance_levels_path):
            try:
                with open(self.governance_levels_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        # Default governance level rules
        return {
            "HIGH": {
                "sectors": ["financial_regulator", "central_bank", "forensic", "ministry_of_finance"],
                "requires_identity_license": True,
                "min_templates": 12,
                "min_keywords": 25
            },
            "MEDIUM": {
                "sectors": ["government_agency", "healthcare", "personal_data_processor"],
                "requires_identity_license": True,
                "min_templates": 10,
                "min_keywords": 20
            },
            "LOW": {
                "sectors": ["public_enterprise", "chamber_of_commerce", "corporation"],
                "requires_identity_license": False,
                "min_templates": 8,
                "min_keywords": 15
            }
        }

    def _generate_onboarding_id(self) -> str:
        """Generate unique onboarding ID."""
        now = datetime.now(timezone.utc)
        seq = int(now.strftime("%H%M%S")[:4])
        return f"ONB-{now.strftime('%Y%m%d')}-{seq:04d}"

    def start_onboarding(self, client_data: Dict) -> Dict:
        """
        Start new onboarding process.

        Args:
            client_data: Client information dictionary

        Returns:
            Onboarding checklist with status
        """
        now = datetime.now(timezone.utc)
        onboarding_id = self._generate_onboarding_id()

        checklist = {
            "onboarding_id": onboarding_id,
            "client_name": client_data.get("name", "Unknown"),
            "status": "IN_PROGRESS",
            "stages": {
                "intake": {"status": "pending", "details": {}},
                "classify": {"status": "pending", "details": {}},
                "generate": {"status": "pending", "details": {}},
                "validate": {"status": "pending", "details": {}},
                "provision": {"status": "pending", "details": {}},
                "activate": {"status": "AWAITING_SOVEREIGN_DECISION", "details": {}}
            },
            "client_data": client_data,
            "created_utc": now.isoformat(),
            "updated_utc": now.isoformat(),
            "estimated_completion": "Dependent on human review"
        }

        # Run intake immediately
        intake_result = self.intake(client_data)
        checklist["stages"]["intake"] = {
            "status": "complete" if intake_result["valid"] else "incomplete",
            "details": intake_result
        }

        # If intake valid, run classification
        if intake_result["valid"]:
            classify_result = self.classify(client_data)
            checklist["stages"]["classify"] = {
                "status": "complete",
                "details": classify_result
            }

        # Save checklist
        checklist_path = os.path.join(self.intake_path, f"{onboarding_id}.json")
        with open(checklist_path, 'w', encoding='utf-8') as f:
            json.dump(checklist, f, indent=2, ensure_ascii=False)

        return checklist

    def intake(self, client_data: Dict) -> Dict:
        """
        Stage 1: Validate client data.

        Args:
            client_data: Raw client information

        Returns:
            Validation result with missing/warning fields
        """
        result = {
            "valid": True,
            "missing_fields": [],
            "warnings": [],
            "data_completeness": 0
        }

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if not client_data.get(field):
                result["missing_fields"].append(field)
                result["valid"] = False

        # Check recommended fields
        for field in self.RECOMMENDED_FIELDS:
            if not client_data.get(field):
                result["warnings"].append(f"Recommended field '{field}' is missing")

        # Calculate completeness
        all_fields = self.REQUIRED_FIELDS + self.RECOMMENDED_FIELDS
        provided = sum(1 for f in all_fields if client_data.get(f))
        result["data_completeness"] = round((provided / len(all_fields)) * 100, 1)

        # Email validation
        email = client_data.get("contact_email", "")
        if email and "@" not in email:
            result["warnings"].append("contact_email appears invalid")

        return result

    def classify(self, client_data: Dict) -> Dict:
        """
        Stage 2: Recommend governance level.

        Args:
            client_data: Validated client information

        Returns:
            Classification with recommendation and reasoning
        """
        sector = client_data.get("sector", "").lower()
        frameworks = client_data.get("compliance_frameworks", [])

        result = {
            "recommended_level": "MEDIUM",
            "reasoning": [],
            "confidence": "MEDIUM",
            "requires_human_decision": True
        }

        # Check HIGH level indicators
        high_sectors = self.governance_levels.get("HIGH", {}).get("sectors", [])
        if any(s in sector for s in high_sectors):
            result["recommended_level"] = "HIGH"
            result["reasoning"].append(f"Sector '{sector}' indicates high governance requirements")

        # Check for regulatory frameworks
        high_frameworks = ["bsi-c5", "iso27001", "sox", "gdpr-high", "pci-dss"]
        if frameworks and any(f.lower() in [fw.lower() for fw in frameworks] for f in high_frameworks):
            result["recommended_level"] = "HIGH"
            result["reasoning"].append(f"Compliance frameworks {frameworks} indicate high governance")

        # Check LOW level indicators
        low_sectors = self.governance_levels.get("LOW", {}).get("sectors", [])
        if any(s in sector for s in low_sectors) and result["recommended_level"] != "HIGH":
            result["recommended_level"] = "LOW"
            result["reasoning"].append(f"Sector '{sector}' suggests standard governance sufficient")

        # Default reasoning
        if not result["reasoning"]:
            result["reasoning"].append("Based on provided data, MEDIUM governance is recommended as balanced default")

        # Confidence based on data completeness
        if len(result["reasoning"]) >= 2:
            result["confidence"] = "HIGH"
        elif not client_data.get("compliance_frameworks"):
            result["confidence"] = "LOW"
            result["reasoning"].append("Limited compliance framework data — review recommended")

        return result

    def generate_isp(self, client_data: Dict, governance_level: str) -> Dict:
        """
        Stage 3: Generate ISP draft.

        Args:
            client_data: Client information
            governance_level: Approved governance level

        Returns:
            ISP generation result with draft path
        """
        now = datetime.now(timezone.utc)
        profile_id = f"ISP-{client_data.get('name', 'ORG')[:10].upper().replace(' ', '-')}-{now.strftime('%Y%m%d')}"

        # Get level requirements
        level_config = self.governance_levels.get(governance_level, self.governance_levels.get("MEDIUM", {}))
        min_templates = level_config.get("min_templates", 10)
        min_keywords = level_config.get("min_keywords", 20)

        # Create draft structure
        isp_draft = {
            "profile_id": profile_id,
            "profile_name": client_data.get("name", ""),
            "version": "1.0.0-draft",
            "governance_level": governance_level,
            "institution": {
                "name": client_data.get("name", ""),
                "legal_form": client_data.get("legal_form", ""),
                "sector": client_data.get("sector", ""),
                "country": client_data.get("country", ""),
                "compliance_frameworks": client_data.get("compliance_frameworks", [])
            },
            "templates": [],
            "sge_keywords": [],
            "metadata": {
                "created_utc": now.isoformat(),
                "created_by": "onboarding-agent",
                "status": "DRAFT",
                "requires_human_review": True
            }
        }

        # Generate placeholder templates based on sector
        sector = client_data.get("sector", "general").lower()
        template_types = self._get_sector_templates(sector)

        for i, ttype in enumerate(template_types[:min_templates]):
            isp_draft["templates"].append({
                "template_id": f"TPL-{profile_id[:10]}-{i+1:03d}",
                "type": ttype,
                "status": "DRAFT",
                "requires_content": True
            })

        # Generate placeholder keywords
        base_keywords = self._get_sector_keywords(sector)
        isp_draft["sge_keywords"] = base_keywords[:min_keywords]

        # Save draft
        draft_dir = os.path.join(self.validation_path, profile_id)
        os.makedirs(draft_dir, exist_ok=True)
        draft_path = os.path.join(draft_dir, "isp_draft.json")

        with open(draft_path, 'w', encoding='utf-8') as f:
            json.dump(isp_draft, f, indent=2, ensure_ascii=False)

        return {
            "isp_draft_path": draft_path,
            "profile_id": profile_id,
            "template_count": len(isp_draft["templates"]),
            "keyword_count": len(isp_draft["sge_keywords"]),
            "governance_level": governance_level,
            "status": "DRAFT_GENERATED",
            "next_step": "validate_isp"
        }

    def _get_sector_templates(self, sector: str) -> List[str]:
        """Get template types for sector."""
        base_templates = [
            "official_letter", "internal_memo", "report", "policy_document",
            "meeting_minutes", "contract", "procedure", "form",
            "audit_report", "compliance_certificate", "decision_record", "notification"
        ]

        sector_specific = {
            "financial": ["risk_assessment", "regulatory_filing", "audit_trail"],
            "government": ["decree", "ordinance", "public_notice"],
            "healthcare": ["patient_consent", "clinical_report", "privacy_notice"]
        }

        templates = base_templates.copy()
        for key, extras in sector_specific.items():
            if key in sector:
                templates.extend(extras)

        return templates

    def _get_sector_keywords(self, sector: str) -> List[str]:
        """Get SGE keywords for sector."""
        base_keywords = [
            "compliance", "governance", "policy", "procedure", "regulation",
            "authorization", "approval", "review", "audit", "control",
            "risk", "assessment", "monitoring", "reporting", "documentation",
            "standard", "requirement", "guideline", "framework", "certification"
        ]

        sector_keywords = {
            "financial": ["fiduciary", "prudential", "capital", "liquidity", "solvency"],
            "government": ["sovereignty", "mandate", "jurisdiction", "statute", "decree"],
            "healthcare": ["confidentiality", "consent", "clinical", "safety", "quality"]
        }

        keywords = base_keywords.copy()
        for key, extras in sector_keywords.items():
            if key in sector:
                keywords.extend(extras)

        return keywords

    def validate_isp(self, isp_path: str) -> Dict:
        """
        Stage 4: Validate ISP draft.

        Args:
            isp_path: Path to ISP draft

        Returns:
            Validation result
        """
        result = {
            "valid": False,
            "grade": "N/A",
            "score": 0,
            "issues": [],
            "passed": False
        }

        if not os.path.exists(isp_path):
            result["issues"].append(f"ISP file not found: {isp_path}")
            return result

        try:
            with open(isp_path, 'r', encoding='utf-8') as f:
                isp = json.load(f)

            # Basic validation
            required = ["profile_id", "profile_name", "version", "governance_level", "templates", "sge_keywords"]
            for field in required:
                if field not in isp:
                    result["issues"].append(f"Missing required field: {field}")

            # Count templates and keywords
            templates = isp.get("templates", [])
            keywords = isp.get("sge_keywords", [])
            gov_level = isp.get("governance_level", "MEDIUM")

            level_config = self.governance_levels.get(gov_level, {})
            min_templates = level_config.get("min_templates", 10)
            min_keywords = level_config.get("min_keywords", 20)

            if len(templates) < min_templates:
                result["issues"].append(f"Insufficient templates: {len(templates)} < {min_templates} required for {gov_level}")

            if len(keywords) < min_keywords:
                result["issues"].append(f"Insufficient keywords: {len(keywords)} < {min_keywords} required for {gov_level}")

            # Calculate score
            template_score = min(100, (len(templates) / min_templates) * 100)
            keyword_score = min(100, (len(keywords) / min_keywords) * 100)
            result["score"] = round((template_score + keyword_score) / 2, 1)

            # Determine grade
            if result["score"] >= 95:
                result["grade"] = "A"
            elif result["score"] >= 85:
                result["grade"] = "B"
            elif result["score"] >= 70:
                result["grade"] = "C"
            else:
                result["grade"] = "D"

            result["valid"] = len(result["issues"]) == 0
            result["passed"] = result["valid"] and result["score"] >= 70

        except Exception as e:
            result["issues"].append(f"Validation error: {str(e)}")

        return result

    def provision(self, onboarding_id: str, isp_path: str) -> Dict:
        """
        Stage 5: Prepare environment for activation.

        Args:
            onboarding_id: Onboarding process ID
            isp_path: Path to validated ISP

        Returns:
            Provisioning result
        """
        now = datetime.now(timezone.utc)

        result = {
            "onboarding_id": onboarding_id,
            "status": "PROVISIONED",
            "actions_taken": [],
            "awaiting_activation": True,
            "activation_requires": "SOVEREIGN_DECISION"
        }

        # Load ISP
        try:
            with open(isp_path, 'r', encoding='utf-8') as f:
                isp = json.load(f)

            profile_id = isp.get("profile_id", "")

            # Create target directory (not activate yet)
            target_dir = os.path.join(self.provisioning_path, profile_id)
            os.makedirs(target_dir, exist_ok=True)

            # Copy ISP to provisioning (still draft)
            target_isp = os.path.join(target_dir, "isp.json")
            with open(target_isp, 'w', encoding='utf-8') as f:
                isp["metadata"]["provisioned_utc"] = now.isoformat()
                isp["metadata"]["status"] = "PROVISIONED_AWAITING_ACTIVATION"
                json.dump(isp, f, indent=2, ensure_ascii=False)

            result["actions_taken"].append(f"ISP copied to provisioning: {target_isp}")
            result["profile_id"] = profile_id

            # Check if identity license needed
            gov_level = isp.get("governance_level", "")
            if gov_level in ["HIGH", "MEDIUM"]:
                result["identity_license_required"] = True
                result["actions_taken"].append("Identity license flagged as required")

        except Exception as e:
            result["status"] = "PROVISION_ERROR"
            result["error"] = str(e)

        return result

    def request_activation(self, onboarding_id: str) -> Dict:
        """
        Stage 6: Request activation from Sovereign.

        Args:
            onboarding_id: Onboarding process ID

        Returns:
            Activation request summary
        """
        now = datetime.now(timezone.utc)

        # Load checklist
        checklist_path = os.path.join(self.intake_path, f"{onboarding_id}.json")
        if not os.path.exists(checklist_path):
            return {"error": f"Onboarding {onboarding_id} not found"}

        with open(checklist_path, 'r', encoding='utf-8') as f:
            checklist = json.load(f)

        # Create activation request
        request = {
            "request_id": f"ACT-{onboarding_id}",
            "onboarding_id": onboarding_id,
            "client_name": checklist.get("client_name", ""),
            "timestamp_utc": now.isoformat(),
            "status": "AWAITING_SOVEREIGN_DECISION",
            "summary": {
                "stages_complete": sum(1 for s in checklist["stages"].values() if s["status"] == "complete"),
                "stages_total": len(checklist["stages"]),
                "governance_level": checklist["stages"].get("classify", {}).get("details", {}).get("recommended_level", "MEDIUM")
            },
            "requires": [
                "Human review of ISP draft",
                "Approval of governance level classification",
                "Confirmation of identity requirements"
            ],
            "action": "HUMAN_DECISION_REQUIRED",
            "message": "This ISP cannot be activated without explicit Sovereign approval."
        }

        # Save request
        request_path = os.path.join(self.provisioning_path, f"{request['request_id']}.json")
        with open(request_path, 'w', encoding='utf-8') as f:
            json.dump(request, f, indent=2, ensure_ascii=False)

        # Update checklist
        checklist["stages"]["activate"]["status"] = "AWAITING_SOVEREIGN_DECISION"
        checklist["stages"]["activate"]["details"] = request
        checklist["updated_utc"] = now.isoformat()

        with open(checklist_path, 'w', encoding='utf-8') as f:
            json.dump(checklist, f, indent=2, ensure_ascii=False)

        return request

    def get_status(self, onboarding_id: str) -> Optional[Dict]:
        """Get status of an onboarding process."""
        checklist_path = os.path.join(self.intake_path, f"{onboarding_id}.json")
        if os.path.exists(checklist_path):
            with open(checklist_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"error": f"Onboarding {onboarding_id} not found"}

    def list_onboardings(self, status_filter: str = None) -> List[Dict]:
        """List all onboardings, optionally filtered."""
        onboardings = []

        for f in glob.glob(os.path.join(self.intake_path, "ONB-*.json")):
            try:
                with open(f, 'r', encoding='utf-8') as rf:
                    data = json.load(rf)
                    if status_filter is None or data.get("status") == status_filter:
                        onboardings.append({
                            "onboarding_id": data.get("onboarding_id"),
                            "client_name": data.get("client_name"),
                            "status": data.get("status"),
                            "created_utc": data.get("created_utc")
                        })
            except (json.JSONDecodeError, IOError):
                pass

        return sorted(onboardings, key=lambda x: x.get("created_utc", ""), reverse=True)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="WINDI Onboarding Agent v1.0.0 — Three Dragons Protocol",
        epilog="Escala sem Fricção"
    )
    parser.add_argument("--new", type=str, metavar="JSON_FILE", help="Start new onboarding from JSON file")
    parser.add_argument("--status", type=str, metavar="ONB_ID", help="Get onboarding status")
    parser.add_argument("--list", action="store_true", help="List all onboardings")
    parser.add_argument("--validate", type=str, metavar="ISP_PATH", help="Validate ISP draft")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")

    args = parser.parse_args()

    agent = OnboardingAgent()

    if args.new:
        if os.path.exists(args.new):
            with open(args.new, 'r', encoding='utf-8') as f:
                client_data = json.load(f)
            result = agent.start_onboarding(client_data)
            if args.json:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(f"Onboarding started: {result['onboarding_id']}")
                print(f"Client: {result['client_name']}")
                print(f"Status: {result['status']}")
                for stage, info in result["stages"].items():
                    print(f"  {stage}: {info['status']}")
        else:
            print(f"File not found: {args.new}")

    elif args.status:
        result = agent.get_status(args.status)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            if "error" in result:
                print(result["error"])
            else:
                print(f"Onboarding: {result['onboarding_id']}")
                print(f"Client: {result['client_name']}")
                print(f"Status: {result['status']}")

    elif args.list:
        onboardings = agent.list_onboardings()
        if args.json:
            print(json.dumps(onboardings, indent=2, ensure_ascii=False))
        else:
            if onboardings:
                print(f"Onboardings ({len(onboardings)}):")
                for o in onboardings:
                    print(f"  {o['onboarding_id']} | {o['client_name']} | {o['status']}")
            else:
                print("No onboardings found.")

    elif args.validate:
        result = agent.validate_isp(args.validate)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"Grade: {result['grade']} ({result['score']}%)")
            print(f"Passed: {result['passed']}")
            if result["issues"]:
                print("Issues:")
                for issue in result["issues"]:
                    print(f"  - {issue}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

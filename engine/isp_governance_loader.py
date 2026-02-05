"""
WINDI ISP Loader v2.0 - Dragon Council Pipeline
validate -> audit -> submit -> seal -> register
AI processes. Human decides. WINDI guarantees.
"""
import json, os
from governance_validator import GovernanceValidator
from submission_id import generate_submission_id, build_submission_header
from tamper_evidence import seal_record
from submission_registry import SubmissionRegistry

POLICY_VERSION = "2.0.0"

class ISPProfile:
    def __init__(self, data, path):
        self.data, self.path = data, path
        self.name = data.get("organization",{}).get("organization_name","Unknown")
        self.isp_id = data.get("isp_id","unknown")
        gov = data.get("governance",{})
        self.default_level = gov.get("default_level","LOW")
        self.allowed_levels = gov.get("allowed_levels",["LOW","MEDIUM","HIGH"])
        self.no_downgrade = gov.get("escalation_policy") == "no_downgrade"
        self.document_types = data.get("document_types",[])

    def get_doc_level(self, doc_type):
        for dt in self.document_types:
            if dt.get("type") == doc_type:
                return dt.get("governance_level", self.default_level)
        return self.default_level

class ISPLoader:
    LEVEL_ORDER = {"LOW":0, "MEDIUM":1, "HIGH":2}

    def __init__(self, config_path, isp_dir, submissions_dir=None):
        self.validator = GovernanceValidator(config_path)
        self.isp_dir = isp_dir
        self.sub_dir = submissions_dir or os.path.join(os.path.dirname(config_path),"submissions")
        self.registry = SubmissionRegistry(self.sub_dir)
        self.profiles = {}

    def discover(self):
        if not os.path.exists(self.isp_dir): return []
        return [n for n in os.listdir(self.isp_dir)
                if os.path.isfile(os.path.join(self.isp_dir,n,"profile.json"))]

    def load(self, name):
        p = os.path.join(self.isp_dir, name, "profile.json")
        with open(p) as f: data = json.load(f)
        prof = ISPProfile(data, p)
        self.profiles[name] = prof
        return prof

    def load_all(self):
        for n in self.discover(): self.load(n)
        return self.profiles

    def generate_document(self, profile_name, metadata=None, document_type=None,
                          governance_level=None, document_id=None, policy_version=None):
        pv = policy_version or POLICY_VERSION

        if profile_name not in self.profiles: self.load(profile_name)
        prof = self.profiles[profile_name]

        eff = governance_level or prof.default_level
        if document_type: eff = prof.get_doc_level(document_type)

        if eff not in prof.allowed_levels:
            raise ValueError(f"Level '{eff}' not allowed for {prof.name}. Allowed: {prof.allowed_levels}")
        if prof.no_downgrade and self.LEVEL_ORDER.get(eff,0) < self.LEVEL_ORDER.get(prof.default_level,0):
            raise ValueError(f"No-downgrade: {prof.name} min={prof.default_level}, requested={eff}")

        self.validator.validate(eff, metadata, pv)
        audit = self.validator.build_audit_record(eff, metadata, pv, document_id)

        lc = self.validator.get_level(eff)
        sid = None

        if lc.get("submission_package_id"):
            sid = generate_submission_id(self.sub_dir)
            audit["submission_id"] = sid

        if lc.get("tamper_evidence"):
            seal_record(audit)

        if sid:
            self.registry.register(sid, audit, document_id)

        pkg = {
            "status": "APPROVED",
            "isp_profile": profile_name,
            "organization": prof.name,
            "governance_level": eff,
            "governance_name": lc["name"],
            "policy_version": pv,
            "audit_record": audit,
        }
        if sid:
            pkg["submission_id"] = sid
            pkg["submission_header"] = build_submission_header(
                sid, eff, pv, self.validator.config_hash())
        return pkg

    def status(self):
        return {
            "engine": "WINDI ISP Loader v2.0",
            "policy_version": POLICY_VERSION,
            "config_hash": self.validator.config_hash()[:16]+"...",
            "profiles": self.discover(),
            "loaded": list(self.profiles.keys()),
            "submissions": self.registry.get_stats().get("total",0),
            "status": "OPERATIONAL",
        }


# === MEDIUM Effective Level Logic (added by MEDIUM deploy) ===


    # === Identity License Methods (added by Identity Governance deploy) ===
    def get_identity_license(self, profile_name):
        """Get identity license data for a profile."""
        if profile_name not in self.profiles:
            return {"status": "model_only", "scope": {}}
        profile = self.profiles[profile_name]
        return profile.get("identity_license", {"status": "model_only", "scope": {}})
    
    def get_identity_governance(self, profile_name):
        """Get full identity governance result for a profile."""
        from governance_validator import validate_identity_license
        profile = self.profiles.get(profile_name, {})
        config = self.config
        return validate_identity_license(profile, config)
    # === END Identity License Methods ===

LEVEL_ORDER_ISP = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}

def effective_level(profile, requested_level=None, document_type=None):
    """
    Determine the effective governance level based on:
    1. ISP default level
    2. Document type overrides
    3. Requested level (if any)
    4. No-downgrade enforcement
    5. Manual upgrade validation
    
    Returns the effective level string: LOW, MEDIUM, or HIGH
    """
    governance = profile.get("governance", {})
    default_level = governance.get("default_level", "LOW")
    policies = governance.get("policies", {})
    overrides = profile.get("document_type_overrides", {})
    
    # Start with default, apply document type override if applicable
    base_level = default_level
    if document_type and document_type in overrides:
        base_level = overrides[document_type]
    
    # If no specific request, use the base level
    level = requested_level if requested_level else base_level
    
    # Enforce no-downgrade minimum
    min_level = policies.get("no_downgrade_min_level")
    if min_level:
        if LEVEL_ORDER_ISP.get(level, 0) < LEVEL_ORDER_ISP.get(min_level, 0):
            level = min_level
    
    # Validate manual upgrade
    if requested_level and LEVEL_ORDER_ISP.get(requested_level, 0) > LEVEL_ORDER_ISP.get(base_level, 0):
        allowed_upgrades = policies.get("manual_upgrade", [])
        if requested_level not in allowed_upgrades:
            raise ValueError(
                f"Upgrade to {requested_level} not allowed for ISP "
                f"'{profile.get('isp_profile', 'unknown')}'. "
                f"Allowed upgrades: {allowed_upgrades}"
            )
    
    return level

# === END MEDIUM Effective Level Logic ===

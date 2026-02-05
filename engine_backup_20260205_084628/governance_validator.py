"""
WINDI Governance Validator v2.0
BIS Principle: Without complete metadata, the document is not valid.
AI processes. Human decides. WINDI guarantees.
"""
import json, hashlib
from datetime import datetime, timezone

class GovernanceValidator:
    def __init__(self, config_path):
        self.config_path = config_path
        with open(config_path) as f:
            self.config = json.load(f)

    def config_hash(self):
        with open(self.config_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    def get_level(self, level):
        level = level.upper()
        if level not in self.config["levels"]:
            raise ValueError(f"Unknown governance level: {level}")
        return self.config["levels"][level]

    def get_schema(self, block_name):
        return self.config.get("metadata_schemas", {}).get(block_name, {})

    def validate(self, level, metadata=None, policy_version=None):
        """Validate request. Raises ValueError if blocked."""
        level = level.upper()
        lc = self.get_level(level)
        errors = []

        if lc.get("policy_version_required") and not policy_version:
            errors.append("Policy version required but not provided.")

        if lc.get("metadata_required"):
            block = lc.get("metadata_block", "regulatory")
            schema = self.get_schema(block)
            required = schema.get("required_fields", [])
            allowed = schema.get("allowed_values", {})

            if not metadata:
                errors.append(f"Metadata block '{block}' required but not provided.")
            else:
                for f in required:
                    v = metadata.get(f)
                    if v is None or str(v).strip() == "":
                        errors.append(f"Required field empty/missing: '{f}'")
                for f, vals in allowed.items():
                    if f in metadata and metadata[f] not in vals:
                        errors.append(f"Invalid '{f}': '{metadata[f]}'. Allowed: {vals}")

        if errors:
            raise ValueError(
                f"GENERATION BLOCKED | Level: {level}\n"
                + "\n".join(f"  - {e}" for e in errors)
            )
        return True

    def build_audit_record(self, level, metadata, policy_version, document_id=None):
        level = level.upper()
        lc = self.get_level(level)
        record = {
            "governance_level": level,
            "governance_name": lc["name"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "audit_depth": lc.get("audit_trail", "basic"),
        }
        if document_id:
            record["document_id"] = document_id
        if lc.get("policy_version_required"):
            record["policy_version"] = policy_version
        if lc.get("config_version_lock"):
            record["config_hash"] = self.config_hash()
        if lc.get("metadata_required") and metadata:
            record["metadata"] = metadata
        return record


# === MEDIUM Institutional Validation (added by MEDIUM deploy) ===
LEVEL_ORDER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}

def validate_institutional_metadata(metadata, config):
    """Validate metadata against the institutional schema (MEDIUM level)."""
    schema = config.get("institutional_metadata_schema")
    if not schema:
        raise ValueError("institutional_metadata_schema not found in governance config")
    
    required = schema.get("required_fields", [])
    missing = [f for f in required if not (metadata.get(f) or "").strip()]
    if missing:
        raise ValueError(f"Missing required institutional metadata: {missing}")
    
    allowed = schema.get("allowed_values", {})
    for field, values in allowed.items():
        val = metadata.get(field)
        if val and val not in values:
            raise ValueError(
                f"Invalid value for {field}: '{val}' (allowed: {values})"
            )
    
    return True


def validate_metadata_by_block(level, metadata, config):
    """Route metadata validation based on the level's metadata_block type."""
    levels = config.get("levels", config)
    level_cfg = levels.get(level, {})
    
    if not level_cfg.get("metadata_required", False):
        return True  # LOW: no validation needed
    
    block = level_cfg.get("metadata_block", "regulatory")
    
    if block == "regulatory":
        # HIGH: use existing regulatory validation
        schema = config.get("regulatory_metadata_schema")
        if not schema:
            raise ValueError("regulatory_metadata_schema not found in governance config")
        required = schema.get("required_fields", [])
        missing = [f for f in required if not (metadata.get(f) or "").strip()]
        if missing:
            raise ValueError(f"Missing required regulatory metadata: {missing}")
        allowed = schema.get("allowed_values", {})
        for field, values in allowed.items():
            val = metadata.get(field)
            if val and val not in values:
                raise ValueError(f"Invalid value for {field}: '{val}' (allowed: {values})")
        return True
    
    elif block == "institutional":
        # MEDIUM: use institutional validation
        return validate_institutional_metadata(metadata, config)
    
    else:
        raise ValueError(f"Unknown metadata_block: {block}")

# === END MEDIUM Institutional Validation ===


# === Identity License Validator (added by Identity Governance deploy) ===
def validate_identity_license(profile_data, config):
    """
    Validate identity license status and determine governance behavior.
    
    Returns dict with:
      - license_status: effective status (may differ from profile if expired)
      - logo_allowed: bool
      - disclaimer_required: bool
      - institutional_tone_allowed: bool
      - audit_category: str for audit trail
      - disclaimer_text: dict (de/en/pt) or None
      - scope: dict of allowed identity elements
    """
    from datetime import date as date_type
    
    license_data = profile_data.get("identity_license", {})
    schema = config.get("identity_license_schema", {})
    behavior_matrix = schema.get("behavior_matrix", {})
    disclaimers = schema.get("disclaimer", {})
    
    # Determine effective status
    status = license_data.get("status", "model_only")
    
    # Check expiration for authorized licenses
    if status == "authorized":
        valid_from = license_data.get("valid_from")
        valid_until = license_data.get("valid_until")
        today = date_type.today().isoformat()
        
        if valid_from and today < valid_from:
            status = "pending"  # Not yet active
        elif valid_until and today > valid_until:
            status = "expired"  # License expired
    
    # Get behavior from matrix
    behavior = behavior_matrix.get(status, behavior_matrix.get("model_only", {}))
    scope = license_data.get("scope", {})
    
    # Override scope based on behavior
    logo_allowed = behavior.get("logo", False) and scope.get("logo", False)
    tone_allowed = behavior.get("tone", True) and scope.get("institutional_tone", True)
    disclaimer_required = behavior.get("disclaimer", True)
    audit_category = behavior.get("audit", "model_simulation")
    
    result = {
        "license_status": status,
        "logo_allowed": logo_allowed,
        "letterhead_allowed": scope.get("letterhead", False) and status == "authorized",
        "institutional_tone_allowed": tone_allowed,
        "values_reference_allowed": scope.get("values_reference", False),
        "official_address_allowed": scope.get("official_address", False) and status == "authorized",
        "disclaimer_required": disclaimer_required,
        "disclaimer_text": disclaimers if disclaimer_required else None,
        "audit_category": audit_category,
        "scope": scope,
        "authorization_ref": license_data.get("authorization_ref"),
        "restrictions": license_data.get("restrictions", [])
    }
    
    return result
# === END Identity License Validator ===

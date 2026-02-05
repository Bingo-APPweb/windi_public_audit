"""
WINDI Governance Health Check v1.0
Makes WINDI governance infrastructure observable.

Endpoint: /api/governance/status
Reports: policy version, ISPs loaded, licenses, registry status, event log stats.

Transforms WINDI from "working system" to "observable infrastructure."
"""

import json
import os
import hashlib
from datetime import datetime, timezone
from typing import Optional

try:
    from identity_detector import IdentityDetector
except ImportError:
    IdentityDetector = None

try:
    from governance_event_log import GovernanceEventLog
except ImportError:
    GovernanceEventLog = None

try:
    from medium_registry import MediumRegistry
except ImportError:
    MediumRegistry = None


GOVERNANCE_CONFIG_PATH = os.environ.get(
    "WINDI_GOVERNANCE_CONFIG",
    "/opt/windi/engine/governance_levels.json"
)

ISP_DIRECTORY = os.environ.get(
    "WINDI_ISP_DIR",
    "/opt/windi/engine/"
)

IDENTITY_DIR_PATH = os.environ.get(
    "WINDI_IDENTITY_DIR",
    "/opt/windi/config/identity_directory.json"
)


class GovernanceHealthCheck:
    """Comprehensive health check for WINDI governance infrastructure."""

    def __init__(
        self,
        governance_config_path: str = None,
        isp_directory: str = None,
        identity_dir_path: str = None,
        event_log: GovernanceEventLog = None,
        medium_registry: MediumRegistry = None,
        identity_detector: IdentityDetector = None
    ):
        self.governance_config_path = governance_config_path or GOVERNANCE_CONFIG_PATH
        self.isp_directory = isp_directory or ISP_DIRECTORY
        self.identity_dir_path = identity_dir_path or IDENTITY_DIR_PATH
        self.event_log = event_log
        self.medium_registry = medium_registry
        self.identity_detector = identity_detector

    def full_check(self) -> dict:
        """Run complete health check across all governance components."""
        now = datetime.now(timezone.utc).isoformat()

        result = {
            "status": "healthy",
            "checked_at": now,
            "components": {},
            "warnings": [],
            "errors": []
        }

        policy = self._check_policy()
        result["components"]["policy"] = policy
        if policy.get("status") == "error":
            result["errors"].append("Policy configuration not found or invalid")
        if policy.get("warnings"):
            result["warnings"].extend(policy["warnings"])

        isps = self._check_isps()
        result["components"]["isp_profiles"] = isps
        if isps.get("warnings"):
            result["warnings"].extend(isps["warnings"])

        identity = self._check_identity_directory()
        result["components"]["identity_directory"] = identity
        if identity.get("status") == "error":
            result["errors"].append("Identity directory not available")

        licenses = self._check_licenses()
        result["components"]["licenses"] = licenses
        if licenses.get("warnings"):
            result["warnings"].extend(licenses["warnings"])

        event_status = self._check_event_log()
        result["components"]["event_log"] = event_status

        registry = self._check_medium_registry()
        result["components"]["medium_registry"] = registry

        modules = self._check_engine_modules()
        result["components"]["engine_modules"] = modules
        if modules.get("missing"):
            result["warnings"].append(f"Missing engine modules: {modules['missing']}")

        if result["errors"]:
            result["status"] = "degraded"
        elif len(result["warnings"]) > 3:
            result["status"] = "warning"

        return result

    def _check_policy(self) -> dict:
        """Check governance policy configuration."""
        try:
            with open(self.governance_config_path, "r") as f:
                config = json.load(f)

            version = config.get("version", config.get("policy_version", "unknown"))
            levels = list(config.get("levels", config.get("governance_levels", {})).keys())

            config_str = json.dumps(config, sort_keys=True)
            config_hash = hashlib.sha256(config_str.encode()).hexdigest()[:12]

            return {
                "status": "ok",
                "policy_version": version,
                "active_levels": levels,
                "config_hash": config_hash,
                "path": self.governance_config_path,
                "warnings": []
            }
        except FileNotFoundError:
            return {
                "status": "error",
                "message": f"Config not found: {self.governance_config_path}",
                "warnings": ["Policy configuration file missing"]
            }
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "message": f"Invalid JSON: {e}",
                "warnings": ["Policy configuration corrupted"]
            }

    def _check_isps(self) -> dict:
        """Check loaded ISP profiles."""
        isps_found = []
        warnings = []

        try:
            for f in os.listdir(self.isp_directory):
                if f.startswith("isp_") and f.endswith(".json"):
                    path = os.path.join(self.isp_directory, f)
                    try:
                        with open(path, "r") as fh:
                            isp_data = json.load(fh)
                        isps_found.append({
                            "file": f,
                            "name": isp_data.get("institution", isp_data.get("name", f)),
                            "version": isp_data.get("version", "unknown"),
                            "level": isp_data.get("governance_level", "unknown")
                        })
                    except Exception as e:
                        warnings.append(f"ISP file {f} could not be loaded: {e}")
        except FileNotFoundError:
            warnings.append(f"ISP directory not found: {self.isp_directory}")

        return {
            "status": "ok" if isps_found else "warning",
            "loaded": len(isps_found),
            "profiles": isps_found,
            "warnings": warnings
        }

    def _check_identity_directory(self) -> dict:
        """Check identity directory status."""
        if self.identity_detector:
            stats = self.identity_detector.get_directory_stats()
            return {
                "status": "ok",
                "source": "detector_instance",
                **stats
            }

        try:
            with open(self.identity_dir_path, "r") as f:
                directory = json.load(f)

            institutions = directory.get("institutions", [])
            return {
                "status": "ok",
                "source": "file",
                "total_institutions": len(institutions),
                "with_isp": sum(1 for i in institutions if i.get("isp_exists")),
                "schema_version": directory.get("meta", {}).get("schema_version", "unknown"),
                "policy_version": directory.get("meta", {}).get("policy_version", "unknown"),
                "last_updated": directory.get("meta", {}).get("updated", "unknown")
            }
        except FileNotFoundError:
            return {"status": "error", "message": "Identity directory not found"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _check_licenses(self) -> dict:
        """Check identity license statuses."""
        warnings = []

        try:
            with open(self.identity_dir_path, "r") as f:
                directory = json.load(f)

            institutions = directory.get("institutions", [])
            statuses = {}
            expired = []

            now = datetime.now(timezone.utc).date()

            for inst in institutions:
                license_info = inst.get("identity_license", {})
                status = license_info.get("status", "unknown")
                statuses[status] = statuses.get(status, 0) + 1

                expires = license_info.get("expires")
                if expires:
                    try:
                        exp_date = datetime.fromisoformat(expires).date()
                        if exp_date < now:
                            expired.append(inst["name_official"])
                            warnings.append(f"Expired license: {inst['name_official']}")
                    except (ValueError, TypeError):
                        pass

            return {
                "status": "ok" if not expired else "warning",
                "total_licenses": len(institutions),
                "by_status": statuses,
                "expired": expired,
                "warnings": warnings
            }
        except Exception:
            return {"status": "unavailable", "warnings": []}

    def _check_event_log(self) -> dict:
        """Check event log status."""
        if not self.event_log:
            return {"status": "not_configured", "message": "Event log not initialized"}

        try:
            stats = self.event_log.get_event_stats()
            integrity = self.event_log.verify_chain_integrity()
            return {
                "status": "ok" if integrity["valid"] else "integrity_error",
                "chain_valid": integrity["valid"],
                **stats
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _check_medium_registry(self) -> dict:
        """Check medium registry status."""
        if not self.medium_registry:
            return {"status": "not_configured", "message": "Medium registry not initialized"}

        try:
            stats = self.medium_registry.get_stats()
            return {"status": "ok", **stats}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _check_engine_modules(self) -> dict:
        """Check presence of required engine modules."""
        required_modules = [
            "governance_validator.py",
            "submission_id.py",
            "tamper_evidence.py",
            "submission_registry.py",
            "audit_dashboard.py",
            "isp_loader.py",
            "windi_governance_api.py"
        ]

        evolution_modules = [
            "identity_detector.py",
            "governance_event_log.py",
            "medium_registry.py",
            "governance_health.py"
        ]

        found = []
        missing = []

        for module in required_modules:
            path = os.path.join(self.isp_directory, module)
            if os.path.exists(path):
                found.append(module)
            else:
                missing.append(module)

        evolution_found = []
        for module in evolution_modules:
            path = os.path.join(self.isp_directory, module)
            if os.path.exists(path):
                evolution_found.append(module)

        return {
            "status": "ok" if not missing else "warning",
            "core_modules": {"found": len(found), "total": len(required_modules)},
            "evolution_modules": {"found": len(evolution_found), "total": len(evolution_modules)},
            "found": found,
            "missing": missing,
            "evolution_installed": evolution_found
        }

    def quick_status(self) -> dict:
        """Quick one-line status for monitoring."""
        full = self.full_check()
        return {
            "status": full["status"],
            "checked_at": full["checked_at"],
            "policy_version": full["components"].get("policy", {}).get("policy_version", "unknown"),
            "isps_loaded": full["components"].get("isp_profiles", {}).get("loaded", 0),
            "institutions": full["components"].get("identity_directory", {}).get("total_institutions", 0),
            "event_log": full["components"].get("event_log", {}).get("status", "unknown"),
            "medium_registry": full["components"].get("medium_registry", {}).get("status", "unknown"),
            "warnings": len(full.get("warnings", [])),
            "errors": len(full.get("errors", []))
        }

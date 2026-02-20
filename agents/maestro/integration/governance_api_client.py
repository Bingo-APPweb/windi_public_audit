#!/usr/bin/env python3
"""
WINDI Maestro — Governance API Client
======================================

Client for WINDI Platform Governance API.
Provides read-only access to ISP profiles, findings, and case history.

API Endpoints (conceptual):
- /isp/{isp_id}/profile: Get ISP configuration
- /isp/{isp_id}/authorities: Get authority hierarchy
- /findings/{finding_hash}: Get finding metadata
- /cases/{case_id}: Get case details
- /cases/{case_id}/timeline: Get case timeline

Principles:
- READ-ONLY: Maestro queries, never modifies via API
- ZERO-CONTENT: Only metadata queries, never document content
- CACHED: Profile data cached to reduce API calls
- AUDIT-LOGGED: All API calls logged for traceability
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from functools import lru_cache

logger = logging.getLogger("WINDI.Maestro.GovernanceAPI")

# Mock data paths (in production, these would be API endpoints)
ISP_PROFILES_PATH = Path("/opt/windi/data/isp_profiles")
FINDINGS_PATH = Path("/opt/windi/data/findings")
CASES_PATH = Path("/opt/windi/data/cases")


class GovernanceAPIClient:
    """
    Client for WINDI Governance API.

    In production, this would make HTTP calls to the WINDI API.
    For now, reads from local data files.
    """

    def __init__(self, api_base: Optional[str] = None, cache_ttl: int = 300):
        """
        Initialize API client.

        Args:
            api_base: Base URL for WINDI API (or None for local mode)
            cache_ttl: Cache TTL in seconds
        """
        self.api_base = api_base
        self.cache_ttl = cache_ttl
        self._cache: Dict = {}
        self._cache_timestamps: Dict = {}

    def _cache_get(self, key: str) -> Optional[Dict]:
        """Get from cache if not expired."""
        if key not in self._cache:
            return None

        cached_at = self._cache_timestamps.get(key)
        if cached_at:
            age = (datetime.now(timezone.utc) - cached_at).total_seconds()
            if age > self.cache_ttl:
                del self._cache[key]
                del self._cache_timestamps[key]
                return None

        return self._cache[key]

    def _cache_set(self, key: str, value: Dict):
        """Set cache entry."""
        self._cache[key] = value
        self._cache_timestamps[key] = datetime.now(timezone.utc)

    def get_isp_profile(self, isp_id: str) -> Optional[Dict]:
        """
        Get ISP profile configuration.

        Args:
            isp_id: ISP identifier

        Returns:
            ISP profile dict or None if not found
        """
        cache_key = f"isp_profile:{isp_id}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        # Local mode: read from file
        profile_path = ISP_PROFILES_PATH / f"{isp_id}.json"

        if not profile_path.exists():
            logger.warning(f"ISP profile not found: {isp_id}")
            return None

        try:
            with open(profile_path, 'r') as f:
                profile = json.load(f)

            self._cache_set(cache_key, profile)
            logger.debug(f"Loaded ISP profile: {isp_id}")
            return profile

        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading ISP profile {isp_id}: {e}")
            return None

    def get_isp_authorities(self, isp_id: str) -> Dict:
        """
        Get authority hierarchy for ISP.

        Returns:
            Dict mapping roles to authority configurations
        """
        profile = self.get_isp_profile(isp_id)
        if not profile:
            return {}

        return profile.get("authorities", {})

    def get_isp_tier(self, isp_id: str) -> Optional[str]:
        """Get ISP tier (tier1/tier2/tier3)."""
        profile = self.get_isp_profile(isp_id)
        if not profile:
            return None

        return profile.get("tier", "tier2")

    def get_finding_metadata(self, finding_hash: str) -> Optional[Dict]:
        """
        Get finding metadata by hash.

        Args:
            finding_hash: Finding forensic hash

        Returns:
            Finding metadata (no content)
        """
        cache_key = f"finding:{finding_hash}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        # Local mode: search findings directory
        for finding_file in FINDINGS_PATH.glob("*.json"):
            try:
                with open(finding_file, 'r') as f:
                    finding = json.load(f)

                if finding.get("forensic_hash") == finding_hash:
                    # Return metadata only
                    metadata = {
                        "hash": finding_hash,
                        "capsule": finding.get("capsule"),
                        "severity": finding.get("severity"),
                        "invariants_at_risk": finding.get("invariants_at_risk"),
                        "timestamp": finding.get("timestamp"),
                        "isp_id": finding.get("isp_id")
                    }
                    self._cache_set(cache_key, metadata)
                    return metadata

            except (json.JSONDecodeError, IOError):
                continue

        logger.warning(f"Finding not found: {finding_hash[:16]}...")
        return None

    def get_case(self, case_id: str) -> Optional[Dict]:
        """
        Get case details.

        Args:
            case_id: Case identifier

        Returns:
            Case dict or None
        """
        case_path = CASES_PATH / f"{case_id}.json"

        if not case_path.exists():
            return None

        try:
            with open(case_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def get_case_timeline(self, case_id: str) -> List[Dict]:
        """Get case timeline events."""
        case = self.get_case(case_id)
        if not case:
            return []

        return case.get("timeline", [])

    def list_active_cases(
        self,
        isp_id: Optional[str] = None,
        status: Optional[str] = None,
        assigned_to: Optional[str] = None
    ) -> List[Dict]:
        """
        List active cases with optional filters.

        Args:
            isp_id: Filter by ISP
            status: Filter by status
            assigned_to: Filter by assignment

        Returns:
            List of case summaries
        """
        cases = []

        if not CASES_PATH.exists():
            return []

        for case_file in CASES_PATH.glob("CASE-*.json"):
            try:
                with open(case_file, 'r') as f:
                    case = json.load(f)

                # Apply filters
                if isp_id and case.get("isp_id") != isp_id:
                    continue
                if status and case.get("status") != status:
                    continue
                if assigned_to and case.get("assigned_to") != assigned_to:
                    continue

                # Skip closed cases for "active" query
                if case.get("status") == "closed":
                    continue

                # Return summary only
                cases.append({
                    "case_id": case.get("case_id"),
                    "status": case.get("status"),
                    "severity": case.get("severity"),
                    "isp_id": case.get("isp_id"),
                    "assigned_to": case.get("assigned_to"),
                    "created_at": case.get("timeline", [{}])[0].get("ts")
                })

            except (json.JSONDecodeError, IOError):
                continue

        return cases

    def get_role_contacts(self, isp_id: str, role: str) -> List[Dict]:
        """
        Get contacts for a role within ISP.

        Args:
            isp_id: ISP identifier
            role: Role name

        Returns:
            List of contact records
        """
        authorities = self.get_isp_authorities(isp_id)
        role_config = authorities.get(role, {})
        return role_config.get("contacts", [])

    def validate_human_authority(
        self,
        isp_id: str,
        human_id: str,
        required_role: str
    ) -> bool:
        """
        Validate that human has authority for role.

        Args:
            isp_id: ISP identifier
            human_id: Human identifier
            required_role: Role being claimed

        Returns:
            True if human is authorized for role
        """
        contacts = self.get_role_contacts(isp_id, required_role)

        for contact in contacts:
            if contact.get("id") == human_id or contact.get("email") == human_id:
                return True

        return False


# Singleton instance
_client: Optional[GovernanceAPIClient] = None


def get_client() -> GovernanceAPIClient:
    """Get or create singleton API client."""
    global _client
    if _client is None:
        _client = GovernanceAPIClient()
    return _client


# Convenience functions

def query_isp_profile(isp_id: str) -> Optional[Dict]:
    """Query ISP profile (convenience function)."""
    return get_client().get_isp_profile(isp_id)


def query_isp_tier(isp_id: str) -> Optional[str]:
    """Query ISP tier (convenience function)."""
    return get_client().get_isp_tier(isp_id)


def query_isp_authorities(isp_id: str) -> Dict:
    """Query ISP authorities (convenience function)."""
    return get_client().get_isp_authorities(isp_id)


def validate_human_for_role(isp_id: str, human_id: str, role: str) -> bool:
    """Validate human has authority for role (convenience function)."""
    return get_client().validate_human_authority(isp_id, human_id, role)

"""
WINDI Constitutional Package
============================
DECREE-001: A Árvore Viva (The Living Tree)

This package contains the constitutional documents and modules
that govern all WINDI organs.

Liga IA+H · 12 Abril 2026
"""

from .windi_tree import (
    WINDI_TREE,
    WindiOrgan,
    OrganTier,
    cross_validate_did,
    get_organ_navigation,
    get_server_operations_nav,
    detect_origin_from_request,
    is_valid_organ,
    build_return_url,
)

from .did_sovereign import (
    DIDTier,
    TIER_HIERARCHY,
    ORGAN_ACCESS,
    cross_validate_did as supreme_validate_did,
    validate_did_format,
    validate_did_sync,
    get_tier_info,
)

__version__ = "1.1.0"
__decree__ = "DECREE-001-LIVING-TREE"
__author__ = "Human Dragon"
__sealed__ = "2026-04-12"

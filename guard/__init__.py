"""
WINDI Surface Guard v0.2.0 — Infrastructure Healer
"Observar. Registrar. CURAR. Dissuadir."

WSG expands from DOM protection to infrastructure healing.

Modules:
- SENTINEL (v0.1.x): DOM Mutation Observer, Overlay Detection, Hash Validation
- HEALER (v0.2.0): Service Health, Link Integrity, CSS Drift, i18n Consistency

Constitutional Principle:
"WSG não toma decisões. WSG preserva decisões já tomadas."

I9 Safe: WSG operates within SEALED parameters.
Does not escalate autonomy. Heals within constitutional envelope.

Author: WINDI Publishing House
Version: 0.2.0
Date: 10 Feb 2026
"""

__version__ = "0.2.0"
__codename__ = "Infrastructure Healer"

from .wsg_health_monitor import ServiceHealthMonitor, WSG_MONITORED_SERVICES
from .wsg_link_checker import LinkIntegrityChecker
from .wsg_css_guard import CSSDriftDetector, CANONICAL_CSS_VARS
from .wsg_i18n_guard import I18nConsistencyGuard
from .wsg_hub import WSGHub

__all__ = [
    "ServiceHealthMonitor",
    "LinkIntegrityChecker",
    "CSSDriftDetector",
    "I18nConsistencyGuard",
    "WSGHub",
    "WSG_MONITORED_SERVICES",
    "CANONICAL_CSS_VARS",
]

WINDI Evolution API - Roadmap
Created: 01 Feb 2026 (post-deployment stabilization)
Status: PLANNED (not deployed)

PORT: 8081
DEPENDS ON: identity_detector, governance_event_log, medium_registry, governance_health
SOURCE: /opt/windi/engine/governance_api_evolution.py

PLANNED ENDPOINTS:
  GET  /api/governance/status        Quick health
  GET  /api/governance/health        Full check
  POST /api/governance/detect        Identity detection
  POST /api/governance/recommend     Governance Advisor
  POST /api/governance/medium/*      Medium Registry ops
  GET  /api/governance/events/*      Event Log queries
  GET  /api/governance/identity/*    Identity Directory

BABEL INTEGRATION:
  Proxy /api/gov/* on :8085 -> localhost:8081
  Add to session bar next to existing Governance button

PREREQUISITES BEFORE DEPLOY:
  - Stabilization period (sleep on it)
  - Review BABEL proxy routes
  - Test API standalone first
  - Then integrate

WINDI Evolution v1.0 = Stable Core (DONE)
WINDI Evolution v1.1 = API + BABEL Integration (NEXT)

--- UPDATE 01 Feb 2026 20:49 UTC ---
ACTUAL PORT: 8083 (8081 occupied by trust_bus, 8082 by gateway)
STATUS: HEARTBEAT ALIVE
PID: 200916
ENDPOINT ACTIVE: GET /api/governance/status -> {"status":"UP"}
NEXT: Connect GovernanceHealthCheck.quick_status() as /api/governance/health

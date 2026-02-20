#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════
 WINDI Sentinel State Writer — Patch for sentinel.py
 
 Este código deve ser integrado ao sentinel.py existente.
 A cada ciclo de monitoramento (~78ms), o Sentinel escreve
 seu estado atual em /opt/windi/data/sentinel_state.json
 
 Isso permite que a Sentinel Bridge API (port 8098) leia
 o estado sem interferir no ciclo de vigilância.
 
 COMO APLICAR:
 1. Adicionar write_state() ao loop principal do sentinel.py
 2. Chamar write_state(services_status) ao final de cada ciclo
 3. Chamar write_incident() quando houver mudança de estado
═══════════════════════════════════════════════════════════════
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

# ─── State File Paths ─────────────────────────────────────────

STATE_DIR = "/opt/windi/data"
STATE_FILE = os.path.join(STATE_DIR, "sentinel_state.json")
HISTORY_FILE = os.path.join(STATE_DIR, "sentinel_history.json")
INCIDENTS_FILE = os.path.join(STATE_DIR, "sentinel_incidents.json")

# Maximum history entries to keep
MAX_HISTORY = 1000
MAX_INCIDENTS = 200


def write_state(services, overall_status, cycle_ms):
    """
    Write current Sentinel state to JSON file.
    Called at the end of each monitoring cycle.
    
    Args:
        services: dict of service_name → {status, latency_ms, port, ...}
        overall_status: "NOMINAL" | "DEGRADED" | "WARNING" | "CRITICAL"
        cycle_ms: duration of this monitoring cycle in milliseconds
    
    Example services dict:
        {
            "governance": {"status": "healthy", "latency_ms": 12, "port": 8080, "critical": True},
            "babel": {"status": "healthy", "latency_ms": 8, "port": 8085, "critical": True},
            ...
        }
    """
    # Calculate summary
    statuses = [s.get('status', 'unknown') for s in services.values()]
    summary = {
        "total": len(statuses),
        "healthy": statuses.count('healthy'),
        "degraded": statuses.count('degraded'),
        "warning": statuses.count('warning'),
        "critical": statuses.count('critical'),
        "unknown": statuses.count('unknown'),
        "avg_latency_ms": _avg_latency(services),
    }
    
    state = {
        "status": overall_status,
        "services": services,
        "summary": summary,
        "cycle_ms": cycle_ms,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": _get_uptime(),
    }
    
    # Atomic write (write to temp, then rename)
    temp_file = STATE_FILE + ".tmp"
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(temp_file, 'w') as f:
            json.dump(state, f, indent=2)
        os.replace(temp_file, STATE_FILE)
    except Exception as e:
        print(f"[sentinel] ERROR writing state: {e}")


def write_history_point(overall_status, healthy_count, total_count, avg_latency):
    """
    Append a data point to health history.
    Called periodically (every 60 seconds) for pulse visualization.
    """
    point = {
        "t": datetime.now(timezone.utc).isoformat(),
        "s": overall_status[0],  # N/D/W/C (compact)
        "h": healthy_count,
        "n": total_count,
        "l": round(avg_latency, 1),
    }
    
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                history = json.load(f)
        except (json.JSONDecodeError, Exception):
            history = []
    
    history.append(point)
    
    # Trim to max size
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]
    
    try:
        temp_file = HISTORY_FILE + ".tmp"
        with open(temp_file, 'w') as f:
            json.dump(history, f)
        os.replace(temp_file, HISTORY_FILE)
    except Exception as e:
        print(f"[sentinel] ERROR writing history: {e}")


def write_incident(from_status, to_status, trigger_service, details=None):
    """
    Log a state change incident.
    Called when overall status changes (e.g., NOMINAL → DEGRADED).
    
    Args:
        from_status: previous overall status
        to_status: new overall status  
        trigger_service: service that triggered the change
        details: optional string with technical details
    """
    incident = {
        "id": f"INC-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "from_status": from_status,
        "to_status": to_status,
        "trigger": trigger_service,
        "details": details,
        "resolved": to_status == "NOMINAL",
    }
    
    incidents = []
    if os.path.exists(INCIDENTS_FILE):
        try:
            with open(INCIDENTS_FILE, 'r') as f:
                incidents = json.load(f)
        except (json.JSONDecodeError, Exception):
            incidents = []
    
    incidents.append(incident)
    
    # Trim
    if len(incidents) > MAX_INCIDENTS:
        incidents = incidents[-MAX_INCIDENTS:]
    
    try:
        temp_file = INCIDENTS_FILE + ".tmp"
        with open(temp_file, 'w') as f:
            json.dump(incidents, f, indent=2)
        os.replace(temp_file, INCIDENTS_FILE)
    except Exception as e:
        print(f"[sentinel] ERROR writing incident: {e}")
    
    # Log to stdout for journalctl
    direction = "↑" if _severity(to_status) > _severity(from_status) else "↓"
    print(f"[sentinel] {direction} INCIDENT: {from_status} → {to_status} (trigger: {trigger_service})")


def _avg_latency(services):
    """Calculate average latency from service dict."""
    latencies = [
        s.get('latency_ms', 0) 
        for s in services.values() 
        if s.get('latency_ms') is not None and s.get('latency_ms', 0) > 0
    ]
    return round(sum(latencies) / len(latencies), 1) if latencies else 0


def _severity(status):
    """Numeric severity for comparison."""
    return {"NOMINAL": 0, "DEGRADED": 1, "WARNING": 2, "CRITICAL": 3}.get(status, -1)


_start_time = time.time()

def _get_uptime():
    """Seconds since Sentinel started."""
    return round(time.time() - _start_time)


# ═══════════════════════════════════════════════════════════════
# INTEGRATION EXAMPLE
# ═══════════════════════════════════════════════════════════════
#
# In sentinel.py main loop, add these calls:
#
# ```python
# from sentinel_state_writer import write_state, write_history_point, write_incident
#
# previous_status = "NOMINAL"
# history_counter = 0
#
# while True:
#     start = time.time()
#     
#     # ... existing service checks ...
#     # services = check_all_services()
#     # overall = calculate_overall_status(services)
#     
#     cycle_ms = (time.time() - start) * 1000
#     
#     # Write state every cycle
#     write_state(services, overall, cycle_ms)
#     
#     # Write history every 60 cycles (~60 seconds at 1s intervals)
#     history_counter += 1
#     if history_counter >= 60:
#         write_history_point(overall, healthy_count, total, avg_latency)
#         history_counter = 0
#     
#     # Log incidents on state change
#     if overall != previous_status:
#         write_incident(previous_status, overall, trigger_service)
#         previous_status = overall
#     
#     time.sleep(1)  # or whatever the cycle interval is
# ```
# ═══════════════════════════════════════════════════════════════

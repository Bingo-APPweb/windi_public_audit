#!/usr/bin/env python3
"""
W-PROV-002 — Seed Collector
WINDI Publishing House · Kempten, Bavaria · 2026-03-13

Scans nginx access logs for verification requests and emits propagation events.
Runs every 15 minutes via cron.

Usage:
    python3 seed_collector.py [--dry-run] [--verbose]

State file: /opt/windi/data/seed_collector_state.json
    Tracks last processed position to avoid duplicate events.

Invariants:
    C-PROV-001: Sistema observa artefatos, nunca pessoas
    C-PROV-002: Fingerprints são anônimos — sem dados pessoais
"""

import re
import os
import sys
import json
import time
import hashlib
import argparse
from datetime import datetime
from urllib.parse import urlparse, parse_qs

# Configuration
LOG_PATH = os.environ.get('NGINX_LOG', '/var/log/nginx/access.log')
STATE_FILE = '/opt/windi/data/seed_collector_state.json'
PROPAGATION_API = os.environ.get('PROPAGATION_API', 'http://localhost:8091/propagation/event')

# Patterns to match verification requests
VERIFY_PATTERNS = [
    # /verify-public/?id=RECEIPT-ID
    r'GET /verify-public/\?id=([^\s&"]+)',
    # /verify-public/RECEIPT-ID
    r'GET /verify-public/([A-Z0-9\-]+)[\s"]',
    # /verify-public/document/RECEIPT-ID
    r'GET /verify-public/document/([^\s"]+)',
]

# Nginx combined log format regex
# Format: $remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent"
LOG_REGEX = re.compile(
    r'^(?P<ip>[\d\.]+)\s+'           # IP address
    r'-\s+'                           # -
    r'(?P<user>\S+)\s+'               # user
    r'\[(?P<time>[^\]]+)\]\s+'        # [time]
    r'"(?P<request>[^"]+)"\s+'        # "request"
    r'(?P<status>\d+)\s+'             # status
    r'(?P<bytes>\d+)\s+'              # bytes
    r'"(?P<referer>[^"]*)"'           # "referer"
)

def load_state():
    """Load last processed position from state file."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {'position': 0, 'inode': 0, 'last_run': None}

def save_state(state):
    """Save current position to state file."""
    state['last_run'] = datetime.utcnow().isoformat() + 'Z'
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def extract_domain(url):
    """Extract domain from URL."""
    if not url or url == '-':
        return 'direct'
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or ''
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain or 'direct'
    except:
        return 'direct'

def anonymize_ip(ip):
    """Create anonymous fingerprint from IP (C-PROV-002)."""
    return hashlib.sha256(ip.encode()).hexdigest()[:8]

def parse_log_time(time_str):
    """Parse nginx log time format."""
    # Format: 13/Mar/2026:10:30:45 +0100
    try:
        dt = datetime.strptime(time_str.split()[0], '%d/%b/%Y:%H:%M:%S')
        return int(dt.timestamp())
    except:
        return int(time.time())

def emit_event(event, dry_run=False, verbose=False):
    """Emit propagation event to W-PROV-002."""
    if dry_run:
        if verbose:
            print(f"  [DRY-RUN] Would emit: {event['ledger_anchor']} from {event['origin_domain']}")
        return True

    try:
        import urllib.request
        data = json.dumps(event).encode('utf-8')
        req = urllib.request.Request(
            PROPAGATION_API,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=2) as resp:
            if verbose:
                print(f"  [OK] {event['ledger_anchor']} from {event['origin_domain']}")
            return True
    except Exception as e:
        if verbose:
            print(f"  [FAIL] {event['ledger_anchor']}: {e}")
        return False

def process_log(dry_run=False, verbose=False):
    """Process nginx access log for verification events."""
    state = load_state()

    # Check if log file exists
    if not os.path.exists(LOG_PATH):
        print(f"[SEED] Log file not found: {LOG_PATH}")
        return 0

    # Check if log file was rotated (different inode)
    current_inode = os.stat(LOG_PATH).st_ino
    if state['inode'] != current_inode:
        state['position'] = 0
        state['inode'] = current_inode
        if verbose:
            print(f"[SEED] Log rotated, starting from beginning")

    events_found = 0
    events_emitted = 0

    with open(LOG_PATH, 'r', errors='ignore') as f:
        # Seek to last position
        f.seek(state['position'])

        for line in f:
            # Check if line contains verification request
            receipt_id = None
            for pattern in VERIFY_PATTERNS:
                match = re.search(pattern, line)
                if match:
                    receipt_id = match.group(1)
                    break

            if not receipt_id:
                continue

            # Parse log line
            log_match = LOG_REGEX.match(line)
            if not log_match:
                continue

            # Skip non-200 responses
            if log_match.group('status') != '200':
                continue

            events_found += 1

            # Build event (C-PROV-001, C-PROV-002 compliant)
            event = {
                'ledger_anchor': receipt_id,
                'event_type': 'SEED',
                'source_type': 'seed',
                'origin_domain': extract_domain(log_match.group('referer')),
                'country_hint': '',  # Not available in standard log
                'verify_node': 'nginx-log',
                'client_fp': anonymize_ip(log_match.group('ip')),
                'timestamp': parse_log_time(log_match.group('time'))
            }

            if emit_event(event, dry_run, verbose):
                events_emitted += 1

        # Save new position
        state['position'] = f.tell()

    save_state(state)
    return events_found, events_emitted

def main():
    parser = argparse.ArgumentParser(description='W-PROV-002 Seed Collector')
    parser.add_argument('--dry-run', action='store_true', help='Parse but do not emit events')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--reset', action='store_true', help='Reset state and reprocess entire log')
    args = parser.parse_args()

    if args.reset:
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
            print(f"[SEED] State reset")

    print(f"[SEED] W-PROV-002 Seed Collector starting...")
    print(f"[SEED] Log: {LOG_PATH}")
    print(f"[SEED] API: {PROPAGATION_API}")

    if args.dry_run:
        print(f"[SEED] Mode: DRY-RUN")

    start = time.time()
    found, emitted = process_log(args.dry_run, args.verbose)
    elapsed = time.time() - start

    print(f"[SEED] Completed in {elapsed:.2f}s")
    print(f"[SEED] Events found: {found}")
    print(f"[SEED] Events emitted: {emitted}")

if __name__ == '__main__':
    main()

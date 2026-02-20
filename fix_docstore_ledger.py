#!/usr/bin/env python3
"""Fix docStore.js bridgeToLedger:
  1. Tagged template literal fetch`...` → fetch(`...`,
  2. Payload alignment with Forensic Ledger API
"""
import uuid
from datetime import datetime

BT = chr(96)  # backtick

p = '/opt/windi/desktop/frontend/src/stores/docStore.js'
with open(p) as f:
    content = f.read()

# === FIX 1: Tagged template literal ===
# fetch`${LEDGER_URL}/receipts` → fetch(`${LEDGER_URL}/receipts`,
old_fetch = 'await fetch' + BT + '${LEDGER_URL}/receipts' + BT + ','
new_fetch = 'await fetch(' + BT + '${LEDGER_URL}/receipts' + BT + ','

if old_fetch in content:
    content = content.replace(old_fetch, new_fetch)
    print("FIX 1: Tagged template literal -> function call ✅")
else:
    print("FIX 1: Pattern not found (may already be fixed)")
    # Try alternate pattern without comma
    old_fetch2 = 'await fetch' + BT + '${LEDGER_URL}/receipts' + BT
    if old_fetch2 in content:
        # Need to be more careful here
        content = content.replace(old_fetch2, 'await fetch(' + BT + '${LEDGER_URL}/receipts' + BT, 1)
        print("FIX 1 (alt): Tagged template literal -> function call ✅")

# === FIX 2: Align payload with Ledger API ===
old_payload = """      body: JSON.stringify({
        doc_id: receipt.doc_id,
        action: receipt.action,
        integrity_hash: receipt.integrity_hash,
        timestamp: receipt.timestamp,
        user_id: receipt.user_id,
        metadata: receipt.metadata,
      }),
    });"""

new_payload = """      body: JSON.stringify({
        id: receipt.doc_id + '-' + Date.now(),
        doc_id: receipt.doc_id,
        doc_name: receipt.doc_name || 'Untitled',
        doc_type: receipt.doc_type || 'DOCUMENT',
        action: receipt.action,
        content_hash: receipt.integrity_hash,
        actor: receipt.user_id || 'human-operator',
        app: 'windi-d1-desktop',
        governance_level: receipt.governance_level || 'LOW',
        sge_score: receipt.sge_score || 0.0,
        timestamp: receipt.timestamp,
        metadata: receipt.metadata || {},
      }),
    });"""

if old_payload in content:
    content = content.replace(old_payload, new_payload)
    print("FIX 2: Payload aligned with Ledger API ✅")
else:
    print("FIX 2: Exact payload not found — checking partial match")
    if 'doc_id: receipt.doc_id,' in content and 'integrity_hash: receipt.integrity_hash,' in content:
        # Line-by-line replacement
        content = content.replace(
            'integrity_hash: receipt.integrity_hash,',
            'content_hash: receipt.integrity_hash,'
        )
        content = content.replace(
            'user_id: receipt.user_id,',
            'actor: receipt.user_id || \'human-operator\','
        )
        # Add missing fields after doc_id line
        content = content.replace(
            'doc_id: receipt.doc_id,\n        action: receipt.action,',
            'id: receipt.doc_id + \'-\' + Date.now(),\n        doc_id: receipt.doc_id,\n        doc_name: receipt.doc_name || \'Untitled\',\n        doc_type: receipt.doc_type || \'DOCUMENT\',\n        action: receipt.action,\n        app: \'windi-d1-desktop\',\n        governance_level: receipt.governance_level || \'LOW\',\n        sge_score: receipt.sge_score || 0.0,'
        )
        print("FIX 2 (partial): Payload fields updated ✅")

# Also fix the closing paren for fetch if needed
# After the fix, we should have fetch(`...`, { ... }); — need closing )
if 'await fetch(' + BT in content and content.count('await fetch(') > 0:
    # Check if there's a matching close paren
    pass  # The original });  should become }); with the ( already added

with open(p, 'w') as f:
    f.write(content)

# Verification
print("\n=== Verification ===")
with open(p) as f:
    lines = f.readlines()
for i, line in enumerate(lines[14:35], start=15):
    print(f"  L{i}: {line.rstrip()}")

print("\nDONE ✅")

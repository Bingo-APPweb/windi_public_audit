#!/usr/bin/env python3
"""Fix docStore.js: send both integrity_hash AND content_hash to satisfy both APIs"""

p = '/opt/windi/desktop/frontend/src/stores/docStore.js'
with open(p) as f:
    content = f.read()

# The current payload has content_hash (from our earlier fix).
# Need to ADD integrity_hash back alongside content_hash.
if 'content_hash: receipt.integrity_hash,' in content and 'integrity_hash:' not in content.split('bridgeToLedger')[1].split('res.ok')[0]:
    content = content.replace(
        'content_hash: receipt.integrity_hash,',
        'integrity_hash: receipt.integrity_hash,\n        content_hash: receipt.integrity_hash,'
    )
    print("FIX: Added integrity_hash alongside content_hash")
elif 'integrity_hash: receipt.integrity_hash,' in content and 'content_hash' not in content.split('bridgeToLedger')[1].split('res.ok')[0]:
    content = content.replace(
        'integrity_hash: receipt.integrity_hash,',
        'integrity_hash: receipt.integrity_hash,\n        content_hash: receipt.integrity_hash,'
    )
    print("FIX: Added content_hash alongside integrity_hash")
else:
    print("Both fields may already exist or pattern not matched")
    # Show what's there
    start = content.find('body: JSON.stringify')
    end = content.find('}),', start) + 3
    print(f"Current payload:\n{content[start:end]}")

with open(p, 'w') as f:
    f.write(content)

# Verify
print("\n=== Payload verification ===")
with open(p) as f:
    lines = f.readlines()
in_payload = False
for i, line in enumerate(lines, 1):
    if 'body: JSON.stringify' in line:
        in_payload = True
    if in_payload:
        print(f"  L{i}: {line.rstrip()}")
    if in_payload and '}),' in line:
        break

print("\nDONE")

#!/usr/bin/env python3
"""Fix GovernancePanel.jsx - backtick-safe using chr(96)"""
BT = chr(96)  # backtick

p = '/opt/windi/desktop/frontend/src/components/GovernancePanel.jsx'
with open(p) as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'className=' + BT + 'receipt-item' in line:
        lines[i] = line.replace(
            'className=' + BT + 'receipt-item',
            'className={' + BT + 'receipt-item'
        ).replace(BT + '>', BT + '}>')
        print(f"Fixed line {i+1}: {lines[i].rstrip()}")
    elif 'className=' + BT + 'receipt-status' in line:
        lines[i] = line.replace(
            'className=' + BT + 'receipt-status',
            'className={' + BT + 'receipt-status'
        ).replace(BT + '>', BT + '}>')
        print(f"Fixed line {i+1}: {lines[i].rstrip()}")

with open(p, 'w') as f:
    f.writelines(lines)

print("\nVerification:")
with open(p) as f:
    for i, line in enumerate(f, 1):
        if 'receipt-item' in line or 'receipt-status' in line:
            print(f"  L{i}: {line.rstrip()}")
print("\nDONE")

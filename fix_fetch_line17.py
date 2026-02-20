#!/usr/bin/env python3
"""Fix ONLY line 17: tagged template fetch -> function call"""
BT = chr(96)

p = '/opt/windi/desktop/frontend/src/stores/docStore.js'
with open(p) as f:
    lines = f.readlines()

line17 = lines[16]  # 0-indexed
print(f"BEFORE L17: {line17.rstrip()}")
print(f"BYTES: {repr(line17)}")

# Replace the whole line
old_part = 'await fetch' + BT + '${LEDGER_URL}/receipts' + BT + ','
new_part = 'await fetch(' + BT + '${LEDGER_URL}/receipts' + BT + ','

if old_part in line17:
    lines[16] = line17.replace(old_part, new_part)
    print(f"AFTER  L17: {lines[16].rstrip()}")
else:
    print(f"Pattern not in line. Forcing replacement...")
    # Just write the correct line
    indent = '    '
    lines[16] = indent + '  const res = ' + 'await fetch(' + BT + '${LEDGER_URL}/receipts' + BT + ', {\n'
    print(f"FORCED L17: {lines[16].rstrip()}")

# Also need closing ) for fetch - line 34 has });  should be });)  
# Actually: fetch( url, { ... }); needs the ) after }
# Line 34 is:     });
# Should be:      });)   -- no wait
# fetch(`url`, { method... body... }); 
# The ); closes the object AND the fetch(
# Actually }); closes the object literal }, then ); closes fetch(
# Current: }, ); — but we only have });
# Need: });\n to become  });\n — wait let me think
# fetch( `url`, { ... } );  
# The { starts at end of line 17, closes at line 34 with }
# Line 34: "    });" — this closes the object } and the fetch( with );
# So }); = } closes object, ); closes fetch — but currently it's just });
# Which means } closes object, ; ends statement — missing ) for fetch

line34 = lines[33]
print(f"\nBEFORE L34: {line34.rstrip()}")
if '});' in line34 and '});)' not in line34:
    lines[33] = line34.replace('});', '});)')  # Hmm that's wrong too
    # Actually: fetch(`url`, { body: JSON.stringify({...}), }); needs to be
    # fetch(`url`, { body: JSON.stringify({...}), });  — wait
    # Let me re-read the structure:
    # Line 17: const res = await fetch(`url`, {
    # Line 18:   method: 'POST',
    # Line 19:   headers: {...},
    # Line 20-33:   body: JSON.stringify({...}),
    # Line 34: });
    # With fetch( added, line 34 }); closes the options object } and statement ;
    # But fetch( is not closed! Need });)  — no, that's ugly
    # Better: change }); to });  and add ) before ;
    # }); → })  ;  — no
    # The correct form is: 
    # await fetch(`url`, { ... });  ← this is WRONG, fetch( not closed
    # await fetch(`url`, { ... })   ← } closes options, ) closes fetch
    # Then ; on same line: });  should become });  but wait...
    # Original without our fix: fetch`url`, { ... }); 
    # Tagged template: fetch`url` returns something, then , { ... }); is syntax error/comma operator
    # With fix: fetch(`url`, { ... }); — HERE }); means } closes options obj, ); closes fetch + semicolon
    # SO }); is actually CORRECT for fetch( ... ); 
    # } closes the options object, ) closes fetch(, ; ends statement
    # Let me revert line 34
    lines[33] = line34  # keep original
    print("L34: }); is correct for fetch(url, {...});")

with open(p, 'w') as f:
    f.writelines(lines)

print("\n=== Final check ===")
with open(p) as f:
    all_lines = f.readlines()
for i in [16, 17, 33, 34]:
    print(f"  L{i+1}: {all_lines[i].rstrip()}")
print("\nDONE")

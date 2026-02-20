#!/usr/bin/env python3
"""
WINDI A4 Desk BABEL — Phase 1 HOTFIX Patch
Version: v4.2 → v4.3
Date: 2026-02-10
Fixes: BUG-001 (Delete), BUG-002 (Witness), UIX-001 (WSG investigation)

Usage on Strato:
  cd /opt/windi/a4desk-editor
  python3 /tmp/patch_v43_phase1.py

BACKUP MUST BE DONE FIRST!
"""

import re
import sys
import os

TARGET = '/opt/windi/a4desk-editor/a4desk_tiptap_babel.py'

if not os.path.exists(TARGET):
    print(f"❌ File not found: {TARGET}")
    sys.exit(1)

with open(TARGET, 'r', encoding='utf-8') as f:
    content = f.read()

original = content  # keep original for comparison
fixes_applied = []

# ═══════════════════════════════════════════════════════════════
# BUG-001: Delete fails on 2nd execution
# Root cause: hideReauth() nulls pendingAction, and confirmReauth
# can leave state corrupted if reauth fails or times out.
# Fix: Robust deleteDocById + bulletproof confirmReauth
# ═══════════════════════════════════════════════════════════════

# Fix 1a: Replace hideReauth to NOT null pendingAction
old_hideReauth = "function hideReauth(){pendingAction=null;document.getElementById('reauthOverlay').classList.remove('show')}"
new_hideReauth = "function hideReauth(){document.getElementById('reauthOverlay').classList.remove('show');document.getElementById('reauthPassword').value=''}"

if old_hideReauth in content:
    content = content.replace(old_hideReauth, new_hideReauth)
    fixes_applied.append("BUG-001a: hideReauth no longer nulls pendingAction prematurely")
else:
    print("⚠️  BUG-001a: hideReauth pattern not found exactly — checking variant...")
    # Try a more flexible search
    if "function hideReauth()" in content and "pendingAction=null" in content:
        # Find the hideReauth function and fix it
        content = content.replace(
            "function hideReauth(){pendingAction=null;",
            "function hideReauth(){"
        )
        fixes_applied.append("BUG-001a: hideReauth — removed premature pendingAction=null (variant)")

# Fix 1b: Replace confirmReauth to properly save and clear callback
old_confirmReauth_line = "if(res.ok){const cb=pendingAction?pendingAction.callback:null;hideReauth();if(cb)cb()}"
new_confirmReauth_line = "if(res.ok){const cb=pendingAction?pendingAction.callback:null;pendingAction=null;hideReauth();if(cb)cb()}else{toast('Authentifizierung fehlgeschlagen','error')}"

if old_confirmReauth_line in content:
    content = content.replace(old_confirmReauth_line, new_confirmReauth_line)
    fixes_applied.append("BUG-001b: confirmReauth now nulls pendingAction explicitly + error toast")
else:
    print("⚠️  BUG-001b: confirmReauth pattern not found exactly")

# Fix 1c: Make deleteDocById more robust — fresh closure each time
old_delete = """async function deleteDocById(id){
    if(!confirm('Loeschen?'))return;
    const targetId=id;
    showReauth('DELETE',async function(){
        const res=await fetch('/api/document/'+targetId,{method:'DELETE',headers:{'X-Session-ID':sessionId}});
        if(res.ok){loadDocs();if(docId===targetId)newDoc();toast('Geloescht','success')}
        else{toast('Fehler beim Loeschen','error')}
    });
}"""

new_delete = """async function deleteDocById(id){
    if(!confirm('Dokument wirklich loeschen?'))return;
    const targetId=String(id);
    const deleteFn=async function(){
        try{
            const res=await fetch('/api/document/'+targetId,{method:'DELETE',headers:{'X-Session-ID':sessionId}});
            if(res.ok){
                await loadDocs();
                if(docId===targetId)newDoc();
                toast('Dokument geloescht','success');
            }else{
                const err=await res.json().catch(function(){return{}});
                toast(err.error||'Fehler beim Loeschen','error');
            }
        }catch(e){console.error('Delete error:',e);toast('Netzwerkfehler','error')}
    };
    showReauth('DELETE',deleteFn);
}"""

if old_delete in content:
    content = content.replace(old_delete, new_delete)
    fixes_applied.append("BUG-001c: deleteDocById — fresh closure, try/catch, await loadDocs")
else:
    print("⚠️  BUG-001c: deleteDocById exact pattern not found — trying flexible match...")
    # Try line-by-line match
    if "async function deleteDocById(id){" in content:
        # Find start and end
        start_idx = content.index("async function deleteDocById(id){")
        # Find the closing brace — count braces
        brace_count = 0
        end_idx = start_idx
        found_first = False
        for i in range(start_idx, min(start_idx + 500, len(content))):
            if content[i] == '{':
                brace_count += 1
                found_first = True
            elif content[i] == '}':
                brace_count -= 1
                if found_first and brace_count == 0:
                    end_idx = i + 1
                    break
        
        if end_idx > start_idx:
            old_fn = content[start_idx:end_idx]
            content = content[:start_idx] + new_delete + content[end_idx:]
            fixes_applied.append("BUG-001c: deleteDocById replaced (flexible match)")
        else:
            print("❌ BUG-001c: Could not find function boundaries")

# ═══════════════════════════════════════════════════════════════
# BUG-002: Witness placeholder persists — not cleared on newDoc
# Fix: Clear witness fields in newDoc() and when loading a doc
# ═══════════════════════════════════════════════════════════════

# Find newDoc function and add witness field clearing
# First, let's find what newDoc currently does
if "function newDoc(){" in content or "function newDoc()" in content:
    # Add witness clearing after the function opening or after existing field resets
    # Look for patterns like docId=null or editor clearing
    
    # Strategy: Add clearWitnessFields() function and call it from newDoc
    
    # Add the helper function before newDoc or before the first function
    clear_witness_fn = """function clearWitnessFields(){
    var wn=document.getElementById('fieldWitnessName');if(wn){wn.value='';wn.removeAttribute('readonly')}
    var wi=document.getElementById('fieldWitnessId');if(wi){wi.value='';wi.removeAttribute('readonly')}
    var wp=document.getElementById('fieldWitnessPosition');if(wp){wp.value='';wp.removeAttribute('readonly')}
    var wr=document.getElementById('fieldWitnessRelation');if(wr)wr.selectedIndex=0;
}
"""
    
    # Insert clearWitnessFields before newDoc
    if "function newDoc(){" in content:
        content = content.replace(
            "function newDoc(){",
            clear_witness_fn + "function newDoc(){"
        )
        fixes_applied.append("BUG-002a: Added clearWitnessFields() helper function")
    elif "function newDoc()" in content:
        content = content.replace(
            "function newDoc()",
            clear_witness_fn + "function newDoc()"
        )
        fixes_applied.append("BUG-002a: Added clearWitnessFields() helper function")
    
    # Now find where newDoc sets docId=null and add clearWitnessFields() call after it
    # Common pattern: docId=null in newDoc
    if "function newDoc(){docId=null" in content:
        content = content.replace(
            "function newDoc(){docId=null",
            "function newDoc(){docId=null;clearWitnessFields()"
        )
        fixes_applied.append("BUG-002b: newDoc() now clears witness fields")
    elif "function newDoc(){" in content:
        # Just add it right after the opening brace
        content = content.replace(
            "function newDoc(){",
            "function newDoc(){clearWitnessFields();",
            1  # only first occurrence
        )
        fixes_applied.append("BUG-002b: newDoc() now clears witness fields (after opening)")
    
    # Also: When loading a document, populate witness fields from doc data
    # Find loadDoc function and add witness population
    if "async function loadDoc(" in content:
        # After loading doc data, populate witness fields
        # Look for where witness data is available after fetch
        # The response includes "witness" field (line 1504)
        # We need to find where the doc data is processed in loadDoc
        
        # Add witness population in the loadDoc success handler
        witness_populate = """
    if(data.witness){
        var w=data.witness;
        var wn=document.getElementById('fieldWitnessName');if(wn)wn.value=w.name||'';
        var wi=document.getElementById('fieldWitnessId');if(wi)wi.value=w.employee_id||w.id||'';
        var wp=document.getElementById('fieldWitnessPosition');if(wp)wp.value=w.position||'';
    }else{clearWitnessFields()}"""
        
        # Find a good insertion point — after status update in loadDoc
        # Look for updateStatus pattern in loadDoc context
        if "updateStatus(data.status)" in content:
            content = content.replace(
                "updateStatus(data.status)",
                "updateStatus(data.status);" + witness_populate,
                1  # first occurrence only
            )
            fixes_applied.append("BUG-002c: loadDoc() now populates/clears witness fields from doc data")
        else:
            print("⚠️  BUG-002c: Could not find updateStatus in loadDoc — manual insertion needed")

# ═══════════════════════════════════════════════════════════════
# UIX-001: WSG Badge — investigate and report
# The wsg-init.js file doesn't exist at expected path.
# Check if WSG badge is inline in the HTML/JS
# ═══════════════════════════════════════════════════════════════

wsg_found = False
wsg_locations = []

# Check for WSG badge patterns in main file
for pattern in ['WSG Active', 'wsg-status-badge', 'createStatusBadge', 'wsg-init', 'WSG_VERSION']:
    if pattern in content:
        wsg_found = True
        wsg_locations.append(pattern)

if wsg_found:
    print(f"ℹ️  UIX-001: WSG code found inline: {', '.join(wsg_locations)}")
    
    # If badge has position:fixed;bottom, move it
    if 'position:fixed;bottom:' in content or 'position: fixed; bottom:' in content:
        # Replace bottom positioning with left positioning
        content = re.sub(
            r'(wsg.*?position:\s*fixed;\s*bottom:\s*\d+px;\s*)right:\s*\d+px',
            r'\1left:12px',
            content,
            flags=re.IGNORECASE
        )
        fixes_applied.append("UIX-001: WSG badge moved from bottom-right to bottom-left")
else:
    print("ℹ️  UIX-001: No WSG badge code found inline — badge may be loaded externally or already removed")
    print("   Check: find /opt/windi/ -name '*wsg*' -o -name '*WSG*' 2>/dev/null")

# ═══════════════════════════════════════════════════════════════
# VERSION BUMP: v4.2 → v4.3 (or v4.7-gov → v4.7.1-gov)
# ═══════════════════════════════════════════════════════════════

# Update version strings
version_updates = [
    ('v4.2', 'v4.3'),
    ('v4.7-gov', 'v4.7.1-gov'),
]

for old_v, new_v in version_updates:
    if old_v in content:
        count = content.count(old_v)
        content = content.replace(old_v, new_v)
        fixes_applied.append(f"VERSION: {old_v} → {new_v} ({count} occurrences)")

# ═══════════════════════════════════════════════════════════════
# WRITE PATCHED FILE
# ═══════════════════════════════════════════════════════════════

if content == original:
    print("\n⚠️  No changes were made — patterns may have changed since briefing")
    sys.exit(1)

with open(TARGET, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n" + "═" * 60)
print("✅ PATCH v4.3 Phase 1 APPLIED")
print("═" * 60)
print(f"\nFixes applied ({len(fixes_applied)}):")
for i, fix in enumerate(fixes_applied, 1):
    print(f"  {i}. {fix}")

print(f"\nFile: {TARGET}")
print(f"Size: {len(content):,} bytes")
print("\n⚡ NEXT STEPS:")
print("  1. Restart: pkill -f a4desk_tiptap_babel.py")
print("  2. Start:   cd /opt/windi/a4desk-editor && nohup python3 a4desk_tiptap_babel.py > /tmp/a4desk.log 2>&1 &")
print("  3. Test:    curl -s http://localhost:8085/health")
print("  4. Test DELETE: Create doc → Delete → Create another → Delete again")
print("  5. Test WITNESS: New doc → Check Prüfer fields are empty")
print("  6. Test WITNESS: Load existing doc → Check Prüfer fields populate")
print("\n🐉 Three Dragons Protocol — I1-I9 ACTIVE")

"""
WINDI Dragon Hub — Patch Helper
================================
Corre este script para ver EXACTAMENTE o que patchar no servidor :8108.

Uso:
    python3 patch_helper.py <caminho_para_servidor.py>

Exemplo:
    python3 patch_helper.py /opt/windi/engine/dragon_server.py

Output: mostra a linha exacta a substituir + o código novo.
"""

import sys
import re
from pathlib import Path


PATCH_IMPORT = """
# ── Dragon Hub (inserted by patch_helper) ────────────────────
import sys as _sys
_sys.path.insert(0, '/opt/windi/engine')
from dragon_hub import hub as _dragon_hub
# ─────────────────────────────────────────────────────────────
"""

PATCH_ASYNC_HANDLER = '''
# PATCHED: delegate to Dragon Hub
async def dragon():
    import asyncio
    from flask import request, jsonify
    data = request.get_json(force=True) or {}

    async def _guardian(payload, history):
        """Chama a lógica ORIGINAL do monolith como fallback."""
        return _original_dragon_logic(payload, history)

    result = await _dragon_hub.handle(data, guardian_fallback=_guardian)
    return jsonify(result)
'''

PATCH_SYNC_HANDLER = '''
# PATCHED: delegate to Dragon Hub (sync wrapper)
def dragon():
    import asyncio
    from flask import request, jsonify
    data = request.get_json(force=True) or {}

    def _guardian_sync(payload, history):
        return _original_dragon_logic(payload, history)

    async def _run():
        async def _guardian(payload, history):
            return _guardian_sync(payload, history)
        return await _dragon_hub.handle(data, guardian_fallback=_guardian)

    result = asyncio.run(_run())
    return jsonify(result)
'''


def analyse(filepath: str):
    p = Path(filepath)
    if not p.exists():
        print(f"❌ File not found: {filepath}")
        return

    src = p.read_text()
    lines = src.splitlines()

    print(f"\n🔍 Analysing: {filepath}")
    print(f"   Total lines: {len(lines)}")

    # Find dragon route
    for i, line in enumerate(lines, 1):
        if re.search(r'route.*dragon|dragon.*route|def dragon', line, re.IGNORECASE):
            print(f"\n✅ Dragon endpoint found → line {i}:")
            # Show context
            start = max(0, i - 2)
            end = min(len(lines), i + 15)
            for j in range(start, end):
                prefix = "→ " if j == i - 1 else "  "
                print(f"  {prefix}{j+1:4d}: {lines[j]}")
            print()

    # Find app.run
    for i, line in enumerate(lines, 1):
        if 'app.run' in line:
            print(f"✅ app.run found → line {i}: {line.strip()}")

    # Find existing imports
    for i, line in enumerate(lines, 1):
        if 'from dragon_apis' in line or 'import dragon_apis' in line:
            print(f"✅ dragon_apis import → line {i}: {line.strip()}")

    print("\n" + "="*60)
    print("PATCH INSTRUCTIONS:")
    print("="*60)
    print("""
1. Add this import block near the top of the file
   (after existing imports):
""")
    print(PATCH_IMPORT)
    print("""
2. Find the def dragon(): function body.
   Wrap the existing logic into a function called:
       _original_dragon_logic(payload, history)

3. Replace the body of def dragon(): with PATCH_SYNC_HANDLER
   (or PATCH_ASYNC_HANDLER if the server uses async Flask/Quart).

4. Restart the :8108 service.

5. Test:
   curl -s -X POST http://localhost:8108/dragon \\
     -H 'Content-Type: application/json' \\
     -d '{"message":"Gerar comunicado sobre activação do Hub","session_id":"test","intent":"communique"}' \\
     | python3 -m json.tool | head -30
""")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 patch_helper.py <server.py>")
        print("\nTo find the server file, run on the VPS:")
        print("  find /opt/windi -name '*.py' | xargs grep -l 'app.run' 2>/dev/null | grep -v __pycache__")
    else:
        analyse(sys.argv[1])

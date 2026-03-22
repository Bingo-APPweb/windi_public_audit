#!/usr/bin/env python3
"""
WINDI — Patch Alzheimer: _handle_sovereign_local + history
═══════════════════════════════════════════════════════════
Executor : Gêmeo (Claude Code no Strato)
Ficheiro : /opt/windi/agent-palette/agent_dragon_server.py
           (confirmar nome exacto antes de executar)
Data     : 2026-03-22

ROOT CAUSE CONFIRMADO pelo Gêmeo:
  _handle_sovereign_local(intent, message, lang, tier)
  → recebe 'message' mas ignora 'history'
  → 93% das chamadas passam por aqui
  → Dragon esquece TUDO após cada turno

REGRA DE OURO: READ FIRST. PROPOSE ≠ EXECUTE.
Este script analisa e propõe. O Human Dragon autoriza.
"""

import subprocess
import sys
import os
import shutil
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIGURAÇÃO — ajustar se necessário
# ─────────────────────────────────────────────
POSSIBLE_PATHS = [
    "/opt/windi/agent-palette/agent_dragon_server.py",
    "/opt/windi/agent-palette/app.py",
    "/opt/windi/agent-palette/dragon_server.py",
    "/opt/windi/agent-palette/server.py",
]
BACKUP_DIR = "/opt/windi/backups/"

def find_server_file():
    for p in POSSIBLE_PATHS:
        if os.path.exists(p):
            return p
    # Procurar no directório
    result = subprocess.run(
        ["find", "/opt/windi/agent-palette", "-name", "*.py", "-maxdepth", "2"],
        capture_output=True, text=True
    )
    files = [f for f in result.stdout.strip().split("\n") if f]
    print("Ficheiros Python encontrados:")
    for f in files:
        print(f"  {f}")
    return None

def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def backup_file(path):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = os.path.basename(path)
    backup_path = os.path.join(BACKUP_DIR, f"{name}-pre-alzheimer-fix-{ts}")
    shutil.copy2(path, backup_path)
    print(f"✅ Backup: {backup_path}")
    return backup_path

# ─────────────────────────────────────────────
# STEP 1: READ FIRST
# ─────────────────────────────────────────────
print("=" * 60)
print("🐉 PATCH ALZHEIMER — READ FIRST")
print("=" * 60)

server_file = find_server_file()
if not server_file:
    print("❌ Ficheiro servidor não encontrado automaticamente.")
    print("   Executar manualmente:")
    print("   find /opt/windi/agent-palette -name '*.py' | xargs grep -l '_handle_sovereign'")
    sys.exit(1)

print(f"\n📄 Ficheiro: {server_file}")
content = read_file(server_file)
lines = content.split("\n")
print(f"   Linhas totais: {len(lines)}")

# ─────────────────────────────────────────────
# STEP 2: MAPEAR OS PONTOS CIRÚRGICOS
# ─────────────────────────────────────────────
print("\n" + "─" * 50)
print("📍 MAPEAMENTO CIRÚRGICO")
print("─" * 50)

surgical_points = {
    "def_sovereign": None,       # definição da função
    "call_sovereign": None,      # onde é chamada
    "route_dragon": None,        # onde route_dragon recebe history
    "valid_history": None,       # se já existe valid_history
}

for i, line in enumerate(lines, 1):
    if "def _handle_sovereign_local" in line:
        surgical_points["def_sovereign"] = i
        print(f"  L{i:4d} | DEF  | {line.strip()}")
    if "_handle_sovereign_local(" in line and "def " not in line:
        surgical_points["call_sovereign"] = i
        print(f"  L{i:4d} | CALL | {line.strip()}")
    if "route_dragon" in line and "def " in line:
        surgical_points["route_dragon"] = i
        print(f"  L{i:4d} | ROUTE| {line.strip()}")
    if "valid_history" in line:
        surgical_points["valid_history"] = i
        print(f"  L{i:4d} | HIST | {line.strip()}")
    if "history" in line.lower() and "message" in line.lower() and i > 1200 and i < 1300:
        print(f"  L{i:4d} | CTX  | {line.strip()}")

# ─────────────────────────────────────────────
# STEP 3: MOSTRAR CONTEXTO DOS PONTOS CRÍTICOS
# ─────────────────────────────────────────────
print("\n" + "─" * 50)
print("🔬 CONTEXTO — DEF _handle_sovereign_local")
print("─" * 50)
if surgical_points["def_sovereign"]:
    start = surgical_points["def_sovereign"] - 1
    for i, line in enumerate(lines[start:start+25], start+1):
        marker = " ◄" if i == surgical_points["def_sovereign"] else ""
        print(f"  L{i:4d} | {line}{marker}")

print("\n" + "─" * 50)
print("🔬 CONTEXTO — CALL _handle_sovereign_local")
print("─" * 50)
if surgical_points["call_sovereign"]:
    start = max(0, surgical_points["call_sovereign"] - 6)
    end = surgical_points["call_sovereign"] + 8
    for i, line in enumerate(lines[start:end], start+1):
        marker = " ◄ CALL" if i == surgical_points["call_sovereign"] else ""
        print(f"  L{i:4d} | {line}{marker}")

# ─────────────────────────────────────────────
# STEP 4: PROPOSTA DE PATCH
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("💊 PROPOSTA DE PATCH (3 cirurgias)")
print("=" * 60)

print("""
╔══════════════════════════════════════════════════════════╗
║  CIRURGIA 1 — Assinatura da função                       ║
╠══════════════════════════════════════════════════════════╣
║  ANTES: def _handle_sovereign_local(intent, message,     ║
║                                     lang, tier):         ║
║                                                          ║
║  DEPOIS: def _handle_sovereign_local(intent, message,    ║
║                                      lang, tier,         ║
║                                      history=None):      ║
╚══════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════╗
║  CIRURGIA 2 — Usar history no corpo da função            ║
╠══════════════════════════════════════════════════════════╣
║  Adicionar no início do corpo da função:                 ║
║                                                          ║
║  history = history or []                                 ║
║  # Construir contexto a partir do histórico              ║
║  context_summary = ""                                    ║
║  if history:                                             ║
║      recent = history[-4:]  # últimos 2 turnos           ║
║      ctx_parts = []                                      ║
║      for m in recent:                                    ║
║          role = m.get("role","")                         ║
║          text = m.get("content","")[:200]                ║
║          if role and text:                               ║
║              ctx_parts.append(f"{role}: {text}")         ║
║      if ctx_parts:                                       ║
║          context_summary = (                             ║
║              "HISTÓRICO RECENTE:\\n" +                   ║
║              "\\n".join(ctx_parts) +                     ║
║              "\\n\\nMENSAGEM ACTUAL: "                   ║
║          )                                               ║
║  message_with_context = context_summary + message        ║
║                                                          ║
║  (usar message_with_context em vez de message            ║
║   onde a resposta é construída)                          ║
╚══════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════╗
║  CIRURGIA 3 — Passar history na call                     ║
╠══════════════════════════════════════════════════════════╣
║  ANTES:                                                  ║
║    return _handle_sovereign_local(                       ║
║        intent, message, lang, tier)                      ║
║                                                          ║
║  DEPOIS:                                                 ║
║    return _handle_sovereign_local(                       ║
║        intent, message, lang, tier,                      ║
║        history=valid_history)                            ║
╚══════════════════════════════════════════════════════════╝
""")

# ─────────────────────────────────────────────
# STEP 5: APLICAR PATCH (só se autorizado)
# ─────────────────────────────────────────────
print("─" * 50)
print("⚡ APLICAR PATCH?")
print("─" * 50)
print("")
print("  Para aplicar, executar com argumento --apply:")
print(f"  python3 {__file__} --apply")
print("")
print("  REGRA: Human Dragon autoriza → Gêmeo executa --apply")
print("")

if "--apply" not in sys.argv:
    print("✋ Modo READ ONLY — patch NÃO aplicado.")
    print("   Análise concluída. Aguardar autorização.")
    sys.exit(0)

# ─────────────────────────────────────────────
# EXECUÇÃO DO PATCH (com --apply)
# ─────────────────────────────────────────────
print("🔧 APLICANDO PATCH...")

# Backup obrigatório
backup_path = backup_file(server_file)

new_content = content

# PATCH 1: Assinatura da função
if surgical_points["def_sovereign"]:
    # Encontrar a linha exacta e adicionar history=None
    old_sig = None
    for line in lines:
        if "def _handle_sovereign_local" in line:
            old_sig = line
            break

    if old_sig and "history" not in old_sig:
        # Adicionar history=None antes do último ')'
        new_sig = old_sig.rstrip()
        if new_sig.endswith("):"):
            new_sig = new_sig[:-2] + ", history=None):"
        elif new_sig.endswith(","):
            new_sig = new_sig + " history=None"

        new_content = new_content.replace(old_sig.rstrip(), new_sig, 1)
        print(f"  ✅ PATCH 1: assinatura actualizada")
        print(f"     {new_sig.strip()}")
    else:
        print(f"  ⚠️  PATCH 1: já tem history ou não encontrado")

# PATCH 2: Corpo da função — injetar contexto
HISTORY_INJECTION = '''    history = history or []
    # ALZHEIMER FIX: construir contexto a partir do histórico
    context_summary = ""
    if history:
        recent = history[-4:]  # últimos 2 turnos
        ctx_parts = []
        for m in recent:
            role = m.get("role", "")
            text = str(m.get("content", ""))[:200]
            if role and text:
                ctx_parts.append(f"{role}: {text}")
        if ctx_parts:
            context_summary = (
                "HISTÓRICO RECENTE:\\n" +
                "\\n".join(ctx_parts) +
                "\\n\\nMENSAGEM ACTUAL: "
            )
    message = context_summary + message
    # FIM ALZHEIMER FIX
'''

# Encontrar o início do corpo da função e injectar após a docstring/primeira linha
if surgical_points["def_sovereign"] and "ALZHEIMER FIX" not in content:
    def_line_idx = surgical_points["def_sovereign"] - 1
    # Procurar a primeira linha de código real após a def
    inject_after = None
    for i in range(def_line_idx + 1, min(def_line_idx + 10, len(lines))):
        line = lines[i]
        stripped = line.strip()
        # Saltar linhas vazias e docstrings
        if stripped and not stripped.startswith('"""') and not stripped.startswith("'''") and not stripped.startswith('#'):
            inject_after = i
            break

    if inject_after:
        # Inserir o injection antes desta linha
        lines_new = lines[:inject_after] + HISTORY_INJECTION.split("\n") + lines[inject_after:]
        new_content = "\n".join(lines_new)
        print(f"  ✅ PATCH 2: history injection adicionado na L{inject_after+1}")

# PATCH 3: Call site — passar history
if surgical_points["call_sovereign"] and "valid_history" in new_content:
    # Encontrar a call e adicionar history=valid_history
    for old_call_variant in [
        "_handle_sovereign_local(intent, message, lang, tier)",
        "_handle_sovereign_local(intent, message, lang, tier)",
    ]:
        if old_call_variant in new_content and "history=" not in new_content.split(old_call_variant)[1][:50]:
            new_call = old_call_variant.replace(
                "lang, tier)",
                "lang, tier, history=valid_history)"
            )
            new_content = new_content.replace(old_call_variant, new_call, 1)
            print(f"  ✅ PATCH 3: call actualizada com history=valid_history")
            break
    else:
        print(f"  ⚠️  PATCH 3: verificar manualmente a call — pode ter formato diferente")

# Escrever ficheiro
with open(server_file, "w", encoding="utf-8") as f:
    f.write(new_content)
print(f"\n✅ Ficheiro escrito: {server_file}")

# ─────────────────────────────────────────────
# STEP 6: REINICIAR SERVIÇO
# ─────────────────────────────────────────────
print("\n" + "─" * 50)
print("🔄 REINICIAR AGENTE-PALETTE")
print("─" * 50)
print("")
print("  Executar manualmente (padrão nohup):")
print("  ps aux | grep '8108' | grep -v grep")
print("  kill <PID>")
print("  cd /opt/windi/agent-palette")
print("  nohup python3 app.py > /opt/windi/logs/agent-palette.log 2>&1 &")
print("  curl -s -o /dev/null -w '%{http_code}' http://localhost:8108/")
print("")

# ─────────────────────────────────────────────
# STEP 7: TESTE DE VERIFICAÇÃO
# ─────────────────────────────────────────────
print("─" * 50)
print("🧪 TESTE ALZHEIMER — após reinício")
print("─" * 50)
print("""
  T1=$(curl -s http://localhost:8108/api/chat -X POST \\
    -H "Content-Type: application/json" \\
    -d '{"message":"O meu nome é Human Dragon","wallet_id":"pioneer-1"}')

  SESSION=$(echo $T1 | python3 -c "import sys,json; print(json.load(sys.stdin).get('session_id',''))")
  echo "Session: $SESSION"

  curl -s http://localhost:8108/api/chat -X POST \\
    -H "Content-Type: application/json" \\
    -d "{\\\"message\\\":\\\"Como me chamo?\\\",\\\"wallet_id\\\":\\\"pioneer-1\\\",\\\"session_id\\\":\\\"$SESSION\\\"}" \\
    | python3 -c "
  import sys,json
  d=json.load(sys.stdin)
  r=str(d.get('response',''))
  print('Resposta:', r[:200])
  print('✅ CURADO' if 'Human Dragon' in r else '❌ AINDA FALHA')
  "
""")

print("=" * 60)
print("🐉 Patch preparado. Human Dragon autoriza → Gêmeo executa.")
print("   python3 patch_alzheimer_sovereign.py --apply")
print("=" * 60)
